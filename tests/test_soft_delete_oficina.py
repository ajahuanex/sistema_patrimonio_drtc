"""
Tests unitarios para SoftDeleteMixin usando el modelo Oficina
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from apps.oficinas.models import Oficina


class SoftDeleteOficinaTestCase(TestCase):
    """Tests para SoftDeleteMixin usando modelo Oficina"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.oficina = Oficina.objects.create(
            nombre='Oficina Test',
            codigo='TEST001',
            responsable='Responsable Test',
            created_by=self.user
        )
    
    def test_soft_delete_marks_as_deleted(self):
        """Test que soft_delete marca el objeto como eliminado"""
        # Verificar estado inicial
        self.assertFalse(self.oficina.is_deleted)
        self.assertIsNone(self.oficina.deleted_at)
        self.assertIsNone(self.oficina.deleted_by)
        
        # Realizar soft delete
        result = self.oficina.soft_delete(user=self.user, reason='Test deletion')
        
        # Verificar resultado
        self.assertTrue(result)
        self.assertTrue(self.oficina.is_deleted)
        self.assertIsNotNone(self.oficina.deleted_at)
        self.assertEqual(self.oficina.deleted_by, self.user)
        self.assertEqual(self.oficina.deletion_reason, 'Test deletion')
    
    def test_soft_delete_already_deleted_returns_false(self):
        """Test que soft_delete retorna False si ya está eliminado"""
        # Eliminar primero
        self.oficina.soft_delete(user=self.user)
        
        # Intentar eliminar de nuevo
        result = self.oficina.soft_delete(user=self.user)
        
        self.assertFalse(result)
    
    def test_restore_restores_deleted_object(self):
        """Test que restore restaura un objeto eliminado"""
        # Eliminar primero
        self.oficina.soft_delete(user=self.user, reason='Test deletion')
        self.assertTrue(self.oficina.is_deleted)
        
        # Restaurar
        result = self.oficina.restore(user=self.user)
        
        # Verificar restauración
        self.assertTrue(result)
        self.assertFalse(self.oficina.is_deleted)
        self.assertIsNone(self.oficina.deleted_at)
        self.assertIsNone(self.oficina.deleted_by)
        self.assertEqual(self.oficina.deletion_reason, '')
    
    def test_restore_non_deleted_returns_false(self):
        """Test que restore retorna False si no está eliminado"""
        result = self.oficina.restore(user=self.user)
        self.assertFalse(result)
    
    def test_is_deleted_property(self):
        """Test de la propiedad is_deleted"""
        # Inicialmente no eliminado
        self.assertFalse(self.oficina.is_deleted)
        
        # Después de soft delete
        self.oficina.soft_delete(user=self.user)
        self.assertTrue(self.oficina.is_deleted)
        
        # Después de restore
        self.oficina.restore(user=self.user)
        self.assertFalse(self.oficina.is_deleted)
    
    def test_hard_delete_removes_from_database(self):
        """Test que hard_delete elimina permanentemente"""
        obj_id = self.oficina.id
        
        # Hard delete
        self.oficina.hard_delete()
        
        # Verificar que no existe en la base de datos
        with self.assertRaises(Oficina.DoesNotExist):
            Oficina.all_objects.get(id=obj_id)
    
    def test_default_delete_uses_soft_delete(self):
        """Test que el método delete por defecto usa soft delete"""
        # Llamar delete() normal
        self.oficina.delete()
        
        # Verificar que es soft delete, no hard delete
        self.assertTrue(self.oficina.is_deleted)
        
        # Verificar que aún existe en la base de datos
        obj_from_db = Oficina.all_objects.get(id=self.oficina.id)
        self.assertTrue(obj_from_db.is_deleted)


class SoftDeleteManagerOficinaTestCase(TestCase):
    """Tests para SoftDeleteManager usando modelo Oficina"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Crear objetos de prueba
        self.active_oficina1 = Oficina.objects.create(
            nombre='Oficina Activa 1',
            codigo='ACT001',
            responsable='Responsable 1',
            created_by=self.user
        )
        self.active_oficina2 = Oficina.objects.create(
            nombre='Oficina Activa 2',
            codigo='ACT002',
            responsable='Responsable 2',
            created_by=self.user
        )
        self.deleted_oficina1 = Oficina.objects.create(
            nombre='Oficina Eliminada 1',
            codigo='DEL001',
            responsable='Responsable 3',
            created_by=self.user
        )
        self.deleted_oficina2 = Oficina.objects.create(
            nombre='Oficina Eliminada 2',
            codigo='DEL002',
            responsable='Responsable 4',
            created_by=self.user
        )
        
        # Eliminar algunos objetos
        self.deleted_oficina1.soft_delete(user=self.user)
        self.deleted_oficina2.soft_delete(user=self.user)
    
    def test_default_manager_excludes_deleted(self):
        """Test que el manager por defecto excluye eliminados"""
        active_objects = Oficina.objects.filter(
            codigo__in=['ACT001', 'ACT002', 'DEL001', 'DEL002']
        )
        
        self.assertEqual(active_objects.count(), 2)
        self.assertIn(self.active_oficina1, active_objects)
        self.assertIn(self.active_oficina2, active_objects)
        self.assertNotIn(self.deleted_oficina1, active_objects)
        self.assertNotIn(self.deleted_oficina2, active_objects)
    
    def test_deleted_only_returns_only_deleted(self):
        """Test que deleted_only retorna solo eliminados"""
        deleted_objects = Oficina.objects.deleted_only().filter(
            codigo__in=['ACT001', 'ACT002', 'DEL001', 'DEL002']
        )
        
        self.assertEqual(deleted_objects.count(), 2)
        self.assertIn(self.deleted_oficina1, deleted_objects)
        self.assertIn(self.deleted_oficina2, deleted_objects)
        self.assertNotIn(self.active_oficina1, deleted_objects)
        self.assertNotIn(self.active_oficina2, deleted_objects)
    
    def test_with_deleted_returns_all(self):
        """Test que with_deleted retorna todos los objetos"""
        all_objects = Oficina.objects.with_deleted().filter(
            codigo__in=['ACT001', 'ACT002', 'DEL001', 'DEL002']
        )
        
        self.assertEqual(all_objects.count(), 4)
        self.assertIn(self.active_oficina1, all_objects)
        self.assertIn(self.active_oficina2, all_objects)
        self.assertIn(self.deleted_oficina1, all_objects)
        self.assertIn(self.deleted_oficina2, all_objects)
    
    def test_all_objects_manager_returns_all(self):
        """Test que all_objects manager retorna todos los objetos"""
        all_objects = Oficina.all_objects.filter(
            codigo__in=['ACT001', 'ACT002', 'DEL001', 'DEL002']
        )
        
        self.assertEqual(all_objects.count(), 4)
        self.assertIn(self.active_oficina1, all_objects)
        self.assertIn(self.active_oficina2, all_objects)
        self.assertIn(self.deleted_oficina1, all_objects)
        self.assertIn(self.deleted_oficina2, all_objects)
    
    def test_filter_works_with_soft_delete(self):
        """Test que los filtros funcionan correctamente con soft delete"""
        # Filtrar por nombre en objetos activos
        active_filtered = Oficina.objects.filter(nombre__startswith='Oficina Activa')
        self.assertEqual(active_filtered.count(), 2)
        
        # Filtrar por nombre en objetos eliminados
        deleted_filtered = Oficina.objects.deleted_only().filter(nombre__startswith='Oficina Eliminada')
        self.assertEqual(deleted_filtered.count(), 2)
    
    def test_get_works_with_soft_delete(self):
        """Test que get funciona correctamente con soft delete"""
        # Get de objeto activo
        obj = Oficina.objects.get(codigo='ACT001')
        self.assertEqual(obj, self.active_oficina1)
        
        # Get de objeto eliminado debe fallar con el manager por defecto
        with self.assertRaises(Oficina.DoesNotExist):
            Oficina.objects.get(codigo='DEL001')
        
        # Pero debe funcionar con deleted_only
        deleted_obj = Oficina.objects.deleted_only().get(codigo='DEL001')
        self.assertEqual(deleted_obj, self.deleted_oficina1)
    
    def test_restore_makes_object_visible_again(self):
        """Test que restaurar hace el objeto visible de nuevo"""
        # Verificar que está eliminado
        self.assertEqual(Oficina.objects.filter(codigo='DEL001').count(), 0)
        
        # Restaurar
        self.deleted_oficina1.restore(user=self.user)
        
        # Verificar que ahora es visible
        self.assertEqual(Oficina.objects.filter(codigo='DEL001').count(), 1)
        restored_obj = Oficina.objects.get(codigo='DEL001')
        self.assertEqual(restored_obj, self.deleted_oficina1)


class OficinaDeleteOverrideTestCase(TestCase):
    """Tests para el método delete() sobrescrito en Oficina"""
    
    def setUp(self):
        """Configuración inicial"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.oficina = Oficina.objects.create(
            nombre='Oficina Test',
            codigo='TEST001',
            responsable='Responsable Test',
            created_by=self.user
        )
    
    def test_delete_with_user_parameter(self):
        """Test que delete() acepta parámetro user"""
        result = self.oficina.delete(user=self.user, reason='Test deletion')
        
        self.assertTrue(result)
        self.assertTrue(self.oficina.is_deleted)
        self.assertEqual(self.oficina.deleted_by, self.user)
        self.assertEqual(self.oficina.deletion_reason, 'Test deletion')
    
    def test_delete_without_parameters_uses_soft_delete(self):
        """Test que delete() sin parámetros usa soft delete"""
        result = self.oficina.delete()
        
        # Debe usar soft delete (retorna True/False, no tupla)
        self.assertIsInstance(result, bool)
        self.assertTrue(self.oficina.is_deleted)
    
    def test_delete_with_bienes_raises_validation_error(self):
        """Test que delete() con bienes asignados lanza ValidationError"""
        from apps.bienes.models import BienPatrimonial
        from apps.catalogo.models import Catalogo
        from django.core.exceptions import ValidationError
        
        # Crear catálogo
        catalogo = Catalogo.objects.create(
            codigo='04220001',
            denominacion='Catálogo Test',
            grupo='04 AGRICOLA Y PESQUERO',
            clase='22 EQUIPO',
            resolucion='001-2024/TEST',
            created_by=self.user
        )
        
        # Crear bien asignado a la oficina
        bien = BienPatrimonial.objects.create(
            codigo_patrimonial='BP001',
            catalogo=catalogo,
            oficina=self.oficina,
            estado_bien='B',
            created_by=self.user
        )
        
        # Intentar eliminar oficina con bienes debe fallar
        with self.assertRaises(ValidationError) as context:
            self.oficina.delete(user=self.user)
        
        # Verificar mensaje de error
        self.assertIn('bienes patrimoniales', str(context.exception).lower())
    
    def test_delete_with_deleted_bienes_succeeds(self):
        """Test que delete() con bienes eliminados (soft deleted) funciona"""
        from apps.bienes.models import BienPatrimonial
        from apps.catalogo.models import Catalogo
        
        # Crear catálogo
        catalogo = Catalogo.objects.create(
            codigo='04220002',
            denominacion='Catálogo Test 2',
            grupo='04 AGRICOLA Y PESQUERO',
            clase='22 EQUIPO',
            resolucion='001-2024/TEST',
            created_by=self.user
        )
        
        # Crear bien asignado a la oficina
        bien = BienPatrimonial.objects.create(
            codigo_patrimonial='BP001',
            catalogo=catalogo,
            oficina=self.oficina,
            estado_bien='B',
            created_by=self.user
        )
        
        # Eliminar el bien (soft delete)
        bien.soft_delete(user=self.user)
        
        # Ahora eliminar la oficina debe funcionar
        result = self.oficina.delete(user=self.user)
        
        self.assertTrue(result)
        self.assertTrue(self.oficina.is_deleted)


class OficinaPuedeEliminarseTestCase(TestCase):
    """Tests para el método puede_eliminarse() actualizado"""
    
    def setUp(self):
        """Configuración inicial"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.oficina = Oficina.objects.create(
            nombre='Oficina Test',
            codigo='TEST001',
            responsable='Responsable Test',
            created_by=self.user
        )
    
    def test_puede_eliminarse_sin_bienes(self):
        """Test que oficina sin bienes puede eliminarse"""
        self.assertTrue(self.oficina.puede_eliminarse())
    
    def test_puede_eliminarse_con_bienes_activos(self):
        """Test que oficina con bienes activos no puede eliminarse"""
        from apps.bienes.models import BienPatrimonial
        from apps.catalogo.models import Catalogo
        
        # Crear catálogo
        catalogo = Catalogo.objects.create(
            codigo='04220003',
            denominacion='Catálogo Test 3',
            grupo='04 AGRICOLA Y PESQUERO',
            clase='22 EQUIPO',
            resolucion='001-2024/TEST',
            created_by=self.user
        )
        
        # Crear bien activo
        bien = BienPatrimonial.objects.create(
            codigo_patrimonial='BP001',
            catalogo=catalogo,
            oficina=self.oficina,
            estado_bien='B',
            created_by=self.user
        )
        
        self.assertFalse(self.oficina.puede_eliminarse())
    
    def test_puede_eliminarse_con_bienes_eliminados(self):
        """Test que oficina con solo bienes eliminados puede eliminarse"""
        from apps.bienes.models import BienPatrimonial
        from apps.catalogo.models import Catalogo
        
        # Crear catálogo
        catalogo = Catalogo.objects.create(
            codigo='04220004',
            denominacion='Catálogo Test 4',
            grupo='04 AGRICOLA Y PESQUERO',
            clase='22 EQUIPO',
            resolucion='001-2024/TEST',
            created_by=self.user
        )
        
        # Crear bien y eliminarlo
        bien = BienPatrimonial.objects.create(
            codigo_patrimonial='BP001',
            catalogo=catalogo,
            oficina=self.oficina,
            estado_bien='B',
            created_by=self.user
        )
        bien.soft_delete(user=self.user)
        
        # Oficina debe poder eliminarse
        self.assertTrue(self.oficina.puede_eliminarse())
    
    def test_puede_eliminarse_con_bienes_mixtos(self):
        """Test que oficina con bienes activos y eliminados no puede eliminarse"""
        from apps.bienes.models import BienPatrimonial
        from apps.catalogo.models import Catalogo
        
        # Crear catálogo
        catalogo = Catalogo.objects.create(
            codigo='04220005',
            denominacion='Catálogo Test 5',
            grupo='04 AGRICOLA Y PESQUERO',
            clase='22 EQUIPO',
            resolucion='001-2024/TEST',
            created_by=self.user
        )
        
        # Crear bien activo
        bien_activo = BienPatrimonial.objects.create(
            codigo_patrimonial='BP001',
            catalogo=catalogo,
            oficina=self.oficina,
            estado_bien='B',
            created_by=self.user
        )
        
        # Crear bien eliminado
        bien_eliminado = BienPatrimonial.objects.create(
            codigo_patrimonial='BP002',
            catalogo=catalogo,
            oficina=self.oficina,
            estado_bien='B',
            created_by=self.user
        )
        bien_eliminado.soft_delete(user=self.user)
        
        # No debe poder eliminarse porque tiene un bien activo
        self.assertFalse(self.oficina.puede_eliminarse())


class SoftDeleteIntegrationOficinaTestCase(TestCase):
    """Tests de integración para el sistema de soft delete con Oficina"""
    
    def setUp(self):
        """Configuración inicial"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_soft_delete_with_reason_and_user(self):
        """Test de soft delete con usuario y razón"""
        oficina = Oficina.objects.create(
            nombre='Oficina Test',
            codigo='TEST001',
            responsable='Responsable Test',
            created_by=self.user
        )
        
        # Soft delete con información completa
        oficina.soft_delete(user=self.user, reason='Testing soft delete functionality')
        
        # Verificar que se guardó toda la información
        oficina.refresh_from_db()
        self.assertTrue(oficina.is_deleted)
        self.assertEqual(oficina.deleted_by, self.user)
        self.assertEqual(oficina.deletion_reason, 'Testing soft delete functionality')
        self.assertIsNotNone(oficina.deleted_at)
    
    def test_soft_delete_without_user_or_reason(self):
        """Test de soft delete sin usuario ni razón"""
        oficina = Oficina.objects.create(
            nombre='Oficina Test',
            codigo='TEST002',
            responsable='Responsable Test',
            created_by=self.user
        )
        
        # Soft delete sin información adicional
        oficina.soft_delete()
        
        # Verificar que funciona sin información adicional
        oficina.refresh_from_db()
        self.assertTrue(oficina.is_deleted)
        self.assertIsNone(oficina.deleted_by)
        self.assertEqual(oficina.deletion_reason, '')
        self.assertIsNotNone(oficina.deleted_at)
    
    def test_multiple_soft_deletes_and_restores(self):
        """Test de múltiples eliminaciones y restauraciones"""
        oficina = Oficina.objects.create(
            nombre='Oficina Test',
            codigo='TEST003',
            responsable='Responsable Test',
            created_by=self.user
        )
        
        # Ciclo de eliminación y restauración
        for i in range(3):
            # Eliminar
            oficina.soft_delete(user=self.user, reason=f'Deletion {i+1}')
            self.assertTrue(oficina.is_deleted)
            
            # Restaurar
            oficina.restore(user=self.user)
            self.assertFalse(oficina.is_deleted)
        
        # Verificar estado final
        self.assertFalse(oficina.is_deleted)
        self.assertIsNone(oficina.deleted_at)
        self.assertIsNone(oficina.deleted_by)
        self.assertEqual(oficina.deletion_reason, '')
    
    def test_updated_by_field_updated_on_restore(self):
        """Test que el campo updated_by se actualiza al restaurar"""
        oficina = Oficina.objects.create(
            nombre='Oficina Test',
            codigo='TEST004',
            responsable='Responsable Test',
            created_by=self.user
        )
        
        # Crear otro usuario para la restauración
        restore_user = User.objects.create_user(
            username='restore_user',
            email='restore@example.com',
            password='testpass123'
        )
        
        # Soft delete
        oficina.soft_delete(user=self.user, reason='Test deletion')
        
        # Restaurar con otro usuario
        oficina.restore(user=restore_user)
        
        # Verificar que updated_by se actualizó
        oficina.refresh_from_db()
        self.assertEqual(oficina.updated_by, restore_user)