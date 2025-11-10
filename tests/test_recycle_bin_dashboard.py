"""
Tests para el dashboard de estadísticas de la papelera de reciclaje.
Verifica la funcionalidad de visualización de estadísticas, gráficos y exportación de reportes.
"""

import json
from datetime import timedelta
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

from apps.core.models import UserProfile, RecycleBin, RecycleBinConfig, AuditLog
from apps.oficinas.models import Oficina
from apps.bienes.models import BienPatrimonial
from apps.catalogo.models import Catalogo


class RecycleBinDashboardTestCase(TestCase):
    """Tests para el dashboard de estadísticas de papelera"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        self.client = Client()
        
        # Crear usuarios
        self.admin_user = User.objects.create_user(
            username='admin',
            password='admin123',
            email='admin@test.com'
        )
        self.admin_profile = UserProfile.objects.create(
            user=self.admin_user,
            role='administrador'
        )
        
        self.regular_user = User.objects.create_user(
            username='user1',
            password='user123',
            email='user1@test.com'
        )
        self.regular_profile = UserProfile.objects.create(
            user=self.regular_user,
            role='funcionario'
        )
        
        self.other_user = User.objects.create_user(
            username='user2',
            password='user123',
            email='user2@test.com'
        )
        self.other_profile = UserProfile.objects.create(
            user=self.other_user,
            role='funcionario'
        )
        
        # Crear oficina de prueba
        self.oficina = Oficina.objects.create(
            codigo='OF001',
            nombre='Oficina Test',
            direccion='Test Address',
            telefono='123456789',
            estado=True
        )
        
        # Crear catálogo de prueba
        self.catalogo = Catalogo.objects.create(
            codigo='CAT001',
            nombre='Catálogo Test',
            descripcion='Test'
        )
        
        # Crear bien patrimonial de prueba
        self.bien = BienPatrimonial.objects.create(
            codigo_patrimonial='BP001',
            descripcion='Bien Test',
            catalogo=self.catalogo,
            oficina=self.oficina,
            estado='bueno',
            valor_adquisicion=1000.00
        )
        
        # Crear entradas en papelera con diferentes estados y fechas
        self._create_test_recycle_bin_entries()
    
    def _create_test_recycle_bin_entries(self):
        """Crea entradas de prueba en la papelera con diferentes estados"""
        now = timezone.now()
        
        # Entradas eliminadas por admin (5 oficinas, 3 bienes, 2 catálogos)
        for i in range(5):
            oficina = Oficina.objects.create(
                codigo=f'OF{i:03d}',
                nombre=f'Oficina {i}',
                direccion='Test',
                telefono='123456789',
                estado=True
            )
            RecycleBin.objects.create(
                content_type=ContentType.objects.get_for_model(Oficina),
                object_id=oficina.id,
                object_repr=oficina.nombre,
                module_name='oficinas',
                deleted_by=self.admin_user,
                deleted_at=now - timedelta(days=i),
                auto_delete_at=now + timedelta(days=30-i)
            )
        
        for i in range(3):
            bien = BienPatrimonial.objects.create(
                codigo_patrimonial=f'BP{i:03d}',
                descripcion=f'Bien {i}',
                catalogo=self.catalogo,
                oficina=self.oficina,
                estado='bueno',
                valor_adquisicion=1000.00
            )
            RecycleBin.objects.create(
                content_type=ContentType.objects.get_for_model(BienPatrimonial),
                object_id=bien.id,
                object_repr=bien.codigo_patrimonial,
                module_name='bienes',
                deleted_by=self.admin_user,
                deleted_at=now - timedelta(days=i+5),
                auto_delete_at=now + timedelta(days=25-i)
            )
        
        for i in range(2):
            catalogo = Catalogo.objects.create(
                codigo=f'CAT{i:03d}',
                nombre=f'Catálogo {i}',
                descripcion='Test'
            )
            RecycleBin.objects.create(
                content_type=ContentType.objects.get_for_model(Catalogo),
                object_id=catalogo.id,
                object_repr=catalogo.nombre,
                module_name='catalogo',
                deleted_by=self.admin_user,
                deleted_at=now - timedelta(days=i+8),
                auto_delete_at=now + timedelta(days=22-i)
            )
        
        # Entradas eliminadas por usuario regular (3 oficinas)
        for i in range(3):
            oficina = Oficina.objects.create(
                codigo=f'OFU{i:03d}',
                nombre=f'Oficina Usuario {i}',
                direccion='Test',
                telefono='123456789',
                estado=True
            )
            RecycleBin.objects.create(
                content_type=ContentType.objects.get_for_model(Oficina),
                object_id=oficina.id,
                object_repr=oficina.nombre,
                module_name='oficinas',
                deleted_by=self.regular_user,
                deleted_at=now - timedelta(days=i+10),
                auto_delete_at=now + timedelta(days=20-i)
            )
        
        # Entradas eliminadas por otro usuario (2 bienes)
        for i in range(2):
            bien = BienPatrimonial.objects.create(
                codigo_patrimonial=f'BPU{i:03d}',
                descripcion=f'Bien Usuario {i}',
                catalogo=self.catalogo,
                oficina=self.oficina,
                estado='bueno',
                valor_adquisicion=1000.00
            )
            RecycleBin.objects.create(
                content_type=ContentType.objects.get_for_model(BienPatrimonial),
                object_id=bien.id,
                object_repr=bien.codigo_patrimonial,
                module_name='bienes',
                deleted_by=self.other_user,
                deleted_at=now - timedelta(days=i+12),
                auto_delete_at=now + timedelta(days=18-i)
            )
        
        # Restaurar algunas entradas
        restored_entries = RecycleBin.objects.filter(deleted_by=self.admin_user)[:3]
        for entry in restored_entries:
            entry.restored_at = now - timedelta(days=2)
            entry.restored_by = self.admin_user
            entry.save()
        
        # Crear logs de eliminación permanente
        for i in range(2):
            AuditLog.objects.create(
                user=self.admin_user,
                action='permanent_delete',
                model_name='RecycleBin',
                object_id=str(i),
                object_repr=f'Deleted Entry {i}',
                created_at=now - timedelta(days=i+1)
            )
    
    def test_dashboard_access_admin(self):
        """Test que administrador puede acceder al dashboard"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('core:recycle_bin_dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/recycle_bin_dashboard.html')
        self.assertTrue(response.context['is_admin'])
    
    def test_dashboard_access_regular_user(self):
        """Test que usuario regular puede acceder al dashboard con datos filtrados"""
        self.client.login(username='user1', password='user123')
        response = self.client.get(reverse('core:recycle_bin_dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['is_admin'])
        # Usuario regular solo ve sus propias eliminaciones
        self.assertEqual(response.context['total_deleted'], 3)
    
    def test_dashboard_statistics_admin(self):
        """Test que las estadísticas generales son correctas para admin"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('core:recycle_bin_dashboard'))
        
        # Total eliminados (todos los registros)
        self.assertEqual(response.context['total_deleted'], 15)
        
        # Total restaurados (3 que restauramos en setUp)
        self.assertEqual(response.context['total_restored'], 3)
        
        # Total pendientes (15 - 3 = 12)
        self.assertEqual(response.context['total_pending'], 12)
        
        # Eliminaciones permanentes (2 que creamos en logs)
        self.assertEqual(response.context['permanent_deletes'], 2)
        
        # Tasa de restauración
        self.assertGreater(response.context['restoration_rate'], 0)
    
    def test_dashboard_statistics_by_module(self):
        """Test que las estadísticas por módulo son correctas"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('core:recycle_bin_dashboard'))
        
        # Verificar que hay datos por módulo
        module_chart_data = json.loads(response.context['module_chart_data'])
        
        self.assertIn('labels', module_chart_data)
        self.assertIn('deleted', module_chart_data)
        self.assertIn('restored', module_chart_data)
        self.assertIn('pending', module_chart_data)
        
        # Verificar que hay datos de oficinas, bienes y catálogo
        self.assertGreater(len(module_chart_data['labels']), 0)
    
    def test_dashboard_statistics_by_user(self):
        """Test que las estadísticas por usuario son correctas (solo admin)"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('core:recycle_bin_dashboard'))
        
        # Verificar que hay datos por usuario
        user_chart_data = json.loads(response.context['user_chart_data'])
        
        self.assertIn('labels', user_chart_data)
        self.assertIn('deleted', user_chart_data)
        self.assertIn('restored', user_chart_data)
        
        # Debe haber al menos 3 usuarios (admin, user1, user2)
        self.assertGreaterEqual(len(user_chart_data['labels']), 3)
    
    def test_dashboard_statistics_by_time(self):
        """Test que las estadísticas por tiempo son correctas"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('core:recycle_bin_dashboard'))
        
        # Verificar que hay datos por tiempo
        time_chart_data = json.loads(response.context['time_chart_data'])
        
        self.assertIn('labels', time_chart_data)
        self.assertIn('deleted', time_chart_data)
        self.assertIn('restored', time_chart_data)
        
        # Debe haber datos de varios días
        self.assertGreater(len(time_chart_data['labels']), 0)
    
    def test_dashboard_date_filter(self):
        """Test que el filtro de fecha funciona correctamente"""
        self.client.login(username='admin', password='admin123')
        
        # Filtrar últimos 7 días
        response = self.client.get(reverse('core:recycle_bin_dashboard'), {'date_range': '7'})
        total_7_days = response.context['total_deleted']
        
        # Filtrar últimos 30 días
        response = self.client.get(reverse('core:recycle_bin_dashboard'), {'date_range': '30'})
        total_30_days = response.context['total_deleted']
        
        # Los últimos 30 días deben tener más o igual registros que los últimos 7
        self.assertGreaterEqual(total_30_days, total_7_days)
    
    def test_dashboard_recent_deletions(self):
        """Test que se muestran las eliminaciones recientes"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('core:recycle_bin_dashboard'))
        
        recent_deletions = response.context['recent_deletions']
        
        # Debe haber hasta 5 eliminaciones recientes
        self.assertLessEqual(len(recent_deletions), 5)
        self.assertGreater(len(recent_deletions), 0)
    
    def test_dashboard_recent_restorations(self):
        """Test que se muestran las restauraciones recientes"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('core:recycle_bin_dashboard'))
        
        recent_restorations = response.context['recent_restorations']
        
        # Debe haber hasta 5 restauraciones recientes
        self.assertLessEqual(len(recent_restorations), 5)
        self.assertGreater(len(recent_restorations), 0)
        
        # Todas deben tener restored_at
        for entry in recent_restorations:
            self.assertIsNotNone(entry.restored_at)
    
    def test_export_csv(self):
        """Test que la exportación a CSV funciona correctamente"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(
            reverse('core:recycle_bin_export_report'),
            {'format': 'csv', 'date_range': '30'}
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8')
        self.assertIn('attachment', response['Content-Disposition'])
        
        # Verificar que el contenido tiene datos
        content = response.content.decode('utf-8-sig')
        self.assertIn('ID', content)
        self.assertIn('Módulo', content)
    
    def test_export_json(self):
        """Test que la exportación a JSON funciona correctamente"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(
            reverse('core:recycle_bin_export_report'),
            {'format': 'json', 'date_range': '30'}
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        # Verificar que el JSON es válido
        data = json.loads(response.content)
        self.assertIn('data', data)
        self.assertIn('total_records', data)
        self.assertIn('exported_at', data)
        
        # Verificar que hay registros
        self.assertGreater(len(data['data']), 0)
    
    def test_export_with_filters(self):
        """Test que la exportación respeta los filtros"""
        self.client.login(username='admin', password='admin123')
        
        # Exportar solo pendientes
        response = self.client.get(
            reverse('core:recycle_bin_export_report'),
            {'format': 'json', 'status': 'pending'}
        )
        
        data = json.loads(response.content)
        
        # Todos los registros deben estar pendientes
        for record in data['data']:
            self.assertEqual(record['status'], 'pending')
        
        # Exportar solo de un módulo
        response = self.client.get(
            reverse('core:recycle_bin_export_report'),
            {'format': 'json', 'module': 'oficinas'}
        )
        
        data = json.loads(response.content)
        
        # Todos los registros deben ser de oficinas
        for record in data['data']:
            self.assertEqual(record['module_name'], 'oficinas')
    
    def test_export_regular_user_filtered(self):
        """Test que usuario regular solo exporta sus propios datos"""
        self.client.login(username='user1', password='user123')
        response = self.client.get(
            reverse('core:recycle_bin_export_report'),
            {'format': 'json'}
        )
        
        data = json.loads(response.content)
        
        # Solo debe tener 3 registros (los del usuario regular)
        self.assertEqual(data['total_records'], 3)
        
        # Todos deben ser del usuario regular
        for record in data['data']:
            self.assertEqual(record['deleted_by'], 'user1')
    
    def test_dashboard_requires_login(self):
        """Test que el dashboard requiere autenticación"""
        response = self.client.get(reverse('core:recycle_bin_dashboard'))
        
        # Debe redirigir al login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_export_requires_login(self):
        """Test que la exportación requiere autenticación"""
        response = self.client.get(reverse('core:recycle_bin_export_report'))
        
        # Debe redirigir al login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_dashboard_stats_by_module_table(self):
        """Test que la tabla de estadísticas por módulo es correcta"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('core:recycle_bin_dashboard'))
        
        stats_by_module = response.context['stats_by_module']
        
        # Debe haber estadísticas de al menos 3 módulos
        self.assertGreaterEqual(len(stats_by_module), 3)
        
        # Verificar estructura de cada estadística
        for stat in stats_by_module:
            self.assertIn('module_name', stat)
            self.assertIn('total', stat)
            self.assertIn('restored', stat)
            self.assertIn('pending', stat)
    
    def test_dashboard_stats_by_user_table(self):
        """Test que la tabla de estadísticas por usuario es correcta (admin)"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('core:recycle_bin_dashboard'))
        
        stats_by_user = response.context['stats_by_user']
        
        # Debe haber estadísticas de usuarios
        self.assertGreater(len(stats_by_user), 0)
        
        # Verificar estructura de cada estadística
        for stat in stats_by_user:
            self.assertIn('deleted_by__username', stat)
            self.assertIn('total', stat)
            self.assertIn('restored', stat)
            self.assertIn('pending', stat)
    
    def test_dashboard_no_user_stats_for_regular_user(self):
        """Test que usuario regular no ve estadísticas de otros usuarios"""
        self.client.login(username='user1', password='user123')
        response = self.client.get(reverse('core:recycle_bin_dashboard'))
        
        # Usuario regular no debe tener stats_by_user
        stats_by_user = response.context['stats_by_user']
        self.assertEqual(len(stats_by_user), 0)
    
    def test_dashboard_restoration_rate_calculation(self):
        """Test que la tasa de restauración se calcula correctamente"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('core:recycle_bin_dashboard'))
        
        total_deleted = response.context['total_deleted']
        total_restored = response.context['total_restored']
        restoration_rate = response.context['restoration_rate']
        
        # Calcular tasa esperada
        expected_rate = round((total_restored / total_deleted) * 100, 1) if total_deleted > 0 else 0
        
        self.assertEqual(restoration_rate, expected_rate)
    
    def test_export_csv_encoding(self):
        """Test que el CSV se exporta con la codificación correcta (UTF-8 con BOM)"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(
            reverse('core:recycle_bin_export_report'),
            {'format': 'csv'}
        )
        
        # Verificar que tiene BOM UTF-8
        content = response.content
        self.assertTrue(content.startswith(b'\xef\xbb\xbf'))


class RecycleBinDashboardIntegrationTestCase(TestCase):
    """Tests de integración para el dashboard"""
    
    def setUp(self):
        """Configuración inicial"""
        self.client = Client()
        
        self.admin_user = User.objects.create_user(
            username='admin',
            password='admin123'
        )
        self.admin_profile = UserProfile.objects.create(
            user=self.admin_user,
            role='administrador'
        )
    
    def test_dashboard_with_no_data(self):
        """Test que el dashboard funciona sin datos"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('core:recycle_bin_dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_deleted'], 0)
        self.assertEqual(response.context['total_restored'], 0)
        self.assertEqual(response.context['total_pending'], 0)
    
    def test_export_with_no_data(self):
        """Test que la exportación funciona sin datos"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(
            reverse('core:recycle_bin_export_report'),
            {'format': 'json'}
        )
        
        data = json.loads(response.content)
        self.assertEqual(data['total_records'], 0)
        self.assertEqual(len(data['data']), 0)
    
    def test_dashboard_link_from_list(self):
        """Test que el enlace al dashboard funciona desde la lista"""
        self.client.login(username='admin', password='admin123')
        
        # Ir a la lista de papelera
        response = self.client.get(reverse('core:recycle_bin_list'))
        self.assertEqual(response.status_code, 200)
        
        # Verificar que hay un enlace al dashboard
        self.assertContains(response, 'recycle_bin_dashboard')
        self.assertContains(response, 'Dashboard')
