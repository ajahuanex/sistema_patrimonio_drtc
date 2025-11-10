"""
Tests para el sistema de filtros avanzados de la papelera de reciclaje
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from apps.core.models import RecycleBin, RecycleBinConfig, UserProfile
from apps.core.filters import RecycleBinFilterForm, RecycleBinQuickFilters
from apps.oficinas.models import Oficina
from apps.bienes.models import BienPatrimonial
from apps.catalogo.models import Catalogo
from django.contrib.contenttypes.models import ContentType


class RecycleBinFilterFormTest(TestCase):
    """Tests para el formulario de filtros de papelera"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        # Crear usuarios
        self.admin_user = User.objects.create_user(
            username='admin',
            password='admin123',
            email='admin@test.com'
        )
        self.admin_user.profile.role = 'administrador'
        self.admin_user.profile.save()
        
        self.regular_user = User.objects.create_user(
            username='user1',
            password='user123',
            email='user1@test.com'
        )
        self.regular_user.profile.role = 'funcionario'
        self.regular_user.profile.save()
        
        # Crear oficina de prueba
        self.oficina = Oficina.objects.create(
            codigo='OF001',
            nombre='Oficina Test',
            direccion='Dirección Test',
            telefono='123456',
            estado=True,
            created_by=self.admin_user
        )
        
        # Crear entradas en papelera con diferentes características
        now = timezone.now()
        
        # Entrada 1: Oficina eliminada hace 5 días, expira en 25 días
        self.entry1 = RecycleBin.objects.create(
            content_type=ContentType.objects.get_for_model(Oficina),
            object_id=self.oficina.id,
            object_repr='Oficina Test 1',
            module_name='oficinas',
            deleted_by=self.admin_user,
            deletion_reason='Test reason 1',
            deleted_at=now - timedelta(days=5),
            auto_delete_at=now + timedelta(days=25)
        )
        
        # Entrada 2: Bien eliminado hace 10 días, expira en 2 días (crítico)
        self.entry2 = RecycleBin.objects.create(
            content_type=ContentType.objects.get_for_model(Oficina),
            object_id=999,
            object_repr='Bien Test 1',
            module_name='bienes',
            deleted_by=self.regular_user,
            deletion_reason='Test reason 2',
            deleted_at=now - timedelta(days=10),
            auto_delete_at=now + timedelta(days=2)
        )
        
        # Entrada 3: Catálogo eliminado hace 1 día, expira en 6 días (advertencia)
        self.entry3 = RecycleBin.objects.create(
            content_type=ContentType.objects.get_for_model(Oficina),
            object_id=998,
            object_repr='Catálogo Test 1',
            module_name='catalogo',
            deleted_by=self.admin_user,
            deletion_reason='Test reason 3',
            deleted_at=now - timedelta(days=1),
            auto_delete_at=now + timedelta(days=6)
        )
        
        # Entrada 4: Elemento expirado (listo para eliminar)
        self.entry4 = RecycleBin.objects.create(
            content_type=ContentType.objects.get_for_model(Oficina),
            object_id=997,
            object_repr='Elemento Expirado',
            module_name='oficinas',
            deleted_by=self.regular_user,
            deletion_reason='Test reason 4',
            deleted_at=now - timedelta(days=31),
            auto_delete_at=now - timedelta(days=1)
        )
        
        # Entrada 5: Elemento restaurado
        self.entry5 = RecycleBin.objects.create(
            content_type=ContentType.objects.get_for_model(Oficina),
            object_id=996,
            object_repr='Elemento Restaurado',
            module_name='bienes',
            deleted_by=self.admin_user,
            deletion_reason='Test reason 5',
            deleted_at=now - timedelta(days=3),
            auto_delete_at=now + timedelta(days=27),
            restored_at=now - timedelta(days=1),
            restored_by=self.admin_user
        )
    
    def test_filter_by_module(self):
        """Test filtro por módulo"""
        form_data = {'module': 'oficinas'}
        form = RecycleBinFilterForm(data=form_data)
        
        self.assertTrue(form.is_valid())
        
        queryset = RecycleBin.objects.all()
        filtered = form.apply_filters(queryset, self.admin_user)
        
        self.assertEqual(filtered.count(), 2)  # entry1 y entry4
        for entry in filtered:
            self.assertEqual(entry.module_name, 'oficinas')
    
    def test_filter_by_search(self):
        """Test filtro por búsqueda de texto"""
        form_data = {'search': 'Bien Test'}
        form = RecycleBinFilterForm(data=form_data)
        
        self.assertTrue(form.is_valid())
        
        queryset = RecycleBin.objects.all()
        filtered = form.apply_filters(queryset, self.admin_user)
        
        self.assertEqual(filtered.count(), 1)
        self.assertEqual(filtered.first().object_repr, 'Bien Test 1')
    
    def test_filter_by_date_range(self):
        """Test filtro por rango de fechas"""
        now = timezone.now()
        date_from = (now - timedelta(days=6)).date()
        date_to = (now - timedelta(days=1)).date()
        
        form_data = {
            'date_from': date_from,
            'date_to': date_to
        }
        form = RecycleBinFilterForm(data=form_data)
        
        self.assertTrue(form.is_valid())
        
        queryset = RecycleBin.objects.all()
        filtered = form.apply_filters(queryset, self.admin_user)
        
        # Debería incluir entry1 (5 días), entry2 (10 días no), entry3 (1 día), entry5 (3 días)
        self.assertGreaterEqual(filtered.count(), 2)
    
    def test_filter_by_deleted_by(self):
        """Test filtro por usuario que eliminó"""
        form_data = {'deleted_by': 'admin'}
        form = RecycleBinFilterForm(data=form_data)
        
        self.assertTrue(form.is_valid())
        
        queryset = RecycleBin.objects.all()
        filtered = form.apply_filters(queryset, self.admin_user)
        
        self.assertEqual(filtered.count(), 3)  # entry1, entry3, entry5
        for entry in filtered:
            self.assertEqual(entry.deleted_by, self.admin_user)
    
    def test_filter_by_time_remaining_expired(self):
        """Test filtro por tiempo restante - expirados"""
        form_data = {'time_remaining': 'expired'}
        form = RecycleBinFilterForm(data=form_data)
        
        self.assertTrue(form.is_valid())
        
        queryset = RecycleBin.objects.all()
        filtered = form.apply_filters(queryset, self.admin_user)
        
        self.assertEqual(filtered.count(), 1)
        self.assertEqual(filtered.first().object_repr, 'Elemento Expirado')
    
    def test_filter_by_time_remaining_critical(self):
        """Test filtro por tiempo restante - crítico (1-3 días)"""
        form_data = {'time_remaining': 'critical'}
        form = RecycleBinFilterForm(data=form_data)
        
        self.assertTrue(form.is_valid())
        
        queryset = RecycleBin.objects.all()
        filtered = form.apply_filters(queryset, self.admin_user)
        
        self.assertEqual(filtered.count(), 1)
        self.assertEqual(filtered.first().object_repr, 'Bien Test 1')
    
    def test_filter_by_time_remaining_warning(self):
        """Test filtro por tiempo restante - advertencia (4-7 días)"""
        form_data = {'time_remaining': 'warning'}
        form = RecycleBinFilterForm(data=form_data)
        
        self.assertTrue(form.is_valid())
        
        queryset = RecycleBin.objects.all()
        filtered = form.apply_filters(queryset, self.admin_user)
        
        self.assertEqual(filtered.count(), 1)
        self.assertEqual(filtered.first().object_repr, 'Catálogo Test 1')
    
    def test_filter_by_time_remaining_safe(self):
        """Test filtro por tiempo restante - seguro (más de 14 días)"""
        form_data = {'time_remaining': 'safe'}
        form = RecycleBinFilterForm(data=form_data)
        
        self.assertTrue(form.is_valid())
        
        queryset = RecycleBin.objects.all()
        filtered = form.apply_filters(queryset, self.admin_user)
        
        self.assertEqual(filtered.count(), 1)
        self.assertEqual(filtered.first().object_repr, 'Oficina Test 1')
    
    def test_filter_by_status_active(self):
        """Test filtro por estado - en papelera"""
        form_data = {'status': 'active'}
        form = RecycleBinFilterForm(data=form_data)
        
        self.assertTrue(form.is_valid())
        
        queryset = RecycleBin.objects.all()
        filtered = form.apply_filters(queryset, self.admin_user)
        
        self.assertEqual(filtered.count(), 4)  # Todos excepto el restaurado
        for entry in filtered:
            self.assertIsNone(entry.restored_at)
    
    def test_filter_by_status_restored(self):
        """Test filtro por estado - restaurados"""
        form_data = {'status': 'restored'}
        form = RecycleBinFilterForm(data=form_data)
        
        self.assertTrue(form.is_valid())
        
        queryset = RecycleBin.objects.all()
        filtered = form.apply_filters(queryset, self.admin_user)
        
        self.assertEqual(filtered.count(), 1)
        self.assertEqual(filtered.first().object_repr, 'Elemento Restaurado')
    
    def test_multiple_filters_combined(self):
        """Test combinación de múltiples filtros"""
        form_data = {
            'module': 'oficinas',
            'deleted_by': 'admin',
            'status': 'active'
        }
        form = RecycleBinFilterForm(data=form_data)
        
        self.assertTrue(form.is_valid())
        
        queryset = RecycleBin.objects.all()
        filtered = form.apply_filters(queryset, self.admin_user)
        
        self.assertEqual(filtered.count(), 1)
        self.assertEqual(filtered.first().object_repr, 'Oficina Test 1')
    
    def test_get_active_filters_count(self):
        """Test contador de filtros activos"""
        form_data = {
            'module': 'oficinas',
            'search': 'test',
            'time_remaining': 'critical'
        }
        form = RecycleBinFilterForm(data=form_data)
        
        self.assertTrue(form.is_valid())
        
        count = form.get_active_filters_count()
        self.assertEqual(count, 3)
    
    def test_get_active_filters_summary(self):
        """Test resumen de filtros activos"""
        form_data = {
            'module': 'oficinas',
            'search': 'test'
        }
        form = RecycleBinFilterForm(data=form_data)
        
        self.assertTrue(form.is_valid())
        
        summary = form.get_active_filters_summary()
        self.assertEqual(len(summary), 2)
        self.assertIn(('Módulo', 'Oficinas'), summary)
        self.assertIn(('Búsqueda', 'test'), summary)


class RecycleBinQuickFiltersTest(TestCase):
    """Tests para filtros rápidos de papelera"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        self.user = User.objects.create_user(
            username='testuser',
            password='test123'
        )
        
        now = timezone.now()
        
        # Crear entradas de prueba
        self.expiring_soon = RecycleBin.objects.create(
            content_type=ContentType.objects.get_for_model(Oficina),
            object_id=1,
            object_repr='Expiring Soon',
            module_name='oficinas',
            deleted_by=self.user,
            deleted_at=now,
            auto_delete_at=now + timedelta(days=5)
        )
        
        self.expired = RecycleBin.objects.create(
            content_type=ContentType.objects.get_for_model(Oficina),
            object_id=2,
            object_repr='Expired',
            module_name='oficinas',
            deleted_by=self.user,
            deleted_at=now - timedelta(days=31),
            auto_delete_at=now - timedelta(days=1)
        )
        
        self.safe = RecycleBin.objects.create(
            content_type=ContentType.objects.get_for_model(Oficina),
            object_id=3,
            object_repr='Safe',
            module_name='bienes',
            deleted_by=self.user,
            deleted_at=now,
            auto_delete_at=now + timedelta(days=20)
        )
    
    def test_get_expiring_soon(self):
        """Test filtro rápido de elementos próximos a expirar"""
        queryset = RecycleBin.objects.all()
        filtered = RecycleBinQuickFilters.get_expiring_soon(queryset)
        
        self.assertEqual(filtered.count(), 1)
        self.assertEqual(filtered.first().object_repr, 'Expiring Soon')
    
    def test_get_expired(self):
        """Test filtro rápido de elementos expirados"""
        queryset = RecycleBin.objects.all()
        filtered = RecycleBinQuickFilters.get_expired(queryset)
        
        self.assertEqual(filtered.count(), 1)
        self.assertEqual(filtered.first().object_repr, 'Expired')
    
    def test_get_by_user(self):
        """Test filtro rápido por usuario"""
        queryset = RecycleBin.objects.all()
        filtered = RecycleBinQuickFilters.get_by_user(queryset, self.user)
        
        self.assertEqual(filtered.count(), 3)
    
    def test_get_by_module(self):
        """Test filtro rápido por módulo"""
        queryset = RecycleBin.objects.all()
        filtered = RecycleBinQuickFilters.get_by_module(queryset, 'oficinas')
        
        self.assertEqual(filtered.count(), 2)
    
    def test_get_recently_deleted(self):
        """Test filtro rápido de elementos eliminados recientemente"""
        queryset = RecycleBin.objects.all()
        filtered = RecycleBinQuickFilters.get_recently_deleted(queryset, days=7)
        
        self.assertEqual(filtered.count(), 2)  # expiring_soon y safe


class RecycleBinFilterViewTest(TestCase):
    """Tests para las vistas con filtros de papelera"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        self.client = Client()
        
        # Crear usuario administrador
        self.admin_user = User.objects.create_user(
            username='admin',
            password='admin123'
        )
        self.admin_user.profile.role = 'administrador'
        self.admin_user.profile.save()
        
        # Crear entradas de prueba
        now = timezone.now()
        
        self.entry1 = RecycleBin.objects.create(
            content_type=ContentType.objects.get_for_model(Oficina),
            object_id=1,
            object_repr='Test Entry 1',
            module_name='oficinas',
            deleted_by=self.admin_user,
            deleted_at=now,
            auto_delete_at=now + timedelta(days=30)
        )
        
        self.entry2 = RecycleBin.objects.create(
            content_type=ContentType.objects.get_for_model(Oficina),
            object_id=2,
            object_repr='Test Entry 2',
            module_name='bienes',
            deleted_by=self.admin_user,
            deleted_at=now,
            auto_delete_at=now + timedelta(days=2)
        )
    
    def test_recycle_bin_list_view_with_filters(self):
        """Test vista de lista con filtros aplicados"""
        self.client.login(username='admin', password='admin123')
        
        response = self.client.get('/core/recycle-bin/', {
            'module': 'oficinas',
            'time_remaining': 'safe'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('filter_form', response.context)
        self.assertIn('active_filters_count', response.context)
        self.assertGreater(response.context['active_filters_count'], 0)
    
    def test_recycle_bin_list_view_quick_filters(self):
        """Test vista de lista con filtros rápidos"""
        self.client.login(username='admin', password='admin123')
        
        response = self.client.get('/core/recycle-bin/', {
            'time_remaining': 'critical'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('quick_filters', response.context)
    
    def test_filter_form_validation_in_view(self):
        """Test validación del formulario de filtros en la vista"""
        self.client.login(username='admin', password='admin123')
        
        # Datos válidos
        response = self.client.get('/core/recycle-bin/', {
            'module': 'oficinas',
            'search': 'test'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['filter_form'].is_valid())
    
    def test_pagination_preserves_filters(self):
        """Test que la paginación preserve los filtros"""
        self.client.login(username='admin', password='admin123')
        
        # Crear más entradas para forzar paginación
        now = timezone.now()
        for i in range(25):
            RecycleBin.objects.create(
                content_type=ContentType.objects.get_for_model(Oficina),
                object_id=100 + i,
                object_repr=f'Entry {i}',
                module_name='oficinas',
                deleted_by=self.admin_user,
                deleted_at=now,
                auto_delete_at=now + timedelta(days=30)
            )
        
        response = self.client.get('/core/recycle-bin/', {
            'module': 'oficinas',
            'page': '2'
        })
        
        self.assertEqual(response.status_code, 200)
        # Verificar que el filtro se mantiene en la página 2
        self.assertIn('module', response.request.get('QUERY_STRING', ''))
