import json
import uuid
from django.test import TestCase
from django.contrib.auth.models import User, Permission
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from apps.catalogo.models import Catalogo
from apps.oficinas.models import Oficina
from apps.bienes.models import BienPatrimonial, HistorialEstado
from .models import SesionMovil, SincronizacionOffline, ConfiguracionMovil
from .serializers import BienPatrimonialMobileSerializer, HistorialEstadoMobileSerializer
from .tasks import procesar_sincronizacion_offline


class SesionMovilTest(TestCase):
    """Pruebas para el modelo SesionMovil"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_crear_sesion_movil(self):
        """Prueba crear sesión móvil"""
        sesion = SesionMovil.objects.create(
            usuario=self.user,
            device_id='test-device-123',
            device_info={
                'platform': 'Android',
                'version': '11.0',
                'model': 'Samsung Galaxy S21'
            },
            ip_address='192.168.1.100'
        )
        
        self.assertEqual(sesion.usuario, self.user)
        self.assertEqual(sesion.device_id, 'test-device-123')
        self.assertTrue(sesion.activa)
        self.assertIsNotNone(sesion.fecha_inicio)
    
    def test_finalizar_sesion(self):
        """Prueba finalizar sesión móvil"""
        sesion = SesionMovil.objects.create(
            usuario=self.user,
            device_id='test-device-123',
            ip_address='192.168.1.100'
        )
        
        sesion.finalizar_sesion()
        
        self.assertFalse(sesion.activa)
        self.assertIsNotNone(sesion.fecha_fin)
    
    def test_duracion_sesion(self):
        """Prueba cálculo de duración de sesión"""
        sesion = SesionMovil.objects.create(
            usuario=self.user,
            device_id='test-device-123',
            ip_address='192.168.1.100'
        )
        
        # Simular sesión finalizada
        sesion.finalizar_sesion()
        
        duracion = sesion.duracion_sesion()
        self.assertIsNotNone(duracion)
        self.assertGreaterEqual(duracion.total_seconds(), 0)


class SincronizacionOfflineTest(TestCase):
    """Pruebas para el modelo SincronizacionOffline"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
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
            estado=True
        )
        
        self.bien = BienPatrimonial.objects.create(
            codigo_patrimonial='PAT-001-2024',
            catalogo=self.catalogo,
            oficina=self.oficina,
            estado_bien='B',
            created_by=self.user
        )
    
    def test_crear_sincronizacion_offline(self):
        """Prueba crear registro de sincronización offline"""
        sync = SincronizacionOffline.objects.create(
            usuario=self.user,
            device_id='test-device-123',
            tipo_operacion='update_estado',
            datos_operacion={
                'bien_id': self.bien.id,
                'estado_anterior': 'B',
                'estado_nuevo': 'R',
                'observaciones': 'Cambio offline'
            },
            timestamp_operacion='2024-01-15T10:30:00Z'
        )
        
        self.assertEqual(sync.usuario, self.user)
        self.assertEqual(sync.tipo_operacion, 'update_estado')
        self.assertEqual(sync.estado, 'pendiente')
        self.assertIsNotNone(sync.fecha_creacion)
    
    def test_marcar_como_procesado(self):
        """Prueba marcar sincronización como procesada"""
        sync = SincronizacionOffline.objects.create(
            usuario=self.user,
            device_id='test-device-123',
            tipo_operacion='update_estado',
            datos_operacion={'bien_id': self.bien.id}
        )
        
        sync.marcar_como_procesado()
        
        self.assertEqual(sync.estado, 'procesado')
        self.assertIsNotNone(sync.fecha_procesamiento)
    
    def test_marcar_como_error(self):
        """Prueba marcar sincronización con error"""
        sync = SincronizacionOffline.objects.create(
            usuario=self.user,
            device_id='test-device-123',
            tipo_operacion='update_estado',
            datos_operacion={'bien_id': self.bien.id}
        )
        
        mensaje_error = "Error de validación"
        sync.marcar_como_error(mensaje_error)
        
        self.assertEqual(sync.estado, 'error')
        self.assertEqual(sync.mensaje_error, mensaje_error)
        self.assertIsNotNone(sync.fecha_procesamiento)


class ConfiguracionMovilTest(TestCase):
    """Pruebas para el modelo ConfiguracionMovil"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_crear_configuracion_movil(self):
        """Prueba crear configuración móvil"""
        config = ConfiguracionMovil.objects.create(
            usuario=self.user,
            configuracion={
                'sync_interval': 300,
                'offline_mode': True,
                'auto_backup': True,
                'image_quality': 'medium'
            }
        )
        
        self.assertEqual(config.usuario, self.user)
        self.assertTrue(config.configuracion['offline_mode'])
        self.assertEqual(config.configuracion['sync_interval'], 300)
    
    def test_obtener_configuracion_usuario(self):
        """Prueba obtener configuración de usuario"""
        ConfiguracionMovil.objects.create(
            usuario=self.user,
            configuracion={'sync_interval': 600}
        )
        
        config = ConfiguracionMovil.obtener_configuracion(self.user)
        
        self.assertIsNotNone(config)
        self.assertEqual(config.configuracion['sync_interval'], 600)
    
    def test_configuracion_por_defecto(self):
        """Prueba configuración por defecto"""
        config = ConfiguracionMovil.obtener_configuracion(self.user)
        
        # Si no existe, debería crear una por defecto
        self.assertIsNotNone(config)
        self.assertIn('sync_interval', config.configuracion)
        self.assertIn('offline_mode', config.configuracion)


class BienPatrimonialMobileSerializerTest(TestCase):
    """Pruebas para el serializer móvil de bienes"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Crear datos de prueba
        self.catalogo = Catalogo.objects.create(
            codigo='04220001',
            denominacion='ELECTROEYACULADOR PARA BOVINOS',
            grupo='04-AGRÍCOLA Y PESQUERO',
            clase='22-EQUIPO',
            resolucion='R.D. 001-2024',
            estado='ACTIVO'
        )
        
        self.oficina = Oficina.objects.create(
            codigo='DIR-001',
            nombre='Dirección Regional',
            responsable='Director Regional',
            estado=True
        )
        
        self.bien = BienPatrimonial.objects.create(
            codigo_patrimonial='PAT-001-2024',
            catalogo=self.catalogo,
            oficina=self.oficina,
            estado_bien='B',
            marca='MARCA TEST',
            modelo='MODELO TEST',
            serie='SER123456',
            created_by=self.user
        )
    
    def test_serializar_bien_completo(self):
        """Prueba serialización completa de bien"""
        serializer = BienPatrimonialMobileSerializer(self.bien)
        data = serializer.data
        
        self.assertEqual(data['codigo_patrimonial'], 'PAT-001-2024')
        self.assertEqual(data['denominacion'], 'ELECTROEYACULADOR PARA BOVINOS')
        self.assertEqual(data['estado_bien']['codigo'], 'B')
        self.assertEqual(data['estado_bien']['descripcion'], 'Bueno')
        self.assertEqual(data['oficina']['codigo'], 'DIR-001')
        self.assertEqual(data['oficina']['nombre'], 'Dirección Regional')
        self.assertIn('qr_code', data)
        self.assertIn('url_qr', data)
    
    def test_campos_optimizados_movil(self):
        """Prueba que incluye campos optimizados para móvil"""
        serializer = BienPatrimonialMobileSerializer(self.bien)
        data = serializer.data
        
        # Campos específicos para móvil
        self.assertIn('es_vehiculo', data)
        self.assertIn('ubicacion_completa', data)
        self.assertIn('responsable_actual', data)
        self.assertIn('fecha_ultimo_movimiento', data)
    
    def test_serializar_lista_bienes(self):
        """Prueba serialización de lista de bienes"""
        # Crear otro bien
        bien2 = BienPatrimonial.objects.create(
            codigo_patrimonial='PAT-002-2024',
            catalogo=self.catalogo,
            oficina=self.oficina,
            estado_bien='R',
            created_by=self.user
        )
        
        bienes = [self.bien, bien2]
        serializer = BienPatrimonialMobileSerializer(bienes, many=True)
        data = serializer.data
        
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['codigo_patrimonial'], 'PAT-001-2024')
        self.assertEqual(data[1]['codigo_patrimonial'], 'PAT-002-2024')


class MobileAPITest(APITestCase):
    """Pruebas para las APIs móviles"""
    
    def setUp(self):
        # Crear usuario con permisos
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        
        # Agregar permisos necesarios
        permission = Permission.objects.get(codename='change_bienpatrimonial')
        self.user.user_permissions.add(permission)
        
        # Crear datos de prueba
        self.catalogo = Catalogo.objects.create(
            codigo='04220001',
            denominacion='ELECTROEYACULADOR PARA BOVINOS',
            grupo='04-AGRÍCOLA Y PESQUERO',
            clase='22-EQUIPO',
            resolucion='R.D. 001-2024',
            estado='ACTIVO'
        )
        
        self.oficina = Oficina.objects.create(
            codigo='DIR-001',
            nombre='Dirección Regional',
            responsable='Director Regional',
            estado=True
        )
        
        self.bien = BienPatrimonial.objects.create(
            codigo_patrimonial='PAT-001-2024',
            catalogo=self.catalogo,
            oficina=self.oficina,
            estado_bien='B',
            created_by=self.user
        )
        
        # Autenticar usuario
        self.client.force_authenticate(user=self.user)
    
    def test_mobile_login_api(self):
        """Prueba API de login móvil"""
        self.client.force_authenticate(user=None)
        
        url = reverse('mobile:login')
        data = {
            'username': 'testuser',
            'password': 'testpass123',
            'device_info': {
                'platform': 'Android',
                'version': '11.0',
                'model': 'Test Device'
            }
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('access_token', response.data)
        self.assertIn('refresh_token', response.data)
        self.assertIn('user_info', response.data)
        self.assertIn('permissions', response.data)
    
    def test_mobile_inventory_api(self):
        """Prueba API de inventario móvil"""
        url = reverse('mobile:inventory')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('bienes', response.data)
        self.assertIn('pagination', response.data)
        self.assertEqual(len(response.data['bienes']), 1)
    
    def test_mobile_inventory_with_filters(self):
        """Prueba API de inventario con filtros"""
        url = reverse('mobile:inventory')
        params = {
            'oficina_id': self.oficina.id,
            'estado': 'B',
            'search': 'PAT-001'
        }
        
        response = self.client.get(url, params)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['bienes']), 1)
        self.assertEqual(response.data['bienes'][0]['codigo_patrimonial'], 'PAT-001-2024')
    
    def test_mobile_scan_qr_api(self):
        """Prueba API de escaneo QR móvil"""
        url = reverse('mobile:scan_qr')
        data = {
            'qr_code': self.bien.qr_code,
            'device_info': {
                'user_agent': 'Mobile App v1.0',
                'location': {
                    'latitude': -15.8422,
                    'longitude': -70.0199
                }
            }
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['bien']['codigo_patrimonial'], 'PAT-001-2024')
        self.assertIn('permissions', response.data)
        self.assertIn('estados_disponibles', response.data)
    
    def test_mobile_update_estado_api(self):
        """Prueba API de actualización de estado móvil"""
        url = reverse('mobile:update_estado')
        data = {
            'bien_id': self.bien.id,
            'estado_nuevo': 'R',
            'observaciones': 'Cambio desde móvil',
            'ubicacion_gps': '-15.8422,-70.0199',
            'foto_base64': None,
            'device_info': {
                'timestamp': '2024-01-15T10:30:00Z',
                'user_agent': 'Mobile App v1.0'
            }
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['bien_actualizado']['estado_bien']['codigo'], 'R')
        
        # Verificar que se creó el historial
        historial = HistorialEstado.objects.filter(bien=self.bien).first()
        self.assertIsNotNone(historial)
        self.assertEqual(historial.estado_anterior, 'B')
        self.assertEqual(historial.estado_nuevo, 'R')
    
    def test_mobile_sync_offline_api(self):
        """Prueba API de sincronización offline"""
        url = reverse('mobile:sync_offline')
        data = {
            'device_id': 'test-device-123',
            'operaciones': [
                {
                    'tipo': 'update_estado',
                    'timestamp': '2024-01-15T10:30:00Z',
                    'datos': {
                        'bien_id': self.bien.id,
                        'estado_anterior': 'B',
                        'estado_nuevo': 'R',
                        'observaciones': 'Cambio offline'
                    }
                }
            ]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['operaciones_procesadas'], 1)
        self.assertEqual(response.data['operaciones_con_error'], 0)
        
        # Verificar que se creó el registro de sincronización
        sync = SincronizacionOffline.objects.filter(usuario=self.user).first()
        self.assertIsNotNone(sync)
        self.assertEqual(sync.tipo_operacion, 'update_estado')
    
    def test_mobile_config_api(self):
        """Prueba API de configuración móvil"""
        url = reverse('mobile:config')
        
        # GET - obtener configuración
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('configuracion', response.data)
        
        # POST - actualizar configuración
        new_config = {
            'sync_interval': 600,
            'offline_mode': True,
            'auto_backup': False,
            'image_quality': 'high'
        }
        
        response = self.client.post(url, {'configuracion': new_config}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verificar que se guardó la configuración
        config = ConfiguracionMovil.obtener_configuracion(self.user)
        self.assertEqual(config.configuracion['sync_interval'], 600)
        self.assertTrue(config.configuracion['offline_mode'])
    
    def test_mobile_session_management(self):
        """Prueba gestión de sesiones móviles"""
        # Iniciar sesión
        url = reverse('mobile:start_session')
        data = {
            'device_id': 'test-device-123',
            'device_info': {
                'platform': 'Android',
                'version': '11.0'
            }
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('session_id', response.data)
        
        # Verificar que se creó la sesión
        sesion = SesionMovil.objects.filter(usuario=self.user, device_id='test-device-123').first()
        self.assertIsNotNone(sesion)
        self.assertTrue(sesion.activa)
        
        # Finalizar sesión
        url = reverse('mobile:end_session')
        data = {'session_id': sesion.id}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verificar que se finalizó la sesión
        sesion.refresh_from_db()
        self.assertFalse(sesion.activa)
    
    def test_unauthorized_access(self):
        """Prueba acceso no autorizado"""
        self.client.force_authenticate(user=None)
        
        url = reverse('mobile:inventory')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_insufficient_permissions(self):
        """Prueba permisos insuficientes"""
        # Crear usuario sin permisos
        user_no_perms = User.objects.create_user(
            username='noperms',
            password='testpass123'
        )
        self.client.force_authenticate(user=user_no_perms)
        
        # Intentar actualizar estado
        url = reverse('mobile:update_estado')
        data = {
            'bien_id': self.bien.id,
            'estado_nuevo': 'R'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class SincronizacionOfflineTaskTest(TestCase):
    """Pruebas para las tareas de sincronización offline"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Agregar permisos
        permission = Permission.objects.get(codename='change_bienpatrimonial')
        self.user.user_permissions.add(permission)
        
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
            estado=True
        )
        
        self.bien = BienPatrimonial.objects.create(
            codigo_patrimonial='PAT-001-2024',
            catalogo=self.catalogo,
            oficina=self.oficina,
            estado_bien='B',
            created_by=self.user
        )
    
    def test_procesar_sincronizacion_update_estado(self):
        """Prueba procesamiento de sincronización de actualización de estado"""
        # Crear registro de sincronización
        sync = SincronizacionOffline.objects.create(
            usuario=self.user,
            device_id='test-device-123',
            tipo_operacion='update_estado',
            datos_operacion={
                'bien_id': self.bien.id,
                'estado_anterior': 'B',
                'estado_nuevo': 'R',
                'observaciones': 'Cambio offline',
                'ubicacion_gps': '-15.8422,-70.0199'
            },
            timestamp_operacion='2024-01-15T10:30:00Z'
        )
        
        # Procesar sincronización
        resultado = procesar_sincronizacion_offline(sync.id)
        
        self.assertTrue(resultado['success'])
        
        # Verificar que se actualizó el bien
        self.bien.refresh_from_db()
        self.assertEqual(self.bien.estado_bien, 'R')
        
        # Verificar que se creó el historial
        historial = HistorialEstado.objects.filter(bien=self.bien).first()
        self.assertIsNotNone(historial)
        self.assertEqual(historial.estado_anterior, 'B')
        self.assertEqual(historial.estado_nuevo, 'R')
        
        # Verificar que se marcó como procesado
        sync.refresh_from_db()
        self.assertEqual(sync.estado, 'procesado')
    
    def test_procesar_sincronizacion_error(self):
        """Prueba procesamiento de sincronización con error"""
        # Crear registro con datos inválidos
        sync = SincronizacionOffline.objects.create(
            usuario=self.user,
            device_id='test-device-123',
            tipo_operacion='update_estado',
            datos_operacion={
                'bien_id': 99999,  # ID inexistente
                'estado_nuevo': 'R'
            }
        )
        
        # Procesar sincronización
        resultado = procesar_sincronizacion_offline(sync.id)
        
        self.assertFalse(resultado['success'])
        self.assertIn('error', resultado)
        
        # Verificar que se marcó como error
        sync.refresh_from_db()
        self.assertEqual(sync.estado, 'error')
        self.assertIsNotNone(sync.mensaje_error)