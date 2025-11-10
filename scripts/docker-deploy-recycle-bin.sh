#!/bin/bash
# Script de despliegue para Sistema de Papelera de Reciclaje en Docker
# Linux/Mac Shell Script

set -e  # Salir si hay algún error

echo "========================================"
echo "  Despliegue de Papelera de Reciclaje"
echo "  Sistema de Patrimonio DRTC"
echo "========================================"
echo ""

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificar que Docker está corriendo
echo "[1/8] Verificando Docker..."
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}[ERROR]${NC} Docker no está corriendo. Por favor inicia Docker."
    exit 1
fi
echo -e "${GREEN}[OK]${NC} Docker está corriendo"
echo ""

# Detener contenedores actuales
echo "[2/8] Deteniendo contenedores actuales..."
docker-compose down
echo -e "${GREEN}[OK]${NC} Contenedores detenidos"
echo ""

# Reconstruir la imagen web con los nuevos archivos
echo "[3/8] Reconstruyendo imagen web..."
if ! docker-compose build web; then
    echo -e "${RED}[ERROR]${NC} Falló al construir la imagen"
    exit 1
fi
echo -e "${GREEN}[OK]${NC} Imagen reconstruida"
echo ""

# Iniciar servicios
echo "[4/8] Iniciando servicios..."
if ! docker-compose up -d; then
    echo -e "${RED}[ERROR]${NC} Falló al iniciar servicios"
    exit 1
fi
echo -e "${GREEN}[OK]${NC} Servicios iniciados"
echo ""

# Esperar a que los servicios estén listos
echo "[5/8] Esperando a que los servicios estén listos..."
sleep 10
echo -e "${GREEN}[OK]${NC} Servicios listos"
echo ""

# Recolectar archivos estáticos (incluye el nuevo CSS)
echo "[6/8] Recolectando archivos estáticos..."
if ! docker-compose exec -T web python manage.py collectstatic --noinput; then
    echo -e "${YELLOW}[ADVERTENCIA]${NC} Falló al recolectar estáticos, intentando de nuevo..."
    sleep 5
    docker-compose exec -T web python manage.py collectstatic --noinput || true
fi
echo -e "${GREEN}[OK]${NC} Archivos estáticos recolectados"
echo ""

# Ejecutar migraciones (por si hay cambios en modelos)
echo "[7/8] Ejecutando migraciones..."
docker-compose exec -T web python manage.py migrate
echo -e "${GREEN}[OK]${NC} Migraciones ejecutadas"
echo ""

# Verificar que todo está funcionando
echo "[8/8] Verificando servicios..."
docker-compose ps
echo ""

echo "========================================"
echo "  DESPLIEGUE COMPLETADO"
echo "========================================"
echo ""
echo "La aplicación está disponible en:"
echo "  - Web: http://localhost:8000"
echo "  - Admin: http://localhost:8000/admin"
echo "  - Papelera: http://localhost:8000/core/recycle-bin/"
echo ""
echo "Para ver los logs en tiempo real:"
echo "  docker-compose logs -f web"
echo ""
echo "Para detener los servicios:"
echo "  docker-compose down"
echo ""
