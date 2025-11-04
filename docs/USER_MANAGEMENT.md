# Sistema de Gestión de Usuarios y Permisos

## Descripción General

El sistema de gestión de usuarios implementa un control de acceso basado en roles (RBAC) que permite administrar usuarios y sus permisos de manera granular según su función en la organización.

## Roles de Usuario

### 1. Administrador
- **Descripción**: Acceso completo al sistema
- **Permisos**:
  - Gestionar usuarios (crear, editar, activar/desactivar)
  - Gestionar catálogo y oficinas
  - Crear, editar y eliminar bienes patrimoniales
  - Importar y exportar datos
  - Generar reportes y códigos QR
  - Ver registros de auditoría
  - Acceso al panel de administración Django

### 2. Funcionario
- **Descripción**: Gestión operativa del inventario
- **Permisos**:
  - Crear y editar bienes patrimoniales
  - Importar y exportar datos
  - Generar reportes y códigos QR
  - Actualizar información desde dispositivos móviles
  - Ver catálogo y oficinas (solo lectura)

### 3. Auditor
- **Descripción**: Supervisión y generación de reportes
- **Permisos**:
  - Ver todos los bienes patrimoniales (solo lectura)
  - Generar y exportar reportes
  - Ver registros de auditoría
  - Ver catálogo y oficinas (solo lectura)

### 4. Consulta
- **Descripción**: Acceso básico de solo lectura
- **Permisos**:
  - Ver bienes patrimoniales (solo lectura)
  - Ver catálogo y oficinas (solo lectura)
  - Generar reportes básicos (solo lectura)

## Funcionalidades Implementadas

### Gestión de Usuarios
- **Lista de usuarios**: Visualización con filtros por rol, estado y búsqueda
- **Crear usuario**: Formulario completo con asignación de rol y oficina
- **Editar usuario**: Actualización de datos personales y profesionales
- **Activar/Desactivar**: Control de estado sin eliminar el historial
- **Resetear contraseña**: Función para administradores

### Sistema de Auditoría
- **Registro automático**: Todas las acciones importantes se registran
- **Información capturada**:
  - Usuario que realizó la acción
  - Tipo de acción (crear, actualizar, eliminar, etc.)
  - Modelo/objeto afectado
  - Cambios realizados (JSON)
  - Dirección IP y User Agent
  - Fecha y hora exacta

### Middleware de Seguridad
- **PermissionMiddleware**: Verifica permisos por URL
- **AuditMiddleware**: Registra acciones automáticamente

## Configuración Inicial

### 1. Ejecutar Migraciones
```bash
python manage.py migrate
```

### 2. Configurar Grupos y Permisos
```bash
python manage.py setup_permissions
```

### 3. Crear Superusuario
```bash
python manage.py createsuperuser
```

## URLs Disponibles

### Interfaz Web (Django Templates)
- `/core/usuarios/` - Lista de usuarios
- `/core/usuarios/crear/` - Crear nuevo usuario
- `/core/usuarios/<id>/` - Detalle de usuario
- `/core/usuarios/<id>/editar/` - Editar usuario
- `/core/auditoria/` - Registros de auditoría

### API REST (para React)
- `GET /core/api/usuarios/` - Listar usuarios
- `POST /core/api/usuarios/crear/` - Crear usuario

## Uso en Vistas

### Decoradores
```python
from apps.core.permissions import role_required, permission_required_custom

@role_required(['administrador'])
def admin_only_view(request):
    # Solo administradores pueden acceder
    pass

@permission_required_custom('can_create_bienes')
def create_bien_view(request):
    # Solo usuarios que pueden crear bienes
    pass
```

### Mixins para Class-Based Views
```python
from apps.core.permissions import RoleRequiredMixin, PermissionRequiredMixin

class AdminOnlyView(RoleRequiredMixin, View):
    allowed_roles = ['administrador']

class CreateBienView(PermissionRequiredMixin, View):
    permission_method = 'can_create_bienes'
```

### Permisos en Django REST Framework
```python
from apps.core.permissions import IsAdministrador, CanCreateBienes

class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdministrador]

class BienViewSet(viewsets.ModelViewSet):
    permission_classes = [CanCreateBienes]
```

## Verificación en Templates

```html
{% if user.profile.is_administrador %}
    <a href="{% url 'core:user_list' %}">Gestión de Usuarios</a>
{% endif %}

{% if user.profile.can_create_bienes %}
    <button>Crear Bien</button>
{% endif %}
```

## Utilidades Disponibles

### Funciones de Utilidad
```python
from apps.core.utils import (
    create_user_with_profile,
    update_user_role,
    deactivate_user,
    activate_user,
    get_user_permissions_summary
)

# Crear usuario con perfil
user, error = create_user_with_profile(
    username='nuevo_usuario',
    email='usuario@example.com',
    password='password123',
    role='funcionario'
)

# Obtener resumen de permisos
permissions = get_user_permissions_summary(user)
```

## Seguridad

### Características de Seguridad
- **Validación de datos**: Verificación de unicidad de username y email
- **Contraseñas seguras**: Validadores de Django aplicados
- **Auditoría completa**: Registro de todas las acciones importantes
- **Control de acceso**: Middleware que verifica permisos por URL
- **Desactivación segura**: Los usuarios se desactivan sin perder historial

### Consideraciones
- Los superusuarios de Django mantienen acceso completo
- Los logs de auditoría solo pueden ser eliminados por administradores
- Las contraseñas nunca se almacenan en logs de auditoría
- El middleware de permisos se ejecuta después de la autenticación

## Pruebas

Ejecutar las pruebas del sistema:
```bash
python manage.py test apps.core.tests
```

Las pruebas cubren:
- Creación automática de perfiles
- Verificación de permisos por rol
- Actualización de roles
- Acceso a vistas protegidas
- Creación de logs de auditoría
- Asignación automática a grupos
- Validación de datos de usuario