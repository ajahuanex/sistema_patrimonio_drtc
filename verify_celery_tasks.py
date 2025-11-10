"""
Script de verificación para las tareas de Celery configuradas
"""
import os
import sys

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'patrimonio.settings')

import django
django.setup()

from patrimonio.celery import app
from celery.schedules import crontab


def verify_celery_configuration():
    """Verifica que la configuración de Celery esté completa"""
    
    print("=" * 80)
    print("VERIFICACIÓN DE CONFIGURACIÓN DE CELERY PARA PAPELERA DE RECICLAJE")
    print("=" * 80)
    print()
    
    # Verificar que las tareas se pueden importar
    print("1. Verificando que las tareas se pueden importar...")
    print("-" * 80)
    
    all_imports_ok = True
    try:
        from apps.core.tasks import (
            cleanup_recycle_bin_task,
            send_recycle_bin_warnings,
            send_recycle_bin_final_warnings
        )
        print("   ✓ cleanup_recycle_bin_task")
        print("   ✓ send_recycle_bin_warnings")
        print("   ✓ send_recycle_bin_final_warnings")
        
        # Verificar que son tareas de Celery
        print("\n   Verificando decoradores @shared_task:")
        print(f"      - cleanup_recycle_bin_task: {hasattr(cleanup_recycle_bin_task, 'delay')}")
        print(f"      - send_recycle_bin_warnings: {hasattr(send_recycle_bin_warnings, 'delay')}")
        print(f"      - send_recycle_bin_final_warnings: {hasattr(send_recycle_bin_final_warnings, 'delay')}")
        
    except ImportError as e:
        print(f"   ✗ Error importando tareas: {e}")
        all_imports_ok = False
    
    print()
    
    # Verificar configuración de Beat Schedule directamente desde el archivo
    print("2. Verificando configuración de Celery Beat Schedule...")
    print("-" * 80)
    
    # Leer directamente desde patrimonio.celery
    from patrimonio import celery as celery_module
    celery_app = celery_module.app
    
    beat_schedule = celery_app.conf.beat_schedule
    
    required_schedules = {
        'cleanup-recycle-bin': {
            'task': 'apps.core.tasks.cleanup_recycle_bin_task',
        },
        'send-recycle-bin-warnings': {
            'task': 'apps.core.tasks.send_recycle_bin_warnings',
        },
        'send-recycle-bin-final-warnings': {
            'task': 'apps.core.tasks.send_recycle_bin_final_warnings',
        },
    }
    
    all_schedules_ok = True
    for schedule_name, expected_config in required_schedules.items():
        if schedule_name in beat_schedule:
            schedule_config = beat_schedule[schedule_name]
            print(f"\n   ✓ {schedule_name}")
            print(f"      - Tarea: {schedule_config['task']}")
            print(f"      - Schedule: {schedule_config['schedule']}")
            
            # Verificar que la tarea coincida
            if schedule_config['task'] != expected_config['task']:
                print(f"      ⚠ ADVERTENCIA: Tarea esperada {expected_config['task']}")
                all_schedules_ok = False
        else:
            print(f"   ✗ {schedule_name} - NO ENCONTRADO")
            all_schedules_ok = False
    
    print()
    
    # Verificar rutas de tareas
    print("3. Verificando rutas de tareas (task routes)...")
    print("-" * 80)
    
    task_routes = celery_app.conf.task_routes
    
    required_tasks = [
        'apps.core.tasks.cleanup_recycle_bin_task',
        'apps.core.tasks.send_recycle_bin_warnings',
        'apps.core.tasks.send_recycle_bin_final_warnings',
    ]
    
    all_routes_ok = True
    for task_name in required_tasks:
        if task_name in task_routes:
            route = task_routes[task_name]
            print(f"   ✓ {task_name}")
            print(f"      - Cola: {route['queue']}")
        else:
            print(f"   ✗ {task_name} - NO TIENE RUTA CONFIGURADA")
            all_routes_ok = False
    
    print()
    
    # Resumen
    print("=" * 80)
    print("RESUMEN DE VERIFICACIÓN")
    print("=" * 80)
    
    if all_schedules_ok and all_routes_ok and all_imports_ok:
        print("✓ TODAS LAS VERIFICACIONES PASARON")
        print()
        print("Las tareas de Celery para la papelera de reciclaje están correctamente configuradas:")
        print()
        print("  1. cleanup_recycle_bin_task - Se ejecuta diariamente a las 2:00 AM")
        print("     Elimina permanentemente elementos que han excedido su tiempo de retención")
        print()
        print("  2. send_recycle_bin_warnings - Se ejecuta diariamente a las 9:00 AM")
        print("     Envía notificaciones de advertencia 7 días antes de la eliminación automática")
        print()
        print("  3. send_recycle_bin_final_warnings - Se ejecuta cada 6 horas")
        print("     Envía notificaciones finales 1 día antes de la eliminación automática")
        print()
        print("Para iniciar Celery Beat, ejecuta:")
        print("  celery -A patrimonio beat --loglevel=info")
        print()
        print("Para iniciar Celery Worker, ejecuta:")
        print("  celery -A patrimonio worker --loglevel=info")
        print()
        return True
    else:
        print("✗ ALGUNAS VERIFICACIONES FALLARON")
        print()
        if not all_schedules_ok:
            print("  - La configuración de Beat Schedule tiene problemas")
        if not all_routes_ok:
            print("  - Las rutas de tareas no están completas")
        if not all_imports_ok:
            print("  - No se pueden importar todas las tareas")
        print()
        return False


if __name__ == '__main__':
    success = verify_celery_configuration()
    sys.exit(0 if success else 1)
