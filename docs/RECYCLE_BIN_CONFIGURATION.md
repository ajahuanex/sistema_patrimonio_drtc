# Guía de Configuración - Sistema de Papelera de Reciclaje

## Introducción

Esta guía describe todas las opciones de configuración disponibles para el sistema de papelera de reciclaje, incluyendo variables de entorno, configuraciones de base de datos y personalizaciones avanzadas.

## Variables de Entorno

### Variables Requeridas

#### PERMANENT_DELETE_CODE

Código de seguridad para eliminación permanente.

```bash
# .env
PERMANENT_DELETE_CODE=tu_codigo_super_secreto_aqui_2025
```

**Requisitos:**
- Mínimo 12 caracteres
- Combinar letras, números y símbolos
- Cambiar cada 90 días
- No compartir en repositorios públicos

**Ejemplo seguro:**
```bash
PERMANENT_DELETE_CODE=P@tr1m0n10_D3l_2025!Secure
```

### Variables Opcionales

#### Configuración de Retención

```bash
# Días de retención por defecto
RECYCLE_BIN_DEFAULT_RETENTION_DAYS=30

# Habilitar eliminación automática
RECYCLE_BIN_AUTO_DELETE_ENABLED=True

# Días para primera advertencia
RECYCLE_BIN_WARNING_DAYS=7

# Días para advertencia final
RECYCLE_BIN_FINAL_WARNING_DAYS=1
```

#### Configuración de Notificaciones

```bash
# Habilitar notificaciones por email
RECYCLE_BIN_EMAIL_NOTIFICATIONS=True

# Email del remitente
RECYCLE_BIN_FROM_EMAIL=noreply@patrimonio.gob

# Emails de administradores para alertas
RECYCLE_BIN_ADMIN_EMAILS=admin1@patrimonio.gob,admin2@patrimonio.gob
```

#### Configuración de Seguridad

```bash
# Intentos máximos de código incorrecto
RECYCLE_BIN_MAX_CODE_ATTEMPTS=3

# Tiempo de bloqueo en minutos
RECYCLE_BIN_LOCKOUT_DURATION=30

# Habilitar CAPTCHA después de intentos fallidos
RECYCLE_BIN_ENABLE_CAPTCHA=True

# Claves de reCAPTCHA
RECAPTCHA_PUBLIC_KEY=tu_clave_publica
RECAPTCHA_PRIVATE_KEY=tu_clave_privada
```

#### Configuración de Performance

```bash
# Tamaño de página en listados
RECYCLE_BIN_PAGE_SIZE=20

# Tiempo de caché en segundos
RECYCLE_BIN_CACHE_TIMEOUT=300

# Habilitar caché de estadísticas
RECYCLE_BIN_ENABLE_STATS_CACHE=True
```

#### Configuración de Celery

```bash
# Broker URL
CELERY_BROKER_URL=redis://localhost:6379/0

# Backend de resultados
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Timezone
CELERY_TIMEZONE=America/Mexico_City
```

## Configuración en settings.py

### Configuración Básica

```python
# patrimonio/settings.py

# Importar configuraciones de papelera
from apps.core.recycle_bin_settings import *

# O configurar manualmente:
RECYCLE_BIN_CONFIG = {
    'DEFAULT_RETENTION_DAYS': int(os.getenv('RECYCLE_BIN_DEFAULT_RETENTION_DAYS', 30)),
    'AUTO_DELETE_ENABLED': os.getenv('RECYCLE_BIN_AUTO_DELETE_ENABLED', 'True') == 'True',
    'WARNING_DAYS': int(os.getenv('RECYCLE_BIN_WARNING_DAYS', 7)),
    'FINAL_WARNING_DAYS': int(os.getenv('RECYCLE_BIN_FINAL_WARNING_DAYS', 1)),
    'EMAIL_NOTIFICATIONS': os.getenv('RECYCLE_BIN_EMAIL_NOTIFICATIONS', 'True') == 'True',
    'MAX_CODE_ATTEMPTS': int(os.getenv('RECYCLE_BIN_MAX_CODE_ATTEMPTS', 3)),
    'LOCKOUT_DURATION': int(os.getenv('RECYCLE_BIN_LOCKOUT_DURATION', 30)),
    'PAGE_SIZE': int(os.getenv('RECYCLE_BIN_PAGE_SIZE', 20)),
    'CACHE_TIMEOUT': int(os.getenv('RECYCLE_BIN_CACHE_TIMEOUT', 300)),
}

# Código de seguridad
PERMANENT_DELETE_CODE = os.getenv('PERMANENT_DELETE_CODE', 'CHANGE_ME_IN_PRODUCTION')

# Validar en producción
if not DEBUG and PERMANENT_DELETE_CODE == 'CHANGE_ME_IN_PRODUCTION':
    raise ImproperlyConfigured('PERMANENT_DELETE_CODE must be set in production')
```

### Configuración de Permisos

```python
# Permisos personalizados
RECYCLE_BIN_PERMISSIONS = {
    'view_recycle_bin': 'Puede ver la papelera de reciclaje',
    'restore_items': 'Puede restaurar elementos',
    'restore_own_items': 'Puede restaurar sus propios elementos',
    'restore_others_items': 'Puede restaurar elementos de otros',
    'permanent_delete_items': 'Puede eliminar permanentemente',
    'view_audit_logs': 'Puede ver logs de auditoría',
    'export_audit_logs': 'Puede exportar logs de auditoría',
    'configure_recycle_bin': 'Puede configurar el sistema',
}
```

### Configuración de Logging

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'recycle_bin_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/recycle_bin.log',
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'security_file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/recycle_bin_security.log',
            'maxBytes': 1024 * 1024 * 10,
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'recycle_bin': {
            'handlers': ['recycle_bin_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'recycle_bin.security': {
            'handlers': ['security_file'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}
```

## Configuración por Módulo

### Usando el Admin de Django

1. Accede al admin: `/admin/core/recyclebinconfig/`
2. Crea o edita configuración para cada módulo
3. Configura:
   - Días de retención
   - Eliminación automática
   - Permisos de restauración
   - Días de advertencia

### Usando Comandos de Management

```bash
# Configurar módulo de oficinas
python manage.py setup_recycle_bin \
  --module=oficinas \
  --retention-days=45 \
  --auto-delete

# Configurar módulo de bienes
python manage.py setup_recycle_bin \
  --module=bienes \
  --retention-days=90 \
  --no-auto-delete
```

### Programáticamente

```python
from apps.core.models import RecycleBinConfig

# Crear configuración
config = RecycleBinConfig.objects.create(
    module_name='oficinas',
    retention_days=45,
    auto_delete_enabled=True,
    can_restore_own=True,
    can_restore_others=False,
    warning_days_before=7,
    final_warning_days_before=1
)

# Actualizar configuración existente
config = RecycleBinConfig.objects.get(module_name='bienes')
config.retention_days = 90
config.save()
```

## Configuración de Celery Beat

### Tareas Periódicas

```python
# patrimonio/celery.py

from celery import Celery
from celery.schedules import crontab

app = Celery('patrimonio')

app.conf.beat_schedule = {
    # Limpieza automática diaria a las 2:00 AM
    'cleanup-recycle-bin': {
        'task': 'patrimonio.celery.cleanup_recycle_bin_task',
        'schedule': crontab(hour=2, minute=0),
        'options': {'expires': 3600},
    },
    
    # Notificaciones de advertencia diarias a las 9:00 AM
    'send-recycle-warnings': {
        'task': 'patrimonio.celery.send_recycle_warnings_task',
        'schedule': crontab(hour=9, minute=0),
        'options': {'expires': 3600},
    },
    
    # Notificaciones finales diarias a las 9:00 AM
    'send-final-warnings': {
        'task': 'patrimonio.celery.send_final_warnings_task',
        'schedule': crontab(hour=9, minute=0),
        'options': {'expires': 3600},
    },
    
    # Verificación de patrones sospechosos diaria a las 9:30 AM
    'check-suspicious-patterns': {
        'task': 'patrimonio.celery.check_suspicious_patterns_task',
        'schedule': crontab(hour=9, minute=30),
        'options': {'expires': 3600},
    },
    
    # Limpieza de caché semanal los domingos a las 3:00 AM
    'cleanup-recycle-cache': {
        'task': 'patrimonio.celery.cleanup_recycle_cache_task',
        'schedule': crontab(hour=3, minute=0, day_of_week=0),
    },
}
```

### Iniciar Celery

```bash
# Worker
celery -A patrimonio worker --loglevel=info

# Beat (scheduler)
celery -A patrimonio beat --loglevel=info

# Ambos juntos
celery -A patrimonio worker --beat --loglevel=info
```

## Configuración de Base de Datos

### Índices Recomendados

Los índices se crean automáticamente con las migraciones, pero puedes verificarlos:

```sql
-- Verificar índices en RecycleBin
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'core_recyclebin';

-- Verificar índices en DeletionAuditLog
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'core_deletionauditlog';
```

### Optimizaciones de PostgreSQL

```sql
-- Analizar tablas para optimizar queries
ANALYZE core_recyclebin;
ANALYZE core_deletionauditlog;

-- Vacuum para limpiar espacio
VACUUM ANALYZE core_recyclebin;
VACUUM ANALYZE core_deletionauditlog;
```

### Configuración de Particionamiento (Opcional)

Para sistemas con alto volumen de datos:

```sql
-- Particionar DeletionAuditLog por mes
CREATE TABLE deletion_audit_log_2025_01 PARTITION OF core_deletionauditlog
FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

CREATE TABLE deletion_audit_log_2025_02 PARTITION OF core_deletionauditlog
FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');
```

## Configuración de Caché

### Redis (Recomendado)

```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'recycle_bin',
        'TIMEOUT': 300,
    }
}
```

### Memcached

```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.PyMemcacheCache',
        'LOCATION': '127.0.0.1:11211',
        'KEY_PREFIX': 'recycle_bin',
        'TIMEOUT': 300,
    }
}
```

### File-based (Desarrollo)

```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': '/var/tmp/django_cache',
        'TIMEOUT': 300,
    }
}
```

## Configuración de Notificaciones

### Email Backend

```python
# settings.py

# SMTP
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'tu_email@gmail.com'
EMAIL_HOST_PASSWORD = 'tu_password'
DEFAULT_FROM_EMAIL = 'noreply@patrimonio.gob'

# Para desarrollo (console)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Para testing (memory)
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
```

### Templates de Email

Personaliza los templates en:
- `templates/notificaciones/email_recycle_warning.html`
- `templates/notificaciones/email_recycle_final_warning.html`

```html
<!-- templates/notificaciones/email_recycle_warning.html -->
{% extends 'notificaciones/email_base.html' %}

{% block content %}
<h2>Elementos próximos a eliminarse</h2>
<p>Hola {{ user.get_full_name }},</p>
<p>Los siguientes elementos se eliminarán en {{ days }} días:</p>
<ul>
{% for item in items %}
    <li>{{ item.object_repr }} ({{ item.module_name }})</li>
{% endfor %}
</ul>
<p>
    <a href="{{ restore_url }}">Restaurar elementos</a>
</p>
{% endblock %}
```

## Configuración de Seguridad

### reCAPTCHA

1. Obtén claves en: https://www.google.com/recaptcha/admin

2. Configura en `.env`:
```bash
RECAPTCHA_PUBLIC_KEY=tu_clave_publica
RECAPTCHA_PRIVATE_KEY=tu_clave_privada
```

3. Configura en `settings.py`:
```python
RECAPTCHA_PUBLIC_KEY = os.getenv('RECAPTCHA_PUBLIC_KEY')
RECAPTCHA_PRIVATE_KEY = os.getenv('RECAPTCHA_PRIVATE_KEY')
RECAPTCHA_REQUIRED_SCORE = 0.5  # Para reCAPTCHA v3
```

### Rate Limiting

```python
# settings.py
RECYCLE_BIN_RATE_LIMITS = {
    'permanent_delete': '3/hour',
    'restore': '20/hour',
    'view': '100/hour',
}
```

### CORS (si usas API)

```python
CORS_ALLOWED_ORIGINS = [
    "https://patrimonio.gob",
    "https://www.patrimonio.gob",
]

CORS_ALLOW_METHODS = [
    'GET',
    'POST',
    'PUT',
    'DELETE',
]
```

## Configuración de Roles y Permisos

### Crear Grupos Predefinidos

```python
# Script de inicialización
from django.contrib.auth.models import Group, Permission

# Grupo Administrador
admin_group = Group.objects.create(name='Administradores Papelera')
admin_perms = Permission.objects.filter(
    codename__in=[
        'view_recycle_bin',
        'restore_items',
        'permanent_delete_items',
        'view_audit_logs',
        'export_audit_logs',
        'configure_recycle_bin',
    ]
)
admin_group.permissions.set(admin_perms)

# Grupo Funcionario
func_group = Group.objects.create(name='Funcionarios')
func_perms = Permission.objects.filter(
    codename__in=[
        'view_recycle_bin',
        'restore_own_items',
    ]
)
func_group.permissions.set(func_perms)

# Grupo Auditor
audit_group = Group.objects.create(name='Auditores')
audit_perms = Permission.objects.filter(
    codename__in=[
        'view_recycle_bin',
        'view_audit_logs',
        'export_audit_logs',
    ]
)
audit_group.permissions.set(audit_perms)
```

### Asignar Usuarios a Grupos

```bash
# Usando comando
python manage.py assign_recycle_permissions \
  --user=admin \
  --role=admin

# Programáticamente
from django.contrib.auth.models import User, Group

user = User.objects.get(username='admin')
group = Group.objects.get(name='Administradores Papelera')
user.groups.add(group)
```

## Configuración de Monitoreo

### Prometheus Metrics (Opcional)

```python
# settings.py
INSTALLED_APPS += ['django_prometheus']

MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    # ... otros middlewares
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]

# Métricas personalizadas
from prometheus_client import Counter, Histogram

recycle_bin_operations = Counter(
    'recycle_bin_operations_total',
    'Total de operaciones en papelera',
    ['operation', 'module']
)

recycle_bin_duration = Histogram(
    'recycle_bin_operation_duration_seconds',
    'Duración de operaciones',
    ['operation']
)
```

### Sentry (Monitoreo de Errores)

```python
# settings.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn=os.getenv('SENTRY_DSN'),
    integrations=[DjangoIntegration()],
    traces_sample_rate=1.0,
    send_default_pii=True,
    environment=os.getenv('ENVIRONMENT', 'development'),
)
```

## Archivos de Configuración de Ejemplo

### .env.example

```bash
# Seguridad
PERMANENT_DELETE_CODE=CHANGE_ME_IN_PRODUCTION
RECAPTCHA_PUBLIC_KEY=your_public_key
RECAPTCHA_PRIVATE_KEY=your_private_key

# Retención
RECYCLE_BIN_DEFAULT_RETENTION_DAYS=30
RECYCLE_BIN_AUTO_DELETE_ENABLED=True
RECYCLE_BIN_WARNING_DAYS=7
RECYCLE_BIN_FINAL_WARNING_DAYS=1

# Notificaciones
RECYCLE_BIN_EMAIL_NOTIFICATIONS=True
RECYCLE_BIN_FROM_EMAIL=noreply@patrimonio.gob
RECYCLE_BIN_ADMIN_EMAILS=admin@patrimonio.gob

# Seguridad
RECYCLE_BIN_MAX_CODE_ATTEMPTS=3
RECYCLE_BIN_LOCKOUT_DURATION=30
RECYCLE_BIN_ENABLE_CAPTCHA=True

# Performance
RECYCLE_BIN_PAGE_SIZE=20
RECYCLE_BIN_CACHE_TIMEOUT=300
RECYCLE_BIN_ENABLE_STATS_CACHE=True

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CELERY_TIMEZONE=America/Mexico_City

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_password
```

### .env.prod.example

```bash
# Producción - Configuración de Papelera de Reciclaje

# CRÍTICO: Cambiar este código en producción
PERMANENT_DELETE_CODE=P@tr1m0n10_Pr0d_2025!Secure_Code

# Configuración de retención
RECYCLE_BIN_DEFAULT_RETENTION_DAYS=60
RECYCLE_BIN_AUTO_DELETE_ENABLED=True
RECYCLE_BIN_WARNING_DAYS=10
RECYCLE_BIN_FINAL_WARNING_DAYS=2

# Notificaciones
RECYCLE_BIN_EMAIL_NOTIFICATIONS=True
RECYCLE_BIN_FROM_EMAIL=noreply@patrimonio.gob
RECYCLE_BIN_ADMIN_EMAILS=admin1@patrimonio.gob,admin2@patrimonio.gob

# Seguridad reforzada
RECYCLE_BIN_MAX_CODE_ATTEMPTS=3
RECYCLE_BIN_LOCKOUT_DURATION=60
RECYCLE_BIN_ENABLE_CAPTCHA=True
RECAPTCHA_PUBLIC_KEY=your_production_public_key
RECAPTCHA_PRIVATE_KEY=your_production_private_key

# Performance optimizada
RECYCLE_BIN_PAGE_SIZE=50
RECYCLE_BIN_CACHE_TIMEOUT=600
RECYCLE_BIN_ENABLE_STATS_CACHE=True

# Celery con Redis
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
CELERY_TIMEZONE=America/Mexico_City

# Email SMTP
EMAIL_HOST=smtp.patrimonio.gob
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=sistema@patrimonio.gob
EMAIL_HOST_PASSWORD=secure_password_here

# Monitoreo
SENTRY_DSN=https://your_sentry_dsn
ENVIRONMENT=production
```

## Validación de Configuración

### Script de Validación

```bash
# Crear script: scripts/validate_recycle_config.py
python manage.py shell < scripts/validate_recycle_config.py
```

```python
# scripts/validate_recycle_config.py
import os
from django.conf import settings

print("=== Validación de Configuración de Papelera ===\n")

# Validar código de seguridad
code = getattr(settings, 'PERMANENT_DELETE_CODE', None)
if not code or code == 'CHANGE_ME':
    print("❌ PERMANENT_DELETE_CODE no configurado")
else:
    if len(code) < 12:
        print("⚠️  PERMANENT_DELETE_CODE muy corto (mínimo 12 caracteres)")
    else:
        print("✓ PERMANENT_DELETE_CODE configurado")

# Validar Celery
broker = getattr(settings, 'CELERY_BROKER_URL', None)
if broker:
    print("✓ Celery broker configurado")
else:
    print("❌ Celery broker no configurado")

# Validar Email
email_backend = getattr(settings, 'EMAIL_BACKEND', None)
if email_backend:
    print(f"✓ Email backend: {email_backend}")
else:
    print("❌ Email backend no configurado")

print("\n=== Validación Completada ===")
```

## Troubleshooting de Configuración

### Problema: Código de seguridad no funciona

**Verificar:**
```python
python manage.py shell
>>> from django.conf import settings
>>> print(settings.PERMANENT_DELETE_CODE)
```

### Problema: Tareas de Celery no se ejecutan

**Verificar:**
```bash
# Ver tareas programadas
celery -A patrimonio inspect scheduled

# Ver workers activos
celery -A patrimonio inspect active
```

### Problema: Notificaciones no se envían

**Verificar:**
```python
python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Test', 'from@test.com', ['to@test.com'])
```

## Referencias

- Django Settings: https://docs.djangoproject.com/en/stable/ref/settings/
- Celery Configuration: https://docs.celeryproject.org/en/stable/userguide/configuration.html
- Redis Configuration: https://redis.io/documentation
- reCAPTCHA: https://developers.google.com/recaptcha
