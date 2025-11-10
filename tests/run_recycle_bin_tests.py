#!/usr/bin/env python
"""
Script para ejecutar todos los tests del sistema de papelera de reciclaje
con reportes detallados y métricas de cobertura.
"""
import os
import sys
import django
import subprocess
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'patrimonio.settings')
django.setup()


def print_header(title):
    """Imprime un encabezado formateado"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def run_test_suite(suite_name, test_path):
    """Ejecuta una suite de tests y retorna el resultado"""
    print(f"\n🧪 Ejecutando: {suite_name}")
    print("-" * 80)
    
    try:
        result = subprocess.run(
            ['python', 'manage.py', 'test', test_path, '--verbosity=2'],
            capture_output=True,
            text=True,
            timeout=600  # 10 minutos timeout
        )
        
        # Mostrar output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        success = result.returncode == 0
        
        if success:
            print(f"✅ {suite_name}: PASSED")
        else:
            print(f"❌ {suite_name}: FAILED")
        
        return success, result.stdout
        
    except subprocess.TimeoutExpired:
        print(f"⏱️ {suite_name}: TIMEOUT (>10 minutos)")
        return False, ""
    except Exception as e:
        print(f"💥 {suite_name}: ERROR - {str(e)}")
        return False, ""


def run_coverage_analysis():
    """Ejecuta análisis de cobertura de código"""
    print_header("ANÁLISIS DE COBERTURA")
    
    try:
        # Ejecutar tests con coverage
        print("📊 Ejecutando tests con análisis de cobertura...")
        subprocess.run([
            'coverage', 'run', '--source=apps/core',
            'manage.py', 'test',
            'tests.test_recycle_bin_integration_complete',
            'tests.test_recycle_bin_load',
            'tests.test_recycle_bin_security_complete',
            'tests.test_recycle_bin_regression'
        ], check=False)
        
        # Generar reporte
        print("\n📈 Generando reporte de cobertura...")
        result = subprocess.run(
            ['coverage', 'report'],
            capture_output=True,
            text=True
        )
        
        if result.stdout:
            print(result.stdout)
        
        # Generar HTML
        print("\n🌐 Generando reporte HTML...")
        subprocess.run(['coverage', 'html'], check=False)
        print("✅ Reporte HTML generado en: htmlcov/index.html")
        
        return True
        
    except FileNotFoundError:
        print("⚠️ Coverage no está instalado. Instalar con: pip install coverage")
        return False
    except Exception as e:
        print(f"💥 Error en análisis de cobertura: {str(e)}")
        return False


def main():
    """Función principal"""
    start_time = datetime.now()
    
    print_header("SISTEMA DE PAPELERA DE RECICLAJE - TEST RUNNER")
    print(f"📅 Fecha: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🐍 Python: {sys.version.split()[0]}")
    print(f"🎯 Django: {django.get_version()}")
    
    # Definir suites de tests
    test_suites = [
        ("Tests de Integración Completa", "tests.test_recycle_bin_integration_complete"),
        ("Tests de Carga y Rendimiento", "tests.test_recycle_bin_load"),
        ("Tests de Seguridad", "tests.test_recycle_bin_security_complete"),
        ("Tests de Regresión", "tests.test_recycle_bin_regression"),
    ]
    
    # Ejecutar cada suite
    results = {}
    for suite_name, test_path in test_suites:
        success, output = run_test_suite(suite_name, test_path)
        results[suite_name] = success
    
    # Resumen de resultados
    print_header("RESUMEN DE RESULTADOS")
    
    total_suites = len(results)
    passed_suites = sum(1 for success in results.values() if success)
    failed_suites = total_suites - passed_suites
    
    print(f"📊 Total de Suites: {total_suites}")
    print(f"✅ Suites Exitosas: {passed_suites}")
    print(f"❌ Suites Fallidas: {failed_suites}")
    print()
    
    for suite_name, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"  {status} - {suite_name}")
    
    # Análisis de cobertura (opcional)
    print("\n" + "=" * 80)
    response = input("\n¿Desea ejecutar análisis de cobertura? (s/n): ")
    if response.lower() in ['s', 'si', 'yes', 'y']:
        run_coverage_analysis()
    
    # Tiempo total
    end_time = datetime.now()
    duration = end_time - start_time
    
    print_header("FINALIZADO")
    print(f"⏱️ Tiempo total: {duration}")
    print(f"📅 Finalizado: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Exit code
    exit_code = 0 if all(results.values()) else 1
    
    if exit_code == 0:
        print("\n🎉 ¡Todos los tests pasaron exitosamente!")
    else:
        print("\n⚠️ Algunos tests fallaron. Revisar logs arriba.")
    
    return exit_code


if __name__ == '__main__':
    sys.exit(main())
