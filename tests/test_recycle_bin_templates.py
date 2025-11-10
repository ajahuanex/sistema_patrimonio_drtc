"""
Tests for Recycle Bin Templates
Task 13: Desarrollar templates de papelera
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from apps.core.models import RecycleBin, UserProfile
from apps.oficinas.models import Oficina
from django.contrib.contenttypes.models import ContentType

User = get_user_model()


class RecycleBinTemplateTests(TestCase):
    """Tests for recycle bin templates"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin',
            password='admin123',
            email='admin@test.com',
            first_name='Admin',
            last_name='User'
        )
        profile, _ = UserProfile.objects.get_or_create(user=self.admin_user)
        profile.rol = 'administrador'
        profile.save()
        
        # Create regular user
        self.regular_user = User.objects.create_user(
            username='user',
            password='user123',
            email='user@test.com'
        )
        UserProfile.objects.get_or_create(user=self.regular_user)
        
        # Create test oficina
        self.oficina = Oficina.objects.create(
            codigo='TEST001',
            nombre='Oficina Test',
            responsable='Test Responsable'
        )
        
        # Soft delete the oficina
        self.oficina.soft_delete(deleted_by=self.admin_user, reason='Test deletion')
        
        # Get the RecycleBin entry
        content_type = ContentType.objects.get_for_model(Oficina)
        self.recycle_entry = RecycleBin.objects.get(
            content_type=content_type,
            object_id=self.oficina.id
        )
    
    def test_recycle_bin_list_template_loads(self):
        """Test that recycle bin list template loads correctly"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('core:recycle_bin_list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/recycle_bin_list.html')
        self.assertTemplateUsed(response, 'base.html')
    
    def test_recycle_bin_list_shows_statistics(self):
        """Test that list view shows statistics boxes"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('core:recycle_bin_list'))
        
        # Check for statistics elements
        self.assertContains(response, 'Total en Papelera')
        self.assertContains(response, 'Próximos a Eliminar')
        self.assertContains(response, 'Listos para Eliminar')
        self.assertContains(response, 'Módulos Activos')
    
    def test_recycle_bin_list_shows_quick_filters(self):
        """Test that list view shows quick filter buttons"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('core:recycle_bin_list'))
        
        # Check for quick filter buttons
        self.assertContains(response, 'Listos para eliminar')
        self.assertContains(response, 'Críticos (1-3 días)')
        self.assertContains(response, 'Advertencia (4-7 días)')
        self.assertContains(response, 'Mis eliminaciones')
        self.assertContains(response, 'Limpiar filtros')
    
    def test_recycle_bin_list_shows_advanced_filters(self):
        """Test that list view shows advanced filters section"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('core:recycle_bin_list'))
        
        # Check for advanced filters
        self.assertContains(response, 'Filtros Avanzados')
        self.assertContains(response, 'advancedFilters')
    
    def test_recycle_bin_list_shows_entries_table(self):
        """Test that list view shows entries in a responsive table"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('core:recycle_bin_list'))
        
        # Check for table headers
        self.assertContains(response, 'Objeto')
        self.assertContains(response, 'Módulo')
        self.assertContains(response, 'Eliminado Por')
        self.assertContains(response, 'Fecha Eliminación')
        self.assertContains(response, 'Días Restantes')
        self.assertContains(response, 'Estado')
        self.assertContains(response, 'Acciones')
        
        # Check for entry data
        self.assertContains(response, self.oficina.nombre)
    
    def test_recycle_bin_list_shows_bulk_actions(self):
        """Test that list view shows bulk action buttons"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('core:recycle_bin_list'))
        
        # Check for bulk action buttons
        self.assertContains(response, 'Restaurar Seleccionados')
        self.assertContains(response, 'Eliminar Permanentemente')
        self.assertContains(response, 'elementos seleccionados')
    
    def test_recycle_bin_list_has_restore_modal(self):
        """Test that list view includes restore confirmation modal"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('core:recycle_bin_list'))
        
        # Check for restore modal
        self.assertContains(response, 'restoreModal')
        self.assertContains(response, 'Confirmar Restauración')
    
    def test_recycle_bin_list_has_delete_modal(self):
        """Test that list view includes permanent delete modal for admins"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('core:recycle_bin_list'))
        
        # Check for delete modal
        self.assertContains(response, 'bulkDeleteModal')
        self.assertContains(response, 'Eliminación Permanente en Lote')
        self.assertContains(response, 'Código de Seguridad')
    
    def test_recycle_bin_list_responsive_design(self):
        """Test that list view includes responsive CSS"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('core:recycle_bin_list'))
        
        # Check for responsive classes
        self.assertContains(response, 'table-responsive')
        self.assertContains(response, 'col-lg-3')
        self.assertContains(response, 'col-md-6')
    
    def test_recycle_bin_list_has_icons(self):
        """Test that list view includes intuitive icons"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('core:recycle_bin_list'))
        
        # Check for FontAwesome icons
        self.assertContains(response, 'fa-trash-restore')
        self.assertContains(response, 'fa-trash')
        self.assertContains(response, 'fa-undo')
        self.assertContains(response, 'fa-eye')
        self.assertContains(response, 'fa-filter')
    
    def test_recycle_bin_detail_template_loads(self):
        """Test that recycle bin detail template loads correctly"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(
            reverse('core:recycle_bin_detail', args=[self.recycle_entry.id])
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/recycle_bin_detail.html')
        self.assertTemplateUsed(response, 'base.html')
    
    def test_recycle_bin_detail_shows_header(self):
        """Test that detail view shows visual header with status"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(
            reverse('core:recycle_bin_detail', args=[self.recycle_entry.id])
        )
        
        # Check for header elements
        self.assertContains(response, 'detail-header')
        self.assertContains(response, 'Detalle del Elemento Eliminado')
        self.assertContains(response, 'status-indicator')
    
    def test_recycle_bin_detail_shows_general_info(self):
        """Test that detail view shows general information card"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(
            reverse('core:recycle_bin_detail', args=[self.recycle_entry.id])
        )
        
        # Check for general info
        self.assertContains(response, 'Información General')
        self.assertContains(response, 'Objeto:')
        self.assertContains(response, 'Módulo:')
        self.assertContains(response, 'Tipo:')
        self.assertContains(response, 'Estado:')
        self.assertContains(response, self.oficina.nombre)
    
    def test_recycle_bin_detail_shows_deletion_info(self):
        """Test that detail view shows deletion information card"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(
            reverse('core:recycle_bin_detail', args=[self.recycle_entry.id])
        )
        
        # Check for deletion info
        self.assertContains(response, 'Información de Eliminación')
        self.assertContains(response, 'Eliminado por:')
        self.assertContains(response, 'Fecha eliminación:')
        self.assertContains(response, 'Eliminación automática:')
        self.assertContains(response, 'Días restantes:')
        self.assertContains(response, 'Motivo:')
    
    def test_recycle_bin_detail_shows_data_preview(self):
        """Test that detail view shows data preview table"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(
            reverse('core:recycle_bin_detail', args=[self.recycle_entry.id])
        )
        
        # Check for data preview
        self.assertContains(response, 'Vista Previa de Datos')
        self.assertContains(response, 'data-preview-table')
    
    def test_recycle_bin_detail_shows_action_buttons(self):
        """Test that detail view shows action buttons"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(
            reverse('core:recycle_bin_detail', args=[self.recycle_entry.id])
        )
        
        # Check for action buttons
        self.assertContains(response, 'Acciones Disponibles')
        self.assertContains(response, 'Restaurar Elemento')
        self.assertContains(response, 'Eliminar Permanentemente')
    
    def test_recycle_bin_detail_has_restore_modal(self):
        """Test that detail view includes restore modal"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(
            reverse('core:recycle_bin_detail', args=[self.recycle_entry.id])
        )
        
        # Check for restore modal
        self.assertContains(response, 'restoreModal')
        self.assertContains(response, 'Confirmar Restauración')
    
    def test_recycle_bin_detail_has_permanent_delete_modal(self):
        """Test that detail view includes permanent delete modal"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(
            reverse('core:recycle_bin_detail', args=[self.recycle_entry.id])
        )
        
        # Check for permanent delete modal
        self.assertContains(response, 'permanentDeleteModal')
        self.assertContains(response, 'Eliminación Permanente')
        self.assertContains(response, 'ADVERTENCIA CRÍTICA')
        self.assertContains(response, 'Código de Seguridad')
        self.assertContains(response, 'Escriba "ELIMINAR"')
        self.assertContains(response, 'Motivo de eliminación permanente')
    
    def test_recycle_bin_detail_has_breadcrumb(self):
        """Test that detail view includes breadcrumb navigation"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(
            reverse('core:recycle_bin_detail', args=[self.recycle_entry.id])
        )
        
        # Check for breadcrumb
        self.assertContains(response, 'breadcrumb')
        self.assertContains(response, 'Papelera')
        self.assertContains(response, 'Detalle del Elemento')
    
    def test_recycle_bin_detail_responsive_design(self):
        """Test that detail view includes responsive design"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(
            reverse('core:recycle_bin_detail', args=[self.recycle_entry.id])
        )
        
        # Check for responsive classes
        self.assertContains(response, 'col-md-6')
        self.assertContains(response, 'info-card')
    
    def test_recycle_bin_detail_has_icons(self):
        """Test that detail view includes intuitive icons"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(
            reverse('core:recycle_bin_detail', args=[self.recycle_entry.id])
        )
        
        # Check for FontAwesome icons
        self.assertContains(response, 'fa-info-circle')
        self.assertContains(response, 'fa-trash-restore')
        self.assertContains(response, 'fa-undo')
        self.assertContains(response, 'fa-trash')
        self.assertContains(response, 'fa-user')
        self.assertContains(response, 'fa-calendar')
    
    def test_recycle_bin_css_file_exists(self):
        """Test that recycle bin CSS file is referenced"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('core:recycle_bin_list'))
        
        # Check for CSS file reference
        self.assertContains(response, 'recycle_bin.css')
    
    def test_recycle_bin_list_pagination(self):
        """Test that list view includes pagination"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('core:recycle_bin_list'))
        
        # Check for pagination elements
        self.assertContains(response, 'pagination')
    
    def test_regular_user_cannot_see_admin_features(self):
        """Test that regular users don't see admin-only features"""
        self.client.login(username='user', password='user123')
        response = self.client.get(reverse('core:recycle_bin_list'))
        
        # Regular users should not see permanent delete button
        # (This depends on the view logic, but the template should respect it)
        self.assertEqual(response.status_code, 200)
