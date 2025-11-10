"""
Tests para los formularios de papelera de reciclaje
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.conf import settings

from apps.core.models import RecycleBin, UserProfile
from apps.core.forms import (
    RestoreForm, 
    PermanentDeleteForm, 
    BulkOperationForm,
    QuickRestoreForm
)
from apps.oficinas.models import Oficina


class RestoreFormTest(TestCase):
    """Tests para el formulario de restauración"""
    
    def setUp(self):
        """Configurar datos de prueba"""
        # Crear usuario administrador
        self.admin_user = User.objects.create_user(
            username='admin',
            password='admin123',
            email='admin@test.com'
        )
        UserProfile.objects.create(
            user=self.admin_user,
            role='administrador',
            is_active=True
        )
        
        # Crear usuario regular
        self.regular_user = User.objects.create_user(
            username='user',
            password='user123',
            email='user@test.com'
        )
        UserProfile.objects.create(
            user=self.regular_user,
            role='funcionario',
            is_active=True
        )
        
        # Crear oficina y eliminarla
        self.oficina = Oficina.objects.create(
            nombre='Oficina Test',
            codigo='OFI-001',
            direccion='Test Address',
            telefono='123456',
            estado=True
        )
        self.oficina.soft_delete(self.admin_user, 'Test deletion')
        
        # Obtener entrada en papelera
        content_type = ContentType.objects.get_for_model(Oficina)
        self.recycle_entry = RecycleBin.objects.get(
            content_type=content_type,
            object_id=self.oficina.id
        )
    
    def test_restore_form_valid(self):
        """Test formulario de restauración válido"""
        form_data = {
            'entry_id': self.recycle_entry.id,
            'confirm': True,
            'notes': 'Restaurando para pruebas'
        }
        
        form = RestoreForm(
            form_data, 
            entry=self.recycle_entry, 
            user=self.admin_user
        )
        
        self.assertTrue(form.is_valid())
    
    def test_restore_form_missing_confirmation(self):
        """Test formulario sin confirmación"""
        form_data = {
            'entry_id': self.recycle_entry.id,
            'confirm': False,
        }
        
        form = RestoreForm(
            form_data, 
            entry=self.recycle_entry, 
            user=self.admin_user
        )
        
        self.assertFalse(form.is_valid())
        self.assertIn('confirm', form.errors)
    
    def test_restore_form_invalid_entry_id(self):
        """Test formulario con ID inválido"""
        form_data = {
            'entry_id': 99999,
            'confirm': True,
        }
        
        form = RestoreForm(form_data, user=self.admin_user)
        
        self.assertFalse(form.is_valid())
        self.assertIn('entry_id', form.errors)
    
    def test_restore_form_no_permissions(self):
        """Test formulario sin permisos"""
        form_data = {
            'entry_id': self.recycle_entry.id,
            'confirm': True,
        }
        
        # Usuario regular intentando restaurar elemento de admin
        form = RestoreForm(
            form_data, 
            entry=self.recycle_entry, 
            user=self.regular_user
        )
        
        self.assertFalse(form.is_valid())


class PermanentDeleteFormTest(TestCase):
    """Tests para el formulario de eliminación permanente"""
    
    def setUp(self):
        """Configurar datos de prueba"""
        # Configurar código de seguridad
        settings.PERMANENT_DELETE_CODE = 'TEST_CODE_123'
        
        # Crear usuario administrador
        self.admin_user = User.objects.create_user(
            username='admin',
            password='admin123',
            email='admin@test.com'
        )
        UserProfile.objects.create(
            user=self.admin_user,
            role='administrador',
            is_active=True
        )
        
        # Crear oficina y eliminarla
        self.oficina = Oficina.objects.create(
            nombre='Oficina Test',
            codigo='OFI-001',
            direccion='Test Address',
            telefono='123456',
            estado=True
        )
        self.oficina.soft_delete(self.admin_user, 'Test deletion')
        
        # Obtener entrada en papelera
        content_type = ContentType.objects.get_for_model(Oficina)
        self.recycle_entry = RecycleBin.objects.get(
            content_type=content_type,
            object_id=self.oficina.id
        )
    
    def test_permanent_delete_form_valid(self):
        """Test formulario de eliminación permanente válido"""
        form_data = {
            'entry_id': self.recycle_entry.id,
            'security_code': 'TEST_CODE_123',
            'confirm_text': 'ELIMINAR',
            'reason': 'Este es un motivo válido con más de 20 caracteres para la eliminación'
        }
        
        form = PermanentDeleteForm(
            form_data,
            entry=self.recycle_entry,
            user=self.admin_user
        )
        
        self.assertTrue(form.is_valid())
    
    def test_permanent_delete_form_wrong_security_code(self):
        """Test formulario con código de seguridad incorrecto"""
        form_data = {
            'entry_id': self.recycle_entry.id,
            'security_code': 'WRONG_CODE',
            'confirm_text': 'ELIMINAR',
            'reason': 'Este es un motivo válido con más de 20 caracteres'
        }
        
        form = PermanentDeleteForm(
            form_data,
            entry=self.recycle_entry,
            user=self.admin_user
        )
        
        self.assertFalse(form.is_valid())
        self.assertIn('security_code', form.errors)
    
    def test_permanent_delete_form_wrong_confirm_text(self):
        """Test formulario con texto de confirmación incorrecto"""
        form_data = {
            'entry_id': self.recycle_entry.id,
            'security_code': 'TEST_CODE_123',
            'confirm_text': 'eliminar',  # Minúsculas
            'reason': 'Este es un motivo válido con más de 20 caracteres'
        }
        
        form = PermanentDeleteForm(
            form_data,
            entry=self.recycle_entry,
            user=self.admin_user
        )
        
        self.assertFalse(form.is_valid())
        self.assertIn('confirm_text', form.errors)
    
    def test_permanent_delete_form_short_reason(self):
        """Test formulario con motivo muy corto"""
        form_data = {
            'entry_id': self.recycle_entry.id,
            'security_code': 'TEST_CODE_123',
            'confirm_text': 'ELIMINAR',
            'reason': 'Corto'  # Menos de 20 caracteres
        }
        
        form = PermanentDeleteForm(
            form_data,
            entry=self.recycle_entry,
            user=self.admin_user
        )
        
        self.assertFalse(form.is_valid())
        self.assertIn('reason', form.errors)


class BulkOperationFormTest(TestCase):
    """Tests para el formulario de operaciones en lote"""
    
    def setUp(self):
        """Configurar datos de prueba"""
        # Configurar código de seguridad
        settings.PERMANENT_DELETE_CODE = 'TEST_CODE_123'
        
        # Crear usuario administrador
        self.admin_user = User.objects.create_user(
            username='admin',
            password='admin123',
            email='admin@test.com'
        )
        UserProfile.objects.create(
            user=self.admin_user,
            role='administrador',
            is_active=True
        )
        
        # Crear múltiples oficinas y eliminarlas
        self.oficinas = []
        self.recycle_entries = []
        
        for i in range(3):
            oficina = Oficina.objects.create(
                nombre=f'Oficina Test {i}',
                codigo=f'OFI-00{i}',
                direccion='Test Address',
                telefono='123456',
                estado=True
            )
            oficina.soft_delete(self.admin_user, f'Test deletion {i}')
            self.oficinas.append(oficina)
            
            content_type = ContentType.objects.get_for_model(Oficina)
            entry = RecycleBin.objects.get(
                content_type=content_type,
                object_id=oficina.id
            )
            self.recycle_entries.append(entry)
    
    def test_bulk_restore_form_valid(self):
        """Test formulario de restauración en lote válido"""
        entry_ids = [entry.id for entry in self.recycle_entries]
        
        form_data = {
            'operation': 'restore',
            'entry_ids': ','.join(map(str, entry_ids)),
            'confirm': True,
            'notes': 'Restauración en lote de prueba'
        }
        
        form = BulkOperationForm(form_data, user=self.admin_user)
        
        self.assertTrue(form.is_valid())
        self.assertEqual(len(form.cleaned_data['entry_ids']), 3)
    
    def test_bulk_delete_form_valid(self):
        """Test formulario de eliminación en lote válido"""
        entry_ids = [entry.id for entry in self.recycle_entries]
        
        form_data = {
            'operation': 'permanent_delete',
            'entry_ids': ','.join(map(str, entry_ids)),
            'security_code': 'TEST_CODE_123',
            'confirm': True,
        }
        
        form = BulkOperationForm(form_data, user=self.admin_user)
        
        self.assertTrue(form.is_valid())
    
    def test_bulk_delete_form_missing_security_code(self):
        """Test formulario de eliminación en lote sin código de seguridad"""
        entry_ids = [entry.id for entry in self.recycle_entries]
        
        form_data = {
            'operation': 'permanent_delete',
            'entry_ids': ','.join(map(str, entry_ids)),
            'confirm': True,
        }
        
        form = BulkOperationForm(form_data, user=self.admin_user)
        
        self.assertFalse(form.is_valid())
    
    def test_bulk_form_empty_entry_ids(self):
        """Test formulario sin IDs seleccionados"""
        form_data = {
            'operation': 'restore',
            'entry_ids': '',
            'confirm': True,
        }
        
        form = BulkOperationForm(form_data, user=self.admin_user)
        
        self.assertFalse(form.is_valid())
        self.assertIn('entry_ids', form.errors)
    
    def test_bulk_form_invalid_entry_ids(self):
        """Test formulario con IDs inválidos"""
        form_data = {
            'operation': 'restore',
            'entry_ids': '99999,88888',
            'confirm': True,
        }
        
        form = BulkOperationForm(form_data, user=self.admin_user)
        
        self.assertFalse(form.is_valid())
        self.assertIn('entry_ids', form.errors)


class QuickRestoreFormTest(TestCase):
    """Tests para el formulario de restauración rápida"""
    
    def setUp(self):
        """Configurar datos de prueba"""
        # Crear usuario administrador
        self.admin_user = User.objects.create_user(
            username='admin',
            password='admin123',
            email='admin@test.com'
        )
        UserProfile.objects.create(
            user=self.admin_user,
            role='administrador',
            is_active=True
        )
        
        # Crear oficina y eliminarla
        self.oficina = Oficina.objects.create(
            nombre='Oficina Test',
            codigo='OFI-001',
            direccion='Test Address',
            telefono='123456',
            estado=True
        )
        self.oficina.soft_delete(self.admin_user, 'Test deletion')
        
        # Obtener entrada en papelera
        content_type = ContentType.objects.get_for_model(Oficina)
        self.recycle_entry = RecycleBin.objects.get(
            content_type=content_type,
            object_id=self.oficina.id
        )
    
    def test_quick_restore_form_valid(self):
        """Test formulario de restauración rápida válido"""
        form_data = {
            'entry_id': self.recycle_entry.id,
        }
        
        form = QuickRestoreForm(form_data, user=self.admin_user)
        
        self.assertTrue(form.is_valid())
    
    def test_quick_restore_form_invalid_entry(self):
        """Test formulario con entrada inválida"""
        form_data = {
            'entry_id': 99999,
        }
        
        form = QuickRestoreForm(form_data, user=self.admin_user)
        
        self.assertFalse(form.is_valid())
        self.assertIn('entry_id', form.errors)
