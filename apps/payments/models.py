from django.db import models
from django.contrib.auth.models import User
from apps.core.models import TimeStampedModel, Stock
from apps.portfolio.models import Portfolio
import uuid
from django.utils import timezone

class Deposit(TimeStampedModel):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_METHODS = [
        ('bank_transfer', 'Bank Transfer'),
        ('credit_card', 'Credit Card'),
        ('crypto', 'Cryptocurrency'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='deposits')
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='deposits')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='deposits', null=True, blank=True)
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    transaction_id = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    invoice_number = models.CharField(max_length=50, unique=True, null=True, blank=True)
    invoice_pdf = models.FileField(upload_to='invoices/', null=True, blank=True)
    
    synced_to_sheets = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Deposit {self.transaction_id} - {self.amount}"
    
    def save(self, *args, **kwargs):
        # Track if status is changing to completed
        is_new = self.pk is None
        old_status = None
        
        if not is_new:
            try:
                old_obj = Deposit.objects.get(pk=self.pk)
                old_status = old_obj.status
            except Deposit.DoesNotExist:
                pass
        
        # Generate invoice number if it doesn't exist
        if not self.invoice_number:
            from django.utils import timezone
            now = timezone.now()
            self.invoice_number = f"INV-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        
        # Set completed_at if status changed to completed
        if self.status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()
        
        # Save first
        super().save(*args, **kwargs)
        
        # If status changed to completed, generate invoice
        if self.status == 'completed' and (is_new or old_status != 'completed'):
            if not self.invoice_pdf:
                from apps.core.utils.pdf_generator import generate_invoice_pdf
                from django.core.files.base import ContentFile
                
                try:
                    pdf_content = generate_invoice_pdf(self)
                    filename = f"invoice_{self.invoice_number}.pdf"
                    self.invoice_pdf.save(filename, ContentFile(pdf_content), save=True)
                    logger.info(f"Invoice generated for deposit {self.id}")
                except Exception as e:
                    logger.error(f"Failed to generate invoice for deposit {self.id}: {e}")

class Invoice(TimeStampedModel):
    deposit = models.OneToOneField(Deposit, on_delete=models.CASCADE, related_name='invoice')
    pdf_file = models.FileField(upload_to='invoices/')
    sent_to_email = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Invoice for {self.deposit.transaction_id}"