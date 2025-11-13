@echo off
REM ################################################################################
REM Sistema de Backups Automáticos - Sistema de Registro de Patrimonio DRTC Puno
REM 
REM Este script realiza backups automáticos de:
REM - Base de datos PostgreSQL (pg_dump con compresión gzip)
REM - Archivos media (tar.gz)
REM - Limpieza automática de backups antiguos (>7 días)
REM ################################################################################

setlocal enabledelayedexpansion

REM Configuración
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..
set BACKUP_DIR=%PROJECT_ROOT%\backups
set DB_BACKUP_DIR=%BACKUP_DIR%\db
set MEDIA_BACKUP_DIR=%BACKUP_DIR%\media
set LOG_DIR=%PROJECT_ROOT%\logs
set BACKUP_LOG=%LOG_DIR%\backup.log
set RETENTION_DAYS=7

REM Obtener timestamp
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set TIMESTAMP=%datetime:~0,8%_%datetime:~8,6%

echo ==========================================
echo Iniciando proceso de backup - %TIMESTAMP%
echo ==========================================

REM Crear estructura de directorios
if not exist "%DB_BACKUP_DIR%" mkdir "%DB_BACKUP_DIR%"
if not exist "%MEDIA_BACKUP_DIR%" mkdir "%MEDIA_BACKUP_DIR%"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

echo [INFO] Directorios de backup creados >> "%BACKUP_LOG%"

REM Cargar variables de entorno
if not exist "%PROJECT_ROOT%\.env.prod" (
    echo [ERROR] Archivo .env.prod no encontrado
    echo [ERROR] Archivo .env.prod no encontrado >> "%BACKUP_LOG%"
    exit /b 1
)

REM Verificar Docker
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker no está corriendo
    echo [ERROR] Docker no está corriendo >> "%BACKUP_LOG%"
    exit /b 1
)

echo [INFO] Docker verificado correctamente
echo [INFO] Docker verificado correctamente >> "%BACKUP_LOG%"

REM Backup de base de datos
echo [INFO] Iniciando backup de base de datos...
echo [INFO] Iniciando backup de base de datos... >> "%BACKUP_LOG%"

set DB_BACKUP_FILE=%DB_BACKUP_DIR%\patrimonio_%TIMESTAMP%.sql

docker-compose -f "%PROJECT_ROOT%\docker-compose.prod.yml" exec -T db pg_dump -U postgres patrimonio > "%DB_BACKUP_FILE%"

if errorlevel 1 (
    echo [ERROR] Error al realizar dump de base de datos
    echo [ERROR] Error al realizar dump de base de datos >> "%BACKUP_LOG%"
    set BACKUP_FAILED=1
) else (
    echo [INFO] Dump de base de datos completado
    echo [INFO] Dump de base de datos completado >> "%BACKUP_LOG%"
    
    REM Comprimir con gzip (usando docker)
    docker run --rm -v "%DB_BACKUP_DIR%:/backup" alpine gzip "/backup/patrimonio_%TIMESTAMP%.sql"
    
    if errorlevel 1 (
        echo [ERROR] Error al comprimir backup
        echo [ERROR] Error al comprimir backup >> "%BACKUP_LOG%"
        set BACKUP_FAILED=1
    ) else (
        echo [INFO] Backup comprimido exitosamente
        echo [INFO] Backup comprimido exitosamente >> "%BACKUP_LOG%"
    )
)

REM Backup de archivos media
echo [INFO] Iniciando backup de archivos media...
echo [INFO] Iniciando backup de archivos media... >> "%BACKUP_LOG%"

if exist "%PROJECT_ROOT%\media" (
    set MEDIA_BACKUP_FILE=%MEDIA_BACKUP_DIR%\media_%TIMESTAMP%.tar.gz
    
    REM Usar docker para crear tar.gz
    docker run --rm -v "%PROJECT_ROOT%:/backup" alpine tar -czf "/backup/backups/media/media_%TIMESTAMP%.tar.gz" -C /backup media/
    
    if errorlevel 1 (
        echo [ERROR] Error al crear backup de media
        echo [ERROR] Error al crear backup de media >> "%BACKUP_LOG%"
        set BACKUP_FAILED=1
    ) else (
        echo [INFO] Backup de media completado
        echo [INFO] Backup de media completado >> "%BACKUP_LOG%"
    )
) else (
    echo [WARN] Directorio media no encontrado
    echo [WARN] Directorio media no encontrado >> "%BACKUP_LOG%"
)

REM Limpiar backups antiguos (más de 7 días)
echo [INFO] Limpiando backups antiguos...
echo [INFO] Limpiando backups antiguos... >> "%BACKUP_LOG%"

forfiles /P "%DB_BACKUP_DIR%" /M *.sql.gz /D -%RETENTION_DAYS% /C "cmd /c del @path" 2>nul
forfiles /P "%MEDIA_BACKUP_DIR%" /M *.tar.gz /D -%RETENTION_DAYS% /C "cmd /c del @path" 2>nul

echo [INFO] Limpieza de backups antiguos completada
echo [INFO] Limpieza de backups antiguos completada >> "%BACKUP_LOG%"

REM Mostrar estadísticas
echo ==========================================
echo Estadísticas de Backups
echo ==========================================

for /f %%A in ('dir /b "%DB_BACKUP_DIR%\*.sql.gz" 2^>nul ^| find /c /v ""') do set DB_COUNT=%%A
echo Backups de base de datos: %DB_COUNT% archivos

for /f %%A in ('dir /b "%MEDIA_BACKUP_DIR%\*.tar.gz" 2^>nul ^| find /c /v ""') do set MEDIA_COUNT=%%A
echo Backups de media: %MEDIA_COUNT% archivos

echo ==========================================

if defined BACKUP_FAILED (
    echo [ERROR] Backup completado con errores
    echo [ERROR] Backup completado con errores >> "%BACKUP_LOG%"
    exit /b 1
) else (
    echo [INFO] Backup completado exitosamente
    echo [INFO] Backup completado exitosamente >> "%BACKUP_LOG%"
    exit /b 0
)
