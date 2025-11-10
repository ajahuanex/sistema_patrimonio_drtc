# Task 16: Quick Reference - Sistema de Notificaciones

## 🚀 Setup Rápido

```bash
# 1. Configurar tipos de notificación
python manage.py setup_recycle_notifications

# 2. Iniciar Celery
celery -A patrimonio worker -l info
celery -A patrimonio beat -l info
```

## 📧 Tipos de Notificación

| Código | Nombre | Cuándo | Prioridad | Color |
|--------|--------|--------|-----------|-------|
| `RECYCLE_WARNING` | Advertencia de Papelera | 7 días antes | ALTA | 🟡 Amarillo |
| `RECYCLE_FINAL_WARNING` | Advertencia Final | 1 día antes | CRÍTICA | 🔴 Rojo |

## 💻 Uso Rápido

### Configurar Preferencias

```python
from apps.notificaciones.utils import configurar_preferencias_papelera

configurar_preferencias_papelera(
    usuario=user,
    recibir_advertencias=True,
    recibir_advertencias_finales=True
)
```

### Notificar Manualmente

```python
from apps.notificaciones.utils import notificar_advertencia_papelera

notificar_advertencia_papelera(
    usuario=user,
    items_count=5,
    dias_restantes=7,
    modulo='Oficinas'
)
```

### Verificar Alertas

```python
from apps.notificaciones.tasks import verificar_alertas_papelera

resultado = verificar_alertas_papelera()
print(f"Alertas: {resultado['alertas_generadas']}")
```

## 📁 Archivos Clave

```
apps/notificaciones/
├── models.py                    # Tipos de notificación actualizados
├── tasks.py                     # Tareas de verificación y envío
├── utils.py                     # Funciones utilitarias
└── management/commands/
    └── setup_recycle_notifications.py

templates/notificaciones/
├── email_recycle_warning.html        # Template advertencia 7 días
├── email_recycle_final_warning.html  # Template advertencia 1 día
└── email_base.txt                    # Template texto plano

tests/
└── test_recycle_bin_notifications.py # 22 tests
```

## ⚙️ Configuración Celery Beat

```python
CELERY_BEAT_SCHEDULE = {
    'verificar-alertas-papelera': {
        'task': 'apps.notificaciones.tasks.verificar_alertas_papelera',
        'schedule': crontab(hour=9, minute=0),  # 9:00 AM diario
    },
}
```

## 🔍 Consultas Útiles

```python
# Notificaciones pendientes
Notificacion.objects.filter(
    tipo_notificacion__codigo='RECYCLE_WARNING',
    estado='PENDIENTE'
).count()

# Elementos próximos a eliminación
RecycleBin.objects.filter(
    restored_at__isnull=True,
    auto_delete_at__lte=timezone.now() + timedelta(days=7)
).count()

# Preferencias de usuario
obtener_preferencias_papelera(user)
```

## 🧪 Tests

```bash
# Ejecutar todos los tests
python manage.py test tests.test_recycle_bin_notifications

# Test específico
python manage.py test tests.test_recycle_bin_notifications.TestNotificacionesPapelera.test_notificar_advertencia_papelera_7_dias
```

## 📊 Datos de Contexto

### Advertencia de 7 días
```python
{
    'items_by_module': [
        {
            'module_display': 'Oficinas',
            'count': 5,
            'days_remaining': 7
        }
    ],
    'total_items': 5,
    'retention_days': 30,
    'module_name': 'oficinas'
}
```

### Advertencia Final de 1 día
```python
{
    'items_by_module': [...],
    'total_items': 3,
    'hours_until_deletion': 23,
    'sample_items': [
        {
            'module_display': 'Oficinas',
            'object_repr': 'Oficina Central',
            'deleted_at': datetime(...)
        }
    ]
}
```

## 🎯 Flujo Completo

```
Usuario elimina elemento
    ↓
Soft delete + RecycleBin entry
    ↓
Día 23: Advertencia de 7 días (ALTA)
    ↓
Día 29: Advertencia final de 1 día (CRÍTICA)
    ↓
Día 30: Eliminación automática + Notificación
```

## 🔧 Troubleshooting

```python
# Verificar configuración
from apps.notificaciones.models import TipoNotificacion
TipoNotificacion.objects.filter(
    codigo__in=['RECYCLE_WARNING', 'RECYCLE_FINAL_WARNING']
)

# Forzar envío
from apps.notificaciones.tasks import procesar_notificaciones_pendientes
procesar_notificaciones_pendientes()

# Ver logs
tail -f logs/celery.log | grep "papelera"
```

## 📝 Variables de Entorno

```env
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@example.com
EMAIL_HOST_PASSWORD=password
DEFAULT_FROM_EMAIL=noreply@example.com
BASE_URL=https://patrimonio.example.com
```

## ✅ Checklist

- [ ] `setup_recycle_notifications` ejecutado
- [ ] Celery worker corriendo
- [ ] Celery beat corriendo
- [ ] Email configurado
- [ ] Templates existen
- [ ] Tests pasan
- [ ] Notificaciones funcionan
