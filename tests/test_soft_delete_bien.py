"""
Tests para soft delete en modelo BienPatrimonial
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.bienes.models import BienPatrimonial, MovimientoBien, HistorialEstado
from apps.catalogo.models import Catalogo
from apps.oficinas.models import Oficina


class TestBienPatrimonialSoftDelete(TestCase):
    """Tests para funcionalidad de soft delete en BienPatrimonial"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        # Crear usuario de prueba
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        
        # Crear catálogo de prueba
        self.catalogo = Catalogo.objects.create(
            codigo='04220001',
            grupo='04 AGRICOLA Y PESQUERO',
            clase='22 EQUIPO',
            denominacion='DENOMINACION TEST',
            resolucion='011-2019/SBN',
            estado='ACTIVO',
            created_by=self.user
        )
        
        # Crear oficina de prueba
        self.oficina = Oficina.objects.create(
            codigo='OF001',
            nombre='Oficina Test',
            responsable='Responsable Test',
            estado=True,
            created_by=self.user
        )
        
        # Crear bien de prueba
        self.bien = BienPatrimonial.objects.create(
            codigo_patrimonial='BP001',
            catalogo=self.catalogo,
            oficina=self.oficina,
            estado_bien='B',
            created_by=self.user
        )
    
    def test_soft_delete_marca_como_eliminado(self):
        """Test que soft_delete marca el bien como eliminado sin borrarlo físicamente"""
        # Verificar que el bien existe y no está eliminado
        self.assertFalse(self.bien.is_deleted)
        self.assertIsNone(self.bien.deleted_at)
        
        # Realizar soft delete
        result = self.bien.soft_delete(user=self.user, reason='Test de eliminación')
        
        # Verificar que se marcó como eliminado
        self.assertTrue(result)
        self.assertTrue(self.bien.is_deleted)
        self.assertIsNotNone(self.bien.deleted_at)
        self.assertEqual(self.bien.deleted_by, self.user)
        self.assertEqual(self.bien.deletion_reason, 'Test de eliminación')
        
        # Verificar que el bien sigue existiendo en la base de datos
        bien_db = BienPatrimonial.all_objects.get(id=self.bien.id)
        self.assertIsNotNone(bien_db)
        self.assertTrue(bien_db.is_deleted)
    
    def test_soft_delete_excluye_de_queryset_normal(self):
        """Test que los bienes eliminados no aparecen en queryset normal"""
        # Crear otro bien
        bien2 = BienPatrimonial.objects.create(
            codigo_patrimonial='BP002',
            catalogo=self.catalogo,
            oficina=self.oficina,
            estado_bien='B',
            created_by=self.user
        )
        
        # Verificar que hay 2 bienes
        self.assertEqual(BienPatrimonial.objects.count(), 2)
        
        # Eliminar uno
        self.bien.soft_delete(user=self.user)
        
        # Verificar que solo aparece 1 en queryset normal
        self.assertEqual(BienPatrimonial.objects.count(), 1)
        self.assertEqual(BienPatrimonial.objects.first().id, bien2.id)
        
        # Verificar que con all_objects aparecen ambos
        self.assertEqual(BienPatrimonial.all_objects.count(), 2)
    
    def test_delete_usa_soft_delete_por_defecto(self):
        """Test que el método delete() usa soft delete por defecto"""
        # Llamar a delete()
        self.bien.delete(user=self.user, reason='Test delete')
        
        # Verificar que se usó soft delete
        self.assertTrue(self.bien.is_deleted)
        
        # Verificar que el bien sigue en la base de datos
        bien_db = BienPatrimonial.all_objects.get(id=self.bien.id)
        self.assertIsNotNone(bien_db)
    
    def test_restore_recupera_bien_eliminado(self):
        """Test que restore() recupera un bien eliminado"""
        # Eliminar el bien
        self.bien.soft_delete(user=self.user, reason='Test')
        self.assertTrue(self.bien.is_deleted)
        
        # Restaurar el bien
        result = self.bien.restore(user=self.user)
        
        # Verificar que se restauró
        self.assertTrue(result)
        self.assertFalse(self.bien.is_deleted)
        self.assertIsNone(self.bien.deleted_at)
        self.assertIsNone(self.bien.deleted_by)
        self.assertEqual(self.bien.deletion_reason, '')
        
        # Verificar que aparece en queryset normal
        self.assertEqual(BienPatrimonial.objects.count(), 1)
    
    def test_hard_delete_elimina_permanentemente(self):
        """Test que hard_delete() elimina permanentemente el bien"""
        bien_id = self.bien.id
        
        # Eliminar permanentemente
        self.bien.hard_delete()
        
        # Verificar que no existe en la base de datos
        with self.assertRaises(BienPatrimonial.DoesNotExist):
            BienPatrimonial.all_objects.get(id=bien_id)
    
    def test_puede_eliminarse_verifica_movimientos_pendientes(self):
        """Test que puede_eliminarse() verifica movimientos pendientes"""
        # Crear oficina destino
        oficina_destino = Oficina.objects.create(
            codigo='OF002',
            nombre='Oficina Destino',
            responsable='Responsable 2',
            estado=True,
            created_by=self.user
        )
        
        # Crear movimiento pendiente
        MovimientoBien.objects.create(
            bien=self.bien,
            oficina_origen=self.oficina,
            oficina_destino=oficina_destino,
            motivo='Test',
            confirmado=False,
            created_by=self.user
        )
        
        # Verificar que no puede eliminarse
        puede, mensaje = self.bien.puede_eliminarse()
        self.assertFalse(puede)
        self.assertIn('movimiento', mensaje.lower())
    
    def test_puede_eliminarse_permite_si_no_hay_pendientes(self):
        """Test que puede_eliminarse() permite eliminación si no hay pendientes"""
        puede, mensaje = self.bien.puede_eliminarse()
        self.assertTrue(puede)
    
    def test_soft_delete_cascade_elimina_relaciones(self):
        """Test que soft_delete_cascade() elimina el bien y sus relaciones"""
        # Crear oficina destino
        oficina_destino = Oficina.objects.create(
            codigo='OF002',
            nombre='Oficina Destino',
            responsable='Responsable 2',
            estado=True,
            created_by=self.user
        )
        
        # Crear movimiento confirmado
        movimiento = MovimientoBien.objects.create(
            bien=self.bien,
            oficina_origen=self.oficina,
            oficina_destino=oficina_destino,
            motivo='Test',
            confirmado=True,
            created_by=self.user
        )
        
        # Crear historial de estado
        historial = HistorialEstado.objects.create(
            bien=self.bien,
            estado_anterior='B',
            estado_nuevo='R',
            observaciones='Test',
            created_by=self.user
        )
        
        # Realizar soft delete en cascada
        result = self.bien.soft_delete_cascade(user=self.user, reason='Test cascada')
        
        # Verificar resultado
        self.assertTrue(result['success'])
        self.assertEqual(len(result['deleted_items']), 3)  # Movimiento, historial y bien
        
        # Verificar que el bien está eliminado
        self.assertTrue(self.bien.is_deleted)
        
        # Verificar que las relaciones están eliminadas
        movimiento.refresh_from_db()
        self.assertTrue(movimiento.is_deleted)
        
        historial.refresh_from_db()
        self.assertTrue(historial.is_deleted)
    
    def test_soft_delete_cascade_falla_con_movimientos_pendientes(self):
        """Test que soft_delete_cascade() falla si hay movimientos pendientes"""
        # Crear oficina destino
        oficina_destino = Oficina.objects.create(
            codigo='OF002',
            nombre='Oficina Destino',
            responsable='Responsable 2',
            estado=True,
            created_by=self.user
        )
        
        # Crear movimiento pendiente
        MovimientoBien.objects.create(
            bien=self.bien,
            oficina_origen=self.oficina,
            oficina_destino=oficina_destino,
            motivo='Test',
            confirmado=False,
            created_by=self.user
        )
        
        # Intentar soft delete en cascada
        result = self.bien.soft_delete_cascade(user=self.user, reason='Test')
        
        # Verificar que falló
        self.assertFalse(result['success'])
        self.assertIn('movimiento', result['message'].lower())
        
        # Verificar que el bien no está eliminado
        self.assertFalse(self.bien.is_deleted)
    
    def test_validacion_catalogo_eliminado(self):
        """Test que no se puede asignar un bien a un catálogo eliminado"""
        # Eliminar el catálogo
        self.catalogo.soft_delete(user=self.user)
        
        # Intentar crear un bien con catálogo eliminado
        with self.assertRaises(ValidationError) as context:
            bien = BienPatrimonial(
                codigo_patrimonial='BP003',
                catalogo=self.catalogo,
                oficina=self.oficina,
                estado_bien='B',
                created_by=self.user
            )
            bien.full_clean()
        
        self.assertIn('catalogo', str(context.exception))
    
    def test_validacion_oficina_eliminada(self):
        """Test que no se puede asignar un bien a una oficina eliminada"""
        # Eliminar la oficina
        self.oficina.soft_delete(user=self.user)
        
        # Intentar crear un bien con oficina eliminada
        with self.assertRaises(ValidationError) as context:
            bien = BienPatrimonial(
                codigo_patrimonial='BP003',
                catalogo=self.catalogo,
                oficina=self.oficina,
                estado_bien='B',
                created_by=self.user
            )
            bien.full_clean()
        
        self.assertIn('oficina', str(context.exception))
    
    def test_obtener_por_oficina_excluye_eliminados(self):
        """Test que obtener_por_oficina() excluye bienes eliminados por defecto"""
        # Crear otro bien
        bien2 = BienPatrimonial.objects.create(
            codigo_patrimonial='BP002',
            catalogo=self.catalogo,
            oficina=self.oficina,
            estado_bien='B',
            created_by=self.user
        )
        
        # Eliminar uno
        self.bien.soft_delete(user=self.user)
        
        # Obtener bienes de la oficina
        bienes = BienPatrimonial.obtener_por_oficina(self.oficina)
        
        # Verificar que solo aparece el no eliminado
        self.assertEqual(bienes.count(), 1)
        self.assertEqual(bienes.first().id, bien2.id)
    
    def test_obtener_por_oficina_incluye_eliminados_si_se_solicita(self):
        """Test que obtener_por_oficina() puede incluir eliminados"""
        # Crear otro bien
        bien2 = BienPatrimonial.objects.create(
            codigo_patrimonial='BP002',
            catalogo=self.catalogo,
            oficina=self.oficina,
            estado_bien='B',
            created_by=self.user
        )
        
        # Eliminar uno
        self.bien.soft_delete(user=self.user)
        
        # Obtener bienes incluyendo eliminados
        bienes = BienPatrimonial.obtener_por_oficina(self.oficina, include_deleted=True)
        
        # Verificar que aparecen ambos
        self.assertEqual(bienes.count(), 2)
    
    def test_obtener_eliminados_retorna_solo_eliminados(self):
        """Test que obtener_eliminados() retorna solo bienes eliminados"""
        # Crear otro bien
        bien2 = BienPatrimonial.objects.create(
            codigo_patrimonial='BP002',
            catalogo=self.catalogo,
            oficina=self.oficina,
            estado_bien='B',
            created_by=self.user
        )
        
        # Eliminar uno
        self.bien.soft_delete(user=self.user)
        
        # Obtener eliminados
        eliminados = BienPatrimonial.obtener_eliminados()
        
        # Verificar que solo aparece el eliminado
        self.assertEqual(eliminados.count(), 1)
        self.assertEqual(eliminados.first().id, self.bien.id)
    
    def test_str_muestra_estado_eliminado(self):
        """Test que __str__ muestra [ELIMINADO] para bienes eliminados"""
        # Verificar string normal
        str_normal = str(self.bien)
        self.assertNotIn('[ELIMINADO]', str_normal)
        
        # Eliminar el bien
        self.bien.soft_delete(user=self.user)
        
        # Verificar string con indicador de eliminado
        str_eliminado = str(self.bien)
        self.assertIn('[ELIMINADO]', str_eliminado)
    
    def test_movimiento_no_permite_bien_eliminado(self):
        """Test que no se puede crear movimiento para bien eliminado"""
        # Eliminar el bien
        self.bien.soft_delete(user=self.user)
        
        # Crear oficina destino
        oficina_destino = Oficina.objects.create(
            codigo='OF002',
            nombre='Oficina Destino',
            responsable='Responsable 2',
            estado=True,
            created_by=self.user
        )
        
        # Intentar crear movimiento
        with self.assertRaises(ValidationError) as context:
            movimiento = MovimientoBien(
                bien=self.bien,
                oficina_origen=self.oficina,
                oficina_destino=oficina_destino,
                motivo='Test',
                created_by=self.user
            )
            movimiento.full_clean()
        
        self.assertIn('bien', str(context.exception))
    
    def test_historial_no_permite_bien_eliminado(self):
        """Test que no se puede crear historial para bien eliminado"""
        # Eliminar el bien
        self.bien.soft_delete(user=self.user)
        
        # Intentar crear historial
        with self.assertRaises(ValidationError) as context:
            historial = HistorialEstado(
                bien=self.bien,
                estado_anterior='B',
                estado_nuevo='R',
                observaciones='Test',
                created_by=self.user
            )
            historial.full_clean()
        
        self.assertIn('bien', str(context.exception))
    
    def test_estadisticas_excluyen_eliminados(self):
        """Test que las estadísticas excluyen bienes eliminados por defecto"""
        # Crear otro bien
        bien2 = BienPatrimonial.objects.create(
            codigo_patrimonial='BP002',
            catalogo=self.catalogo,
            oficina=self.oficina,
            estado_bien='R',
            created_by=self.user
        )
        
        # Eliminar uno
        self.bien.soft_delete(user=self.user)
        
        # Obtener estadísticas por estado
        stats = BienPatrimonial.estadisticas_por_estado()
        
        # Verificar que solo cuenta el no eliminado
        total = sum(item['total'] for item in stats)
        self.assertEqual(total, 1)
    
    def test_estadisticas_pueden_incluir_eliminados(self):
        """Test que las estadísticas pueden incluir eliminados si se solicita"""
        # Crear otro bien
        bien2 = BienPatrimonial.objects.create(
            codigo_patrimonial='BP002',
            catalogo=self.catalogo,
            oficina=self.oficina,
            estado_bien='R',
            created_by=self.user
        )
        
        # Eliminar uno
        self.bien.soft_delete(user=self.user)
        
        # Obtener estadísticas incluyendo eliminados
        stats = BienPatrimonial.estadisticas_por_estado(include_deleted=True)
        
        # Verificar que cuenta ambos
        total = sum(item['total'] for item in stats)
        self.assertEqual(total, 2)
