from celery import shared_task
import logging
from django.utils import timezone
from ..models import Stock
import random

logger = logging.getLogger(__name__)

@shared_task
def update_stock_prices():
    """Mock task to update stock prices (for demo)"""
    logger.info("Updating stock prices...")
    
    stocks = Stock.objects.filter(is_active=True)
    updated = 0
    
    for stock in stocks:
        # Mock price update - in real app, fetch from API
        old_price = float(stock.current_price)
        change = (random.random() - 0.5) * 0.05  # +/- 5%
        new_price = old_price * (1 + change)
        
        stock.previous_close = stock.current_price
        stock.current_price = round(new_price, 2)
        stock.last_updated = timezone.now()
        stock.save()
        updated += 1
    
    logger.info(f"Updated {updated} stock prices")
    return f"Updated {updated} stock prices"