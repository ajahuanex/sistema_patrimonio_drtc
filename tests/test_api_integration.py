"""
Pruebas de integración para todas las APIs del sistema
"""
import json
import uuid
from django.test import TestCase
from django.contrib.auth.models import User, Permission
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from apps.catalogo.models import Catalogo
from apps.oficinas.models import Oficina
from apps.bienes.models import BienPatrimonial, MovimientoBien, HistorialEstado
from apps.reportes.models import ConfiguracionFiltro, HistorialReporte
from apps.mobile.models import SesionMovil, ConfiguracionMovil
from apps.notificaciones.models import NotificacionEmail


class APIAuthenticationTest(APITestCase):
    """Pruebas de autenticación de la API"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.client = APIClient()
    
    def test_jwt_token_obtain(self):
        """Prueba obtención de token JWT"""
        url = reverse('token_obtain_pair')
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
    
    def test_jwt_token_refresh(self):
        """Prueba renovación de token JWT"""
        refresh = RefreshToken.for_user(self.user)
        
        url = reverse('token_refresh')
        data = {'refresh': str(refresh)}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
    
    def test_protected_endpoint_without_token(self):
        """Prueba acceso a endpoint protegido sin token"""
        url = reverse('bienes:api_list')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_protected_endpoint_with_token(self):
        """Prueba acceso a endpoint protegido con token"""
        refresh = RefreshToken.for_user(self.user)
        access_token = refresh.access_token
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        url = reverse('bienes:api_list')
        response = self.client.get(url)
        
        # Debería permitir acceso (aunque puede devolver 200 con lista vacía)
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN])


class BienesAPIIntegrationTest(APITestCase):
    """Pruebas de integración para la API de bienes"""
    
    def setUp(self):
        # Crear usuario con permisos
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        
        # Agregar permisos necesarios
        permissions = Permission.objects.filter(
            codename__in=['add_bienpatrimonial', 'change_bienpatrimonial', 'view_bienpatrimonial']
        )
        self.user.user_permissions.set(permissions)
        
        # Autenticar usuario
        self.client.force_authenticate(user=self.user)
        
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
            created_by=self.user
        )
    
    def test_listar_bienes_api(self):
        """Prueba listar bienes via API"""
        url = reverse('bienes:api_list')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['codigo_patrimonial'], 'PAT-001-2024')
    
    def test_crear_bien_api(self):
        """Prueba crear bien via API"""
        url = reverse('bienes:api_list')
        data = {
            'codigo_patrimonial': 'PAT-002-2024',
            'catalogo': self.catalogo.id,
            'oficina': self.oficina.id,
            'estado_bien': 'N',
            'marca': 'NUEVA MARCA',
            'modelo': 'NUEVO MODELO'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['codigo_patrimonial'], 'PAT-002-2024')
        
        # Verificar que se creó en la base de datos
        bien_creado = BienPatrimonial.objects.get(codigo_patrimonial='PAT-002-2024')
        self.assertEqual(bien_creado.marca, 'NUEVA MARCA')
    
    def test_obtener_bien_detalle_api(self):
        """Prueba obtener detalle de bien via API"""
        url = reverse('bienes:api_detail', kwargs={'pk': self.bien.id})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['codigo_patrimonial'], 'PAT-001-2024')
        self.assertEqual(response.data['denominacion'], 'ELECTROEYACULADOR PARA BOVINOS')
    
    def test_actualizar_bien_api(self):
        """Prueba actualizar bien via API"""
        url = reverse('bienes:api_detail', kwargs={'pk': self.bien.id})
        data = {
            'codigo_patrimonial': 'PAT-001-2024',
            'catalogo': self.catalogo.id,
            'oficina': self.oficina.id,
            'estado_bien': 'R',  # Cambiar estado
            'marca': 'MARCA ACTUALIZADA',
            'modelo': 'MODELO TEST'
        }
        
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['estado_bien'], 'R')
        self.assertEqual(response.data['marca'], 'MARCA ACTUALIZADA')
        
        # Verificar que se actualizó en la base de datos
        self.bien.refresh_from_db()
        self.assertEqual(self.bien.estado_bien, 'R')
    
    def test_filtrar_bienes_api(self):
        """Prueba filtrar bienes via API"""
        # Crear otro bien con estado diferente
        BienPatrimonial.objects.create(
            codigo_patrimonial='PAT-003-2024',
            catalogo=self.catalogo,
            oficina=self.oficina,
            estado_bien='R',
            created_by=self.user
        )
        
        url = reverse('bienes:api_list')
        
        # Filtrar por estado
        response = self.client.get(url, {'estado_bien': 'B'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['estado_bien'], 'B')
    
    def test_buscar_bienes_api(self):
        """Prueba búsqueda de bienes via API"""
        url = reverse('bienes:api_list')
        
        response = self.client.get(url, {'search': 'PAT-001'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['codigo_patrimonial'], 'PAT-001-2024')


class CatalogoAPIIntegrationTest(APITestCase):
    """Pruebas de integración para la API de catálogo"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        self.catalogo = Catalogo.objects.create(
            codigo='04220001',
            denominacion='TEST BIEN',
            grupo='04-AGRÍCOLA Y PESQUERO',
            clase='22-EQUIPO',
            resolucion='R.D. 001-2024',
            estado='ACTIVO'
        )
    
    def test_listar_catalogo_api(self):
        """Prueba listar catálogo via API"""
        url = reverse('catalogo:api_list')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_buscar_catalogo_api(self):
        """Prueba búsqueda en catálogo via API"""
        url = reverse('catalogo:api_search')
        
        response = self.client.get(url, {'q': 'TEST'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)
    
    def test_obtener_grupos_api(self):
        """Prueba obtener grupos del catálogo via API"""
        url = reverse('catalogo:api_grupos')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('04-AGRÍCOLA Y PESQUERO', response.data['grupos'])


class OficinasAPIIntegrationTest(APITestCase):
    """Pruebas de integración para la API de oficinas"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        self.oficina = Oficina.objects.create(
            codigo='DIR-001',
            nombre='Dirección Regional',
            responsable='Director Regional',
            estado=True
        )
    
    def test_listar_oficinas_api(self):
        """Prueba listar oficinas via API"""
        url = reverse('oficinas:api_list')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_crear_oficina_api(self):
        """Prueba crear oficina via API"""
        url = reverse('oficinas:api_list')
        data = {
            'codigo': 'ADM-001',
            'nombre': 'Administración',
            'responsable': 'Administrador',
            'estado': True
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['codigo'], 'ADM-001')
    
    def test_obtener_oficinas_activas_api(self):
        """Prueba obtener solo oficinas activas via API"""
        # Crear oficina inactiva
        Oficina.objects.create(
            codigo='INA-001',
            nombre='Oficina Inactiva',
            responsable='Responsable',
            estado=False
        )
        
        url = reverse('oficinas:api_activas')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Solo debe devolver oficinas activas
        for oficina in response.data['results']:
            self.assertTrue(oficina['estado'])


class ReportesAPIIntegrationTest(APITestCase):
    """Pruebas de integración para la API de reportes"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
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
    
    def test_generar_reporte_api(self):
        """Prueba generar reporte via API"""
        url = reverse('reportes:api_generar_reporte')
        data = {
            'filtros': {'estado_bien': 'B'},
            'formato': 'json'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('data', response.data)
        self.assertEqual(len(response.data['data']), 1)
    
    def test_obtener_estadisticas_api(self):
        """Prueba obtener estadísticas via API"""
        url = reverse('reportes:api_estadisticas')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_bienes', response.data)
        self.assertIn('por_estado', response.data)
        self.assertIn('por_oficina', response.data)
    
    def test_guardar_configuracion_filtro_api(self):
        """Prueba guardar configuración de filtro via API"""
        url = reverse('reportes:api_configuraciones_filtro')
        data = {
            'nombre': 'Filtro Test API',
            'descripcion': 'Filtro creado via API',
            'filtros': {'estado_bien': 'B', 'oficina_id': self.oficina.id}
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['nombre'], 'Filtro Test API')
        
        # Verificar que se creó en la base de datos
        config = ConfiguracionFiltro.objects.get(nombre='Filtro Test API')
        self.assertEqual(config.usuario, self.user)
    
    def test_historial_reportes_api(self):
        """Prueba obtener historial de reportes via API"""
        # Crear historial
        HistorialReporte.objects.create(
            usuario=self.user,
            tipo_reporte='inventario_completo',
            formato_exportacion='excel',
            total_registros=1
        )
        
        url = reverse('reportes:api_historial_reportes')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 1)


class MobileAPIIntegrationTest(APITestCase):
    """Pruebas de integración para la API móvil"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        
        # Agregar permisos
        permission = Permission.objects.get(codename='change_bienpatrimonial')
        self.user.user_permissions.add(permission)
        
        self.client.force_authenticate(user=self.user)
        
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
    
    def test_mobile_login_flow(self):
        """Prueba flujo completo de login móvil"""
        self.client.force_authenticate(user=None)
        
        # Login
        url = reverse('mobile:login')
        data = {
            'username': 'testuser',
            'password': 'testpass123',
            'device_info': {
                'platform': 'Android',
                'version': '11.0'
            }
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('access_token', response.data)
        
        # Usar token para acceder a endpoint protegido
        access_token = response.data['access_token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        inventory_url = reverse('mobile:inventory')
        inventory_response = self.client.get(inventory_url)
        
        self.assertEqual(inventory_response.status_code, status.HTTP_200_OK)
    
    def test_mobile_scan_and_update_flow(self):
        """Prueba flujo completo de escaneo y actualización móvil"""
        # Escanear QR
        scan_url = reverse('mobile:scan_qr')
        scan_data = {
            'qr_code': self.bien.qr_code,
            'device_info': {'location': {'latitude': -15.8422, 'longitude': -70.0199}}
        }
        
        scan_response = self.client.post(scan_url, scan_data, format='json')
        
        self.assertEqual(scan_response.status_code, status.HTTP_200_OK)
        self.assertTrue(scan_response.data['success'])
        self.assertEqual(scan_response.data['bien']['codigo_patrimonial'], 'PAT-001-2024')
        
        # Actualizar estado
        update_url = reverse('mobile:update_estado')
        update_data = {
            'bien_id': self.bien.id,
            'estado_nuevo': 'R',
            'observaciones': 'Cambio desde móvil',
            'ubicacion_gps': '-15.8422,-70.0199'
        }
        
        update_response = self.client.post(update_url, update_data, format='json')
        
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertTrue(update_response.data['success'])
        
        # Verificar que se actualizó
        self.bien.refresh_from_db()
        self.assertEqual(self.bien.estado_bien, 'R')
    
    def test_mobile_offline_sync_flow(self):
        """Prueba flujo de sincronización offline"""
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


class APIErrorHandlingTest(APITestCase):
    """Pruebas de manejo de errores en las APIs"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_not_found_error(self):
        """Prueba error 404 en API"""
        url = reverse('bienes:api_detail', kwargs={'pk': 99999})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_validation_error(self):
        """Prueba error de validación en API"""
        url = reverse('bienes:api_list')
        data = {
            'codigo_patrimonial': '',  # Campo requerido vacío
            'catalogo': 99999,  # ID inexistente
            'oficina': 99999    # ID inexistente
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data)
    
    def test_permission_denied_error(self):
        """Prueba error de permisos en API"""
        # Crear usuario sin permisos
        user_no_perms = User.objects.create_user(
            username='noperms',
            password='testpass123'
        )
        self.client.force_authenticate(user=user_no_perms)
        
        url = reverse('bienes:api_list')
        data = {
            'codigo_patrimonial': 'PAT-TEST-001',
            'catalogo': 1,
            'oficina': 1
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_method_not_allowed_error(self):
        """Prueba error de método no permitido"""
        url = reverse('bienes:api_list')
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class APIPerformanceTest(APITestCase):
    """Pruebas de rendimiento básicas para las APIs"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Crear datos de prueba en cantidad
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
        
        # Crear múltiples bienes
        for i in range(50):
            BienPatrimonial.objects.create(
                codigo_patrimonial=f'PAT-{i:03d}-2024',
                catalogo=self.catalogo,
                oficina=self.oficina,
                estado_bien='B',
                created_by=self.user
            )
    
    def test_list_bienes_pagination(self):
        """Prueba paginación en listado de bienes"""
        url = reverse('bienes:api_list')
        
        response = self.client.get(url, {'page_size': 10})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)
        self.assertIn('count', response.data)
    
    def test_search_performance(self):
        """Prueba rendimiento de búsqueda"""
        url = reverse('bienes:api_list')
        
        # Búsqueda que debería ser rápida
        response = self.client.get(url, {'search': 'PAT-001'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verificar que devuelve resultados relevantes
        self.assertGreater(len(response.data['results']), 0)
    
    def test_filter_performance(self):
        """Prueba rendimiento de filtros"""
        url = reverse('bienes:api_list')
        
        response = self.client.get(url, {
            'estado_bien': 'B',
            'oficina_id': self.oficina.id
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Todos los resultados deberían cumplir los filtros
        for bien in response.data['results']:
            self.assertEqual(bien['estado_bien'], 'B')
            self.assertEqual(bien['oficina']['id'], self.oficina.id)