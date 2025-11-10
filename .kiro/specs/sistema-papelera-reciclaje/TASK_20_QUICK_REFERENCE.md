# Task 20: Sistema de Permisos Granular - Guía Rápida

## Permisos por Rol

### 👑 Administrador
```python
✓ Ver papelera (todos los elementos)
✓ Ver logs de auditoría
✓ Restaurar cualquier elemento
✓ Restaurar en lote
✓ Eliminar permanentemente
✓ Eliminar permanentemente en lote
✓ Gestionar configuración
```

### 👤 Funcionario
```python
✓ Ver papelera (solo propios elementos)
✓ Restaurar propios elementos
✓ Restaurar en lote (solo propios)
✗ Ver elementos de otros
✗ Restaurar elementos de otros
✗ Eliminar permanentemente
✗ Ver logs de auditoría
```

### 📊 Auditor
```python
✓ Ver papelera (todos los elementos)
✓ Ver logs de auditoría
✗ Restaurar elementos
✗ Eliminar permanentemente
✗ Modificar configuración
```

### 👁️ Consulta
```python
✗ Sin acceso a papelera
```

## Comandos Rápidos

### Configurar Permisos
```bash
# Crear grupos de permisos
python manage.py setup_recycle_permissions

# Recrear grupos (elimina y recrea)
python manage.py setup_recycle_permissions --reset
```

### Asignar Usuarios
```bash
# Asignar usuario a rol
python manage.py assign_recycle_permissions admin administrador
python manage.py assign_recycle_permissions func1 funcionario
python manage.py assign_recycle_permissions audit1 auditor

# Remover usuario de rol
python manage.py assign_recycle_permissions func1 funcionario --remove
```

## Verificación de Permisos en Código

### En Vistas
```python
# Verificar permiso específico
if request.user.profile.can_view_recycle_bin():
    # Permitir acceso

# Verificar múltiples permisos
can_restore = request.user.profile.can_restore_items()
can_delete = request.user.profile.can_permanent_delete()
```

### En Templates
```django
{% if user.profile.can_restore_items %}
    <button>Restaurar</button>
{% endif %}

{% if user.profile.can_permanent_delete %}
    <button>Eliminar Permanentemente</button>
{% endif %}
```

### Con Decoradores
```python
from apps.core.permissions import permission_required_custom

@permission_required_custom('can_view_recycle_bin')
def my_view(request):
    # Vista protegida
    pass
```

## Métodos de Permisos Disponibles

```python
# Visualización
user.profile.can_view_recycle_bin()
user.profile.can_view_all_recycle_items()
user.profile.can_view_deletion_audit_logs()

# Restauración
user.profile.can_restore_items()
user.profile.can_restore_own_items()
user.profile.can_restore_others_items()
user.profile.can_bulk_restore()

# Eliminación
user.profile.can_permanent_delete()
user.profile.can_bulk_permanent_delete()

# Configuración
user.profile.can_manage_recycle_config()
```

## Clases de Permisos DRF

```python
from apps.core.permissions import (
    CanViewRecycleBin,
    CanViewAllRecycleItems,
    CanRestoreItems,
    CanRestoreOwnItems,
    CanRestoreOthersItems,
    CanPermanentDelete,
    CanViewDeletionAuditLogs,
    CanManageRecycleConfig,
    CanBulkRestore,
    CanBulkPermanentDelete,
)

# Uso en ViewSet
class MyViewSet(viewsets.ModelViewSet):
    permission_classes = [CanViewRecycleBin]
```

## Segregación de Datos

### Automática en Vistas
```python
# En recycle_bin_list
if not user.profile.can_view_all_recycle_items():
    # Usuario ve solo sus elementos
    queryset = queryset.filter(deleted_by=request.user)
else:
    # Admin/Auditor ve todos
    queryset = RecycleBin.objects.all()
```

### Manual en Queries
```python
# Obtener elementos según permisos
if user.profile.can_view_all_recycle_items():
    entries = RecycleBin.objects.all()
else:
    entries = RecycleBin.objects.filter(deleted_by=user)
```

## Contexto de Permisos en Templates

Las vistas proporcionan `user_permissions` en el contexto:

```python
context = {
    'user_permissions': {
        'can_view_all': bool,
        'can_restore_items': bool,
        'can_restore_own': bool,
        'can_restore_others': bool,
        'can_permanent_delete': bool,
        'can_bulk_restore': bool,
        'can_bulk_delete': bool,
        'can_view_audit_logs': bool,
    }
}
```

Uso en template:
```django
{% if user_permissions.can_restore %}
    <!-- Mostrar botón de restaurar -->
{% endif %}
```

## Flujos Comunes

### Flujo 1: Funcionario Elimina y Restaura
```
1. Funcionario elimina oficina
2. Oficina va a papelera
3. Funcionario ve su elemento en papelera
4. Funcionario puede restaurar su elemento
5. ✗ Funcionario NO ve elementos de otros
```

### Flujo 2: Admin Gestiona Todo
```
1. Admin accede a papelera
2. Admin ve TODOS los elementos
3. Admin puede restaurar cualquier elemento
4. Admin puede eliminar permanentemente
5. Admin puede gestionar configuración
```

### Flujo 3: Auditor Revisa
```
1. Auditor accede a papelera
2. Auditor ve TODOS los elementos
3. Auditor ve logs de auditoría
4. ✗ Auditor NO puede modificar nada
5. ✗ Auditor NO puede restaurar
```

## Troubleshooting

### Usuario no puede acceder a papelera
```python
# Verificar rol
user.profile.role  # Debe ser 'administrador', 'funcionario' o 'auditor'

# Verificar estado activo
user.profile.is_active  # Debe ser True

# Verificar permiso
user.profile.can_view_recycle_bin()  # Debe ser True
```

### Usuario no ve elementos en papelera
```python
# Verificar si tiene permiso de ver todos
user.profile.can_view_all_recycle_items()  # False = solo ve propios

# Verificar elementos propios
RecycleBin.objects.filter(deleted_by=user).count()
```

### Usuario no puede restaurar
```python
# Verificar permiso general
user.profile.can_restore_items()  # Debe ser True

# Verificar permiso específico
if entry.deleted_by == user:
    user.profile.can_restore_own_items()  # Debe ser True
else:
    user.profile.can_restore_others_items()  # Debe ser True
```

## Testing

### Test Rápido de Permisos
```python
from django.contrib.auth.models import User

# Obtener usuario
user = User.objects.get(username='funcionario1')

# Verificar permisos
assert user.profile.can_view_recycle_bin() == True
assert user.profile.can_permanent_delete() == False
```

### Ejecutar Tests
```bash
# Todos los tests de permisos
python manage.py test tests.test_recycle_bin_permissions

# Test específico
python manage.py test tests.test_recycle_bin_permissions.RecycleBinPermissionsTestCase.test_admin_has_all_recycle_permissions
```

## Mejores Prácticas

1. **Siempre verificar permisos** antes de operaciones sensibles
2. **Usar decoradores** en vistas para protección automática
3. **Implementar segregación** en queries para seguridad
4. **Proporcionar contexto** de permisos a templates
5. **Registrar intentos** de acceso no autorizado
6. **Mantener roles actualizados** en perfiles de usuario
7. **Revisar logs** de auditoría regularmente

## Referencias Rápidas

- **Modelo**: `apps/core/models.py` - UserProfile
- **Permisos**: `apps/core/permissions.py`
- **Vistas**: `apps/core/views.py` - recycle_bin_*
- **Tests**: `tests/test_recycle_bin_permissions.py`
- **Comandos**: `apps/core/management/commands/`
