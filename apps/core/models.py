from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

class Profile(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True)
    company = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.user.email}'s Profile"

class Stock(TimeStampedModel):
    symbol = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    current_price = models.DecimalField(max_digits=10, decimal_places=2)
    previous_close = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    change_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    volume = models.BigIntegerField(null=True, blank=True)
    last_updated = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.symbol} - {self.name}"
    
    def save(self, *args, **kwargs):
        if self.previous_close and self.current_price:
            self.change_percent = ((self.current_price - self.previous_close) / self.previous_close) * 100
        super().save(*args, **kwargs)

class StockHistory(TimeStampedModel):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='history')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=timezone.now)
    
    class Meta:
        ordering = ['-date']
        unique_together = ['stock', 'date']