# Task 15: Eliminación Automática - Guía Rápida

## 🚀 Uso Rápido

### Comando de Management

```bash
# Limpieza normal
python manage.py cleanup_recycle_bin

# Ver qué se eliminaría (sin eliminar)
python manage.py cleanup_recycle_bin --dry-run

# Limpiar solo oficinas
python manage.py cleanup_recycle_bin --module oficinas

# Forzar eliminación (ignora auto_delete_enabled)
python manage.py cleanup_recycle_bin --force

# Usar 15 días de retención en lugar de la configuración
python manage.py cleanup_recycle_bin --days 15
```

### Tarea de Celery

```python
# Ejecutar manualmente
from apps.core.tasks import cleanup_recycle_bin_task
resultado = cleanup_recycle_bin_task()

# Programada automáticamente
# Se ejecuta diariamente a las 4:00 AM
```

## ⚙️ Configuración

### Por Módulo (RecycleBinConfig)

```python
from apps.core.models import RecycleBinConfig

# Crear configuración
config = RecycleBinConfig.objects.create(
    module_name='oficinas',
    retention_days=30,              # Días en papelera
    auto_delete_enabled=True,       # Habilitar auto-delete
    warning_days_before=7,          # Advertencia 7 días antes
    final_warning_days_before=1     # Advertencia final 1 día antes
)

# Obtener configuración
config = RecycleBinConfig.get_config_for_module('oficinas')
```

### Variables de Entorno

```bash
# .env
RECYCLE_BIN_RETENTION_DAYS=30
RECYCLE_BIN_AUTO_CLEANUP_ENABLED=True
```

## 📊 Verificar Estado

### Elementos Listos para Eliminación

```python
from apps.core.models import RecycleBin
from django.utils import timezone

# Elementos listos para auto-delete
ready = RecycleBin.objects.filter(
    restored_at__isnull=True,
    auto_delete_at__lte=timezone.now()
)

print(f"Elementos listos: {ready.count()}")
```

### Elementos Próximos a Eliminarse

```python
# Elementos con ≤7 días restantes
near_delete = RecycleBin.objects.filter(
    restored_at__isnull=True
)

for item in near_delete:
    if item.is_near_auto_delete:
        print(f"{item.object_repr}: {item.days_until_auto_delete} días restantes")
```

## 🔍 Auditoría

### Ver Eliminaciones Automáticas

```python
from apps.core.models import AuditLog

# Últimas eliminaciones automáticas
logs = AuditLog.objects.filter(
    action='delete',
    changes__tipo='eliminacion_automatica'
).order_by('-timestamp')[:10]

for log in logs:
    print(f"{log.timestamp}: {log.object_repr} - {log.changes['module_name']}")
```

## 🛠️ Troubleshooting

### Verificar Configuración de Celery

```bash
# Ver tareas programadas
celery -A patrimonio inspect scheduled

# Ver workers activos
celery -A patrimonio inspect active
```

### Ejecutar Manualmente

```bash
# Si Celery no está funcionando
python manage.py cleanup_recycle_bin
```

### Verificar Logs

```python
import logging
logger = logging.getLogger('patrimonio')

# Los logs se guardan en logs/django.log
```

## 📋 Checklist de Despliegue

- [ ] Migraciones ejecutadas
- [ ] RecycleBinConfig creado para cada módulo
- [ ] Variables de entorno configuradas
- [ ] Celery worker iniciado
- [ ] Celery beat iniciado
- [ ] Dry-run ejecutado exitosamente
- [ ] Logs monitoreados

## 🎯 Casos de Uso Comunes

### Cambiar Días de Retención

```python
config = RecycleBinConfig.objects.get(module_name='oficinas')
config.retention_days = 45
config.save()
```

### Deshabilitar Auto-Delete Temporalmente

```python
config = RecycleBinConfig.objects.get(module_name='bienes')
config.auto_delete_enabled = False
config.save()
```

### Limpiar Módulo Específico Manualmente

```bash
python manage.py cleanup_recycle_bin --module catalogo --force
```

### Ver Estadísticas

```python
from apps.core.models import RecycleBin

# Por módulo
for module in ['oficinas', 'bienes', 'catalogo']:
    count = RecycleBin.objects.filter(
        module_name=module,
        restored_at__isnull=True
    ).count()
    print(f"{module}: {count} elementos")
```

## ⚠️ Advertencias

1. **Eliminación Permanente**: Los elementos eliminados automáticamente NO pueden recuperarse
2. **Configuración por Módulo**: Cada módulo puede tener diferentes políticas
3. **Auditoría**: Todas las eliminaciones se registran en AuditLog
4. **Celery Requerido**: La ejecución automática requiere Celery funcionando
5. **Backup**: Considerar backup antes de eliminaciones masivas

## 📞 Soporte

- Logs: `logs/django.log`
- Auditoría: Modelo `AuditLog`
- Configuración: Modelo `RecycleBinConfig`
- Comando: `python manage.py cleanup_recycle_bin --help`
