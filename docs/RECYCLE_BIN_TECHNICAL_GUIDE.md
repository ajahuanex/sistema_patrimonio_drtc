# Guía Técnica - Sistema de Papelera de Reciclaje

## Introducción

Esta guía técnica está dirigida a desarrolladores que necesitan entender, mantener o extender el sistema de papelera de reciclaje. Cubre la arquitectura, componentes, APIs y mejores prácticas de desarrollo.

## Arquitectura del Sistema

### Componentes Principales

```
┌─────────────────────────────────────────────────────────────┐
│                    Sistema de Papelera                      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │ SoftDeleteMixin │  │  RecycleBin     │  │ RecycleBin   │ │
│  │   & Manager     │  │     Model       │  │   Service    │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │ DeletionAudit   │  │  Notifications  │  │  Permissions │ │
│  │      Log        │  │    & Alerts     │  │  & Security  │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Flujo de Datos

1. **Eliminación**: Usuario → Vista → Service → SoftDeleteMixin → RecycleBin
2. **Restauración**: Usuario → Vista → Service → Validaciones → Restauración
3. **Eliminación Permanente**: Usuario → Vista → Validación Código → Service → Hard Delete
4. **Limpieza Automática**: Celery Task → Service → Validaciones → Hard Delete

## Modelos de Datos

### SoftDeleteMixin

Mixin que agrega funcionalidad de soft delete a cualquier modelo.


**Ubicación**: `apps/core/models.py`

```python
class SoftDeleteMixin(models.Model):
    """
    Mixin para agregar funcionalidad de soft delete a modelos.
    
    Campos:
    - deleted_at: Timestamp de eliminación (null si no está eliminado)
    - deleted_by: Usuario que eliminó el registro
    - deletion_reason: Motivo opcional de la eliminación
    
    Métodos:
    - soft_delete(user, reason=None): Marca el registro como eliminado
    - restore(user): Restaura el registro eliminado
    - hard_delete(): Elimina físicamente el registro
    - is_deleted: Property que indica si está eliminado
    """
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)
    deleted_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    deletion_reason = models.TextField(blank=True)
    
    objects = SoftDeleteManager()
    all_objects = models.Manager()
```

**Uso en modelos existentes:**

```python
class MiModelo(SoftDeleteMixin, models.Model):
    # Tus campos aquí
    nombre = models.CharField(max_length=100)
    
    # El mixin agrega automáticamente soft delete
```

### SoftDeleteManager

Manager personalizado que excluye automáticamente registros eliminados.

```python
class SoftDeleteManager(models.Manager):
    """
    Manager que excluye automáticamente registros eliminados.
    
    Métodos:
    - get_queryset(): Retorna solo registros no eliminados
    - deleted(): Retorna solo registros eliminados
    - with_deleted(): Retorna todos los registros
    """
    
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)
    
    def deleted(self):
        return super().get_queryset().filter(deleted_at__isnull=False)
    
    def with_deleted(self):
        return super().get_queryset()
```

### RecycleBin Model

Modelo centralizado para gestionar la papelera.

**Ubicación**: `apps/core/models.py`

```python
class RecycleBin(models.Model):
    """
    Registro centralizado de elementos en papelera.
    
    Usa GenericForeignKey para referenciar cualquier modelo.
    """
    # Referencia genérica al objeto eliminado
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Metadatos
    object_repr = models.CharField(max_length=200)
    module_name = models.CharField(max_length=50)
    
    # Auditoría
    deleted_at = models.DateTimeField(auto_now_add=True)
    deleted_by = models.ForeignKey(User, related_name='deleted_items')
    restored_at = models.DateTimeField(null=True, blank=True)
    restored_by = models.ForeignKey(User, null=True, related_name='restored_items')
    
    # Eliminación automática
    auto_delete_at = models.DateTimeField()
    
    class Meta:
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['deleted_at']),
            models.Index(fields=['auto_delete_at']),
            models.Index(fields=['module_name']),
        ]
```

### RecycleBinConfig Model

Configuración del sistema por módulo.

```python
class RecycleBinConfig(models.Model):
    """
    Configuración de papelera por módulo.
    """
    module_name = models.CharField(max_length=50, unique=True)
    retention_days = models.IntegerField(default=30)
    auto_delete_enabled = models.BooleanField(default=True)
    
    # Permisos
    can_restore_own = models.BooleanField(default=True)
    can_restore_others = models.BooleanField(default=False)
    
    # Notificaciones
    warning_days_before = models.IntegerField(default=7)
    final_warning_days_before = models.IntegerField(default=1)
```

### DeletionAuditLog Model

Registro de auditoría de operaciones.

```python
class DeletionAuditLog(models.Model):
    """
    Log de auditoría para operaciones de eliminación.
    """
    ACTION_CHOICES = [
        ('soft_delete', 'Eliminación Lógica'),
        ('restore', 'Restauración'),
        ('permanent_delete', 'Eliminación Permanente'),
        ('auto_delete', 'Eliminación Automática'),
    ]
    
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Contexto
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.TextField(blank=True)
    
    # Datos del objeto
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    object_repr = models.CharField(max_length=200)
    object_data = models.JSONField(null=True)
```

## Servicios

### RecycleBinService

Servicio centralizado para operaciones de papelera.

**Ubicación**: `apps/core/services.py`

```python
class RecycleBinService:
    """
    Servicio para gestionar operaciones de papelera.
    """
    
    @staticmethod
    def soft_delete_object(obj, user, reason=None):
        """
        Elimina lógicamente un objeto y crea entrada en papelera.
        
        Args:
            obj: Objeto a eliminar
            user: Usuario que realiza la eliminación
            reason: Motivo opcional
            
        Returns:
            RecycleBin: Entrada creada en papelera
        """
        
    @staticmethod
    def restore_object(recycle_bin_entry, user):
        """
        Restaura un objeto desde la papelera.
        
        Args:
            recycle_bin_entry: Entrada de RecycleBin
            user: Usuario que restaura
            
        Returns:
            object: Objeto restaurado
            
        Raises:
            ValidationError: Si hay conflictos
        """
        
    @staticmethod
    def permanent_delete(recycle_bin_entry, user, security_code):
        """
        Elimina permanentemente un objeto.
        
        Args:
            recycle_bin_entry: Entrada de RecycleBin
            user: Usuario que elimina
            security_code: Código de seguridad
            
        Raises:
            PermissionDenied: Si el código es incorrecto
        """
        
    @staticmethod
    def auto_cleanup():
        """
        Limpia automáticamente registros vencidos.
        
        Returns:
            dict: Estadísticas de limpieza
        """
```

## Vistas

### RecycleBinListView

Vista principal de listado de papelera.

**Ubicación**: `apps/core/views.py`

```python
class RecycleBinListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """
    Lista elementos en papelera con filtros y paginación.
    """
    model = RecycleBin
    template_name = 'core/recycle_bin_list.html'
    context_object_name = 'items'
    paginate_by = 20
    permission_required = 'core.view_recycle_bin'
    
    def get_queryset(self):
        # Aplicar filtros
        # Aplicar permisos de usuario
        # Ordenar por fecha
```

### RestoreView

Vista para restaurar objetos.

```python
class RestoreView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """
    Restaura un objeto desde la papelera.
    """
    permission_required = 'core.restore_items'
    
    def post(self, request, pk):
        # Validar permisos
        # Llamar a RecycleBinService.restore_object()
        # Manejar conflictos
        # Retornar respuesta
```

### PermanentDeleteView

Vista para eliminación permanente.

```python
class PermanentDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """
    Elimina permanentemente con código de seguridad.
    """
    permission_required = 'core.permanent_delete_items'
    
    def post(self, request, pk):
        # Validar código de seguridad
        # Verificar rate limiting
        # Llamar a RecycleBinService.permanent_delete()
        # Registrar en auditoría
```

## Comandos de Management

### cleanup_recycle_bin

Limpia automáticamente registros vencidos.

**Ubicación**: `apps/core/management/commands/cleanup_recycle_bin.py`

```bash
# Ejecutar limpieza
python manage.py cleanup_recycle_bin

# Modo dry-run (sin eliminar)
python manage.py cleanup_recycle_bin --dry-run

# Módulo específico
python manage.py cleanup_recycle_bin --module=oficinas

# Verbose
python manage.py cleanup_recycle_bin --verbose
```

### setup_recycle_bin

Configura el sistema de papelera.

```bash
# Configuración inicial
python manage.py setup_recycle_bin

# Configurar módulo específico
python manage.py setup_recycle_bin --module=bienes --retention-days=60

# Actualizar permisos
python manage.py setup_recycle_bin --setup-permissions
```

### generate_recycle_report

Genera reportes de auditoría.

```bash
# Reporte general
python manage.py generate_recycle_report

# Período específico
python manage.py generate_recycle_report --start-date=2025-01-01 --end-date=2025-01-31

# Formato específico
python manage.py generate_recycle_report --format=pdf --output=reporte.pdf
```

### restore_from_backup

Restaura desde backup en emergencias.

```bash
# Restaurar objeto específico
python manage.py restore_from_backup --object-id=123 --content-type=oficina

# Desde archivo de backup
python manage.py restore_from_backup --backup-file=backup.json
```

## Tareas de Celery

### cleanup_recycle_bin_task

Tarea periódica de limpieza automática.

**Ubicación**: `patrimonio/celery.py`

```python
@app.task
def cleanup_recycle_bin_task():
    """
    Tarea periódica para limpiar papelera.
    Ejecuta diariamente a las 2:00 AM.
    """
    from apps.core.services import RecycleBinService
    return RecycleBinService.auto_cleanup()
```

**Configuración en celery.py:**

```python
app.conf.beat_schedule = {
    'cleanup-recycle-bin': {
        'task': 'patrimonio.celery.cleanup_recycle_bin_task',
        'schedule': crontab(hour=2, minute=0),
    },
}
```

### send_recycle_warnings_task

Envía notificaciones de advertencia.

```python
@app.task
def send_recycle_warnings_task():
    """
    Envía notificaciones 7 días antes de eliminación.
    Ejecuta diariamente a las 9:00 AM.
    """
```

### send_final_warnings_task

Envía notificaciones finales.

```python
@app.task
def send_final_warnings_task():
    """
    Envía notificaciones 1 día antes de eliminación.
    Ejecuta diariamente a las 9:00 AM.
    """
```

## APIs y Endpoints

### REST API Endpoints

```python
# Listar elementos en papelera
GET /api/recycle-bin/
Query params: module, deleted_after, deleted_before, search

# Detalle de elemento
GET /api/recycle-bin/{id}/

# Restaurar elemento
POST /api/recycle-bin/{id}/restore/

# Eliminación permanente
POST /api/recycle-bin/{id}/permanent-delete/
Body: {"security_code": "CODE"}

# Restauración múltiple
POST /api/recycle-bin/bulk-restore/
Body: {"ids": [1, 2, 3]}

# Estadísticas
GET /api/recycle-bin/stats/

# Dashboard
GET /api/recycle-bin/dashboard/
```

### Respuestas de API

```json
// Éxito
{
    "success": true,
    "message": "Objeto restaurado exitosamente",
    "data": {
        "id": 123,
        "object_repr": "Oficina Central"
    }
}

// Error
{
    "success": false,
    "error": "conflict",
    "message": "Ya existe un registro con ese código",
    "details": {
        "field": "codigo",
        "existing_id": 456
    }
}
```

## Integración con Módulos Existentes

### Extender un Modelo con Soft Delete

```python
# En tu modelo
from apps.core.models import SoftDeleteMixin

class MiModelo(SoftDeleteMixin, models.Model):
    # Tus campos
    nombre = models.CharField(max_length=100)
    
    # Sobrescribir delete() para usar soft delete
    def delete(self, using=None, keep_parents=False):
        if hasattr(self, 'soft_delete'):
            # Obtener usuario del contexto
            user = getattr(self, '_current_user', None)
            self.soft_delete(user=user)
        else:
            super().delete(using=using, keep_parents=keep_parents)
```

### Actualizar Vistas Existentes

```python
# En tus vistas
class MiDeleteView(DeleteView):
    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        # Usar soft delete en lugar de delete()
        obj._current_user = request.user
        obj.delete()
        return redirect('success_url')
```

### Excluir Eliminados en Consultas

```python
# Automático con el manager por defecto
MiModelo.objects.all()  # Solo no eliminados

# Incluir eliminados explícitamente
MiModelo.objects.with_deleted()

# Solo eliminados
MiModelo.objects.deleted()
```

## Seguridad

### Código de Seguridad

El código de seguridad se configura en variables de entorno:

```python
# settings.py
PERMANENT_DELETE_CODE = os.getenv('PERMANENT_DELETE_CODE', 'CHANGE_ME')
```

**Mejores prácticas:**
- Usar código complejo (mínimo 12 caracteres)
- Cambiar periódicamente (cada 90 días)
- No compartir por canales inseguros
- Registrar todos los usos

### Rate Limiting

Protección contra fuerza bruta:

```python
# En views.py
from django.core.cache import cache

def check_rate_limit(user, action):
    key = f'rate_limit:{user.id}:{action}'
    attempts = cache.get(key, 0)
    
    if attempts >= 3:
        # Bloquear por 30 minutos
        return False
    
    cache.set(key, attempts + 1, 1800)
    return True
```

### Permisos Requeridos

```python
# Permisos del sistema
'core.view_recycle_bin'           # Ver papelera
'core.restore_items'              # Restaurar elementos
'core.permanent_delete_items'     # Eliminación permanente
'core.view_audit_logs'            # Ver auditoría
'core.export_audit_logs'          # Exportar auditoría
```

## Testing

### Tests Unitarios

```python
# tests/test_soft_delete.py
class SoftDeleteTestCase(TestCase):
    def test_soft_delete_marks_as_deleted(self):
        obj = MiModelo.objects.create(nombre="Test")
        obj.soft_delete(user=self.user)
        
        self.assertIsNotNone(obj.deleted_at)
        self.assertEqual(obj.deleted_by, self.user)
        
    def test_restore_removes_deletion_mark(self):
        obj = MiModelo.objects.create(nombre="Test")
        obj.soft_delete(user=self.user)
        obj.restore(user=self.user)
        
        self.assertIsNone(obj.deleted_at)
```

### Tests de Integración

```python
# tests/test_recycle_bin_integration.py
class RecycleBinIntegrationTestCase(TestCase):
    def test_delete_creates_recycle_bin_entry(self):
        obj = MiModelo.objects.create(nombre="Test")
        RecycleBinService.soft_delete_object(obj, self.user)
        
        self.assertTrue(RecycleBin.objects.filter(
            object_id=obj.id
        ).exists())
```

### Ejecutar Tests

```bash
# Todos los tests de papelera
python manage.py test tests.test_recycle_bin

# Tests específicos
python manage.py test tests.test_soft_delete.SoftDeleteTestCase

# Con coverage
coverage run --source='apps.core' manage.py test
coverage report
```

## Optimización de Performance

### Índices de Base de Datos

```python
class Meta:
    indexes = [
        models.Index(fields=['deleted_at']),
        models.Index(fields=['deleted_by']),
        models.Index(fields=['auto_delete_at']),
        models.Index(fields=['content_type', 'object_id']),
    ]
```

### Consultas Optimizadas

```python
# Usar select_related para ForeignKeys
RecycleBin.objects.select_related(
    'deleted_by',
    'content_type'
).all()

# Usar prefetch_related para relaciones inversas
RecycleBin.objects.prefetch_related(
    'content_object'
).all()

# Paginación eficiente
from django.core.paginator import Paginator
paginator = Paginator(queryset, 20)
```

### Caché

```python
from django.core.cache import cache

def get_recycle_bin_stats():
    key = 'recycle_bin_stats'
    stats = cache.get(key)
    
    if stats is None:
        stats = calculate_stats()
        cache.set(key, stats, 300)  # 5 minutos
    
    return stats
```

## Monitoreo y Logs

### Logging

```python
import logging
logger = logging.getLogger('recycle_bin')

# En operaciones críticas
logger.info(f'Soft delete: {obj} by {user}')
logger.warning(f'Failed restore attempt: {obj}')
logger.error(f'Permanent delete failed: {obj}')
```

### Métricas

```python
# Métricas a monitorear
- Número de elementos en papelera
- Tasa de restauración vs eliminación
- Tiempo promedio en papelera
- Intentos fallidos de código de seguridad
- Performance de consultas
```

## Troubleshooting

### Problema: Registros no se eliminan automáticamente

**Diagnóstico:**
```bash
# Verificar configuración de Celery
python manage.py shell
>>> from patrimonio.celery import app
>>> app.conf.beat_schedule

# Verificar que Celery Beat está corriendo
celery -A patrimonio beat --loglevel=info
```

**Solución:**
- Asegurar que Celery Beat está activo
- Verificar configuración de tareas periódicas
- Revisar logs de Celery

### Problema: Conflictos al restaurar

**Diagnóstico:**
```python
# Verificar conflictos de unicidad
obj = RecycleBin.objects.get(pk=123)
MiModelo.objects.filter(codigo=obj.content_object.codigo).exists()
```

**Solución:**
- Resolver conflictos manualmente
- Asignar nuevo código
- Eliminar registro conflictivo

### Problema: Performance lenta en listados

**Diagnóstico:**
```python
# Analizar consultas
from django.db import connection
print(connection.queries)
```

**Solución:**
- Agregar índices necesarios
- Usar select_related/prefetch_related
- Implementar paginación
- Activar caché

## Extensiones Futuras

### Ideas para Mejoras

1. **Versionado de Objetos**
   - Guardar múltiples versiones antes de eliminar
   - Permitir restaurar a versión específica

2. **Papelera Compartida**
   - Compartir elementos eliminados entre usuarios
   - Colaboración en restauración

3. **Reglas de Retención Avanzadas**
   - Retención basada en importancia
   - Retención por categoría de datos

4. **Integración con Backup**
   - Backup automático antes de eliminación permanente
   - Restauración desde backup externo

5. **Machine Learning**
   - Predecir probabilidad de restauración
   - Sugerir limpieza inteligente

## Referencias

- **Django Documentation**: https://docs.djangoproject.com/
- **Celery Documentation**: https://docs.celeryproject.org/
- **Soft Delete Pattern**: https://en.wikipedia.org/wiki/Soft_deletion
- **Código Fuente**: Ver archivos en `apps/core/`

## Contacto

Para consultas técnicas:
- **Email**: dev@patrimonio.gob
- **Repositorio**: [URL del repositorio]
- **Issues**: [URL de issues]
