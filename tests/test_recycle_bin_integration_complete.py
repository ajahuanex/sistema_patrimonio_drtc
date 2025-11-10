"""
Pruebas de integración completas para el sistema de papelera de reciclaje
"""
from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User, Permission
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from apps.core.models import RecycleBin, RecycleBinConfig, DeletionAuditLog
from apps.core.services import RecycleBinService
from apps.oficinas.models import Oficina
from apps.bienes.models import BienPatrimonial
from apps.catalogo.models import Catalogo


class RecycleBinEndToEndIntegrationTest(TestCase):
    """Pruebas de integración de extremo a extremo del sistema de papelera"""
    
    def setUp(self):
        """Configurar datos de prueba"""
        # Crear usuarios con diferentes roles
        self.admin_user = User.objects.create_user(
            username='admin',
            password='admin123',
            is_staff=True,
            is_superuser=True
        )
        
        self.funcionario_user = User.objects.create_user(
            username='funcionario',
            password='func123'
        )
        
        # Asignar permisos
        perms = Permission.objects.filter(
            codename__in=['view_recyclebin', 'can_restore_items', 'can_permanent_delete']
        )
        self.admin_user.user_permissions.set(perms)
        
        # Crear datos base
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
        
        # Configurar papelera
        RecycleBinConfig.objects.create(
            module_name='bienes',
            retention_days=30,
            auto_delete_enabled=True
        )
        
        self.service = RecycleBinService()

    def test_complete_soft_delete_workflow(self):
        """Prueba flujo completo de eliminación lógica"""
        # 1. Crear bien
        bien = BienPatrimonial.objects.create(
            codigo_patrimonial='PAT-INT-001',
            catalogo=self.catalogo,
            oficina=self.oficina,
            estado_bien='B',
            created_by=self.admin_user
        )
        
        # 2. Eliminar lógicamente
        self.service.soft_delete_object(
            obj=bien,
            user=self.admin_user,
            reason='Prueba de integración'
        )
        
        # 3. Verificar que está en papelera
        self.assertTrue(bien.is_deleted)
        recycle_entry = RecycleBin.objects.get(
            content_type__model='bienpatrimonial',
            object_id=bien.id
        )
        self.assertIsNotNone(recycle_entry)
        self.assertEqual(recycle_entry.deleted_by, self.admin_user)
        
        # 4. Verificar que se creó log de auditoría
        audit_log = DeletionAuditLog.objects.filter(
            content_type__model='bienpatrimonial',
            object_id=bien.id,
            action='soft_delete'
        ).first()
        self.assertIsNotNone(audit_log)
        
        # 5. Verificar que no aparece en consultas normales
        bienes_activos = BienPatrimonial.objects.all()
        self.assertNotIn(bien, bienes_activos)
        
        # 6. Verificar que aparece en consultas de eliminados
        bienes_eliminados = BienPatrimonial.all_objects.filter(deleted_at__isnull=False)
        self.assertIn(bien, bienes_eliminados)
    
    def test_complete_restore_workflow(self):
        """Prueba flujo completo de restauración"""
        # 1. Crear y eliminar bien
        bien = BienPatrimonial.objects.create(
            codigo_patrimonial='PAT-INT-002',
            catalogo=self.catalogo,
            oficina=self.oficina,
            estado_bien='B',
            created_by=self.admin_user
        )
        
        self.service.soft_delete_object(bien, self.admin_user, 'Test')
        
        # 2. Restaurar
        result = self.service.restore_object(bien, self.admin_user)
        
        # 3. Verificar restauración exitosa
        self.assertTrue(result['success'])
        bien.refresh_from_db()
        self.assertFalse(bien.is_deleted)
        self.assertIsNone(bien.deleted_at)
        
        # 4. Verificar que se actualizó entrada en papelera
        recycle_entry = RecycleBin.objects.get(
            content_type__model='bienpatrimonial',
            object_id=bien.id
        )
        self.assertIsNotNone(recycle_entry.restored_at)
        self.assertEqual(recycle_entry.restored_by, self.admin_user)
        
        # 5. Verificar log de auditoría
        audit_log = DeletionAuditLog.objects.filter(
            content_type__model='bienpatrimonial',
            object_id=bien.id,
            action='restore'
        ).first()
        self.assertIsNotNone(audit_log)
        
        # 6. Verificar que vuelve a aparecer en consultas normales
        bienes_activos = BienPatrimonial.objects.all()
        self.assertIn(bien, bienes_activos)

    def test_complete_permanent_delete_workflow(self):
        """Prueba flujo completo de eliminación permanente"""
        # 1. Crear y eliminar bien
        bien = BienPatrimonial.objects.create(
            codigo_patrimonial='PAT-INT-003',
            catalogo=self.catalogo,
            oficina=self.oficina,
            estado_bien='B',
            created_by=self.admin_user
        )
        
        bien_id = bien.id
        self.service.soft_delete_object(bien, self.admin_user, 'Test')
        
        # 2. Eliminar permanentemente
        result = self.service.permanent_delete(
            bien,
            self.admin_user,
            security_code='PERMANENT_DELETE_2024'
        )
        
        # 3. Verificar eliminación exitosa
        self.assertTrue(result['success'])
        
        # 4. Verificar que ya no existe en BD
        with self.assertRaises(BienPatrimonial.DoesNotExist):
            BienPatrimonial.all_objects.get(id=bien_id)
        
        # 5. Verificar que se actualizó entrada en papelera
        recycle_entry = RecycleBin.objects.get(
            content_type__model='bienpatrimonial',
            object_id=bien_id
        )
        self.assertIsNotNone(recycle_entry.permanently_deleted_at)
        
        # 6. Verificar log de auditoría con snapshot
        audit_log = DeletionAuditLog.objects.filter(
            content_type__model='bienpatrimonial',
            object_id=bien_id,
            action='permanent_delete'
        ).first()
        self.assertIsNotNone(audit_log)
        self.assertIsNotNone(audit_log.object_snapshot)
        self.assertIn('codigo_patrimonial', audit_log.object_snapshot)
    
    def test_multi_module_integration(self):
        """Prueba integración con múltiples módulos"""
        # 1. Crear objetos de diferentes módulos
        oficina = Oficina.objects.create(
            codigo='TEST-001',
            nombre='Oficina Test',
            responsable='Responsable Test'
        )
        
        bien = BienPatrimonial.objects.create(
            codigo_patrimonial='PAT-INT-004',
            catalogo=self.catalogo,
            oficina=self.oficina,
            estado_bien='B',
            created_by=self.admin_user
        )
        
        catalogo = Catalogo.objects.create(
            codigo='99999999',
            denominacion='CATALOGO TEST',
            grupo='99-TEST',
            clase='99-TEST',
            resolucion='R.D. 999-2024',
            estado='ACTIVO'
        )
        
        # 2. Eliminar todos
        self.service.soft_delete_object(oficina, self.admin_user, 'Test oficina')
        self.service.soft_delete_object(bien, self.admin_user, 'Test bien')
        self.service.soft_delete_object(catalogo, self.admin_user, 'Test catalogo')
        
        # 3. Verificar que todos están en papelera
        recycle_entries = RecycleBin.objects.filter(deleted_by=self.admin_user)
        self.assertEqual(recycle_entries.count(), 3)
        
        # 4. Verificar que se pueden filtrar por módulo
        oficinas_deleted = RecycleBin.objects.filter(
            content_type__model='oficina'
        )
        self.assertEqual(oficinas_deleted.count(), 1)
        
        bienes_deleted = RecycleBin.objects.filter(
            content_type__model='bienpatrimonial'
        )
        self.assertEqual(bienes_deleted.count(), 1)
        
        catalogos_deleted = RecycleBin.objects.filter(
            content_type__model='catalogo'
        )
        self.assertEqual(catalogos_deleted.count(), 1)

    def test_auto_cleanup_integration(self):
        """Prueba integración de limpieza automática"""
        # 1. Crear bien con fecha de eliminación antigua
        bien = BienPatrimonial.objects.create(
            codigo_patrimonial='PAT-INT-005',
            catalogo=self.catalogo,
            oficina=self.oficina,
            estado_bien='B',
            created_by=self.admin_user
        )
        
        # 2. Eliminar y modificar fecha
        self.service.soft_delete_object(bien, self.admin_user, 'Test')
        
        recycle_entry = RecycleBin.objects.get(
            content_type__model='bienpatrimonial',
            object_id=bien.id
        )
        
        # Simular que pasaron 31 días
        recycle_entry.auto_delete_at = timezone.now() - timedelta(days=1)
        recycle_entry.save()
        
        # 3. Ejecutar limpieza automática
        result = self.service.auto_cleanup()
        
        # 4. Verificar que se eliminó
        self.assertGreater(result['deleted_count'], 0)
        
        # 5. Verificar que ya no existe
        with self.assertRaises(BienPatrimonial.DoesNotExist):
            BienPatrimonial.all_objects.get(id=bien.id)
    
    def test_cascade_delete_integration(self):
        """Prueba eliminación en cascada"""
        # 1. Crear oficina con bienes
        oficina = Oficina.objects.create(
            codigo='CASCADE-001',
            nombre='Oficina Cascade',
            responsable='Responsable'
        )
        
        bienes = []
        for i in range(3):
            bien = BienPatrimonial.objects.create(
                codigo_patrimonial=f'PAT-CASCADE-{i:03d}',
                catalogo=self.catalogo,
                oficina=oficina,
                estado_bien='B',
                created_by=self.admin_user
            )
            bienes.append(bien)
        
        # 2. Eliminar oficina (debería manejar bienes relacionados)
        self.service.soft_delete_object(oficina, self.admin_user, 'Test cascade')
        
        # 3. Verificar que oficina está eliminada
        self.assertTrue(oficina.is_deleted)
        
        # 4. Verificar que bienes siguen existiendo pero con referencia a oficina eliminada
        for bien in bienes:
            bien.refresh_from_db()
            self.assertEqual(bien.oficina, oficina)


class RecycleBinWebIntegrationTest(TestCase):
    """Pruebas de integración de interfaz web"""
    
    def setUp(self):
        """Configurar datos de prueba"""
        self.admin_user = User.objects.create_user(
            username='admin',
            password='admin123',
            is_staff=True,
            is_superuser=True
        )
        
        # Asignar permisos
        perms = Permission.objects.filter(
            codename__in=['view_recyclebin', 'can_restore_items', 'can_permanent_delete']
        )
        self.admin_user.user_permissions.set(perms)
        
        self.client.login(username='admin', password='admin123')
        
        # Crear datos base
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

    def test_web_delete_to_recycle_bin_flow(self):
        """Prueba flujo de eliminación desde interfaz web"""
        # 1. Crear bien
        bien = BienPatrimonial.objects.create(
            codigo_patrimonial='PAT-WEB-001',
            catalogo=self.catalogo,
            oficina=self.oficina,
            estado_bien='B',
            created_by=self.admin_user
        )
        
        # 2. Eliminar desde interfaz web
        response = self.client.post(
            reverse('bienes:delete', kwargs={'pk': bien.id}),
            {'confirm': 'yes', 'reason': 'Test desde web'}
        )
        
        # 3. Verificar redirección
        self.assertEqual(response.status_code, 302)
        
        # 4. Verificar que está en papelera
        bien.refresh_from_db()
        self.assertTrue(bien.is_deleted)
        
        # 5. Verificar que aparece en lista de papelera
        response = self.client.get(reverse('core:recycle_bin_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'PAT-WEB-001')
    
    def test_web_restore_from_recycle_bin_flow(self):
        """Prueba flujo de restauración desde interfaz web"""
        # 1. Crear y eliminar bien
        bien = BienPatrimonial.objects.create(
            codigo_patrimonial='PAT-WEB-002',
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
        
        # 2. Restaurar desde interfaz web
        response = self.client.post(
            reverse('core:recycle_bin_restore', kwargs={'pk': recycle_entry.id})
        )
        
        # 3. Verificar redirección
        self.assertEqual(response.status_code, 302)
        
        # 4. Verificar que se restauró
        bien.refresh_from_db()
        self.assertFalse(bien.is_deleted)
        
        # 5. Verificar mensaje de éxito
        response = self.client.get(reverse('core:recycle_bin_list'))
        self.assertEqual(response.status_code, 200)
    
    def test_web_permanent_delete_flow(self):
        """Prueba flujo de eliminación permanente desde interfaz web"""
        # 1. Crear y eliminar bien
        bien = BienPatrimonial.objects.create(
            codigo_patrimonial='PAT-WEB-003',
            catalogo=self.catalogo,
            oficina=self.oficina,
            estado_bien='B',
            created_by=self.admin_user
        )
        
        bien_id = bien.id
        self.service.soft_delete_object(bien, self.admin_user, 'Test')
        
        recycle_entry = RecycleBin.objects.get(
            content_type__model='bienpatrimonial',
            object_id=bien_id
        )
        
        # 2. Eliminar permanentemente desde interfaz web
        response = self.client.post(
            reverse('core:recycle_bin_permanent_delete', kwargs={'pk': recycle_entry.id}),
            {'security_code': 'PERMANENT_DELETE_2024'}
        )
        
        # 3. Verificar redirección
        self.assertEqual(response.status_code, 302)
        
        # 4. Verificar que ya no existe
        with self.assertRaises(BienPatrimonial.DoesNotExist):
            BienPatrimonial.all_objects.get(id=bien_id)
    
    def test_web_filters_integration(self):
        """Prueba integración de filtros en interfaz web"""
        # 1. Crear objetos de diferentes módulos
        bien1 = BienPatrimonial.objects.create(
            codigo_patrimonial='PAT-FILTER-001',
            catalogo=self.catalogo,
            oficina=self.oficina,
            estado_bien='B',
            created_by=self.admin_user
        )
        
        oficina = Oficina.objects.create(
            codigo='FILTER-001',
            nombre='Oficina Filter',
            responsable='Responsable'
        )
        
        # 2. Eliminar ambos
        self.service.soft_delete_object(bien1, self.admin_user, 'Test')
        self.service.soft_delete_object(oficina, self.admin_user, 'Test')
        
        # 3. Filtrar por módulo bienes
        response = self.client.get(
            reverse('core:recycle_bin_list'),
            {'module': 'bienes'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'PAT-FILTER-001')
        self.assertNotContains(response, 'FILTER-001')
        
        # 4. Filtrar por módulo oficinas
        response = self.client.get(
            reverse('core:recycle_bin_list'),
            {'module': 'oficinas'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'FILTER-001')
        self.assertNotContains(response, 'PAT-FILTER-001')
