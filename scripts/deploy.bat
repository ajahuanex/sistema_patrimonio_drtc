@echo off
REM Deployment Script for Sistema de Registro de Patrimonio (Windows)
REM This script handles the complete deployment process

setlocal enabledelayedexpansion

set DOMAIN=%1
set EMAIL=%2
set ENVIRONMENT=%3

if "%DOMAIN%"=="" set DOMAIN=your-domain.com
if "%EMAIL%"=="" set EMAIL=admin@your-domain.com
if "%ENVIRONMENT%"=="" set ENVIRONMENT=production

echo Starting deployment for %ENVIRONMENT% environment
echo Domain: %DOMAIN%
echo Email: %EMAIL%

REM Check if .env.prod exists
if not exist .env.prod (
    echo Error: .env.prod file not found!
    echo Please copy .env.prod.example to .env.prod and configure it.
    exit /b 1
)

REM Create necessary directories
echo Creating directories...
if not exist logs mkdir logs
if not exist backups mkdir backups
if not exist nginx\logs mkdir nginx\logs
if not exist certbot\conf mkdir certbot\conf
if not exist certbot\www mkdir certbot\www

REM Pull latest images
echo Pulling latest Docker images...
docker-compose -f docker-compose.prod.yml pull

REM Build application image
echo Building application image...
docker-compose -f docker-compose.prod.yml build

REM Stop existing containers
echo Stopping existing containers...
docker-compose -f docker-compose.prod.yml down

REM Start database and redis first
echo Starting database and redis...
docker-compose -f docker-compose.prod.yml up -d db redis

REM Wait for database to be ready
echo Waiting for database to be ready...
timeout /t 30 /nobreak > nul

REM Run migrations
echo Running database migrations...
docker-compose -f docker-compose.prod.yml run --rm web python manage.py migrate

REM Collect static files
echo Collecting static files...
docker-compose -f docker-compose.prod.yml run --rm web python manage.py collectstatic --noinput

REM Start all services
echo Starting all services...
docker-compose -f docker-compose.prod.yml up -d

REM Wait for services to be ready
echo Waiting for services to be ready...
timeout /t 30 /nobreak > nul

echo.
echo =========================================
echo Deployment completed successfully!
echo =========================================
echo.
echo Services:
echo - Web application: http://%DOMAIN%
echo - Admin interface: http://%DOMAIN%/admin/
echo - API documentation: http://%DOMAIN%/api/
echo - Health check: http://%DOMAIN%/health/
echo.
echo Default admin credentials:
echo - Username: admin
echo - Password: admin123
echo - Email: %EMAIL%
echo.
echo IMPORTANT: Change the default admin password!
echo.
echo Logs location: .\logs\
echo Backups location: .\backups\
echo.
echo To view logs: docker-compose -f docker-compose.prod.yml logs -f
echo To stop services: docker-compose -f docker-compose.prod.yml down
echo To restart services: docker-compose -f docker-compose.prod.yml restart
echo.