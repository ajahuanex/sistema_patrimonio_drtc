#!/bin/bash

echo "=========================================="
echo "Verificando Puertos para Despliegue"
echo "=========================================="
echo ""

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para verificar puerto
check_port() {
    local port=$1
    local service=$2
    
    if sudo lsof -i :$port > /dev/null 2>&1; then
        echo -e "${RED}✗ Puerto $port ($service) OCUPADO${NC}"
        echo "  Proceso usando el puerto:"
        sudo lsof -i :$port | grep LISTEN
        echo ""
        return 1
    else
        echo -e "${GREEN}✓ Puerto $port ($service) LIBRE${NC}"
        return 0
    fi
}

# Verificar puertos
all_free=true

check_port 80 "HTTP/Nginx" || all_free=false
check_port 443 "HTTPS/Nginx" || all_free=false
check_port 5432 "PostgreSQL" || all_free=false
check_port 6379 "Redis" || all_free=false
check_port 8000 "Django" || all_free=false

echo ""
echo "=========================================="

if [ "$all_free" = true ]; then
    echo -e "${GREEN}✓ Todos los puertos están libres${NC}"
    echo -e "${GREEN}✓ Puedes proceder con el despliegue${NC}"
    exit 0
else
    echo -e "${RED}✗ Algunos puertos están ocupados${NC}"
    echo ""
    echo "Soluciones:"
    echo "  - Detener servicios: sudo systemctl stop nginx postgresql redis"
    echo "  - O usar: docker compose down"
    echo ""
    exit 1
fi
