"""
Django settings for patrimonio project.
"""

import os
from pathlib import Path
from decouple import config
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-this-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_celery_beat',
    'django_extensions',
]

LOCAL_APPS = [
    'apps.core',
    'apps.catalogo',
    'apps.oficinas',
    'apps.bienes',
    'apps.reportes',
    'apps.mobile',
    'apps.notificaciones',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'apps.core.middleware.PermissionMiddleware',
    'apps.core.middleware.AuditMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'patrimonio.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'patrimonio.wsgi.application'

# Database
DATABASES = {
    'default': dj_database_url.parse(
        config('DATABASE_URL', default='sqlite:///db.sqlite3')
    )
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'es-pe'
TIME_ZONE = 'America/Lima'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'static'
STATICFILES_DIRS = [
    BASE_DIR / 'assets',
    BASE_DIR / 'static' / 'frontend',  # React build files
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}

# JWT Settings
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
}

# CORS Settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8080",
]

CORS_ALLOW_CREDENTIALS = True

# Celery Configuration
CELERY_BROKER_URL = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = True

# Configuración de tareas periódicas
from celery.schedules import crontab
CELERY_BEAT_SCHEDULE = {
    # Limpiar reportes expirados cada día a las 2:00 AM
    'limpiar-reportes-expirados': {
        'task': 'apps.reportes.tasks.limpiar_reportes_expirados',
        'schedule': crontab(hour=2, minute=0),
    },
    # Actualizar estadísticas en caché cada hora
    'actualizar-estadisticas-cache': {
        'task': 'apps.reportes.tasks.actualizar_estadisticas_cache',
        'schedule': crontab(minute=0),  # Cada hora en punto
    },
    # Limpiar archivos temporales cada 6 horas
    'limpiar-archivos-temporales': {
        'task': 'apps.core.tasks.limpiar_archivos_temporales',
        'schedule': crontab(minute=0, hour='*/6'),
    },
    # Backup de base de datos cada día a las 3:00 AM
    'backup-base-datos': {
        'task': 'apps.core.tasks.backup_base_datos',
        'schedule': crontab(hour=3, minute=0),
    },
    # Procesar notificaciones pendientes cada 5 minutos
    'procesar-notificaciones-pendientes': {
        'task': 'apps.notificaciones.tasks.procesar_notificaciones_pendientes',
        'schedule': crontab(minute='*/5'),
    },
    # Verificar alertas de mantenimiento cada día a las 8:00 AM
    'verificar-alertas-mantenimiento': {
        'task': 'apps.notificaciones.tasks.verificar_alertas_mantenimiento',
        'schedule': crontab(hour=8, minute=0),
    },
    # Verificar alertas de depreciación cada lunes a las 9:00 AM
    'verificar-alertas-depreciacion': {
        'task': 'apps.notificaciones.tasks.verificar_alertas_depreciacion',
        'schedule': crontab(hour=9, minute=0, day_of_week=1),
    },
    # Limpiar notificaciones expiradas cada día a las 1:00 AM
    'limpiar-notificaciones-expiradas': {
        'task': 'apps.notificaciones.tasks.limpiar_notificaciones_expiradas',
        'schedule': crontab(hour=1, minute=0),
    },
    # Reenviar notificaciones fallidas cada 2 horas
    'reenviar-notificaciones-fallidas': {
        'task': 'apps.notificaciones.tasks.reenviar_notificaciones_fallidas',
        'schedule': crontab(minute=0, hour='*/2'),
    },
}

# Configuración adicional de Celery
CELERY_TASK_ROUTES = {
    'apps.reportes.tasks.generar_reporte_async': {'queue': 'reportes'},
    'apps.core.tasks.importacion_masiva_excel': {'queue': 'importaciones'},
    'apps.mobile.tasks.procesar_sincronizacion_async': {'queue': 'mobile'},
}

CELERY_TASK_DEFAULT_QUEUE = 'default'
CELERY_TASK_CREATE_MISSING_QUEUES = True

# Configuración de workers
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='sistema.patrimonio@drtc-puno.gob.pe')
EMAIL_SUBJECT_PREFIX = '[Sistema Patrimonio] '

# QR Code Configuration
BASE_URL = config('BASE_URL', default='http://localhost:8000')

# Login/Logout URLs
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'patrimonio': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}