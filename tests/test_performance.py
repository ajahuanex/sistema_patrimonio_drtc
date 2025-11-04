"""
Pruebas de rendimiento para el sistema
"""
import time
import statistics
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.test.utils import override_settings
from django.db import connection
from django.test import TransactionTestCase
from rest_framework.test import APITestCase
from apps.catalogo.models import Catalogo
from apps.oficinas.models import Oficina
from apps.bienes.models import BienPatrimonial
from apps.reportes.utils import ReportGenerator


class DatabasePerformanceTest(TransactionTestCase):
    """Pruebas de rendimiento de base de datos"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Crear datos base
        self.catalogo = Catalogo.objects.create(
            codigo='04220001',
            denominacion='TEST BIEN',
            grupo='04-AGRÍCOLA Y PESQUERO',
            clase='22-EQUIPO',
            resolucion='R.D. 001-2024',
            estado='ACTIVO'
        )
        
        self.oficina = Oficina.objects.create(
            codigo='DIR-001',
            nombre='Dirección Regional',
            responsable='Director Regional'
        )
    
    def create_test_data(self, count=1000):
        """Crear datos de prueba en cantidad"""
        bienes = []
        for i in range(count):
            bienes.append(BienPatrimonial(
                codigo_patrimonial=f'PAT-{i:06d}-2024',
                catalogo=self.catalogo,
                oficina=self.oficina,
                estado_bien='B',
                marca=f'MARCA {i % 10}',
                modelo=f'MODELO {i % 20}',
                serie=f'SER{i:06d}',
                created_by=self.user
            ))
        
        # Inserción masiva
        start_time = time.time()
        BienPatrimonial.objects.bulk_create(bienes, batch_size=100)
        end_time = time.time()
        
        print(f"Creación de {count} bienes: {end_time - start_time:.2f} segundos")
        return end_time - start_time
    
    def test_bulk_insert_performance(self):
        """Prueba rendimiento de inserción masiva"""
        # Probar diferentes tamaños
        sizes = [100, 500, 1000]
        times = []
        
        for size in sizes:
            # Limpiar datos anteriores
            BienPatrimonial.objects.all().delete()
            
            # Medir tiempo de inserción
            insert_time = self.create_test_data(size)
            times.append(insert_time)
            
            # Verificar que se insertaron correctamente
            self.assertEqual(BienPatrimonial.objects.count(), size)
        
        # Verificar que el tiempo no crece exponencialmente
        # (debería ser aproximadamente lineal)
        if len(times) >= 2:
            ratio = times[-1] / times[0]
            size_ratio = sizes[-1] / sizes[0]
            # El tiempo no debería crecer más del doble del ratio de tamaño
            self.assertLess(ratio, size_ratio * 2)
    
    def test_query_performance_with_indexes(self):
        """Prueba rendimiento de consultas con índices"""
        # Crear datos de prueba
        self.create_test_data(1000)
        
        # Medir consultas comunes
        queries = [
            ('Búsqueda por código', lambda: BienPatrimonial.objects.filter(codigo_patrimonial='PAT-000500-2024')),
            ('Filtro por estado', lambda: BienPatrimonial.objects.filter(estado_bien='B')),
            ('Filtro por oficina', lambda: BienPatrimonial.objects.filter(oficina=self.oficina)),
            ('Búsqueda por marca', lambda: BienPatrimonial.objects.filter(marca='MARCA 5')),
            ('Consulta con JOIN', lambda: BienPatrimonial.objects.select_related('catalogo', 'oficina').filter(estado_bien='B')),
        ]
        
        for query_name, query_func in queries:
            # Ejecutar múltiples veces para obtener promedio
            times = []
            for _ in range(5):
                start_time = time.time()
                list(query_func())  # Forzar evaluación del QuerySet
                end_time = time.time()
                times.append(end_time - start_time)
            
            avg_time = statistics.mean(times)
            print(f"{query_name}: {avg_time:.4f} segundos promedio")
            
            # Las consultas deberían ser rápidas (menos de 1 segundo)
            self.assertLess(avg_time, 1.0, f"{query_name} tomó demasiado tiempo: {avg_time:.4f}s")
    
    def test_complex_query_performance(self):
        """Prueba rendimiento de consultas complejas"""
        self.create_test_data(1000)
        
        # Consulta compleja con múltiples filtros y agregaciones
        start_time = time.time()
        
        result = BienPatrimonial.objects.select_related('catalogo', 'oficina').filter(
            estado_bien__in=['B', 'R'],
            marca__icontains='MARCA'
        ).order_by('codigo_patrimonial')[:50]
        
        # Forzar evaluación
        list(result)
        
        end_time = time.time()
        query_time = end_time - start_time
        
        print(f"Consulta compleja: {query_time:.4f} segundos")
        
        # Debería completarse en menos de 0.5 segundos
        self.assertLess(query_time, 0.5)
    
    def test_database_connection_efficiency(self):
        """Prueba eficiencia de conexiones a base de datos"""
        self.create_test_data(100)
        
        # Contar consultas realizadas
        initial_queries = len(connection.queries)
        
        # Operación que debería ser eficiente
        bienes = BienPatrimonial.objects.select_related('catalogo', 'oficina').all()[:10]
        for bien in bienes:
            # Acceder a campos relacionados (no debería generar consultas adicionales)
            _ = bien.catalogo.denominacion
            _ = bien.oficina.nombre
        
        final_queries = len(connection.queries)
        queries_used = final_queries - initial_queries
        
        print(f"Consultas utilizadas: {queries_used}")
        
        # Debería usar pocas consultas (idealmente 1 con select_related)
        self.assertLessEqual(queries_used, 3)


class APIPerformanceTest(APITestCase):
    """Pruebas de rendimiento de APIs"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Crear datos base
        self.catalogo = Catalogo.objects.create(
            codigo='04220001',
            denominacion='TEST BIEN',
            grupo='04-AGRÍCOLA Y PESQUERO',
            clase='22-EQUIPO',
            resolucion='R.D. 001-2024',
            estado='ACTIVO'
        )
        
        self.oficina = Oficina.objects.create(
            codigo='DIR-001',
            nombre='Dirección Regional',
            responsable='Director Regional'
        )
        
        # Crear datos de prueba
        bienes = []
        for i in range(200):
            bienes.append(BienPatrimonial(
                codigo_patrimonial=f'PAT-{i:06d}-2024',
                catalogo=self.catalogo,
                oficina=self.oficina,
                estado_bien='B' if i % 2 == 0 else 'R',
                marca=f'MARCA {i % 10}',
                modelo=f'MODELO {i % 20}',
                created_by=self.user
            ))
        
        BienPatrimonial.objects.bulk_create(bienes)
    
    def measure_api_response_time(self, url, method='GET', data=None, iterations=5):
        """Medir tiempo de respuesta de API"""
        times = []
        
        for _ in range(iterations):
            start_time = time.time()
            
            if method == 'GET':
                response = self.client.get(url)
            elif method == 'POST':
                response = self.client.post(url, data, format='json')
            
            end_time = time.time()
            
            # Verificar que la respuesta sea exitosa
            self.assertIn(response.status_code, [200, 201])
            
            times.append(end_time - start_time)
        
        avg_time = statistics.mean(times)
        max_time = max(times)
        min_time = min(times)
        
        return {
            'avg': avg_time,
            'max': max_time,
            'min': min_time,
            'times': times
        }
    
    def test_bienes_list_api_performance(self):
        """Prueba rendimiento de API de listado de bienes"""
        url = reverse('bienes:api_list')
        
        # Sin filtros
        result = self.measure_api_response_time(url)
        print(f"API Bienes List (sin filtros): {result['avg']:.4f}s promedio")
        self.assertLess(result['avg'], 2.0)
        
        # Con filtros
        url_with_filters = f"{url}?estado_bien=B&oficina_id={self.oficina.id}"
        result = self.measure_api_response_time(url_with_filters)
        print(f"API Bienes List (con filtros): {result['avg']:.4f}s promedio")
        self.assertLess(result['avg'], 2.0)
        
        # Con búsqueda
        url_with_search = f"{url}?search=PAT-000001"
        result = self.measure_api_response_time(url_with_search)
        print(f"API Bienes List (con búsqueda): {result['avg']:.4f}s promedio")
        self.assertLess(result['avg'], 2.0)
    
    def test_bienes_detail_api_performance(self):
        """Prueba rendimiento de API de detalle de bien"""
        bien = BienPatrimonial.objects.first()
        url = reverse('bienes:api_detail', kwargs={'pk': bien.id})
        
        result = self.measure_api_response_time(url)
        print(f"API Bienes Detail: {result['avg']:.4f}s promedio")
        
        # Debería ser muy rápido
        self.assertLess(result['avg'], 0.5)
    
    def test_pagination_performance(self):
        """Prueba rendimiento de paginación"""
        url = reverse('bienes:api_list')
        
        # Primera página
        result1 = self.measure_api_response_time(f"{url}?page=1&page_size=20")
        print(f"Paginación página 1: {result1['avg']:.4f}s promedio")
        
        # Página intermedia
        result2 = self.measure_api_response_time(f"{url}?page=5&page_size=20")
        print(f"Paginación página 5: {result2['avg']:.4f}s promedio")
        
        # Última página
        result3 = self.measure_api_response_time(f"{url}?page=10&page_size=20")
        print(f"Paginación página 10: {result3['avg']:.4f}s promedio")
        
        # Los tiempos deberían ser similares
        self.assertLess(result1['avg'], 2.0)
        self.assertLess(result2['avg'], 2.0)
        self.assertLess(result3['avg'], 2.0)
        
        # La diferencia entre páginas no debería ser significativa
        max_diff = max(result1['avg'], result2['avg'], result3['avg']) - min(result1['avg'], result2['avg'], result3['avg'])
        self.assertLess(max_diff, 1.0)


class ReportPerformanceTest(TestCase):
    """Pruebas de rendimiento de reportes"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Crear datos base
        self.catalogo = Catalogo.objects.create(
            codigo='04220001',
            denominacion='TEST BIEN',
            grupo='04-AGRÍCOLA Y PESQUERO',
            clase='22-EQUIPO',
            resolucion='R.D. 001-2024',
            estado='ACTIVO'
        )
        
        self.oficina1 = Oficina.objects.create(
            codigo='DIR-001',
            nombre='Dirección Regional',
            responsable='Director Regional'
        )
        
        self.oficina2 = Oficina.objects.create(
            codigo='ADM-001',
            nombre='Administración',
            responsable='Administrador'
        )
        
        # Crear datos de prueba para reportes
        bienes = []
        for i in range(500):
            bienes.append(BienPatrimonial(
                codigo_patrimonial=f'PAT-{i:06d}-2024',
                catalogo=self.catalogo,
                oficina=self.oficina1 if i % 2 == 0 else self.oficina2,
                estado_bien=['B', 'R', 'N', 'M'][i % 4],
                marca=f'MARCA {i % 10}',
                modelo=f'MODELO {i % 20}',
                created_by=self.user
            ))
        
        BienPatrimonial.objects.bulk_create(bienes)
        
        self.report_generator = ReportGenerator()
    
    def test_basic_report_generation_performance(self):
        """Prueba rendimiento de generación de reportes básicos"""
        start_time = time.time()
        
        resultado = self.report_generator.generar_reporte({}, self.user)
        
        end_time = time.time()
        generation_time = end_time - start_time
        
        print(f"Generación de reporte básico (500 bienes): {generation_time:.4f}s")
        
        self.assertTrue(resultado['success'])
        self.assertEqual(len(resultado['data']), 500)
        
        # Debería completarse en menos de 5 segundos
        self.assertLess(generation_time, 5.0)
    
    def test_filtered_report_performance(self):
        """Prueba rendimiento de reportes con filtros"""
        filtros = {
            'estado_bien': 'B',
            'oficina_id': self.oficina1.id
        }
        
        start_time = time.time()
        
        resultado = self.report_generator.generar_reporte(filtros, self.user)
        
        end_time = time.time()
        generation_time = end_time - start_time
        
        print(f"Generación de reporte filtrado: {generation_time:.4f}s")
        
        self.assertTrue(resultado['success'])
        # Debería filtrar correctamente
        self.assertLess(len(resultado['data']), 500)
        
        # Debería ser más rápido que el reporte completo
        self.assertLess(generation_time, 3.0)
    
    def test_statistics_generation_performance(self):
        """Prueba rendimiento de generación de estadísticas"""
        start_time = time.time()
        
        stats = self.report_generator.generar_estadisticas()
        
        end_time = time.time()
        generation_time = end_time - start_time
        
        print(f"Generación de estadísticas: {generation_time:.4f}s")
        
        self.assertIn('total_bienes', stats)
        self.assertIn('por_estado', stats)
        self.assertIn('por_oficina', stats)
        
        # Las estadísticas deberían generarse rápidamente
        self.assertLess(generation_time, 2.0)
    
    def test_complex_report_with_aggregations(self):
        """Prueba rendimiento de reportes complejos con agregaciones"""
        start_time = time.time()
        
        # Simular reporte complejo con múltiples agregaciones
        from django.db.models import Count, Q
        
        result = BienPatrimonial.objects.select_related('catalogo', 'oficina').aggregate(
            total_bienes=Count('id'),
            bienes_buenos=Count('id', filter=Q(estado_bien='B')),
            bienes_regulares=Count('id', filter=Q(estado_bien='R')),
            bienes_nuevos=Count('id', filter=Q(estado_bien='N')),
            bienes_malos=Count('id', filter=Q(estado_bien='M'))
        )
        
        end_time = time.time()
        generation_time = end_time - start_time
        
        print(f"Reporte complejo con agregaciones: {generation_time:.4f}s")
        
        self.assertEqual(result['total_bienes'], 500)
        
        # Debería completarse rápidamente
        self.assertLess(generation_time, 1.0)


class WebInterfacePerformanceTest(TestCase):
    """Pruebas de rendimiento de interfaz web"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        
        # Crear datos base
        self.catalogo = Catalogo.objects.create(
            codigo='04220001',
            denominacion='TEST BIEN',
            grupo='04-AGRÍCOLA Y PESQUERO',
            clase='22-EQUIPO',
            resolucion='R.D. 001-2024',
            estado='ACTIVO'
        )
        
        self.oficina = Oficina.objects.create(
            codigo='DIR-001',
            nombre='Dirección Regional',
            responsable='Director Regional'
        )
        
        # Crear algunos bienes para las vistas
        for i in range(50):
            BienPatrimonial.objects.create(
                codigo_patrimonial=f'PAT-{i:03d}-2024',
                catalogo=self.catalogo,
                oficina=self.oficina,
                estado_bien='B',
                created_by=self.user
            )
    
    def measure_view_response_time(self, url, iterations=3):
        """Medir tiempo de respuesta de vista"""
        times = []
        
        for _ in range(iterations):
            start_time = time.time()
            response = self.client.get(url)
            end_time = time.time()
            
            self.assertEqual(response.status_code, 200)
            times.append(end_time - start_time)
        
        return statistics.mean(times)
    
    def test_dashboard_performance(self):
        """Prueba rendimiento del dashboard"""
        url = reverse('home')
        
        avg_time = self.measure_view_response_time(url)
        print(f"Dashboard: {avg_time:.4f}s promedio")
        
        # El dashboard debería cargar rápidamente
        self.assertLess(avg_time, 3.0)
    
    def test_bienes_list_view_performance(self):
        """Prueba rendimiento de vista de lista de bienes"""
        url = reverse('bienes:list')
        
        avg_time = self.measure_view_response_time(url)
        print(f"Lista de bienes: {avg_time:.4f}s promedio")
        
        # La lista debería cargar en tiempo razonable
        self.assertLess(avg_time, 4.0)
    
    def test_reportes_dashboard_performance(self):
        """Prueba rendimiento del dashboard de reportes"""
        url = reverse('reportes:dashboard')
        
        avg_time = self.measure_view_response_time(url)
        print(f"Dashboard de reportes: {avg_time:.4f}s promedio")
        
        # El dashboard de reportes puede tomar más tiempo por las estadísticas
        self.assertLess(avg_time, 5.0)


class ConcurrencyTest(TransactionTestCase):
    """Pruebas de concurrencia"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.catalogo = Catalogo.objects.create(
            codigo='04220001',
            denominacion='TEST BIEN',
            grupo='04-AGRÍCOLA Y PESQUERO',
            clase='22-EQUIPO',
            resolucion='R.D. 001-2024',
            estado='ACTIVO'
        )
        
        self.oficina = Oficina.objects.create(
            codigo='DIR-001',
            nombre='Dirección Regional',
            responsable='Director Regional'
        )
        
        self.bien = BienPatrimonial.objects.create(
            codigo_patrimonial='PAT-CONCURRENCY-001',
            catalogo=self.catalogo,
            oficina=self.oficina,
            estado_bien='B',
            created_by=self.user
        )
    
    def test_concurrent_bien_updates(self):
        """Prueba actualizaciones concurrentes de bienes"""
        import threading
        import time
        
        results = []
        errors = []
        
        def update_bien(thread_id):
            try:
                # Simular actualización concurrente
                bien = BienPatrimonial.objects.get(id=self.bien.id)
                bien.marca = f'MARCA_THREAD_{thread_id}'
                time.sleep(0.1)  # Simular procesamiento
                bien.save()
                results.append(f'Thread {thread_id} success')
            except Exception as e:
                errors.append(f'Thread {thread_id} error: {str(e)}')
        
        # Crear múltiples threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=update_bien, args=(i,))
            threads.append(thread)
        
        # Iniciar todos los threads
        for thread in threads:
            thread.start()
        
        # Esperar a que terminen
        for thread in threads:
            thread.join()
        
        print(f"Resultados concurrencia: {len(results)} éxitos, {len(errors)} errores")
        
        # Al menos algunos threads deberían completarse exitosamente
        self.assertGreater(len(results), 0)
        
        # Verificar estado final del bien
        self.bien.refresh_from_db()
        self.assertIsNotNone(self.bien.marca)


@override_settings(DEBUG=False)
class MemoryUsageTest(TestCase):
    """Pruebas básicas de uso de memoria"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.catalogo = Catalogo.objects.create(
            codigo='04220001',
            denominacion='TEST BIEN',
            grupo='04-AGRÍCOLA Y PESQUERO',
            clase='22-EQUIPO',
            resolucion='R.D. 001-2024',
            estado='ACTIVO'
        )
        
        self.oficina = Oficina.objects.create(
            codigo='DIR-001',
            nombre='Dirección Regional',
            responsable='Director Regional'
        )
    
    def test_large_queryset_memory_usage(self):
        """Prueba uso de memoria con QuerySets grandes"""
        # Crear muchos bienes
        bienes = []
        for i in range(1000):
            bienes.append(BienPatrimonial(
                codigo_patrimonial=f'PAT-{i:06d}-2024',
                catalogo=self.catalogo,
                oficina=self.oficina,
                estado_bien='B',
                created_by=self.user
            ))
        
        BienPatrimonial.objects.bulk_create(bienes)
        
        # Usar iterator() para evitar cargar todo en memoria
        count = 0
        for bien in BienPatrimonial.objects.iterator():
            count += 1
            if count > 100:  # Solo procesar algunos para la prueba
                break
        
        self.assertGreater(count, 0)
        
        # Verificar que values() también funciona eficientemente
        values_count = BienPatrimonial.objects.values('codigo_patrimonial').count()
        self.assertEqual(values_count, 1000)