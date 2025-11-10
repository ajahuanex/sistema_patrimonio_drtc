# DeletionAuditLog - Referencia Rápida

## 🚀 Inicio Rápido

### Importar
```python
from apps.core.models import DeletionAuditLog
from apps.core.utils import RecycleBinService
```

### Logging Automático (Recomendado)
```python
# El logging es automático al usar RecycleBinService
success, msg, entry = RecycleBinService.soft_delete_object(
    obj, user, reason='Motivo', 
    ip_address=request.META.get('REMOTE_ADDR'),
    user_agent=request.META.get('HTTP_USER_AGENT', '')
)
```

### Logging Manual
```python
# Soft delete
DeletionAuditLog.log_soft_delete(obj, user, reason='...', ip_address='...', user_agent='...')

# Restore
DeletionAuditLog.log_restore(obj, user, ip_address='...', user_agent='...')

# Permanent delete
DeletionAuditLog.log_permanent_delete(obj, user, reason='...', security_code_used=True)

# Failed operation
DeletionAuditLog.log_failed_operation('restore', obj, user, error_message='...')

# Bulk operation
DeletionAuditLog.log_bulk_operation('bulk_restore', [obj1, obj2], user, metadata={...})
```

## 🔍 Consultas Comunes

### Básicas
```python
# Todos los logs
DeletionAuditLog.objects.all()

# Por usuario
DeletionAuditLog.objects.filter(user=mi_usuario)

# Por acción
DeletionAuditLog.objects.filter(action='soft_delete')

# Por módulo
DeletionAuditLog.objects.filter(module_name='oficinas')

# Últimas 24 horas
from django.utils import timezone
from datetime import timedelta
DeletionAuditLog.objects.filter(
    timestamp__gte=timezone.now() - timedelta(days=1)
)
```

### Avanzadas
```python
# Logs de un objeto específico
from django.contrib.contenttypes.models import ContentType
ct = ContentType.objects.get_for_model(mi_objeto)
DeletionAuditLog.objects.filter(content_type=ct, object_id=mi_objeto.pk)

# Logs exitosos vs fallidos
DeletionAuditLog.objects.filter(success=True)
DeletionAuditLog.objects.filter(success=False)

# Con código de seguridad
DeletionAuditLog.objects.filter(security_code_used=True)

# Por IP
DeletionAuditLog.objects.filter(ip_address='192.168.1.1')
```

### Estadísticas
```python
from django.db.models import Count

# Por acción
DeletionAuditLog.objects.values('action').annotate(count=Count('id'))

# Por usuario
DeletionAuditLog.objects.values('user__username').annotate(count=Count('id'))

# Por módulo
DeletionAuditLog.objects.values('module_name').annotate(count=Count('id'))
```

## 📊 Acceso a Datos

### Información Básica
```python
log = DeletionAuditLog.objects.first()

log.action                    # 'soft_delete', 'restore', etc.
log.get_action_display()      # 'Eliminación Lógica', etc.
log.get_action_icon()         # '🗑️', '♻️', '❌', etc.
log.get_action_color()        # 'warning', 'success', 'danger'
log.user.username             # Nombre de usuario
log.object_repr               # Representación del objeto
log.module_name               # 'oficinas', 'bienes', etc.
log.timestamp                 # Fecha y hora
log.ip_address                # IP del usuario
log.user_agent                # User Agent
log.reason                    # Motivo
log.success                   # True/False
log.error_message             # Mensaje de error si falló
```

### Snapshot
```python
log = DeletionAuditLog.objects.filter(action='permanent_delete').first()

snapshot = log.object_snapshot
snapshot['codigo']            # Valor del campo
snapshot['nombre']            # Valor del campo
```

### Estado Anterior
```python
log = DeletionAuditLog.objects.filter(action='restore').first()

previous = log.previous_state
previous['deleted_at']        # Cuándo fue eliminado
previous['deleted_by']        # Quién lo eliminó
```

### Metadatos
```python
log = DeletionAuditLog.objects.filter(action='bulk_restore').first()

metadata = log.metadata
metadata['total_count']       # Total de elementos
metadata['restored_count']    # Elementos restaurados
```

## 🎨 Uso en Templates

### Lista Simple
```html
{% for log in logs %}
<tr>
    <td>{{ log.get_action_icon }} {{ log.get_action_display }}</td>
    <td>{{ log.user.username }}</td>
    <td>{{ log.object_repr }}</td>
    <td>{{ log.timestamp|date:"d/m/Y H:i" }}</td>
</tr>
{% endfor %}
```

### Con Badges
```html
<span class="badge badge-{{ log.get_action_color }}">
    {{ log.get_action_icon }} {{ log.get_action_display }}
</span>
```

### Estado
```html
{% if log.success %}
    <span class="badge badge-success">✓ Exitoso</span>
{% else %}
    <span class="badge badge-danger">✗ Fallido</span>
{% endif %}
```

## 🔐 Permisos

### Verificar Permisos
```python
def can_view_audit_logs(user):
    return user.profile.role in ['administrador', 'auditor']

# En vista
if not can_view_audit_logs(request.user):
    return redirect('home')
```

### Filtrar por Permisos
```python
def get_logs_for_user(requesting_user):
    if requesting_user.profile.is_administrador:
        return DeletionAuditLog.objects.all()
    else:
        return DeletionAuditLog.objects.filter(user=requesting_user)
```

## 📈 Reportes

### Reporte Simple
```python
from datetime import date

logs = DeletionAuditLog.objects.filter(
    timestamp__date__gte=date(2025, 1, 1),
    timestamp__date__lte=date(2025, 1, 31)
)

report = {
    'total': logs.count(),
    'successful': logs.filter(success=True).count(),
    'failed': logs.filter(success=False).count(),
}
```

### Exportar a CSV
```python
import csv
from django.http import HttpResponse

response = HttpResponse(content_type='text/csv')
response['Content-Disposition'] = 'attachment; filename="logs.csv"'

writer = csv.writer(response)
writer.writerow(['Fecha', 'Acción', 'Usuario', 'Objeto', 'Éxito'])

for log in DeletionAuditLog.objects.all():
    writer.writerow([
        log.timestamp,
        log.get_action_display(),
        log.user.username,
        log.object_repr,
        'Sí' if log.success else 'No'
    ])

return response
```

## 🎯 Tipos de Acciones

| Código | Nombre | Icono | Color |
|--------|--------|-------|-------|
| `soft_delete` | Eliminación Lógica | 🗑️ | warning |
| `restore` | Restauración | ♻️ | success |
| `permanent_delete` | Eliminación Permanente | ❌ | danger |
| `auto_delete` | Eliminación Automática | ⏰ | info |
| `bulk_restore` | Restauración en Lote | ♻️📦 | success |
| `bulk_delete` | Eliminación en Lote | ❌📦 | danger |
| `failed_restore` | Restauración Fallida | ⚠️♻️ | danger |
| `failed_delete` | Eliminación Fallida | ⚠️❌ | danger |

## 💡 Tips

### Performance
- Usa `select_related('user', 'content_type')` para optimizar consultas
- Implementa paginación para listados grandes
- Los índices están optimizados para consultas por timestamp, usuario y acción

### Seguridad
- Siempre verifica permisos antes de mostrar logs
- No expongas snapshots completos a usuarios no autorizados
- Registra IP y User-Agent para auditoría forense

### Mejores Prácticas
- Proporciona razones descriptivas en las operaciones
- Usa logging automático cuando sea posible
- No elimines logs de auditoría
- Revisa logs regularmente para detectar patrones

## 🔗 Enlaces Rápidos

- **Modelo:** `apps/core/models.py` (línea ~615)
- **Servicio:** `apps/core/utils.py` (RecycleBinService)
- **Tests:** `tests/test_deletion_audit_log.py`
- **Documentación completa:** `TASK_19_USAGE_GUIDE.md`

## 📞 Soporte

Para más información, consulta:
- `TASK_19_SUMMARY.md` - Resumen técnico completo
- `TASK_19_USAGE_GUIDE.md` - Guía de uso detallada
- `TASK_19_VERIFICATION.md` - Checklist de verificación
