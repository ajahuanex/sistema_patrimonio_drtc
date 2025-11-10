# Task 12: Ejemplos de Uso de Formularios

## 📚 Ejemplos Completos de Implementación

### Ejemplo 1: Vista de Restauración Completa

```python
# apps/core/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import RecycleBin
from .forms import RestoreForm
from .utils import RecycleBinService

@login_required
def restore_item_view(request, entry_id):
    """
    Vista completa para restaurar un elemento con manejo de conflictos
    """
    entry = get_object_or_404(RecycleBin, id=entry_id)
    
    # Verificar permisos
    if not entry.can_be_restored_by(request.user):
        messages.error(request, 'No tiene permisos para restaurar este elemento')
        return redirect('core:recycle_bin_list')
    
    if request.method == 'POST':
        form = RestoreForm(request.POST, entry=entry, user=request.user)
        
        if form.is_valid():
            # Obtener datos del formulario
            notes = form.cleaned_data.get('notes', '')
            resolve_method = form.cleaned_data.get('resolve_conflicts')
            
            # Intentar restaurar
            success, message, restored_object = RecycleBinService.restore_object(
                entry, 
                request.user,
                notes=notes,
                resolve_method=resolve_method
            )
            
            if success:
                messages.success(request, message)
                
                # Redirigir al objeto restaurado
                if restored_object:
                    return redirect('object_detail', pk=restored_object.pk)
                return redirect('core:recycle_bin_list')
            else:
                messages.error(request, message)
        else:
            # Mostrar errores del formulario
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        # GET - Mostrar formulario
        form = RestoreForm(
            initial={'entry_id': entry_id}, 
            entry=entry, 
            user=request.user
        )
    
    # Obtener información adicional
    original_object = entry.content_object
    conflicts = None
    
    if original_object:
        conflicts = RecycleBinService._check_restore_conflicts(original_object)
    
    context = {
        'entry': entry,
        'form': form,
        'original_object': original_object,
        'conflicts': conflicts,
    }
    
    return render(request, 'core/restore_form.html', context)
```

**Template correspondiente**:

```django
<!-- templates/core/restore_form.html -->
{% extends 'base.html' %}
{% load static %}

{% block extra_js %}
<script src="{% static 'js/recycle_bin_forms.js' %}"></script>
{% endblock %}

{% block content %}
<div class="container">
    <h2>Restaurar Elemento</h2>
    
    <div class="card mb-3">
        <div class="card-body">
            <h5>{{ entry.object_repr }}</h5>
            <p class="text-muted">Eliminado el {{ entry.deleted_at|date:"d/m/Y H:i" }}</p>
        </div>
    </div>
    
    {% if conflicts %}
    <div class="alert alert-warning">
        <strong>Conflicto detectado:</strong> {{ conflicts }}
    </div>
    {% endif %}
    
    <form method="post" id="restoreForm">
        {% csrf_token %}
        
        <input type="hidden" name="entry_id" value="{{ entry.id }}">
        
        <div class="form-group">
            <div class="form-check">
                <input type="checkbox" class="form-check-input" 
                       id="confirmRestore" name="confirm" required>
                <label class="form-check-label" for="confirmRestore">
                    Confirmo que deseo restaurar este elemento
                </label>
            </div>
        </div>
        
        {% if conflicts %}
        <div class="form-group">
            <label for="resolveConflicts">Método de resolución:</label>
            <select class="form-control" id="resolveConflicts" 
                    name="resolve_conflicts" required>
                <option value="">-- Seleccione --</option>
                <option value="rename">Renombrar elemento restaurado</option>
                <option value="replace">Reemplazar elemento existente</option>
                <option value="cancel">Cancelar restauración</option>
            </select>
        </div>
        <div id="conflictResolutionMessage"></div>
        {% endif %}
        
        <div class="form-group">
            <label for="notes">Notas (opcional):</label>
            <textarea class="form-control" id="notes" name="notes" 
                      rows="3" placeholder="Agregue notas..."></textarea>
        </div>
        
        <button type="submit" class="btn btn-success" id="btnRestore">
            <i class="fas fa-undo"></i> Restaurar
        </button>
        <a href="{% url 'core:recycle_bin_list' %}" class="btn btn-secondary">
            Cancelar
        </a>
    </form>
</div>
{% endblock %}
```

### Ejemplo 2: Modal de Eliminación Permanente

```django
<!-- Modal en template -->
<div class="modal fade" id="deleteModal" tabindex="-1">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <div class="modal-header bg-danger text-white">
                <h5 class="modal-title">
                    <i class="fas fa-exclamation-triangle"></i> 
                    Eliminación Permanente
                </h5>
                <button type="button" class="close text-white" data-dismiss="modal">
                    <span>&times;</span>
                </button>
            </div>
            
            <form method="post" 
                  action="{% url 'core:recycle_bin_permanent_delete' entry.id %}" 
                  id="permanentDeleteForm">
                {% csrf_token %}
                <input type="hidden" name="entry_id" value="{{ entry.id }}">
                
                <div class="modal-body">
                    <div class="alert alert-danger">
                        <strong>¡ADVERTENCIA!</strong> Esta acción es irreversible.
                    </div>
                    
                    <p>Elemento: <strong>{{ entry.object_repr }}</strong></p>
                    
                    <!-- Código de seguridad -->
                    <div class="form-group">
                        <label for="securityCode">
                            Código de Seguridad: 
                            <span class="text-danger">*</span>
                        </label>
                        <input type="password" 
                               class="form-control" 
                               id="securityCode" 
                               name="security_code" 
                               required
                               data-validate="security-code"
                               autocomplete="off"
                               placeholder="Ingrese el código">
                        <small class="form-text text-muted">
                            Ingrese el código de seguridad del sistema
                        </small>
                    </div>
                    
                    <!-- Confirmación de texto -->
                    <div class="form-group">
                        <label for="confirmText">
                            Escriba "ELIMINAR": 
                            <span class="text-danger">*</span>
                        </label>
                        <input type="text" 
                               class="form-control" 
                               id="confirmText" 
                               name="confirm_text" 
                               required
                               data-validate="confirm-text"
                               placeholder="ELIMINAR"
                               autocomplete="off">
                        <small class="form-text text-muted">
                            Debe escribir exactamente "ELIMINAR" en mayúsculas
                        </small>
                    </div>
                    
                    <!-- Motivo -->
                    <div class="form-group">
                        <label for="reason">
                            Motivo: 
                            <span class="text-danger">*</span>
                        </label>
                        <textarea class="form-control" 
                                  id="reason" 
                                  name="reason" 
                                  rows="3" 
                                  required
                                  data-validate="required"
                                  placeholder="Explique por qué es necesario eliminar este elemento (mínimo 20 caracteres)..."></textarea>
                        <small class="form-text text-muted">
                            Mínimo 20 caracteres
                        </small>
                    </div>
                </div>
                
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" 
                            data-dismiss="modal">
                        Cancelar
                    </button>
                    <button type="submit" 
                            class="btn btn-secondary" 
                            id="btnPermanentDelete" 
                            disabled>
                        <i class="fas fa-trash"></i> Eliminar Permanentemente
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>

<!-- Botón para abrir modal -->
<button type="button" class="btn btn-danger" 
        data-toggle="modal" data-target="#deleteModal">
    <i class="fas fa-trash"></i> Eliminar Permanentemente
</button>
```

### Ejemplo 3: Operaciones en Lote con JavaScript

```javascript
// Script personalizado para operaciones en lote
(function() {
    'use strict';
    
    // Selección de elementos
    const selectAllCheckbox = document.getElementById('selectAll');
    const itemCheckboxes = document.querySelectorAll('.item-checkbox');
    const bulkRestoreBtn = document.getElementById('bulkRestoreBtn');
    const bulkDeleteBtn = document.getElementById('bulkDeleteBtn');
    const selectedCountSpan = document.getElementById('selectedCount');
    
    // Actualizar contador de seleccionados
    function updateSelectedCount() {
        const selected = document.querySelectorAll('.item-checkbox:checked');
        const count = selected.length;
        
        selectedCountSpan.textContent = `${count} elemento(s) seleccionado(s)`;
        
        // Habilitar/deshabilitar botones
        bulkRestoreBtn.disabled = count === 0;
        bulkDeleteBtn.disabled = count === 0;
        
        return count;
    }
    
    // Seleccionar todos
    selectAllCheckbox.addEventListener('change', function() {
        itemCheckboxes.forEach(cb => {
            cb.checked = this.checked;
        });
        updateSelectedCount();
    });
    
    // Actualizar al cambiar selección individual
    itemCheckboxes.forEach(cb => {
        cb.addEventListener('change', updateSelectedCount);
    });
    
    // Restaurar en lote
    bulkRestoreBtn.addEventListener('click', function() {
        const selected = Array.from(
            document.querySelectorAll('.item-checkbox:checked')
        ).map(cb => cb.value);
        
        if (selected.length === 0) return;
        
        if (confirm(`¿Restaurar ${selected.length} elemento(s)?`)) {
            // Crear formulario dinámicamente
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = '/recycle-bin/bulk-restore/';
            
            // CSRF token
            const csrf = document.createElement('input');
            csrf.type = 'hidden';
            csrf.name = 'csrfmiddlewaretoken';
            csrf.value = getCsrfToken();
            form.appendChild(csrf);
            
            // Confirmación
            const confirm = document.createElement('input');
            confirm.type = 'hidden';
            confirm.name = 'confirm';
            confirm.value = 'on';
            form.appendChild(confirm);
            
            // IDs de elementos
            selected.forEach(id => {
                const input = document.createElement('input');
                input.type = 'hidden';
                input.name = 'entry_ids[]';
                input.value = id;
                form.appendChild(input);
            });
            
            // Enviar
            document.body.appendChild(form);
            form.submit();
        }
    });
    
    // Eliminar en lote
    bulkDeleteBtn.addEventListener('click', function() {
        const selected = Array.from(
            document.querySelectorAll('.item-checkbox:checked')
        );
        
        if (selected.length === 0) return;
        
        // Actualizar contador en modal
        document.getElementById('deleteCount').textContent = selected.length;
        
        // Limpiar IDs anteriores
        const form = document.getElementById('bulkDeleteForm');
        form.querySelectorAll('input[name="entry_ids[]"]').forEach(i => i.remove());
        
        // Agregar IDs seleccionados
        selected.forEach(cb => {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'entry_ids[]';
            input.value = cb.value;
            form.appendChild(input);
        });
        
        // Mostrar modal
        $('#bulkDeleteModal').modal('show');
    });
    
    // Obtener CSRF token
    function getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }
    
    // Inicializar
    updateSelectedCount();
})();
```

### Ejemplo 4: Vista API para Frontend React

```python
# apps/core/api_views.py

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import RecycleBin
from .forms import RestoreForm, PermanentDeleteForm
from .utils import RecycleBinService

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_restore_item(request, entry_id):
    """
    API endpoint para restaurar un elemento
    """
    try:
        entry = RecycleBin.objects.get(id=entry_id)
    except RecycleBin.DoesNotExist:
        return Response(
            {'error': 'Elemento no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Validar con formulario
    form = RestoreForm(request.data, entry=entry, user=request.user)
    
    if not form.is_valid():
        return Response(
            {'errors': form.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Restaurar
    success, message, restored_object = RecycleBinService.restore_object(
        entry,
        request.user,
        notes=form.cleaned_data.get('notes', '')
    )
    
    if success:
        return Response({
            'success': True,
            'message': message,
            'object_id': restored_object.pk if restored_object else None
        })
    else:
        return Response(
            {'error': message},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_permanent_delete(request, entry_id):
    """
    API endpoint para eliminación permanente
    """
    try:
        entry = RecycleBin.objects.get(id=entry_id)
    except RecycleBin.DoesNotExist:
        return Response(
            {'error': 'Elemento no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Validar con formulario
    form = PermanentDeleteForm(request.data, entry=entry, user=request.user)
    
    if not form.is_valid():
        return Response(
            {'errors': form.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Eliminar permanentemente
    success, message = RecycleBinService.permanent_delete(
        entry,
        request.user,
        form.cleaned_data['security_code'],
        reason=form.cleaned_data['reason']
    )
    
    if success:
        return Response({
            'success': True,
            'message': message
        })
    else:
        return Response(
            {'error': message},
            status=status.HTTP_400_BAD_REQUEST
        )
```

### Ejemplo 5: Componente React

```typescript
// RestoreButton.tsx
import React, { useState } from 'react';
import axios from 'axios';

interface RestoreButtonProps {
    entryId: number;
    objectName: string;
    onSuccess?: () => void;
}

export const RestoreButton: React.FC<RestoreButtonProps> = ({
    entryId,
    objectName,
    onSuccess
}) => {
    const [loading, setLoading] = useState(false);
    const [showModal, setShowModal] = useState(false);
    const [notes, setNotes] = useState('');
    const [error, setError] = useState('');
    
    const handleRestore = async () => {
        setLoading(true);
        setError('');
        
        try {
            const response = await axios.post(
                `/api/recycle-bin/${entryId}/restore/`,
                {
                    entry_id: entryId,
                    confirm: true,
                    notes: notes
                }
            );
            
            if (response.data.success) {
                setShowModal(false);
                if (onSuccess) onSuccess();
            }
        } catch (err: any) {
            setError(err.response?.data?.error || 'Error al restaurar');
        } finally {
            setLoading(false);
        }
    };
    
    return (
        <>
            <button 
                className="btn btn-success btn-sm"
                onClick={() => setShowModal(true)}
            >
                <i className="fas fa-undo"></i> Restaurar
            </button>
            
            {showModal && (
                <div className="modal show d-block" tabIndex={-1}>
                    <div className="modal-dialog">
                        <div className="modal-content">
                            <div className="modal-header">
                                <h5 className="modal-title">Restaurar Elemento</h5>
                                <button 
                                    type="button" 
                                    className="close"
                                    onClick={() => setShowModal(false)}
                                >
                                    <span>&times;</span>
                                </button>
                            </div>
                            <div className="modal-body">
                                <p>¿Restaurar <strong>{objectName}</strong>?</p>
                                
                                {error && (
                                    <div className="alert alert-danger">
                                        {error}
                                    </div>
                                )}
                                
                                <div className="form-group">
                                    <label>Notas (opcional):</label>
                                    <textarea 
                                        className="form-control"
                                        rows={3}
                                        value={notes}
                                        onChange={(e) => setNotes(e.target.value)}
                                        placeholder="Agregue notas..."
                                    />
                                </div>
                            </div>
                            <div className="modal-footer">
                                <button 
                                    type="button" 
                                    className="btn btn-secondary"
                                    onClick={() => setShowModal(false)}
                                    disabled={loading}
                                >
                                    Cancelar
                                </button>
                                <button 
                                    type="button" 
                                    className="btn btn-success"
                                    onClick={handleRestore}
                                    disabled={loading}
                                >
                                    {loading ? 'Restaurando...' : 'Restaurar'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
};
```

## 🎓 Mejores Prácticas

1. **Siempre validar en el backend**: No confiar solo en validaciones JavaScript
2. **Usar formularios Django**: Aprovechan validaciones y seguridad integradas
3. **Incluir CSRF tokens**: Protección contra ataques CSRF
4. **Registrar en auditoría**: Mantener trazabilidad de operaciones
5. **Feedback al usuario**: Mensajes claros de éxito/error
6. **Deshabilitar botones**: Prevenir doble envío durante procesamiento
7. **Validar permisos**: Verificar en cada operación
8. **Manejar errores**: Try-catch en operaciones críticas

## 📖 Recursos Adicionales

- Documentación Django Forms: https://docs.djangoproject.com/en/stable/topics/forms/
- Bootstrap 4 Forms: https://getbootstrap.com/docs/4.6/components/forms/
- JavaScript Form Validation: https://developer.mozilla.org/en-US/docs/Learn/Forms/Form_validation
