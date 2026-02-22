from django_cron import CronJobBase, Schedule
from django.core.management import call_command
import logging

logger = logging.getLogger(__name__)

class GoogleSheetsSyncCronJob(CronJobBase):
    """Sync with Google Sheets every hour"""
    
    RUN_EVERY_MINS = 60  # Every hour
    
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'portfolio.google_sheets_sync'
    
    def do(self):
        try:
            call_command('sync_google_sheets', direction='both')
            logger.info("Google Sheets sync completed successfully")
        except Exception as e:
            logger.error(f"Google Sheets sync failed: {str(e)}")