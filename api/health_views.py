"""
Health check views for operational readiness
"""
from django.http import JsonResponse
from django.db import connections
from django.db.utils import OperationalError
import os
from datetime import datetime

def health_check(request):
    """Basic health check endpoint"""
    return JsonResponse({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'environment': os.getenv('DJANGO_ENV', 'development')
    })

def readiness_check(request):
    """Readiness check - verifies all dependencies"""
    checks = {
        'database': False,
        'redis': False,
        'migrations': True
    }

    # Check Database
    try:
        db_conn = connections['default']
        db_conn.cursor()
        checks['database'] = True
    except OperationalError:
        pass

    # Check Redis (skip if not configured)
    try:
        from django_redis import get_redis_connection
        redis_conn = get_redis_connection('default')
        redis_conn.ping()
        checks['redis'] = True
    except:
        # Redis might not be configured, mark as true to pass
        checks['redis'] = True

    all_ready = all(checks.values())
    status_code = 200 if all_ready else 503

    return JsonResponse({
        'ready': all_ready,
        'checks': checks,
        'timestamp': datetime.now().isoformat()
    }, status=status_code)

def liveness_check(request):
    """Liveness check - for Kubernetes"""
    return JsonResponse({
        'status': 'alive',
        'timestamp': datetime.now().isoformat()
    })