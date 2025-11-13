#!/bin/bash
set -e  # Detener si hay errores

echo "🚀 Desplegando Sistema de Patrimonio en Ubuntu"
echo "=============================================="

# Verificar que existe .env.prod
if [ ! -f ".env.prod" ]; then
    echo "❌ Error: No existe el archivo .env.prod"
    echo "Creando .env.prod con valores de prueba..."
    cat > .env.prod << 'EOF'
# Django Configuration
DEBUG=False
SECRET_KEY=django-insecure-test-key-change-this-in-production-12345678
ALLOWED_HOSTS=localhost,127.0.0.1
BASE_URL=http://localhost

# Database Configuration
POSTGRES_DB=patrimonio_db
POSTGRES_USER=patrimonio_user
POSTGRES_PASSWORD=patrimonio_pass_2024

# Redis Configuration
REDIS_PASSWORD=redis_pass_2024

# Email Configuration (opcional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=noreply@example.com
EMAIL_HOST_PASSWORD=email_password_here

# Application
APP_VERSION=1.0.0
EOF
    echo "✅ Archivo .env.prod creado"
fi

echo ""
echo "📋 Cargando variables de entorno..."
# Cargar variables en el shell actual
set -a  # Exportar automáticamente todas las variables
source .env.prod
set +a

echo "✅ Variables cargadas:"
echo "  - POSTGRES_DB: $POSTGRES_DB"
echo "  - POSTGRES_USER: $POSTGRES_USER"
echo "  - POSTGRES_PASSWORD: [configurado]"
echo "  - REDIS_PASSWORD: [configurado]"
echo ""

# Detener contenedores existentes
echo "🛑 Deteniendo contenedores existentes..."
docker compose -f docker-compose.simple.yml down -v 2>/dev/null || true

# Limpiar sistema
echo "🧹 Limpiando sistema Docker..."
docker system prune -f

# Verificar que las variables están disponibles
echo ""
echo "🔍 Verificando variables antes de iniciar..."
if [ -z "$POSTGRES_PASSWORD" ]; then
    echo "❌ ERROR: POSTGRES_PASSWORD no está definida"
    exit 1
fi
if [ -z "$REDIS_PASSWORD" ]; then
    echo "❌ ERROR: REDIS_PASSWORD no está definida"
    exit 1
fi
echo "✅ Variables verificadas correctamente"

# Iniciar servicios
echo ""
echo "🚀 Iniciando servicios..."
docker compose -f docker-compose.simple.yml --env-file .env.prod up -d

echo ""
echo "⏳ Esperando que los servicios estén listos (60 segundos)..."
sleep 60

echo ""
echo "📊 Estado de los contenedores:"
docker compose -f docker-compose.simple.yml ps

echo ""
echo "🔍 Verificando salud de los servicios..."
echo "- PostgreSQL:"
docker compose -f docker-compose.simple.yml exec -T db pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" && echo "  ✅ PostgreSQL está listo" || echo "  ❌ PostgreSQL no está listo"

echo "- Redis:"
docker compose -f docker-compose.simple.yml exec -T redis redis-cli -a "$REDIS_PASSWORD" ping && echo "  ✅ Redis está listo" || echo "  ❌ Redis no está listo"

echo ""
echo "📝 Comandos útiles:"
echo "  Ver logs:     docker compose -f docker-compose.simple.yml logs -f"
echo "  Ver logs db:  docker compose -f docker-compose.simple.yml logs db"
echo "  Ver logs web: docker compose -f docker-compose.simple.yml logs web"
echo "  Detener:      docker compose -f docker-compose.simple.yml down"
echo ""
echo "🌐 Si todo está bien, la aplicación estará en:"
echo "   http://localhost"
echo ""
echo "✅ Despliegue completado!"
