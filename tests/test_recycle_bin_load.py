"""
Pruebas de carga para operaciones masivas del sistema de papelera
"""
import time
import statistics
from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from apps.core.models import RecycleBin, RecycleBinConfig, DeletionAuditLog
from apps.core.services import RecycleBinService
from apps.oficinas.models import Oficina
from apps.bienes.models import BienPatrimonial
from apps.catalogo.models import Catalogo


class RecycleBinBulkOperationsLoadTest(TransactionTestCase):
    """Pruebas de carga para operaciones masivas"""
    
    def setUp(self):
        """Configurar datos de prueba"""
        self.admin_user = User.objects.create_user(
            username='admin',
            password='admin123',
            is_staff=True
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
        
        RecycleBinConfig.objects.create(
            module_name='bienes',
            retention_days=30,
            auto_delete_enabled=True
        )
        
        self.service = RecycleBinService()
    
    def test_bulk_soft_delete_performance(self):
        """Prueba rendimiento de eliminación masiva"""
        # Crear 1000 bienes
        bienes = []
        for i in range(1000):
            bienes.append(BienPatrimonial(
                codigo_patrimonial=f'PAT-BULK-{i:06d}',
                catalogo=self.catalogo,
                oficina=self.oficina,
                estado_bien='B',
                created_by=self.admin_user
            ))
        
        BienPatrimonial.objects.bulk_create(bienes)
        
        # Medir tiempo de eliminación masiva
        start_time = time.time()
        
        for bien in BienPatrimonial.objects.all():
            self.service.soft_delete_object(bien, self.admin_user, 'Bulk test')
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        print(f"Eliminación masiva de 1000 bienes: {elapsed_time:.2f}s")
        print(f"Promedio por bien: {elapsed_time/1000:.4f}s")
        
        # Verificar que todos están en papelera
        recycle_count = RecycleBin.objects.filter(
            content_type__model='bienpatrimonial'
        ).count()
        self.assertEqual(recycle_count, 1000)
        
        # Debería completarse en tiempo razonable (menos de 60 segundos)
        self.assertLess(elapsed_time, 60.0)

    def test_bulk_restore_performance(self):
        """Prueba rendimiento de restauración masiva"""
        # Crear y eliminar 500 bienes
        bienes = []
        for i in range(500):
            bien = BienPatrimonial.objects.create(
                codigo_patrimonial=f'PAT-RESTORE-{i:06d}',
                catalogo=self.catalogo,
                oficina=self.oficina,
                estado_bien='B',
                created_by=self.admin_user
            )
            self.service.soft_delete_object(bien, self.admin_user, 'Test')
            bienes.append(bien)
        
        # Medir tiempo de restauración masiva
        start_time = time.time()
        
        for bien in bienes:
            self.service.restore_object(bien, self.admin_user)
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        print(f"Restauración masiva de 500 bienes: {elapsed_time:.2f}s")
        print(f"Promedio por bien: {elapsed_time/500:.4f}s")
        
        # Verificar que todos se restauraron
        restored_count = BienPatrimonial.objects.filter(deleted_at__isnull=True).count()
        self.assertEqual(restored_count, 500)
        
        # Debería completarse en tiempo razonable
        self.assertLess(elapsed_time, 45.0)
    
    def test_auto_cleanup_large_dataset_performance(self):
        """Prueba rendimiento de limpieza automática con dataset grande"""
        # Crear 2000 bienes eliminados con fechas antiguas
        bienes = []
        for i in range(2000):
            bien = BienPatrimonial.objects.create(
                codigo_patrimonial=f'PAT-CLEANUP-{i:06d}',
                catalogo=self.catalogo,
                oficina=self.oficina,
                estado_bien='B',
                created_by=self.admin_user
            )
            self.service.soft_delete_object(bien, self.admin_user, 'Test')
            bienes.append(bien)
        
        # Modificar fechas para simular antigüedad
        RecycleBin.objects.filter(
            content_type__model='bienpatrimonial'
        ).update(
            auto_delete_at=timezone.now() - timedelta(days=1)
        )
        
        # Medir tiempo de limpieza
        start_time = time.time()
        
        result = self.service.auto_cleanup()
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        print(f"Limpieza automática de 2000 bienes: {elapsed_time:.2f}s")
        print(f"Bienes eliminados: {result['deleted_count']}")
        
        # Verificar que se eliminaron
        self.assertEqual(result['deleted_count'], 2000)
        
        # Debería completarse en tiempo razonable
        self.assertLess(elapsed_time, 120.0)
    
    def test_recycle_bin_list_pagination_performance(self):
        """Prueba rendimiento de paginación con muchos elementos"""
        # Crear 5000 bienes eliminados
        for i in range(5000):
            bien = BienPatrimonial.objects.create(
                codigo_patrimonial=f'PAT-PAGE-{i:06d}',
                catalogo=self.catalogo,
                oficina=self.oficina,
                estado_bien='B',
                created_by=self.admin_user
            )
            self.service.soft_delete_object(bien, self.admin_user, 'Test')
        
        # Medir tiempo de consulta paginada
        times = []
        
        for page in [1, 50, 100, 250]:
            start_time = time.time()
            
            # Simular consulta paginada
            entries = RecycleBin.objects.select_related(
                'content_type', 'deleted_by'
            ).filter(
                permanently_deleted_at__isnull=True
            ).order_by('-deleted_at')[(page-1)*20:page*20]
            
            list(entries)  # Forzar evaluación
            
            end_time = time.time()
            times.append(end_time - start_time)
        
        avg_time = statistics.mean(times)
        max_time = max(times)
        
        print(f"Paginación con 5000 elementos:")
        print(f"  Tiempo promedio: {avg_time:.4f}s")
        print(f"  Tiempo máximo: {max_time:.4f}s")
        
        # Todas las páginas deberían cargar rápido
        self.assertLess(avg_time, 1.0)
        self.assertLess(max_time, 2.0)

    def test_audit_log_creation_performance(self):
        """Prueba rendimiento de creación de logs de auditoría"""
        # Crear 1000 bienes y eliminarlos (genera logs)
        start_time = time.time()
        
        for i in range(1000):
            bien = BienPatrimonial.objects.create(
                codigo_patrimonial=f'PAT-AUDIT-{i:06d}',
                catalogo=self.catalogo,
                oficina=self.oficina,
                estado_bien='B',
                created_by=self.admin_user
            )
            self.service.soft_delete_object(bien, self.admin_user, 'Audit test')
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        print(f"Creación de 1000 logs de auditoría: {elapsed_time:.2f}s")
        
        # Verificar que se crearon los logs
        audit_count = DeletionAuditLog.objects.filter(
            action='soft_delete'
        ).count()
        self.assertEqual(audit_count, 1000)
        
        # Debería completarse en tiempo razonable
        self.assertLess(elapsed_time, 60.0)
    
    def test_concurrent_operations_stress(self):
        """Prueba de estrés con operaciones concurrentes"""
        import threading
        
        # Crear bienes para operaciones concurrentes
        bienes = []
        for i in range(100):
            bien = BienPatrimonial.objects.create(
                codigo_patrimonial=f'PAT-CONCURRENT-{i:06d}',
                catalogo=self.catalogo,
                oficina=self.oficina,
                estado_bien='B',
                created_by=self.admin_user
            )
            bienes.append(bien)
        
        results = {'success': 0, 'errors': 0}
        lock = threading.Lock()
        
        def delete_bien(bien):
            try:
                self.service.soft_delete_object(bien, self.admin_user, 'Concurrent test')
                with lock:
                    results['success'] += 1
            except Exception as e:
                with lock:
                    results['errors'] += 1
                print(f"Error en thread: {str(e)}")
        
        # Ejecutar eliminaciones concurrentes
        threads = []
        start_time = time.time()
        
        for bien in bienes:
            thread = threading.Thread(target=delete_bien, args=(bien,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        print(f"Operaciones concurrentes:")
        print(f"  Tiempo total: {elapsed_time:.2f}s")
        print(f"  Éxitos: {results['success']}")
        print(f"  Errores: {results['errors']}")
        
        # La mayoría deberían completarse exitosamente
        self.assertGreater(results['success'], 90)
    
    def test_search_performance_large_dataset(self):
        """Prueba rendimiento de búsqueda en dataset grande"""
        # Crear 3000 bienes eliminados con diferentes características
        for i in range(3000):
            bien = BienPatrimonial.objects.create(
                codigo_patrimonial=f'PAT-SEARCH-{i:06d}',
                catalogo=self.catalogo,
                oficina=self.oficina,
                estado_bien='B',
                marca=f'MARCA {i % 50}',
                modelo=f'MODELO {i % 100}',
                created_by=self.admin_user
            )
            self.service.soft_delete_object(bien, self.admin_user, 'Test')
        
        # Medir diferentes tipos de búsqueda
        search_tests = [
            ('Búsqueda por código exacto', {'object_repr__icontains': 'PAT-SEARCH-001500'}),
            ('Búsqueda por módulo', {'content_type__model': 'bienpatrimonial'}),
            ('Búsqueda por usuario', {'deleted_by': self.admin_user}),
            ('Búsqueda por rango de fechas', {
                'deleted_at__gte': timezone.now() - timedelta(hours=1)
            }),
        ]
        
        for search_name, filters in search_tests:
            start_time = time.time()
            
            results = RecycleBin.objects.filter(**filters)
            count = results.count()
            
            end_time = time.time()
            elapsed_time = end_time - start_time
            
            print(f"{search_name}: {elapsed_time:.4f}s ({count} resultados)")
            
            # Todas las búsquedas deberían ser rápidas
            self.assertLess(elapsed_time, 2.0)


class RecycleBinMemoryUsageTest(TestCase):
    """Pruebas de uso de memoria"""
    
    def setUp(self):
        """Configurar datos de prueba"""
        self.admin_user = User.objects.create_user(
            username='admin',
            password='admin123'
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
        
        self.service = RecycleBinService()
    
    def test_iterator_memory_efficiency(self):
        """Prueba eficiencia de memoria usando iteradores"""
        # Crear 5000 bienes eliminados
        for i in range(5000):
            bien = BienPatrimonial.objects.create(
                codigo_patrimonial=f'PAT-MEM-{i:06d}',
                catalogo=self.catalogo,
                oficina=self.oficina,
                estado_bien='B',
                created_by=self.admin_user
            )
            self.service.soft_delete_object(bien, self.admin_user, 'Test')
        
        # Procesar usando iterator (no carga todo en memoria)
        count = 0
        for entry in RecycleBin.objects.iterator(chunk_size=100):
            count += 1
            if count >= 1000:  # Procesar solo algunos para la prueba
                break
        
        self.assertEqual(count, 1000)
        
        # Verificar que values() también funciona eficientemente
        values_count = RecycleBin.objects.values('id').count()
        self.assertEqual(values_count, 5000)
