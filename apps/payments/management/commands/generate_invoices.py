from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from apps.payments.models import Deposit
from apps.core.utils.pdf_generator import generate_invoice_pdf
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Generate invoices for completed deposits'
    
    def add_arguments(self, parser):
        parser.add_argument('--deposit-id', type=int, help='Generate for specific deposit')
        parser.add_argument('--all', action='store_true', help='Generate for all pending deposits')
    
    def handle(self, *args, **options):
        if options['deposit_id']:
            deposits = Deposit.objects.filter(id=options['deposit_id'])
        elif options['all']:
            deposits = Deposit.objects.filter(
                status='completed',
                invoice_pdf__isnull=True
            )
        else:
            deposits = Deposit.objects.filter(
                status='completed',
                invoice_pdf__isnull=True
            )[:10]  # Limit to 10 by default
        
        if not deposits.exists():
            self.stdout.write('No deposits needing invoices')
            return
        
        self.stdout.write(f'Generating invoices for {deposits.count()} deposits...')
        
        for deposit in deposits:
            try:
                pdf_content = generate_invoice_pdf(deposit)
                
                # Save PDF to deposit
                filename = f"invoice_{deposit.invoice_number}.pdf"
                deposit.invoice_pdf.save(filename, ContentFile(pdf_content), save=True)
                
                self.stdout.write(f'  Generated: {filename}')
                
            except Exception as e:
                logger.error(f'Failed to generate invoice for deposit {deposit.id}: {str(e)}')
                self.stdout.write(self.style.ERROR(f'  Failed: {deposit.transaction_id}'))