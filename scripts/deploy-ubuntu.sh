#!/bin/bash

################################################################################
# Script de Despliegue - Sistema de Patrimonio DRTC Puno
# Uso: ./scripts/deploy-ubuntu.sh
################################################################################

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=========================================="
echo "  Desplegando Sistema de Patrimonio"
echo "=========================================="
echo ""

# Validaciones básicas
echo "1. Validando pre-requisitos..."
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker no está instalado"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "ERROR: Docker Compose no está instalado"
    exit 1
fi

if [ ! -f "$PROJECT_ROOT/.env.prod" ]; then
    echo "ERROR: Archivo .env.prod no existe"
    exit 1
fi

echo "✓ Pre-requisitos OK"
echo ""

# Cargar variables de entorno
cd "$PROJECT_ROOT"
set -a
source .env.prod
set +a

# Construir imágenes
echo "2. Construyendo imágenes Docker..."
docker-compose -f docker-compose.prod.yml build
echo "✓ Imágenes construidas"
echo ""

# Iniciar base de datos
echo "3. Iniciando PostgreSQL y Redis..."
docker-compose -f docker-compose.prod.yml up -d db redis
echo "✓ Servicios de BD iniciados"
echo ""

# Esperar PostgreSQL
echo "4. Esperando PostgreSQL..."
sleep 10
for i in {1..30}; do
    if docker-compose -f docker-compose.prod.yml exec -T db pg_isready -U "${POSTGRES_USER:-patrimonio}" > /dev/null 2>&1; then
        echo "✓ PostgreSQL lista"
        break
    fi
    echo "   Intento $i/30..."
    sleep 2
done
echo ""

# Migraciones
echo "5. Aplicando migraciones..."
docker-compose -f docker-compose.prod.yml run --rm web python manage.py migrate --noinput
echo "✓ Migraciones aplicadas"
echo ""

# Superusuario
echo "6. Configurando superusuario..."
if [ -n "${DJANGO_SUPERUSER_USERNAME:-}" ]; then
    docker-compose -f docker-compose.prod.yml run --rm web python manage.py createsuperuser --noinput 2>/dev/null || echo "   Superusuario ya existe"
fi
echo "✓ Superusuario configurado"
echo ""

# Archivos estáticos
echo "7. Recolectando archivos estáticos..."
docker-compose -f docker-compose.prod.yml run --rm web python manage.py collectstatic --noinput --clear
echo "✓ Archivos estáticos listos"
echo ""

# Iniciar todos los servicios
echo "8. Iniciando todos los servicios..."
docker-compose -f docker-compose.prod.yml up -d
echo "✓ Servicios iniciados"
echo ""

# Esperar y verificar
echo "9. Verificando servicios..."
sleep 10
docker-compose -f docker-compose.prod.yml ps
echo ""

echo "=========================================="
echo "  ✅ DESPLIEGUE COMPLETADO"
echo "=========================================="
echo ""
echo "El sistema está corriendo en:"
echo "  http://localhost (o tu dominio)"
echo "  Admin: http://localhost/admin/"
echo ""
echo "Ver logs:"
echo "  docker-compose -f docker-compose.prod.yml logs -f"
echo ""
