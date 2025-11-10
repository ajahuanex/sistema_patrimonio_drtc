# Task 26: Configuración de Celery - Guía Rápida

## 🚀 Inicio Rápido

### Iniciar Celery Worker
```bash
celery -A patrimonio worker --loglevel=info
```

### Iniciar Celery Beat
```bash
celery -A patrimonio beat --loglevel=info
```

### Iniciar ambos (desarrollo)
```bash
celery -A patrimonio worker --beat --loglevel=info
```

### Verificar configuración
```bash
python verify_celery_tasks.py
```

## 📋 Tareas Configuradas

| Tarea | Horario | Cola | Propósito |
|-------|---------|------|-----------|
| `cleanup_recycle_bin_task` | 4:00 AM diario | maintenance | Elimina elementos expirados |
| `send_recycle_bin_warnings` | 9:00 AM diario | notifications | Advertencia 7 días antes |
| `send_recycle_bin_final_warnings` | Cada 6 horas | notifications | Advertencia 1 día antes |

## 📁 Archivos Clave

```
apps/core/tasks.py                    # Implementación de tareas
patrimonio/settings.py                # Configuración Beat Schedule
tests/test_celery_periodic_tasks.py   # Tests
verify_celery_tasks.py                # Script de verificación
```

## 🔧 Configuración

### Beat Schedule (settings.py)
```python
CELERY_BEAT_SCHEDULE = {
    'cleanup-recycle-bin': {
        'task': 'apps.core.tasks.cleanup_recycle_bin_task',
        'schedule': crontab(hour=4, minute=0),
    },
    'send-recycle-bin-warnings': {
        'task': 'apps.core.tasks.send_recycle_bin_warnings',
        'schedule': crontab(hour=9, minute=0),
    },
    'send-recycle-bin-final-warnings': {
        'task': 'apps.core.tasks.send_recycle_bin_final_warnings',
        'schedule': crontab(minute=0, hour='*/6'),
    },
}
```

### Task Routes (settings.py)
```python
CELERY_TASK_ROUTES = {
    'apps.core.tasks.cleanup_recycle_bin_task': {'queue': 'maintenance'},
    'apps.core.tasks.send_recycle_bin_warnings': {'queue': 'notifications'},
    'apps.core.tasks.send_recycle_bin_final_warnings': {'queue': 'notifications'},
}
```

## 🧪 Ejecutar Tests

```bash
# Todos los tests de Celery
python -m pytest tests/test_celery_periodic_tasks.py -v

# Test específico
python -m pytest tests/test_celery_periodic_tasks.py::TestCleanupRecycleBinTask -v
```

## 🔍 Monitoreo

### Ver logs de Celery
```bash
# Worker logs
tail -f celery_worker.log

# Beat logs
tail -f celery_beat.log
```

### Verificar tareas en ejecución
```bash
celery -A patrimonio inspect active
```

### Ver tareas programadas
```bash
celery -A patrimonio inspect scheduled
```

## 🐛 Troubleshooting

### Problema: Tareas no se ejecutan
```bash
# Verificar que Beat está corriendo
ps aux | grep celery

# Verificar configuración
python verify_celery_tasks.py

# Revisar logs
tail -f celery_beat.log
```

### Problema: Errores en tareas
```bash
# Ver detalles del error
celery -A patrimonio inspect stats

# Reiniciar worker
celery -A patrimonio control shutdown
celery -A patrimonio worker --loglevel=info
```

## 📊 Flujo de Ejecución

```
Usuario elimina registro
    ↓
RecycleBin creado (auto_delete_at = +30 días)
    ↓
Día 23: Advertencia 7 días (9:00 AM)
    ↓
Día 29: Advertencia final (cada 6h)
    ↓
Día 30: Eliminación automática (4:00 AM)
```

## ⚙️ Variables de Entorno

```bash
# Redis (Broker y Backend)
REDIS_URL=redis://localhost:6379/0

# Timezone
TIME_ZONE=America/La_Paz
```

## 🎯 Comandos Útiles

```bash
# Ejecutar tarea manualmente
python manage.py shell
>>> from apps.core.tasks import cleanup_recycle_bin_task
>>> cleanup_recycle_bin_task.delay()

# Ver resultado de tarea
>>> result = cleanup_recycle_bin_task.delay()
>>> result.get()

# Purgar todas las tareas
celery -A patrimonio purge

# Reiniciar workers
celery -A patrimonio control shutdown
```

## 📝 Notas Importantes

1. **Horarios**: Configurados para zona horaria del sistema
2. **Colas**: Separadas para mejor rendimiento
3. **Errores**: Se registran pero no detienen el proceso
4. **Notificaciones**: Respetan preferencias de usuario
5. **Configuración**: Centralizada en settings.py

## ✅ Checklist de Verificación

- [ ] Celery Worker corriendo
- [ ] Celery Beat corriendo
- [ ] Redis accesible
- [ ] Tareas en CELERY_BEAT_SCHEDULE
- [ ] Task routes configuradas
- [ ] Tests pasando
- [ ] Logs sin errores

---

**Última actualización**: 2025-11-10
