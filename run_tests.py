#!/usr/bin/env python
"""
Script para ejecutar todas las pruebas del sistema
"""
import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """Ejecutar comando y mostrar resultado"""
    print(f"\n{'='*60}")
    print(f"EJECUTANDO: {description}")
    print(f"COMANDO: {command}")
    print(f"{'='*60}")
    
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.stdout:
        print("STDOUT:")
        print(result.stdout)
    
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    
    print(f"CÓDIGO DE SALIDA: {result.returncode}")
    
    return result.returncode == 0

def main():
    """Función principal"""
    print("INICIANDO SUITE COMPLETA DE PRUEBAS")
    print("="*60)
    
    # Cambiar al directorio del proyecto
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    # Lista de comandos de prueba
    test_commands = [
        # Pruebas unitarias básicas con Django
        ("python manage.py test apps.catalogo.tests", "Pruebas unitarias - Catálogo"),
        ("python manage.py test apps.oficinas.tests", "Pruebas unitarias - Oficinas"),
        ("python manage.py test apps.bienes.tests", "Pruebas unitarias - Bienes"),
        ("python manage.py test apps.core.tests", "Pruebas unitarias - Core"),
        ("python manage.py test apps.reportes.tests", "Pruebas unitarias - Reportes"),
        ("python manage.py test apps.mobile.tests", "Pruebas unitarias - Mobile"),
        ("python manage.py test apps.notificaciones.tests", "Pruebas unitarias - Notificaciones"),
        
        # Pruebas de integración
        ("python manage.py test tests.test_api_integration", "Pruebas de integración - APIs"),
        ("python manage.py test tests.test_import_export", "Pruebas de integración - Import/Export"),
        ("python manage.py test tests.test_user_flows", "Pruebas de integración - Flujos de usuario"),
        
        # Pruebas de rendimiento
        ("python manage.py test tests.test_performance", "Pruebas de rendimiento"),
        ("python manage.py test tests.test_database_optimization", "Pruebas de optimización de BD"),
        
        # Pruebas con pytest (si está disponible)
        ("pytest --tb=short --disable-warnings -m 'not slow'", "Pruebas rápidas con pytest"),
        ("pytest --tb=short --disable-warnings -m 'slow'", "Pruebas lentas con pytest"),
        
        # Verificar cobertura
        ("coverage run --source='.' manage.py test", "Ejecutar con cobertura"),
        ("coverage report --show-missing", "Reporte de cobertura detallado"),
        ("coverage html", "Generar reporte HTML de cobertura"),
    ]
    
    results = []
    
    for command, description in test_commands:
        try:
            success = run_command(command, description)
            results.append((description, success))
        except Exception as e:
            print(f"ERROR ejecutando {description}: {e}")
            results.append((description, False))
    
    # Resumen final
    print("\n" + "="*60)
    print("RESUMEN DE PRUEBAS")
    print("="*60)
    
    total_tests = len(results)
    passed_tests = sum(1 for _, success in results if success)
    failed_tests = total_tests - passed_tests
    
    for description, success in results:
        status = "✅ PASÓ" if success else "❌ FALLÓ"
        print(f"{status} - {description}")
    
    print(f"\nTOTAL: {total_tests}")
    print(f"PASARON: {passed_tests}")
    print(f"FALLARON: {failed_tests}")
    
    if failed_tests == 0:
        print("\n🎉 ¡TODAS LAS PRUEBAS PASARON!")
        return 0
    else:
        print(f"\n⚠️  {failed_tests} PRUEBAS FALLARON")
        return 1

if __name__ == "__main__":
    sys.exit(main())