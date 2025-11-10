"""
Script para ejecutar la suite completa de tests de integración y seguridad
del sistema de papelera de reciclaje
"""
import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'patrimonio.settings')
django.setup()


def run_comprehensive_tests():
    """Ejecutar suite completa de tests"""
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2, interactive=True, keepdb=False)
    
    # Lista de módulos de test a ejecutar
    test_modules = [
        'tests.test_recycle_bin_integration_complete',
        'tests.test_recycle_bin_load',
        'tests.test_recycle_bin_security_complete',
        'tests.test_recycle_bin_regression',
    ]
    
    print("=" * 80)
    print("EJECUTANDO SUITE COMPLETA DE TESTS DE PAPELERA DE RECICLAJE")
    print("=" * 80)
    print()
    print("Módulos de test:")
    for module in test_modules:
        print(f"  - {module}")
    print()
    print("=" * 80)
    print()
    
    failures = test_runner.run_tests(test_modules)
    
    print()
    print("=" * 80)
    if failures:
        print(f"TESTS COMPLETADOS CON {failures} FALLOS")
    else:
        print("TODOS LOS TESTS PASARON EXITOSAMENTE")
    print("=" * 80)
    
    return failures


if __name__ == '__main__':
    failures = run_comprehensive_tests()
    sys.exit(bool(failures))
