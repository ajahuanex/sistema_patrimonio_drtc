"""
Production settings for Sistema de Registro de Patrimonio
"""

import os
from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY')

# Allowed hosts
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB'),
        'USER': os.environ.get('POSTGRES_USER'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD'),
        'HOST': 'db',
        'PORT': '5432',
        'OPTIONS': {
            'connect_timeout': 60,
        },
        'CONN_MAX_AGE': 600,
    }
}

# Redis Cache
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f"redis://:{os.environ.get('REDIS_PASSWORD')}@redis:6379/0",
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            }
        }
    }
}

# Celery Configuration
CELERY_BROKER_URL = f"redis://:{os.environ.get('REDIS_PASSWORD')}@redis:6379/0"
CELERY_RESULT_BACKEND = f"redis://:{os.environ.get('REDIS_PASSWORD')}@redis:6379/0"
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# Celery Beat Schedule - Tareas Programadas
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    # Limpiar papelera de reciclaje cada día a las 4:00 AM
    'cleanup-recycle-bin': {
        'task': 'apps.core.tasks.cleanup_recycle_bin_task',
        'schedule': crontab(hour=4, minute=0),
        'options': {
            'expires': 3600,  # Expira después de 1 hora si no se ejecuta
        }
    },
    # Advertencias de papelera (7 días antes) - ejecutar diariamente a las 9:00 AM
    'send-recycle-bin-warnings': {
        'task': 'apps.core.tasks.send_recycle_bin_warnings',
        'schedule': crontab(hour=9, minute=0),
        'options': {
            'expires': 3600,
        }
    },
    # Advertencias finales de papelera (1 día antes) - ejecutar cada 6 horas
    'send-recycle-bin-final-warnings': {
        'task': 'apps.core.tasks.send_recycle_bin_final_warnings',
        'schedule': crontab(minute=0, hour='*/6'),  # 00:00, 06:00, 12:00, 18:00
        'options': {
            'expires': 3600,
        }
    },
    # Limpiar reportes expirados cada día a las 2:00 AM
    'limpiar-reportes-expirados': {
        'task': 'apps.reportes.tasks.limpiar_reportes_expirados',
        'schedule': crontab(hour=2, minute=0),
        'options': {
            'expires': 3600,
        }
    },
    # Actualizar estadísticas en caché cada hora
    'actualizar-estadisticas-cache': {
        'task': 'apps.reportes.tasks.actualizar_estadisticas_cache',
        'schedule': crontab(minute=0),  # Cada hora en punto
        'options': {
            'expires': 3600,
        }
    },
    # Limpiar archivos temporales cada 6 horas
    'limpiar-archivos-temporales': {
        'task': 'apps.core.tasks.limpiar_archivos_temporales',
        'schedule': crontab(minute=0, hour='*/6'),
        'options': {
            'expires': 3600,
        }
    },
    # Procesar notificaciones pendientes cada 5 minutos
    'procesar-notificaciones-pendientes': {
        'task': 'apps.notificaciones.tasks.procesar_notificaciones_pendientes',
        'schedule': crontab(minute='*/5'),
        'options': {
            'expires': 300,  # 5 minutos
        }
    },
    # Verificar alertas de mantenimiento cada día a las 8:00 AM
    'verificar-alertas-mantenimiento': {
        'task': 'apps.notificaciones.tasks.verificar_alertas_mantenimiento',
        'schedule': crontab(hour=8, minute=0),
        'options': {
            'expires': 3600,
        }
    },
    # Verificar alertas de depreciación cada lunes a las 9:00 AM
    'verificar-alertas-depreciacion': {
        'task': 'apps.notificaciones.tasks.verificar_alertas_depreciacion',
        'schedule': crontab(hour=9, minute=0, day_of_week=1),
        'options': {
            'expires': 3600,
        }
    },
    # Limpiar notificaciones expiradas cada día a las 1:00 AM
    'limpiar-notificaciones-expiradas': {
        'task': 'apps.notificaciones.tasks.limpiar_notificaciones_expiradas',
        'schedule': crontab(hour=1, minute=0),
        'options': {
            'expires': 3600,
        }
    },
    # Reenviar notificaciones fallidas cada 2 horas
    'reenviar-notificaciones-fallidas': {
        'task': 'apps.notificaciones.tasks.reenviar_notificaciones_fallidas',
        'schedule': crontab(minute=0, hour='*/2'),
        'options': {
            'expires': 3600,
        }
    },
}

# Configuración adicional de Celery
CELERY_TASK_ROUTES = {
    'apps.reportes.tasks.generar_reporte_async': {'queue': 'reportes'},
    'apps.core.tasks.importacion_masiva_excel': {'queue': 'importaciones'},
    'apps.mobile.tasks.procesar_sincronizacion_async': {'queue': 'mobile'},
    'apps.core.tasks.cleanup_recycle_bin_task': {'queue': 'maintenance'},
    'apps.core.tasks.send_recycle_bin_warnings': {'queue': 'notifications'},
    'apps.core.tasks.send_recycle_bin_final_warnings': {'queue': 'notifications'},
}

CELERY_TASK_DEFAULT_QUEUE = 'default'
CELERY_TASK_CREATE_MISSING_QUEUES = True

# Configuración de workers
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)

# Security Settings
SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'True').lower() == 'true'
SECURE_HSTS_SECONDS = int(os.environ.get('SECURE_HSTS_SECONDS', 31536000))
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.environ.get('SECURE_HSTS_INCLUDE_SUBDOMAINS', 'True').lower() == 'true'
SECURE_HSTS_PRELOAD = os.environ.get('SECURE_HSTS_PRELOAD', 'True').lower() == 'true'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Session Configuration
SESSION_COOKIE_AGE = 3600  # 1 hour
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST = True

# CSRF Configuration
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict'

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/app/logs/django.log',
            'maxBytes': 1024*1024*15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/app/logs/django_error.log',
            'maxBytes': 1024*1024*15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'patrimonio': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Sentry Configuration (optional)
SENTRY_DSN = os.environ.get('SENTRY_DSN')
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration
    
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(auto_enabling=True),
            CeleryIntegration(auto_enabling=True),
        ],
        traces_sample_rate=0.1,
        send_default_pii=True,
        environment='production',
    )

# File Upload Settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB

# Application specific settings
BASE_URL = os.environ.get('BASE_URL', 'https://localhost')

# Backup Configuration
BACKUP_RETENTION_DAYS = int(os.environ.get('BACKUP_RETENTION_DAYS', 30))

# Recycle Bin Configuration
PERMANENT_DELETE_CODE = os.environ.get('PERMANENT_DELETE_CODE')
RECYCLE_BIN_RETENTION_DAYS = int(os.environ.get('RECYCLE_BIN_RETENTION_DAYS', 30))
RECYCLE_BIN_AUTO_CLEANUP_ENABLED = os.environ.get('RECYCLE_BIN_AUTO_CLEANUP_ENABLED', 'True').lower() == 'true'
RECYCLE_BIN_MAX_BULK_SIZE = int(os.environ.get('RECYCLE_BIN_MAX_BULK_SIZE', 100))
RECYCLE_BIN_LOCKOUT_ATTEMPTS = int(os.environ.get('RECYCLE_BIN_LOCKOUT_ATTEMPTS', 3))
RECYCLE_BIN_LOCKOUT_MINUTES = int(os.environ.get('RECYCLE_BIN_LOCKOUT_MINUTES', 30))

# reCAPTCHA Configuration
RECAPTCHA_PUBLIC_KEY = os.environ.get('RECAPTCHA_PUBLIC_KEY', '')
RECAPTCHA_PRIVATE_KEY = os.environ.get('RECAPTCHA_PRIVATE_KEY', '')

# Celery Beat Configuration
CELERY_BEAT_ENABLED = os.environ.get('CELERY_BEAT_ENABLED', 'True').lower() == 'true'

# Performance Settings
CONN_MAX_AGE = 600
DATABASE_CONN_MAX_AGE = 600