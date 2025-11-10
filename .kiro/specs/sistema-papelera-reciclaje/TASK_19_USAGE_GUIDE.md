# Guía de Uso: DeletionAuditLog

## 📖 Introducción

El sistema `DeletionAuditLog` proporciona trazabilidad completa de todas las operaciones de eliminación, restauración y eliminación permanente en el sistema de papelera de reciclaje.

## 🚀 Uso Básico

### Logging Automático

El logging es **automático** cuando se usan los métodos de `RecycleBinService`. No necesitas hacer nada adicional:

```python
from apps.core.utils import RecycleBinService

# Soft delete - se registra automáticamente
success, message, recycle_entry = RecycleBinService.soft_delete_object(
    obj=mi_oficina,
    user=request.user,
    reason='Oficina cerrada',
    ip_address=request.META.get('REMOTE_ADDR'),
    user_agent=request.META.get('HTTP_USER_AGENT', '')
)

# Restore - se registra automáticamente
success, message, restored = RecycleBinService.restore_object(
    recycle_entry=entry,
    user=request.user,
    notes='Reapertura de oficina',
    ip_address=request.META.get('REMOTE_ADDR'),
    user_agent=request.META.get('HTTP_USER_AGENT', '')
)

# Permanent delete - se registra automáticamente
success, message = RecycleBinService.permanent_delete(
    recycle_entry=entry,
    user=request.user,
    security_code='CODIGO123',
    reason='Eliminación definitiva',
    ip_address=request.META.get('REMOTE_ADDR'),
    user_agent=request.META.get('HTTP_USER_AGENT', '')
)
```

### Logging Manual

Si necesitas registrar operaciones manualmente:

```python
from apps.core.models import DeletionAuditLog

# Registrar soft delete
audit_log = DeletionAuditLog.log_soft_delete(
    obj=mi_objeto,
    user=request.user,
    reason='Motivo de eliminación',
    ip_address='192.168.1.1',
    user_agent='Mozilla/5.0...',
    recycle_bin_entry=recycle_entry
)

# Registrar restauración
audit_log = DeletionAuditLog.log_restore(
    obj=mi_objeto,
    user=request.user,
    ip_address='192.168.1.1',
    user_agent='Mozilla/5.0...',
    recycle_bin_entry=recycle_entry,
    previous_state={'deleted_at': '2025-01-01', 'deleted_by': 'user1'}
)

# Registrar eliminación permanente
audit_log = DeletionAuditLog.log_permanent_delete(
    obj=mi_objeto,
    user=request.user,
    reason='Eliminación definitiva',
    ip_address='192.168.1.1',
    user_agent='Mozilla/5.0...',
    recycle_bin_entry=recycle_entry,
    security_code_used=True
)

# Registrar operación fallida
audit_log = DeletionAuditLog.log_failed_operation(
    action='restore',
    obj=mi_objeto,
    user=request.user,
    error_message='Conflicto: código duplicado',
    ip_address='192.168.1.1',
    user_agent='Mozilla/5.0...'
)

# Registrar operación en lote
logs = DeletionAuditLog.log_bulk_operation(
    action='bulk_restore',
    objects=[obj1, obj2, obj3],
    user=request.user,
    ip_address='192.168.1.1',
    user_agent='Mozilla/5.0...',
    metadata={'total_count': 3, 'restored_count': 3}
)
```

## 🔍 Consultas de Auditoría

### Consultas Básicas

```python
from apps.core.models import DeletionAuditLog

# Todos los logs de auditoría (ordenados por más reciente)
all_logs = DeletionAuditLog.objects.all()

# Logs de un usuario específico
user_logs = DeletionAuditLog.objects.filter(user=mi_usuario)

# Logs de una acción específica
soft_deletes = DeletionAuditLog.objects.filter(action='soft_delete')
restores = DeletionAuditLog.objects.filter(action='restore')
permanent_deletes = DeletionAuditLog.objects.filter(action='permanent_delete')

# Logs de un módulo específico
oficinas_logs = DeletionAuditLog.objects.filter(module_name='oficinas')
bienes_logs = DeletionAuditLog.objects.filter(module_name='bienes')

# Logs de un objeto específico
from django.contrib.contenttypes.models import ContentType

content_type = ContentType.objects.get_for_model(mi_oficina)
object_logs = DeletionAuditLog.objects.filter(
    content_type=content_type,
    object_id=mi_oficina.pk
)
```

### Consultas Avanzadas

```python
from django.utils import timezone
from datetime import timedelta

# Logs de las últimas 24 horas
yesterday = timezone.now() - timedelta(days=1)
recent_logs = DeletionAuditLog.objects.filter(timestamp__gte=yesterday)

# Logs exitosos vs fallidos
successful_logs = DeletionAuditLog.objects.filter(success=True)
failed_logs = DeletionAuditLog.objects.filter(success=False)

# Logs con código de seguridad usado
security_logs = DeletionAuditLog.objects.filter(security_code_used=True)

# Logs de una IP específica
ip_logs = DeletionAuditLog.objects.filter(ip_address='192.168.1.1')

# Logs por rango de fechas
from datetime import date

start_date = date(2025, 1, 1)
end_date = date(2025, 1, 31)
date_range_logs = DeletionAuditLog.objects.filter(
    timestamp__date__gte=start_date,
    timestamp__date__lte=end_date
)

# Logs de eliminaciones permanentes con snapshot
permanent_with_snapshot = DeletionAuditLog.objects.filter(
    action='permanent_delete',
    object_snapshot__isnull=False
)
```

### Estadísticas

```python
from django.db.models import Count

# Contar logs por acción
stats_by_action = DeletionAuditLog.objects.values('action').annotate(
    count=Count('id')
).order_by('-count')

# Contar logs por usuario
stats_by_user = DeletionAuditLog.objects.values('user__username').annotate(
    count=Count('id')
).order_by('-count')

# Contar logs por módulo
stats_by_module = DeletionAuditLog.objects.values('module_name').annotate(
    count=Count('id')
).order_by('-count')

# Tasa de éxito
total_logs = DeletionAuditLog.objects.count()
successful = DeletionAuditLog.objects.filter(success=True).count()
success_rate = (successful / total_logs * 100) if total_logs > 0 else 0
```

## 📊 Acceso a Datos del Log

### Información Básica

```python
log = DeletionAuditLog.objects.first()

# Información de la acción
print(log.action)  # 'soft_delete', 'restore', etc.
print(log.get_action_display())  # 'Eliminación Lógica', 'Restauración', etc.
print(log.get_action_icon())  # '🗑️', '♻️', '❌', etc.
print(log.get_action_color())  # 'warning', 'success', 'danger', etc.

# Información del usuario
print(log.user.username)
print(log.user.get_full_name())

# Información del objeto
print(log.object_repr)  # Representación en texto
print(log.module_name)  # 'oficinas', 'bienes', etc.
print(log.content_type)  # ContentType del objeto
print(log.object_id)  # ID del objeto

# Contexto
print(log.timestamp)  # Fecha y hora
print(log.ip_address)  # IP del usuario
print(log.user_agent)  # User Agent del navegador
print(log.reason)  # Motivo de la acción

# Estado
print(log.success)  # True/False
print(log.error_message)  # Mensaje de error si falló
```

### Snapshot del Objeto

```python
log = DeletionAuditLog.objects.filter(
    action='permanent_delete'
).first()

# Acceder al snapshot
snapshot = log.object_snapshot
print(snapshot['codigo'])  # 'OF001'
print(snapshot['nombre'])  # 'Oficina Central'
print(snapshot['direccion'])  # 'Calle Principal 123'

# Verificar si tiene snapshot
if log.object_snapshot:
    print("Snapshot disponible")
    for field, value in log.object_snapshot.items():
        print(f"{field}: {value}")
```

### Estado Anterior (Restauraciones)

```python
log = DeletionAuditLog.objects.filter(action='restore').first()

# Acceder al estado anterior
previous = log.previous_state
print(previous['deleted_at'])  # Cuándo fue eliminado
print(previous['deleted_by'])  # Quién lo eliminó
print(previous['deletion_reason'])  # Por qué fue eliminado
```

### Metadatos (Operaciones en Lote)

```python
log = DeletionAuditLog.objects.filter(action='bulk_restore').first()

# Acceder a metadatos
metadata = log.metadata
print(metadata['total_count'])  # Total de elementos
print(metadata['restored_count'])  # Elementos restaurados
print(metadata['error_count'])  # Elementos con error
print(metadata['notes'])  # Notas adicionales
```

## 🎨 Uso en Templates

### Mostrar Logs en una Vista

```python
# views.py
from apps.core.models import DeletionAuditLog

def audit_logs_view(request):
    logs = DeletionAuditLog.objects.select_related(
        'user', 'content_type'
    ).all()[:100]  # Últimos 100 logs
    
    context = {
        'logs': logs
    }
    return render(request, 'audit_logs.html', context)
```

```html
<!-- audit_logs.html -->
<table class="table">
    <thead>
        <tr>
            <th>Acción</th>
            <th>Usuario</th>
            <th>Objeto</th>
            <th>Módulo</th>
            <th>Fecha</th>
            <th>Estado</th>
        </tr>
    </thead>
    <tbody>
        {% for log in logs %}
        <tr>
            <td>
                <span class="badge badge-{{ log.get_action_color }}">
                    {{ log.get_action_icon }} {{ log.get_action_display }}
                </span>
            </td>
            <td>{{ log.user.username }}</td>
            <td>{{ log.object_repr }}</td>
            <td>{{ log.module_name|title }}</td>
            <td>{{ log.timestamp|date:"d/m/Y H:i" }}</td>
            <td>
                {% if log.success %}
                    <span class="badge badge-success">✓ Exitoso</span>
                {% else %}
                    <span class="badge badge-danger">✗ Fallido</span>
                {% endif %}
            </td>
        </tr>
        {% endfor %}
    </tbody>
</table>
```

### Mostrar Detalles del Log

```html
<!-- audit_log_detail.html -->
<div class="card">
    <div class="card-header">
        <h3>
            {{ log.get_action_icon }} {{ log.get_action_display }}
        </h3>
    </div>
    <div class="card-body">
        <dl class="row">
            <dt class="col-sm-3">Usuario:</dt>
            <dd class="col-sm-9">{{ log.user.get_full_name }}</dd>
            
            <dt class="col-sm-3">Objeto:</dt>
            <dd class="col-sm-9">{{ log.object_repr }}</dd>
            
            <dt class="col-sm-3">Módulo:</dt>
            <dd class="col-sm-9">{{ log.module_name|title }}</dd>
            
            <dt class="col-sm-3">Fecha:</dt>
            <dd class="col-sm-9">{{ log.timestamp }}</dd>
            
            <dt class="col-sm-3">IP:</dt>
            <dd class="col-sm-9">{{ log.ip_address|default:"N/A" }}</dd>
            
            {% if log.reason %}
            <dt class="col-sm-3">Motivo:</dt>
            <dd class="col-sm-9">{{ log.reason }}</dd>
            {% endif %}
            
            {% if log.object_snapshot %}
            <dt class="col-sm-3">Snapshot:</dt>
            <dd class="col-sm-9">
                <pre>{{ log.object_snapshot|pprint }}</pre>
            </dd>
            {% endif %}
        </dl>
    </div>
</div>
```

## 🔐 Permisos y Seguridad

### Verificar Permisos para Ver Logs

```python
def can_view_audit_logs(user):
    """Solo administradores y auditores pueden ver logs"""
    if not hasattr(user, 'profile'):
        return False
    return user.profile.role in ['administrador', 'auditor']

# En una vista
@login_required
def audit_logs_view(request):
    if not can_view_audit_logs(request.user):
        messages.error(request, 'No tiene permisos para ver logs de auditoría')
        return redirect('home')
    
    logs = DeletionAuditLog.objects.all()
    # ...
```

### Filtrar Logs por Usuario

```python
def get_user_audit_logs(user, requesting_user):
    """
    Obtiene logs de auditoría según permisos del usuario solicitante
    """
    if requesting_user.profile.is_administrador:
        # Administradores ven todos los logs
        return DeletionAuditLog.objects.filter(user=user)
    elif requesting_user.profile.is_auditor:
        # Auditores ven todos los logs
        return DeletionAuditLog.objects.filter(user=user)
    else:
        # Usuarios regulares solo ven sus propios logs
        if requesting_user == user:
            return DeletionAuditLog.objects.filter(user=user)
        else:
            return DeletionAuditLog.objects.none()
```

## 📈 Reportes y Análisis

### Generar Reporte de Actividad

```python
from django.utils import timezone
from datetime import timedelta

def generate_activity_report(start_date, end_date):
    """Genera reporte de actividad de auditoría"""
    logs = DeletionAuditLog.objects.filter(
        timestamp__date__gte=start_date,
        timestamp__date__lte=end_date
    )
    
    report = {
        'period': f"{start_date} - {end_date}",
        'total_actions': logs.count(),
        'by_action': {},
        'by_user': {},
        'by_module': {},
        'success_rate': 0,
        'failed_actions': []
    }
    
    # Estadísticas por acción
    for action_code, action_name in DeletionAuditLog.ACTION_CHOICES:
        count = logs.filter(action=action_code).count()
        if count > 0:
            report['by_action'][action_name] = count
    
    # Estadísticas por usuario
    user_stats = logs.values('user__username').annotate(
        count=Count('id')
    ).order_by('-count')
    report['by_user'] = {
        stat['user__username']: stat['count'] 
        for stat in user_stats
    }
    
    # Estadísticas por módulo
    module_stats = logs.values('module_name').annotate(
        count=Count('id')
    ).order_by('-count')
    report['by_module'] = {
        stat['module_name']: stat['count'] 
        for stat in module_stats
    }
    
    # Tasa de éxito
    total = logs.count()
    successful = logs.filter(success=True).count()
    report['success_rate'] = (successful / total * 100) if total > 0 else 0
    
    # Acciones fallidas
    failed = logs.filter(success=False).values(
        'action', 'object_repr', 'error_message', 'timestamp'
    )
    report['failed_actions'] = list(failed)
    
    return report
```

## 🛠️ Mantenimiento

### Limpiar Logs Antiguos (Opcional)

```python
from django.utils import timezone
from datetime import timedelta

def cleanup_old_audit_logs(days=365):
    """
    Elimina logs de auditoría más antiguos que X días
    NOTA: Usar con precaución, los logs son importantes para auditoría
    """
    cutoff_date = timezone.now() - timedelta(days=days)
    old_logs = DeletionAuditLog.objects.filter(timestamp__lt=cutoff_date)
    count = old_logs.count()
    old_logs.delete()
    return count
```

### Exportar Logs a CSV

```python
import csv
from django.http import HttpResponse

def export_audit_logs_csv(request):
    """Exporta logs de auditoría a CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="audit_logs.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Fecha', 'Acción', 'Usuario', 'Objeto', 'Módulo', 
        'IP', 'Éxito', 'Motivo'
    ])
    
    logs = DeletionAuditLog.objects.all()
    for log in logs:
        writer.writerow([
            log.timestamp,
            log.get_action_display(),
            log.user.username,
            log.object_repr,
            log.module_name,
            log.ip_address or '',
            'Sí' if log.success else 'No',
            log.reason or ''
        ])
    
    return response
```

## 💡 Mejores Prácticas

1. **Siempre proporcionar contexto**: Incluye `ip_address` y `user_agent` cuando sea posible
2. **Motivos descriptivos**: Proporciona razones claras para las acciones
3. **No eliminar logs**: Los logs de auditoría deben preservarse permanentemente
4. **Revisar logs regularmente**: Monitorea patrones sospechosos
5. **Usar índices**: Las consultas están optimizadas, usa los campos indexados
6. **Paginación**: Usa paginación para listados grandes de logs
7. **Permisos estrictos**: Solo administradores y auditores deben ver logs completos
