"""
Tests para el modelo RecycleBin centralizado
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from datetime import timedelta

from apps.core.models import RecycleBin, RecycleBinConfig
from apps.oficinas.models import Oficina


class RecycleBinModelTest(TestCase):
    """Tests para el modelo RecycleBin"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Crear una oficina para usar en los tests
        self.oficina = Oficina.objects.create(
            codigo='TEST001',
            nombre='Oficina de Prueba',
            responsable='Responsable de Prueba',
            ubicacion='Ubicación de prueba',
            telefono='123456789',
            created_by=self.user
        )
        
        # Crear configuración de papelera para oficinas
        self.config = RecycleBinConfig.objects.create(
            module_name='oficinas',
            retention_days=30,
            auto_delete_enabled=True,
            warning_days_before=7,
            final_warning_days_before=1,
            can_restore_own=True,
            can_restore_others=False
        )
    
    def test_recycle_bin_creation(self):
        """Test de creación de entrada en papelera"""
        # Crear entrada en papelera
        recycle_entry = RecycleBin.objects.create(
            content_object=self.oficina,
            object_repr=str(self.oficina),
            module_name='oficinas',
            deleted_by=self.user,
            deletion_reason='Test de eliminación'
        )
        
        # Verificar que se creó correctamente
        self.assertEqual(recycle_entry.content_object, self.oficina)
        self.assertEqual(recycle_entry.object_repr, str(self.oficina))
        self.assertEqual(recycle_entry.module_name, 'oficinas')
        self.assertEqual(recycle_entry.deleted_by, self.user)
        self.assertEqual(recycle_entry.deletion_reason, 'Test de eliminación')
        self.assertIsNotNone(recycle_entry.deleted_at)
        self.assertIsNotNone(recycle_entry.auto_delete_at)
        self.assertFalse(recycle_entry.is_restored)
    
    def test_auto_delete_at_calculation(self):
        """Test del cálculo automático de auto_delete_at"""
        recycle_entry = RecycleBin.objects.create(
            content_object=self.oficina,
            object_repr=str(self.oficina),
            module_name='oficinas',
            deleted_by=self.user
        )
        
        # Verificar que auto_delete_at se calculó correctamente
        expected_auto_delete = recycle_entry.deleted_at + timedelta(days=30)
        self.assertEqual(
            recycle_entry.auto_delete_at.date(),
            expected_auto_delete.date()
        )
    
    def test_days_until_auto_delete(self):
        """Test del cálculo de días hasta eliminación automática"""
        recycle_entry = RecycleBin.objects.create(
            content_object=self.oficina,
            object_repr=str(self.oficina),
            module_name='oficinas',
            deleted_by=self.user
        )
        
        # Verificar días restantes
        days_remaining = recycle_entry.days_until_auto_delete
        self.assertIsInstance(days_remaining, int)
        self.assertGreaterEqual(days_remaining, 0)
    
    def test_is_near_auto_delete(self):
        """Test de detección de proximidad a eliminación automática"""
        # Crear entrada que se elimina en 5 días
        future_delete = timezone.now() + timedelta(days=5)
        recycle_entry = RecycleBin.objects.create(
            content_object=self.oficina,
            object_repr=str(self.oficina),
            module_name='oficinas',
            deleted_by=self.user,
            auto_delete_at=future_delete
        )
        
        self.assertTrue(recycle_entry.is_near_auto_delete)
        
        # Crear otra oficina para evitar constraint de unicidad
        oficina2 = Oficina.objects.create(
            codigo='TEST002',
            nombre='Oficina de Prueba 2',
            responsable='Responsable de Prueba 2',
            ubicacion='Ubicación de prueba 2',
            telefono='987654321',
            created_by=self.user
        )
        
        # Crear entrada que se elimina en 10 días
        future_delete_far = timezone.now() + timedelta(days=10)
        recycle_entry_far = RecycleBin.objects.create(
            content_object=oficina2,
            object_repr=str(oficina2),
            module_name='oficinas',
            deleted_by=self.user,
            auto_delete_at=future_delete_far
        )
        
        self.assertFalse(recycle_entry_far.is_near_auto_delete)
    
    def test_is_ready_for_auto_delete(self):
        """Test de detección de elementos listos para eliminación automática"""
        # Crear entrada que ya debería eliminarse
        past_delete = timezone.now() - timedelta(days=1)
        recycle_entry = RecycleBin.objects.create(
            content_object=self.oficina,
            object_repr=str(self.oficina),
            module_name='oficinas',
            deleted_by=self.user,
            auto_delete_at=past_delete
        )
        
        self.assertTrue(recycle_entry.is_ready_for_auto_delete)
    
    def test_mark_as_restored(self):
        """Test de marcado como restaurado"""
        recycle_entry = RecycleBin.objects.create(
            content_object=self.oficina,
            object_repr=str(self.oficina),
            module_name='oficinas',
            deleted_by=self.user
        )
        
        # Marcar como restaurado
        recycle_entry.mark_as_restored(self.user)
        
        # Verificar que se marcó correctamente
        self.assertTrue(recycle_entry.is_restored)
        self.assertIsNotNone(recycle_entry.restored_at)
        self.assertEqual(recycle_entry.restored_by, self.user)
    
    def test_can_be_restored_by(self):
        """Test de permisos de restauración"""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        recycle_entry = RecycleBin.objects.create(
            content_object=self.oficina,
            object_repr=str(self.oficina),
            module_name='oficinas',
            deleted_by=self.user
        )
        
        # El usuario que eliminó puede restaurar
        self.assertTrue(recycle_entry.can_be_restored_by(self.user))
        
        # Otro usuario no puede restaurar (sin perfil de administrador)
        self.assertFalse(recycle_entry.can_be_restored_by(other_user))
        
        # Una vez restaurado, nadie puede restaurar
        recycle_entry.mark_as_restored(self.user)
        self.assertFalse(recycle_entry.can_be_restored_by(self.user))
    
    def test_get_module_display(self):
        """Test de visualización del nombre del módulo"""
        recycle_entry = RecycleBin.objects.create(
            content_object=self.oficina,
            object_repr=str(self.oficina),
            module_name='oficinas',
            deleted_by=self.user
        )
        
        self.assertEqual(recycle_entry.get_module_display(), 'Oficinas')
    
    def test_unique_constraint(self):
        """Test de constraint de unicidad para entradas activas"""
        # Crear primera entrada
        first_entry = RecycleBin.objects.create(
            content_object=self.oficina,
            object_repr=str(self.oficina),
            module_name='oficinas',
            deleted_by=self.user
        )
        
        # Intentar crear segunda entrada para el mismo objeto debería fallar
        with self.assertRaises(Exception):
            RecycleBin.objects.create(
                content_object=self.oficina,
                object_repr=str(self.oficina),
                module_name='oficinas',
                deleted_by=self.user
            )
        
        # Verificar que la primera entrada existe
        self.assertIsNotNone(first_entry)
        self.assertFalse(first_entry.is_restored)


class RecycleBinConfigModelTest(TestCase):
    """Tests para el modelo RecycleBinConfig"""
    
    def test_config_creation(self):
        """Test de creación de configuración"""
        config = RecycleBinConfig.objects.create(
            module_name='bienes',
            retention_days=45,
            auto_delete_enabled=True,
            warning_days_before=10,
            final_warning_days_before=2,
            can_restore_own=True,
            can_restore_others=True
        )
        
        self.assertEqual(config.module_name, 'bienes')
        self.assertEqual(config.retention_days, 45)
        self.assertTrue(config.auto_delete_enabled)
        self.assertEqual(config.warning_days_before, 10)
        self.assertEqual(config.final_warning_days_before, 2)
        self.assertTrue(config.can_restore_own)
        self.assertTrue(config.can_restore_others)
    
    def test_get_config_for_module(self):
        """Test de obtención de configuración por módulo"""
        # Crear configuración específica
        config = RecycleBinConfig.objects.create(
            module_name='catalogo',
            retention_days=60
        )
        
        # Obtener configuración existente
        retrieved_config = RecycleBinConfig.get_config_for_module('catalogo')
        self.assertEqual(retrieved_config.retention_days, 60)
        
        # Obtener configuración no existente (debería crear una por defecto)
        default_config = RecycleBinConfig.get_config_for_module('nonexistent')
        self.assertEqual(default_config.retention_days, 30)  # Valor por defecto
        self.assertEqual(default_config.module_name, 'nonexistent')
    
    def test_unique_module_constraint(self):
        """Test de constraint de unicidad por módulo"""
        RecycleBinConfig.objects.create(
            module_name='oficinas',
            retention_days=30
        )
        
        # Intentar crear segunda configuración para el mismo módulo debería fallar
        with self.assertRaises(Exception):
            RecycleBinConfig.objects.create(
                module_name='oficinas',
                retention_days=45
            )