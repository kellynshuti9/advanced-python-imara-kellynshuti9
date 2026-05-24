import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'imara.settings')

app = Celery('imara')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Add this for Windows compatibility
app.conf.update(
    worker_pool='solo',
    worker_concurrency=1,
)