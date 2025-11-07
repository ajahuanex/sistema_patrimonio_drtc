from django.test import TestCase
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.contrib.auth.models import User
from io import StringIO
from apps.core.models import RecycleBinConfig


class RecycleBinConfigModelTest(TestCase):
    """Tests para el modelo RecycleBinConfig"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_create_config_with_valid_data(self):
        """Test crear configuración con datos válidos"""
        config = RecycleBinConfig.objects.create(
            module_name='oficinas',
            retention_days=30,
            auto_delete_enabled=True,
            warning_days_before=7,
            final_warning_days_before=1,
            can_restore_own=True,
            can_restore_others=False,
            updated_by=self.user
        )
        
        self.assertEqual(config.module_name, 'oficinas')
        self.assertEqual(config.retention_days, 30)
        self.assertTrue(config.auto_delete_enabled)
        self.assertEqual(config.warning_days_before, 7)
        self.assertEqual(config.final_warning_days_before, 1)
        self.assertTrue(config.can_restore_own)
        self.assertFalse(config.can_restore_others)
        self.assertEqual(config.updated_by, self.user)
    
    def test_config_str_representation(self):
        """Test representación en string de la configuración"""
        config = RecycleBinConfig.objects.create(
            module_name='bienes',
            retention_days=30
        )
        
        self.assertEqual(str(config), "Configuración de Bienes Patrimoniales")
    
    def test_unique_module_constraint(self):
        """Test que no se pueden crear configuraciones duplicadas para el mismo módulo"""
        RecycleBinConfig.objects.create(
            module_name='catalogo',
            retention_days=30
        )
        
        with self.assertRaises(Exception):  # IntegrityError
            RecycleBinConfig.objects.create(
                module_name='catalogo',
                retention_days=45
            )
    
    def test_validation_retention_days_positive(self):
        """Test validación de días de retención positivos"""
        config = RecycleBinConfig(
            module_name='oficinas',
            retention_days=0,  # Inválido
            warning_days_before=7,
            final_warning_days_before=1
        )
        
        with self.assertRaises(ValidationError) as context:
            config.clean()
        
        self.assertIn('retention_days', context.exception.message_dict)
    
    def test_validation_warning_days_less_than_retention(self):
        """Test validación de días de advertencia menores que retención"""
        config = RecycleBinConfig(
            module_name='oficinas',
            retention_days=30,
            warning_days_before=30,  # Inválido (igual a retention_days)
            final_warning_days_before=1
        )
        
        with self.assertRaises(ValidationError) as context:
            config.clean()
        
        self.assertIn('warning_days_before', context.exception.message_dict)
    
    def test_validation_final_warning_less_than_warning(self):
        """Test validación de días de advertencia final menores que advertencia"""
        config = RecycleBinConfig(
            module_name='oficinas',
            retention_days=30,
            warning_days_before=7,
            final_warning_days_before=7  # Inválido (igual a warning_days_before)
        )
        
        with self.assertRaises(ValidationError) as context:
            config.clean()
        
        self.assertIn('final_warning_days_before', context.exception.message_dict)
    
    def test_validation_final_warning_positive(self):
        """Test validación de días de advertencia final positivos"""
        config = RecycleBinConfig(
            module_name='oficinas',
            retention_days=30,
            warning_days_before=7,
            final_warning_days_before=0  # Inválido
        )
        
        with self.assertRaises(ValidationError) as context:
            config.clean()
        
        self.assertIn('final_warning_days_before', context.exception.message_dict)
    
    def test_get_config_for_module_existing(self):
        """Test obtener configuración existente para módulo"""
        config = RecycleBinConfig.objects.create(
            module_name='oficinas',
            retention_days=45
        )
        
        retrieved_config = RecycleBinConfig.get_config_for_module('oficinas')
        self.assertEqual(retrieved_config.id, config.id)
        self.assertEqual(retrieved_config.retention_days, 45)
    
    def test_get_config_for_module_creates_default(self):
        """Test crear configuración por defecto si no existe"""
        # Verificar que no existe configuración
        self.assertFalse(RecycleBinConfig.objects.filter(module_name='bienes').exists())
        
        # Obtener configuración (debería crear una por defecto)
        config = RecycleBinConfig.get_config_for_module('bienes')
        
        self.assertEqual(config.module_name, 'bienes')
        self.assertEqual(config.retention_days, 30)
        self.assertTrue(config.auto_delete_enabled)
        self.assertEqual(config.warning_days_before, 7)
        self.assertEqual(config.final_warning_days_before, 1)
        self.assertTrue(config.can_restore_own)
        self.assertFalse(config.can_restore_others)
    
    def test_get_effective_permissions_admin_user(self):
        """Test permisos efectivos para usuario administrador"""
        from apps.core.models import UserProfile
        
        # Crear usuario administrador
        admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        # Actualizar el perfil que se crea automáticamente
        admin_user.profile.role = 'administrador'
        admin_user.profile.save()
        
        config = RecycleBinConfig.objects.create(
            module_name='oficinas',
            can_restore_own=False,
            can_restore_others=False
        )
        
        permissions = config.get_effective_permissions(admin_user)
        
        # Los administradores siempre tienen todos los permisos
        self.assertTrue(permissions['can_restore_own'])
        self.assertTrue(permissions['can_restore_others'])
        self.assertTrue(permissions['can_permanent_delete'])
        self.assertTrue(permissions['can_view_all'])
    
    def test_get_effective_permissions_regular_user(self):
        """Test permisos efectivos para usuario regular"""
        config = RecycleBinConfig.objects.create(
            module_name='oficinas',
            can_restore_own=True,
            can_restore_others=False
        )
        
        permissions = config.get_effective_permissions(self.user)
        
        # Los usuarios regulares siguen la configuración del módulo
        self.assertTrue(permissions['can_restore_own'])
        self.assertFalse(permissions['can_restore_others'])
        self.assertFalse(permissions['can_permanent_delete'])
        self.assertFalse(permissions['can_view_all'])


class SetupRecycleBinCommandTest(TestCase):
    """Tests para el comando de management setup_recycle_bin"""
    
    def test_setup_all_modules_default_config(self):
        """Test configurar todos los módulos con configuración por defecto"""
        out = StringIO()
        call_command('setup_recycle_bin', stdout=out)
        
        # Verificar que se crearon configuraciones para todos los módulos
        self.assertEqual(RecycleBinConfig.objects.count(), 4)
        
        for module_name in ['oficinas', 'bienes', 'catalogo', 'core']:
            config = RecycleBinConfig.objects.get(module_name=module_name)
            self.assertEqual(config.retention_days, 30)
            self.assertTrue(config.auto_delete_enabled)
            self.assertEqual(config.warning_days_before, 7)
            self.assertEqual(config.final_warning_days_before, 1)
            self.assertTrue(config.can_restore_own)
            self.assertFalse(config.can_restore_others)
        
        output = out.getvalue()
        self.assertIn('Configuraciones creadas: 4', output)
    
    def test_setup_specific_module(self):
        """Test configurar un módulo específico"""
        out = StringIO()
        call_command('setup_recycle_bin', '--module=oficinas', stdout=out)
        
        # Solo debería existir configuración para oficinas
        self.assertEqual(RecycleBinConfig.objects.count(), 1)
        config = RecycleBinConfig.objects.get(module_name='oficinas')
        self.assertEqual(config.retention_days, 30)
        
        output = out.getvalue()
        self.assertIn('Configuraciones creadas: 1', output)
    
    def test_setup_custom_parameters(self):
        """Test configurar con parámetros personalizados"""
        out = StringIO()
        call_command(
            'setup_recycle_bin',
            '--retention-days=60',
            '--warning-days=14',
            '--final-warning-days=3',
            '--disable-auto-delete',
            '--enable-restore-others',
            '--module=bienes',
            stdout=out
        )
        
        config = RecycleBinConfig.objects.get(module_name='bienes')
        self.assertEqual(config.retention_days, 60)
        self.assertFalse(config.auto_delete_enabled)
        self.assertEqual(config.warning_days_before, 14)
        self.assertEqual(config.final_warning_days_before, 3)
        self.assertTrue(config.can_restore_own)
        self.assertTrue(config.can_restore_others)
    
    def test_setup_force_update_existing(self):
        """Test forzar actualización de configuración existente"""
        # Crear configuración inicial
        RecycleBinConfig.objects.create(
            module_name='catalogo',
            retention_days=15
        )
        
        out = StringIO()
        call_command(
            'setup_recycle_bin',
            '--retention-days=45',
            '--module=catalogo',
            '--force',
            stdout=out
        )
        
        config = RecycleBinConfig.objects.get(module_name='catalogo')
        self.assertEqual(config.retention_days, 45)
        
        output = out.getvalue()
        self.assertIn('Configuraciones actualizadas: 1', output)
    
    def test_setup_validation_error_retention_days(self):
        """Test error de validación en días de retención"""
        with self.assertRaises(Exception):  # CommandError
            call_command('setup_recycle_bin', '--retention-days=0')
    
    def test_setup_validation_error_warning_days(self):
        """Test error de validación en días de advertencia"""
        with self.assertRaises(Exception):  # CommandError
            call_command(
                'setup_recycle_bin',
                '--retention-days=30',
                '--warning-days=30'
            )