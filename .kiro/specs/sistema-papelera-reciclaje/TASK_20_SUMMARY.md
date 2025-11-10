# Task 20: Sistema de Permisos Granular - Resumen de Implementación

## Descripción General

Se ha implementado un sistema completo de permisos granulares para la papelera de reciclaje que incluye:

- **Permisos específicos por rol** (administrador, funcionario, auditor)
- **Grupos de permisos predefinidos** para cada rol
- **Segregación de datos por usuario** según permisos
- **Validaciones de permisos en todas las vistas**
- **Comandos de management** para configuración de permisos

## Componentes Implementados

### 1. Permisos en UserProfile (apps/core/models.py)

Se agregaron los siguientes métodos de permisos al modelo `UserProfile`:

#### Permisos de Visualización
- `can_view_recycle_bin()` - Ver la papelera de reciclaje
- `can_view_all_recycle_items()` - Ver todos los elementos (no solo propios)
- `can_view_deletion_audit_logs()` - Ver logs de auditoría de eliminaciones

#### Permisos de Restauración
- `can_restore_items()` - Restaurar elementos de la papelera
- `can_restore_own_items()` - Restaurar propios elementos
- `can_restore_others_items()` - Restaurar elementos de otros usuarios
- `can_bulk_restore()` - Restaurar elementos en lote

#### Permisos de Eliminación
- `can_permanent_delete()` - Eliminar permanentemente elementos
- `can_bulk_permanent_delete()` - Eliminar permanentemente en lote

#### Permisos de Configuración
- `can_manage_recycle_config()` - Gestionar configuración de papelera

### 2. Clases de Permisos para DRF (apps/core/permissions.py)

Se crearon las siguientes clases de permisos para Django REST Framework:

- `CanViewRecycleBin` - Permiso para ver la papelera
- `CanViewAllRecycleItems` - Permiso para ver todos los elementos
- `CanRestoreItems` - Permiso para restaurar elementos
- `CanRestoreOwnItems` - Permiso para restaurar propios elementos
- `CanRestoreOthersItems` - Permiso para restaurar elementos de otros
- `CanPermanentDelete` - Permiso para eliminar permanentemente
- `CanViewDeletionAuditLogs` - Permiso para ver logs de auditoría
- `CanManageRecycleConfig` - Permiso para gestionar configuración
- `CanBulkRestore` - Permiso para restaurar en lote
- `CanBulkPermanentDelete` - Permiso para eliminar permanentemente en lote

### 3. Validaciones en Vistas (apps/core/views.py)

Se actualizaron todas las vistas de papelera con validaciones de permisos:

#### recycle_bin_list
- Requiere `can_view_recycle_bin`
- Implementa segregación de datos (usuarios ven solo sus elementos si no tienen `can_view_all_recycle_items`)
- Proporciona contexto de permisos al template

#### recycle_bin_detail
- Requiere `can_view_recycle_bin`
- Valida acceso según propietario del elemento
- Proporciona permisos específicos en contexto

#### recycle_bin_restore
- Requiere `can_restore_items`
- Valida permisos granulares según propietario:
  - Propios elementos: requiere `can_restore_own_items`
  - Elementos de otros: requiere `can_restore_others_items`

#### recycle_bin_bulk_restore
- Requiere `can_bulk_restore`
- Valida permisos para cada elemento individualmente

#### recycle_bin_permanent_delete
- Requiere `can_permanent_delete` (solo administradores)
- Incluye validación de código de seguridad

#### recycle_bin_bulk_permanent_delete
- Requiere `can_bulk_permanent_delete` (solo administradores)
- Incluye validación de código de seguridad

### 4. Tests Completos (tests/test_recycle_bin_permissions.py)

Se creó una suite completa de tests que incluye:

#### Tests de Permisos en UserProfile
- `test_admin_has_all_recycle_permissions` - Administrador tiene todos los permisos
- `test_funcionario_has_limited_permissions` - Funcionario tiene permisos limitados
- `test_auditor_has_view_only_permissions` - Auditor solo puede visualizar
- `test_consulta_has_no_recycle_permissions` - Usuario de consulta sin permisos
- `test_inactive_user_has_no_permissions` - Usuario inactivo sin permisos

#### Tests de Segregación de Datos
- `test_admin_can_view_all_entries` - Admin ve todas las entradas
- `test_funcionario_can_only_view_own_entries` - Funcionario ve solo sus entradas
- `test_auditor_can_view_all_entries` - Auditor ve todas las entradas
- `test_consulta_cannot_access_recycle_bin` - Usuario de consulta no accede

#### Tests de Permisos en Vistas
- `test_recycle_bin_list_requires_permission` - Lista requiere permiso
- `test_recycle_bin_detail_requires_permission` - Detalle requiere permiso
- `test_funcionario_cannot_view_others_entries` - Funcionario no ve entradas ajenas
- `test_restore_requires_permission` - Restauración requiere permiso
- `test_funcionario_cannot_restore_others_items` - Funcionario no restaura elementos ajenos
- `test_admin_can_restore_others_items` - Admin restaura cualquier elemento
- `test_permanent_delete_requires_admin` - Eliminación permanente requiere admin
- `test_bulk_restore_requires_permission` - Restauración en lote requiere permiso
- `test_bulk_permanent_delete_requires_admin` - Eliminación en lote requiere admin

#### Tests de Contexto de Templates
- `test_list_view_provides_user_permissions_context` - Lista proporciona permisos en contexto
- `test_detail_view_provides_user_permissions_context` - Detalle proporciona permisos en contexto

#### Tests de Grupos de Permisos
- `test_administrator_permission_group` - Grupo de permisos de administrador
- `test_funcionario_permission_group` - Grupo de permisos de funcionario
- `test_auditor_permission_group` - Grupo de permisos de auditor

#### Tests de Integración
- `test_complete_workflow_with_permissions` - Flujo completo con validación de permisos

### 5. Comandos de Management

#### setup_recycle_permissions.py
Configura grupos de permisos predefinidos para la papelera:

```bash
python manage.py setup_recycle_permissions
```

Opciones:
- `--reset` - Elimina y recrea los grupos de permisos

Crea los siguientes grupos:
- **Recycle Bin - Administrador**: Todos los permisos
- **Recycle Bin - Funcionario**: Permisos de visualización y restauración de propios elementos
- **Recycle Bin - Auditor**: Permisos de solo visualización

#### assign_recycle_permissions.py
Asigna usuarios a grupos de permisos:

```bash
python manage.py assign_recycle_permissions <username> <role>
```

Argumentos:
- `username` - Nombre de usuario a asignar
- `role` - Rol a asignar (administrador, funcionario, auditor)

Opciones:
- `--remove` - Remover usuario del grupo

## Matriz de Permisos por Rol

| Permiso | Administrador | Funcionario | Auditor | Consulta |
|---------|--------------|-------------|---------|----------|
| Ver papelera | ✓ | ✓ | ✓ | ✗ |
| Ver todos los elementos | ✓ | ✗ | ✓ | ✗ |
| Ver logs de auditoría | ✓ | ✗ | ✓ | ✗ |
| Restaurar propios elementos | ✓ | ✓ | ✗ | ✗ |
| Restaurar elementos de otros | ✓ | ✗ | ✗ | ✗ |
| Restaurar en lote | ✓ | ✓ | ✗ | ✗ |
| Eliminar permanentemente | ✓ | ✗ | ✗ | ✗ |
| Eliminar permanentemente en lote | ✓ | ✗ | ✗ | ✗ |
| Gestionar configuración | ✓ | ✗ | ✗ | ✗ |

## Segregación de Datos

El sistema implementa segregación de datos automática:

### Administradores y Auditores
- Ven **todos** los elementos en la papelera
- Pueden filtrar por usuario que eliminó
- Tienen acceso completo a estadísticas globales

### Funcionarios
- Ven **solo** los elementos que ellos eliminaron
- No pueden ver elementos eliminados por otros usuarios
- Las estadísticas muestran solo sus propios datos

### Usuarios de Consulta
- **No tienen acceso** a la papelera de reciclaje
- Son redirigidos si intentan acceder

## Validaciones de Permisos en Vistas

Todas las vistas implementan validaciones en múltiples niveles:

### Nivel 1: Decorador de Permiso
```python
@permission_required_custom('can_view_recycle_bin')
```

### Nivel 2: Validación de Propietario
```python
if entry.deleted_by == request.user:
    if not can_restore_own:
        # Denegar acceso
else:
    if not can_restore_others:
        # Denegar acceso
```

### Nivel 3: Segregación en Queryset
```python
if not can_view_all:
    queryset = queryset.filter(deleted_by=request.user)
```

## Uso en Templates

Los templates reciben un diccionario `user_permissions` con todos los permisos:

```django
{% if user_permissions.can_restore %}
    <button>Restaurar</button>
{% endif %}

{% if user_permissions.can_permanent_delete %}
    <button>Eliminar Permanentemente</button>
{% endif %}
```

## Configuración Inicial

Para configurar el sistema de permisos en un nuevo entorno:

1. **Ejecutar setup de permisos:**
```bash
python manage.py setup_recycle_permissions
```

2. **Asignar usuarios a grupos:**
```bash
python manage.py assign_recycle_permissions admin administrador
python manage.py assign_recycle_permissions funcionario1 funcionario
python manage.py assign_recycle_permissions auditor1 auditor
```

3. **Verificar permisos:**
Los permisos se verifican automáticamente en cada request a través de los decoradores y mixins.

## Integración con Sistema Existente

El sistema de permisos se integra perfectamente con:

- **Sistema de roles existente** en UserProfile
- **Decoradores de permisos** existentes
- **Sistema de auditoría** (DeletionAuditLog)
- **Configuración por módulo** (RecycleBinConfig)

## Seguridad

El sistema implementa múltiples capas de seguridad:

1. **Autenticación requerida** - Todas las vistas requieren login
2. **Validación de permisos** - Múltiples niveles de validación
3. **Segregación de datos** - Usuarios ven solo lo permitido
4. **Auditoría completa** - Todos los intentos se registran
5. **Código de seguridad** - Para eliminación permanente
6. **Bloqueo temporal** - Tras intentos fallidos

## Archivos Modificados

1. `apps/core/models.py` - Métodos de permisos en UserProfile
2. `apps/core/permissions.py` - Clases de permisos para DRF
3. `apps/core/views.py` - Validaciones en vistas de papelera
4. `tests/test_recycle_bin_permissions.py` - Suite completa de tests
5. `apps/core/management/commands/setup_recycle_permissions.py` - Comando de setup
6. `apps/core/management/commands/assign_recycle_permissions.py` - Comando de asignación

## Verificación de Implementación

Para verificar que el sistema funciona correctamente:

1. **Ejecutar tests:**
```bash
python manage.py test tests.test_recycle_bin_permissions
```

2. **Verificar permisos de un usuario:**
```python
from django.contrib.auth.models import User
user = User.objects.get(username='funcionario1')
print(user.profile.can_view_recycle_bin())  # True
print(user.profile.can_permanent_delete())  # False
```

3. **Probar acceso a vistas:**
- Login como funcionario y verificar que solo ve sus elementos
- Login como admin y verificar que ve todos los elementos
- Login como auditor y verificar que puede ver pero no modificar

## Cumplimiento de Requirements

✅ **Requirement 8.1** - Permisos específicos implementados y validados
✅ **Requirement 8.2** - Segregación de datos por usuario implementada
✅ **Requirement 8.3** - Validaciones de permisos en todas las vistas
✅ **Requirement 2.6** - Usuarios ven solo registros permitidos según rol

## Próximos Pasos

El sistema de permisos está completo y listo para uso. Los siguientes pasos recomendados son:

1. Ejecutar `setup_recycle_permissions` en producción
2. Asignar usuarios a grupos apropiados
3. Verificar funcionamiento con usuarios reales
4. Documentar políticas de permisos para el equipo
