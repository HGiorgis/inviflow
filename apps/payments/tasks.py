from celery import shared_task
from django.core.management import call_command
import logging

logger = logging.getLogger(__name__)

@shared_task
def generate_pending_invoices():
    """Generate invoices for pending deposits"""
    logger.info("Generating pending invoices...")
    try:
        call_command('generate_invoices')
        logger.info("Invoice generation completed")
        return "Invoices generated successfully"
    except Exception as e:
        logger.error(f"Invoice generation failed: {str(e)}")
        raise e