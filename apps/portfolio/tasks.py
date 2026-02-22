from celery import shared_task
from django.core.management import call_command
import logging

logger = logging.getLogger(__name__)

@shared_task
def sync_google_sheets():
    """Sync data with Google Sheets"""
    logger.info("Starting Google Sheets sync...")
    try:
        call_command('sync_google_sheets', direction='both')
        logger.info("Google Sheets sync completed")
        return "Sync completed successfully"
    except Exception as e:
        logger.error(f"Google Sheets sync failed: {str(e)}")
        raise e