@echo off
REM Script para desplegar el sistema de patrimonio en Docker local (Windows)

echo ========================================
echo Sistema de Registro de Patrimonio DRTC
echo Despliegue Local con Docker
echo ========================================
echo.

REM Verificar que Docker está corriendo
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker no está corriendo. Por favor inicia Docker Desktop.
    pause
    exit /b 1
)

echo [1/6] Copiando archivo de configuración...
copy .env.local .env

echo.
echo [2/6] Deteniendo contenedores existentes...
docker-compose down

echo.
echo [3/6] Construyendo imágenes...
docker-compose build

echo.
echo [4/6] Iniciando servicios...
docker-compose up -d

echo.
echo [5/6] Esperando a que los servicios estén listos...
timeout /t 10 /nobreak >nul

echo.
echo [6/6] Ejecutando migraciones y creando superusuario...
docker-compose exec -T web python manage.py migrate
docker-compose exec -T web python manage.py collectstatic --noinput

echo.
echo ========================================
echo Despliegue completado exitosamente!
echo ========================================
echo.
echo Servicios disponibles:
echo - Aplicación web: http://localhost:8000
echo - Admin Django: http://localhost:8000/admin
echo - PostgreSQL: localhost:5432
echo - Redis: localhost:6379
echo.
echo Para crear un superusuario, ejecuta:
echo docker-compose exec web python manage.py createsuperuser
echo.
echo Para ver los logs:
echo docker-compose logs -f web
echo.
echo Para detener los servicios:
echo docker-compose down
echo.
pause
