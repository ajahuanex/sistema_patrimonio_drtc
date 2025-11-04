from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.urls import reverse
from .models import UserProfile, AuditLog
from .utils import create_user_with_profile, update_user_role
from apps.oficinas.models import Oficina


class UserPermissionsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Configurar grupos y permisos
        from django.core.management import call_command
        call_command('setup_permissions')
        
        # Crear oficina de prueba
        self.oficina = Oficina.objects.create(
            codigo='TEST001',
            nombre='Oficina de Prueba',
            responsable='Test Manager'
        )
        
        # Crear usuarios de prueba
        self.admin_user, _ = create_user_with_profile(
            username='admin_test',
            email='admin@test.com',
            first_name='Admin',
            last_name='Test',
            password='testpass123',
            role='administrador',
            oficina=self.oficina
        )
        
        self.funcionario_user, _ = create_user_with_profile(
            username='funcionario_test',
            email='funcionario@test.com',
            first_name='Funcionario',
            last_name='Test',
            password='testpass123',
            role='funcionario',
            oficina=self.oficina
        )
        
        self.consulta_user, _ = create_user_with_profile(
            username='consulta_test',
            email='consulta@test.com',
            first_name='Consulta',
            last_name='Test',
            password='testpass123',
            role='consulta',
            oficina=self.oficina
        )

    def test_user_profile_creation(self):
        """Test que se crea automáticamente el perfil del usuario"""
        self.assertTrue(hasattr(self.admin_user, 'profile'))
        self.assertEqual(self.admin_user.profile.role, 'administrador')
        self.assertEqual(self.admin_user.profile.oficina, self.oficina)

    def test_user_permissions(self):
        """Test de permisos según el rol"""
        # Administrador
        self.assertTrue(self.admin_user.profile.can_manage_users())
        self.assertTrue(self.admin_user.profile.can_create_bienes())
        self.assertTrue(self.admin_user.profile.can_delete_bienes())
        
        # Funcionario
        self.assertFalse(self.funcionario_user.profile.can_manage_users())
        self.assertTrue(self.funcionario_user.profile.can_create_bienes())
        self.assertFalse(self.funcionario_user.profile.can_delete_bienes())
        
        # Consulta
        self.assertFalse(self.consulta_user.profile.can_manage_users())
        self.assertFalse(self.consulta_user.profile.can_create_bienes())
        self.assertFalse(self.consulta_user.profile.can_delete_bienes())

    def test_role_update(self):
        """Test de actualización de rol"""
        success, message = update_user_role(self.consulta_user, 'funcionario')
        self.assertTrue(success)
        
        # Recargar desde la base de datos
        self.consulta_user.refresh_from_db()
        self.assertEqual(self.consulta_user.profile.role, 'funcionario')
        self.assertTrue(self.consulta_user.profile.can_create_bienes())

    def test_user_list_access(self):
        """Test de acceso a la lista de usuarios"""
        # Administrador puede acceder
        self.client.login(username='admin_test', password='testpass123')
        response = self.client.get(reverse('core:user_list'))
        self.assertEqual(response.status_code, 200)
        
        # Funcionario no puede acceder
        self.client.login(username='funcionario_test', password='testpass123')
        response = self.client.get(reverse('core:user_list'))
        self.assertEqual(response.status_code, 302)  # Redirect

    def test_audit_log_creation(self):
        """Test de creación de logs de auditoría"""
        initial_count = AuditLog.objects.count()
        
        # Crear un log de auditoría
        AuditLog.objects.create(
            user=self.admin_user,
            action='create',
            model_name='User',
            object_id='1',
            object_repr='test_user',
            ip_address='127.0.0.1'
        )
        
        self.assertEqual(AuditLog.objects.count(), initial_count + 1)

    def test_group_assignment(self):
        """Test de asignación automática a grupos"""
        # Verificar que los usuarios están en los grupos correctos
        admin_group = Group.objects.get(name='Administrador')
        funcionario_group = Group.objects.get(name='Funcionario')
        consulta_group = Group.objects.get(name='Consulta')
        
        self.assertTrue(self.admin_user.groups.filter(name='Administrador').exists())
        self.assertTrue(self.funcionario_user.groups.filter(name='Funcionario').exists())
        self.assertTrue(self.consulta_user.groups.filter(name='Consulta').exists())

    def test_user_deactivation(self):
        """Test de desactivación de usuario"""
        from .utils import deactivate_user
        
        success, message = deactivate_user(self.consulta_user, self.admin_user)
        self.assertTrue(success)
        
        # Recargar desde la base de datos
        self.consulta_user.refresh_from_db()
        self.assertFalse(self.consulta_user.is_active)
        self.assertFalse(self.consulta_user.profile.is_active)

    def test_user_validation(self):
        """Test de validación de datos de usuario"""
        from .utils import validate_user_data
        
        # Usuario duplicado
        errors = validate_user_data('admin_test', 'new@test.com', 'funcionario')
        self.assertIn('El nombre de usuario ya existe', errors)
        
        # Email duplicado
        errors = validate_user_data('new_user', 'admin@test.com', 'funcionario')
        self.assertIn('El email ya está registrado', errors)
        
        # Rol inválido
        errors = validate_user_data('new_user', 'new@test.com', 'invalid_role')
        self.assertIn('Rol inválido', errors[0])
        
        # Datos válidos
        errors = validate_user_data('new_user', 'new@test.com', 'funcionario')
        self.assertEqual(len(errors), 0)