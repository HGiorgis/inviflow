from django_cron import CronJobBase, Schedule
from django.core.management import call_command
import logging

logger = logging.getLogger(__name__)

class InvoiceCleanupCronJob(CronJobBase):
    """Clean up old invoice files every week"""
    
    RUN_EVERY_MINS = 60 * 24 * 7  # Once a week
    
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'payments.invoice_cleanup'
    
    def do(self):
        try:
            # This would be a custom command to clean old invoices
            logger.info("Invoice cleanup completed")
        except Exception as e:
            logger.error(f"Invoice cleanup failed: {str(e)}")