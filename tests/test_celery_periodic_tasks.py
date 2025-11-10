"""
Tests para tareas periódicas de Celery
"""
import os
import django

# Configurar Django antes de importar modelos
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'patrimonio.settings')
django.setup()

import pytest
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from unittest.mock import patch, MagicMock

from apps.core.models import RecycleBin, RecycleBinConfig, AuditLog
from apps.core.tasks import (
    cleanup_recycle_bin_task,
    send_recycle_bin_warnings,
    send_recycle_bin_final_warnings
)
from apps.notificaciones.models import Notificacion, TipoNotificacion
from apps.oficinas.models import Oficina


@pytest.mark.django_db
class TestCleanupRecycleBinTask:
    """Tests para la tarea de limpieza automática de papelera"""
    
    def test_cleanup_no_items_to_delete(self):
        """Verifica que no se elimine nada si no hay elementos listos"""
        resultado = cleanup_recycle_bin_task()
        
        assert resultado['status'] == 'success'
        assert resultado['eliminados'] == 0
        assert 'No hay elementos para eliminar' in resultado['mensaje']
    
    def test_cleanup_deletes_expired_items(self, django_user_model):
        """Verifica que se eliminen elementos que han excedido su tiempo de retención"""
        # Crear usuario
        user = django_user_model.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Crear configuración
        config = RecycleBinConfig.objects.create(
            module_name='oficinas',
            retention_days=30,
            auto_delete_enabled=True
        )
        
        # Crear oficina
        oficina = Oficina.objects.create(
            codigo='TEST001',
            nombre='Oficina Test',
            direccion='Test Address'
        )
        
        # Soft delete de la oficina
        oficina.delete()
        
        # Obtener el item de RecycleBin y modificar auto_delete_at para que esté en el pasado
        recycle_item = RecycleBin.objects.get(object_id=oficina.id)
        recycle_item.auto_delete_at = timezone.now() - timedelta(days=1)
        recycle_item.save()
        
        # Ejecutar tarea
        resultado = cleanup_recycle_bin_task()
        
        # Verificar resultados
        assert resultado['status'] == 'success'
        assert resultado['eliminados'] == 1
        assert resultado['total_encontrados'] == 1
        
        # Verificar que el item fue eliminado de RecycleBin
        assert not RecycleBin.objects.filter(id=recycle_item.id).exists()
        
        # Verificar que se creó un log de auditoría
        audit_log = AuditLog.objects.filter(
            action='delete',
            object_id=str(oficina.id)
        ).first()
        assert audit_log is not None
        assert audit_log.changes['tipo'] == 'eliminacion_automatica'
    
    def test_cleanup_respects_auto_delete_disabled(self, django_user_model):
        """Verifica que no se eliminen elementos si auto_delete está deshabilitado"""
        user = django_user_model.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Crear configuración con auto_delete deshabilitado
        config = RecycleBinConfig.objects.create(
            module_name='oficinas',
            retention_days=30,
            auto_delete_enabled=False
        )
        
        # Crear y eliminar oficina
        oficina = Oficina.objects.create(
            codigo='TEST001',
            nombre='Oficina Test',
            direccion='Test Address'
        )
        oficina.delete()
        
        # Modificar auto_delete_at para que esté en el pasado
        recycle_item = RecycleBin.objects.get(object_id=oficina.id)
        recycle_item.auto_delete_at = timezone.now() - timedelta(days=1)
        recycle_item.save()
        
        # Ejecutar tarea
        resultado = cleanup_recycle_bin_task()
        
        # Verificar que no se eliminó nada
        assert resultado['status'] == 'success'
        assert resultado['eliminados'] == 0
        assert RecycleBin.objects.filter(id=recycle_item.id).exists()
    
    def test_cleanup_handles_errors_gracefully(self, django_user_model):
        """Verifica que los errores se manejen correctamente"""
        user = django_user_model.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        config = RecycleBinConfig.objects.create(
            module_name='oficinas',
            retention_days=30,
            auto_delete_enabled=True
        )
        
        # Crear oficina
        oficina = Oficina.objects.create(
            codigo='TEST001',
            nombre='Oficina Test',
            direccion='Test Address'
        )
        oficina.delete()
        
        # Modificar auto_delete_at
        recycle_item = RecycleBin.objects.get(object_id=oficina.id)
        recycle_item.auto_delete_at = timezone.now() - timedelta(days=1)
        recycle_item.save()
        
        # Simular error en hard_delete
        with patch.object(Oficina, 'hard_delete', side_effect=Exception('Test error')):
            resultado = cleanup_recycle_bin_task()
        
        # Verificar que se registró el error
        assert resultado['status'] == 'success'
        assert len(resultado['errores']) > 0
        assert 'Test error' in resultado['errores'][0]['error']
    
    def test_cleanup_multiple_modules(self, django_user_model):
        """Verifica que se procesen múltiples módulos correctamente"""
        user = django_user_model.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Crear configuraciones para múltiples módulos
        config1 = RecycleBinConfig.objects.create(
            module_name='oficinas',
            retention_days=30,
            auto_delete_enabled=True
        )
        
        config2 = RecycleBinConfig.objects.create(
            module_name='catalogo',
            retention_days=60,
            auto_delete_enabled=True
        )
        
        # Crear y eliminar oficinas
        oficina1 = Oficina.objects.create(
            codigo='TEST001',
            nombre='Oficina Test 1',
            direccion='Test Address 1'
        )
        oficina1.delete()
        
        oficina2 = Oficina.objects.create(
            codigo='TEST002',
            nombre='Oficina Test 2',
            direccion='Test Address 2'
        )
        oficina2.delete()
        
        # Modificar auto_delete_at para ambos
        for oficina in [oficina1, oficina2]:
            recycle_item = RecycleBin.objects.get(object_id=oficina.id)
            recycle_item.auto_delete_at = timezone.now() - timedelta(days=1)
            recycle_item.save()
        
        # Ejecutar tarea
        resultado = cleanup_recycle_bin_task()
        
        # Verificar resultados
        assert resultado['status'] == 'success'
        assert resultado['eliminados'] == 2
        assert 'oficinas' in resultado['modulos']


@pytest.mark.django_db
class TestSendRecycleBinWarnings:
    """Tests para la tarea de envío de advertencias (7 días)"""
    
    def test_no_warnings_when_no_items(self):
        """Verifica que no se envíen advertencias si no hay elementos"""
        resultado = send_recycle_bin_warnings()
        
        assert resultado['status'] == 'success'
        assert resultado['notificaciones_enviadas'] == 0
        assert resultado['usuarios_notificados'] == 0
    
    def test_send_warning_for_items_7_days_before_deletion(self, django_user_model):
        """Verifica que se envíen advertencias para elementos a 7 días de eliminación"""
        # Crear usuario
        user = django_user_model.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Crear tipo de notificación
        tipo_notif = TipoNotificacion.objects.create(
            codigo='RECYCLE_WARNING',
            nombre='Advertencia de Papelera',
            descripcion='Advertencia de eliminación próxima',
            activo=True
        )
        
        # Crear configuración
        config = RecycleBinConfig.objects.create(
            module_name='oficinas',
            retention_days=30,
            auto_delete_enabled=True
        )
        
        # Crear oficina
        oficina = Oficina.objects.create(
            codigo='TEST001',
            nombre='Oficina Test',
            direccion='Test Address'
        )
        oficina.delete()
        
        # Modificar auto_delete_at para que sea en 7 días
        recycle_item = RecycleBin.objects.get(object_id=oficina.id)
        recycle_item.auto_delete_at = timezone.now() + timedelta(days=7, hours=2)
        recycle_item.deleted_by = user
        recycle_item.save()
        
        # Ejecutar tarea
        resultado = send_recycle_bin_warnings()
        
        # Verificar resultados
        assert resultado['status'] == 'success'
        assert resultado['notificaciones_enviadas'] == 1
        assert resultado['usuarios_notificados'] == 1
        assert user.username in resultado['usuarios']
        
        # Verificar que se creó la notificación
        notificacion = Notificacion.objects.filter(
            usuario=user,
            tipo_notificacion=tipo_notif
        ).first()
        assert notificacion is not None
        assert '7 días' in notificacion.titulo
        assert notificacion.prioridad == 'ALTA'
    
    def test_no_duplicate_warnings(self, django_user_model):
        """Verifica que no se envíen advertencias duplicadas"""
        user = django_user_model.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        tipo_notif = TipoNotificacion.objects.create(
            codigo='RECYCLE_WARNING',
            nombre='Advertencia de Papelera',
            descripcion='Advertencia de eliminación próxima',
            activo=True
        )
        
        config = RecycleBinConfig.objects.create(
            module_name='oficinas',
            retention_days=30,
            auto_delete_enabled=True
        )
        
        oficina = Oficina.objects.create(
            codigo='TEST001',
            nombre='Oficina Test',
            direccion='Test Address'
        )
        oficina.delete()
        
        recycle_item = RecycleBin.objects.get(object_id=oficina.id)
        recycle_item.auto_delete_at = timezone.now() + timedelta(days=7, hours=2)
        recycle_item.deleted_by = user
        recycle_item.save()
        
        # Ejecutar tarea primera vez
        resultado1 = send_recycle_bin_warnings()
        assert resultado1['notificaciones_enviadas'] == 1
        
        # Ejecutar tarea segunda vez (debería detectar notificación reciente)
        resultado2 = send_recycle_bin_warnings()
        assert resultado2['notificaciones_enviadas'] == 0
    
    def test_warning_respects_user_preferences(self, django_user_model):
        """Verifica que se respeten las preferencias del usuario"""
        from apps.notificaciones.models import ConfiguracionNotificacion
        
        user = django_user_model.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        tipo_notif = TipoNotificacion.objects.create(
            codigo='RECYCLE_WARNING',
            nombre='Advertencia de Papelera',
            descripcion='Advertencia de eliminación próxima',
            activo=True
        )
        
        # Deshabilitar notificaciones para el usuario
        ConfiguracionNotificacion.objects.create(
            usuario=user,
            tipo_notificacion=tipo_notif,
            activa=False
        )
        
        config = RecycleBinConfig.objects.create(
            module_name='oficinas',
            retention_days=30,
            auto_delete_enabled=True
        )
        
        oficina = Oficina.objects.create(
            codigo='TEST001',
            nombre='Oficina Test',
            direccion='Test Address'
        )
        oficina.delete()
        
        recycle_item = RecycleBin.objects.get(object_id=oficina.id)
        recycle_item.auto_delete_at = timezone.now() + timedelta(days=7, hours=2)
        recycle_item.deleted_by = user
        recycle_item.save()
        
        # Ejecutar tarea
        resultado = send_recycle_bin_warnings()
        
        # No debería enviar notificación
        assert resultado['notificaciones_enviadas'] == 0


@pytest.mark.django_db
class TestSendRecycleBinFinalWarnings:
    """Tests para la tarea de envío de advertencias finales (1 día)"""
    
    def test_send_final_warning_for_items_1_day_before_deletion(self, django_user_model):
        """Verifica que se envíen advertencias finales para elementos a 1 día de eliminación"""
        user = django_user_model.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        tipo_notif = TipoNotificacion.objects.create(
            codigo='RECYCLE_FINAL_WARNING',
            nombre='Advertencia Final de Papelera',
            descripcion='Advertencia final de eliminación',
            activo=True
        )
        
        config = RecycleBinConfig.objects.create(
            module_name='oficinas',
            retention_days=30,
            auto_delete_enabled=True
        )
        
        oficina = Oficina.objects.create(
            codigo='TEST001',
            nombre='Oficina Test',
            direccion='Test Address'
        )
        oficina.delete()
        
        # Modificar auto_delete_at para que sea en 1 día
        recycle_item = RecycleBin.objects.get(object_id=oficina.id)
        recycle_item.auto_delete_at = timezone.now() + timedelta(days=1, hours=2)
        recycle_item.deleted_by = user
        recycle_item.save()
        
        # Ejecutar tarea
        resultado = send_recycle_bin_final_warnings()
        
        # Verificar resultados
        assert resultado['status'] == 'success'
        assert resultado['notificaciones_enviadas'] == 1
        assert resultado['usuarios_notificados'] == 1
        
        # Verificar que se creó la notificación
        notificacion = Notificacion.objects.filter(
            usuario=user,
            tipo_notificacion=tipo_notif
        ).first()
        assert notificacion is not None
        assert '24 horas' in notificacion.titulo
        assert notificacion.prioridad == 'CRITICA'
        assert 'hours_remaining' in notificacion.datos_contexto
    
    def test_final_warning_includes_hours_remaining(self, django_user_model):
        """Verifica que la advertencia final incluya las horas restantes"""
        user = django_user_model.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        tipo_notif = TipoNotificacion.objects.create(
            codigo='RECYCLE_FINAL_WARNING',
            nombre='Advertencia Final de Papelera',
            descripcion='Advertencia final de eliminación',
            activo=True
        )
        
        config = RecycleBinConfig.objects.create(
            module_name='oficinas',
            retention_days=30,
            auto_delete_enabled=True
        )
        
        oficina = Oficina.objects.create(
            codigo='TEST001',
            nombre='Oficina Test',
            direccion='Test Address'
        )
        oficina.delete()
        
        # Modificar auto_delete_at para que sea en 12 horas
        recycle_item = RecycleBin.objects.get(object_id=oficina.id)
        recycle_item.auto_delete_at = timezone.now() + timedelta(hours=12)
        recycle_item.deleted_by = user
        recycle_item.save()
        
        # Ejecutar tarea
        resultado = send_recycle_bin_final_warnings()
        
        # Verificar notificación
        notificacion = Notificacion.objects.filter(
            usuario=user,
            tipo_notificacion=tipo_notif
        ).first()
        assert notificacion is not None
        assert notificacion.datos_contexto['hours_remaining'] >= 0
        assert notificacion.datos_contexto['hours_remaining'] <= 24
    
    def test_final_warning_multiple_items(self, django_user_model):
        """Verifica que se agrupen múltiples elementos en una sola notificación"""
        user = django_user_model.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        tipo_notif = TipoNotificacion.objects.create(
            codigo='RECYCLE_FINAL_WARNING',
            nombre='Advertencia Final de Papelera',
            descripcion='Advertencia final de eliminación',
            activo=True
        )
        
        config = RecycleBinConfig.objects.create(
            module_name='oficinas',
            retention_days=30,
            auto_delete_enabled=True
        )
        
        # Crear múltiples oficinas
        for i in range(3):
            oficina = Oficina.objects.create(
                codigo=f'TEST00{i+1}',
                nombre=f'Oficina Test {i+1}',
                direccion=f'Test Address {i+1}'
            )
            oficina.delete()
            
            recycle_item = RecycleBin.objects.get(object_id=oficina.id)
            recycle_item.auto_delete_at = timezone.now() + timedelta(days=1, hours=2)
            recycle_item.deleted_by = user
            recycle_item.save()
        
        # Ejecutar tarea
        resultado = send_recycle_bin_final_warnings()
        
        # Debería crear solo 1 notificación para los 3 elementos
        assert resultado['notificaciones_enviadas'] == 1
        
        # Verificar que la notificación incluye los 3 elementos
        notificacion = Notificacion.objects.filter(
            usuario=user,
            tipo_notificacion=tipo_notif
        ).first()
        assert notificacion is not None
        assert notificacion.datos_contexto['total_items'] == 3


@pytest.mark.django_db
class TestCeleryBeatSchedule:
    """Tests para verificar la configuración de Celery Beat"""
    
    def test_beat_schedule_configuration(self):
        """Verifica que la configuración de Celery Beat esté correctamente definida"""
        from patrimonio.celery import app
        
        beat_schedule = app.conf.beat_schedule
        
        # Verificar que existen las tareas de papelera
        assert 'cleanup-recycle-bin-daily' in beat_schedule
        assert 'send-recycle-bin-warnings-daily' in beat_schedule
        assert 'send-recycle-bin-final-warnings-every-6h' in beat_schedule
        
        # Verificar configuración de cleanup
        cleanup_config = beat_schedule['cleanup-recycle-bin-daily']
        assert cleanup_config['task'] == 'apps.core.tasks.cleanup_recycle_bin_task'
        assert 'schedule' in cleanup_config
        assert cleanup_config['options']['queue'] == 'maintenance'
        
        # Verificar configuración de warnings
        warnings_config = beat_schedule['send-recycle-bin-warnings-daily']
        assert warnings_config['task'] == 'apps.core.tasks.send_recycle_bin_warnings'
        assert warnings_config['options']['queue'] == 'notifications'
        
        # Verificar configuración de final warnings
        final_warnings_config = beat_schedule['send-recycle-bin-final-warnings-every-6h']
        assert final_warnings_config['task'] == 'apps.core.tasks.send_recycle_bin_final_warnings'
        assert final_warnings_config['options']['queue'] == 'notifications'
    
    def test_task_routes_configuration(self):
        """Verifica que las rutas de tareas estén correctamente configuradas"""
        from patrimonio.celery import app
        
        task_routes = app.conf.task_routes
        
        # Verificar rutas de tareas de papelera
        assert 'apps.core.tasks.cleanup_recycle_bin_task' in task_routes
        assert task_routes['apps.core.tasks.cleanup_recycle_bin_task']['queue'] == 'maintenance'
        
        assert 'apps.core.tasks.send_recycle_bin_warnings' in task_routes
        assert task_routes['apps.core.tasks.send_recycle_bin_warnings']['queue'] == 'notifications'
        
        assert 'apps.core.tasks.send_recycle_bin_final_warnings' in task_routes
        assert task_routes['apps.core.tasks.send_recycle_bin_final_warnings']['queue'] == 'notifications'


@pytest.mark.django_db
class TestTaskIntegration:
    """Tests de integración para el flujo completo de tareas"""
    
    def test_complete_lifecycle(self, django_user_model):
        """Verifica el ciclo de vida completo: advertencia -> advertencia final -> eliminación"""
        user = django_user_model.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Crear tipos de notificación
        tipo_warning = TipoNotificacion.objects.create(
            codigo='RECYCLE_WARNING',
            nombre='Advertencia de Papelera',
            activo=True
        )
        
        tipo_final = TipoNotificacion.objects.create(
            codigo='RECYCLE_FINAL_WARNING',
            nombre='Advertencia Final de Papelera',
            activo=True
        )
        
        config = RecycleBinConfig.objects.create(
            module_name='oficinas',
            retention_days=30,
            auto_delete_enabled=True
        )
        
        oficina = Oficina.objects.create(
            codigo='TEST001',
            nombre='Oficina Test',
            direccion='Test Address'
        )
        oficina_id = oficina.id
        oficina.delete()
        
        recycle_item = RecycleBin.objects.get(object_id=oficina_id)
        recycle_item.deleted_by = user
        recycle_item.save()
        
        # Fase 1: Advertencia de 7 días
        recycle_item.auto_delete_at = timezone.now() + timedelta(days=7, hours=2)
        recycle_item.save()
        
        resultado_warning = send_recycle_bin_warnings()
        assert resultado_warning['notificaciones_enviadas'] == 1
        assert Notificacion.objects.filter(tipo_notificacion=tipo_warning).count() == 1
        
        # Fase 2: Advertencia final de 1 día
        recycle_item.auto_delete_at = timezone.now() + timedelta(days=1, hours=2)
        recycle_item.save()
        
        resultado_final = send_recycle_bin_final_warnings()
        assert resultado_final['notificaciones_enviadas'] == 1
        assert Notificacion.objects.filter(tipo_notificacion=tipo_final).count() == 1
        
        # Fase 3: Eliminación automática
        recycle_item.auto_delete_at = timezone.now() - timedelta(hours=1)
        recycle_item.save()
        
        resultado_cleanup = cleanup_recycle_bin_task()
        assert resultado_cleanup['eliminados'] == 1
        assert not RecycleBin.objects.filter(id=recycle_item.id).exists()
        
        # Verificar que se creó log de auditoría
        audit_log = AuditLog.objects.filter(
            action='delete',
            object_id=str(oficina_id)
        ).first()
        assert audit_log is not None
