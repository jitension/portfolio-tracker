"""
Celery configuration for Portfolio Performance Tracker.
"""
import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

app = Celery('portfolio_tracker')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Configure periodic tasks
app.conf.beat_schedule = {
    'create-daily-portfolio-snapshot': {
        'task': 'apps.portfolio.tasks.create_daily_snapshots',
        'schedule': crontab(hour=23, minute=0),  # 11 PM daily
        'options': {
            'expires': 3600,  # Task expires after 1 hour
        }
    },
    'cleanup-old-manual-snapshots': {
        'task': 'apps.portfolio.tasks.cleanup_old_snapshots',
        'schedule': crontab(hour=2, minute=0, day_of_week=0),  # 2 AM every Sunday
        'options': {
            'expires': 3600,
        }
    },
}

# Celery configuration
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
)


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery."""
    print(f'Request: {self.request!r}')
