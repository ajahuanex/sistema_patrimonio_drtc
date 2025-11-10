# Task 20: Sistema de Permisos Granular - Guía de Uso

## 🎯 Introducción

Esta guía proporciona instrucciones paso a paso para usar el sistema de permisos granulares de la papelera de reciclaje.

## 📋 Tabla de Contenidos

1. [Configuración Inicial](#configuración-inicial)
2. [Gestión de Usuarios](#gestión-de-usuarios)
3. [Uso en Código](#uso-en-código)
4. [Uso en Templates](#uso-en-templates)
5. [Casos de Uso Comunes](#casos-de-uso-comunes)
6. [Troubleshooting](#troubleshooting)

## 🚀 Configuración Inicial

### Paso 1: Crear Grupos de Permisos

Ejecutar el comando de setup para crear los grupos predefinidos:

```bash
python manage.py setup_recycle_permissions
```

**Salida esperada:**
```
Configurando grupos de permisos de papelera...
✓ Grupo "Administrador" creado
  ✓ 13 permisos asignados a Administrador
✓ Grupo "Funcionario" creado
  ✓ 4 permisos asignados a Funcionario
✓ Grupo "Auditor" creado
  ✓ 4 permisos asignados a Auditor

======================================================================
Configuración de permisos completada
======================================================================

Grupos creados:
  • Recycle Bin - Administrador (13 permisos)
  • Recycle Bin - Funcionario (4 permisos)
  • Recycle Bin - Auditor (4 permisos)
```

### Paso 2: Verificar Grupos Creados

```python
python manage.py shell

>>> from django.contrib.auth.models import Group
>>> Group.objects.filter(name__startswith='Recycle Bin').count()
3
```

## 👥 Gestión de Usuarios

### Asignar Usuario a Rol

#### Asignar Administrador
```bash
python manage.py assign_recycle_permissions admin administrador
```

#### Asignar Funcionario
```bash
python manage.py assign_recycle_permissions funcionario1 funcionario
```

#### Asignar Auditor
```bash
python manage.py assign_recycle_permissions auditor1 auditor
```

### Remover Usuario de Rol

```bash
python manage.py assign_recycle_permissions funcionario1 funcionario --remove
```

### Verificar Permisos de Usuario

```python
python manage.py shell

>>> from django.contrib.auth.models import User
>>> user = User.objects.get(username='funcionario1')
>>> 
>>> # Verificar rol
>>> user.profile.role
'funcionario'
>>> 
>>> # Verificar permisos específicos
>>> user.profile.can_view_recycle_bin()
True
>>> user.profile.can_restore_own_items()
True
>>> user.profile.can_permanent_delete()
False
```

## 💻 Uso en Código

### En Vistas Basadas en Funciones

#### Proteger Vista con Decorador

```python
from apps.core.permissions import permission_required_custom

@login_required
@permission_required_custom('can_view_recycle_bin')
def my_recycle_view(request):
    # Vista protegida
    entries = RecycleBin.objects.all()
    return render(request, 'my_template.html', {'entries': entries})
```

#### Validación Manual de Permisos

```python
@login_required
def my_view(request):
    # Verificar permiso
    if not request.user.profile.can_view_recycle_bin():
        messages.error(request, 'No tiene permisos para acceder')
        return redirect('home')
    
    # Continuar con la lógica
    entries = RecycleBin.objects.all()
    return render(request, 'template.html', {'entries': entries})
```

#### Segregación de Datos

```python
@login_required
@permission_required_custom('can_view_recycle_bin')
def recycle_list(request):
    # Obtener queryset base
    queryset = RecycleBin.objects.all()
    
    # Aplicar segregación según permisos
    if not request.user.profile.can_view_all_recycle_items():
        # Usuario ve solo sus elementos
        queryset = queryset.filter(deleted_by=request.user)
    
    return render(request, 'list.html', {'entries': queryset})
```

### En Vistas Basadas en Clases

#### Usando Mixin

```python
from apps.core.permissions import PermissionRequiredMixin

class MyRecycleView(PermissionRequiredMixin, ListView):
    permission_method = 'can_view_recycle_bin'
    model = RecycleBin
    template_name = 'recycle_list.html'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Segregación de datos
        if not self.request.user.profile.can_view_all_recycle_items():
            queryset = queryset.filter(deleted_by=self.request.user)
        
        return queryset
```

### En Django REST Framework

#### Usando Clases de Permisos

```python
from rest_framework import viewsets
from apps.core.permissions import CanViewRecycleBin, CanRestoreItems

class RecycleBinViewSet(viewsets.ModelViewSet):
    queryset = RecycleBin.objects.all()
    serializer_class = RecycleBinSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [CanViewRecycleBin]
        elif self.action == 'restore':
            permission_classes = [CanRestoreItems]
        else:
            permission_classes = [IsAdminUser]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Segregación de datos
        if not self.request.user.profile.can_view_all_recycle_items():
            queryset = queryset.filter(deleted_by=self.request.user)
        
        return queryset
```

## 🎨 Uso en Templates

### Verificar Permisos Directamente

```django
{% if user.profile.can_view_recycle_bin %}
    <a href="{% url 'core:recycle_bin_list' %}">Ver Papelera</a>
{% endif %}

{% if user.profile.can_restore_items %}
    <button class="btn-restore">Restaurar</button>
{% endif %}

{% if user.profile.can_permanent_delete %}
    <button class="btn-delete">Eliminar Permanentemente</button>
{% endif %}
```

### Usar Contexto de Permisos

Las vistas proporcionan un diccionario `user_permissions`:

```django
{% if user_permissions.can_restore %}
    <form method="post" action="{% url 'core:recycle_bin_restore' entry.id %}">
        {% csrf_token %}
        <button type="submit">Restaurar</button>
    </form>
{% endif %}

{% if user_permissions.can_permanent_delete %}
    <a href="{% url 'core:recycle_bin_permanent_delete' entry.id %}">
        Eliminar Permanentemente
    </a>
{% endif %}
```

### Mostrar Mensajes Condicionales

```django
{% if not user_permissions.can_restore_others %}
    <div class="alert alert-info">
        Solo puede restaurar elementos que usted eliminó.
    </div>
{% endif %}

{% if user_permissions.can_view_all %}
    <div class="badge badge-admin">
        Viendo todos los elementos
    </div>
{% else %}
    <div class="badge badge-user">
        Viendo solo sus elementos
    </div>
{% endif %}
```

## 📚 Casos de Uso Comunes

### Caso 1: Funcionario Elimina y Restaura Oficina

```python
# 1. Funcionario elimina oficina
oficina = Oficina.objects.get(codigo='OF001')
oficina.soft_delete(user=request.user, reason='Oficina cerrada')

# 2. Se crea entrada en papelera automáticamente
entry = RecycleBin.objects.get(object_id=oficina.id)

# 3. Funcionario puede ver su entrada
if request.user.profile.can_view_recycle_bin():
    my_entries = RecycleBin.objects.filter(deleted_by=request.user)
    # entry está en my_entries

# 4. Funcionario puede restaurar su entrada
if entry.deleted_by == request.user and request.user.profile.can_restore_own_items():
    success, message, restored = RecycleBinService.restore_object(
        entry, 
        request.user
    )
```

### Caso 2: Admin Gestiona Elementos de Todos

```python
# 1. Admin ve todos los elementos
if request.user.profile.can_view_all_recycle_items():
    all_entries = RecycleBin.objects.all()
    # Ve elementos de todos los usuarios

# 2. Admin puede restaurar cualquier elemento
for entry in all_entries:
    if request.user.profile.can_restore_others_items():
        # Puede restaurar incluso si deleted_by != request.user
        success, message, restored = RecycleBinService.restore_object(
            entry,
            request.user
        )

# 3. Admin puede eliminar permanentemente
if request.user.profile.can_permanent_delete():
    success, message = RecycleBinService.permanent_delete(
        entry,
        request.user,
        security_code='CODIGO_SEGURO'
    )
```

### Caso 3: Auditor Revisa Actividad

```python
# 1. Auditor ve todos los elementos
if request.user.profile.can_view_all_recycle_items():
    all_entries = RecycleBin.objects.all()

# 2. Auditor ve logs de auditoría
if request.user.profile.can_view_deletion_audit_logs():
    audit_logs = DeletionAuditLog.objects.all()
    
    # Filtrar por acción
    soft_deletes = audit_logs.filter(action='soft_delete')
    restores = audit_logs.filter(action='restore')
    permanent_deletes = audit_logs.filter(action='permanent_delete')

# 3. Auditor NO puede modificar
if not request.user.profile.can_restore_items():
    # No puede restaurar
    pass

if not request.user.profile.can_permanent_delete():
    # No puede eliminar permanentemente
    pass
```

### Caso 4: Operaciones en Lote

```python
# 1. Verificar permiso de restauración en lote
if request.user.profile.can_bulk_restore():
    entry_ids = request.POST.getlist('entry_ids[]')
    entries = RecycleBin.objects.filter(id__in=entry_ids)
    
    # 2. Validar permisos para cada elemento
    for entry in entries:
        if entry.deleted_by == request.user:
            if not request.user.profile.can_restore_own_items():
                continue  # Saltar este elemento
        else:
            if not request.user.profile.can_restore_others_items():
                continue  # Saltar este elemento
        
        # 3. Restaurar elemento
        RecycleBinService.restore_object(entry, request.user)

# 4. Eliminación permanente en lote (solo admin)
if request.user.profile.can_bulk_permanent_delete():
    for entry in entries:
        RecycleBinService.permanent_delete(
            entry,
            request.user,
            security_code='CODIGO_SEGURO'
        )
```

## 🔧 Troubleshooting

### Problema: Usuario no puede acceder a papelera

**Síntomas:**
- Usuario es redirigido al intentar acceder
- Mensaje: "No tiene permisos para realizar esta acción"

**Solución:**
```python
# 1. Verificar rol del usuario
python manage.py shell
>>> from django.contrib.auth.models import User
>>> user = User.objects.get(username='usuario')
>>> user.profile.role
'consulta'  # ← Problema: rol sin permisos

# 2. Cambiar rol
>>> user.profile.role = 'funcionario'
>>> user.profile.save()

# 3. Asignar a grupo
python manage.py assign_recycle_permissions usuario funcionario

# 4. Verificar permiso
>>> user.profile.can_view_recycle_bin()
True  # ← Ahora tiene permiso
```

### Problema: Usuario no ve elementos en papelera

**Síntomas:**
- Papelera aparece vacía
- Otros usuarios ven elementos

**Solución:**
```python
# 1. Verificar si tiene permiso de ver todos
>>> user.profile.can_view_all_recycle_items()
False  # ← Solo ve sus propios elementos

# 2. Verificar elementos propios
>>> RecycleBin.objects.filter(deleted_by=user).count()
0  # ← No tiene elementos propios

# 3. Si debe ver todos, cambiar rol
>>> user.profile.role = 'administrador'
>>> user.profile.save()
>>> user.profile.can_view_all_recycle_items()
True  # ← Ahora ve todos
```

### Problema: Usuario no puede restaurar elemento

**Síntomas:**
- Botón de restaurar no aparece
- Error al intentar restaurar

**Solución:**
```python
# 1. Verificar permiso general
>>> user.profile.can_restore_items()
False  # ← No tiene permiso de restaurar

# 2. Cambiar rol si es necesario
>>> user.profile.role = 'funcionario'
>>> user.profile.save()

# 3. Verificar permiso específico
>>> entry = RecycleBin.objects.get(id=1)
>>> if entry.deleted_by == user:
...     user.profile.can_restore_own_items()
... else:
...     user.profile.can_restore_others_items()
True  # ← Ahora puede restaurar
```

### Problema: Grupos de permisos no existen

**Síntomas:**
- Error al asignar usuario a grupo
- Mensaje: "Grupo no existe"

**Solución:**
```bash
# 1. Ejecutar setup de permisos
python manage.py setup_recycle_permissions

# 2. Verificar grupos creados
python manage.py shell
>>> from django.contrib.auth.models import Group
>>> Group.objects.filter(name__startswith='Recycle Bin').count()
3  # ← Debe ser 3

# 3. Si no existen, recrear
python manage.py setup_recycle_permissions --reset
```

## 📊 Verificación de Configuración

### Checklist de Verificación

```bash
# 1. Verificar grupos existen
python manage.py shell
>>> from django.contrib.auth.models import Group
>>> Group.objects.filter(name__startswith='Recycle Bin').count()
3  # ✓ OK

# 2. Verificar usuarios asignados
>>> from django.contrib.auth.models import User
>>> admin = User.objects.get(username='admin')
>>> admin.groups.filter(name='Recycle Bin - Administrador').exists()
True  # ✓ OK

# 3. Verificar permisos funcionan
>>> admin.profile.can_view_recycle_bin()
True  # ✓ OK
>>> admin.profile.can_permanent_delete()
True  # ✓ OK

# 4. Verificar segregación
>>> func = User.objects.get(username='funcionario1')
>>> func.profile.can_view_all_recycle_items()
False  # ✓ OK (solo ve propios)
```

## 🎓 Mejores Prácticas

1. **Siempre verificar permisos** antes de operaciones sensibles
2. **Usar decoradores** para protección automática de vistas
3. **Implementar segregación** en queries para seguridad
4. **Proporcionar contexto** de permisos a templates
5. **Registrar intentos** de acceso no autorizado
6. **Mantener roles actualizados** en perfiles de usuario
7. **Revisar logs** de auditoría regularmente

## 📞 Soporte

Para más información, consultar:
- `TASK_20_SUMMARY.md` - Resumen completo
- `TASK_20_QUICK_REFERENCE.md` - Referencia rápida
- `TASK_20_VERIFICATION.md` - Verificación y pruebas
