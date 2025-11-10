"""
Simple verification script for recycle bin views
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

from apps.core.models import RecycleBin, UserProfile
from apps.oficinas.models import Oficina
from apps.core.utils import RecycleBinService


class TestRecycleBinViewsSimple(TestCase):
    """Simple tests for recycle bin views"""
    
    def setUp(self):
        """Setup test data"""
        self.client = Client()
        
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin',
            password='admin123',
            email='admin@test.com'
        )
        self.admin_user.profile.role = 'administrador'
        self.admin_user.profile.save()
        
        # Create test office
        self.oficina = Oficina.objects.create(
            codigo='TEST001',
            nombre='Oficina Test',
            direccion='Test Address',
            telefono='123456',
            estado=True,
            created_by=self.admin_user
        )
        
        # Soft delete the office
        success, message, self.recycle_entry = RecycleBinService.soft_delete_object(
            self.oficina,
            self.admin_user,
            'Test deletion'
        )
    
    def test_recycle_bin_list_view_loads(self):
        """Test that the list view loads successfully"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('core:recycle_bin_list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/recycle_bin_list.html')
        print("✓ RecycleBinListView loads successfully")
    
    def test_recycle_bin_detail_view_loads(self):
        """Test that the detail view loads successfully"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(
            reverse('core:recycle_bin_detail', args=[self.recycle_entry.id])
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/recycle_bin_detail.html')
        print("✓ RecycleBinDetailView loads successfully")
    
    def test_recycle_bin_restore_works(self):
        """Test that restore functionality works"""
        self.client.login(username='admin', password='admin123')
        response = self.client.post(
            reverse('core:recycle_bin_restore', args=[self.recycle_entry.id])
        )
        
        # Should redirect after successful restore
        self.assertEqual(response.status_code, 302)
        
        # Verify object was restored
        self.oficina.refresh_from_db()
        self.assertFalse(self.oficina.is_deleted)
        
        # Verify entry was marked as restored
        self.recycle_entry.refresh_from_db()
        self.assertTrue(self.recycle_entry.is_restored)
        print("✓ Restore functionality works")
    
    def test_recycle_bin_bulk_restore_works(self):
        """Test that bulk restore works"""
        # Create another office and delete it
        oficina2 = Oficina.objects.create(
            codigo='TEST002',
            nombre='Oficina Test 2',
            direccion='Test',
            telefono='123',
            estado=True,
            created_by=self.admin_user
        )
        success, message, entry2 = RecycleBinService.soft_delete_object(
            oficina2,
            self.admin_user,
            'Test'
        )
        
        self.client.login(username='admin', password='admin123')
        response = self.client.post(
            reverse('core:recycle_bin_bulk_restore'),
            {'entry_ids[]': [str(self.recycle_entry.id), str(entry2.id)]}
        )
        
        self.assertEqual(response.status_code, 302)
        
        # Verify both were restored
        self.recycle_entry.refresh_from_db()
        entry2.refresh_from_db()
        self.assertTrue(self.recycle_entry.is_restored)
        self.assertTrue(entry2.is_restored)
        print("✓ Bulk restore functionality works")


if __name__ == '__main__':
    import django
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'patrimonio.settings')
    django.setup()
    
    from django.test.utils import get_runner
    from django.conf import settings
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2, interactive=False, keepdb=False)
    failures = test_runner.run_tests(['tests.test_recycle_bin_views_simple'])
    
    if failures == 0:
        print("\n✅ All tests passed!")
    else:
        print(f"\n❌ {failures} test(s) failed")
