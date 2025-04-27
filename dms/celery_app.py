import os
from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dms.settings')
app = Celery('dms')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Periodic tasks
app.conf.beat_schedule = {
    'check-switches-hourly': {
        'task': 'switch.tasks.check_switches',
        'schedule': 3600,  # Every hour
    },
}