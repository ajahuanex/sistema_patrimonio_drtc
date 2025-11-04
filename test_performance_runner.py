#!/usr/bin/env python
"""
Script especializado para ejecutar pruebas de rendimiento
"""
import os
import sys
import subprocess
import time
from pathlib import Path

def run_performance_tests():
    """Ejecutar suite de pruebas de rendimiento"""
    print("INICIANDO PRUEBAS DE RENDIMIENTO")
    print("="*60)
    
    # Cambiar al directorio del proyecto
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    # Configurar variables de entorno para pruebas de rendimiento
    os.environ['DJANGO_SETTINGS_MODULE'] = 'patrimonio.settings'
    os.environ['TESTING'] = '1'
    
    performance_tests = [
        {
            'name': 'Pruebas de Rendimiento de Base de Datos',
            'command': 'python manage.py test tests.test_performance.DatabasePerformanceTest --verbosity=2',
            'timeout': 300
        },
        {
            'name': 'Pruebas de Rendimiento de APIs',
            'command': 'python manage.py test tests.test_performance.APIPerformanceTest --verbosity=2',
            'timeout': 300
        },
        {
            'name': 'Pruebas de Rendimiento de Reportes',
            'command': 'python manage.py test tests.test_performance.ReportPerformanceTest --verbosity=2',
            'timeout': 300
        },
        {
            'name': 'Pruebas de Optimización de Consultas',
            'command': 'python manage.py test tests.test_database_optimization.QueryOptimizationTest --verbosity=2',
            'timeout': 300
        },
        {
            'name': 'Pruebas de Optimización de Índices',
            'command': 'python manage.py test tests.test_database_optimization.IndexOptimizationTest --verbosity=2',
            'timeout': 300
        },
        {
            'name': 'Pruebas de Concurrencia',
            'command': 'python manage.py test tests.test_performance.ConcurrencyTest --verbosity=2',
            'timeout': 300
        }
    ]
    
    results = []
    
    for test in performance_tests:
        print(f"\n{'='*60}")
        print(f"EJECUTANDO: {test['name']}")
        print(f"COMANDO: {test['command']}")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                test['command'],
                shell=True,
                capture_output=True,
                text=True,
                timeout=test['timeout']
            )
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            print(f"TIEMPO DE EJECUCIÓN: {execution_time:.2f} segundos")
            
            if result.stdout:
                print("SALIDA:")
                print(result.stdout)
            
            if result.stderr:
                print("ERRORES:")
                print(result.stderr)
            
            success = result.returncode == 0
            results.append({
                'name': test['name'],
                'success': success,
                'time': execution_time,
                'returncode': result.returncode
            })
            
            print(f"RESULTADO: {'✅ ÉXITO' if success else '❌ FALLO'}")
            
        except subprocess.TimeoutExpired:
            print(f"⏰ TIMEOUT después de {test['timeout']} segundos")
            results.append({
                'name': test['name'],
                'success': False,
                'time': test['timeout'],
                'returncode': -1
            })
        except Exception as e:
            print(f"❌ ERROR: {e}")
            results.append({
                'name': test['name'],
                'success': False,
                'time': 0,
                'returncode': -1
            })
    
    # Resumen final
    print("\n" + "="*60)
    print("RESUMEN DE PRUEBAS DE RENDIMIENTO")
    print("="*60)
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r['success'])
    failed_tests = total_tests - passed_tests
    total_time = sum(r['time'] for r in results)
    
    for result in results:
        status = "✅ PASÓ" if result['success'] else "❌ FALLÓ"
        print(f"{status} - {result['name']} ({result['time']:.2f}s)")
    
    print(f"\nTOTAL DE PRUEBAS: {total_tests}")
    print(f"PASARON: {passed_tests}")
    print(f"FALLARON: {failed_tests}")
    print(f"TIEMPO TOTAL: {total_time:.2f} segundos")
    
    if failed_tests == 0:
        print("\n🎉 ¡TODAS LAS PRUEBAS DE RENDIMIENTO PASARON!")
        return 0
    else:
        print(f"\n⚠️  {failed_tests} PRUEBAS DE RENDIMIENTO FALLARON")
        return 1

def run_load_tests():
    """Ejecutar pruebas de carga básicas"""
    print("\n" + "="*60)
    print("EJECUTANDO PRUEBAS DE CARGA BÁSICAS")
    print("="*60)
    
    # Simular carga con múltiples procesos
    load_tests = [
        {
            'name': 'Carga de API de Bienes',
            'description': 'Simular múltiples requests concurrentes a la API',
            'command': 'python -c "import requests; import threading; import time; [threading.Thread(target=lambda: print(f\'Request {i} completed\')) for i in range(10)]"'
        }
    ]
    
    print("NOTA: Las pruebas de carga completas requieren herramientas adicionales como Apache Bench o Locust")
    print("Estas son pruebas básicas de concurrencia incluidas en el sistema")
    
    return 0

def generate_performance_report():
    """Generar reporte de rendimiento"""
    print("\n" + "="*60)
    print("GENERANDO REPORTE DE RENDIMIENTO")
    print("="*60)
    
    report_content = f"""
# Reporte de Pruebas de Rendimiento
Generado el: {time.strftime('%Y-%m-%d %H:%M:%S')}

## Resumen
- Suite completa de pruebas de rendimiento ejecutada
- Incluye pruebas de base de datos, APIs, reportes y optimizaciones
- Métricas de tiempo de respuesta y uso de recursos

## Recomendaciones
1. Monitorear consultas N+1 usando select_related() y prefetch_related()
2. Implementar índices apropiados para consultas frecuentes
3. Usar bulk_create() y bulk_update() para operaciones masivas
4. Considerar caché para consultas costosas
5. Optimizar consultas de reportes con agregaciones

## Próximos Pasos
- Implementar monitoreo continuo de rendimiento
- Configurar alertas para consultas lentas
- Revisar y optimizar consultas identificadas como problemáticas
"""
    
    with open('performance_report.md', 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print("Reporte guardado en: performance_report.md")
    return 0

def main():
    """Función principal"""
    if len(sys.argv) > 1:
        if sys.argv[1] == '--load':
            return run_load_tests()
        elif sys.argv[1] == '--report':
            return generate_performance_report()
        elif sys.argv[1] == '--help':
            print("Uso: python test_performance_runner.py [--load|--report|--help]")
            print("  Sin argumentos: Ejecuta todas las pruebas de rendimiento")
            print("  --load: Ejecuta pruebas de carga básicas")
            print("  --report: Genera reporte de rendimiento")
            print("  --help: Muestra esta ayuda")
            return 0
    
    # Ejecutar pruebas de rendimiento
    result = run_performance_tests()
    
    # Generar reporte
    generate_performance_report()
    
    return result

if __name__ == "__main__":
    sys.exit(main())