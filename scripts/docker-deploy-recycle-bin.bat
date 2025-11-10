@echo off
REM Script de despliegue para Sistema de Papelera de Reciclaje en Docker
REM Windows Batch Script

echo ========================================
echo   Despliegue de Papelera de Reciclaje
echo   Sistema de Patrimonio DRTC
echo ========================================
echo.

REM Verificar que Docker está corriendo
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker no esta corriendo. Por favor inicia Docker Desktop.
    pause
    exit /b 1
)

echo [1/8] Verificando Docker...
echo [OK] Docker esta corriendo
echo.

REM Detener contenedores actuales
echo [2/8] Deteniendo contenedores actuales...
docker-compose down
echo [OK] Contenedores detenidos
echo.

REM Reconstruir la imagen web con los nuevos archivos
echo [3/8] Reconstruyendo imagen web...
docker-compose build web
if errorlevel 1 (
    echo [ERROR] Fallo al construir la imagen
    pause
    exit /b 1
)
echo [OK] Imagen reconstruida
echo.

REM Iniciar servicios
echo [4/8] Iniciando servicios...
docker-compose up -d
if errorlevel 1 (
    echo [ERROR] Fallo al iniciar servicios
    pause
    exit /b 1
)
echo [OK] Servicios iniciados
echo.

REM Esperar a que los servicios estén listos
echo [5/8] Esperando a que los servicios esten listos...
timeout /t 10 /nobreak >nul
echo [OK] Servicios listos
echo.

REM Recolectar archivos estáticos (incluye el nuevo CSS)
echo [6/8] Recolectando archivos estaticos...
docker-compose exec -T web python manage.py collectstatic --noinput
if errorlevel 1 (
    echo [ADVERTENCIA] Fallo al recolectar estaticos, intentando de nuevo...
    timeout /t 5 /nobreak >nul
    docker-compose exec -T web python manage.py collectstatic --noinput
)
echo [OK] Archivos estaticos recolectados
echo.

REM Ejecutar migraciones (por si hay cambios en modelos)
echo [7/8] Ejecutando migraciones...
docker-compose exec -T web python manage.py migrate
echo [OK] Migraciones ejecutadas
echo.

REM Verificar que todo está funcionando
echo [8/8] Verificando servicios...
docker-compose ps
echo.

echo ========================================
echo   DESPLIEGUE COMPLETADO
echo ========================================
echo.
echo La aplicacion esta disponible en:
echo   - Web: http://localhost:8000
echo   - Admin: http://localhost:8000/admin
echo   - Papelera: http://localhost:8000/core/recycle-bin/
echo.
echo Para ver los logs en tiempo real:
echo   docker-compose logs -f web
echo.
echo Para detener los servicios:
echo   docker-compose down
echo.

pause
