"""
Tests para el modelo DeletionAuditLog y su integración con el sistema de papelera
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from datetime import timedelta

from apps.core.models import DeletionAuditLog, RecycleBin
from apps.oficinas.models import Oficina
from apps.core.utils import RecycleBinService


class DeletionAuditLogModelTest(TestCase):
    """Tests para el modelo DeletionAuditLog"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.user.profile.role = 'administrador'
        self.user.profile.save()
        
        self.oficina = Oficina.objects.create(
            codigo='OF001',
            nombre='Oficina Test',
            direccion='Calle Test 123',
            created_by=self.user
        )
    
    def test_log_soft_delete_creates_audit_entry(self):
        """Test que log_soft_delete crea una entrada de auditoría correctamente"""
        # Realizar soft delete
        ip_address = '192.168.1.1'
        user_agent = 'Mozilla/5.0 Test Browser'
        reason = 'Oficina ya no está en uso'
        
        success, message, recycle_entry = RecycleBinService.soft_delete_object(
            self.oficina,
            self.user,
            reason=reason,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.assertTrue(success)
        
        # Verificar que se creó la entrada de auditoría
        audit_log = DeletionAuditLog.objects.filter(
            action='soft_delete',
            object_id=self.oficina.pk,
            user=self.user
        ).first()
        
        self.assertIsNotNone(audit_log)
        self.assertEqual(audit_log.action, 'soft_delete')
        self.assertEqual(audit_log.user, self.user)
        self.assertEqual(audit_log.object_repr, str(self.oficina))
        self.assertEqual(audit_log.module_name, 'oficinas')
        self.assertEqual(audit_log.reason, reason)
        self.assertEqual(audit_log.ip_address, ip_address)
        self.assertEqual(audit_log.user_agent, user_agent)
        self.assertTrue(audit_log.success)
        self.assertIsNotNone(audit_log.object_snapshot)
        self.assertEqual(audit_log.recycle_bin_entry, recycle_entry)
    
    def test_log_soft_delete_includes_snapshot(self):
        """Test que el snapshot incluye los datos del objeto"""
        success, message, recycle_entry = RecycleBinService.soft_delete_object(
            self.oficina,
            self.user,
            reason='Test'
        )
        
        audit_log = DeletionAuditLog.objects.filter(
            action='soft_delete',
            object_id=self.oficina.pk
        ).first()
        
        self.assertIsNotNone(audit_log.object_snapshot)
        self.assertIn('codigo', audit_log.object_snapshot)
        self.assertIn('nombre', audit_log.object_snapshot)
        self.assertEqual(audit_log.object_snapshot['codigo'], 'OF001')
        self.assertEqual(audit_log.object_snapshot['nombre'], 'Oficina Test')
    
    def test_log_restore_creates_audit_entry(self):
        """Test que log_restore crea una entrada de auditoría correctamente"""
        # Primero eliminar
        success, message, recycle_entry = RecycleBinService.soft_delete_object(
            self.oficina,
            self.user,
            reason='Test delete'
        )
        
        # Refrescar objeto
        self.oficina.refresh_from_db()
        
        # Restaurar
        ip_address = '192.168.1.2'
        user_agent = 'Mozilla/5.0 Restore Browser'
        
        success, message, restored_obj = RecycleBinService.restore_object(
            recycle_entry,
            self.user,
            notes='Restauración de prueba',
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.assertTrue(success)
        
        # Verificar entrada de auditoría de restauración
        audit_log = DeletionAuditLog.objects.filter(
            action='restore',
            object_id=self.oficina.pk,
            user=self.user
        ).first()
        
        self.assertIsNotNone(audit_log)
        self.assertEqual(audit_log.action, 'restore')
        self.assertEqual(audit_log.user, self.user)
        self.assertEqual(audit_log.ip_address, ip_address)
        self.assertEqual(audit_log.user_agent, user_agent)
        self.assertTrue(audit_log.success)
        self.assertIsNotNone(audit_log.previous_state)
        self.assertIn('deleted_at', audit_log.previous_state)
    
    def test_log_permanent_delete_creates_audit_entry(self):
        """Test que log_permanent_delete crea una entrada de auditoría correctamente"""
        # Primero eliminar
        success, message, recycle_entry = RecycleBinService.soft_delete_object(
            self.oficina,
            self.user,
            reason='Test delete'
        )
        
        # Refrescar objeto
        self.oficina.refresh_from_db()
        
        # Configurar código de seguridad
        from django.conf import settings
        settings.PERMANENT_DELETE_CODE = 'TEST123'
        
        # Eliminar permanentemente
        ip_address = '192.168.1.3'
        user_agent = 'Mozilla/5.0 Delete Browser'
        reason = 'Eliminación permanente de prueba'
        
        success, message = RecycleBinService.permanent_delete(
            recycle_entry,
            self.user,
            'TEST123',
            reason=reason,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.assertTrue(success)
        
        # Verificar entrada de auditoría de eliminación permanente
        audit_log = DeletionAuditLog.objects.filter(
            action='permanent_delete',
            object_id=self.oficina.pk,
            user=self.user
        ).first()
        
        self.assertIsNotNone(audit_log)
        self.assertEqual(audit_log.action, 'permanent_delete')
        self.assertEqual(audit_log.user, self.user)
        self.assertEqual(audit_log.reason, reason)
        self.assertEqual(audit_log.ip_address, ip_address)
        self.assertEqual(audit_log.user_agent, user_agent)
        self.assertTrue(audit_log.success)
        self.assertTrue(audit_log.security_code_used)
        self.assertIsNotNone(audit_log.object_snapshot)
    
    def test_log_failed_restore_creates_audit_entry(self):
        """Test que log_failed_operation registra fallos correctamente"""
        # Crear entrada de auditoría de fallo
        audit_log = DeletionAuditLog.log_failed_operation(
            action='restore',
            obj=self.oficina,
            user=self.user,
            error_message='Conflicto: código duplicado',
            ip_address='192.168.1.4',
            user_agent='Test Browser'
        )
        
        self.assertIsNotNone(audit_log)
        self.assertEqual(audit_log.action, 'failed_restore')
        self.assertFalse(audit_log.success)
        self.assertEqual(audit_log.error_message, 'Conflicto: código duplicado')
    
    def test_log_bulk_restore_creates_multiple_entries(self):
        """Test que log_bulk_operation crea múltiples entradas"""
        # Crear múltiples oficinas
        oficinas = []
        for i in range(3):
            oficina = Oficina.objects.create(
                codigo=f'OF00{i+2}',
                nombre=f'Oficina {i+2}',
                direccion=f'Calle {i+2}',
                created_by=self.user
            )
            oficinas.append(oficina)
        
        # Registrar operación en lote
        logs = DeletionAuditLog.log_bulk_operation(
            action='bulk_restore',
            objects=oficinas,
            user=self.user,
            ip_address='192.168.1.5',
            user_agent='Bulk Browser',
            metadata={'total_count': 3, 'restored_count': 3}
        )
        
        self.assertEqual(len(logs), 3)
        for log in logs:
            self.assertEqual(log.action, 'bulk_restore')
            self.assertEqual(log.user, self.user)
            self.assertTrue(log.success)
            self.assertIn('total_count', log.metadata)
    
    def test_audit_log_indexes_exist(self):
        """Test que los índices de la base de datos existen"""
        # Verificar que el modelo tiene los índices definidos
        indexes = DeletionAuditLog._meta.indexes
        self.assertGreater(len(indexes), 0)
        
        # Verificar nombres de índices específicos
        index_names = [idx.name for idx in indexes]
        self.assertIn('deletion_audit_time_idx', index_names)
        self.assertIn('deletion_audit_user_time_idx', index_names)
        self.assertIn('deletion_audit_action_time_idx', index_names)
    
    def test_get_action_icon_returns_correct_icon(self):
        """Test que get_action_icon retorna el icono correcto"""
        audit_log = DeletionAuditLog.objects.create(
            action='soft_delete',
            user=self.user,
            content_type=ContentType.objects.get_for_model(self.oficina),
            object_id=self.oficina.pk,
            object_repr=str(self.oficina),
            module_name='oficinas'
        )
        
        self.assertEqual(audit_log.get_action_icon(), '🗑️')
        
        audit_log.action = 'restore'
        self.assertEqual(audit_log.get_action_icon(), '♻️')
        
        audit_log.action = 'permanent_delete'
        self.assertEqual(audit_log.get_action_icon(), '❌')
    
    def test_get_action_color_returns_correct_color(self):
        """Test que get_action_color retorna el color correcto"""
        audit_log = DeletionAuditLog.objects.create(
            action='soft_delete',
            user=self.user,
            content_type=ContentType.objects.get_for_model(self.oficina),
            object_id=self.oficina.pk,
            object_repr=str(self.oficina),
            module_name='oficinas'
        )
        
        self.assertEqual(audit_log.get_action_color(), 'warning')
        
        audit_log.action = 'restore'
        self.assertEqual(audit_log.get_action_color(), 'success')
        
        audit_log.action = 'permanent_delete'
        self.assertEqual(audit_log.get_action_color(), 'danger')
    
    def test_audit_log_ordering(self):
        """Test que los logs se ordenan por timestamp descendente"""
        # Crear múltiples logs
        for i in range(3):
            DeletionAuditLog.objects.create(
                action='soft_delete',
                user=self.user,
                content_type=ContentType.objects.get_for_model(self.oficina),
                object_id=self.oficina.pk,
                object_repr=f'Test {i}',
                module_name='oficinas'
            )
        
        logs = DeletionAuditLog.objects.all()
        
        # Verificar que están ordenados por timestamp descendente
        for i in range(len(logs) - 1):
            self.assertGreaterEqual(logs[i].timestamp, logs[i+1].timestamp)
    
    def test_audit_log_str_representation(self):
        """Test que __str__ retorna una representación legible"""
        audit_log = DeletionAuditLog.objects.create(
            action='soft_delete',
            user=self.user,
            content_type=ContentType.objects.get_for_model(self.oficina),
            object_id=self.oficina.pk,
            object_repr=str(self.oficina),
            module_name='oficinas'
        )
        
        str_repr = str(audit_log)
        self.assertIn(self.user.username, str_repr)
        self.assertIn('Eliminación Lógica', str_repr)
        self.assertIn(str(self.oficina), str_repr)


class DeletionAuditLogIntegrationTest(TestCase):
    """Tests de integración del DeletionAuditLog con el sistema completo"""
    
    def setUp(self):
        """Configuración inicial"""
        self.admin = User.objects.create_user(
            username='admin',
            password='admin123',
            email='admin@example.com'
        )
        self.admin.profile.role = 'administrador'
        self.admin.profile.save()
        
        self.user = User.objects.create_user(
            username='user',
            password='user123',
            email='user@example.com'
        )
        self.user.profile.role = 'funcionario'
        self.user.profile.save()
    
    def test_complete_lifecycle_creates_all_audit_entries(self):
        """Test que el ciclo completo de vida crea todas las entradas de auditoría"""
        # Crear oficina
        oficina = Oficina.objects.create(
            codigo='OF001',
            nombre='Oficina Lifecycle',
            direccion='Calle Test',
            created_by=self.admin
        )
        
        # 1. Soft delete
        success, message, recycle_entry = RecycleBinService.soft_delete_object(
            oficina,
            self.user,
            reason='Prueba de ciclo completo',
            ip_address='192.168.1.1',
            user_agent='Test Browser'
        )
        self.assertTrue(success)
        
        # Verificar log de soft delete
        soft_delete_log = DeletionAuditLog.objects.filter(
            action='soft_delete',
            object_id=oficina.pk
        ).first()
        self.assertIsNotNone(soft_delete_log)
        
        # 2. Restaurar
        oficina.refresh_from_db()
        success, message, restored = RecycleBinService.restore_object(
            recycle_entry,
            self.admin,
            ip_address='192.168.1.2',
            user_agent='Admin Browser'
        )
        self.assertTrue(success)
        
        # Verificar log de restore
        restore_log = DeletionAuditLog.objects.filter(
            action='restore',
            object_id=oficina.pk
        ).first()
        self.assertIsNotNone(restore_log)
        
        # 3. Eliminar nuevamente
        oficina.refresh_from_db()
        success, message, recycle_entry2 = RecycleBinService.soft_delete_object(
            oficina,
            self.admin,
            reason='Segunda eliminación',
            ip_address='192.168.1.3',
            user_agent='Admin Browser'
        )
        self.assertTrue(success)
        
        # 4. Eliminar permanentemente
        from django.conf import settings
        settings.PERMANENT_DELETE_CODE = 'TEST123'
        
        oficina.refresh_from_db()
        success, message = RecycleBinService.permanent_delete(
            recycle_entry2,
            self.admin,
            'TEST123',
            reason='Eliminación permanente final',
            ip_address='192.168.1.4',
            user_agent='Admin Browser'
        )
        self.assertTrue(success)
        
        # Verificar log de permanent delete
        permanent_log = DeletionAuditLog.objects.filter(
            action='permanent_delete',
            object_id=oficina.pk
        ).first()
        self.assertIsNotNone(permanent_log)
        
        # Verificar que tenemos todos los logs
        all_logs = DeletionAuditLog.objects.filter(object_id=oficina.pk)
        self.assertEqual(all_logs.count(), 4)  # 2 soft deletes, 1 restore, 1 permanent delete
    
    def test_audit_log_preserves_data_after_permanent_delete(self):
        """Test que los logs de auditoría se preservan después de eliminación permanente"""
        oficina = Oficina.objects.create(
            codigo='OF002',
            nombre='Oficina Preserve',
            direccion='Calle Preserve',
            created_by=self.admin
        )
        
        oficina_id = oficina.pk
        oficina_repr = str(oficina)
        
        # Eliminar y luego eliminar permanentemente
        success, message, recycle_entry = RecycleBinService.soft_delete_object(
            oficina,
            self.admin,
            reason='Test preserve'
        )
        
        from django.conf import settings
        settings.PERMANENT_DELETE_CODE = 'TEST123'
        
        oficina.refresh_from_db()
        success, message = RecycleBinService.permanent_delete(
            recycle_entry,
            self.admin,
            'TEST123',
            reason='Eliminación permanente'
        )
        
        # Verificar que el objeto ya no existe
        self.assertFalse(Oficina.all_objects.filter(pk=oficina_id).exists())
        
        # Verificar que los logs de auditoría aún existen
        logs = DeletionAuditLog.objects.filter(object_id=oficina_id)
        self.assertGreater(logs.count(), 0)
        
        # Verificar que el snapshot está completo
        permanent_log = logs.filter(action='permanent_delete').first()
        self.assertIsNotNone(permanent_log.object_snapshot)
        self.assertIn('codigo', permanent_log.object_snapshot)
        self.assertEqual(permanent_log.object_snapshot['codigo'], 'OF002')
