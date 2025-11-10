@echo off
REM Script para crear superusuario en Docker
REM Windows Batch Script

echo ========================================
echo   Crear Superusuario
echo   Sistema de Patrimonio DRTC
echo ========================================
echo.

echo Creando superusuario con credenciales por defecto...
echo Usuario: admin
echo Password: admin123
echo.

docker-compose exec -T web python manage.py shell << EOF
from django.contrib.auth import get_user_model
from apps.core.models import UserProfile

User = get_user_model()

# Eliminar usuario admin si existe
if User.objects.filter(username='admin').exists():
    User.objects.filter(username='admin').delete()
    print('Usuario admin anterior eliminado')

# Crear nuevo superusuario
user = User.objects.create_superuser(
    username='admin',
    email='admin@drtc.gob.pe',
    password='admin123',
    first_name='Administrador',
    last_name='Sistema'
)

# Crear o actualizar perfil
profile, created = UserProfile.objects.get_or_create(user=user)
profile.rol = 'administrador'
profile.telefono = '051-123456'
profile.cargo = 'Administrador del Sistema'
profile.save()

print('Superusuario creado exitosamente!')
print('Usuario: admin')
print('Password: admin123')
print('Email: admin@drtc.gob.pe')
EOF

echo.
echo ========================================
echo   SUPERUSUARIO CREADO
echo ========================================
echo.
echo Credenciales:
echo   Usuario: admin
echo   Password: admin123
echo.
echo Accede en: http://localhost:8000/admin
echo.

pause
