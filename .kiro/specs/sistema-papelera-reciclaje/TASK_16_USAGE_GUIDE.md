# Guía de Uso: Sistema de Notificaciones de Papelera

## 📖 Introducción

Esta guía explica cómo usar y configurar el sistema de notificaciones de advertencia para la papelera de reciclaje.

## 🚀 Configuración Inicial

### 1. Configurar Tipos de Notificación

Ejecutar el comando de setup para crear los tipos de notificación:

```bash
python manage.py setup_recycle_notifications
```

**Salida esperada:**
```
Configurando tipos de notificaciones de papelera...
✓ Tipo de notificación creado: Advertencia de Papelera
✓ Tipo de notificación creado: Advertencia Final de Papelera

============================================================
Configuración completada exitosamente
============================================================
```

### 2. Configurar Celery Beat

Agregar las tareas programadas en `patrimonio/celery.py`:

```python
from celery.schedules import crontab

app.conf.beat_schedule = {
    # Verificar alertas de papelera diariamente
    'verificar-alertas-papelera': {
        'task': 'apps.notificaciones.tasks.verificar_alertas_papelera',
        'schedule': crontab(hour=9, minute=0),  # 9:00 AM todos los días
    },
    
    # Procesar notificaciones pendientes cada 30 minutos
    'procesar-notificaciones-pendientes': {
        'task': 'apps.notificaciones.tasks.procesar_notificaciones_pendientes',
        'schedule': crontab(minute='*/30'),
    },
}
```

### 3. Iniciar Celery Workers

```bash
# Worker principal
celery -A patrimonio worker -l info

# Beat scheduler (en otra terminal)
celery -A patrimonio beat -l info
```

## 👤 Configuración de Preferencias de Usuario

### Desde Python/Django Shell

```python
from django.contrib.auth.models import User
from apps.notificaciones.utils import configurar_preferencias_papelera

# Obtener usuario
usuario = User.objects.get(username='juan.perez')

# Configurar preferencias
configurar_preferencias_papelera(
    usuario=usuario,
    recibir_advertencias=True,        # Advertencias de 7 días
    recibir_advertencias_finales=True # Advertencias finales de 1 día
)
```

### Deshabilitar Notificaciones

```python
# Deshabilitar todas las notificaciones de papelera
configurar_preferencias_papelera(
    usuario=usuario,
    recibir_advertencias=False,
    recibir_advertencias_finales=False
)
```

### Deshabilitar Solo Advertencias Finales

```python
# Solo recibir advertencias de 7 días, no las finales
configurar_preferencias_papelera(
    usuario=usuario,
    recibir_advertencias=True,
    recibir_advertencias_finales=False
)
```

### Consultar Preferencias Actuales

```python
from apps.notificaciones.utils import obtener_preferencias_papelera

preferencias = obtener_preferencias_papelera(usuario)
print(preferencias)
# {
#     'recibir_advertencias': True,
#     'recibir_advertencias_finales': True,
#     'enviar_email_advertencias': True,
#     'enviar_email_finales': True
# }
```

## 📧 Tipos de Notificaciones

### 1. Advertencia de 7 Días (RECYCLE_WARNING)

**Cuándo se envía:**
- 7 días antes de la eliminación automática
- Una vez por período de 7 días (no se duplica)

**Características:**
- Prioridad: ALTA
- Color: Amarillo (advertencia)
- Incluye: Tabla de elementos por módulo, días restantes

**Ejemplo de uso manual:**

```python
from apps.notificaciones.utils import notificar_advertencia_papelera

notificar_advertencia_papelera(
    usuario=usuario,
    items_count=5,
    dias_restantes=7,
    modulo='Oficinas'
)
```

### 2. Advertencia Final de 1 Día (RECYCLE_FINAL_WARNING)

**Cuándo se envía:**
- 24 horas antes de la eliminación automática
- Una vez por período de 1 día

**Características:**
- Prioridad: CRÍTICA
- Color: Rojo (alerta)
- Incluye: Lista urgente, ejemplos de elementos, horas restantes

**Ejemplo de uso manual:**

```python
notificar_advertencia_papelera(
    usuario=usuario,
    items_count=3,
    dias_restantes=1,
    modulo='Bienes Patrimoniales'
)
```

### 3. Notificación de Eliminación Automática

**Cuándo se envía:**
- Después de que elementos son eliminados automáticamente
- Enviada por el comando `cleanup_recycle_bin`

**Características:**
- Prioridad: MEDIA
- Tipo: SISTEMA
- Incluye: Resumen de elementos eliminados por módulo

## 🔧 Uso Programático

### Notificar Restauración Exitosa

```python
from apps.notificaciones.utils import notificar_restauracion_exitosa

notificar_restauracion_exitosa(
    usuario=request.user,
    objeto_repr='Oficina Central - Lima',
    modulo='Oficinas'
)
```

### Notificar Eliminación Permanente

```python
from apps.notificaciones.utils import notificar_eliminacion_permanente

notificar_eliminacion_permanente(
    usuario=request.user,
    objeto_repr='Bien Patrimonial #12345',
    modulo='Bienes Patrimoniales'
)
```

### Verificar Alertas Manualmente

```python
from apps.notificaciones.tasks import verificar_alertas_papelera

# Ejecutar verificación inmediata
resultado = verificar_alertas_papelera()
print(f"Alertas generadas: {resultado['alertas_generadas']}")
```

## 📊 Consultas Útiles

### Ver Notificaciones Pendientes de un Usuario

```python
from apps.notificaciones.models import Notificacion

notificaciones = Notificacion.objects.filter(
    usuario=usuario,
    tipo_notificacion__codigo__in=['RECYCLE_WARNING', 'RECYCLE_FINAL_WARNING'],
    estado='PENDIENTE'
)

for notif in notificaciones:
    print(f"{notif.titulo} - {notif.prioridad}")
```

### Ver Elementos Próximos a Eliminación

```python
from apps.core.models import RecycleBin
from django.utils import timezone
from datetime import timedelta

# Elementos a 7 días o menos
elementos_proximos = RecycleBin.objects.filter(
    restored_at__isnull=True,
    auto_delete_at__lte=timezone.now() + timedelta(days=7)
)

for item in elementos_proximos:
    print(f"{item.object_repr} - {item.days_until_auto_delete} días restantes")
```

### Estadísticas de Notificaciones

```python
from apps.notificaciones.models import Notificacion
from django.db.models import Count

# Notificaciones por tipo
stats = Notificacion.objects.filter(
    tipo_notificacion__codigo__in=['RECYCLE_WARNING', 'RECYCLE_FINAL_WARNING']
).values('tipo_notificacion__nombre', 'estado').annotate(
    total=Count('id')
)

for stat in stats:
    print(f"{stat['tipo_notificacion__nombre']} - {stat['estado']}: {stat['total']}")
```

## 🎯 Casos de Uso Comunes

### Caso 1: Usuario Elimina Oficina

```python
# 1. Usuario elimina oficina
oficina.soft_delete(user=request.user, reason='Oficina cerrada')

# 2. Se crea entrada en RecycleBin automáticamente
# 3. Después de 23 días, se envía advertencia de 7 días
# 4. Después de 29 días, se envía advertencia final de 1 día
# 5. Después de 30 días, se elimina automáticamente
```

### Caso 2: Usuario Quiere Deshabilitar Notificaciones

```python
from apps.notificaciones.utils import configurar_preferencias_papelera

# Deshabilitar todas las notificaciones de papelera
configurar_preferencias_papelera(
    usuario=request.user,
    recibir_advertencias=False,
    recibir_advertencias_finales=False
)
```

### Caso 3: Administrador Revisa Notificaciones Pendientes

```python
from apps.notificaciones.models import Notificacion

# Ver todas las notificaciones de papelera pendientes
notificaciones_pendientes = Notificacion.objects.filter(
    tipo_notificacion__codigo__in=['RECYCLE_WARNING', 'RECYCLE_FINAL_WARNING'],
    estado='PENDIENTE'
).select_related('usuario', 'tipo_notificacion')

for notif in notificaciones_pendientes:
    print(f"{notif.usuario.username}: {notif.titulo}")
    print(f"  Items: {notif.datos_contexto.get('total_items', 0)}")
    print(f"  Programada: {notif.fecha_programada}")
```

### Caso 4: Forzar Envío de Notificaciones

```python
from apps.notificaciones.tasks import procesar_notificaciones_pendientes

# Procesar todas las notificaciones pendientes inmediatamente
resultado = procesar_notificaciones_pendientes()
print(f"Notificaciones procesadas: {resultado['procesadas']}")
```

## 🔍 Debugging y Troubleshooting

### Verificar Configuración de Email

```python
from django.core.mail import send_mail

# Test de envío de email
send_mail(
    'Test Email',
    'Este es un email de prueba',
    'noreply@example.com',
    ['tu_email@example.com'],
    fail_silently=False,
)
```

### Ver Logs de Celery

```bash
# Ver logs en tiempo real
tail -f logs/celery.log

# Buscar errores de notificaciones
grep "ERROR" logs/celery.log | grep "notificacion"
```

### Verificar Tareas Programadas

```python
from celery import current_app

# Ver tareas programadas
schedule = current_app.conf.beat_schedule
for name, config in schedule.items():
    print(f"{name}: {config['task']} - {config['schedule']}")
```

### Ejecutar Tarea Manualmente

```python
from apps.notificaciones.tasks import verificar_alertas_papelera

# Ejecutar sincrónicamente (para debugging)
resultado = verificar_alertas_papelera()
print(resultado)

# Ejecutar asincrónicamente
task = verificar_alertas_papelera.delay()
print(f"Task ID: {task.id}")
print(f"Estado: {task.state}")
```

## 📝 Personalización de Templates

### Modificar Template de Advertencia

Editar `templates/notificaciones/email_recycle_warning.html`:

```html
<!-- Agregar logo personalizado -->
<div style="text-align: center; margin-bottom: 20px;">
    <img src="{{ base_url }}/static/img/logo.png" alt="Logo" style="max-width: 200px;">
</div>

<!-- Personalizar colores -->
<div style="background-color: #tu-color; ...">
    ...
</div>
```

### Modificar Template de Advertencia Final

Editar `templates/notificaciones/email_recycle_final_warning.html`:

```html
<!-- Agregar información adicional -->
<div style="margin-top: 20px;">
    <p>Para soporte, contacta a: soporte@example.com</p>
</div>
```

## 🎨 Personalización de Mensajes

### Cambiar Días de Advertencia

```python
from apps.core.models import RecycleBinConfig

# Cambiar a 10 días de advertencia
config = RecycleBinConfig.objects.get(module_name='oficinas')
config.warning_days_before = 10
config.final_warning_days_before = 2
config.save()
```

### Personalizar Mensaje de Notificación

```python
from apps.notificaciones.utils import crear_notificacion

# Crear notificación personalizada
crear_notificacion(
    usuario=usuario,
    tipo_codigo='RECYCLE_WARNING',
    titulo='🔔 Título Personalizado',
    mensaje='Mensaje personalizado con más detalles...',
    prioridad='ALTA',
    datos_contexto={
        'custom_field': 'valor personalizado'
    }
)
```

## 📈 Monitoreo y Métricas

### Dashboard de Notificaciones

```python
from apps.notificaciones.models import Notificacion
from django.db.models import Count, Q
from datetime import timedelta
from django.utils import timezone

# Últimos 30 días
fecha_inicio = timezone.now() - timedelta(days=30)

stats = {
    'total_enviadas': Notificacion.objects.filter(
        tipo_notificacion__codigo__in=['RECYCLE_WARNING', 'RECYCLE_FINAL_WARNING'],
        estado='ENVIADA',
        created_at__gte=fecha_inicio
    ).count(),
    
    'total_pendientes': Notificacion.objects.filter(
        tipo_notificacion__codigo__in=['RECYCLE_WARNING', 'RECYCLE_FINAL_WARNING'],
        estado='PENDIENTE'
    ).count(),
    
    'total_errores': Notificacion.objects.filter(
        tipo_notificacion__codigo__in=['RECYCLE_WARNING', 'RECYCLE_FINAL_WARNING'],
        estado='ERROR',
        created_at__gte=fecha_inicio
    ).count(),
}

print(f"Enviadas: {stats['total_enviadas']}")
print(f"Pendientes: {stats['total_pendientes']}")
print(f"Errores: {stats['total_errores']}")
```

## 🆘 Soporte

Para problemas o preguntas:

1. Revisar logs de Celery: `logs/celery.log`
2. Revisar logs de Django: `logs/django.log`
3. Verificar configuración de email en `.env`
4. Ejecutar tests: `pytest tests/test_recycle_bin_notifications.py -v`
5. Consultar documentación de Celery: https://docs.celeryproject.org/

## ✅ Checklist de Verificación

- [ ] Comando `setup_recycle_notifications` ejecutado
- [ ] Celery worker corriendo
- [ ] Celery beat corriendo
- [ ] Configuración de email correcta
- [ ] Templates de email existen
- [ ] Tests pasan exitosamente
- [ ] Logs no muestran errores
- [ ] Notificaciones se envían correctamente
- [ ] Preferencias de usuario funcionan
- [ ] Emails llegan a destinatarios
