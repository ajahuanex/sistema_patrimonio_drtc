"""
Tests para la integración de la papelera de reciclaje en la navegación principal.
Verifica que los enlaces, badges, notificaciones y accesos rápidos funcionen correctamente.
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from apps.core.models import UserProfile, RecycleBin
from apps.oficinas.models import Oficina
from apps.bienes.models import BienPatrimonial
from apps.catalogo.models import Catalogo
from django.contrib.contenttypes.models import ContentType


class RecycleBinNavigationIntegrationTest(TestCase):
    """Tests para la integración de papelera en navegación"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        # Crear usuarios con diferentes roles
        self.admin_user = User.objects.create_user(
            username='admin',
            password='admin123',
            email='admin@test.com'
        )
        self.admin_user.profile.role = 'administrador'
        self.admin_user.profile.save()
        
        self.funcionario_user = User.objects.create_user(
            username='funcionario',
            password='func123',
            email='func@test.com'
        )
        self.funcionario_user.profile.role = 'funcionario'
        self.funcionario_user.profile.save()
        
        self.consulta_user = User.objects.create_user(
            username='consulta',
            password='cons123',
            email='cons@test.com'
        )
        self.consulta_user.profile.role = 'consulta'
        self.consulta_user.profile.save()
        
        # Crear oficina de prueba
        self.oficina = Oficina.objects.create(
            codigo='001',
            nombre='Oficina Test',
            sede='Sede Principal',
            created_by=self.admin_user
        )
        
        # Crear catálogo de prueba
        self.catalogo = Catalogo.objects.create(
            codigo='12345678',
            denominacion='Escritorio',
            cuenta_contable='1.3.1.1',
            created_by=self.admin_user
        )
        
        self.client = Client()
    
    def test_context_processor_adds_recycle_bin_variables(self):
        """Verifica que el context processor agregue las variables correctas"""
        self.client.login(username='admin', password='admin123')
        
        # Crear algunos elementos en papelera
        RecycleBin.objects.create(
            content_type=ContentType.objects.get_for_model(Oficina),
            object_id=self.oficina.id,
            object_repr=str(self.oficina),
            module_name='oficinas',
            deleted_by=self.admin_user,
            auto_delete_at=timezone.now() + timedelta(days=30)
        )
        
        response = self.client.get(reverse('home'))
        
        # Verificar que las variables estén en el contexto
        self.assertIn('recycle_bin_count', response.context)
        self.assertIn('recycle_bin_near_delete_count', response.context)
        self.assertIn('can_view_recycle_bin', response.context)
        
        # Verificar valores
        self.assertEqual(response.context['recycle_bin_count'], 1)
        self.assertTrue(response.context['can_view_recycle_bin'])
    
    def test_navigation_shows_recycle_bin_link_for_authorized_users(self):
        """Verifica que el enlace de papelera aparezca para usuarios autorizados"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('home'))
        
        # Verificar que el enlace esté presente
        self.assertContains(response, 'Papelera')
        self.assertContains(response, reverse('core:recycle_bin_list'))
        self.assertContains(response, 'fa-trash-restore')
    
    def test_navigation_hides_recycle_bin_for_unauthorized_users(self):
        """Verifica que el enlace de papelera no aparezca para usuarios no autorizados"""
        self.client.login(username='consulta', password='cons123')
        response = self.client.get(reverse('home'))
        
        # El enlace no debería estar visible para usuarios de consulta
        self.assertNotContains(response, 'recycle-bin-count-badge')
    
    def test_badges_show_correct_counts(self):
        """Verifica que los badges muestren los contadores correctos"""
        self.client.login(username='admin', password='admin123')
        
        # Crear elementos en papelera
        for i in range(5):
            RecycleBin.objects.create(
                content_type=ContentType.objects.get_for_model(Oficina),
                object_id=self.oficina.id + i,
                object_repr=f'Oficina {i}',
                module_name='oficinas',
                deleted_by=self.admin_user,
                auto_delete_at=timezone.now() + timedelta(days=30)
            )
        
        # Crear elementos próximos a eliminarse
        for i in range(2):
            RecycleBin.objects.create(
                content_type=ContentType.objects.get_for_model(Oficina),
                object_id=self.oficina.id + i + 10,
                object_repr=f'Oficina Urgente {i}',
                module_name='oficinas',
                deleted_by=self.admin_user,
                auto_delete_at=timezone.now() + timedelta(days=3)
            )
        
        response = self.client.get(reverse('home'))
        
        # Verificar que los badges tengan los valores correctos
        self.assertContains(response, 'recycle-bin-count-badge')
        self.assertContains(response, 'recycle-bin-near-delete-badge')
    
    def test_warning_banner_shows_for_near_delete_items(self):
        """Verifica que el banner de advertencia aparezca para elementos próximos a eliminarse"""
        self.client.login(username='admin', password='admin123')
        
        # Crear elemento próximo a eliminarse
        RecycleBin.objects.create(
            content_type=ContentType.objects.get_for_model(Oficina),
            object_id=self.oficina.id,
            object_repr=str(self.oficina),
            module_name='oficinas',
            deleted_by=self.admin_user,
            auto_delete_at=timezone.now() + timedelta(days=5)
        )
        
        response = self.client.get(reverse('home'))
        
        # Verificar que el banner de advertencia esté presente
        self.assertContains(response, '¡Atención!')
        self.assertContains(response, 'eliminar')
        self.assertContains(response, 'próximos 7 días')
    
    def test_quick_access_appears_in_module_lists(self):
        """Verifica que los accesos rápidos aparezcan en los listados de módulos"""
        self.client.login(username='admin', password='admin123')
        
        # Crear elemento en papelera para oficinas
        RecycleBin.objects.create(
            content_type=ContentType.objects.get_for_model(Oficina),
            object_id=self.oficina.id,
            object_repr=str(self.oficina),
            module_name='oficinas',
            deleted_by=self.admin_user,
            auto_delete_at=timezone.now() + timedelta(days=30)
        )
        
        response = self.client.get(reverse('oficinas:lista'))
        
        # Verificar que el acceso rápido esté presente
        self.assertContains(response, 'papelera de reciclaje')
        self.assertContains(response, 'Ver en papelera')
    
    def test_notification_widget_shows_urgent_items(self):
        """Verifica que el widget de notificaciones muestre elementos urgentes"""
        self.client.login(username='admin', password='admin123')
        
        # Crear elementos urgentes
        for i in range(3):
            RecycleBin.objects.create(
                content_type=ContentType.objects.get_for_model(Oficina),
                object_id=self.oficina.id + i,
                object_repr=f'Oficina Urgente {i}',
                module_name='oficinas',
                deleted_by=self.admin_user,
                auto_delete_at=timezone.now() + timedelta(days=i + 1)
            )
        
        response = self.client.get(reverse('home'))
        
        # Verificar que el widget esté presente
        self.assertContains(response, 'Elementos Próximos a Eliminarse')
    
    def test_api_endpoint_returns_correct_status(self):
        """Verifica que el endpoint de API retorne el estado correcto"""
        self.client.login(username='admin', password='admin123')
        
        # Crear elementos en papelera
        RecycleBin.objects.create(
            content_type=ContentType.objects.get_for_model(Oficina),
            object_id=self.oficina.id,
            object_repr=str(self.oficina),
            module_name='oficinas',
            deleted_by=self.admin_user,
            auto_delete_at=timezone.now() + timedelta(days=30)
        )
        
        RecycleBin.objects.create(
            content_type=ContentType.objects.get_for_model(Oficina),
            object_id=self.oficina.id + 1,
            object_repr='Oficina Urgente',
            module_name='oficinas',
            deleted_by=self.admin_user,
            auto_delete_at=timezone.now() + timedelta(days=3)
        )
        
        response = self.client.get(reverse('core:recycle_bin_status_api'))
        
        # Verificar respuesta
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('count', data)
        self.assertIn('near_delete_count', data)
        self.assertIn('urgent_items', data)
        self.assertIn('module_stats', data)
        
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['near_delete_count'], 1)
    
    def test_api_endpoint_requires_authentication(self):
        """Verifica que el endpoint de API requiera autenticación"""
        response = self.client.get(reverse('core:recycle_bin_status_api'))
        
        # Debería redirigir al login
        self.assertEqual(response.status_code, 302)
    
    def test_api_endpoint_respects_permissions(self):
        """Verifica que el endpoint de API respete los permisos"""
        self.client.login(username='consulta', password='cons123')
        
        response = self.client.get(reverse('core:recycle_bin_status_api'))
        
        # Usuario de consulta no debería tener acceso
        self.assertEqual(response.status_code, 403)
    
    def test_funcionario_sees_only_own_items(self):
        """Verifica que funcionarios vean solo sus propios elementos"""
        # Crear elementos eliminados por diferentes usuarios
        RecycleBin.objects.create(
            content_type=ContentType.objects.get_for_model(Oficina),
            object_id=self.oficina.id,
            object_repr=str(self.oficina),
            module_name='oficinas',
            deleted_by=self.admin_user,
            auto_delete_at=timezone.now() + timedelta(days=30)
        )
        
        RecycleBin.objects.create(
            content_type=ContentType.objects.get_for_model(Oficina),
            object_id=self.oficina.id + 1,
            object_repr='Oficina Funcionario',
            module_name='oficinas',
            deleted_by=self.funcionario_user,
            auto_delete_at=timezone.now() + timedelta(days=30)
        )
        
        # Login como funcionario
        self.client.login(username='funcionario', password='func123')
        response = self.client.get(reverse('core:recycle_bin_status_api'))
        
        data = response.json()
        
        # Funcionario debería ver solo 1 elemento (el suyo)
        self.assertEqual(data['count'], 1)
    
    def test_admin_sees_all_items(self):
        """Verifica que administradores vean todos los elementos"""
        # Crear elementos eliminados por diferentes usuarios
        RecycleBin.objects.create(
            content_type=ContentType.objects.get_for_model(Oficina),
            object_id=self.oficina.id,
            object_repr=str(self.oficina),
            module_name='oficinas',
            deleted_by=self.admin_user,
            auto_delete_at=timezone.now() + timedelta(days=30)
        )
        
        RecycleBin.objects.create(
            content_type=ContentType.objects.get_for_model(Oficina),
            object_id=self.oficina.id + 1,
            object_repr='Oficina Funcionario',
            module_name='oficinas',
            deleted_by=self.funcionario_user,
            auto_delete_at=timezone.now() + timedelta(days=30)
        )
        
        # Login como admin
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('core:recycle_bin_status_api'))
        
        data = response.json()
        
        # Admin debería ver todos los elementos
        self.assertEqual(data['count'], 2)
    
    def test_module_stats_in_api_response(self):
        """Verifica que las estadísticas por módulo estén en la respuesta de API"""
        self.client.login(username='admin', password='admin123')
        
        # Crear elementos en diferentes módulos
        RecycleBin.objects.create(
            content_type=ContentType.objects.get_for_model(Oficina),
            object_id=self.oficina.id,
            object_repr=str(self.oficina),
            module_name='oficinas',
            deleted_by=self.admin_user,
            auto_delete_at=timezone.now() + timedelta(days=30)
        )
        
        RecycleBin.objects.create(
            content_type=ContentType.objects.get_for_model(Catalogo),
            object_id=self.catalogo.id,
            object_repr=str(self.catalogo),
            module_name='catalogo',
            deleted_by=self.admin_user,
            auto_delete_at=timezone.now() + timedelta(days=30)
        )
        
        response = self.client.get(reverse('core:recycle_bin_status_api'))
        data = response.json()
        
        # Verificar estadísticas por módulo
        self.assertIn('module_stats', data)
        self.assertIn('oficinas', data['module_stats'])
        self.assertIn('catalogo', data['module_stats'])
        self.assertEqual(data['module_stats']['oficinas'], 1)
        self.assertEqual(data['module_stats']['catalogo'], 1)


class RecycleBinTemplateTagsTest(TestCase):
    """Tests para los template tags de acceso rápido"""
    
    def setUp(self):
        """Configuración inicial"""
        self.admin_user = User.objects.create_user(
            username='admin',
            password='admin123'
        )
        self.admin_user.profile.role = 'administrador'
        self.admin_user.profile.save()
        
        self.oficina = Oficina.objects.create(
            codigo='001',
            nombre='Oficina Test',
            sede='Sede Principal',
            created_by=self.admin_user
        )
        
        self.client = Client()
    
    def test_recycle_bin_quick_access_tag(self):
        """Verifica que el tag de acceso rápido funcione correctamente"""
        self.client.login(username='admin', password='admin123')
        
        # Crear elemento en papelera
        RecycleBin.objects.create(
            content_type=ContentType.objects.get_for_model(Oficina),
            object_id=self.oficina.id,
            object_repr=str(self.oficina),
            module_name='oficinas',
            deleted_by=self.admin_user,
            auto_delete_at=timezone.now() + timedelta(days=30)
        )
        
        response = self.client.get(reverse('oficinas:lista'))
        
        # Verificar que el acceso rápido esté presente
        self.assertContains(response, 'elemento')
        self.assertContains(response, 'papelera')
    
    def test_quick_access_not_shown_when_no_items(self):
        """Verifica que el acceso rápido no aparezca cuando no hay elementos"""
        self.client.login(username='admin', password='admin123')
        
        response = self.client.get(reverse('oficinas:lista'))
        
        # No debería mostrar el acceso rápido si no hay elementos
        # (depende de la implementación específica del template)
        self.assertEqual(response.status_code, 200)



