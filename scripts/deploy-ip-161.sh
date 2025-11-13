#!/bin/bash

# ============================================================================
# Script de Despliegue Automatizado para IP 161.132.47.92
# Sistema de Registro de Patrimonio DRTC Puno
# ============================================================================

set -e  # Detener en caso de error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Función para imprimir con color
print_step() {
    echo -e "\n${CYAN}============================================================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}============================================================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Banner
clear
echo -e "${MAGENTA}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║   Sistema de Registro de Patrimonio DRTC Puno                       ║
║   Script de Despliegue Automatizado                                 ║
║   IP: 161.132.47.92                                                  ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}\n"

# ============================================================================
# PASO 1: Verificar requisitos
# ============================================================================
print_step "PASO 1: Verificando requisitos del sistema"

# Verificar Docker
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    print_success "Docker instalado: $DOCKER_VERSION"
else
    print_error "Docker no está instalado"
    exit 1
fi

# Verificar Docker Compose
if docker compose version &> /dev/null; then
    COMPOSE_VERSION=$(docker compose version)
    print_success "Docker Compose instalado: $COMPOSE_VERSION"
else
    print_error "Docker Compose no está instalado"
    exit 1
fi

# Verificar Git
if command -v git &> /dev/null; then
    GIT_VERSION=$(git --version)
    print_success "Git instalado: $GIT_VERSION"
else
    print_error "Git no está instalado"
    exit 1
fi

# ============================================================================
# PASO 2: Verificar/Crear archivo .env.prod
# ============================================================================
print_step "PASO 2: Configurando variables de entorno"

if [ -f ".env.prod" ]; then
    print_warning "Archivo .env.prod ya existe"
    read -p "¿Deseas sobrescribirlo? (s/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        print_info "Usando archivo .env.prod existente"
    else
        rm .env.prod
        print_info "Generando nuevo archivo .env.prod..."
        
        # Generar claves
        SECRET_KEY=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())" 2>/dev/null || openssl rand -base64 50 | tr -d "=+/" | cut -c1-50)
        POSTGRES_PASSWORD=$(openssl rand -base64 24 | tr -d "=+/" | cut -c1-24)
        REDIS_PASSWORD=$(openssl rand -base64 24 | tr -d "=+/" | cut -c1-24)
        PERMANENT_DELETE_CODE=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
        
        # Solicitar información
        read -p "Email para notificaciones: " EMAIL_USER
        read -sp "Contraseña de aplicación de Gmail: " EMAIL_PASSWORD
        echo
        
        # Crear archivo
        cp .env.prod.ip-only .env.prod
        sed -i "s|SECRET_KEY=.*|SECRET_KEY=$SECRET_KEY|g" .env.prod
        sed -i "s|POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$POSTGRES_PASSWORD|g" .env.prod
        sed -i "s|REDIS_PASSWORD=.*|REDIS_PASSWORD=$REDIS_PASSWORD|g" .env.prod
        sed -i "s|PERMANENT_DELETE_CODE=.*|PERMANENT_DELETE_CODE=$PERMANENT_DELETE_CODE|g" .env.prod
        sed -i "s|EMAIL_HOST_USER=.*|EMAIL_HOST_USER=$EMAIL_USER|g" .env.prod
        sed -i "s|EMAIL_HOST_PASSWORD=.*|EMAIL_HOST_PASSWORD=$EMAIL_PASSWORD|g" .env.prod
        sed -i "s|DEFAULT_FROM_EMAIL=.*|DEFAULT_FROM_EMAIL=Sistema Patrimonio DRTC <$EMAIL_USER>|g" .env.prod
        
        print_success "Archivo .env.prod generado"
        
        # Mostrar credenciales
        echo -e "\n${YELLOW}GUARDA ESTAS CREDENCIALES EN UN LUGAR SEGURO:${NC}"
        echo "SECRET_KEY: $SECRET_KEY"
        echo "POSTGRES_PASSWORD: $POSTGRES_PASSWORD"
        echo "REDIS_PASSWORD: $REDIS_PASSWORD"
        echo "PERMANENT_DELETE_CODE: $PERMANENT_DELETE_CODE"
        echo ""
        read -p "Presiona Enter para continuar..."
    fi
else
    print_info "Generando archivo .env.prod..."
    
    # Generar claves
    SECRET_KEY=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())" 2>/dev/null || openssl rand -base64 50 | tr -d "=+/" | cut -c1-50)
    POSTGRES_PASSWORD=$(openssl rand -base64 24 | tr -d "=+/" | cut -c1-24)
    REDIS_PASSWORD=$(openssl rand -base64 24 | tr -d "=+/" | cut -c1-24)
    PERMANENT_DELETE_CODE=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
    
    # Solicitar información
    read -p "Email para notificaciones: " EMAIL_USER
    read -sp "Contraseña de aplicación de Gmail: " EMAIL_PASSWORD
    echo
    
    # Crear archivo
    cp .env.prod.ip-only .env.prod
    sed -i "s|SECRET_KEY=.*|SECRET_KEY=$SECRET_KEY|g" .env.prod
    sed -i "s|POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$POSTGRES_PASSWORD|g" .env.prod
    sed -i "s|REDIS_PASSWORD=.*|REDIS_PASSWORD=$REDIS_PASSWORD|g" .env.prod
    sed -i "s|PERMANENT_DELETE_CODE=.*|PERMANENT_DELETE_CODE=$PERMANENT_DELETE_CODE|g" .env.prod
    sed -i "s|EMAIL_HOST_USER=.*|EMAIL_HOST_USER=$EMAIL_USER|g" .env.prod
    sed -i "s|EMAIL_HOST_PASSWORD=.*|EMAIL_HOST_PASSWORD=$EMAIL_PASSWORD|g" .env.prod
    sed -i "s|DEFAULT_FROM_EMAIL=.*|DEFAULT_FROM_EMAIL=Sistema Patrimonio DRTC <$EMAIL_USER>|g" .env.prod
    
    print_success "Archivo .env.prod generado"
    
    # Mostrar credenciales
    echo -e "\n${YELLOW}GUARDA ESTAS CREDENCIALES EN UN LUGAR SEGURO:${NC}"
    echo "SECRET_KEY: $SECRET_KEY"
    echo "POSTGRES_PASSWORD: $POSTGRES_PASSWORD"
    echo "REDIS_PASSWORD: $REDIS_PASSWORD"
    echo "PERMANENT_DELETE_CODE: $PERMANENT_DELETE_CODE"
    echo ""
    read -p "Presiona Enter para continuar..."
fi

# ============================================================================
# PASO 3: Configurar Nginx
# ============================================================================
print_step "PASO 3: Configurando Nginx para HTTP"

cp nginx/nginx.http-only.conf nginx/nginx.prod.conf
print_success "Configuración de Nginx copiada"

# ============================================================================
# PASO 4: Crear directorios
# ============================================================================
print_step "PASO 4: Creando directorios necesarios"

mkdir -p logs backups nginx/logs
chmod -R 755 logs backups nginx/logs
print_success "Directorios creados: logs, backups, nginx/logs"

# ============================================================================
# PASO 5: Detener servicios existentes (si existen)
# ============================================================================
print_step "PASO 5: Deteniendo servicios existentes (si existen)"

if docker compose -f docker-compose.prod.yml ps | grep -q "Up"; then
    print_info "Deteniendo servicios existentes..."
    docker compose -f docker-compose.prod.yml down
    print_success "Servicios detenidos"
else
    print_info "No hay servicios corriendo"
fi

# ============================================================================
# PASO 6: Construir imágenes
# ============================================================================
print_step "PASO 6: Construyendo imágenes Docker"

print_info "Este proceso puede tardar 5-10 minutos..."
docker compose -f docker-compose.prod.yml build
print_success "Imágenes construidas exitosamente"

# ============================================================================
# PASO 7: Iniciar servicios
# ============================================================================
print_step "PASO 7: Iniciando servicios"

docker compose -f docker-compose.prod.yml up -d
print_success "Servicios iniciados"

# ============================================================================
# PASO 8: Esperar a que los servicios estén healthy
# ============================================================================
print_step "PASO 8: Esperando a que los servicios estén listos"

print_info "Esperando 60 segundos para que los servicios inicien..."
for i in {60..1}; do
    echo -ne "${BLUE}Tiempo restante: $i segundos\r${NC}"
    sleep 1
done
echo ""

print_info "Verificando estado de los servicios..."
docker compose -f docker-compose.prod.yml ps

# Verificar health checks
print_info "Verificando health checks..."
sleep 10

UNHEALTHY=$(docker compose -f docker-compose.prod.yml ps | grep -c "unhealthy" || true)
if [ "$UNHEALTHY" -gt 0 ]; then
    print_warning "Algunos servicios están unhealthy. Esperando 30 segundos más..."
    sleep 30
fi

# ============================================================================
# PASO 9: Ejecutar migraciones
# ============================================================================
print_step "PASO 9: Ejecutando migraciones de base de datos"

docker compose -f docker-compose.prod.yml exec -T web python manage.py migrate
print_success "Migraciones ejecutadas"

# ============================================================================
# PASO 10: Crear superusuario
# ============================================================================
print_step "PASO 10: Crear superusuario"

print_info "Ingresa los datos del superusuario:"
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
print_success "Superusuario creado"

# ============================================================================
# PASO 11: Recolectar archivos estáticos
# ============================================================================
print_step "PASO 11: Recolectando archivos estáticos"

docker compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput
print_success "Archivos estáticos recolectados"

# ============================================================================
# PASO 12: Verificar health checks
# ============================================================================
print_step "PASO 12: Verificando health checks"

print_info "Health check básico:"
curl -s http://localhost/health/ | python3 -m json.tool || echo "Error en health check"

echo ""
print_info "Health check detallado:"
curl -s http://localhost/health/detailed/ | python3 -m json.tool || echo "Error en health check detallado"

# ============================================================================
# PASO 13: Mostrar estado final
# ============================================================================
print_step "PASO 13: Estado final de los servicios"

docker compose -f docker-compose.prod.yml ps

# ============================================================================
# RESUMEN FINAL
# ============================================================================
echo -e "\n${GREEN}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║   ✓ DESPLIEGUE COMPLETADO EXITOSAMENTE                              ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}\n"

print_success "Aplicación desplegada en: http://161.132.47.92"
print_success "Panel de administración: http://161.132.47.92/admin/"
print_success "Health check: http://161.132.47.92/health/detailed/"

echo -e "\n${YELLOW}Comandos útiles:${NC}"
echo "  Ver logs:      docker compose -f docker-compose.prod.yml logs -f"
echo "  Reiniciar:     docker compose -f docker-compose.prod.yml restart"
echo "  Detener:       docker compose -f docker-compose.prod.yml down"
echo "  Estado:        docker compose -f docker-compose.prod.yml ps"

echo -e "\n${YELLOW}Archivos importantes:${NC}"
echo "  Logs:          ./logs/"
echo "  Backups:       ./backups/"
echo "  Config:        .env.prod"

echo -e "\n${GREEN}¡Listo para usar!${NC}\n"
