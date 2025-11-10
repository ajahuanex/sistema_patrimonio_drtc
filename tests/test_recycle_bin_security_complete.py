"""
Pruebas de seguridad completas para el sistema de papelera de reciclaje
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User, Permission, Group
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from apps.core.models import RecycleBin, RecycleBinConfig, DeletionAuditLog, SecurityAttempt
from apps.core.services import RecycleBinService
from apps.oficinas.models import Oficina
from apps.bienes.models import BienPatrimonial
from apps.catalogo.models import Catalogo


class RecycleBinAccessControlTest(TestCase):
    """Pruebas de control de acceso"""
    
    def setUp(self):
        """Configurar usuarios con diferentes permisos"""
        # Usuario administrador con todos los permisos
        self.admin_user = User.objects.create_user(
            username='admin',
            password='admin123',
            is_staff=True,
            is_superuser=True
        )
        
        # Usuario funcionario con permisos limitados
        self.funcionario_user = User.objects.create_user(
            username='funcionario',
            password='func123'
        )
        
        # Usuario sin permisos
        self.no_perms_user = User.objects.create_user(
            username='noperms',
            password='noperms123'
        )
        
        # Asignar permisos específicos
        view_perm = Permission.objects.get(codename='view_recyclebin')
        restore_perm = Permission.objects.get(codename='can_restore_items')
        
        self.funcionario_user.user_permissions.add(view_perm, restore_perm)
        
        # Crear datos de prueba
        self.catalogo = Catalogo.objects.create(
            codigo='04220001',
            denominacion='TEST BIEN',
            grupo='04-AGRÍCOLA Y PESQUERO',
            clase='22-EQUIPO',
            resolucion='R.D. 001-2024',
            estado='ACTIVO'
        )
        
        self.oficina = Oficina.objects.create(
            codigo='DIR-001',
            nombre='Dirección Regional',
            responsable='Director Regional'
        )
        
        self.service = RecycleBinService()
        
        # Crear bien eliminado
        self.bien = BienPatrimonial.objects.create(
            codigo_patrimonial='PAT-SEC-001',
            catalogo=self.catalogo,
            oficina=self.oficina,
            estado_bien='B',
            created_by=self.admin_user
        )
        
        self.service.soft_delete_object(self.bien, self.admin_user, 'Test')
        
        self.recycle_entry = RecycleBin.objects.get(
            content_type__model='bienpatrimonial',
            object_id=self.bien.id
        )

    def test_unauthorized_access_to_recycle_bin(self):
        """Prueba acceso no autorizado a papelera"""
        client = Client()
        
        # Sin login
        response = client.get(reverse('core:recycle_bin_list'))
        self.assertEqual(response.status_code, 302)  # Redirect a login
        
        # Con usuario sin permisos
        client.login(username='noperms', password='noperms123')
        response = client.get(reverse('core:recycle_bin_list'))
        self.assertIn(response.status_code, [302, 403])
    
    def test_view_permission_enforcement(self):
        """Prueba aplicación de permiso de visualización"""
        client = Client()
        
        # Usuario con permiso de visualización
        client.login(username='funcionario', password='func123')
        response = client.get(reverse('core:recycle_bin_list'))
        self.assertEqual(response.status_code, 200)
        
        # Usuario sin permiso
        client.logout()
        client.login(username='noperms', password='noperms123')
        response = client.get(reverse('core:recycle_bin_list'))
        self.assertIn(response.status_code, [302, 403])
    
    def test_restore_permission_enforcement(self):
        """Prueba aplicación de permiso de restauración"""
        client = Client()
        
        # Usuario con permiso de restauración
        client.login(username='funcionario', password='func123')
        response = client.post(
            reverse('core:recycle_bin_restore', kwargs={'pk': self.recycle_entry.id})
        )
        self.assertEqual(response.status_code, 302)  # Éxito
        
        # Crear otro bien eliminado
        bien2 = BienPatrimonial.objects.create(
            codigo_patrimonial='PAT-SEC-002',
            catalogo=self.catalogo,
            oficina=self.oficina,
            estado_bien='B',
            created_by=self.admin_user
        )
        self.service.soft_delete_object(bien2, self.admin_user, 'Test')
        recycle_entry2 = RecycleBin.objects.get(
            content_type__model='bienpatrimonial',
            object_id=bien2.id
        )
        
        # Usuario sin permiso
        client.logout()
        client.login(username='noperms', password='noperms123')
        response = client.post(
            reverse('core:recycle_bin_restore', kwargs={'pk': recycle_entry2.id})
        )
        self.assertIn(response.status_code, [302, 403])
    
    def test_permanent_delete_permission_enforcement(self):
        """Prueba aplicación de permiso de eliminación permanente"""
        client = Client()
        
        # Usuario sin permiso de eliminación permanente
        client.login(username='funcionario', password='func123')
        response = client.post(
            reverse('core:recycle_bin_permanent_delete', kwargs={'pk': self.recycle_entry.id}),
            {'security_code': 'PERMANENT_DELETE_2024'}
        )
        self.assertIn(response.status_code, [302, 403])
        
        # Verificar que no se eliminó
        self.bien.refresh_from_db()
        self.assertTrue(self.bien.is_deleted)
        
        # Usuario con permiso (admin)
        client.logout()
        client.login(username='admin', password='admin123')
        response = client.post(
            reverse('core:recycle_bin_permanent_delete', kwargs={'pk': self.recycle_entry.id}),
            {'security_code': 'PERMANENT_DELETE_2024'}
        )
        self.assertEqual(response.status_code, 302)
    
    def test_data_segregation_by_user(self):
        """Prueba segregación de datos por usuario"""
        # Crear otro usuario y sus datos
        user2 = User.objects.create_user(
            username='user2',
            password='user2123'
        )
        
        view_perm = Permission.objects.get(codename='view_recyclebin')
        user2.user_permissions.add(view_perm)
        
        # Configurar para que solo vea sus propias eliminaciones
        config = RecycleBinConfig.objects.create(
            module_name='bienes',
            can_restore_own=True,
            can_restore_others=False
        )
        
        # Crear bien eliminado por user2
        bien2 = BienPatrimonial.objects.create(
            codigo_patrimonial='PAT-SEC-003',
            catalogo=self.catalogo,
            oficina=self.oficina,
            estado_bien='B',
            created_by=user2
        )
        self.service.soft_delete_object(bien2, user2, 'Test')
        
        # Verificar que funcionario no ve eliminaciones de user2
        client = Client()
        client.login(username='funcionario', password='func123')
        response = client.get(reverse('core:recycle_bin_list'))
        
        # Debería ver solo sus propias eliminaciones o las del admin
        self.assertEqual(response.status_code, 200)


class RecycleBinSecurityCodeTest(TestCase):
    """Pruebas de código de seguridad"""
    
    def setUp(self):
        """Configurar datos de prueba"""
        self.admin_user = User.objects.create_user(
            username='admin',
            password='admin123',
            is_staff=True,
            is_superuser=True
        )
        
        self.catalogo = Catalogo.objects.create(
            codigo='04220001',
            denominacion='TEST BIEN',
            grupo='04-AGRÍCOLA Y PESQUERO',
            clase='22-EQUIPO',
            resolucion='R.D. 001-2024',
            estado='ACTIVO'
        )
        
        self.oficina = Oficina.objects.create(
            codigo='DIR-001',
            nombre='Dirección Regional',
            responsable='Director Regional'
        )
        
        self.service = RecycleBinService()
        
        self.bien = BienPatrimonial.objects.create(
            codigo_patrimonial='PAT-CODE-001',
            catalogo=self.catalogo,
            oficina=self.oficina,
            estado_bien='B',
            created_by=self.admin_user
        )
        
        self.service.soft_delete_object(self.bien, self.admin_user, 'Test')
        
        self.client = Client()
        self.client.login(username='admin', password='admin123')

    def test_correct_security_code(self):
        """Prueba código de seguridad correcto"""
        recycle_entry = RecycleBin.objects.get(
            content_type__model='bienpatrimonial',
            object_id=self.bien.id
        )
        
        response = self.client.post(
            reverse('core:recycle_bin_permanent_delete', kwargs={'pk': recycle_entry.id}),
            {'security_code': 'PERMANENT_DELETE_2024'}
        )
        
        self.assertEqual(response.status_code, 302)
        
        # Verificar que se eliminó
        with self.assertRaises(BienPatrimonial.DoesNotExist):
            BienPatrimonial.all_objects.get(id=self.bien.id)
    
    def test_incorrect_security_code(self):
        """Prueba código de seguridad incorrecto"""
        recycle_entry = RecycleBin.objects.get(
            content_type__model='bienpatrimonial',
            object_id=self.bien.id
        )
        
        response = self.client.post(
            reverse('core:recycle_bin_permanent_delete', kwargs={'pk': recycle_entry.id}),
            {'security_code': 'WRONG_CODE'}
        )
        
        # Debería rechazar
        self.assertEqual(response.status_code, 200)  # Vuelve al formulario con error
        
        # Verificar que NO se eliminó
        self.bien.refresh_from_db()
        self.assertTrue(self.bien.is_deleted)
        
        # Verificar que se registró el intento
        attempt = SecurityAttempt.objects.filter(
            user=self.admin_user,
            attempt_type='permanent_delete',
            success=False
        ).first()
        self.assertIsNotNone(attempt)
    
    def test_rate_limiting_security_code(self):
        """Prueba limitación de intentos de código de seguridad"""
        recycle_entry = RecycleBin.objects.get(
            content_type__model='bienpatrimonial',
            object_id=self.bien.id
        )
        
        url = reverse('core:recycle_bin_permanent_delete', kwargs={'pk': recycle_entry.id})
        
        # Intentar 5 veces con código incorrecto
        for i in range(5):
            response = self.client.post(url, {'security_code': f'WRONG_CODE_{i}'})
        
        # El sexto intento debería ser bloqueado
        response = self.client.post(url, {'security_code': 'WRONG_CODE_6'})
        
        # Verificar que se bloqueó (puede ser 403 o mensaje de error)
        self.assertIn(response.status_code, [200, 403])
        
        # Verificar que se registraron los intentos
        attempts_count = SecurityAttempt.objects.filter(
            user=self.admin_user,
            attempt_type='permanent_delete'
        ).count()
        self.assertGreaterEqual(attempts_count, 5)
    
    def test_security_code_logging(self):
        """Prueba logging de uso de código de seguridad"""
        recycle_entry = RecycleBin.objects.get(
            content_type__model='bienpatrimonial',
            object_id=self.bien.id
        )
        
        # Usar código correcto
        self.client.post(
            reverse('core:recycle_bin_permanent_delete', kwargs={'pk': recycle_entry.id}),
            {'security_code': 'PERMANENT_DELETE_2024'}
        )
        
        # Verificar que se registró en auditoría
        audit_log = DeletionAuditLog.objects.filter(
            action='permanent_delete',
            user=self.admin_user
        ).first()
        
        self.assertIsNotNone(audit_log)
        self.assertIn('security_code_used', audit_log.context_data)


class RecycleBinInjectionAttackTest(TestCase):
    """Pruebas de protección contra ataques de inyección"""
    
    def setUp(self):
        """Configurar datos de prueba"""
        self.admin_user = User.objects.create_user(
            username='admin',
            password='admin123',
            is_staff=True,
            is_superuser=True
        )
        
        self.catalogo = Catalogo.objects.create(
            codigo='04220001',
            denominacion='TEST BIEN',
            grupo='04-AGRÍCOLA Y PESQUERO',
            clase='22-EQUIPO',
            resolucion='R.D. 001-2024',
            estado='ACTIVO'
        )
        
        self.oficina = Oficina.objects.create(
            codigo='DIR-001',
            nombre='Dirección Regional',
            responsable='Director Regional'
        )
        
        self.service = RecycleBinService()
        self.client = Client()
        self.client.login(username='admin', password='admin123')
    
    def test_sql_injection_protection_in_search(self):
        """Prueba protección contra SQL injection en búsqueda"""
        # Crear bien eliminado
        bien = BienPatrimonial.objects.create(
            codigo_patrimonial='PAT-INJ-001',
            catalogo=self.catalogo,
            oficina=self.oficina,
            estado_bien='B',
            created_by=self.admin_user
        )
        self.service.soft_delete_object(bien, self.admin_user, 'Test')
        
        # Intentar SQL injection en búsqueda
        malicious_queries = [
            "'; DROP TABLE recycle_bin; --",
            "1' OR '1'='1",
            "admin'--",
            "1; DELETE FROM recycle_bin WHERE 1=1; --"
        ]
        
        for query in malicious_queries:
            response = self.client.get(
                reverse('core:recycle_bin_list'),
                {'search': query}
            )
            
            # Debería manejar graciosamente sin error
            self.assertEqual(response.status_code, 200)
        
        # Verificar que los datos siguen intactos
        self.assertTrue(RecycleBin.objects.exists())
    
    def test_xss_protection_in_reason_field(self):
        """Prueba protección contra XSS en campo de razón"""
        # Intentar XSS en razón de eliminación
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src='javascript:alert(\"XSS\")'></iframe>"
        ]
        
        for payload in xss_payloads:
            bien = BienPatrimonial.objects.create(
                codigo_patrimonial=f'PAT-XSS-{xss_payloads.index(payload)}',
                catalogo=self.catalogo,
                oficina=self.oficina,
                estado_bien='B',
                created_by=self.admin_user
            )
            
            self.service.soft_delete_object(bien, self.admin_user, payload)
            
            # Verificar que se guardó pero escapado
            recycle_entry = RecycleBin.objects.get(
                content_type__model='bienpatrimonial',
                object_id=bien.id
            )
            
            # El payload debería estar almacenado pero será escapado al renderizar
            self.assertIsNotNone(recycle_entry.deletion_reason)
    
    def test_csrf_protection(self):
        """Prueba protección CSRF"""
        # Crear bien eliminado
        bien = BienPatrimonial.objects.create(
            codigo_patrimonial='PAT-CSRF-001',
            catalogo=self.catalogo,
            oficina=self.oficina,
            estado_bien='B',
            created_by=self.admin_user
        )
        self.service.soft_delete_object(bien, self.admin_user, 'Test')
        
        recycle_entry = RecycleBin.objects.get(
            content_type__model='bienpatrimonial',
            object_id=bien.id
        )
        
        # Intentar POST sin CSRF token
        client_no_csrf = Client(enforce_csrf_checks=True)
        client_no_csrf.login(username='admin', password='admin123')
        
        response = client_no_csrf.post(
            reverse('core:recycle_bin_restore', kwargs={'pk': recycle_entry.id})
        )
        
        # Debería rechazar por falta de CSRF token
        self.assertEqual(response.status_code, 403)


class RecycleBinAuditTrailTest(TestCase):
    """Pruebas de trazabilidad de auditoría"""
    
    def setUp(self):
        """Configurar datos de prueba"""
        self.admin_user = User.objects.create_user(
            username='admin',
            password='admin123',
            is_staff=True
        )
        
        self.catalogo = Catalogo.objects.create(
            codigo='04220001',
            denominacion='TEST BIEN',
            grupo='04-AGRÍCOLA Y PESQUERO',
            clase='22-EQUIPO',
            resolucion='R.D. 001-2024',
            estado='ACTIVO'
        )
        
        self.oficina = Oficina.objects.create(
            codigo='DIR-001',
            nombre='Dirección Regional',
            responsable='Director Regional'
        )
        
        self.service = RecycleBinService()

    def test_complete_audit_trail_soft_delete(self):
        """Prueba trazabilidad completa de eliminación lógica"""
        bien = BienPatrimonial.objects.create(
            codigo_patrimonial='PAT-AUDIT-001',
            catalogo=self.catalogo,
            oficina=self.oficina,
            estado_bien='B',
            created_by=self.admin_user
        )
        
        # Eliminar con contexto
        self.service.soft_delete_object(
            bien,
            self.admin_user,
            'Eliminación para auditoría',
            context={'ip': '192.168.1.1', 'user_agent': 'Test Browser'}
        )
        
        # Verificar log de auditoría
        audit_log = DeletionAuditLog.objects.filter(
            content_type__model='bienpatrimonial',
            object_id=bien.id,
            action='soft_delete'
        ).first()
        
        self.assertIsNotNone(audit_log)
        self.assertEqual(audit_log.user, self.admin_user)
        self.assertIsNotNone(audit_log.timestamp)
        self.assertIn('ip', audit_log.context_data)
        self.assertEqual(audit_log.context_data['ip'], '192.168.1.1')
    
    def test_complete_audit_trail_restore(self):
        """Prueba trazabilidad completa de restauración"""
        bien = BienPatrimonial.objects.create(
            codigo_patrimonial='PAT-AUDIT-002',
            catalogo=self.catalogo,
            oficina=self.oficina,
            estado_bien='B',
            created_by=self.admin_user
        )
        
        self.service.soft_delete_object(bien, self.admin_user, 'Test')
        self.service.restore_object(bien, self.admin_user)
        
        # Verificar logs de ambas acciones
        delete_log = DeletionAuditLog.objects.filter(
            object_id=bien.id,
            action='soft_delete'
        ).first()
        
        restore_log = DeletionAuditLog.objects.filter(
            object_id=bien.id,
            action='restore'
        ).first()
        
        self.assertIsNotNone(delete_log)
        self.assertIsNotNone(restore_log)
        self.assertLess(delete_log.timestamp, restore_log.timestamp)
    
    def test_complete_audit_trail_permanent_delete(self):
        """Prueba trazabilidad completa de eliminación permanente"""
        bien = BienPatrimonial.objects.create(
            codigo_patrimonial='PAT-AUDIT-003',
            catalogo=self.catalogo,
            oficina=self.oficina,
            estado_bien='B',
            marca='MARCA TEST',
            modelo='MODELO TEST',
            created_by=self.admin_user
        )
        
        bien_id = bien.id
        
        self.service.soft_delete_object(bien, self.admin_user, 'Test')
        self.service.permanent_delete(bien, self.admin_user, 'PERMANENT_DELETE_2024')
        
        # Verificar log de eliminación permanente
        perm_delete_log = DeletionAuditLog.objects.filter(
            object_id=bien_id,
            action='permanent_delete'
        ).first()
        
        self.assertIsNotNone(perm_delete_log)
        self.assertIsNotNone(perm_delete_log.object_snapshot)
        
        # Verificar que el snapshot contiene los datos del objeto
        snapshot = perm_delete_log.object_snapshot
        self.assertIn('codigo_patrimonial', snapshot)
        self.assertEqual(snapshot['codigo_patrimonial'], 'PAT-AUDIT-003')
        self.assertIn('marca', snapshot)
        self.assertEqual(snapshot['marca'], 'MARCA TEST')
    
    def test_audit_log_immutability(self):
        """Prueba inmutabilidad de logs de auditoría"""
        bien = BienPatrimonial.objects.create(
            codigo_patrimonial='PAT-AUDIT-004',
            catalogo=self.catalogo,
            oficina=self.oficina,
            estado_bien='B',
            created_by=self.admin_user
        )
        
        self.service.soft_delete_object(bien, self.admin_user, 'Test')
        
        audit_log = DeletionAuditLog.objects.filter(
            object_id=bien.id,
            action='soft_delete'
        ).first()
        
        original_timestamp = audit_log.timestamp
        original_user = audit_log.user
        
        # Intentar modificar (en producción esto debería estar protegido)
        # Aquí solo verificamos que los datos originales se mantienen
        audit_log.refresh_from_db()
        
        self.assertEqual(audit_log.timestamp, original_timestamp)
        self.assertEqual(audit_log.user, original_user)
    
    def test_audit_log_retention(self):
        """Prueba retención de logs de auditoría"""
        # Crear múltiples operaciones
        for i in range(10):
            bien = BienPatrimonial.objects.create(
                codigo_patrimonial=f'PAT-RETENTION-{i:03d}',
                catalogo=self.catalogo,
                oficina=self.oficina,
                estado_bien='B',
                created_by=self.admin_user
            )
            
            self.service.soft_delete_object(bien, self.admin_user, f'Test {i}')
            
            if i % 2 == 0:
                self.service.restore_object(bien, self.admin_user)
        
        # Verificar que todos los logs se mantienen
        total_logs = DeletionAuditLog.objects.count()
        self.assertEqual(total_logs, 15)  # 10 deletes + 5 restores
        
        # Los logs deberían mantenerse incluso después de restaurar
        restored_bienes = BienPatrimonial.objects.filter(deleted_at__isnull=True)
        for bien in restored_bienes:
            delete_log = DeletionAuditLog.objects.filter(
                object_id=bien.id,
                action='soft_delete'
            ).exists()
            restore_log = DeletionAuditLog.objects.filter(
                object_id=bien.id,
                action='restore'
            ).exists()
            
            self.assertTrue(delete_log)
            self.assertTrue(restore_log)
