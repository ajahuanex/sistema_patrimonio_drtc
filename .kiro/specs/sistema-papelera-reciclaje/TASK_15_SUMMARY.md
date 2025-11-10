# Task 15: Implementación de Eliminación Automática por Tiempo - Resumen

## ✅ Implementación Completada

Se ha implementado exitosamente el sistema de eliminación automática por tiempo para la papelera de reciclaje, cumpliendo con todos los requisitos especificados.

## 📋 Componentes Implementados

### 1. Comando de Management: `cleanup_recycle_bin`

**Ubicación:** `apps/core/management/commands/cleanup_recycle_bin.py`

**Características:**
- ✅ Elimina permanentemente elementos que han excedido su tiempo de retención
- ✅ Respeta la configuración `auto_delete_enabled` por módulo
- ✅ Soporta modo `--dry-run` para previsualización sin eliminación
- ✅ Permite filtrar por módulo específico con `--module`
- ✅ Opción `--force` para ignorar `auto_delete_enabled`
- ✅ Opción `--days` para sobrescribir días de retención
- ✅ Crea registros de auditoría para cada eliminación
- ✅ Manejo robusto de errores individuales
- ✅ Reportes detallados por módulo

**Uso:**
```bash
# Limpieza normal
python manage.py cleanup_recycle_bin

# Modo dry-run (previsualización)
python manage.py cleanup_recycle_bin --dry-run

# Limpiar solo un módulo específico
python manage.py cleanup_recycle_bin --module oficinas

# Forzar eliminación incluso si auto_delete está deshabilitado
python manage.py cleanup_recycle_bin --force

# Sobrescribir días de retención
python manage.py cleanup_recycle_bin --days 15
```

### 2. Tarea de Celery: `cleanup_recycle_bin_task`

**Ubicación:** `apps/core/tasks.py`

**Características:**
- ✅ Tarea asíncrona para ejecución automática
- ✅ Procesa múltiples módulos en una sola ejecución
- ✅ Respeta configuración `auto_delete_enabled` por módulo
- ✅ Crea registros de auditoría automáticamente
- ✅ Manejo de errores sin fallar completamente
- ✅ Retorna resultado detallado con estadísticas
- ✅ Logging completo de operaciones

**Resultado de la tarea:**
```python
{
    'status': 'success',
    'eliminados': 5,
    'total_encontrados': 5,
    'modulos': {
        'oficinas': {
            'eliminados': 2,
            'omitidos': 0,
            'razon': 'success'
        },
        'catalogo': {
            'eliminados': 3,
            'omitidos': 0,
            'razon': 'success'
        },
        'bienes': {
            'eliminados': 0,
            'omitidos': 5,
            'razon': 'auto_delete_disabled'
        }
    },
    'errores': [],
    'timestamp': '2025-01-09T10:30:00'
}
```

### 3. Configuración de Celery Beat

**Ubicación:** `patrimonio/settings.py`

**Programación:**
- ✅ Tarea programada para ejecutarse diariamente a las 4:00 AM
- ✅ Cola dedicada `maintenance` para tareas de mantenimiento
- ✅ Configuración en `CELERY_BEAT_SCHEDULE`

```python
'cleanup-recycle-bin': {
    'task': 'apps.core.tasks.cleanup_recycle_bin_task',
    'schedule': crontab(hour=4, minute=0),
}
```

### 4. Configuración por Módulo

**Modelo:** `RecycleBinConfig`

**Campos relevantes:**
- `retention_days`: Días que los elementos permanecen en papelera (default: 30)
- `auto_delete_enabled`: Habilita/deshabilita eliminación automática (default: True)
- `warning_days_before`: Días antes para enviar advertencia (default: 7)
- `final_warning_days_before`: Días antes para advertencia final (default: 1)

**Ejemplo de configuración:**
```python
# Oficinas: 30 días de retención, auto-delete habilitado
RecycleBinConfig.objects.create(
    module_name='oficinas',
    retention_days=30,
    auto_delete_enabled=True,
    warning_days_before=7,
    final_warning_days_before=1
)

# Bienes: 60 días de retención, auto-delete deshabilitado
RecycleBinConfig.objects.create(
    module_name='bienes',
    retention_days=60,
    auto_delete_enabled=False,
    warning_days_before=10,
    final_warning_days_before=2
)
```

### 5. Tests Comprehensivos

**Ubicación:** `tests/test_recycle_bin_cleanup.py`

**Cobertura de tests:**
- ✅ Comando sin elementos para eliminar
- ✅ Comando elimina elementos expirados
- ✅ Modo dry-run no elimina elementos
- ✅ Creación de audit logs
- ✅ Tarea de Celery sin elementos
- ✅ Tarea de Celery elimina elementos expirados
- ✅ Tarea crea audit logs
- ✅ Diferentes retention_days por módulo
- ✅ Cálculo automático de auto_delete_at
- ✅ Configuración por defecto si no existe

## 🔧 Integración con Sistema Existente

### Variables de Entorno

Las siguientes variables están disponibles en `settings.py`:

```python
# Código de seguridad para eliminación permanente
PERMANENT_DELETE_CODE = config('PERMANENT_DELETE_CODE', default='CHANGE-THIS-IN-PRODUCTION')

# Días de retención por defecto
RECYCLE_BIN_RETENTION_DAYS = config('RECYCLE_BIN_RETENTION_DAYS', default=30, cast=int)

# Habilitar/deshabilitar limpieza automática globalmente
RECYCLE_BIN_AUTO_CLEANUP_ENABLED = config('RECYCLE_BIN_AUTO_CLEANUP_ENABLED', default=True, cast=bool)
```

### Modelo RecycleBin

El modelo `RecycleBin` calcula automáticamente `auto_delete_at` al guardar:

```python
def save(self, *args, **kwargs):
    if not self.auto_delete_at and not self.is_restored:
        # Obtener configuración de retención por módulo
        retention_days = self.get_retention_days_for_module()
        self.auto_delete_at = self.deleted_at + timedelta(days=retention_days)
    
    super().save(*args, **kwargs)
```

### Propiedades Útiles

```python
# Días restantes hasta eliminación automática
recycle_entry.days_until_auto_delete  # int o None

# ¿Está cerca de la eliminación automática? (≤7 días)
recycle_entry.is_near_auto_delete  # bool

# ¿Está listo para eliminación automática?
recycle_entry.is_ready_for_auto_delete  # bool
```

## 📊 Flujo de Eliminación Automática

```
1. Elemento eliminado (soft delete)
   ↓
2. Entrada creada en RecycleBin
   ↓
3. auto_delete_at calculado automáticamente
   (deleted_at + retention_days del módulo)
   ↓
4. Tarea de Celery ejecuta diariamente (4:00 AM)
   ↓
5. Verifica elementos con auto_delete_at ≤ ahora
   ↓
6. Verifica auto_delete_enabled del módulo
   ↓
7. Si habilitado:
   - Crea registro de auditoría
   - Elimina permanentemente el objeto (hard_delete)
   - Elimina entrada de RecycleBin
   ↓
8. Si deshabilitado:
   - Omite el elemento
   - Registra en resultado como 'omitido'
```

## 🔍 Auditoría

Cada eliminación automática crea un registro en `AuditLog`:

```python
AuditLog.objects.create(
    user_id=1,  # Sistema
    action='delete',
    model_name='oficina',
    object_id='123',
    object_repr='Oficina Central',
    changes={
        'tipo': 'eliminacion_automatica',
        'dias_en_papelera': 35,
        'module_name': 'oficinas',
        'deleted_by': 'admin',
        'deletion_reason': 'Reorganización',
        'auto_delete_at': '2025-02-15T04:00:00'
    }
)
```

## 🚀 Despliegue

### 1. Ejecutar Migraciones

```bash
python manage.py migrate
```

### 2. Configurar Módulos

```bash
python manage.py setup_recycle_bin
```

### 3. Configurar Variables de Entorno

```bash
# .env o .env.prod
RECYCLE_BIN_RETENTION_DAYS=30
RECYCLE_BIN_AUTO_CLEANUP_ENABLED=True
```

### 4. Iniciar Celery Worker y Beat

```bash
# Worker
celery -A patrimonio worker -l info -Q maintenance

# Beat (programador)
celery -A patrimonio beat -l info
```

### 5. Verificar Configuración

```bash
# Dry-run para verificar
python manage.py cleanup_recycle_bin --dry-run
```

## 📈 Monitoreo

### Logs de Celery

```python
# Ver logs de la tarea
logger.info("Iniciando limpieza automática de papelera de reciclaje")
logger.info(f"Encontrados {total_elementos} elementos para eliminación automática")
logger.info(f"Módulo {module_name}: {eliminados_modulo} elementos eliminados")
logger.error(f"Error eliminando {item.object_repr}: {str(e)}")
```

### Estadísticas

```python
# Obtener estadísticas de limpieza
from apps.core.tasks import cleanup_recycle_bin_task

resultado = cleanup_recycle_bin_task()
print(f"Eliminados: {resultado['eliminados']}")
print(f"Errores: {len(resultado['errores'])}")
print(f"Módulos procesados: {resultado['modulos']}")
```

## ✅ Requisitos Cumplidos

- ✅ **5.1**: Eliminación automática basada en auto_delete_at
- ✅ **5.2**: Configuración de días de retención por módulo
- ✅ **5.5**: Tarea de Celery para ejecución automática

## 🎯 Próximos Pasos

Para completar el sistema de papelera de reciclaje, los siguientes tasks son:

- **Task 16**: Sistema de notificaciones de advertencia (7 días y 1 día antes)
- **Task 17**: Dashboard de estadísticas de papelera
- **Task 18**: Comandos de management adicionales

## 📝 Notas Importantes

1. **Seguridad**: La eliminación automática respeta `auto_delete_enabled` por módulo
2. **Auditoría**: Todas las eliminaciones se registran en `AuditLog`
3. **Recuperación**: Los elementos pueden restaurarse antes de `auto_delete_at`
4. **Flexibilidad**: Diferentes módulos pueden tener diferentes políticas de retención
5. **Monitoreo**: Los logs de Celery permiten rastrear todas las operaciones

## 🔗 Referencias

- Comando: `apps/core/management/commands/cleanup_recycle_bin.py`
- Tarea: `apps/core/tasks.cleanup_recycle_bin_task`
- Configuración: `patrimonio/settings.py` (CELERY_BEAT_SCHEDULE)
- Tests: `tests/test_recycle_bin_cleanup.py`
- Modelo: `apps/core/models.RecycleBin`
- Config: `apps/core/models.RecycleBinConfig`
