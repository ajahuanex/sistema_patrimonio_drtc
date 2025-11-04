"""
Health check views for monitoring
"""

import json
from django.http import JsonResponse, HttpResponse
from django.db import connection
from django.core.cache import cache
from django.conf import settings
import redis
import os

def health_check(request):
    """
    Basic health check endpoint
    """
    return HttpResponse("healthy", content_type="text/plain")

def health_detailed(request):
    """
    Detailed health check with component status
    """
    health_status = {
        'status': 'healthy',
        'timestamp': None,
        'components': {}
    }
    
    overall_status = True
    
    # Database check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        health_status['components']['database'] = {
            'status': 'healthy',
            'message': 'Database connection successful'
        }
    except Exception as e:
        health_status['components']['database'] = {
            'status': 'unhealthy',
            'message': f'Database connection failed: {str(e)}'
        }
        overall_status = False
    
    # Redis check
    try:
        cache.set('health_check', 'test', 30)
        cache.get('health_check')
        health_status['components']['redis'] = {
            'status': 'healthy',
            'message': 'Redis connection successful'
        }
    except Exception as e:
        health_status['components']['redis'] = {
            'status': 'unhealthy',
            'message': f'Redis connection failed: {str(e)}'
        }
        overall_status = False
    
    # Disk space check
    try:
        statvfs = os.statvfs('/')
        free_space = statvfs.f_frsize * statvfs.f_bavail
        total_space = statvfs.f_frsize * statvfs.f_blocks
        used_percentage = ((total_space - free_space) / total_space) * 100
        
        if used_percentage > 90:
            health_status['components']['disk'] = {
                'status': 'warning',
                'message': f'Disk usage high: {used_percentage:.1f}%'
            }
        else:
            health_status['components']['disk'] = {
                'status': 'healthy',
                'message': f'Disk usage: {used_percentage:.1f}%'
            }
    except Exception as e:
        health_status['components']['disk'] = {
            'status': 'unknown',
            'message': f'Could not check disk space: {str(e)}'
        }
    
    # Set overall status
    if not overall_status:
        health_status['status'] = 'unhealthy'
    
    # Set timestamp
    from datetime import datetime
    health_status['timestamp'] = datetime.now().isoformat()
    
    status_code = 200 if overall_status else 503
    return JsonResponse(health_status, status=status_code)