#!/bin/bash

# SSL Setup Script for Sistema de Registro de Patrimonio
# This script sets up Let's Encrypt SSL certificates

set -e

# Configuration
DOMAIN=${1:-"your-domain.com"}
EMAIL=${2:-"admin@your-domain.com"}
STAGING=${3:-0}

echo "Setting up SSL for domain: $DOMAIN"
echo "Email: $EMAIL"

# Create directories
mkdir -p ./certbot/conf
mkdir -p ./certbot/www
mkdir -p ./nginx/ssl

# Check if running in staging mode
if [ "$STAGING" = "1" ]; then
    echo "Running in STAGING mode"
    STAGING_ARG="--staging"
else
    echo "Running in PRODUCTION mode"
    STAGING_ARG=""
fi

# Stop any running containers
echo "Stopping existing containers..."
docker-compose -f docker-compose.prod.yml down

# Start nginx with temporary configuration
echo "Starting nginx with temporary configuration..."
cp nginx/nginx.temp.conf nginx/nginx.prod.conf
docker-compose -f docker-compose.prod.yml up -d nginx

# Wait for nginx to be ready
echo "Waiting for nginx to be ready..."
sleep 10

# Request certificate
echo "Requesting SSL certificate..."
docker-compose -f docker-compose.prod.yml run --rm certbot \
    certonly --webroot \
    --webroot-path=/var/www/certbot \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    $STAGING_ARG \
    -d $DOMAIN \
    -d www.$DOMAIN

# Update nginx configuration with SSL
echo "Updating nginx configuration with SSL..."
sed -i "s/your-domain.com/$DOMAIN/g" nginx/nginx.prod.conf

# Restart with SSL configuration
echo "Restarting with SSL configuration..."
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d

echo "SSL setup completed!"
echo "Your site should now be available at https://$DOMAIN"

# Set up automatic renewal
echo "Setting up automatic certificate renewal..."
(crontab -l 2>/dev/null; echo "0 12 * * * cd $(pwd) && docker-compose -f docker-compose.prod.yml run --rm certbot renew --quiet && docker-compose -f docker-compose.prod.yml exec nginx nginx -s reload") | crontab -

echo "Automatic renewal set up. Certificates will be renewed daily at 12:00 PM."