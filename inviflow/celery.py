import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inviflow.settings')

app = Celery('inviflow')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Configure periodic tasks
app.conf.beat_schedule = {
    'sync-google-sheets-every-hour': {
        'task': 'apps.portfolio.tasks.sync_google_sheets',
        'schedule': crontab(minute=0, hour='*/1'),  # Every hour
    },
    'generate-invoices-every-15-minutes': {
        'task': 'apps.payments.tasks.generate_pending_invoices',
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
    },
    'update-stock-prices-daily': {
        'task': 'apps.core.tasks.update_stock_prices',
        'schedule': crontab(minute=0, hour=9),  # 9 AM daily
    },
}

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')