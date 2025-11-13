"""
Health check views for monitoring
"""

import time
from datetime import datetime
from django.http import JsonResponse, HttpResponse
from django.db import connection
from django.core.cache import cache
from django.conf import settings
from celery import Celery
import redis
import os

# Application version
APP_VERSION = os.environ.get('APP_VERSION', '1.0.0')


def health_check(request):
    """
    Basic health check endpoint
    Returns simple status for quick health verification
    """
    response_data = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'version': APP_VERSION
    }
    return JsonResponse(response_data, status=200)


def health_detailed(request):
    """
    Detailed health check with component status
    Verifies DB, Redis, and Celery workers
    """
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'version': APP_VERSION,
        'services': {}
    }
    
    overall_healthy = True
    
    # Database check with timeout
    db_status = check_database()
    health_status['services']['database'] = db_status
    if db_status['status'] != 'healthy':
        overall_healthy = False
    
    # Redis check with ping
    redis_status = check_redis()
    health_status['services']['redis'] = redis_status
    if redis_status['status'] != 'healthy':
        overall_healthy = False
    
    # Celery workers check
    celery_status = check_celery()
    health_status['services']['celery'] = celery_status
    if celery_status['status'] != 'healthy':
        overall_healthy = False
    
    # Set overall status
    health_status['status'] = 'healthy' if overall_healthy else 'unhealthy'
    
    status_code = 200 if overall_healthy else 503
    return JsonResponse(health_status, status=status_code)


def check_database():
    """
    Check PostgreSQL connection with timeout
    """
    try:
        start_time = time.time()
        
        # Set statement timeout to 5 seconds
        with connection.cursor() as cursor:
            cursor.execute("SET statement_timeout = 5000")  # 5 seconds in milliseconds
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
        
        response_time_ms = int((time.time() - start_time) * 1000)
        
        if result and result[0] == 1:
            return {
                'status': 'healthy',
                'response_time_ms': response_time_ms,
                'message': 'Database connection successful'
            }
        else:
            return {
                'status': 'unhealthy',
                'response_time_ms': response_time_ms,
                'message': 'Database query returned unexpected result'
            }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'response_time_ms': None,
            'message': f'Database connection failed: {str(e)}'
        }


def check_redis():
    """
    Check Redis connection with ping
    """
    try:
        start_time = time.time()
        
        # Use Django cache to test Redis
        test_key = 'health_check_test'
        test_value = 'ping'
        
        # Set a value
        cache.set(test_key, test_value, timeout=10)
        
        # Get the value back
        result = cache.get(test_key)
        
        # Clean up
        cache.delete(test_key)
        
        response_time_ms = int((time.time() - start_time) * 1000)
        
        if result == test_value:
            return {
                'status': 'healthy',
                'response_time_ms': response_time_ms,
                'message': 'Redis connection successful'
            }
        else:
            return {
                'status': 'unhealthy',
                'response_time_ms': response_time_ms,
                'message': 'Redis ping failed: value mismatch'
            }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'response_time_ms': None,
            'message': f'Redis connection failed: {str(e)}'
        }


def check_celery():
    """
    Check Celery workers status
    """
    try:
        start_time = time.time()
        
        # Initialize Celery app
        app = Celery('patrimonio')
        app.config_from_object('django.conf:settings', namespace='CELERY')
        
        # Get active workers with timeout
        inspect = app.control.inspect(timeout=5.0)
        active_workers = inspect.active()
        stats = inspect.stats()
        
        response_time_ms = int((time.time() - start_time) * 1000)
        
        if active_workers is None:
            return {
                'status': 'unhealthy',
                'response_time_ms': response_time_ms,
                'active_workers': 0,
                'message': 'No Celery workers responding'
            }
        
        worker_count = len(active_workers)
        
        if worker_count > 0:
            # Get task counts
            total_active_tasks = sum(len(tasks) for tasks in active_workers.values())
            
            return {
                'status': 'healthy',
                'response_time_ms': response_time_ms,
                'active_workers': worker_count,
                'active_tasks': total_active_tasks,
                'message': f'{worker_count} worker(s) active'
            }
        else:
            return {
                'status': 'unhealthy',
                'response_time_ms': response_time_ms,
                'active_workers': 0,
                'message': 'No active Celery workers found'
            }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'response_time_ms': None,
            'active_workers': 0,
            'message': f'Celery check failed: {str(e)}'
        }