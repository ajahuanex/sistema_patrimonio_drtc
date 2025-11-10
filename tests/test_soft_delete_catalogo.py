"""
Tests unitarios para SoftDeleteMixin usando el modelo Catalogo
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.catalogo.models import Catalogo
from apps.bienes.models import BienPatrimonial
from apps.oficinas.models import Oficina


class SoftDeleteCatalogoTestCase(TestCase):
    """Tests para SoftDeleteMixin usando modelo Catalogo"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.catalogo = Catalogo.objects.create(
            codigo='04220001',
            denominacion='EQUIPO DE PRUEBA',
            grupo='04 AGRICOLA Y PESQUERO',
            clase='22 EQUIPO',
            resolucion='001-2024/TEST',
            estado='ACTIVO',
            created_by=self.user
        )
    
    def test_soft_delete_marks_as_deleted(self):
        """Test que soft_delete marca el catálogo como eliminado"""
        # Verificar estado inicial
        self.assertFalse(self.catalogo.is_deleted)
        self.assertIsNone(self.catalogo.deleted_at)
        self.assertIsNone(self.catalogo.deleted_by)
        
        # Realizar soft delete
        result = self.catalogo.soft_delete(user=self.user, reason='Test deletion')
        
        # Verificar resultado
        self.assertTrue(result)
        self.assertTrue(self.catalogo.is_deleted)
        self.assertIsNotNone(self.catalogo.deleted_at)
        self.assertEqual(self.catalogo.deleted_by, self.user)
        self.assertEqual(self.catalogo.deletion_reason, 'Test deletion')
    
    def test_soft_delete_already_deleted_returns_false(self):
        """Test que soft_delete retorna False si ya está eliminado"""
        # Eliminar primero
        self.catalogo.soft_delete(user=self.user)
        
        # Intentar eliminar de nuevo
        result = self.catalogo.soft_delete(user=self.user)
        
        self.assertFalse(result)
    
    def test_restore_restores_deleted_catalogo(self):
        """Test que restore restaura un catálogo eliminado"""
        # Eliminar primero
        self.catalogo.soft_delete(user=self.user, reason='Test deletion')
        self.assertTrue(self.catalogo.is_deleted)
        
        # Restaurar
        result = self.catalogo.restore(user=self.user)
        
        # Verificar restauración
        self.assertTrue(result)
        self.assertFalse(self.catalogo.is_deleted)
        self.assertIsNone(self.catalogo.deleted_at)
        self.assertIsNone(self.catalogo.deleted_by)
        self.assertEqual(self.catalogo.deletion_reason, '')
    
    def test_restore_non_deleted_returns_false(self):
        """Test que restore retorna False si no está eliminado"""
        result = self.catalogo.restore(user=self.user)
        self.assertFalse(result)
    
    def test_is_deleted_property(self):
        """Test de la propiedad is_deleted"""
        # Inicialmente no eliminado
        self.assertFalse(self.catalogo.is_deleted)
        
        # Después de soft delete
        self.catalogo.soft_delete(user=self.user)
        self.assertTrue(self.catalogo.is_deleted)
        
        # Después de restore
        self.catalogo.restore(user=self.user)
        self.assertFalse(self.catalogo.is_deleted)
    
    def test_hard_delete_removes_from_database(self):
        """Test que hard_delete elimina permanentemente"""
        obj_id = self.catalogo.id
        
        # Hard delete
        self.catalogo.hard_delete()
        
        # Verificar que no existe en la base de datos
        with self.assertRaises(Catalogo.DoesNotExist):
            Catalogo.all_objects.get(id=obj_id)
    
    def test_default_delete_uses_soft_delete(self):
        """Test que el método delete por defecto usa soft delete"""
        # Llamar delete() normal
        self.catalogo.delete(user=self.user)
        
        # Verificar que es soft delete, no hard delete
        self.assertTrue(self.catalogo.is_deleted)
        
        # Verificar que aún existe en la base de datos
        obj_from_db = Catalogo.all_objects.get(id=self.catalogo.id)
        self.assertTrue(obj_from_db.is_deleted)


class SoftDeleteManagerCatalogoTestCase(TestCase):
    """Tests para SoftDeleteManager usando modelo Catalogo"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Crear objetos de prueba
        self.active_catalogo1 = Catalogo.objects.create(
            codigo='04220001',
            denominacion='EQUIPO ACTIVO 1',
            grupo='04 AGRICOLA Y PESQUERO',
            clase='22 EQUIPO',
            resolucion='001-2024/TEST',
            estado='ACTIVO',
            created_by=self.user
        )
        self.active_catalogo2 = Catalogo.objects.create(
            codigo='04220002',
            denominacion='EQUIPO ACTIVO 2',
            grupo='04 AGRICOLA Y PESQUERO',
            clase='22 EQUIPO',
            resolucion='001-2024/TEST',
            estado='ACTIVO',
            created_by=self.user
        )
        self.deleted_catalogo1 = Catalogo.objects.create(
            codigo='04220003',
            denominacion='EQUIPO ELIMINADO 1',
            grupo='04 AGRICOLA Y PESQUERO',
            clase='22 EQUIPO',
            resolucion='001-2024/TEST',
            estado='ACTIVO',
            created_by=self.user
        )
        self.deleted_catalogo2 = Catalogo.objects.create(
            codigo='04220004',
            denominacion='EQUIPO ELIMINADO 2',
            grupo='04 AGRICOLA Y PESQUERO',
            clase='22 EQUIPO',
            resolucion='001-2024/TEST',
            estado='ACTIVO',
            created_by=self.user
        )
        
        # Eliminar algunos objetos
        self.deleted_catalogo1.soft_delete(user=self.user)
        self.deleted_catalogo2.soft_delete(user=self.user)
    
    def test_default_manager_excludes_deleted(self):
        """Test que el manager por defecto excluye eliminados"""
        active_objects = Catalogo.objects.filter(
            codigo__in=['04220001', '04220002', '04220003', '04220004']
        )
        
        self.assertEqual(active_objects.count(), 2)
        self.assertIn(self.active_catalogo1, active_objects)
        self.assertIn(self.active_catalogo2, active_objects)
        self.assertNotIn(self.deleted_catalogo1, active_objects)
        self.assertNotIn(self.deleted_catalogo2, active_objects)
    
    def test_deleted_only_returns_only_deleted(self):
        """Test que deleted_only retorna solo eliminados"""
        deleted_objects = Catalogo.objects.deleted_only().filter(
            codigo__in=['04220001', '04220002', '04220003', '04220004']
        )
        
        self.assertEqual(deleted_objects.count(), 2)
        self.assertIn(self.deleted_catalogo1, deleted_objects)
        self.assertIn(self.deleted_catalogo2, deleted_objects)
        self.assertNotIn(self.active_catalogo1, deleted_objects)
        self.assertNotIn(self.active_catalogo2, deleted_objects)
    
    def test_with_deleted_returns_all(self):
        """Test que with_deleted retorna todos los objetos"""
        all_objects = Catalogo.objects.with_deleted().filter(
            codigo__in=['04220001', '04220002', '04220003', '04220004']
        )
        
        self.assertEqual(all_objects.count(), 4)
        self.assertIn(self.active_catalogo1, all_objects)
        self.assertIn(self.active_catalogo2, all_objects)
        self.assertIn(self.deleted_catalogo1, all_objects)
        self.assertIn(self.deleted_catalogo2, all_objects)
    
    def test_all_objects_manager_returns_all(self):
        """Test que all_objects manager retorna todos los objetos"""
        all_objects = Catalogo.all_objects.filter(
            codigo__in=['04220001', '04220002', '04220003', '04220004']
        )
        
        self.assertEqual(all_objects.count(), 4)
        self.assertIn(self.active_catalogo1, all_objects)
        self.assertIn(self.active_catalogo2, all_objects)
        self.assertIn(self.deleted_catalogo1, all_objects)
        self.assertIn(self.deleted_catalogo2, all_objects)
    
    def test_buscar_por_denominacion_excludes_deleted(self):
        """Test que buscar_por_denominacion excluye eliminados"""
        resultados = Catalogo.buscar_por_denominacion('EQUIPO')
        
        # Debe retornar solo los activos
        self.assertEqual(resultados.count(), 2)
        self.assertIn(self.active_catalogo1, resultados)
        self.assertIn(self.active_catalogo2, resultados)
        self.assertNotIn(self.deleted_catalogo1, resultados)
        self.assertNotIn(self.deleted_catalogo2, resultados)
    
    def test_obtener_grupos_excludes_deleted(self):
        """Test que obtener_grupos excluye eliminados"""
        # Crear catálogo con grupo diferente y eliminarlo
        catalogo_otro_grupo = Catalogo.objects.create(
            codigo='05110001',
            denominacion='MUEBLE ELIMINADO',
            grupo='05 MUEBLES',
            clase='11 MOBILIARIO',
            resolucion='001-2024/TEST',
            estado='ACTIVO',
            created_by=self.user
        )
        catalogo_otro_grupo.soft_delete(user=self.user)
        
        grupos = list(Catalogo.obtener_grupos())
        
        # Solo debe aparecer el grupo de los catálogos activos
        self.assertIn('04 AGRICOLA Y PESQUERO', grupos)
        self.assertNotIn('05 MUEBLES', grupos)


class CatalogoDeleteOverrideTestCase(TestCase):
    """Tests para el método delete() sobrescrito en Catalogo"""
    
    def setUp(self):
        """Configuración inicial"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.catalogo = Catalogo.objects.create(
            codigo='04220001',
            denominacion='EQUIPO DE PRUEBA',
            grupo='04 AGRICOLA Y PESQUERO',
            clase='22 EQUIPO',
            resolucion='001-2024/TEST',
            estado='ACTIVO',
            created_by=self.user
        )
        self.oficina = Oficina.objects.create(
            nombre='Oficina Test',
            codigo='TEST001',
            responsable='Responsable Test',
            created_by=self.user
        )
    
    def test_delete_with_user_parameter(self):
        """Test que delete() acepta parámetro user"""
        result = self.catalogo.delete(user=self.user, reason='Test deletion')
        
        self.assertTrue(result)
        self.assertTrue(self.catalogo.is_deleted)
        self.assertEqual(self.catalogo.deleted_by, self.user)
        self.assertEqual(self.catalogo.deletion_reason, 'Test deletion')
    
    def test_delete_without_parameters_uses_soft_delete(self):
        """Test que delete() sin parámetros usa soft delete"""
        result = self.catalogo.delete()
        
        # Debe usar soft delete (retorna True/False, no tupla)
        self.assertIsInstance(result, bool)
        self.assertTrue(self.catalogo.is_deleted)
    
    def test_delete_with_bienes_raises_validation_error(self):
        """Test que delete() con bienes asignados lanza ValidationError"""
        # Crear bien asignado al catálogo
        bien = BienPatrimonial.objects.create(
            codigo_patrimonial='BP001',
            catalogo=self.catalogo,
            oficina=self.oficina,
            estado_bien='B',
            created_by=self.user
        )
        
        # Intentar eliminar catálogo con bienes debe fallar
        with self.assertRaises(ValidationError) as context:
            self.catalogo.delete(user=self.user)
        
        # Verificar mensaje de error
        self.assertIn('bienes patrimoniales', str(context.exception).lower())
    
    def test_delete_with_deleted_bienes_succeeds(self):
        """Test que delete() con bienes eliminados (soft deleted) funciona"""
        # Crear bien asignado al catálogo
        bien = BienPatrimonial.objects.create(
            codigo_patrimonial='BP001',
            catalogo=self.catalogo,
            oficina=self.oficina,
            estado_bien='B',
            created_by=self.user
        )
        
        # Eliminar el bien (soft delete)
        bien.soft_delete(user=self.user)
        
        # Ahora eliminar el catálogo debe funcionar
        result = self.catalogo.delete(user=self.user)
        
        self.assertTrue(result)
        self.assertTrue(self.catalogo.is_deleted)
    
    def test_delete_with_multiple_bienes_some_deleted(self):
        """Test que delete() falla si hay al menos un bien activo"""
        # Crear bien activo
        bien_activo = BienPatrimonial.objects.create(
            codigo_patrimonial='BP001',
            catalogo=self.catalogo,
            oficina=self.oficina,
            estado_bien='B',
            created_by=self.user
        )
        
        # Crear bien eliminado
        bien_eliminado = BienPatrimonial.objects.create(
            codigo_patrimonial='BP002',
            catalogo=self.catalogo,
            oficina=self.oficina,
            estado_bien='B',
            created_by=self.user
        )
        bien_eliminado.soft_delete(user=self.user)
        
        # Intentar eliminar debe fallar porque hay un bien activo
        with self.assertRaises(ValidationError):
            self.catalogo.delete(user=self.user)


class CatalogoPuedeEliminarseTestCase(TestCase):
    """Tests para el método puede_eliminarse()"""
    
    def setUp(self):
        """Configuración inicial"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.catalogo = Catalogo.objects.create(
            codigo='04220001',
            denominacion='EQUIPO DE PRUEBA',
            grupo='04 AGRICOLA Y PESQUERO',
            clase='22 EQUIPO',
            resolucion='001-2024/TEST',
            estado='ACTIVO',
            created_by=self.user
        )
        self.oficina = Oficina.objects.create(
            nombre='Oficina Test',
            codigo='TEST001',
            responsable='Responsable Test',
            created_by=self.user
        )
    
    def test_puede_eliminarse_sin_bienes(self):
        """Test que catálogo sin bienes puede eliminarse"""
        self.assertTrue(self.catalogo.puede_eliminarse())
    
    def test_puede_eliminarse_con_bienes_activos(self):
        """Test que catálogo con bienes activos no puede eliminarse"""
        # Crear bien activo
        bien = BienPatrimonial.objects.create(
            codigo_patrimonial='BP001',
            catalogo=self.catalogo,
            oficina=self.oficina,
            estado_bien='B',
            created_by=self.user
        )
        
        self.assertFalse(self.catalogo.puede_eliminarse())
    
    def test_puede_eliminarse_con_bienes_eliminados(self):
        """Test que catálogo con solo bienes eliminados puede eliminarse"""
        # Crear bien y eliminarlo
        bien = BienPatrimonial.objects.create(
            codigo_patrimonial='BP001',
            catalogo=self.catalogo,
            oficina=self.oficina,
            estado_bien='B',
            created_by=self.user
        )
        bien.soft_delete(user=self.user)
        
        # Catálogo debe poder eliminarse
        self.assertTrue(self.catalogo.puede_eliminarse())
    
    def test_puede_eliminarse_con_bienes_mixtos(self):
        """Test que catálogo con bienes activos y eliminados no puede eliminarse"""
        # Crear bien activo
        bien_activo = BienPatrimonial.objects.create(
            codigo_patrimonial='BP001',
            catalogo=self.catalogo,
            oficina=self.oficina,
            estado_bien='B',
            created_by=self.user
        )
        
        # Crear bien eliminado
        bien_eliminado = BienPatrimonial.objects.create(
            codigo_patrimonial='BP002',
            catalogo=self.catalogo,
            oficina=self.oficina,
            estado_bien='B',
            created_by=self.user
        )
        bien_eliminado.soft_delete(user=self.user)
        
        # No debe poder eliminarse porque tiene un bien activo
        self.assertFalse(self.catalogo.puede_eliminarse())
    
    def test_puede_eliminarse_con_multiples_bienes_eliminados(self):
        """Test que catálogo con múltiples bienes eliminados puede eliminarse"""
        # Crear y eliminar múltiples bienes
        for i in range(5):
            bien = BienPatrimonial.objects.create(
                codigo_patrimonial=f'BP00{i+1}',
                catalogo=self.catalogo,
                oficina=self.oficina,
                estado_bien='B',
                created_by=self.user
            )
            bien.soft_delete(user=self.user)
        
        # Catálogo debe poder eliminarse
        self.assertTrue(self.catalogo.puede_eliminarse())


class CatalogoIntegridadReferencialTestCase(TestCase):
    """Tests de integridad referencial con soft delete"""
    
    def setUp(self):
        """Configuración inicial"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.catalogo = Catalogo.objects.create(
            codigo='04220001',
            denominacion='EQUIPO DE PRUEBA',
            grupo='04 AGRICOLA Y PESQUERO',
            clase='22 EQUIPO',
            resolucion='001-2024/TEST',
            estado='ACTIVO',
            created_by=self.user
        )
        self.oficina = Oficina.objects.create(
            nombre='Oficina Test',
            codigo='TEST001',
            responsable='Responsable Test',
            created_by=self.user
        )
    
    def test_bien_no_puede_usar_catalogo_eliminado(self):
        """Test que no se puede crear bien con catálogo eliminado"""
        # Eliminar catálogo
        self.catalogo.soft_delete(user=self.user)
        
        # Intentar crear bien con catálogo eliminado debe fallar
        with self.assertRaises(ValidationError) as context:
            bien = BienPatrimonial(
                codigo_patrimonial='BP001',
                catalogo=self.catalogo,
                oficina=self.oficina,
                estado_bien='B',
                created_by=self.user
            )
            bien.full_clean()
        
        # Verificar mensaje de error
        self.assertIn('catalogo', str(context.exception).lower())
        self.assertIn('eliminado', str(context.exception).lower())
    
    def test_bien_existente_mantiene_referencia_a_catalogo_eliminado(self):
        """Test que bien existente mantiene referencia a catálogo eliminado"""
        # Crear bien con catálogo activo
        bien = BienPatrimonial.objects.create(
            codigo_patrimonial='BP001',
            catalogo=self.catalogo,
            oficina=self.oficina,
            estado_bien='B',
            created_by=self.user
        )
        
        # Eliminar el bien primero
        bien.soft_delete(user=self.user)
        
        # Ahora eliminar el catálogo
        self.catalogo.soft_delete(user=self.user)
        
        # Recargar bien desde BD
        bien.refresh_from_db()
        
        # El bien debe mantener la referencia al catálogo
        self.assertEqual(bien.catalogo, self.catalogo)
        self.assertTrue(bien.catalogo.is_deleted)
    
    def test_restaurar_catalogo_permite_crear_nuevos_bienes(self):
        """Test que restaurar catálogo permite crear nuevos bienes"""
        # Eliminar catálogo
        self.catalogo.soft_delete(user=self.user)
        
        # Restaurar catálogo
        self.catalogo.restore(user=self.user)
        
        # Ahora debe poder crear bien
        bien = BienPatrimonial.objects.create(
            codigo_patrimonial='BP001',
            catalogo=self.catalogo,
            oficina=self.oficina,
            estado_bien='B',
            created_by=self.user
        )
        
        self.assertEqual(bien.catalogo, self.catalogo)
        self.assertFalse(bien.catalogo.is_deleted)
    
    def test_eliminar_todos_bienes_permite_eliminar_catalogo(self):
        """Test que eliminar todos los bienes permite eliminar catálogo"""
        # Crear múltiples bienes
        bienes = []
        for i in range(3):
            bien = BienPatrimonial.objects.create(
                codigo_patrimonial=f'BP00{i+1}',
                catalogo=self.catalogo,
                oficina=self.oficina,
                estado_bien='B',
                created_by=self.user
            )
            bienes.append(bien)
        
        # Catálogo no debe poder eliminarse
        self.assertFalse(self.catalogo.puede_eliminarse())
        
        # Eliminar todos los bienes
        for bien in bienes:
            bien.soft_delete(user=self.user)
        
        # Ahora catálogo debe poder eliminarse
        self.assertTrue(self.catalogo.puede_eliminarse())
        
        # Eliminar catálogo
        result = self.catalogo.delete(user=self.user)
        self.assertTrue(result)
        self.assertTrue(self.catalogo.is_deleted)


class CatalogoImportWithSoftDeleteTestCase(TestCase):
    """Tests de importación con soft delete"""
    
    def setUp(self):
        """Configuración inicial"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_import_restaura_catalogo_eliminado(self):
        """Test que importar restaura catálogo eliminado si actualizar_existentes=True"""
        # Crear y eliminar catálogo
        catalogo = Catalogo.objects.create(
            codigo='04220001',
            denominacion='EQUIPO ORIGINAL',
            grupo='04 AGRICOLA Y PESQUERO',
            clase='22 EQUIPO',
            resolucion='001-2024/TEST',
            estado='ACTIVO',
            created_by=self.user
        )
        catalogo.soft_delete(user=self.user)
        
        # Verificar que está eliminado
        self.assertTrue(catalogo.is_deleted)
        self.assertEqual(Catalogo.objects.count(), 0)
        self.assertEqual(Catalogo.all_objects.count(), 1)
        
        # Simular importación (esto se probaría con archivo real en test de integración)
        # Por ahora verificamos que with_deleted() funciona
        catalogo_eliminado = Catalogo.objects.with_deleted().get(codigo='04220001')
        self.assertTrue(catalogo_eliminado.is_deleted)
        
        # Restaurar
        catalogo_eliminado.restore(user=self.user)
        
        # Verificar que ahora está activo
        self.assertFalse(catalogo_eliminado.is_deleted)
        self.assertEqual(Catalogo.objects.count(), 1)


class CatalogoSoftDeleteIntegrationTestCase(TestCase):
    """Tests de integración para el sistema de soft delete con Catalogo"""
    
    def setUp(self):
        """Configuración inicial"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_soft_delete_with_reason_and_user(self):
        """Test de soft delete con usuario y razón"""
        catalogo = Catalogo.objects.create(
            codigo='04220001',
            denominacion='EQUIPO DE PRUEBA',
            grupo='04 AGRICOLA Y PESQUERO',
            clase='22 EQUIPO',
            resolucion='001-2024/TEST',
            estado='ACTIVO',
            created_by=self.user
        )
        
        # Soft delete con información completa
        catalogo.soft_delete(user=self.user, reason='Testing soft delete functionality')
        
        # Verificar que se guardó toda la información
        catalogo.refresh_from_db()
        self.assertTrue(catalogo.is_deleted)
        self.assertEqual(catalogo.deleted_by, self.user)
        self.assertEqual(catalogo.deletion_reason, 'Testing soft delete functionality')
        self.assertIsNotNone(catalogo.deleted_at)
    
    def test_multiple_soft_deletes_and_restores(self):
        """Test de múltiples eliminaciones y restauraciones"""
        catalogo = Catalogo.objects.create(
            codigo='04220001',
            denominacion='EQUIPO DE PRUEBA',
            grupo='04 AGRICOLA Y PESQUERO',
            clase='22 EQUIPO',
            resolucion='001-2024/TEST',
            estado='ACTIVO',
            created_by=self.user
        )
        
        # Ciclo de eliminación y restauración
        for i in range(3):
            # Eliminar
            catalogo.soft_delete(user=self.user, reason=f'Deletion {i+1}')
            self.assertTrue(catalogo.is_deleted)
            
            # Restaurar
            catalogo.restore(user=self.user)
            self.assertFalse(catalogo.is_deleted)
        
        # Verificar estado final
        self.assertFalse(catalogo.is_deleted)
        self.assertIsNone(catalogo.deleted_at)
        self.assertIsNone(catalogo.deleted_by)
        self.assertEqual(catalogo.deletion_reason, '')
    
    def test_str_method_shows_deleted_status(self):
        """Test que __str__ muestra estado de eliminado"""
        catalogo = Catalogo.objects.create(
            codigo='04220001',
            denominacion='EQUIPO DE PRUEBA',
            grupo='04 AGRICOLA Y PESQUERO',
            clase='22 EQUIPO',
            resolucion='001-2024/TEST',
            estado='ACTIVO',
            created_by=self.user
        )
        
        # String normal
        str_normal = str(catalogo)
        self.assertIn('04220001', str_normal)
        self.assertIn('EQUIPO DE PRUEBA', str_normal)
        
        # Eliminar
        catalogo.soft_delete(user=self.user)
        
        # String debe indicar eliminado
        str_deleted = str(catalogo)
        self.assertIn('ELIMINADO', str_deleted.upper())
