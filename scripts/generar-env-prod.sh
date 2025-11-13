#!/bin/bash

# ============================================================================
# Script para generar archivo .env.prod con claves seguras
# Para servidor Ubuntu con IP 161.132.47.92
# ============================================================================

echo "============================================================================"
echo "Generador de archivo .env.prod para IP 161.132.47.92"
echo "============================================================================"
echo ""

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Función para generar contraseña aleatoria
generate_password() {
    local length=$1
    openssl rand -base64 $length | tr -d "=+/" | cut -c1-$length
}

# Función para generar SECRET_KEY de Django
generate_django_secret() {
    python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())" 2>/dev/null || \
    openssl rand -base64 50 | tr -d "=+/" | cut -c1-50
}

echo -e "${YELLOW}Generando claves seguras...${NC}"
echo ""

# Generar claves
SECRET_KEY=$(generate_django_secret)
POSTGRES_PASSWORD=$(generate_password 24)
REDIS_PASSWORD=$(generate_password 24)
PERMANENT_DELETE_CODE=$(generate_password 32)

echo -e "${GREEN}✓ Claves generadas exitosamente${NC}"
echo ""

# Solicitar información del usuario
echo -e "${YELLOW}Por favor, ingresa la siguiente información:${NC}"
echo ""

read -p "Email para notificaciones (ej: tu-email@gmail.com): " EMAIL_USER
read -sp "Contraseña de aplicación de Gmail (16 caracteres): " EMAIL_PASSWORD
echo ""
read -p "Email para reCAPTCHA (opcional, Enter para omitir): " RECAPTCHA_EMAIL

# Generar archivo .env.prod
cat > .env.prod << EOF
# ============================================================================
# CONFIGURACIÓN DE PRODUCCIÓN PARA IP 161.132.47.92 (SIN SSL)
# ============================================================================
# Archivo generado automáticamente el $(date)
# ============================================================================

# ============================================================================
# DJANGO SETTINGS
# ============================================================================
DEBUG=False
SECRET_KEY=$SECRET_KEY
DJANGO_SETTINGS_MODULE=patrimonio.settings.production
ALLOWED_HOSTS=161.132.47.92,localhost

# ============================================================================
# DATABASE CONFIGURATION (PostgreSQL)
# ============================================================================
POSTGRES_DB=patrimonio_prod
POSTGRES_USER=patrimonio_user
POSTGRES_PASSWORD=$POSTGRES_PASSWORD

# ============================================================================
# REDIS CONFIGURATION
# ============================================================================
REDIS_PASSWORD=$REDIS_PASSWORD

# ============================================================================
# EMAIL CONFIGURATION
# ============================================================================
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=$EMAIL_USER
EMAIL_HOST_PASSWORD=$EMAIL_PASSWORD
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=Sistema Patrimonio DRTC <$EMAIL_USER>

# ============================================================================
# APPLICATION URLS
# ============================================================================
BASE_URL=http://161.132.47.92

# ============================================================================
# APPLICATION VERSION
# ============================================================================
APP_VERSION=1.0.0

# ============================================================================
# SECURITY SETTINGS (DESACTIVADO SSL - SOLO PARA IP SIN DOMINIO)
# ============================================================================
SECURE_SSL_REDIRECT=False
SECURE_HSTS_SECONDS=0
SECURE_HSTS_INCLUDE_SUBDOMAINS=False
SECURE_HSTS_PRELOAD=False
SECURE_CONTENT_TYPE_NOSNIFF=True
SECURE_BROWSER_XSS_FILTER=True
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False

# ============================================================================
# RECYCLE BIN CONFIGURATION
# ============================================================================
PERMANENT_DELETE_CODE=$PERMANENT_DELETE_CODE
RECYCLE_BIN_RETENTION_DAYS=30
RECYCLE_BIN_AUTO_CLEANUP_ENABLED=True
RECYCLE_BIN_MAX_BULK_SIZE=100
RECYCLE_BIN_LOCKOUT_ATTEMPTS=3
RECYCLE_BIN_LOCKOUT_MINUTES=30

# ============================================================================
# reCAPTCHA CONFIGURATION (OPCIONAL)
# ============================================================================
RECAPTCHA_PUBLIC_KEY=
RECAPTCHA_PRIVATE_KEY=

# ============================================================================
# CELERY CONFIGURATION
# ============================================================================
CELERY_BEAT_ENABLED=True

# ============================================================================
# BACKUP CONFIGURATION
# ============================================================================
BACKUP_RETENTION_DAYS=30

# ============================================================================
# MONITORING (OPCIONAL)
# ============================================================================
SENTRY_DSN=
EOF

echo ""
echo -e "${GREEN}============================================================================${NC}"
echo -e "${GREEN}✓ Archivo .env.prod generado exitosamente${NC}"
echo -e "${GREEN}============================================================================${NC}"
echo ""
echo -e "${YELLOW}IMPORTANTE - Guarda estas credenciales en un lugar seguro:${NC}"
echo ""
echo "SECRET_KEY: $SECRET_KEY"
echo "POSTGRES_PASSWORD: $POSTGRES_PASSWORD"
echo "REDIS_PASSWORD: $REDIS_PASSWORD"
echo "PERMANENT_DELETE_CODE: $PERMANENT_DELETE_CODE"
echo ""
echo -e "${YELLOW}Ubicación del archivo: $(pwd)/.env.prod${NC}"
echo ""
echo -e "${RED}⚠ NUNCA subas este archivo a GitHub${NC}"
echo -e "${RED}⚠ Mantén estas credenciales en un lugar seguro${NC}"
echo ""
echo -e "${GREEN}Siguiente paso: Ejecutar el despliegue con docker-compose${NC}"
echo ""
