from django.test import TestCase
from django.contrib.auth.models import User
from django.core import mail
from django.utils import timezone
from datetime import timedelta
from apps.catalogo.models import Catalogo
from apps.oficinas.models import Oficina
from apps.bienes.models import BienPatrimonial, MovimientoBien
from .models import NotificacionEmail, ConfiguracionNotificacion, PlantillaEmail
from .utils import NotificationManager, EmailTemplateManager
from .tasks import enviar_notificacion_email, verificar_alertas_mantenimiento


class NotificacionEmailTest(TestCase):
    """Pruebas para el modelo NotificacionEmail"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
    
    def test_crear_notificacion_email(self):
        """Prueba crear notificación de email"""
        notificacion = NotificacionEmail.objects.create(
            destinatario='test@example.com',
            asunto='Prueba de notificación',
            mensaje='Este es un mensaje de prueba',
            tipo_notificacion='movimiento',
            usuario_relacionado=self.user
        )
        
        self.assertEqual(notificacion.destinatario, 'test@example.com')
        self.assertEqual(notificacion.tipo_notificacion, 'movimiento')
        self.assertEqual(notificacion.estado, 'pendiente')
        self.assertIsNotNone(notificacion.fecha_creacion)
    
    def test_marcar_como_enviado(self):
        """Prueba marcar notificación como enviada"""
        notificacion = NotificacionEmail.objects.create(
            destinatario='test@example.com',
            asunto='Prueba',
            mensaje='Mensaje de prueba',
            tipo_notificacion='movimiento'
        )
        
        notificacion.marcar_como_enviado()
        
        self.assertEqual(notificacion.estado, 'enviado')
        self.assertIsNotNone(notificacion.fecha_envio)
    
    def test_marcar_como_error(self):
        """Prueba marcar notificación con error"""
        notificacion = NotificacionEmail.objects.create(
            destinatario='test@example.com',
            asunto='Prueba',
            mensaje='Mensaje de prueba',
            tipo_notificacion='movimiento'
        )
        
        mensaje_error = "Error de conexión SMTP"
        notificacion.marcar_como_error(mensaje_error)
        
        self.assertEqual(notificacion.estado, 'error')
        self.assertEqual(notificacion.mensaje_error, mensaje_error)
        self.assertIsNotNone(notificacion.fecha_envio)
    
    def test_str_representation(self):
        """Prueba representación string de la notificación"""
        notificacion = NotificacionEmail(
            destinatario='test@example.com',
            asunto='Prueba de notificación',
            tipo_notificacion='movimiento'
        )
        
        expected = "movimiento - test@example.com - Prueba de notificación"
        self.assertEqual(str(notificacion), expected)


class ConfiguracionNotificacionTest(TestCase):
    """Pruebas para el modelo ConfiguracionNotificacion"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
    
    def test_crear_configuracion_notificacion(self):
        """Prueba crear configuración de notificación"""
        config = ConfiguracionNotificacion.objects.create(
            usuario=self.user,
            tipo_notificacion='movimiento',
            activa=True,
            configuracion={
                'email_enabled': True,
                'frequency': 'immediate',
                'include_details': True
            }
        )
        
        self.assertEqual(config.usuario, self.user)
        self.assertEqual(config.tipo_notificacion, 'movimiento')
        self.assertTrue(config.activa)
        self.assertTrue(config.configuracion['email_enabled'])
    
    def test_obtener_configuracion_usuario(self):
        """Prueba obtener configuración de usuario"""
        ConfiguracionNotificacion.objects.create(
            usuario=self.user,
            tipo_notificacion='movimiento',
            activa=True,
            configuracion={'email_enabled': True}
        )
        
        config = ConfiguracionNotificacion.obtener_configuracion(
            self.user, 'movimiento'
        )
        
        self.assertIsNotNone(config)
        self.assertTrue(config.activa)
        self.assertTrue(config.configuracion['email_enabled'])
    
    def test_configuracion_por_defecto(self):
        """Prueba configuración por defecto"""
        config = ConfiguracionNotificacion.obtener_configuracion(
            self.user, 'movimiento'
        )
        
        # Si no existe, debería crear una por defecto
        self.assertIsNotNone(config)
        self.assertTrue(config.activa)
        self.assertIn('email_enabled', config.configuracion)


class PlantillaEmailTest(TestCase):
    """Pruebas para el modelo PlantillaEmail"""
    
    def test_crear_plantilla_email(self):
        """Prueba crear plantilla de email"""
        plantilla = PlantillaEmail.objects.create(
            nombre='movimiento_bien',
            asunto='Movimiento de Bien Patrimonial',
            contenido_html='<p>Se ha registrado un movimiento del bien {{bien.codigo_patrimonial}}</p>',
            contenido_texto='Se ha registrado un movimiento del bien {{bien.codigo_patrimonial}}',
            tipo_notificacion='movimiento'
        )
        
        self.assertEqual(plantilla.nombre, 'movimiento_bien')
        self.assertEqual(plantilla.tipo_notificacion, 'movimiento')
        self.assertTrue(plantilla.activa)
    
    def test_renderizar_plantilla(self):
        """Prueba renderizado de plantilla"""
        plantilla = PlantillaEmail.objects.create(
            nombre='test_template',
            asunto='Prueba {{usuario.username}}',
            contenido_html='<p>Hola {{usuario.first_name}}</p>',
            contenido_texto='Hola {{usuario.first_name}}',
            tipo_notificacion='test'
        )
        
        user = User.objects.create_user(
            username='testuser',
            first_name='Juan',
            email='test@example.com'
        )
        
        contexto = {'usuario': user}
        asunto_renderizado, html_renderizado, texto_renderizado = plantilla.renderizar(contexto)
        
        self.assertEqual(asunto_renderizado, 'Prueba testuser')
        self.assertEqual(html_renderizado, '<p>Hola Juan</p>')
        self.assertEqual(texto_renderizado, 'Hola Juan')


class NotificationManagerTest(TestCase):
    """Pruebas para el gestor de notificaciones"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        
        # Crear datos de prueba
        self.catalogo = Catalogo.objects.create(
            codigo='04220001',
            denominacion='TEST BIEN',
            grupo='04-AGRÍCOLA Y PESQUERO',
            clase='22-EQUIPO',
            resolucion='R.D. 001-2024',
            estado='ACTIVO'
        )
        
        self.oficina_origen = Oficina.objects.create(
            codigo='ORI-001',
            nombre='Oficina Origen',
            responsable='Responsable Origen',
            email='origen@test.com'
        )
        
        self.oficina_destino = Oficina.objects.create(
            codigo='DES-001',
            nombre='Oficina Destino',
            responsable='Responsable Destino',
            email='destino@test.com'
        )
        
        self.bien = BienPatrimonial.objects.create(
            codigo_patrimonial='PAT-001-2024',
            catalogo=self.catalogo,
            oficina=self.oficina_origen,
            estado_bien='B',
            created_by=self.user
        )
        
        self.notification_manager = NotificationManager()
    
    def test_notificar_movimiento_bien(self):
        """Prueba notificación de movimiento de bien"""
        movimiento = MovimientoBien.objects.create(
            bien=self.bien,
            oficina_origen=self.oficina_origen,
            oficina_destino=self.oficina_destino,
            motivo='Reasignación administrativa',
            usuario=self.user
        )
        
        resultado = self.notification_manager.notificar_movimiento_bien(movimiento)
        
        self.assertTrue(resultado['success'])
        self.assertGreater(resultado['notificaciones_enviadas'], 0)
        
        # Verificar que se crearon las notificaciones
        notificaciones = NotificacionEmail.objects.filter(tipo_notificacion='movimiento')
        self.assertGreater(notificaciones.count(), 0)
    
    def test_notificar_cambio_estado(self):
        """Prueba notificación de cambio de estado"""
        resultado = self.notification_manager.notificar_cambio_estado(
            self.bien, 'B', 'R', 'Deterioro por uso', self.user
        )
        
        self.assertTrue(resultado['success'])
        
        # Verificar que se creó la notificación
        notificacion = NotificacionEmail.objects.filter(
            tipo_notificacion='cambio_estado'
        ).first()
        self.assertIsNotNone(notificacion)
        self.assertIn('PAT-001-2024', notificacion.asunto)
    
    def test_notificar_alerta_mantenimiento(self):
        """Prueba notificación de alerta de mantenimiento"""
        resultado = self.notification_manager.notificar_alerta_mantenimiento(
            self.bien, 'preventivo', 'Mantenimiento programado'
        )
        
        self.assertTrue(resultado['success'])
        
        # Verificar que se creó la notificación
        notificacion = NotificacionEmail.objects.filter(
            tipo_notificacion='mantenimiento'
        ).first()
        self.assertIsNotNone(notificacion)
        self.assertIn('mantenimiento', notificacion.asunto.lower())
    
    def test_notificar_depreciacion(self):
        """Prueba notificación de depreciación"""
        resultado = self.notification_manager.notificar_depreciacion(
            self.bien, 6  # 6 meses para depreciación
        )
        
        self.assertTrue(resultado['success'])
        
        # Verificar que se creó la notificación
        notificacion = NotificacionEmail.objects.filter(
            tipo_notificacion='depreciacion'
        ).first()
        self.assertIsNotNone(notificacion)
        self.assertIn('depreciación', notificacion.asunto.lower())


class EmailTemplateManagerTest(TestCase):
    """Pruebas para el gestor de plantillas de email"""
    
    def setUp(self):
        self.template_manager = EmailTemplateManager()
        
        # Crear plantilla de prueba
        self.plantilla = PlantillaEmail.objects.create(
            nombre='test_template',
            asunto='Prueba {{bien.codigo_patrimonial}}',
            contenido_html='<p>Bien: {{bien.denominacion}}</p>',
            contenido_texto='Bien: {{bien.denominacion}}',
            tipo_notificacion='test'
        )
        
        # Crear datos de prueba
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
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
        
        self.bien = BienPatrimonial.objects.create(
            codigo_patrimonial='PAT-001-2024',
            catalogo=self.catalogo,
            oficina=self.oficina,
            estado_bien='B',
            created_by=self.user
        )
    
    def test_obtener_plantilla(self):
        """Prueba obtener plantilla por tipo"""
        plantilla = self.template_manager.obtener_plantilla('test')
        
        self.assertIsNotNone(plantilla)
        self.assertEqual(plantilla.nombre, 'test_template')
    
    def test_renderizar_email(self):
        """Prueba renderizado de email"""
        contexto = {
            'bien': self.bien,
            'usuario': self.user
        }
        
        resultado = self.template_manager.renderizar_email('test', contexto)
        
        self.assertTrue(resultado['success'])
        self.assertEqual(resultado['asunto'], 'Prueba PAT-001-2024')
        self.assertIn('TEST BIEN', resultado['contenido_html'])
        self.assertIn('TEST BIEN', resultado['contenido_texto'])
    
    def test_crear_plantilla_desde_archivo(self):
        """Prueba crear plantilla desde archivo"""
        # Simular contenido de archivo
        contenido_plantilla = {
            'asunto': 'Nuevo movimiento {{bien.codigo_patrimonial}}',
            'contenido_html': '<h1>Movimiento registrado</h1><p>{{bien.denominacion}}</p>',
            'contenido_texto': 'Movimiento registrado: {{bien.denominacion}}'
        }
        
        plantilla = self.template_manager.crear_plantilla_desde_dict(
            'movimiento_nuevo',
            'movimiento',
            contenido_plantilla
        )
        
        self.assertIsNotNone(plantilla)
        self.assertEqual(plantilla.nombre, 'movimiento_nuevo')
        self.assertEqual(plantilla.tipo_notificacion, 'movimiento')


class NotificacionTasksTest(TestCase):
    """Pruebas para las tareas de notificación"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        
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
            responsable='Director Regional',
            email='director@test.com'
        )
        
        self.bien = BienPatrimonial.objects.create(
            codigo_patrimonial='PAT-001-2024',
            catalogo=self.catalogo,
            oficina=self.oficina,
            estado_bien='B',
            created_by=self.user
        )
    
    def test_enviar_notificacion_email_task(self):
        """Prueba tarea de envío de email"""
        # Crear notificación pendiente
        notificacion = NotificacionEmail.objects.create(
            destinatario='test@example.com',
            asunto='Prueba de notificación',
            mensaje='Este es un mensaje de prueba',
            tipo_notificacion='test'
        )
        
        # Ejecutar tarea
        resultado = enviar_notificacion_email(notificacion.id)
        
        self.assertTrue(resultado['success'])
        
        # Verificar que se marcó como enviado
        notificacion.refresh_from_db()
        self.assertEqual(notificacion.estado, 'enviado')
        
        # Verificar que se envió el email
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['test@example.com'])
        self.assertEqual(mail.outbox[0].subject, 'Prueba de notificación')
    
    def test_verificar_alertas_mantenimiento_task(self):
        """Prueba tarea de verificación de alertas de mantenimiento"""
        # Simular bien que necesita mantenimiento
        # (esto dependería de la lógica específica de mantenimiento)
        
        resultado = verificar_alertas_mantenimiento()
        
        self.assertTrue(resultado['success'])
        self.assertIn('alertas_generadas', resultado)
    
    def test_enviar_notificacion_email_error(self):
        """Prueba manejo de errores en envío de email"""
        # Crear notificación con email inválido
        notificacion = NotificacionEmail.objects.create(
            destinatario='email-invalido',
            asunto='Prueba',
            mensaje='Mensaje de prueba',
            tipo_notificacion='test'
        )
        
        # Ejecutar tarea
        resultado = enviar_notificacion_email(notificacion.id)
        
        self.assertFalse(resultado['success'])
        self.assertIn('error', resultado)
        
        # Verificar que se marcó como error
        notificacion.refresh_from_db()
        self.assertEqual(notificacion.estado, 'error')
        self.assertIsNotNone(notificacion.mensaje_error)


class NotificacionIntegrationTest(TestCase):
    """Pruebas de integración para notificaciones"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        
        # Crear configuración de notificaciones
        ConfiguracionNotificacion.objects.create(
            usuario=self.user,
            tipo_notificacion='movimiento',
            activa=True,
            configuracion={'email_enabled': True}
        )
        
        # Crear plantilla
        PlantillaEmail.objects.create(
            nombre='movimiento_bien',
            asunto='Movimiento de Bien {{bien.codigo_patrimonial}}',
            contenido_html='<p>Se ha movido el bien {{bien.denominacion}}</p>',
            contenido_texto='Se ha movido el bien {{bien.denominacion}}',
            tipo_notificacion='movimiento'
        )
        
        # Crear datos de prueba
        self.catalogo = Catalogo.objects.create(
            codigo='04220001',
            denominacion='TEST BIEN',
            grupo='04-AGRÍCOLA Y PESQUERO',
            clase='22-EQUIPO',
            resolucion='R.D. 001-2024',
            estado='ACTIVO'
        )
        
        self.oficina_origen = Oficina.objects.create(
            codigo='ORI-001',
            nombre='Oficina Origen',
            responsable='Responsable Origen',
            email='origen@test.com'
        )
        
        self.oficina_destino = Oficina.objects.create(
            codigo='DES-001',
            nombre='Oficina Destino',
            responsable='Responsable Destino',
            email='destino@test.com'
        )
        
        self.bien = BienPatrimonial.objects.create(
            codigo_patrimonial='PAT-001-2024',
            catalogo=self.catalogo,
            oficina=self.oficina_origen,
            estado_bien='B',
            created_by=self.user
        )
    
    def test_flujo_completo_notificacion_movimiento(self):
        """Prueba flujo completo de notificación de movimiento"""
        # Crear movimiento
        movimiento = MovimientoBien.objects.create(
            bien=self.bien,
            oficina_origen=self.oficina_origen,
            oficina_destino=self.oficina_destino,
            motivo='Reasignación administrativa',
            usuario=self.user
        )
        
        # Notificar movimiento
        notification_manager = NotificationManager()
        resultado = notification_manager.notificar_movimiento_bien(movimiento)
        
        self.assertTrue(resultado['success'])
        
        # Verificar que se crearon las notificaciones
        notificaciones = NotificacionEmail.objects.filter(tipo_notificacion='movimiento')
        self.assertGreater(notificaciones.count(), 0)
        
        # Procesar notificaciones pendientes
        for notificacion in notificaciones.filter(estado='pendiente'):
            resultado_envio = enviar_notificacion_email(notificacion.id)
            self.assertTrue(resultado_envio['success'])
        
        # Verificar que se enviaron los emails
        self.assertGreater(len(mail.outbox), 0)
        
        # Verificar contenido del email
        email_enviado = mail.outbox[0]
        self.assertIn('PAT-001-2024', email_enviado.subject)
        self.assertIn('TEST BIEN', email_enviado.body)