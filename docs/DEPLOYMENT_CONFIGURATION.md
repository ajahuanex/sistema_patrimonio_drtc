# Guía de Configuración para Deployment - Sistema de Papelera de Reciclaje

## Tabla de Contenidos

1. [Introducción](#introducción)
2. [Variables de Entorno Requeridas](#variables-de-entorno-requeridas)
3. [Configuración de Papelera de Reciclaje](#configuración-de-papelera-de-reciclaje)
4. [Configuración de reCAPTCHA](#configuración-de-recaptcha)
5. [Configuración de Celery Beat](#configuración-de-celery-beat)
6. [Configuración de Seguridad](#configuración-de-seguridad)
7. [Pasos de Deployment](#pasos-de-deployment)
8. [Verificación Post-Deployment](#verificación-post-deployment)
9. [Troubleshooting](#troubleshooting)

---

## Introducción

Esta guía proporciona instrucciones detalladas para configurar todas las variables de entorno necesarias para el deployment en producción del Sistema de Papelera de Reciclaje.

**IMPORTANTE**: Nunca commits archivos `.env.prod` con valores reales al repositorio. Use `.env.prod.example` como plantilla.

---

## Variables de Entorno Requeridas

### Archivo de Configuración

Copie el archivo de ejemplo y configure los valores:

```bash
cp .env.prod.example .env.prod
```

### Variables Críticas

#### 1. Django Core

```bash
# OBLIGATORIO: Genere una clave secreta única
SECRET_KEY=your-super-secret-key-here-change-this-in-production

# OBLIGATORIO: Desactivar debug en producción
DEBUG=False

# OBLIGATORIO: Configure sus dominios
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
```

**Generar SECRET_KEY segura:**
```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

#### 2. Base de Datos

```bash
POSTGRES_DB=patrimonio_prod
POSTGRES_USER=patrimonio_user
POSTGRES_PASSWORD=your-secure-database-password-here
```

**Recomendaciones:**
- Use contraseñas de al menos 20 caracteres
- Incluya mayúsculas, minúsculas, números y símbolos
- No use palabras del diccionario

#### 3. Redis

```bash
REDIS_PASSWORD=your-secure-redis-password-here
```

---

## Configuración de Papelera de Reciclaje

### Variables de Papelera

```bash
# CRÍTICO: Código de seguridad para eliminación permanente
PERMANENT_DELETE_CODE=CHANGE-THIS-TO-SECURE-CODE-IN-PRODUCTION

# Días de retención antes de eliminación automática
RECYCLE_BIN_RETENTION_DAYS=30

# Habilitar eliminación automática
RECYCLE_BIN_AUTO_CLEANUP_ENABLED=True

# Máximo de elementos en operaciones en lote
RECYCLE_BIN_MAX_BULK_SIZE=100

# Intentos permitidos antes de bloqueo
RECYCLE_BIN_LOCKOUT_ATTEMPTS=3

# Minutos de bloqueo tras intentos fallidos
RECYCLE_BIN_LOCKOUT_MINUTES=30
```

### Configuración del Código de Seguridad

El `PERMANENT_DELETE_CODE` es **crítico** para la seguridad del sistema:

**Características requeridas:**
- Mínimo 16 caracteres
- Combinación de letras, números y símbolos
- No debe ser predecible
- Debe ser único para su instalación

**Ejemplo de generación:**
```bash
# Linux/Mac
openssl rand -base64 32

# Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# PowerShell
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 24 | % {[char]$_})
```

**Ejemplo de código seguro:**
```bash
PERMANENT_DELETE_CODE=Xk9mP2vL8qR4wN7tY3hJ6sF1dG5aZ0bC
```

### Políticas de Retención

Configure `RECYCLE_BIN_RETENTION_DAYS` según sus necesidades:

| Tipo de Organización | Días Recomendados |
|---------------------|-------------------|
| Pequeña empresa     | 15-30 días        |
| Mediana empresa     | 30-60 días        |
| Gran empresa        | 60-90 días        |
| Gobierno            | 90-180 días       |

---

## Configuración de reCAPTCHA

### Obtener Claves de reCAPTCHA

1. Visite: https://www.google.com/recaptcha/admin
2. Registre un nuevo sitio
3. Seleccione **reCAPTCHA v2** → **"I'm not a robot" Checkbox**
4. Agregue sus dominios
5. Copie las claves generadas

### Variables de reCAPTCHA

```bash
# Clave pública (Site Key) - visible en el frontend
RECAPTCHA_PUBLIC_KEY=6LcXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# Clave privada (Secret Key) - solo en backend
RECAPTCHA_PRIVATE_KEY=6LcYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY
```

### Configuración de Dominios

En la consola de reCAPTCHA, agregue:
- `your-domain.com`
- `www.your-domain.com`
- `localhost` (solo para testing)

### Testing de reCAPTCHA

Google proporciona claves de prueba:

```bash
# SOLO PARA DESARROLLO - Siempre pasa la validación
RECAPTCHA_PUBLIC_KEY=6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI
RECAPTCHA_PRIVATE_KEY=6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe
```

**ADVERTENCIA**: Nunca use estas claves en producción.

---

## Configuración de Celery Beat

### Variables de Celery

```bash
# Habilitar Celery Beat para tareas periódicas
CELERY_BEAT_ENABLED=True
```

### Tareas Periódicas Configuradas

El sistema incluye las siguientes tareas automáticas:

#### Tareas de Papelera de Reciclaje

| Tarea | Frecuencia | Descripción |
|-------|-----------|-------------|
| `cleanup-recycle-bin` | Diaria 4:00 AM | Elimina permanentemente items expirados |
| `send-recycle-bin-warnings` | Diaria 9:00 AM | Envía advertencias 7 días antes |
| `send-recycle-bin-final-warnings` | Cada 6 horas | Envía advertencias finales 1 día antes |

#### Otras Tareas del Sistema

| Tarea | Frecuencia | Descripción |
|-------|-----------|-------------|
| `limpiar-reportes-expirados` | Diaria 2:00 AM | Limpia reportes antiguos |
| `backup-base-datos` | Diaria 3:00 AM | Backup automático |
| `procesar-notificaciones-pendientes` | Cada 5 minutos | Procesa cola de notificaciones |

### Verificar Configuración de Celery Beat

```bash
# Ver tareas programadas
python manage.py shell
>>> from celery import current_app
>>> print(current_app.conf.beat_schedule)

# Verificar workers activos
celery -A patrimonio inspect active

# Ver estadísticas
celery -A patrimonio inspect stats
```

### Iniciar Celery Beat en Producción

```bash
# Worker principal
celery -A patrimonio worker -l info

# Beat scheduler (en proceso separado)
celery -A patrimonio beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler

# Ambos en un solo comando (solo para desarrollo)
celery -A patrimonio worker -B -l info
```

### Docker Compose

En `docker-compose.prod.yml`, asegúrese de tener:

```yaml
celery-worker:
  build:
    context: .
    dockerfile: Dockerfile.prod
  command: celery -A patrimonio worker -l info
  environment:
    - CELERY_BEAT_ENABLED=True
  depends_on:
    - redis
    - db

celery-beat:
  build:
    context: .
    dockerfile: Dockerfile.prod
  command: celery -A patrimonio beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
  environment:
    - CELERY_BEAT_ENABLED=True
  depends_on:
    - redis
    - db
```

---

## Configuración de Seguridad

### Variables de Seguridad SSL/HTTPS

```bash
# Redirigir HTTP a HTTPS
SECURE_SSL_REDIRECT=True

# HSTS (HTTP Strict Transport Security)
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True

# Cookies seguras
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

### Certificados SSL

```bash
# Rutas a certificados Let's Encrypt
SSL_CERTIFICATE_PATH=/etc/letsencrypt/live/your-domain.com/fullchain.pem
SSL_CERTIFICATE_KEY_PATH=/etc/letsencrypt/live/your-domain.com/privkey.pem
```

### Configuración de Email

```bash
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password-here
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=Sistema Patrimonio <your-email@gmail.com>
```

**Para Gmail:**
1. Habilite verificación en 2 pasos
2. Genere una "Contraseña de aplicación"
3. Use esa contraseña en `EMAIL_HOST_PASSWORD`

---

## Pasos de Deployment

### 1. Preparación

```bash
# Clonar repositorio
git clone <repository-url>
cd patrimonio

# Copiar archivo de configuración
cp .env.prod.example .env.prod

# Editar con valores reales
nano .env.prod  # o vim, code, etc.
```

### 2. Configurar Variables Críticas

Edite `.env.prod` y configure **OBLIGATORIAMENTE**:

- [ ] `SECRET_KEY` - Nueva clave única
- [ ] `PERMANENT_DELETE_CODE` - Código seguro único
- [ ] `ALLOWED_HOSTS` - Sus dominios
- [ ] `POSTGRES_PASSWORD` - Contraseña segura
- [ ] `REDIS_PASSWORD` - Contraseña segura
- [ ] `EMAIL_HOST_USER` y `EMAIL_HOST_PASSWORD`
- [ ] `RECAPTCHA_PUBLIC_KEY` y `RECAPTCHA_PRIVATE_KEY`

### 3. Build y Deploy con Docker

```bash
# Build de imágenes
docker-compose -f docker-compose.prod.yml build

# Iniciar servicios
docker-compose -f docker-compose.prod.yml up -d

# Ver logs
docker-compose -f docker-compose.prod.yml logs -f
```

### 4. Migraciones y Setup Inicial

```bash
# Ejecutar migraciones
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Crear superusuario
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# Configurar permisos de papelera
docker-compose -f docker-compose.prod.yml exec web python manage.py setup_recycle_permissions

# Configurar papelera
docker-compose -f docker-compose.prod.yml exec web python manage.py setup_recycle_bin

# Recolectar archivos estáticos
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

### 5. Verificar Celery

```bash
# Verificar worker
docker-compose -f docker-compose.prod.yml exec celery-worker celery -A patrimonio inspect active

# Verificar beat
docker-compose -f docker-compose.prod.yml logs celery-beat

# Ver tareas programadas
docker-compose -f docker-compose.prod.yml exec web python manage.py shell
>>> from patrimonio.celery import app
>>> print(app.conf.beat_schedule.keys())
```

---

## Verificación Post-Deployment

### Checklist de Verificación

#### 1. Aplicación Web

- [ ] Sitio accesible en HTTPS
- [ ] Login funciona correctamente
- [ ] Certificado SSL válido
- [ ] No hay errores en consola del navegador

#### 2. Papelera de Reciclaje

```bash
# Acceder al sistema
# Navegar a: https://your-domain.com/recycle-bin/

# Verificar:
- [ ] Lista de papelera se muestra
- [ ] Filtros funcionan
- [ ] Restauración funciona
- [ ] Código de seguridad se solicita para eliminación permanente
```

#### 3. reCAPTCHA

```bash
# Intentar eliminar permanentemente un item
# Después de 3 intentos fallidos:
- [ ] reCAPTCHA aparece
- [ ] Validación funciona
- [ ] Bloqueo temporal se activa
```

#### 4. Celery y Tareas Periódicas

```bash
# Verificar workers activos
docker-compose -f docker-compose.prod.yml exec celery-worker celery -A patrimonio inspect active

# Verificar beat está corriendo
docker-compose -f docker-compose.prod.yml logs celery-beat | grep "beat: Starting"

# Verificar tareas programadas
docker-compose -f docker-compose.prod.yml exec web python manage.py shell
>>> from celery import current_app
>>> list(current_app.conf.beat_schedule.keys())
```

Debe ver:
- `cleanup-recycle-bin`
- `send-recycle-bin-warnings`
- `send-recycle-bin-final-warnings`

#### 5. Notificaciones

```bash
# Crear un item de prueba en papelera con fecha de expiración cercana
# Verificar que se envían notificaciones:
- [ ] Advertencia 7 días antes
- [ ] Advertencia final 1 día antes
- [ ] Email recibido correctamente
```

#### 6. Logs

```bash
# Verificar logs sin errores críticos
docker-compose -f docker-compose.prod.yml logs web | grep ERROR
docker-compose -f docker-compose.prod.yml logs celery-worker | grep ERROR
docker-compose -f docker-compose.prod.yml logs celery-beat | grep ERROR
```

---

## Troubleshooting

### Problema: Celery Beat no ejecuta tareas

**Síntomas:**
- Tareas programadas no se ejecutan
- No hay logs de tareas en celery-beat

**Solución:**
```bash
# 1. Verificar que beat está corriendo
docker-compose -f docker-compose.prod.yml ps celery-beat

# 2. Ver logs de beat
docker-compose -f docker-compose.prod.yml logs celery-beat

# 3. Verificar configuración
docker-compose -f docker-compose.prod.yml exec web python manage.py shell
>>> from django.conf import settings
>>> print(settings.CELERY_BEAT_ENABLED)
>>> print(settings.CELERY_BEAT_SCHEDULE)

# 4. Reiniciar beat
docker-compose -f docker-compose.prod.yml restart celery-beat
```

### Problema: reCAPTCHA no aparece

**Síntomas:**
- Después de intentos fallidos, no se muestra reCAPTCHA
- Error en consola del navegador

**Solución:**
```bash
# 1. Verificar claves configuradas
docker-compose -f docker-compose.prod.yml exec web python manage.py shell
>>> from django.conf import settings
>>> print(settings.RECAPTCHA_PUBLIC_KEY)
>>> print(settings.RECAPTCHA_PRIVATE_KEY)

# 2. Verificar dominios en Google reCAPTCHA console
# https://www.google.com/recaptcha/admin

# 3. Verificar que el dominio está en ALLOWED_HOSTS
>>> print(settings.ALLOWED_HOSTS)
```

### Problema: Código de seguridad no funciona

**Síntomas:**
- Código correcto es rechazado
- Error "Código de seguridad incorrecto"

**Solución:**
```bash
# 1. Verificar código configurado
docker-compose -f docker-compose.prod.yml exec web python manage.py shell
>>> from django.conf import settings
>>> print(settings.PERMANENT_DELETE_CODE)

# 2. Verificar que no hay espacios extra
>>> print(repr(settings.PERMANENT_DELETE_CODE))

# 3. Verificar en .env.prod
docker-compose -f docker-compose.prod.yml exec web cat /app/.env.prod | grep PERMANENT_DELETE_CODE
```

### Problema: Notificaciones no se envían

**Síntomas:**
- No se reciben emails de advertencia
- Logs muestran errores de email

**Solución:**
```bash
# 1. Verificar configuración de email
docker-compose -f docker-compose.prod.yml exec web python manage.py shell
>>> from django.conf import settings
>>> print(settings.EMAIL_HOST)
>>> print(settings.EMAIL_HOST_USER)

# 2. Probar envío de email
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Test message', settings.DEFAULT_FROM_EMAIL, ['test@example.com'])

# 3. Verificar logs de celery
docker-compose -f docker-compose.prod.yml logs celery-worker | grep "send_recycle_bin"

# 4. Verificar tareas en cola
docker-compose -f docker-compose.prod.yml exec celery-worker celery -A patrimonio inspect scheduled
```

### Problema: Eliminación automática no funciona

**Síntomas:**
- Items expirados no se eliminan automáticamente
- Tarea cleanup no aparece en logs

**Solución:**
```bash
# 1. Verificar configuración
docker-compose -f docker-compose.prod.yml exec web python manage.py shell
>>> from django.conf import settings
>>> print(settings.RECYCLE_BIN_AUTO_CLEANUP_ENABLED)
>>> print(settings.RECYCLE_BIN_RETENTION_DAYS)

# 2. Ejecutar manualmente
docker-compose -f docker-compose.prod.yml exec web python manage.py cleanup_recycle_bin

# 3. Verificar schedule de beat
>>> from celery import current_app
>>> print(current_app.conf.beat_schedule['cleanup-recycle-bin'])

# 4. Forzar ejecución de tarea
docker-compose -f docker-compose.prod.yml exec web python manage.py shell
>>> from apps.core.tasks import cleanup_recycle_bin_task
>>> cleanup_recycle_bin_task.delay()
```

### Logs Útiles

```bash
# Logs de aplicación web
docker-compose -f docker-compose.prod.yml logs -f web

# Logs de Celery worker
docker-compose -f docker-compose.prod.yml logs -f celery-worker

# Logs de Celery beat
docker-compose -f docker-compose.prod.yml logs -f celery-beat

# Logs de Redis
docker-compose -f docker-compose.prod.yml logs -f redis

# Logs de PostgreSQL
docker-compose -f docker-compose.prod.yml logs -f db

# Todos los logs
docker-compose -f docker-compose.prod.yml logs -f
```

---

## Mantenimiento

### Rotación del Código de Seguridad

Se recomienda cambiar `PERMANENT_DELETE_CODE` periódicamente:

```bash
# 1. Generar nuevo código
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 2. Actualizar .env.prod
nano .env.prod

# 3. Reiniciar aplicación
docker-compose -f docker-compose.prod.yml restart web

# 4. Notificar a administradores del nuevo código
```

### Actualización de Políticas de Retención

```bash
# Cambiar días de retención para todos los módulos
docker-compose -f docker-compose.prod.yml exec web python manage.py update_retention_policies --days 60

# Cambiar para módulo específico
docker-compose -f docker-compose.prod.yml exec web python manage.py update_retention_policies --module oficinas --days 90
```

### Monitoreo

```bash
# Ver estadísticas de papelera
docker-compose -f docker-compose.prod.yml exec web python manage.py generate_recycle_report

# Ver items próximos a expirar
docker-compose -f docker-compose.prod.yml exec web python manage.py shell
>>> from apps.core.models import RecycleBin
>>> from django.utils import timezone
>>> from datetime import timedelta
>>> expiring_soon = RecycleBin.objects.filter(
...     auto_delete_at__lte=timezone.now() + timedelta(days=7)
... ).count()
>>> print(f"Items expiring in 7 days: {expiring_soon}")
```

---

## Contacto y Soporte

Para problemas o preguntas sobre la configuración:

1. Revise esta documentación completa
2. Consulte los logs del sistema
3. Revise la documentación técnica en `docs/RECYCLE_BIN_TECHNICAL_GUIDE.md`
4. Consulte la guía de comandos en `docs/RECYCLE_BIN_COMMANDS.md`

---

## Referencias

- [Documentación de Django](https://docs.djangoproject.com/)
- [Documentación de Celery](https://docs.celeryproject.org/)
- [Google reCAPTCHA](https://www.google.com/recaptcha/)
- [Let's Encrypt](https://letsencrypt.org/)
- [Docker Compose](https://docs.docker.com/compose/)

---

**Última actualización:** 2025-11-10
**Versión:** 1.0.0
