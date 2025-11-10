# Task 28: Quick Reference - Variables de Entorno de Producción

## ⚡ Configuración Rápida

### 1. Copiar Archivo de Configuración
```bash
cp .env.prod.example .env.prod
```

### 2. Variables OBLIGATORIAS a Configurar

```bash
# Django Core
SECRET_KEY=<generar-con-comando-abajo>
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# Base de Datos
POSTGRES_PASSWORD=<contraseña-segura-20+-caracteres>

# Redis
REDIS_PASSWORD=<contraseña-segura-20+-caracteres>

# Email
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=<app-password-de-gmail>

# Papelera de Reciclaje (CRÍTICO)
PERMANENT_DELETE_CODE=<generar-con-comando-abajo>

# reCAPTCHA (OBLIGATORIO)
RECAPTCHA_PUBLIC_KEY=<obtener-de-google-recaptcha>
RECAPTCHA_PRIVATE_KEY=<obtener-de-google-recaptcha>
```

---

## 🔐 Generar Códigos Seguros

### SECRET_KEY
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### PERMANENT_DELETE_CODE
```bash
# Opción 1: Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Opción 2: OpenSSL (Linux/Mac)
openssl rand -base64 32

# Opción 3: PowerShell (Windows)
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 24 | % {[char]$_})
```

---

## 🤖 Configurar reCAPTCHA

### Paso 1: Obtener Claves
1. Ir a: https://www.google.com/recaptcha/admin
2. Click en "+" para crear nuevo sitio
3. Seleccionar **reCAPTCHA v2** → **"I'm not a robot" Checkbox**
4. Agregar dominios:
   - `your-domain.com`
   - `www.your-domain.com`
5. Copiar las claves generadas

### Paso 2: Configurar en .env.prod
```bash
RECAPTCHA_PUBLIC_KEY=6LcXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
RECAPTCHA_PRIVATE_KEY=6LcYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY
```

### Claves de Prueba (SOLO DESARROLLO)
```bash
RECAPTCHA_PUBLIC_KEY=6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI
RECAPTCHA_PRIVATE_KEY=6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe
```

---

## ⏰ Tareas Periódicas Configuradas

| Tarea | Frecuencia | Hora |
|-------|-----------|------|
| Limpieza de papelera | Diaria | 4:00 AM |
| Advertencias (7 días) | Diaria | 9:00 AM |
| Advertencias finales (1 día) | Cada 6 horas | 00:00, 06:00, 12:00, 18:00 |

**Nota:** Celery Beat debe estar corriendo para que funcionen.

---

## 🚀 Deploy Rápido

```bash
# 1. Build
docker-compose -f docker-compose.prod.yml build

# 2. Iniciar servicios
docker-compose -f docker-compose.prod.yml up -d

# 3. Migraciones
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# 4. Setup de papelera
docker-compose -f docker-compose.prod.yml exec web python manage.py setup_recycle_bin
docker-compose -f docker-compose.prod.yml exec web python manage.py setup_recycle_permissions

# 5. Crear superusuario
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# 6. Collectstatic
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

---

## ✅ Verificación Rápida

### Verificar Variables
```bash
docker-compose -f docker-compose.prod.yml exec web python manage.py shell
>>> from django.conf import settings
>>> print(settings.PERMANENT_DELETE_CODE)
>>> print(settings.RECAPTCHA_PUBLIC_KEY)
>>> print(settings.CELERY_BEAT_ENABLED)
```

### Verificar Celery Beat
```bash
# Ver tareas programadas
docker-compose -f docker-compose.prod.yml exec web python manage.py shell
>>> from celery import current_app
>>> list(current_app.conf.beat_schedule.keys())
```

Debe mostrar:
- `cleanup-recycle-bin`
- `send-recycle-bin-warnings`
- `send-recycle-bin-final-warnings`

### Verificar Logs
```bash
# Logs de aplicación
docker-compose -f docker-compose.prod.yml logs -f web

# Logs de Celery Beat
docker-compose -f docker-compose.prod.yml logs -f celery-beat

# Logs de Celery Worker
docker-compose -f docker-compose.prod.yml logs -f celery-worker
```

---

## 🔧 Troubleshooting Rápido

### Problema: Código de seguridad no funciona
```bash
# Verificar código configurado
docker-compose -f docker-compose.prod.yml exec web python manage.py shell
>>> from django.conf import settings
>>> print(repr(settings.PERMANENT_DELETE_CODE))
```

### Problema: reCAPTCHA no aparece
```bash
# Verificar claves
docker-compose -f docker-compose.prod.yml exec web python manage.py shell
>>> from django.conf import settings
>>> print(settings.RECAPTCHA_PUBLIC_KEY)
>>> print(settings.RECAPTCHA_PRIVATE_KEY)
```

### Problema: Celery Beat no ejecuta tareas
```bash
# Verificar que beat está corriendo
docker-compose -f docker-compose.prod.yml ps celery-beat

# Ver logs
docker-compose -f docker-compose.prod.yml logs celery-beat

# Reiniciar
docker-compose -f docker-compose.prod.yml restart celery-beat
```

### Problema: Notificaciones no se envían
```bash
# Probar envío de email
docker-compose -f docker-compose.prod.yml exec web python manage.py shell
>>> from django.core.mail import send_mail
>>> from django.conf import settings
>>> send_mail('Test', 'Test', settings.DEFAULT_FROM_EMAIL, ['test@example.com'])
```

---

## 📋 Checklist de Deployment

- [ ] Copiar `.env.prod.example` a `.env.prod`
- [ ] Generar `SECRET_KEY` única
- [ ] Generar `PERMANENT_DELETE_CODE` seguro
- [ ] Configurar `ALLOWED_HOSTS` con dominios reales
- [ ] Configurar contraseñas de base de datos y Redis
- [ ] Configurar email (Gmail con app password)
- [ ] Obtener claves de reCAPTCHA
- [ ] Configurar claves de reCAPTCHA en `.env.prod`
- [ ] Verificar que `CELERY_BEAT_ENABLED=True`
- [ ] Build de imágenes Docker
- [ ] Iniciar servicios
- [ ] Ejecutar migraciones
- [ ] Ejecutar setup de papelera
- [ ] Crear superusuario
- [ ] Collectstatic
- [ ] Verificar que sitio funciona
- [ ] Verificar que Celery Beat está corriendo
- [ ] Probar eliminación con código de seguridad
- [ ] Probar que reCAPTCHA aparece después de 3 intentos
- [ ] Verificar logs sin errores

---

## 📚 Documentación Completa

Para información detallada, consultar:

- **Guía Completa de Deployment:** `docs/DEPLOYMENT_CONFIGURATION.md`
- **Resumen de Implementación:** `.kiro/specs/sistema-papelera-reciclaje/TASK_28_IMPLEMENTATION_SUMMARY.md`
- **Guía Técnica:** `docs/RECYCLE_BIN_TECHNICAL_GUIDE.md`
- **Comandos:** `docs/RECYCLE_BIN_COMMANDS.md`

---

## 🎯 Variables Clave por Categoría

### Seguridad Crítica
```bash
SECRET_KEY=<único-por-instalación>
PERMANENT_DELETE_CODE=<mínimo-16-caracteres>
RECAPTCHA_PRIVATE_KEY=<mantener-secreto>
```

### Papelera de Reciclaje
```bash
RECYCLE_BIN_RETENTION_DAYS=30
RECYCLE_BIN_AUTO_CLEANUP_ENABLED=True
RECYCLE_BIN_LOCKOUT_ATTEMPTS=3
RECYCLE_BIN_LOCKOUT_MINUTES=30
```

### Automatización
```bash
CELERY_BEAT_ENABLED=True
```

### Protección
```bash
RECAPTCHA_PUBLIC_KEY=<site-key>
RECAPTCHA_PRIVATE_KEY=<secret-key>
```

---

**Última actualización:** 2025-11-10
