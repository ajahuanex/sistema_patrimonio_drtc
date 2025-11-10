"""
Tests para las vistas de la papelera de reciclaje
"""
import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from apps.core.models import RecycleBin, RecycleBinConfig, UserProfile
from apps.oficinas.models import Oficina
from apps.core.utils import RecycleBinService


@pytest.mark.django_db
class TestRecycleBinListView(TestCase):
    """Tests para RecycleBinListView"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        self.client = Client()
        
        # Crear usuarios
        self.admin_user = User.objects.create_user(
            username='admin',
            password='admin123',
            email='admin@test.com'
        )
        self.admin_user.profile.role = 'administrador'
        self.admin_user.profile.save()
        
        self.regular_user = User.objects.create_user(
            username='user',
            password='user123',
            email='user@test.com'
        )
        self.regular_user.profile.role = 'funcionario'
        self.regular_user.profile.save()
        
        # Crear oficina de prueba
        self.oficina = Oficina.objects.create(
            codigo='TEST001',
            nombre='Oficina Test',
            direccion='Test Address',
            telefono='123456',
            estado=True,
            created_by=self.admin_user
        )
        
        # Eliminar la oficina para crear entrada en papelera
        RecycleBinService.soft_delete_object(
            self.oficina,
            self.admin_user,
            'Test deletion'
        )
    
    def test_list_view_requires_login(self):
        """Verificar que la vista requiere autenticación"""
        response = self.client.get(reverse('core:recycle_bin_list'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_list_view_accessible_by_authenticated_user(self):
        """Verificar que usuarios autenticados pueden acceder"""
        self.client.login(username='user', password='user123')
        response = self.client.get(reverse('core:recycle_bin_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/recycle_bin_list.html')
    
    def test_list_view_shows_deleted_items(self):
        """Verificar que la vista muestra elementos eliminados"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('core:recycle_bin_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Oficina Test')
    
    def test_list_view_filters_by_module(self):
        """Verificar filtrado por módulo"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('core:recycle_bin_list') + '?module=oficinas')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Oficina Test')
    
    def test_list_view_search_functionality(self):
        """Verificar funcionalidad de búsqueda"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('core:recycle_bin_list') + '?search=Test')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Oficina Test')
    
    def test_regular_user_sees_only_own_deletions(self):
        """Verificar que usuarios regulares solo ven sus propias eliminaciones"""
        self.client.login(username='user', password='user123')
        response = self.client.get(reverse('core:recycle_bin_list'))
        self.assertEqual(response.status_code, 200)
        # El usuario regular no debería ver la oficina eliminada por admin
        self.assertNotContains(response, 'Oficina Test')
    
    def test_admin_sees_all_deletions(self):
        """Verificar que administradores ven todas las eliminaciones"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('core:recycle_bin_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Oficina Test')
    
    def test_list_view_pagination(self):
        """Verificar paginación"""
        # Crear múltiples oficinas y eliminarlas
        for i in range(25):
            oficina = Oficina.objects.create(
                codigo=f'TEST{i:03d}',
                nombre=f'Oficina {i}',
                direccion='Test',
                telefono='123',
                estado=True,
                created_by=self.admin_user
            )
            RecycleBinService.soft_delete_object(oficina, self.admin_user, 'Test')
        
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('core:recycle_bin_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['page_obj'].has_next())


@pytest.mark.django_db
class TestRecycleBinDetailView(TestCase):
    """Tests para RecycleBinDetailView"""
    
    def setUp(self):
        """Configuración inicial"""
        self.client = Client()
        
        self.admin_user = User.objects.create_user(
            username='admin',
            password='admin123'
        )
        self.admin_user.profile.role = 'administrador'
        self.admin_user.profile.save()
        
        self.oficina = Oficina.objects.create(
            codigo='TEST001',
            nombre='Oficina Test',
            direccion='Test',
            telefono='123',
            estado=True,
            created_by=self.admin_user
        )
        
        success, message, self.recycle_entry = RecycleBinService.soft_delete_object(
            self.oficina,
            self.admin_user,
            'Test deletion'
        )
    
    def test_detail_view_requires_login(self):
        """Verificar que requiere autenticación"""
        response = self.client.get(
            reverse('core:recycle_bin_detail', args=[self.recycle_entry.id])
        )
        self.assertEqual(response.status_code, 302)
    
    def test_detail_view_shows_entry_info(self):
        """Verificar que muestra información del elemento"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(
            reverse('core:recycle_bin_detail', args=[self.recycle_entry.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Oficina Test')
        self.assertContains(response, 'Test deletion')
    
    def test_detail_view_shows_original_data(self):
        """Verificar que muestra datos originales"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(
            reverse('core:recycle_bin_detail', args=[self.recycle_entry.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Vista Previa de Datos')


@pytest.mark.django_db
class TestRecycleBinRestoreView(TestCase):
    """Tests para RestoreView"""
    
    def setUp(self):
        """Configuración inicial"""
        self.client = Client()
        
        self.admin_user = User.objects.create_user(
            username='admin',
            password='admin123'
        )
        self.admin_user.profile.role = 'administrador'
        self.admin_user.profile.save()
        
        self.oficina = Oficina.objects.create(
            codigo='TEST001',
            nombre='Oficina Test',
            direccion='Test',
            telefono='123',
            estado=True,
            created_by=self.admin_user
        )
        
        success, message, self.recycle_entry = RecycleBinService.soft_delete_object(
            self.oficina,
            self.admin_user,
            'Test deletion'
        )
    
    def test_restore_requires_post(self):
        """Verificar que solo acepta POST"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(
            reverse('core:recycle_bin_restore', args=[self.recycle_entry.id])
        )
        self.assertEqual(response.status_code, 405)  # Method not allowed
    
    def test_restore_successful(self):
        """Verificar restauración exitosa"""
        self.client.login(username='admin', password='admin123')
        response = self.client.post(
            reverse('core:recycle_bin_restore', args=[self.recycle_entry.id])
        )
        
        # Verificar redirección
        self.assertEqual(response.status_code, 302)
        
        # Verificar que el objeto fue restaurado
        self.oficina.refresh_from_db()
        self.assertFalse(self.oficina.is_deleted)
        
        # Verificar que la entrada fue marcada como restaurada
        self.recycle_entry.refresh_from_db()
        self.assertTrue(self.recycle_entry.is_restored)
    
    def test_restore_without_permissions(self):
        """Verificar que usuarios sin permisos no pueden restaurar"""
        other_user = User.objects.create_user(
            username='other',
            password='other123'
        )
        other_user.profile.role = 'funcionario'
        other_user.profile.save()
        
        self.client.login(username='other', password='other123')
        response = self.client.post(
            reverse('core:recycle_bin_restore', args=[self.recycle_entry.id])
        )
        
        # Debería redirigir con mensaje de error
        self.assertEqual(response.status_code, 302)
        
        # Verificar que el objeto NO fue restaurado
        self.oficina.refresh_from_db()
        self.assertTrue(self.oficina.is_deleted)


@pytest.mark.django_db
class TestRecycleBinBulkRestoreView(TestCase):
    """Tests para BulkRestoreView"""
    
    def setUp(self):
        """Configuración inicial"""
        self.client = Client()
        
        self.admin_user = User.objects.create_user(
            username='admin',
            password='admin123'
        )
        self.admin_user.profile.role = 'administrador'
        self.admin_user.profile.save()
        
        # Crear y eliminar múltiples oficinas
        self.entries = []
        for i in range(3):
            oficina = Oficina.objects.create(
                codigo=f'TEST{i:03d}',
                nombre=f'Oficina {i}',
                direccion='Test',
                telefono='123',
                estado=True,
                created_by=self.admin_user
            )
            success, message, entry = RecycleBinService.soft_delete_object(
                oficina,
                self.admin_user,
                'Test'
            )
            self.entries.append(entry)
    
    def test_bulk_restore_successful(self):
        """Verificar restauración en lote exitosa"""
        self.client.login(username='admin', password='admin123')
        
        entry_ids = [str(entry.id) for entry in self.entries]
        response = self.client.post(
            reverse('core:recycle_bin_bulk_restore'),
            {'entry_ids[]': entry_ids}
        )
        
        self.assertEqual(response.status_code, 302)
        
        # Verificar que todos fueron restaurados
        for entry in self.entries:
            entry.refresh_from_db()
            self.assertTrue(entry.is_restored)
    
    def test_bulk_restore_empty_selection(self):
        """Verificar manejo de selección vacía"""
        self.client.login(username='admin', password='admin123')
        response = self.client.post(
            reverse('core:recycle_bin_bulk_restore'),
            {'entry_ids[]': []}
        )
        self.assertEqual(response.status_code, 302)


@pytest.mark.django_db
class TestRecycleBinPermanentDeleteView(TestCase):
    """Tests para eliminación permanente"""
    
    def setUp(self):
        """Configuración inicial"""
        self.client = Client()
        
        self.admin_user = User.objects.create_user(
            username='admin',
            password='admin123'
        )
        self.admin_user.profile.role = 'administrador'
        self.admin_user.profile.save()
        
        self.oficina = Oficina.objects.create(
            codigo='TEST001',
            nombre='Oficina Test',
            direccion='Test',
            telefono='123',
            estado=True,
            created_by=self.admin_user
        )
        
        success, message, self.recycle_entry = RecycleBinService.soft_delete_object(
            self.oficina,
            self.admin_user,
            'Test'
        )
    
    def test_permanent_delete_requires_admin(self):
        """Verificar que solo administradores pueden eliminar permanentemente"""
        regular_user = User.objects.create_user(
            username='user',
            password='user123'
        )
        regular_user.profile.role = 'funcionario'
        regular_user.profile.save()
        
        self.client.login(username='user', password='user123')
        response = self.client.post(
            reverse('core:recycle_bin_permanent_delete', args=[self.recycle_entry.id]),
            {'security_code': 'test'}
        )
        
        self.assertEqual(response.status_code, 302)
        
        # Verificar que el objeto NO fue eliminado
        self.assertTrue(RecycleBin.objects.filter(id=self.recycle_entry.id).exists())
    
    def test_permanent_delete_requires_security_code(self):
        """Verificar que requiere código de seguridad"""
        self.client.login(username='admin', password='admin123')
        response = self.client.post(
            reverse('core:recycle_bin_permanent_delete', args=[self.recycle_entry.id]),
            {}
        )
        
        self.assertEqual(response.status_code, 302)
        
        # Verificar que el objeto NO fue eliminado
        self.assertTrue(RecycleBin.objects.filter(id=self.recycle_entry.id).exists())


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
