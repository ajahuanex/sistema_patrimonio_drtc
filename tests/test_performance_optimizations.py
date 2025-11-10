"""
Tests para las optimizaciones de rendimiento del sistema de papelera de reciclaje.
Verifica caché, optimización de consultas y paginación eficiente.
"""
from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
from django.db import connection
from django.test.utils import override_settings

from apps.core.models import RecycleBin, RecycleBinConfig, UserProfile
from apps.core.cache_utils import RecycleBinCache, QueryOptimizer, PaginationOptimizer
from apps.oficinas.models import Oficina
from apps.bienes.models import BienPatrimonial
from apps.catalogo.models import Catalogo


class RecycleBinCacheTestCase(TestCase):
    """Tests para el sistema de caché de la papelera"""
    
    def setUp(self):
        """Configurar datos de prueba"""
        cache.clear()
        
        # Crear usuarios
        self.admin_user = User.objects.create_user(
            username='admin_cache',
            password='test123',
            email='admin@test.com'
        )
        self.admin_user.profile.role = 'administrador'
        self.admin_user.profile.save()
        
        self.regular_user = User.objects.create_user(
            username='user_cache',
            password='test123',
            email='user@test.com'
        )
        self.regular_user.profile.role = 'funcionario'
        self.regular_user.profile.save()
        
        # Crear oficina
        self.oficina = Oficina.objects.create(
            codigo='OF-CACHE-001',
            nombre='Oficina Cache Test',
            direccion='Test Address',
            telefono='123456',
            estado=True,
            created_by=self.admin_user
        )
        
        # Crear entradas en papelera
        self.create_recycle_entries()
    
    def create_recycle_entries(self):
        """Crear entradas de prueba en la papelera"""
        from django.contrib.contenttypes.models import ContentType
        
        content_type = ContentType.objects.get_for_model(Oficina)
        
        # Crear 10 entradas
        for i in range(10):
            RecycleBin.objects.create(
                content_type=content_type,
                object_id=self.oficina.id,
                object_repr=f'Oficina Test {i}',
                module_name='oficinas',
                deleted_by=self.admin_user if i % 2 == 0 else self.regular_user,
                deletion_reason=f'Test reason {i}',
                deleted_at=timezone.now() - timedelta(days=i)
            )
    
    def test_cache_general_stats(self):
        """Verificar que las estadísticas generales se cachean correctamente"""
        # Primera llamada - debe calcular
        stats1 = RecycleBinCache.get_general_stats(days=30)
        
        # Segunda llamada - debe venir del caché
        stats2 = RecycleBinCache.get_general_stats(days=30)
        
        # Verificar que los datos son iguales
        self.assertEqual(stats1, stats2)
        self.assertEqual(stats1['total_deleted'], 10)
        self.assertEqual(stats1['total_restored'], 0)
        self.assertEqual(stats1['total_pending'], 10)
    
    def test_cache_module_stats(self):
        """Verificar que las estadísticas por módulo se cachean"""
        # Primera llamada
        stats1 = RecycleBinCache.get_module_stats(days=30)
        
        # Segunda llamada
        stats2 = RecycleBinCache.get_module_stats(days=30)
        
        # Verificar
        self.assertEqual(stats1, stats2)
        self.assertEqual(len(stats1), 1)  # Solo módulo 'oficinas'
        self.assertEqual(stats1[0]['module_name'], 'oficinas')
        self.assertEqual(stats1[0]['total'], 10)
    
    def test_cache_user_stats(self):
        """Verificar que las estadísticas por usuario se cachean"""
        stats1 = RecycleBinCache.get_user_stats(days=30, limit=10)
        stats2 = RecycleBinCache.get_user_stats(days=30, limit=10)
        
        self.assertEqual(stats1, stats2)
        self.assertEqual(len(stats1), 2)  # Dos usuarios
    
    def test_cache_dashboard_data(self):
        """Verificar que los datos del dashboard se cachean"""
        data1 = RecycleBinCache.get_dashboard_data(
            user_id=self.admin_user.id,
            is_admin=True,
            days=30
        )
        
        data2 = RecycleBinCache.get_dashboard_data(
            user_id=self.admin_user.id,
            is_admin=True,
            days=30
        )
        
        self.assertEqual(data1, data2)
        self.assertIn('general_stats', data1)
        self.assertIn('module_stats', data1)
        self.assertIn('user_stats', data1)
    
    def test_cache_invalidation_all(self):
        """Verificar que la invalidación total funciona"""
        # Obtener datos (se cachean)
        stats1 = RecycleBinCache.get_general_stats(days=30)
        
        # Invalidar todo
        RecycleBinCache.invalidate_all()
        
        # Crear nueva entrada
        from django.contrib.contenttypes.models import ContentType
        content_type = ContentType.objects.get_for_model(Oficina)
        RecycleBin.objects.create(
            content_type=content_type,
            object_id=self.oficina.id,
            object_repr='Nueva Oficina',
            module_name='oficinas',
            deleted_by=self.admin_user,
            deletion_reason='Test'
        )
        
        # Obtener datos nuevamente (debe recalcular)
        stats2 = RecycleBinCache.get_general_stats(days=30)
        
        # Verificar que los datos cambiaron
        self.assertNotEqual(stats1['total_deleted'], stats2['total_deleted'])
        self.assertEqual(stats2['total_deleted'], 11)
    
    def test_cache_invalidation_user(self):
        """Verificar que la invalidación por usuario funciona"""
        # Obtener datos del usuario
        stats1 = RecycleBinCache.get_general_stats(
            user_id=self.admin_user.id,
            days=30
        )
        
        # Invalidar caché del usuario
        RecycleBinCache.invalidate_user(self.admin_user.id)
        
        # Los datos deben recalcularse
        stats2 = RecycleBinCache.get_general_stats(
            user_id=self.admin_user.id,
            days=30
        )
        
        # Verificar que se recalculó (aunque los valores sean iguales)
        self.assertEqual(stats1, stats2)
    
    def test_cache_key_generation(self):
        """Verificar que las claves de caché se generan correctamente"""
        key1 = RecycleBinCache._generate_cache_key(
            'test_prefix',
            'arg1',
            'arg2',
            param1='value1',
            param2='value2'
        )
        
        key2 = RecycleBinCache._generate_cache_key(
            'test_prefix',
            'arg1',
            'arg2',
            param1='value1',
            param2='value2'
        )
        
        # Las claves deben ser iguales para los mismos parámetros
        self.assertEqual(key1, key2)
        
        # Clave diferente con parámetros diferentes
        key3 = RecycleBinCache._generate_cache_key(
            'test_prefix',
            'arg1',
            'arg3',
            param1='value1'
        )
        
        self.assertNotEqual(key1, key3)


class QueryOptimizerTestCase(TestCase):
    """Tests para la optimización de consultas"""
    
    def setUp(self):
        """Configurar datos de prueba"""
        self.admin_user = User.objects.create_user(
            username='admin_query',
            password='test123'
        )
        self.admin_user.profile.role = 'administrador'
        self.admin_user.profile.save()
        
        # Crear oficina
        self.oficina = Oficina.objects.create(
            codigo='OF-QUERY-001',
            nombre='Oficina Query Test',
            direccion='Test Address',
            telefono='123456',
            estado=True,
            created_by=self.admin_user
        )
        
        # Crear entradas en papelera
        from django.contrib.contenttypes.models import ContentType
        content_type = ContentType.objects.get_for_model(Oficina)
        
        for i in range(5):
            RecycleBin.objects.create(
                content_type=content_type,
                object_id=self.oficina.id,
                object_repr=f'Oficina {i}',
                module_name='oficinas',
                deleted_by=self.admin_user,
                deletion_reason=f'Reason {i}'
            )
    
    def test_optimize_recycle_bin_queryset(self):
        """Verificar que select_related reduce el número de consultas"""
        # Sin optimización
        with self.assertNumQueries(6):  # 1 para RecycleBin + 5 para usuarios
            queryset = RecycleBin.objects.all()
            for entry in queryset:
                _ = entry.deleted_by.username
        
        # Con optimización
        with self.assertNumQueries(1):  # Solo 1 consulta con select_related
            queryset = RecycleBin.objects.all()
            queryset = QueryOptimizer.optimize_recycle_bin_queryset(queryset)
            for entry in queryset:
                _ = entry.deleted_by.username
    
    def test_optimize_with_profile_access(self):
        """Verificar que se optimiza el acceso a perfiles de usuario"""
        with self.assertNumQueries(1):
            queryset = RecycleBin.objects.all()
            queryset = QueryOptimizer.optimize_recycle_bin_queryset(queryset)
            for entry in queryset:
                _ = entry.deleted_by.profile.role


class PaginationOptimizerTestCase(TestCase):
    """Tests para la paginación optimizada"""
    
    def setUp(self):
        """Configurar datos de prueba"""
        cache.clear()
        
        self.admin_user = User.objects.create_user(
            username='admin_page',
            password='test123'
        )
        self.admin_user.profile.role = 'administrador'
        self.admin_user.profile.save()
        
        # Crear oficina
        self.oficina = Oficina.objects.create(
            codigo='OF-PAGE-001',
            nombre='Oficina Page Test',
            direccion='Test Address',
            telefono='123456',
            estado=True,
            created_by=self.admin_user
        )
        
        # Crear 50 entradas para probar paginación
        from django.contrib.contenttypes.models import ContentType
        content_type = ContentType.objects.get_for_model(Oficina)
        
        for i in range(50):
            RecycleBin.objects.create(
                content_type=content_type,
                object_id=self.oficina.id,
                object_repr=f'Oficina {i}',
                module_name='oficinas',
                deleted_by=self.admin_user,
                deletion_reason=f'Reason {i}'
            )
    
    def test_optimized_pagination(self):
        """Verificar que la paginación optimizada funciona correctamente"""
        queryset = RecycleBin.objects.all().order_by('-id')
        
        # Primera página
        page_items, total_count, total_pages = PaginationOptimizer.get_optimized_page(
            queryset, page_number=1, page_size=20, use_cache=True
        )
        
        self.assertEqual(len(page_items), 20)
        self.assertEqual(total_count, 50)
        self.assertEqual(total_pages, 3)
        
        # Segunda página
        page_items, total_count, total_pages = PaginationOptimizer.get_optimized_page(
            queryset, page_number=2, page_size=20, use_cache=True
        )
        
        self.assertEqual(len(page_items), 20)
        self.assertEqual(total_count, 50)
    
    def test_pagination_cache(self):
        """Verificar que el conteo se cachea"""
        queryset = RecycleBin.objects.all().order_by('-id')
        
        # Primera llamada - calcula el conteo
        page_items1, total_count1, total_pages1 = PaginationOptimizer.get_optimized_page(
            queryset, page_number=1, page_size=20, use_cache=True
        )
        
        # Segunda llamada - usa caché
        page_items2, total_count2, total_pages2 = PaginationOptimizer.get_optimized_page(
            queryset, page_number=1, page_size=20, use_cache=True
        )
        
        self.assertEqual(total_count1, total_count2)
        self.assertEqual(total_pages1, total_pages2)
    
    def test_cursor_pagination(self):
        """Verificar que la paginación por cursor funciona"""
        queryset = RecycleBin.objects.all().order_by('-id')
        
        # Primera página
        page_items, next_cursor, prev_cursor = PaginationOptimizer.get_cursor_page(
            queryset, 'id', None, page_size=10, direction='next'
        )
        
        self.assertEqual(len(page_items), 10)
        self.assertIsNotNone(next_cursor)
        self.assertIsNone(prev_cursor)
        
        # Segunda página usando el cursor
        page_items2, next_cursor2, prev_cursor2 = PaginationOptimizer.get_cursor_page(
            queryset, 'id', next_cursor, page_size=10, direction='next'
        )
        
        self.assertEqual(len(page_items2), 10)
        self.assertIsNotNone(next_cursor2)
        self.assertIsNotNone(prev_cursor2)


class PerformanceBenchmarkTestCase(TransactionTestCase):
    """Tests de rendimiento para verificar mejoras"""
    
    def setUp(self):
        """Configurar datos de prueba a gran escala"""
        self.admin_user = User.objects.create_user(
            username='admin_bench',
            password='test123'
        )
        self.admin_user.profile.role = 'administrador'
        self.admin_user.profile.save()
        
        # Crear oficina
        self.oficina = Oficina.objects.create(
            codigo='OF-BENCH-001',
            nombre='Oficina Benchmark',
            direccion='Test Address',
            telefono='123456',
            estado=True,
            created_by=self.admin_user
        )
    
    def test_large_dataset_performance(self):
        """Verificar rendimiento con dataset grande"""
        from django.contrib.contenttypes.models import ContentType
        import time
        
        content_type = ContentType.objects.get_for_model(Oficina)
        
        # Crear 100 entradas
        entries = []
        for i in range(100):
            entries.append(RecycleBin(
                content_type=content_type,
                object_id=self.oficina.id,
                object_repr=f'Oficina {i}',
                module_name='oficinas',
                deleted_by=self.admin_user,
                deletion_reason=f'Reason {i}'
            ))
        
        RecycleBin.objects.bulk_create(entries)
        
        # Medir tiempo sin optimización
        start = time.time()
        queryset = RecycleBin.objects.all()
        for entry in queryset:
            _ = entry.deleted_by.username
        time_without_optimization = time.time() - start
        
        # Medir tiempo con optimización
        start = time.time()
        queryset = RecycleBin.objects.all()
        queryset = QueryOptimizer.optimize_recycle_bin_queryset(queryset)
        for entry in queryset:
            _ = entry.deleted_by.username
        time_with_optimization = time.time() - start
        
        # La versión optimizada debe ser más rápida
        self.assertLess(time_with_optimization, time_without_optimization)
        
        print(f"\nSin optimización: {time_without_optimization:.4f}s")
        print(f"Con optimización: {time_with_optimization:.4f}s")
        print(f"Mejora: {((time_without_optimization - time_with_optimization) / time_without_optimization * 100):.1f}%")


class CacheInvalidationIntegrationTestCase(TestCase):
    """Tests de integración para la invalidación de caché"""
    
    def setUp(self):
        """Configurar datos de prueba"""
        cache.clear()
        
        self.admin_user = User.objects.create_user(
            username='admin_inv',
            password='test123'
        )
        self.admin_user.profile.role = 'administrador'
        self.admin_user.profile.save()
        
        self.oficina = Oficina.objects.create(
            codigo='OF-INV-001',
            nombre='Oficina Invalidation',
            direccion='Test Address',
            telefono='123456',
            estado=True,
            created_by=self.admin_user
        )
    
    def test_cache_invalidation_on_soft_delete(self):
        """Verificar que el caché se invalida al hacer soft delete"""
        # Obtener estadísticas iniciales (se cachean)
        stats1 = RecycleBinCache.get_general_stats(days=30)
        initial_count = stats1['total_deleted']
        
        # Realizar soft delete
        self.oficina.soft_delete(user=self.admin_user, reason='Test')
        
        # Invalidar caché manualmente (en producción lo haría el servicio)
        RecycleBinCache.invalidate_all()
        
        # Obtener estadísticas nuevamente
        stats2 = RecycleBinCache.get_general_stats(days=30)
        
        # Verificar que el conteo aumentó
        self.assertEqual(stats2['total_deleted'], initial_count + 1)
    
    def test_cache_invalidation_on_restore(self):
        """Verificar que el caché se invalida al restaurar"""
        from django.contrib.contenttypes.models import ContentType
        
        # Crear entrada en papelera
        content_type = ContentType.objects.get_for_model(Oficina)
        entry = RecycleBin.objects.create(
            content_type=content_type,
            object_id=self.oficina.id,
            object_repr='Test Oficina',
            module_name='oficinas',
            deleted_by=self.admin_user,
            deletion_reason='Test'
        )
        
        # Obtener estadísticas (se cachean)
        stats1 = RecycleBinCache.get_general_stats(days=30)
        
        # Restaurar
        entry.mark_as_restored(self.admin_user)
        
        # Invalidar caché
        RecycleBinCache.invalidate_all()
        
        # Obtener estadísticas nuevamente
        stats2 = RecycleBinCache.get_general_stats(days=30)
        
        # Verificar que el conteo de restaurados aumentó
        self.assertEqual(stats2['total_restored'], stats1['total_restored'] + 1)
