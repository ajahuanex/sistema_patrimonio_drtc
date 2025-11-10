"""
Tests para el sistema de notificaciones de papelera de reciclaje
"""
from datetime import timedelta
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from django.core import mail
from unittest.mock import patch, MagicMock

from apps.core.models import RecycleBin, RecycleBinConfig
from apps.notificaciones.models import (
    TipoNotificacion, ConfiguracionNotificacion, Notificacion
)
from apps.notificaciones.tasks import (
    verificar_alertas_papelera, enviar_notificaciones_advertencia,
    notificar_eliminacion_automatica
)
from apps.notificaciones.utils import (
    notificar_advertencia_papelera, configurar_preferencias_papelera,
    obtener_preferencias_papelera, notificar_restauracion_exitosa,
    notificar_eliminacion_permanente
)
from apps.oficinas.models import Oficina
from django.contrib.contenttypes.models import ContentType


class TestNotificacionesPapelera(TestCase):
    """Tests para notificaciones de papelera de reciclaje"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        # Crear usuarios
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='testuser1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='testuser2@example.com',
            password='testpass123'
        )
        
        # Crear tipos de notificación
        self.tipo_warning = TipoNotificacion.objects.create(
            codigo='RECYCLE_WARNING',
            nombre='Advertencia de Papelera',
            activo=True,
            enviar_email=True,
            plantilla_email='notificaciones/email_recycle_warning.html'
        )
        
        self.tipo_final_warning = TipoNotificacion.objects.create(
            codigo='RECYCLE_FINAL_WARNING',
            nombre='Advertencia Final de Papelera',
            activo=True,
            enviar_email=True,
            plantilla_email='notificaciones/email_recycle_final_warning.html'
        )
        
        self.tipo_sistema = TipoNotificacion.objects.create(
            codigo='SISTEMA',
            nombre='Sistema',
            activo=True,
            enviar_email=True
        )
        
        # Crear configuración de papelera
        self.config = RecycleBinConfig.objects.create(
            module_name='oficinas',
            retention_days=30,
            auto_delete_enabled=True,
            warning_days_before=7,
            final_warning_days_before=1
        )
        
        # Crear oficina de prueba
        self.oficina = Oficina.objects.create(
            codigo='TEST001',
            nombre='Oficina Test',
            direccion='Dirección Test',
            created_by=self.user1
        )
        
        # Soft delete de la oficina
        self.oficina.soft_delete(user=self.user1, reason='Test')
        
        # Crear entrada en RecycleBin
        content_type = ContentType.objects.get_for_model(Oficina)
        self.recycle_entry = RecycleBin.objects.create(
            content_type=content_type,
            object_id=self.oficina.id,
            object_repr=str(self.oficina),
            module_name='oficinas',
            deleted_by=self.user1,
            deletion_reason='Test',
            auto_delete_at=timezone.now() + timedelta(days=7)
        )
    
    def test_crear_tipos_notificacion(self):
        """Test: Verificar que los tipos de notificación se crean correctamente"""
        self.assertEqual(self.tipo_warning.codigo, 'RECYCLE_WARNING')
        self.assertEqual(self.tipo_final_warning.codigo, 'RECYCLE_FINAL_WARNING')
        self.assertTrue(self.tipo_warning.activo)
        self.assertTrue(self.tipo_final_warning.activo)
    
    def test_notificar_advertencia_papelera_7_dias(self):
        """Test: Crear notificación de advertencia de 7 días"""
        notificar_advertencia_papelera(
            usuario=self.user1,
            items_count=5,
            dias_restantes=7,
            modulo='Oficinas'
        )
        
        notificacion = Notificacion.objects.filter(
            usuario=self.user1,
            tipo_notificacion=self.tipo_warning
        ).first()
        
        self.assertIsNotNone(notificacion)
        self.assertIn('5 elemento(s)', notificacion.titulo)
        self.assertIn('7 días', notificacion.titulo)
        self.assertEqual(notificacion.prioridad, 'ALTA')
        self.assertEqual(notificacion.datos_contexto['items_count'], 5)
    
    def test_notificar_advertencia_papelera_1_dia(self):
        """Test: Crear notificación de advertencia final de 1 día"""
        notificar_advertencia_papelera(
            usuario=self.user1,
            items_count=3,
            dias_restantes=1,
            modulo='Bienes'
        )
        
        notificacion = Notificacion.objects.filter(
            usuario=self.user1,
            tipo_notificacion=self.tipo_final_warning
        ).first()
        
        self.assertIsNotNone(notificacion)
        self.assertIn('ADVERTENCIA FINAL', notificacion.titulo)
        self.assertIn('24 horas', notificacion.titulo)
        self.assertEqual(notificacion.prioridad, 'CRITICA')
    
    def test_configurar_preferencias_papelera(self):
        """Test: Configurar preferencias de notificaciones de papelera"""
        configuraciones = configurar_preferencias_papelera(
            usuario=self.user1,
            recibir_advertencias=True,
            recibir_advertencias_finales=True
        )
        
        self.assertIn('warning', configuraciones)
        self.assertIn('final_warning', configuraciones)
        
        config_warning = configuraciones['warning']
        self.assertTrue(config_warning.activa)
        self.assertTrue(config_warning.enviar_email)
        self.assertEqual(config_warning.usuario, self.user1)
    
    def test_obtener_preferencias_papelera(self):
        """Test: Obtener preferencias de notificaciones de papelera"""
        # Configurar preferencias primero
        configurar_preferencias_papelera(
            usuario=self.user1,
            recibir_advertencias=True,
            recibir_advertencias_finales=False
        )
        
        preferencias = obtener_preferencias_papelera(self.user1)
        
        self.assertTrue(preferencias['recibir_advertencias'])
        self.assertFalse(preferencias['recibir_advertencias_finales'])
    
    def test_obtener_preferencias_papelera_sin_configuracion(self):
        """Test: Obtener preferencias cuando no hay configuración (valores por defecto)"""
        preferencias = obtener_preferencias_papelera(self.user2)
        
        # Valores por defecto
        self.assertTrue(preferencias['recibir_advertencias'])
        self.assertTrue(preferencias['recibir_advertencias_finales'])
    
    def test_verificar_alertas_papelera_7_dias(self):
        """Test: Verificar alertas de papelera para elementos a 7 días"""
        # Configurar entrada para advertencia de 7 días
        self.recycle_entry.auto_delete_at = timezone.now() + timedelta(days=7)
        self.recycle_entry.save()
        
        # Ejecutar verificación
        resultado = verificar_alertas_papelera()
        
        # Verificar que se generó notificación
        notificaciones = Notificacion.objects.filter(
            usuario=self.user1,
            tipo_notificacion=self.tipo_warning
        )
        
        self.assertGreater(notificaciones.count(), 0)
    
    def test_verificar_alertas_papelera_1_dia(self):
        """Test: Verificar alertas de papelera para elementos a 1 día"""
        # Configurar entrada para advertencia final de 1 día
        self.recycle_entry.auto_delete_at = timezone.now() + timedelta(hours=23)
        self.recycle_entry.save()
        
        # Ejecutar verificación
        resultado = verificar_alertas_papelera()
        
        # Verificar que se generó notificación final
        notificaciones = Notificacion.objects.filter(
            usuario=self.user1,
            tipo_notificacion=self.tipo_final_warning
        )
        
        self.assertGreater(notificaciones.count(), 0)
    
    def test_no_duplicar_notificaciones_recientes(self):
        """Test: No crear notificaciones duplicadas si ya existe una reciente"""
        # Crear notificación reciente
        Notificacion.objects.create(
            usuario=self.user1,
            tipo_notificacion=self.tipo_warning,
            titulo='Test',
            mensaje='Test',
            created_at=timezone.now()
        )
        
        # Configurar entrada para advertencia
        self.recycle_entry.auto_delete_at = timezone.now() + timedelta(days=7)
        self.recycle_entry.save()
        
        # Ejecutar verificación
        verificar_alertas_papelera()
        
        # Verificar que no se duplicó
        notificaciones = Notificacion.objects.filter(
            usuario=self.user1,
            tipo_notificacion=self.tipo_warning
        )
        
        self.assertEqual(notificaciones.count(), 1)
    
    def test_respetar_preferencias_usuario(self):
        """Test: Respetar preferencias de notificación del usuario"""
        # Deshabilitar notificaciones de advertencia
        configurar_preferencias_papelera(
            usuario=self.user1,
            recibir_advertencias=False,
            recibir_advertencias_finales=True
        )
        
        # Configurar entrada para advertencia de 7 días
        self.recycle_entry.auto_delete_at = timezone.now() + timedelta(days=7)
        self.recycle_entry.save()
        
        # Ejecutar verificación
        verificar_alertas_papelera()
        
        # Verificar que NO se creó notificación
        notificaciones = Notificacion.objects.filter(
            usuario=self.user1,
            tipo_notificacion=self.tipo_warning
        )
        
        self.assertEqual(notificaciones.count(), 0)
    
    def test_notificacion_agrupada_por_modulo(self):
        """Test: Notificaciones agrupadas por módulo"""
        # Crear múltiples entradas del mismo usuario
        for i in range(3):
            oficina = Oficina.objects.create(
                codigo=f'TEST{i:03d}',
                nombre=f'Oficina Test {i}',
                direccion='Dirección Test',
                created_by=self.user1
            )
            oficina.soft_delete(user=self.user1)
            
            content_type = ContentType.objects.get_for_model(Oficina)
            RecycleBin.objects.create(
                content_type=content_type,
                object_id=oficina.id,
                object_repr=str(oficina),
                module_name='oficinas',
                deleted_by=self.user1,
                auto_delete_at=timezone.now() + timedelta(days=7)
            )
        
        # Ejecutar verificación
        verificar_alertas_papelera()
        
        # Verificar que se creó UNA notificación con todos los elementos
        notificaciones = Notificacion.objects.filter(
            usuario=self.user1,
            tipo_notificacion=self.tipo_warning
        )
        
        self.assertEqual(notificaciones.count(), 1)
        notificacion = notificaciones.first()
        
        # Verificar que incluye todos los elementos
        self.assertGreaterEqual(notificacion.datos_contexto['total_items'], 4)
    
    def test_notificar_restauracion_exitosa(self):
        """Test: Notificar restauración exitosa"""
        notificar_restauracion_exitosa(
            usuario=self.user1,
            objeto_repr='Oficina Test',
            modulo='Oficinas'
        )
        
        notificacion = Notificacion.objects.filter(
            usuario=self.user1,
            tipo_notificacion=self.tipo_sistema
        ).first()
        
        self.assertIsNotNone(notificacion)
        self.assertIn('restaurado', notificacion.titulo.lower())
        self.assertIn('Oficina Test', notificacion.titulo)
    
    def test_notificar_eliminacion_permanente(self):
        """Test: Notificar eliminación permanente"""
        notificar_eliminacion_permanente(
            usuario=self.user1,
            objeto_repr='Oficina Test',
            modulo='Oficinas'
        )
        
        notificacion = Notificacion.objects.filter(
            usuario=self.user1,
            tipo_notificacion=self.tipo_sistema
        ).first()
        
        self.assertIsNotNone(notificacion)
        self.assertIn('eliminado permanentemente', notificacion.mensaje.lower())
        self.assertEqual(notificacion.prioridad, 'ALTA')
    
    def test_notificar_eliminacion_automatica(self):
        """Test: Notificar eliminación automática"""
        # Crear algunas entradas
        recycle_ids = [self.recycle_entry.id]
        
        # Ejecutar notificación
        resultado = notificar_eliminacion_automatica(recycle_ids)
        
        # Verificar que se creó notificación
        notificaciones = Notificacion.objects.filter(
            usuario=self.user1,
            tipo_notificacion=self.tipo_sistema
        )
        
        self.assertGreater(notificaciones.count(), 0)
        notificacion = notificaciones.first()
        self.assertIn('Eliminación automática', notificacion.titulo)
    
    def test_datos_contexto_notificacion_warning(self):
        """Test: Verificar datos de contexto en notificación de advertencia"""
        # Configurar entrada
        self.recycle_entry.auto_delete_at = timezone.now() + timedelta(days=7)
        self.recycle_entry.save()
        
        # Ejecutar verificación
        verificar_alertas_papelera()
        
        # Obtener notificación
        notificacion = Notificacion.objects.filter(
            usuario=self.user1,
            tipo_notificacion=self.tipo_warning
        ).first()
        
        self.assertIsNotNone(notificacion)
        
        # Verificar datos de contexto
        contexto = notificacion.datos_contexto
        self.assertIn('items_by_module', contexto)
        self.assertIn('total_items', contexto)
        self.assertIn('retention_days', contexto)
        self.assertGreater(contexto['total_items'], 0)
    
    def test_prioridad_notificaciones(self):
        """Test: Verificar prioridades correctas de notificaciones"""
        # Advertencia de 7 días
        notificar_advertencia_papelera(
            usuario=self.user1,
            items_count=5,
            dias_restantes=7
        )
        
        notif_warning = Notificacion.objects.filter(
            usuario=self.user1,
            tipo_notificacion=self.tipo_warning
        ).first()
        
        self.assertEqual(notif_warning.prioridad, 'ALTA')
        
        # Advertencia final de 1 día
        notificar_advertencia_papelera(
            usuario=self.user2,
            items_count=3,
            dias_restantes=1
        )
        
        notif_final = Notificacion.objects.filter(
            usuario=self.user2,
            tipo_notificacion=self.tipo_final_warning
        ).first()
        
        self.assertEqual(notif_final.prioridad, 'CRITICA')
    
    def test_url_accion_en_notificaciones(self):
        """Test: Verificar que las notificaciones incluyen URL de acción"""
        notificar_advertencia_papelera(
            usuario=self.user1,
            items_count=5,
            dias_restantes=7
        )
        
        notificacion = Notificacion.objects.filter(
            usuario=self.user1,
            tipo_notificacion=self.tipo_warning
        ).first()
        
        self.assertIsNotNone(notificacion.url_accion)
        self.assertIn('recycle-bin', notificacion.url_accion)
    
    def test_fecha_expiracion_notificaciones(self):
        """Test: Verificar fechas de expiración de notificaciones"""
        # Advertencia de 7 días
        notificar_advertencia_papelera(
            usuario=self.user1,
            items_count=5,
            dias_restantes=7
        )
        
        notif_warning = Notificacion.objects.filter(
            usuario=self.user1,
            tipo_notificacion=self.tipo_warning
        ).first()
        
        # Debe expirar en aproximadamente 7 días
        dias_hasta_expiracion = (notif_warning.fecha_expiracion - timezone.now()).days
        self.assertGreaterEqual(dias_hasta_expiracion, 6)
        self.assertLessEqual(dias_hasta_expiracion, 8)
    
    def test_multiples_usuarios_diferentes_elementos(self):
        """Test: Notificaciones separadas para diferentes usuarios"""
        # Crear elemento para user2
        oficina2 = Oficina.objects.create(
            codigo='TEST999',
            nombre='Oficina User2',
            direccion='Dirección Test',
            created_by=self.user2
        )
        oficina2.soft_delete(user=self.user2)
        
        content_type = ContentType.objects.get_for_model(Oficina)
        RecycleBin.objects.create(
            content_type=content_type,
            object_id=oficina2.id,
            object_repr=str(oficina2),
            module_name='oficinas',
            deleted_by=self.user2,
            auto_delete_at=timezone.now() + timedelta(days=7)
        )
        
        # Configurar entrada de user1
        self.recycle_entry.auto_delete_at = timezone.now() + timedelta(days=7)
        self.recycle_entry.save()
        
        # Ejecutar verificación
        verificar_alertas_papelera()
        
        # Verificar que cada usuario tiene su notificación
        notif_user1 = Notificacion.objects.filter(
            usuario=self.user1,
            tipo_notificacion=self.tipo_warning
        ).count()
        
        notif_user2 = Notificacion.objects.filter(
            usuario=self.user2,
            tipo_notificacion=self.tipo_warning
        ).count()
        
        self.assertGreater(notif_user1, 0)
        self.assertGreater(notif_user2, 0)


class TestEmailsNotificacionesPapelera(TestCase):
    """Tests para emails de notificaciones de papelera"""
    
    def setUp(self):
        """Configuración inicial"""
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass123'
        )
        
        self.tipo_warning = TipoNotificacion.objects.create(
            codigo='RECYCLE_WARNING',
            nombre='Advertencia de Papelera',
            activo=True,
            enviar_email=True,
            plantilla_email='notificaciones/email_recycle_warning.html'
        )
    
    def test_template_email_warning_existe(self):
        """Test: Verificar que el template de email de advertencia existe"""
        from django.template.loader import get_template
        
        try:
            template = get_template('notificaciones/email_recycle_warning.html')
            self.assertIsNotNone(template)
        except Exception as e:
            self.fail(f'Template no encontrado: {str(e)}')
    
    def test_template_email_final_warning_existe(self):
        """Test: Verificar que el template de email de advertencia final existe"""
        from django.template.loader import get_template
        
        try:
            template = get_template('notificaciones/email_recycle_final_warning.html')
            self.assertIsNotNone(template)
        except Exception as e:
            self.fail(f'Template no encontrado: {str(e)}')


if __name__ == '__main__':
    import unittest
    unittest.main()
