#!/usr/bin/env python
"""
Script para ejecutar pruebas finales de integración del sistema de papelera de reciclaje.
Este script ejecuta todos los tests de integración, seguridad, carga y regresión.
"""

import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner

# Configurar el entorno para usar SQLite en lugar de PostgreSQL
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'patrimonio.settings')
os.environ['DATABASE_URL'] = 'sqlite:///test_db.sqlite3'
os.environ['DEBUG'] = 'True'

# Inicializar Django
django.setup()

def run_tests():
    """Ejecuta la suite completa de tests de integración final."""
    
    print("=" * 80)
    print("PRUEBAS FINALES DE INTEGRACIÓN - SISTEMA DE PAPELERA DE RECICLAJE")
    print("=" * 80)
    print()
    
    # Obtener el test runner de Django
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2, interactive=False, keepdb=False)
    
    # Lista de módulos de test a ejecutar
    test_modules = [
        # Tests de integración completa
        'tests.test_recycle_bin_integration_complete',
        
        # Tests de seguridad completa
        'tests.test_recycle_bin_security_complete',
        
        # Tests de carga y rendimiento
        'tests.test_recycle_bin_load',
        
        # Tests de regresión
        'tests.test_recycle_bin_regression',
        
        # Tests de navegación e integración UI
        'tests.test_recycle_bin_navigation_integration',
        
        # Tests de permisos
        'tests.test_recycle_bin_permissions',
        
        # Tests de notificaciones
        'tests.test_recycle_bin_notifications',
        
        # Tests de limpieza automática
        'tests.test_recycle_bin_cleanup',
        
        # Tests de auditoría
        'tests.test_deletion_audit_log',
        'tests.test_deletion_audit_reports',
        
        # Tests de tareas periódicas de Celery
        'tests.test_celery_periodic_tasks',
    ]
    
    print(f"Ejecutando {len(test_modules)} módulos de test...")
    print()
    
    # Ejecutar los tests
    failures = test_runner.run_tests(test_modules)
    
    print()
    print("=" * 80)
    if failures:
        print(f"RESULTADO: {failures} test(s) fallaron")
        print("=" * 80)
        return 1
    else:
        print("RESULTADO: Todos los tests pasaron exitosamente ✓")
        print("=" * 80)
        return 0

if __name__ == '__main__':
    sys.exit(run_tests())
