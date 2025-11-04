@echo off
REM Backup Script for Sistema de Registro de Patrimonio (Windows)
REM This script creates backups of database and media files

setlocal enabledelayedexpansion

REM Configuration
set BACKUP_DIR=.\backups
set RETENTION_DAYS=30

REM Get current date and time
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%" & set "Sec=%dt:~12,2%"
set "DATE=%YYYY%%MM%%DD%_%HH%%Min%%Sec%"

echo Starting backup process...

REM Create backup directory
if not exist %BACKUP_DIR% mkdir %BACKUP_DIR%

REM Load environment variables from .env.prod
if exist .env.prod (
    for /f "usebackq tokens=1,2 delims==" %%a in (".env.prod") do (
        if not "%%a"=="" if not "%%a:~0,1%"=="#" (
            set "%%a=%%b"
        )
    )
)

REM Database backup
echo Creating database backup...
docker-compose -f docker-compose.prod.yml exec -T db pg_dump -U %POSTGRES_USER% -d %POSTGRES_DB% --no-owner --no-privileges --clean --if-exists > %BACKUP_DIR%\db_backup_%DATE%.sql

REM Compress database backup using PowerShell
echo Compressing database backup...
powershell -Command "Compress-Archive -Path '%BACKUP_DIR%\db_backup_%DATE%.sql' -DestinationPath '%BACKUP_DIR%\db_backup_%DATE%.zip'"
del %BACKUP_DIR%\db_backup_%DATE%.sql

REM Media files backup
echo Creating media files backup...
docker run --rm -v patrimonio_media_files:/data -v %cd%\%BACKUP_DIR%:/backup alpine tar czf /backup/media_backup_%DATE%.tar.gz -C /data .

REM Static files backup
echo Creating static files backup...
docker run --rm -v patrimonio_static_files:/data -v %cd%\%BACKUP_DIR%:/backup alpine tar czf /backup/static_backup_%DATE%.tar.gz -C /data .

REM Configuration backup
echo Creating configuration backup...
powershell -Command "Compress-Archive -Path 'docker-compose.prod.yml','nginx\','scripts\','.env.prod' -DestinationPath '%BACKUP_DIR%\config_backup_%DATE%.zip'"

REM Clean old backups (older than retention days)
echo Cleaning old backups (older than %RETENTION_DAYS% days)...
forfiles /p %BACKUP_DIR% /s /m *.zip /d -%RETENTION_DAYS% /c "cmd /c del @path" 2>nul
forfiles /p %BACKUP_DIR% /s /m *.tar.gz /d -%RETENTION_DAYS% /c "cmd /c del @path" 2>nul

REM Generate backup report
echo Generating backup report...
(
echo Backup Report - %DATE%
echo =====================
echo.
echo Database Backup: db_backup_%DATE%.zip
echo Media Backup: media_backup_%DATE%.tar.gz
echo Static Backup: static_backup_%DATE%.tar.gz
echo Config Backup: config_backup_%DATE%.zip
echo.
echo Backup completed at: %date% %time%
) > %BACKUP_DIR%\backup_report_%DATE%.txt

echo Backup completed successfully!
echo Backup files created:
dir %BACKUP_DIR%\*_%DATE%.*