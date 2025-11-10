# Task 12: Formularios de Papelera - Guía Rápida

## 🚀 Inicio Rápido

### Configuración Inicial

1. **Agregar código de seguridad en `.env`**:
```bash
PERMANENT_DELETE_CODE=your-secure-code-here
```

2. **Incluir JavaScript en templates**:
```django
{% block extra_js %}
<script src="{% static 'js/recycle_bin_forms.js' %}"></script>
{% endblock %}
```

## 📋 Formularios Disponibles

### 1. RestoreForm - Restauración con Validación

**Uso en Vista**:
```python
from apps.core.forms import RestoreForm

def restore_view(request, entry_id):
    entry = get_object_or_404(RecycleBin, id=entry_id)
    
    if request.method == 'POST':
        form = RestoreForm(request.POST, entry=entry, user=request.user)
        if form.is_valid():
            # Procesar restauración
            notes = form.cleaned_data['notes']
            resolve_method = form.cleaned_data.get('resolve_conflicts')
    else:
        form = RestoreForm(initial={'entry_id': entry_id}, entry=entry, user=request.user)
```

**Uso en Template**:
```django
<form method="post" id="restoreForm">
    {% csrf_token %}
    {{ form.as_p }}
    <button type="submit">Restaurar</button>
</form>
```

### 2. PermanentDeleteForm - Eliminación Segura

**Uso en Vista**:
```python
from apps.core.forms import PermanentDeleteForm

def permanent_delete_view(request, entry_id):
    entry = get_object_or_404(RecycleBin, id=entry_id)
    
    if request.method == 'POST':
        form = PermanentDeleteForm(request.POST, entry=entry, user=request.user)
        if form.is_valid():
            security_code = form.cleaned_data['security_code']
            reason = form.cleaned_data['reason']
            # Procesar eliminación
```

**Uso en Template**:
```django
<form method="post" id="permanentDeleteForm">
    {% csrf_token %}
    <input type="hidden" name="entry_id" value="{{ entry.id }}">
    
    <div class="form-group">
        <label>Código de Seguridad:</label>
        <input type="password" name="security_code" class="form-control" 
               data-validate="security-code" required>
    </div>
    
    <div class="form-group">
        <label>Escriba "ELIMINAR":</label>
        <input type="text" name="confirm_text" class="form-control" 
               data-validate="confirm-text" required>
    </div>
    
    <div class="form-group">
        <label>Motivo:</label>
        <textarea name="reason" class="form-control" rows="3" 
                  data-validate="required" required></textarea>
    </div>
    
    <button type="submit" class="btn btn-danger" disabled>Eliminar</button>
</form>
```

### 3. BulkOperationForm - Operaciones en Lote

**Uso en Vista**:
```python
from apps.core.forms import BulkOperationForm

def bulk_operation_view(request):
    entry_ids = request.POST.getlist('entry_ids[]')
    
    form_data = {
        'operation': 'restore',  # o 'permanent_delete'
        'entry_ids': ','.join(entry_ids),
        'confirm': True,
        'security_code': request.POST.get('security_code', ''),  # solo para delete
    }
    
    form = BulkOperationForm(form_data, user=request.user)
    if form.is_valid():
        entries = form.get_entries()
        # Procesar cada entrada
```

### 4. QuickRestoreForm - Restauración Rápida

**Uso en Vista**:
```python
from apps.core.forms import QuickRestoreForm

def quick_restore_view(request, entry_id):
    form = QuickRestoreForm({'entry_id': entry_id}, user=request.user)
    if form.is_valid():
        # Restaurar sin confirmaciones adicionales
```

**Uso en Template**:
```django
<form method="post" action="{% url 'core:recycle_bin_restore' entry.id %}">
    {% csrf_token %}
    <input type="hidden" name="quick_restore" value="1">
    <input type="hidden" name="entry_id" value="{{ entry.id }}">
    <button type="submit">Restaurar</button>
</form>
```

## 🎨 Atributos data-validate

Para activar validaciones JavaScript en tiempo real:

```html
<!-- Código de seguridad -->
<input data-validate="security-code" />

<!-- Texto de confirmación -->
<input data-validate="confirm-text" />

<!-- Campo requerido con contador -->
<textarea data-validate="required"></textarea>
```

## ⚡ Validaciones JavaScript

### Eventos Automáticos

El script `recycle_bin_forms.js` se activa automáticamente en:
- Formularios con ID `restoreForm`
- Formularios con ID `permanentDeleteForm`
- Formularios con ID `bulkOperationForm`

### Funciones Disponibles

```javascript
// Validar formulario manualmente
validateRestoreForm(form, submitButton);
validatePermanentDeleteForm(form, submitButton);
validateBulkOperationForm(form, submitButton);

// Mostrar error en campo
showFieldError(field, message);

// Mostrar éxito en campo
showFieldSuccess(field, message);

// Limpiar errores
clearFieldError(field);
```

## 🔒 Seguridad

### Código de Seguridad

**Configurar**:
```python
# settings.py o .env
PERMANENT_DELETE_CODE = 'your-secure-code-here'
```

**Validar**:
```python
from django.conf import settings

correct_code = getattr(settings, 'PERMANENT_DELETE_CODE', None)
if security_code == correct_code:
    # Código correcto
```

### Auditoría de Intentos Fallidos

Los intentos fallidos se registran automáticamente:
```python
AuditLog.objects.create(
    user=request.user,
    action='security_violation',
    model_name='RecycleBin',
    object_id=str(entry_id),
    changes={'security_code_attempt': 'failed'}
)
```

## 📊 Manejo de Errores

### En Formularios Django

```python
if not form.is_valid():
    for field, errors in form.errors.items():
        for error in errors:
            messages.error(request, f'{field}: {error}')
```

### En JavaScript

```javascript
// Los errores se muestran automáticamente
// Pero puedes capturarlos en el evento submit:
document.addEventListener('submit', function(e) {
    if (!validateForm(e.target)) {
        e.preventDefault();
        alert('Corrija los errores antes de continuar');
    }
});
```

## 🧪 Testing

### Ejecutar Tests

```bash
python manage.py test tests.test_recycle_bin_forms
```

### Ejemplo de Test

```python
from apps.core.forms import RestoreForm

def test_restore_form():
    form_data = {
        'entry_id': entry.id,
        'confirm': True,
        'notes': 'Test notes'
    }
    form = RestoreForm(form_data, entry=entry, user=user)
    assert form.is_valid()
```

## 🎯 Casos de Uso Comunes

### Restaurar con Conflictos

```python
# Vista
form = RestoreForm(request.POST, entry=entry, user=request.user)
if form.is_valid():
    resolve_method = form.cleaned_data.get('resolve_conflicts')
    if resolve_method == 'rename':
        # Renombrar elemento
    elif resolve_method == 'replace':
        # Reemplazar existente
```

### Eliminar Múltiples Elementos

```python
# Vista
form = BulkOperationForm(form_data, user=request.user)
if form.is_valid():
    entries = form.get_entries()
    for entry in entries:
        # Procesar cada uno
```

### Validar Permisos

```python
# Los formularios validan automáticamente
# Pero puedes verificar manualmente:
if not entry.can_be_restored_by(request.user):
    # Sin permisos
```

## 📝 Notas Importantes

1. **Siempre usar CSRF token** en formularios POST
2. **Incluir JavaScript** para validaciones en tiempo real
3. **Configurar código de seguridad** antes de usar en producción
4. **Validar permisos** en el backend, no solo en frontend
5. **Registrar operaciones** en auditoría para trazabilidad

## 🔗 Referencias

- Formularios: `apps/core/forms.py`
- Vistas: `apps/core/views.py`
- JavaScript: `static/js/recycle_bin_forms.js`
- Tests: `tests/test_recycle_bin_forms.py`
- Documentación completa: `TASK_12_SUMMARY.md`
