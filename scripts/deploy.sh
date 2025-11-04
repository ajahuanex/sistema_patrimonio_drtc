#!/bin/bash

# Deployment Script for Sistema de Registro de Patrimonio
# This script handles the complete deployment process

set -e

# Configuration
DOMAIN=${1:-"your-domain.com"}
EMAIL=${2:-"admin@your-domain.com"}
ENVIRONMENT=${3:-"production"}

echo "Starting deployment for $ENVIRONMENT environment"
echo "Domain: $DOMAIN"
echo "Email: $EMAIL"

# Check if .env.prod exists
if [ ! -f .env.prod ]; then
    echo "Error: .env.prod file not found!"
    echo "Please copy .env.prod.example to .env.prod and configure it."
    exit 1
fi

# Load environment variables
export $(cat .env.prod | grep -v '^#' | xargs)

# Create necessary directories
echo "Creating directories..."
mkdir -p logs backups nginx/logs certbot/conf certbot/www

# Set permissions
chmod +x scripts/*.sh

# Pull latest images
echo "Pulling latest Docker images..."
docker-compose -f docker-compose.prod.yml pull

# Build application image
echo "Building application image..."
docker-compose -f docker-compose.prod.yml build

# Stop existing containers
echo "Stopping existing containers..."
docker-compose -f docker-compose.prod.yml down

# Start database and redis first
echo "Starting database and redis..."
docker-compose -f docker-compose.prod.yml up -d db redis

# Wait for database to be ready
echo "Waiting for database to be ready..."
sleep 30

# Run migrations
echo "Running database migrations..."
docker-compose -f docker-compose.prod.yml run --rm web python manage.py migrate

# Create superuser if it doesn't exist
echo "Creating superuser..."
docker-compose -f docker-compose.prod.yml run --rm web python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', '$EMAIL', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
EOF

# Collect static files
echo "Collecting static files..."
docker-compose -f docker-compose.prod.yml run --rm web python manage.py collectstatic --noinput

# Setup SSL certificates
if [ "$ENVIRONMENT" = "production" ]; then
    echo "Setting up SSL certificates..."
    ./scripts/setup-ssl.sh $DOMAIN $EMAIL
else
    echo "Skipping SSL setup for non-production environment"
    # Start all services without SSL
    docker-compose -f docker-compose.prod.yml up -d
fi

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 30

# Health check
echo "Performing health check..."
if curl -f http://localhost/health/ > /dev/null 2>&1; then
    echo "✓ Health check passed"
else
    echo "✗ Health check failed"
    echo "Checking logs..."
    docker-compose -f docker-compose.prod.yml logs web
    exit 1
fi

# Setup backup cron job
echo "Setting up backup cron job..."
(crontab -l 2>/dev/null; echo "0 2 * * * cd $(pwd) && ./scripts/backup.sh") | crontab -

# Display deployment information
echo ""
echo "========================================="
echo "Deployment completed successfully!"
echo "========================================="
echo ""
echo "Services:"
echo "- Web application: http://$DOMAIN"
if [ "$ENVIRONMENT" = "production" ]; then
    echo "- Secure web: https://$DOMAIN"
fi
echo "- Admin interface: http://$DOMAIN/admin/"
echo "- API documentation: http://$DOMAIN/api/"
echo "- Health check: http://$DOMAIN/health/"
echo ""
echo "Default admin credentials:"
echo "- Username: admin"
echo "- Password: admin123"
echo "- Email: $EMAIL"
echo ""
echo "IMPORTANT: Change the default admin password!"
echo ""
echo "Logs location: ./logs/"
echo "Backups location: ./backups/"
echo ""
echo "To view logs: docker-compose -f docker-compose.prod.yml logs -f"
echo "To stop services: docker-compose -f docker-compose.prod.yml down"
echo "To restart services: docker-compose -f docker-compose.prod.yml restart"
echo ""