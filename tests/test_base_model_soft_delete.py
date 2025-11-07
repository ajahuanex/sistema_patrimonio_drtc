"""
Tests para verificar que BaseModel funciona correctamente con SoftDeleteMixin
"""
from django.test import TestCase
from django.contrib.auth.models import User
from apps.oficinas.models import Oficina
from apps.bienes.models import BienPatrimonial
from apps.catalogo.models import Catalogo


class BaseModelSoftDeleteTestCase(TestCase):
    """Tests para verificar integración de SoftDeleteMixin con BaseModel"""
    
    def setUp(self):
        """Configuración inicial"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Crear oficina
        self.oficina = Oficina.objects.create(
            nombre='Oficina Test',
            codigo='TEST001',
            responsable='Responsable Test',
            created_by=self.user
        )
        
        # Crear catálogo
        self.catalogo = Catalogo.objects.create(
            codigo='12345678',
            denominacion='Computadora Test',
            grupo='04 AGRICOLA Y PESQUERO',
            clase='22 EQUIPO',
            resolucion='011-2019/SBN',
            created_by=self.user
        )
    
    def test_oficina_inherits_soft_delete(self):
        """Test que Oficina hereda correctamente funcionalidad de soft delete"""
        # Verificar que tiene los campos de soft delete
        self.assertTrue(hasattr(self.oficina, 'deleted_at'))
        self.assertTrue(hasattr(self.oficina, 'deleted_by'))
        self.assertTrue(hasattr(self.oficina, 'deletion_reason'))
        
        # Verificar que tiene los métodos de soft delete
        self.assertTrue(hasattr(self.oficina, 'soft_delete'))
        self.assertTrue(hasattr(self.oficina, 'restore'))
        self.assertTrue(hasattr(self.oficina, 'hard_delete'))
        self.assertTrue(hasattr(self.oficina, 'is_deleted'))
        
        # Verificar que tiene los managers
        self.assertTrue(hasattr(Oficina, 'objects'))
        self.assertTrue(hasattr(Oficina, 'all_objects'))
        
        # Verificar funcionalidad
        self.assertFalse(self.oficina.is_deleted)
        self.oficina.soft_delete(user=self.user, reason='Test')
        self.assertTrue(self.oficina.is_deleted)
    
    def test_catalogo_inherits_soft_delete(self):
        """Test que Catalogo hereda correctamente funcionalidad de soft delete"""
        # Verificar que tiene los campos de soft delete
        self.assertTrue(hasattr(self.catalogo, 'deleted_at'))
        self.assertTrue(hasattr(self.catalogo, 'deleted_by'))
        self.assertTrue(hasattr(self.catalogo, 'deletion_reason'))
        
        # Verificar funcionalidad
        self.assertFalse(self.catalogo.is_deleted)
        self.catalogo.soft_delete(user=self.user, reason='Test')
        self.assertTrue(self.catalogo.is_deleted)
    
    def test_bien_patrimonial_inherits_soft_delete(self):
        """Test que BienPatrimonial hereda correctamente funcionalidad de soft delete"""
        # Crear bien patrimonial
        bien = BienPatrimonial.objects.create(
            codigo_patrimonial='BP001',
            catalogo=self.catalogo,
            oficina=self.oficina,
            estado_bien='B',
            created_by=self.user
        )
        
        # Verificar que tiene los campos de soft delete
        self.assertTrue(hasattr(bien, 'deleted_at'))
        self.assertTrue(hasattr(bien, 'deleted_by'))
        self.assertTrue(hasattr(bien, 'deletion_reason'))
        
        # Verificar funcionalidad
        self.assertFalse(bien.is_deleted)
        bien.soft_delete(user=self.user, reason='Test')
        self.assertTrue(bien.is_deleted)
    
    def test_audit_fields_work_with_soft_delete(self):
        """Test que los campos de auditoría funcionan con soft delete"""
        # Verificar campos de auditoría iniciales
        self.assertEqual(self.oficina.created_by, self.user)
        self.assertIsNotNone(self.oficina.created_at)
        
        # Crear otro usuario para actualización
        update_user = User.objects.create_user(
            username='updateuser',
            email='update@example.com',
            password='testpass123'
        )
        
        # Actualizar oficina
        self.oficina.updated_by = update_user
        self.oficina.save()
        
        # Soft delete
        self.oficina.soft_delete(user=self.user, reason='Test deletion')
        
        # Verificar que todos los campos están presentes
        self.assertEqual(self.oficina.created_by, self.user)
        self.assertEqual(self.oficina.updated_by, update_user)
        self.assertEqual(self.oficina.deleted_by, self.user)
        self.assertIsNotNone(self.oficina.created_at)
        self.assertIsNotNone(self.oficina.updated_at)
        self.assertIsNotNone(self.oficina.deleted_at)
    
    def test_managers_work_across_all_models(self):
        """Test que los managers funcionan en todos los modelos que heredan de BaseModel"""
        # Crear objetos adicionales
        oficina2 = Oficina.objects.create(
            nombre='Oficina 2',
            codigo='TEST002',
            responsable='Responsable 2',
            created_by=self.user
        )
        
        catalogo2 = Catalogo.objects.create(
            codigo='87654321',
            denominacion='Impresora Test',
            grupo='04 AGRICOLA Y PESQUERO',
            clase='22 EQUIPO',
            resolucion='012-2019/SBN',
            created_by=self.user
        )
        
        # Eliminar algunos objetos
        self.oficina.soft_delete(user=self.user)
        self.catalogo.soft_delete(user=self.user)
        
        # Verificar que los managers funcionan correctamente
        # Oficinas
        self.assertEqual(Oficina.objects.count(), 1)  # Solo oficina2
        self.assertEqual(Oficina.objects.deleted_only().count(), 1)  # Solo oficina eliminada
        self.assertEqual(Oficina.objects.with_deleted().count(), 2)  # Ambas
        
        # Catálogos
        self.assertEqual(Catalogo.objects.count(), 1)  # Solo catalogo2
        self.assertEqual(Catalogo.objects.deleted_only().count(), 1)  # Solo catalogo eliminado
        self.assertEqual(Catalogo.objects.with_deleted().count(), 2)  # Ambos
    
    def test_restore_updates_audit_fields(self):
        """Test que restore actualiza correctamente los campos de auditoría"""
        # Crear usuario para restauración
        restore_user = User.objects.create_user(
            username='restoreuser',
            email='restore@example.com',
            password='testpass123'
        )
        
        # Soft delete
        self.oficina.soft_delete(user=self.user, reason='Test deletion')
        original_updated_at = self.oficina.updated_at
        
        # Esperar un momento para que el timestamp sea diferente
        import time
        time.sleep(0.1)
        
        # Restaurar
        self.oficina.restore(user=restore_user)
        
        # Verificar que updated_by se actualizó
        self.assertEqual(self.oficina.updated_by, restore_user)
        # Verificar que updated_at se actualizó
        self.assertGreater(self.oficina.updated_at, original_updated_at)
        
        # Verificar que los campos de eliminación se limpiaron
        self.assertIsNone(self.oficina.deleted_at)
        self.assertIsNone(self.oficina.deleted_by)
        self.assertEqual(self.oficina.deletion_reason, '')
    
    def test_multiple_inheritance_works_correctly(self):
        """Test que la herencia múltiple funciona correctamente"""
        # Verificar que BaseModel hereda de SoftDeleteMixin y models.Model
        from apps.core.models import BaseModel, SoftDeleteMixin
        
        # Verificar que BaseModel es subclase de SoftDeleteMixin
        self.assertTrue(issubclass(BaseModel, SoftDeleteMixin))
        
        # Verificar que los modelos concretos heredan de BaseModel
        self.assertTrue(issubclass(Oficina, BaseModel))
        self.assertTrue(issubclass(Catalogo, BaseModel))
        self.assertTrue(issubclass(BienPatrimonial, BaseModel))
        
        # Verificar que tienen acceso a todos los métodos
        for model_class in [Oficina, Catalogo, BienPatrimonial]:
            # Verificar managers
            self.assertTrue(hasattr(model_class, 'objects'))
            self.assertTrue(hasattr(model_class, 'all_objects'))
            
            # Verificar que objects es instancia de SoftDeleteManager
            from apps.core.models import SoftDeleteManager
            self.assertIsInstance(model_class.objects, SoftDeleteManager)