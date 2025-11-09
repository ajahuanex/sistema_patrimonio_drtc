# Task 9 Verification Guide

## Verificación de Implementación de Soft Delete en Vistas

### 1. Verificar Vista de Oficinas

**Archivo:** `apps/oficinas/views.py`

**Función:** `eliminar_oficina_view()`

**Verificar que:**
- ✅ Usa `oficina.soft_delete(user=request.user, reason=deletion_reason)` en lugar de `oficina.delete()`
- ✅ Crea entrada en `RecycleBin` con todos los metadatos
- ✅ Mensaje indica "movida a la papelera de reciclaje"
- ✅ Mantiene validación de bienes asignados

**Código clave:**
```python
# Usar soft delete
oficina.soft_delete(user=request.user, reason=deletion_reason)

# Crear entrada en papelera
RecycleBin.objects.create(
    content_type=content_type,
    object_id=oficina.id,
    object_repr=f"{codigo_oficina} - {nombre_oficina}",
    module_name='oficinas',
    deleted_by=request.user,
    deletion_reason=deletion_reason,
    auto_delete_at=auto_delete_at,
    original_data={...}
)
```

### 2. Verificar Vista de Bienes

**Archivo:** `apps/bienes/views.py`

**Clase:** `BienDeleteView`

**Verificar que:**
- ✅ Sobrescribe método `delete()` para usar soft delete
- ✅ Crea entrada en `RecycleBin` con datos del bien
- ✅ Mensaje indica "movido a la papelera de reciclaje"
- ✅ Mantiene compatibilidad con `DeleteView`

**Código clave:**
```python
def delete(self, request, *args, **kwargs):
    """Sobrescribe delete para usar soft delete"""
    self.object = self.get_object()
    
    # Usar soft delete
    self.object.soft_delete(user=request.user, reason=deletion_reason)
    
    # Crear entrada en RecycleBin
    RecycleBin.objects.create(...)
    
    messages.success(request, 'Bien patrimonial movido a la papelera de reciclaje.')
    return redirect(success_url)
```

### 3. Verificar Vista de Catálogo

**Archivo:** `apps/catalogo/views.py`

**Función:** `eliminar_catalogo_view()` (NUEVA)

**Verificar que:**
- ✅ Nueva función creada con decoradores apropiados
- ✅ Valida bienes asociados antes de eliminar
- ✅ Usa soft delete con usuario y motivo
- ✅ Crea entrada en `RecycleBin`
- ✅ Retorna respuesta JSON

**Archivo:** `apps/catalogo/urls.py`

**Verificar que:**
- ✅ Nueva ruta agregada: `path('<int:pk>/eliminar/', views.eliminar_catalogo_view, name='eliminar')`

### 4. Verificar Comportamiento de Managers

**Ejecutar en Django shell:**

```python
from apps.oficinas.models import Oficina
from apps.bienes.models import BienPatrimonial
from apps.catalogo.models import Catalogo
from django.contrib.auth.models import User

# Crear usuario de prueba
user = User.objects.first()

# Test con Oficina
oficina = Oficina.objects.first()
print(f"Oficinas activas: {Oficina.objects.count()}")

# Soft delete
oficina.soft_delete(user=user, reason="Prueba")
print(f"Oficinas activas después de soft delete: {Oficina.objects.count()}")
print(f"Oficinas eliminadas: {Oficina.objects.deleted_only().count()}")
print(f"Todas las oficinas: {Oficina.all_objects.count()}")

# Restore
oficina.restore(user=user)
print(f"Oficinas activas después de restore: {Oficina.objects.count()}")
```

### 5. Verificar RecycleBin

**Ejecutar en Django shell:**

```python
from apps.core.models import RecycleBin
from apps.oficinas.models import Oficina
from django.contrib.auth.models import User

user = User.objects.first()
oficina = Oficina.objects.first()

# Eliminar oficina
oficina.soft_delete(user=user, reason="Prueba de papelera")

# Verificar entrada en RecycleBin
recycle_entry = RecycleBin.objects.filter(
    object_id=oficina.id,
    module_name='oficinas'
).first()

print(f"Entrada en papelera: {recycle_entry}")
print(f"Objeto representado: {recycle_entry.object_repr}")
print(f"Eliminado por: {recycle_entry.deleted_by}")
print(f"Motivo: {recycle_entry.deletion_reason}")
print(f"Días hasta auto-eliminación: {recycle_entry.days_until_auto_delete}")
print(f"Datos originales: {recycle_entry.original_data}")
```

### 6. Verificar Tests

**Ejecutar tests:**

```bash
# Tests de soft delete para oficinas
python manage.py test tests.test_soft_delete_oficina -v 2

# Tests de soft delete para bienes
python manage.py test tests.test_soft_delete_bien -v 2

# Tests de soft delete para catálogo
python manage.py test tests.test_soft_delete_catalogo -v 2

# Todos los tests juntos
python manage.py test tests.test_soft_delete_oficina tests.test_soft_delete_bien tests.test_soft_delete_catalogo -v 2
```

**Resultado esperado:** ✅ 76/76 tests pasando

### 7. Verificar Compatibilidad con Vistas Existentes

**Vistas de listado:**
```python
# Estas vistas NO requieren cambios
# El manager objects excluye automáticamente eliminados

# apps/oficinas/views.py
def lista_oficinas_view(request):
    oficinas = Oficina.objects.all()  # ✅ Excluye eliminados automáticamente
    
# apps/bienes/views.py
class BienListView(ListView):
    queryset = BienPatrimonial.objects.all()  # ✅ Excluye eliminados automáticamente

# apps/catalogo/views.py
def lista_catalogo_view(request):
    catalogos = Catalogo.objects.all()  # ✅ Excluye eliminados automáticamente
```

**Vistas de detalle:**
```python
# get_object_or_404 usa el manager por defecto
oficina = get_object_or_404(Oficina, id=oficina_id)  # ✅ No encuentra eliminados
```

**Búsquedas:**
```python
# Todas las búsquedas excluyen eliminados automáticamente
Oficina.objects.filter(nombre__icontains=busqueda)  # ✅ Solo activos
```

### 8. Verificar Configuración de RecycleBin

**Ejecutar en Django shell:**

```python
from apps.core.models import RecycleBinConfig

# Verificar configuraciones por módulo
for module in ['oficinas', 'bienes', 'catalogo']:
    config = RecycleBinConfig.get_config_for_module(module)
    print(f"\nConfiguración para {module}:")
    print(f"  Días de retención: {config.retention_days}")
    print(f"  Auto-eliminación habilitada: {config.auto_delete_enabled}")
    print(f"  Días de advertencia: {config.warning_days_before}")
    print(f"  Advertencia final: {config.final_warning_days_before}")
```

### 9. Verificar Mensajes de Usuario

**Oficinas:**
- Antes: "La oficina X ha sido eliminada exitosamente."
- Ahora: "La oficina X ha sido movida a la papelera de reciclaje."

**Bienes:**
- Antes: "Bien patrimonial eliminado correctamente."
- Ahora: "Bien patrimonial movido a la papelera de reciclaje."

**Catálogo:**
- Nuevo: "El catálogo X ha sido movido a la papelera de reciclaje."

### 10. Checklist de Verificación Final

- [ ] ✅ Vista de oficinas usa soft delete
- [ ] ✅ Vista de bienes usa soft delete
- [ ] ✅ Vista de catálogo creada y usa soft delete
- [ ] ✅ URL de catálogo agregada
- [ ] ✅ Todas las vistas crean entrada en RecycleBin
- [ ] ✅ Managers excluyen eliminados automáticamente
- [ ] ✅ Tests pasan (76/76)
- [ ] ✅ Validaciones de dependencias funcionan
- [ ] ✅ Mensajes actualizados para usuarios
- [ ] ✅ Compatibilidad con código existente mantenida

## Resultado

✅ **TASK 9 COMPLETADA EXITOSAMENTE**

Todas las vistas de eliminación ahora usan soft delete y crean entradas en la papelera de reciclaje. El sistema mantiene total compatibilidad con el código existente mientras agrega la funcionalidad de recuperación.
