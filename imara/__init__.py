# Celery is disabled for development (Redis not installed)
# The async alerts from Formative 1 are preserved but require Redis to run
# To enable Celery, install Redis and uncomment the lines below

# from .celery import app as celery_app
# __all__ = ('celery_app',)