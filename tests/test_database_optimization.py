"""
Pruebas de optimización de base de datos
"""
from django.test import TestCase, TransactionTestCase
from django.db import connection, transaction
from django.test.utils import override_settings
from django.contrib.auth.models import User
from django.db.models import Count, Q, Prefetch
from apps.catalogo.models import Catalogo
from apps.oficinas.models import Oficina
from apps.bienes.models import BienPatrimonial, MovimientoBien, HistorialEstado
import time


class QueryOptimizationTest(TestCase):
    """Pruebas de optimización de consultas"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Crear datos base
        self.catalogo1 = Catalogo.objects.create(
            codigo='04220001',
            denominacion='ELECTROEYACULADOR PARA BOVINOS',
            grupo='04-AGRÍCOLA Y PESQUERO',
            clase='22-EQUIPO',
            resolucion='R.D. 001-2024',
            estado='ACTIVO'
        )
        
        self.catalogo2 = Catalogo.objects.create(
            codigo='05110001',
            denominacion='COMPUTADORA PERSONAL',
            grupo='05-INFORMÁTICA Y COMUNICACIONES',
            clase='11-EQUIPO',
            resolucion='R.D. 002-2024',
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
        
        # Crear bienes de prueba
        bienes = []
        for i in range(100):
            bienes.append(BienPatrimonial(
                codigo_patrimonial=f'PAT-{i:06d}-2024',
                catalogo=self.catalogo1 if i % 2 == 0 else self.catalogo2,
                oficina=self.oficina1 if i % 3 == 0 else self.oficina2,
                estado_bien=['B', 'R', 'N', 'M'][i % 4],
                marca=f'MARCA {i % 10}',
                modelo=f'MODELO {i % 20}',
                created_by=self.user
            ))
        
        BienPatrimonial.objects.bulk_create(bienes)
    
    def count_queries(self, func):
        """Contar número de consultas ejecutadas por una función"""
        initial_queries = len(connection.queries)
        func()
        final_queries = len(connection.queries)
        return final_queries - initial_queries
    
    def test_select_related_optimization(self):
        """Prueba optimización con select_related"""
        # Sin optimización (N+1 queries)
        def without_optimization():
            bienes = BienPatrimonial.objects.all()[:10]
            for bien in bienes:
                _ = bien.catalogo.denominacion
                _ = bien.oficina.nombre
        
        queries_without = self.count_queries(without_optimization)
        
        # Con optimización
        def with_optimization():
            bienes = BienPatrimonial.objects.select_related('catalogo', 'oficina').all()[:10]
            for bien in bienes:
                _ = bien.catalogo.denominacion
                _ = bien.oficina.nombre
        
        queries_with = self.count_queries(with_optimization)
        
        print(f"Sin optimización: {queries_without} consultas")
        print(f"Con select_related: {queries_with} consultas")
        
        # Con select_related debería usar significativamente menos consultas
        self.assertLess(queries_with, queries_without)
        self.assertLessEqual(queries_with, 3)  # Idealmente 1 consulta
    
    def test_prefetch_related_optimization(self):
        """Prueba optimización con prefetch_related"""
        # Crear algunos movimientos
        bien = BienPatrimonial.objects.first()
        for i in range(5):
            MovimientoBien.objects.create(
                bien=bien,
                oficina_origen=self.oficina1,
                oficina_destino=self.oficina2,
                motivo=f'Movimiento {i}',
                usuario=self.user
            )
        
        # Sin optimización
        def without_prefetch():
            bienes = BienPatrimonial.objects.all()[:5]
            for bien in bienes:
                movimientos = list(bien.movimientobien_set.all())
        
        queries_without = self.count_queries(without_prefetch)
        
        # Con prefetch_related
        def with_prefetch():
            bienes = BienPatrimonial.objects.prefetch_related('movimientobien_set').all()[:5]
            for bien in bienes:
                movimientos = list(bien.movimientobien_set.all())
        
        queries_with = self.count_queries(with_prefetch)
        
        print(f"Sin prefetch: {queries_without} consultas")
        print(f"Con prefetch_related: {queries_with} consultas")
        
        self.assertLess(queries_with, queries_without)
    
    def test_only_defer_optimization(self):
        """Prueba optimización con only() y defer()"""
        # Consulta con todos los campos
        def all_fields():
            bienes = list(BienPatrimonial.objects.all()[:20])
        
        queries_all = self.count_queries(all_fields)
        
        # Consulta solo campos necesarios
        def only_needed_fields():
            bienes = list(BienPatrimonial.objects.only(
                'codigo_patrimonial', 'estado_bien', 'marca'
            ).all()[:20])
        
        queries_only = self.count_queries(only_needed_fields)
        
        # Consulta excluyendo campos grandes
        def defer_large_fields():
            bienes = list(BienPatrimonial.objects.defer(
                'observaciones', 'dimension'
            ).all()[:20])
        
        queries_defer = self.count_queries(defer_large_fields)
        
        print(f"Todos los campos: {queries_all} consultas")
        print(f"Solo campos necesarios: {queries_only} consultas")
        print(f"Defer campos grandes: {queries_defer} consultas")
        
        # Las consultas optimizadas no deberían usar más consultas
        self.assertLessEqual(queries_only, queries_all + 1)
        self.assertLessEqual(queries_defer, queries_all + 1)
    
    def test_aggregation_optimization(self):
        """Prueba optimización de agregaciones"""
        # Agregación simple
        def simple_aggregation():
            return BienPatrimonial.objects.aggregate(
                total=Count('id'),
                buenos=Count('id', filter=Q(estado_bien='B')),
                regulares=Count('id', filter=Q(estado_bien='R'))
            )
        
        queries_simple = self.count_queries(simple_aggregation)
        
        # Agregación con GROUP BY
        def group_aggregation():
            return list(BienPatrimonial.objects.values('estado_bien').annotate(
                count=Count('id')
            ).order_by('estado_bien'))
        
        queries_group = self.count_queries(group_aggregation)
        
        print(f"Agregación simple: {queries_simple} consultas")
        print(f"Agregación con GROUP BY: {queries_group} consultas")
        
        # Ambas deberían usar pocas consultas
        self.assertLessEqual(queries_simple, 2)
        self.assertLessEqual(queries_group, 2)
    
    def test_bulk_operations_optimization(self):
        """Prueba optimización de operaciones masivas"""
        # Crear datos para actualización masiva
        bienes_ids = list(BienPatrimonial.objects.filter(estado_bien='B').values_list('id', flat=True)[:10])
        
        # Actualización individual (ineficiente)
        def individual_updates():
            for bien_id in bienes_ids:
                BienPatrimonial.objects.filter(id=bien_id).update(marca='MARCA_INDIVIDUAL')
        
        queries_individual = self.count_queries(individual_updates)
        
        # Restaurar datos
        BienPatrimonial.objects.filter(id__in=bienes_ids).update(marca='MARCA_ORIGINAL')
        
        # Actualización masiva (eficiente)
        def bulk_update():
            BienPatrimonial.objects.filter(id__in=bienes_ids).update(marca='MARCA_BULK')
        
        queries_bulk = self.count_queries(bulk_update)
        
        print(f"Actualizaciones individuales: {queries_individual} consultas")
        print(f"Actualización masiva: {queries_bulk} consultas")
        
        # La actualización masiva debería usar menos consultas
        self.assertLess(queries_bulk, queries_individual)
        self.assertLessEqual(queries_bulk, 2)


class IndexOptimizationTest(TransactionTestCase):
    """Pruebas de optimización de índices"""
    
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
    
    def create_large_dataset(self, size=1000):
        """Crear dataset grande para pruebas de índices"""
        bienes = []
        for i in range(size):
            bienes.append(BienPatrimonial(
                codigo_patrimonial=f'PAT-{i:06d}-2024',
                catalogo=self.catalogo,
                oficina=self.oficina,
                estado_bien=['B', 'R', 'N', 'M'][i % 4],
                marca=f'MARCA {i % 100}',
                modelo=f'MODELO {i % 200}',
                serie=f'SER{i:06d}',
                created_by=self.user
            ))
        
        BienPatrimonial.objects.bulk_create(bienes, batch_size=100)
    
    def measure_query_time(self, query_func, iterations=5):
        """Medir tiempo de ejecución de consulta"""
        times = []
        for _ in range(iterations):
            start_time = time.time()
            list(query_func())  # Forzar evaluación
            end_time = time.time()
            times.append(end_time - start_time)
        
        return sum(times) / len(times)
    
    def test_primary_key_lookup_performance(self):
        """Prueba rendimiento de búsqueda por clave primaria"""
        self.create_large_dataset(1000)
        
        # Obtener algunos IDs para buscar
        sample_ids = list(BienPatrimonial.objects.values_list('id', flat=True)[:10])
        
        def pk_lookup():
            return BienPatrimonial.objects.filter(id__in=sample_ids)
        
        avg_time = self.measure_query_time(pk_lookup)
        print(f"Búsqueda por PK (1000 registros): {avg_time:.4f}s promedio")
        
        # Debería ser muy rápido
        self.assertLess(avg_time, 0.1)
    
    def test_indexed_field_lookup_performance(self):
        """Prueba rendimiento de búsqueda por campos indexados"""
        self.create_large_dataset(1000)
        
        # Búsqueda por código patrimonial (debería estar indexado)
        def codigo_lookup():
            return BienPatrimonial.objects.filter(codigo_patrimonial='PAT-000500-2024')
        
        avg_time = self.measure_query_time(codigo_lookup)
        print(f"Búsqueda por código patrimonial: {avg_time:.4f}s promedio")
        
        # Debería ser rápido con índice
        self.assertLess(avg_time, 0.1)
    
    def test_foreign_key_lookup_performance(self):
        """Prueba rendimiento de búsqueda por claves foráneas"""
        self.create_large_dataset(1000)
        
        def fk_lookup():
            return BienPatrimonial.objects.filter(oficina=self.oficina)
        
        avg_time = self.measure_query_time(fk_lookup)
        print(f"Búsqueda por FK oficina: {avg_time:.4f}s promedio")
        
        # Debería ser razonablemente rápido
        self.assertLess(avg_time, 0.5)
    
    def test_text_search_performance(self):
        """Prueba rendimiento de búsqueda de texto"""
        self.create_large_dataset(1000)
        
        # Búsqueda exacta
        def exact_search():
            return BienPatrimonial.objects.filter(marca='MARCA 50')
        
        avg_time_exact = self.measure_query_time(exact_search)
        print(f"Búsqueda exacta por marca: {avg_time_exact:.4f}s promedio")
        
        # Búsqueda con LIKE
        def like_search():
            return BienPatrimonial.objects.filter(marca__icontains='MARCA 5')
        
        avg_time_like = self.measure_query_time(like_search)
        print(f"Búsqueda LIKE por marca: {avg_time_like:.4f}s promedio")
        
        # La búsqueda exacta debería ser más rápida
        self.assertLess(avg_time_exact, avg_time_like)
        self.assertLess(avg_time_like, 1.0)
    
    def test_compound_index_performance(self):
        """Prueba rendimiento con índices compuestos"""
        self.create_large_dataset(1000)
        
        # Búsqueda que podría beneficiarse de índice compuesto
        def compound_search():
            return BienPatrimonial.objects.filter(
                estado_bien='B',
                oficina=self.oficina
            )
        
        avg_time = self.measure_query_time(compound_search)
        print(f"Búsqueda compuesta (estado + oficina): {avg_time:.4f}s promedio")
        
        # Debería ser razonablemente rápido
        self.assertLess(avg_time, 0.5)


class TransactionOptimizationTest(TransactionTestCase):
    """Pruebas de optimización de transacciones"""
    
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
    
    def test_bulk_create_vs_individual_creates(self):
        """Comparar rendimiento de bulk_create vs creaciones individuales"""
        # Datos de prueba
        bienes_data = []
        for i in range(100):
            bienes_data.append({
                'codigo_patrimonial': f'PAT-BULK-{i:03d}',
                'catalogo': self.catalogo,
                'oficina': self.oficina,
                'estado_bien': 'B',
                'created_by': self.user
            })
        
        # Creaciones individuales
        start_time = time.time()
        for data in bienes_data:
            BienPatrimonial.objects.create(**data)
        individual_time = time.time() - start_time
        
        # Limpiar datos
        BienPatrimonial.objects.filter(codigo_patrimonial__startswith='PAT-BULK-').delete()
        
        # Bulk create
        bienes_objects = [BienPatrimonial(**data) for data in bienes_data]
        start_time = time.time()
        BienPatrimonial.objects.bulk_create(bienes_objects)
        bulk_time = time.time() - start_time
        
        print(f"Creaciones individuales: {individual_time:.4f}s")
        print(f"Bulk create: {bulk_time:.4f}s")
        print(f"Mejora: {individual_time/bulk_time:.2f}x más rápido")
        
        # Bulk create debería ser significativamente más rápido
        self.assertLess(bulk_time, individual_time)
        self.assertGreater(individual_time / bulk_time, 2)  # Al menos 2x más rápido
    
    def test_transaction_atomic_performance(self):
        """Prueba rendimiento con transacciones atómicas"""
        # Sin transacción explícita
        start_time = time.time()
        for i in range(50):
            BienPatrimonial.objects.create(
                codigo_patrimonial=f'PAT-NO-TX-{i:03d}',
                catalogo=self.catalogo,
                oficina=self.oficina,
                estado_bien='B',
                created_by=self.user
            )
        no_transaction_time = time.time() - start_time
        
        # Con transacción atómica
        start_time = time.time()
        with transaction.atomic():
            for i in range(50):
                BienPatrimonial.objects.create(
                    codigo_patrimonial=f'PAT-TX-{i:03d}',
                    catalogo=self.catalogo,
                    oficina=self.oficina,
                    estado_bien='B',
                    created_by=self.user
                )
        transaction_time = time.time() - start_time
        
        print(f"Sin transacción explícita: {no_transaction_time:.4f}s")
        print(f"Con transaction.atomic(): {transaction_time:.4f}s")
        
        # La transacción atómica debería ser más rápida o similar
        # (Django ya maneja transacciones automáticamente)
        self.assertLessEqual(transaction_time, no_transaction_time * 1.5)
    
    def test_bulk_update_performance(self):
        """Prueba rendimiento de bulk_update"""
        # Crear datos de prueba
        bienes = []
        for i in range(100):
            bienes.append(BienPatrimonial(
                codigo_patrimonial=f'PAT-UPDATE-{i:03d}',
                catalogo=self.catalogo,
                oficina=self.oficina,
                estado_bien='B',
                marca='MARCA_ORIGINAL',
                created_by=self.user
            ))
        
        BienPatrimonial.objects.bulk_create(bienes)
        
        # Actualizaciones individuales
        bienes_queryset = BienPatrimonial.objects.filter(codigo_patrimonial__startswith='PAT-UPDATE-')
        
        start_time = time.time()
        for bien in bienes_queryset:
            bien.marca = 'MARCA_INDIVIDUAL'
            bien.save()
        individual_update_time = time.time() - start_time
        
        # Restaurar datos
        bienes_queryset.update(marca='MARCA_ORIGINAL')
        
        # Bulk update
        start_time = time.time()
        bienes_queryset.update(marca='MARCA_BULK')
        bulk_update_time = time.time() - start_time
        
        print(f"Actualizaciones individuales: {individual_update_time:.4f}s")
        print(f"Bulk update: {bulk_update_time:.4f}s")
        print(f"Mejora: {individual_update_time/bulk_update_time:.2f}x más rápido")
        
        # Bulk update debería ser mucho más rápido
        self.assertLess(bulk_update_time, individual_update_time)
        self.assertGreater(individual_update_time / bulk_update_time, 5)  # Al menos 5x más rápido


class CacheOptimizationTest(TestCase):
    """Pruebas de optimización con caché"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Crear datos que podrían beneficiarse de caché
        for i in range(10):
            Catalogo.objects.create(
                codigo=f'0422000{i}',
                denominacion=f'BIEN {i}',
                grupo='04-AGRÍCOLA Y PESQUERO',
                clase='22-EQUIPO',
                resolucion='R.D. 001-2024',
                estado='ACTIVO'
            )
    
    @override_settings(CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'test-cache',
        }
    })
    def test_queryset_caching_pattern(self):
        """Prueba patrón de caché para QuerySets"""
        from django.core.cache import cache
        
        cache_key = 'catalogo_activos'
        
        # Primera consulta (sin caché)
        start_time = time.time()
        cached_data = cache.get(cache_key)
        if cached_data is None:
            catalogos = list(Catalogo.objects.filter(estado='ACTIVO').values(
                'codigo', 'denominacion'
            ))
            cache.set(cache_key, catalogos, 300)  # 5 minutos
        else:
            catalogos = cached_data
        first_query_time = time.time() - start_time
        
        # Segunda consulta (con caché)
        start_time = time.time()
        cached_data = cache.get(cache_key)
        if cached_data is None:
            catalogos = list(Catalogo.objects.filter(estado='ACTIVO').values(
                'codigo', 'denominacion'
            ))
            cache.set(cache_key, catalogos, 300)
        else:
            catalogos = cached_data
        second_query_time = time.time() - start_time
        
        print(f"Primera consulta (sin caché): {first_query_time:.6f}s")
        print(f"Segunda consulta (con caché): {second_query_time:.6f}s")
        
        # La segunda consulta debería ser más rápida
        self.assertLess(second_query_time, first_query_time)
        self.assertEqual(len(catalogos), 10)
    
    def test_expensive_calculation_caching(self):
        """Prueba caché para cálculos costosos"""
        from django.core.cache import cache
        
        def expensive_calculation():
            """Simular cálculo costoso"""
            time.sleep(0.1)  # Simular procesamiento
            return sum(range(1000))
        
        cache_key = 'expensive_calc_result'
        
        # Primera ejecución (sin caché)
        start_time = time.time()
        result = cache.get(cache_key)
        if result is None:
            result = expensive_calculation()
            cache.set(cache_key, result, 60)
        first_time = time.time() - start_time
        
        # Segunda ejecución (con caché)
        start_time = time.time()
        result = cache.get(cache_key)
        if result is None:
            result = expensive_calculation()
            cache.set(cache_key, result, 60)
        second_time = time.time() - start_time
        
        print(f"Primera ejecución: {first_time:.4f}s")
        print(f"Segunda ejecución: {second_time:.4f}s")
        
        # La segunda ejecución debería ser mucho más rápida
        self.assertLess(second_time, first_time)
        self.assertLess(second_time, 0.01)  # Debería ser casi instantánea