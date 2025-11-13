@echo off
echo ==========================================
echo Verificando Puertos para Despliegue
echo ==========================================
echo.

echo Verificando puerto 80 (HTTP/Nginx)...
netstat -ano | findstr ":80 " >nul 2>&1
if %errorlevel% equ 0 (
    echo [X] Puerto 80 OCUPADO
    netstat -ano | findstr ":80 "
) else (
    echo [OK] Puerto 80 LIBRE
)
echo.

echo Verificando puerto 5432 (PostgreSQL)...
netstat -ano | findstr ":5432 " >nul 2>&1
if %errorlevel% equ 0 (
    echo [X] Puerto 5432 OCUPADO
    netstat -ano | findstr ":5432 "
) else (
    echo [OK] Puerto 5432 LIBRE
)
echo.

echo Verificando puerto 6379 (Redis)...
netstat -ano | findstr ":6379 " >nul 2>&1
if %errorlevel% equ 0 (
    echo [X] Puerto 6379 OCUPADO
    netstat -ano | findstr ":6379 "
) else (
    echo [OK] Puerto 6379 LIBRE
)
echo.

echo ==========================================
echo Verificacion completa
echo ==========================================
pause
