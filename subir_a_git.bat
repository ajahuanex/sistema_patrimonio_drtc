@echo off
echo ========================================
echo   Subir Cambios a GitHub
echo ========================================
echo.

REM Ver estado actual
echo [1/4] Verificando estado de Git...
git status
echo.

REM Agregar todos los cambios
echo [2/4] Agregando archivos...
git add .
echo.

REM Pedir mensaje de commit
set /p mensaje="Ingresa el mensaje del commit: "
echo.

REM Hacer commit
echo [3/4] Haciendo commit...
git commit -m "%mensaje%"
echo.

REM Subir a GitHub
echo [4/4] Subiendo a GitHub...
git push origin main
echo.

echo ========================================
echo   Cambios subidos exitosamente!
echo ========================================
echo.
echo Ahora puedes ir a Ubuntu y ejecutar:
echo   cd /ruta/del/proyecto
echo   git pull origin main
echo   ./desplegar_servidor.sh
echo.

pause
