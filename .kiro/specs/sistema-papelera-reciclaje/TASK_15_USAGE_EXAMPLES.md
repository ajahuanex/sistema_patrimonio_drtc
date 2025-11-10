# Task 15: Ejemplos de Uso - Eliminación Automática

## 📚 Ejemplos Prácticos

### Ejemplo 1: Configuración Inicial del Sistema

```python
from apps.core.models import RecycleBinConfig

# Configurar oficinas: 30 días de retención
RecycleBinConfig.objects.create(
    module_name='oficinas',
    retention_days=30,
    auto_delete_enabled=True,
    warning_days_before=7,
    final_warning_days_before=1
)

# Configurar catálogo: 15 días de retención
RecycleBinConfig.objects.create(
    module_name='catalogo',
    retention_days=15,
    auto_delete_enabled=True,
    warning_days_before=5,
    final_warning_days_before=1
)

# Configurar bienes: 60 días, auto-delete deshabilitado
RecycleBinConfig.objects.create(
    module_name='bienes',
    retention_days=60,
    auto_delete_enabled=False,  # Requiere aprobación manual
    warning_days_before=10,
    final_warning_days_before=2
)
```

### Ejemplo 2: Limpieza Manual Básica

```bash
# Ver qué se eliminaría sin eliminar realmente
python manage.py cleanup_recycle_bin --dry-run

# Salida esperada:
# === Iniciando limpieza de papelera de reciclaje ===
# MODO DRY-RUN: No se eliminarán elementos realmente
# Elementos encontrados para eliminación: 5
#
# oficinas: 2 elementos
#   Días de retención: 30
#   - Oficina Central (ID: 123, 35 días en papelera)
#   - Oficina Regional (ID: 124, 32 días en papelera)
#
# catalogo: 3 elementos
#   Días de retención: 15
#   - Mobiliario (ID: 45, 18 días en papelera)
#   - Equipos (ID: 46, 16 días en papelera)
#   - Vehículos (ID: 47, 20 días en papelera)
#
# DRY-RUN: Se eliminarían 5 elementos en total

# Ejecutar limpieza real
python manage.py cleanup_recycle_bin

# Salida esperada:
# === Iniciando limpieza de papelera de reciclaje ===
# Elementos encontrados para eliminación: 5
#
# oficinas: 2 elementos
#   ✓ Eliminados: 2 elementos
#
# catalogo: 3 elementos
#   ✓ Eliminados: 3 elementos
#
# === Limpieza completada: 5 elementos eliminados ===
```

### Ejemplo 3: Limpieza por Módulo Específico

```bash
# Limpiar solo oficinas
python manage.py cleanup_recycle_bin --module oficinas

# Limpiar solo catálogo
python manage.py cleanup_recycle_bin --module catalogo

# Limpiar bienes (forzando, ya que auto_delete_enabled=False)
python manage.py cleanup_recycle_bin --module bienes --force
```

### Ejemplo 4: Sobrescribir Días de Retención

```bash
# Eliminar elementos con más de 10 días en papelera
python manage.py cleanup_recycle_bin --days 10

# Eliminar elementos con más de 60 días
python manage.py cleanup_recycle_bin --days 60

# Combinar con módulo específico
python manage.py cleanup_recycle_bin --module oficinas --days 20
```

### Ejemplo 5: Ejecución Programática de la Tarea

```python
from apps.core.tasks import cleanup_recycle_bin_task

# Ejecutar tarea manualmente
resultado = cleanup_recycle_bin_task()

# Procesar resultado
print(f"Estado: {resultado['status']}")
print(f"Elementos eliminados: {resultado['eliminados']}")
print(f"Total encontrados: {resultado['total_encontrados']}")

# Ver detalles por módulo
for module_name, stats in resultado['modulos'].items():
    print(f"\n{module_name}:")
    print(f"  Eliminados: {stats['eliminados']}")
    print(f"  Omitidos: {stats['omitidos']}")
    print(f"  Razón: {stats['razon']}")

# Ver errores si los hay
if resultado['errores']:
    print("\nErrores:")
    for error in resultado['errores']:
        print(f"  - {error['object_repr']}: {error['error']}")
```

### Ejemplo 6: Monitoreo de Elementos Próximos a Eliminarse

```python
from apps.core.models import RecycleBin
from django.utils import timezone

# Obtener elementos que se eliminarán en los próximos 7 días
elementos_proximos = RecycleBin.objects.filter(
    restored_at__isnull=True
)

print("Elementos próximos a eliminación automática:\n")

for item in elementos_proximos:
    if item.is_near_auto_delete:
        dias = item.days_until_auto_delete
        print(f"⚠️  {item.object_repr}")
        print(f"   Módulo: {item.get_module_display()}")
        print(f"   Días restantes: {dias}")
        print(f"   Eliminado por: {item.deleted_by.username}")
        print(f"   Fecha de eliminación: {item.auto_delete_at.strftime('%Y-%m-%d %H:%M')}")
        print()
```

### Ejemplo 7: Verificar Configuración Antes de Limpieza

```python
from apps.core.models import RecycleBin, RecycleBinConfig
from django.utils import timezone

# Obtener estadísticas por módulo
modulos = RecycleBin.objects.filter(
    restored_at__isnull=True
).values('module_name').distinct()

print("Estado de la papelera por módulo:\n")

for modulo_data in modulos:
    module_name = modulo_data['module_name']
    
    # Obtener configuración
    try:
        config = RecycleBinConfig.objects.get(module_name=module_name)
        auto_delete = "✅ Habilitado" if config.auto_delete_enabled else "❌ Deshabilitado"
        retention = config.retention_days
    except RecycleBinConfig.DoesNotExist:
        auto_delete = "⚠️  Sin configuración"
        retention = 30
    
    # Contar elementos
    total = RecycleBin.objects.filter(
        module_name=module_name,
        restored_at__isnull=True
    ).count()
    
    ready = RecycleBin.objects.filter(
        module_name=module_name,
        restored_at__isnull=True,
        auto_delete_at__lte=timezone.now()
    ).count()
    
    print(f"{module_name}:")
    print(f"  Total en papelera: {total}")
    print(f"  Listos para eliminar: {ready}")
    print(f"  Días de retención: {retention}")
    print(f"  Auto-delete: {auto_delete}")
    print()
```

### Ejemplo 8: Auditoría de Eliminaciones Automáticas

```python
from apps.core.models import AuditLog
from datetime import timedelta
from django.utils import timezone

# Obtener eliminaciones automáticas de los últimos 30 días
fecha_inicio = timezone.now() - timedelta(days=30)

eliminaciones = AuditLog.objects.filter(
    action='delete',
    changes__tipo='eliminacion_automatica',
    timestamp__gte=fecha_inicio
).order_by('-timestamp')

print(f"Eliminaciones automáticas (últimos 30 días): {eliminaciones.count()}\n")

# Agrupar por módulo
from collections import defaultdict
por_modulo = defaultdict(int)

for log in eliminaciones:
    module_name = log.changes.get('module_name', 'desconocido')
    por_modulo[module_name] += 1

print("Por módulo:")
for module, count in por_modulo.items():
    print(f"  {module}: {count} eliminaciones")

# Mostrar últimas 10 eliminaciones
print("\nÚltimas 10 eliminaciones:")
for log in eliminaciones[:10]:
    print(f"  {log.timestamp.strftime('%Y-%m-%d %H:%M')} - {log.object_repr}")
    print(f"    Módulo: {log.changes.get('module_name')}")
    print(f"    Días en papelera: {log.changes.get('dias_en_papelera')}")
    print(f"    Eliminado originalmente por: {log.changes.get('deleted_by')}")
    print()
```

### Ejemplo 9: Cambiar Configuración Dinámicamente

```python
from apps.core.models import RecycleBinConfig

# Aumentar días de retención temporalmente
config = RecycleBinConfig.objects.get(module_name='oficinas')
config_anterior = config.retention_days

config.retention_days = 60  # Aumentar a 60 días
config.save()

print(f"Días de retención cambiados de {config_anterior} a {config.retention_days}")

# Deshabilitar auto-delete temporalmente
config.auto_delete_enabled = False
config.save()

print("Auto-delete deshabilitado temporalmente")

# Restaurar configuración después
config.retention_days = config_anterior
config.auto_delete_enabled = True
config.save()

print("Configuración restaurada")
```

### Ejemplo 10: Script de Mantenimiento Completo

```python
#!/usr/bin/env python
"""
Script de mantenimiento para papelera de reciclaje
Ejecutar semanalmente para verificar estado
"""

from apps.core.models import RecycleBin, RecycleBinConfig, AuditLog
from django.utils import timezone
from datetime import timedelta

def reporte_semanal():
    """Genera reporte semanal del estado de la papelera"""
    
    print("=" * 60)
    print("REPORTE SEMANAL - PAPELERA DE RECICLAJE")
    print("=" * 60)
    print(f"Fecha: {timezone.now().strftime('%Y-%m-%d %H:%M')}\n")
    
    # 1. Elementos en papelera
    total_papelera = RecycleBin.objects.filter(restored_at__isnull=True).count()
    print(f"📊 Total elementos en papelera: {total_papelera}\n")
    
    # 2. Por módulo
    print("Por módulo:")
    for module in ['oficinas', 'bienes', 'catalogo']:
        count = RecycleBin.objects.filter(
            module_name=module,
            restored_at__isnull=True
        ).count()
        print(f"  {module}: {count}")
    print()
    
    # 3. Elementos próximos a eliminarse
    proximos = []
    for item in RecycleBin.objects.filter(restored_at__isnull=True):
        if item.is_near_auto_delete:
            proximos.append(item)
    
    print(f"⚠️  Elementos próximos a eliminación (≤7 días): {len(proximos)}")
    for item in proximos[:5]:  # Mostrar primeros 5
        print(f"  - {item.object_repr} ({item.days_until_auto_delete} días)")
    if len(proximos) > 5:
        print(f"  ... y {len(proximos) - 5} más")
    print()
    
    # 4. Eliminaciones de la última semana
    fecha_inicio = timezone.now() - timedelta(days=7)
    eliminaciones = AuditLog.objects.filter(
        action='delete',
        changes__tipo='eliminacion_automatica',
        timestamp__gte=fecha_inicio
    ).count()
    
    print(f"🗑️  Eliminaciones automáticas (última semana): {eliminaciones}\n")
    
    # 5. Restauraciones de la última semana
    restauraciones = RecycleBin.objects.filter(
        restored_at__gte=fecha_inicio
    ).count()
    
    print(f"♻️  Restauraciones (última semana): {restauraciones}\n")
    
    # 6. Configuración actual
    print("⚙️  Configuración actual:")
    for module in ['oficinas', 'bienes', 'catalogo']:
        try:
            config = RecycleBinConfig.objects.get(module_name=module)
            status = "✅" if config.auto_delete_enabled else "❌"
            print(f"  {module}: {config.retention_days} días, auto-delete {status}")
        except RecycleBinConfig.DoesNotExist:
            print(f"  {module}: ⚠️  Sin configuración")
    print()
    
    # 7. Recomendaciones
    print("💡 Recomendaciones:")
    if len(proximos) > 10:
        print("  - Revisar elementos próximos a eliminarse")
    if total_papelera > 100:
        print("  - Considerar reducir días de retención")
    if eliminaciones == 0:
        print("  - Verificar que Celery Beat esté funcionando")
    print()
    
    print("=" * 60)

# Ejecutar reporte
if __name__ == '__main__':
    reporte_semanal()
```

### Ejemplo 11: Integración con Cron (Linux)

```bash
# Agregar a crontab para ejecutar limpieza manual diaria a las 3 AM
# (además de la tarea de Celery)

# Editar crontab
crontab -e

# Agregar línea:
0 3 * * * cd /path/to/proyecto && /path/to/venv/bin/python manage.py cleanup_recycle_bin >> /var/log/recycle_bin_cleanup.log 2>&1

# Verificar crontab
crontab -l
```

### Ejemplo 12: Integración con Task Scheduler (Windows)

```powershell
# Crear tarea programada en Windows

# Script PowerShell: cleanup_recycle_bin.ps1
$projectPath = "D:\proyecto\sistema_patrimonio"
$pythonPath = "D:\proyecto\venv\Scripts\python.exe"
$logPath = "D:\proyecto\logs\cleanup.log"

cd $projectPath
& $pythonPath manage.py cleanup_recycle_bin >> $logPath 2>&1

# Crear tarea programada
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-File D:\proyecto\scripts\cleanup_recycle_bin.ps1"
$trigger = New-ScheduledTaskTrigger -Daily -At 3am
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable

Register-ScheduledTask -TaskName "RecycleBinCleanup" -Action $action -Trigger $trigger -Principal $principal -Settings $settings
```

## 🎯 Casos de Uso Reales

### Caso 1: Organización con Política Estricta

```python
# Configuración: Eliminar rápidamente, sin excepciones
RecycleBinConfig.objects.update_or_create(
    module_name='oficinas',
    defaults={
        'retention_days': 7,  # Solo 7 días
        'auto_delete_enabled': True,
        'warning_days_before': 3,
        'final_warning_days_before': 1
    }
)
```

### Caso 2: Organización con Política Flexible

```python
# Configuración: Retención larga, eliminación manual
RecycleBinConfig.objects.update_or_create(
    module_name='bienes',
    defaults={
        'retention_days': 90,  # 90 días
        'auto_delete_enabled': False,  # Manual
        'warning_days_before': 30,
        'final_warning_days_before': 7
    }
)
```

### Caso 3: Limpieza de Emergencia

```bash
# Eliminar todo lo que tenga más de 5 días
python manage.py cleanup_recycle_bin --days 5 --force

# Limpiar módulo específico inmediatamente
python manage.py cleanup_recycle_bin --module catalogo --days 0 --force
```

## 📊 Monitoreo y Alertas

### Script de Monitoreo

```python
from apps.core.models import RecycleBin
from django.core.mail import send_mail
from django.utils import timezone

def verificar_y_alertar():
    """Verifica estado y envía alertas si es necesario"""
    
    # Contar elementos próximos a eliminarse
    proximos = []
    for item in RecycleBin.objects.filter(restored_at__isnull=True):
        if item.is_near_auto_delete:
            proximos.append(item)
    
    # Enviar alerta si hay muchos elementos
    if len(proximos) > 20:
        send_mail(
            'Alerta: Muchos elementos próximos a eliminación',
            f'Hay {len(proximos)} elementos que se eliminarán en los próximos 7 días.',
            'sistema@empresa.com',
            ['admin@empresa.com'],
            fail_silently=False,
        )
    
    return len(proximos)
```

## 🔧 Troubleshooting

### Problema: Celery no ejecuta la tarea

```bash
# Verificar que Celery Beat está corriendo
celery -A patrimonio inspect scheduled

# Verificar logs de Celery
tail -f logs/celery.log

# Ejecutar manualmente para verificar
python manage.py cleanup_recycle_bin --dry-run
```

### Problema: Elementos no se eliminan

```python
# Verificar configuración
from apps.core.models import RecycleBinConfig

config = RecycleBinConfig.objects.get(module_name='oficinas')
print(f"Auto-delete habilitado: {config.auto_delete_enabled}")
print(f"Días de retención: {config.retention_days}")

# Verificar elementos listos
from apps.core.models import RecycleBin
from django.utils import timezone

ready = RecycleBin.objects.filter(
    module_name='oficinas',
    restored_at__isnull=True,
    auto_delete_at__lte=timezone.now()
)
print(f"Elementos listos: {ready.count()}")
```

Estos ejemplos cubren los casos de uso más comunes y proporcionan una guía práctica para utilizar el sistema de eliminación automática.
