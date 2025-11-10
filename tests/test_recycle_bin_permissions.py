"""
Tests para el sistema de permisos granular de la papelera de reciclaje.

Este módulo prueba:
- Permisos específicos por rol (administrador, funcionario, auditor)
- Segregación de datos por usuario
- Validaciones de permisos en vistas
- Grupos de permisos por rol
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from apps.core.models import (
    UserProfile, RecycleBin, RecycleBinConfig, 
    DeletionAuditLog, SecurityCodeAttempt
)
from apps.oficinas.models import Oficina
from apps.bienes.models import BienPatrimonial
from apps.catalogo.models import Catalogo


class RecycleBinPermissionsTestCase(TestCase):
    """
    Tests para permisos del sistema de papelera de reciclaje
    """
    
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
            email='funcionario@test.com'
        )
        self.funcionario_user.profile.role = 'funcionario'
        self.funcionario_user.profile.save()
        
        self.auditor_user = User.objects.create_user(
            username='auditor',
            password='audit123',
            email='auditor@test.com'
        )
        self.auditor_user.profile.role = 'auditor'
        self.auditor_user.profile.save()
        
        self.consulta_user = User.objects.create_user(
            username='consulta',
            password='cons123',
            email='consulta@test.com'
        )
        self.consulta_user.profile.role = 'consulta'
        self.consulta_user.profile.save()
        
        # Crear oficina de prueba
        self.oficina = Oficina.objects.create(
            codigo='OF001',
            nombre='Oficina Test',
            direccion='Dirección Test',
            telefono='123456789',
            estado=True,
            created_by=self.admin_user
        )
        
        # Crear entrada en papelera
        self.oficina.soft_delete(user=self.funcionario_user, reason='Test deletion')
        self.recycle_entry = RecycleBin.objects.create(
            content_object=self.oficina,
            object_repr=str(self.oficina),
            module_name='oficinas',
            deleted_by=self.funcionario_user,
            deletion_reason='Test deletion',
            auto_delete_at=timezone.now() + timedelta(days=30)
        )
        
        # Cliente para requests
        self.client = Client()
    
    # ========================================================================
    # TESTS DE PERMISOS EN USERPROFILE
    # ========================================================================
    
    def test_admin_has_all_recycle_permissions(self):
        """Administrador debe tener todos los permisos de papelera"""
        profile = self.admin_user.profile
        
        self.assertTrue(profile.can_view_recycle_bin())
        self.assertTrue(profile.can_view_all_recycle_items())
        self.assertTrue(profile.can_restore_items())
        self.assertTrue(profile.can_restore_own_items())
        self.assertTrue(profile.can_restore_others_items())
        self.assertTrue(profile.can_permanent_delete())
        self.assertTrue(profile.can_view_deletion_audit_logs())
        self.assertTrue(profile.can_manage_recycle_config())
        self.assertTrue(profile.can_bulk_restore())
        self.assertTrue(profile.can_bulk_permanent_delete())
    
    def test_funcionario_has_limited_permissions(self):
        """Funcionario debe tener permisos limitados"""
        profile = self.funcionario_user.profile
        
        # Permisos que debe tener
        self.assertTrue(profile.can_view_recycle_bin())
        self.assertTrue(profile.can_restore_items())
        self.assertTrue(profile.can_restore_own_items())
        self.assertTrue(profile.can_bulk_restore())
        
        # Permisos que NO debe tener
        self.assertFalse(profile.can_view_all_recycle_items())
        self.assertFalse(profile.can_restore_others_items())
        self.assertFalse(profile.can_permanent_delete())
        self.assertFalse(profile.can_manage_recycle_config())
        self.assertFalse(profile.can_bulk_permanent_delete())
    
    def test_auditor_has_view_only_permissions(self):
        """Auditor debe tener permisos de solo visualización"""
        profile = self.auditor_user.profile
        
        # Permisos que debe tener
        self.assertTrue(profile.can_view_recycle_bin())
        self.assertTrue(profile.can_view_all_recycle_items())
        self.assertTrue(profile.can_view_deletion_audit_logs())
        
        # Permisos que NO debe tener
        self.assertFalse(profile.can_restore_items())
        self.assertFalse(profile.can_restore_own_items())
        self.assertFalse(profile.can_restore_others_items())
        self.assertFalse(profile.can_permanent_delete())
        self.assertFalse(profile.can_manage_recycle_config())
        self.assertFalse(profile.can_bulk_restore())
        self.assertFalse(profile.can_bulk_permanent_delete())
    
    def test_consulta_has_no_recycle_permissions(self):
        """Usuario de consulta no debe tener permisos de papelera"""
        profile = self.consulta_user.profile
        
        self.assertFalse(profile.can_view_recycle_bin())
        self.assertFalse(profile.can_view_all_recycle_items())
        self.assertFalse(profile.can_restore_items())
        self.assertFalse(profile.can_restore_own_items())
        self.assertFalse(profile.can_restore_others_items())
        self.assertFalse(profile.can_permanent_delete())
        self.assertFalse(profile.can_view_deletion_audit_logs())
        self.assertFalse(profile.can_manage_recycle_config())
        self.assertFalse(profile.can_bulk_restore())
        self.assertFalse(profile.can_bulk_permanent_delete())
    
    def test_inactive_user_has_no_permissions(self):
        """Usuario inactivo no debe tener permisos"""
        self.admin_user.profile.is_active = False
        self.admin_user.profile.save()
        
        profile = self.admin_user.profile
        
        self.assertFalse(profile.can_view_recycle_bin())
        self.assertFalse(profile.can_restore_items())
        self.assertFalse(profile.can_permanent_delete())
    
    # ========================================================================
    # TESTS DE SEGREGACIÓN DE DATOS
    # ========================================================================
    
    def test_admin_can_view_all_entries(self):
        """Administrador puede ver todas las entradas en papelera"""
        self.client.login(username='admin', password='admin123')
        
        response = self.client.get(reverse('core:recycle_bin_list'))
        self.assertEqual(response.status_code, 200)
        
        # Debe ver la entrada creada por funcionario
        self.assertIn(self.recycle_entry, response.context['page_obj'])
    
    def test_funcionario_can_only_view_own_entries(self):
        """Funcionario solo puede ver sus propias entradas"""
        # Crear otra entrada por admin
        oficina2 = Oficina.objects.create(
            codigo='OF002',
            nombre='Oficina Test 2',
            direccion='Dirección Test 2',
            telefono='987654321',
            estado=True,
            created_by=self.admin_user
        )
        oficina2.soft_delete(user=self.admin_user, reason='Admin deletion')
        admin_entry = RecycleBin.objects.create(
            content_object=oficina2,
            object_repr=str(oficina2),
            module_name='oficinas',
            deleted_by=self.admin_user,
            deletion_reason='Admin deletion',
            auto_delete_at=timezone.now() + timedelta(days=30)
        )
        
        self.client.login(username='funcionario', password='func123')
        
        response = self.client.get(reverse('core:recycle_bin_list'))
        self.assertEqual(response.status_code, 200)
        
        # Debe ver solo su propia entrada
        entries = list(response.context['page_obj'])
        self.assertIn(self.recycle_entry, entries)
        self.assertNotIn(admin_entry, entries)
    
    def test_auditor_can_view_all_entries(self):
        """Auditor puede ver todas las entradas"""
        self.client.login(username='auditor', password='audit123')
        
        response = self.client.get(reverse('core:recycle_bin_list'))
        self.assertEqual(response.status_code, 200)
        
        # Debe ver la entrada
        self.assertIn(self.recycle_entry, response.context['page_obj'])
    
    def test_consulta_cannot_access_recycle_bin(self):
        """Usuario de consulta no puede acceder a la papelera"""
        self.client.login(username='consulta', password='cons123')
        
        response = self.client.get(reverse('core:recycle_bin_list'))
        # Debe redirigir por falta de permisos
        self.assertEqual(response.status_code, 302)
    
    # ========================================================================
    # TESTS DE PERMISOS EN VISTAS
    # ========================================================================
    
    def test_recycle_bin_list_requires_permission(self):
        """Vista de lista requiere permiso can_view_recycle_bin"""
        # Sin login
        response = self.client.get(reverse('core:recycle_bin_list'))
        self.assertEqual(response.status_code, 302)  # Redirect a login
        
        # Con usuario sin permisos
        self.client.login(username='consulta', password='cons123')
        response = self.client.get(reverse('core:recycle_bin_list'))
        self.assertEqual(response.status_code, 302)  # Redirect por falta de permisos
        
        # Con usuario con permisos
        self.client.login(username='funcionario', password='func123')
        response = self.client.get(reverse('core:recycle_bin_list'))
        self.assertEqual(response.status_code, 200)
    
    def test_recycle_bin_detail_requires_permission(self):
        """Vista de detalle requiere permiso y segregación de datos"""
        url = reverse('core:recycle_bin_detail', args=[self.recycle_entry.id])
        
        # Sin login
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        
        # Con usuario sin permisos
        self.client.login(username='consulta', password='cons123')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        
        # Con funcionario (propietario)
        self.client.login(username='funcionario', password='func123')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        # Con admin (puede ver todo)
        self.client.login(username='admin', password='admin123')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
    
    def test_funcionario_cannot_view_others_entries(self):
        """Funcionario no puede ver entradas de otros usuarios"""
        # Crear entrada por admin
        oficina2 = Oficina.objects.create(
            codigo='OF002',
            nombre='Oficina Test 2',
            direccion='Dirección Test 2',
            telefono='987654321',
            estado=True,
            created_by=self.admin_user
        )
        oficina2.soft_delete(user=self.admin_user, reason='Admin deletion')
        admin_entry = RecycleBin.objects.create(
            content_object=oficina2,
            object_repr=str(oficina2),
            module_name='oficinas',
            deleted_by=self.admin_user,
            deletion_reason='Admin deletion',
            auto_delete_at=timezone.now() + timedelta(days=30)
        )
        
        self.client.login(username='funcionario', password='func123')
        url = reverse('core:recycle_bin_detail', args=[admin_entry.id])
        
        response = self.client.get(url)
        # Debe redirigir por falta de permisos
        self.assertEqual(response.status_code, 302)
    
    def test_restore_requires_permission(self):
        """Restauración requiere permiso can_restore_items"""
        url = reverse('core:recycle_bin_restore', args=[self.recycle_entry.id])
        
        # Sin login
        response = self.client.post(url, {'quick_restore': 'true'})
        self.assertEqual(response.status_code, 302)
        
        # Con auditor (sin permiso de restaurar)
        self.client.login(username='auditor', password='audit123')
        response = self.client.post(url, {'quick_restore': 'true'})
        self.assertEqual(response.status_code, 302)
        
        # Con funcionario (propietario, con permiso)
        self.client.login(username='funcionario', password='func123')
        response = self.client.post(url, {'quick_restore': 'true'})
        # Debe procesar (puede redirigir después)
        self.assertIn(response.status_code, [200, 302])
    
    def test_funcionario_cannot_restore_others_items(self):
        """Funcionario no puede restaurar elementos de otros"""
        # Crear entrada por admin
        oficina2 = Oficina.objects.create(
            codigo='OF002',
            nombre='Oficina Test 2',
            direccion='Dirección Test 2',
            telefono='987654321',
            estado=True,
            created_by=self.admin_user
        )
        oficina2.soft_delete(user=self.admin_user, reason='Admin deletion')
        admin_entry = RecycleBin.objects.create(
            content_object=oficina2,
            object_repr=str(oficina2),
            module_name='oficinas',
            deleted_by=self.admin_user,
            deletion_reason='Admin deletion',
            auto_delete_at=timezone.now() + timedelta(days=30)
        )
        
        self.client.login(username='funcionario', password='func123')
        url = reverse('core:recycle_bin_restore', args=[admin_entry.id])
        
        response = self.client.post(url, {'quick_restore': 'true'})
        # Debe redirigir por falta de permisos
        self.assertEqual(response.status_code, 302)
    
    def test_admin_can_restore_others_items(self):
        """Administrador puede restaurar elementos de otros"""
        self.client.login(username='admin', password='admin123')
        url = reverse('core:recycle_bin_restore', args=[self.recycle_entry.id])
        
        response = self.client.post(url, {'quick_restore': 'true'})
        # Debe procesar
        self.assertIn(response.status_code, [200, 302])
    
    def test_permanent_delete_requires_admin(self):
        """Eliminación permanente requiere ser administrador"""
        url = reverse('core:recycle_bin_permanent_delete', args=[self.recycle_entry.id])
        
        # Con funcionario
        self.client.login(username='funcionario', password='func123')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        
        # Con auditor
        self.client.login(username='auditor', password='audit123')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        
        # Con admin
        self.client.login(username='admin', password='admin123')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
    
    def test_bulk_restore_requires_permission(self):
        """Restauración en lote requiere permiso can_bulk_restore"""
        url = reverse('core:recycle_bin_bulk_restore')
        data = {
            'entry_ids[]': [self.recycle_entry.id],
            'confirm': 'on'
        }
        
        # Con auditor (sin permiso)
        self.client.login(username='auditor', password='audit123')
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        
        # Con funcionario (con permiso)
        self.client.login(username='funcionario', password='func123')
        response = self.client.post(url, data)
        # Debe procesar
        self.assertIn(response.status_code, [200, 302])
    
    def test_bulk_permanent_delete_requires_admin(self):
        """Eliminación permanente en lote requiere ser administrador"""
        url = reverse('core:recycle_bin_bulk_permanent_delete')
        data = {
            'entry_ids[]': [self.recycle_entry.id],
            'security_code': 'test_code',
            'confirm': 'on'
        }
        
        # Con funcionario
        self.client.login(username='funcionario', password='func123')
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        
        # Con admin
        self.client.login(username='admin', password='admin123')
        response = self.client.post(url, data)
        # Debe procesar (aunque el código sea incorrecto)
        self.assertIn(response.status_code, [200, 302])
    
    # ========================================================================
    # TESTS DE PERMISOS EN CONTEXTO DE TEMPLATES
    # ========================================================================
    
    def test_list_view_provides_user_permissions_context(self):
        """Vista de lista debe proporcionar permisos del usuario en contexto"""
        self.client.login(username='funcionario', password='func123')
        
        response = self.client.get(reverse('core:recycle_bin_list'))
        self.assertEqual(response.status_code, 200)
        
        # Verificar que el contexto incluye permisos
        self.assertIn('user_permissions', response.context)
        perms = response.context['user_permissions']
        
        # Verificar permisos específicos
        self.assertFalse(perms['can_view_all'])
        self.assertTrue(perms['can_restore_items'])
        self.assertTrue(perms['can_restore_own'])
        self.assertFalse(perms['can_restore_others'])
        self.assertFalse(perms['can_permanent_delete'])
        self.assertTrue(perms['can_bulk_restore'])
        self.assertFalse(perms['can_bulk_delete'])
    
    def test_detail_view_provides_user_permissions_context(self):
        """Vista de detalle debe proporcionar permisos del usuario en contexto"""
        self.client.login(username='funcionario', password='func123')
        
        url = reverse('core:recycle_bin_detail', args=[self.recycle_entry.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        # Verificar que el contexto incluye permisos
        self.assertIn('user_permissions', response.context)
        perms = response.context['user_permissions']
        
        # Verificar permisos específicos
        self.assertTrue(perms['can_restore'])
        self.assertFalse(perms['can_permanent_delete'])
        self.assertFalse(perms['can_view_audit_logs'])
    
    # ========================================================================
    # TESTS DE GRUPOS DE PERMISOS POR ROL
    # ========================================================================
    
    def test_administrator_permission_group(self):
        """Grupo de permisos de administrador"""
        profile = self.admin_user.profile
        
        # Permisos de visualización
        self.assertTrue(profile.can_view_recycle_bin())
        self.assertTrue(profile.can_view_all_recycle_items())
        self.assertTrue(profile.can_view_deletion_audit_logs())
        
        # Permisos de restauración
        self.assertTrue(profile.can_restore_items())
        self.assertTrue(profile.can_restore_own_items())
        self.assertTrue(profile.can_restore_others_items())
        self.assertTrue(profile.can_bulk_restore())
        
        # Permisos de eliminación
        self.assertTrue(profile.can_permanent_delete())
        self.assertTrue(profile.can_bulk_permanent_delete())
        
        # Permisos de configuración
        self.assertTrue(profile.can_manage_recycle_config())
    
    def test_funcionario_permission_group(self):
        """Grupo de permisos de funcionario"""
        profile = self.funcionario_user.profile
        
        # Permisos de visualización (limitados)
        self.assertTrue(profile.can_view_recycle_bin())
        self.assertFalse(profile.can_view_all_recycle_items())
        self.assertFalse(profile.can_view_deletion_audit_logs())
        
        # Permisos de restauración (propios elementos)
        self.assertTrue(profile.can_restore_items())
        self.assertTrue(profile.can_restore_own_items())
        self.assertFalse(profile.can_restore_others_items())
        self.assertTrue(profile.can_bulk_restore())
        
        # Sin permisos de eliminación
        self.assertFalse(profile.can_permanent_delete())
        self.assertFalse(profile.can_bulk_permanent_delete())
        
        # Sin permisos de configuración
        self.assertFalse(profile.can_manage_recycle_config())
    
    def test_auditor_permission_group(self):
        """Grupo de permisos de auditor"""
        profile = self.auditor_user.profile
        
        # Permisos de visualización (completos)
        self.assertTrue(profile.can_view_recycle_bin())
        self.assertTrue(profile.can_view_all_recycle_items())
        self.assertTrue(profile.can_view_deletion_audit_logs())
        
        # Sin permisos de restauración
        self.assertFalse(profile.can_restore_items())
        self.assertFalse(profile.can_restore_own_items())
        self.assertFalse(profile.can_restore_others_items())
        self.assertFalse(profile.can_bulk_restore())
        
        # Sin permisos de eliminación
        self.assertFalse(profile.can_permanent_delete())
        self.assertFalse(profile.can_bulk_permanent_delete())
        
        # Sin permisos de configuración
        self.assertFalse(profile.can_manage_recycle_config())


class RecycleBinPermissionIntegrationTestCase(TestCase):
    """
    Tests de integración para permisos de papelera
    """
    
    def setUp(self):
        """Configuración inicial"""
        # Crear usuarios
        self.admin = User.objects.create_user(
            username='admin',
            password='admin123'
        )
        self.admin.profile.role = 'administrador'
        self.admin.profile.save()
        
        self.func1 = User.objects.create_user(
            username='func1',
            password='func123'
        )
        self.func1.profile.role = 'funcionario'
        self.func1.profile.save()
        
        self.func2 = User.objects.create_user(
            username='func2',
            password='func123'
        )
        self.func2.profile.role = 'funcionario'
        self.func2.profile.save()
        
        self.client = Client()
    
    def test_complete_workflow_with_permissions(self):
        """Test de flujo completo con validación de permisos"""
        # 1. Funcionario 1 crea y elimina una oficina
        oficina = Oficina.objects.create(
            codigo='OF001',
            nombre='Oficina Test',
            direccion='Dirección Test',
            telefono='123456789',
            estado=True,
            created_by=self.func1
        )
        oficina.soft_delete(user=self.func1, reason='Test')
        entry = RecycleBin.objects.get(object_id=oficina.id)
        
        # 2. Funcionario 2 no puede ver la entrada
        self.client.login(username='func2', password='func123')
        response = self.client.get(reverse('core:recycle_bin_list'))
        self.assertNotIn(entry, response.context['page_obj'])
        
        # 3. Funcionario 2 no puede restaurar la entrada
        url = reverse('core:recycle_bin_restore', args=[entry.id])
        response = self.client.post(url, {'quick_restore': 'true'})
        self.assertEqual(response.status_code, 302)
        
        # 4. Funcionario 1 puede ver y restaurar su entrada
        self.client.login(username='func1', password='func123')
        response = self.client.get(reverse('core:recycle_bin_list'))
        self.assertIn(entry, response.context['page_obj'])
        
        # 5. Admin puede ver todas las entradas
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('core:recycle_bin_list'))
        self.assertIn(entry, response.context['page_obj'])
        
        # 6. Admin puede restaurar cualquier entrada
        url = reverse('core:recycle_bin_restore', args=[entry.id])
        response = self.client.post(url, {'quick_restore': 'true'})
        self.assertIn(response.status_code, [200, 302])
