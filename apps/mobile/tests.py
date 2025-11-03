"""
Tests para la API móvil
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from apps.bienes.models import BienPatrimonial
from apps.catalogo.models import Catalogo
from apps.oficinas.models import Oficina
from .models import CambioOffline


class MobileAPITestCase(TestCase):
    def setUp(self):
        """Configurar datos de prueba"""
        # Crear usuario
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        
        # Crear catálogo
        self.catalogo = Catalogo.objects.create(
            codigo='12345678',
            denominacion='Computadora de Escritorio',
            grupo='EQUIPOS',
            clase='INFORMATICOS',
            resolucion='R001-2024',
            estado='ACTIVO'
        )
        
        # Crear oficina
        self.oficina = Oficina.objects.create(
            codigo='OF001',
            nombre='Oficina de Sistemas',
            responsable='Juan Pérez',
            estado=True
        )
        
        # Crear bien patrimonial
        self.bien = BienPatrimonial.objects.create(
            codigo_patrimonial='PAT001',
            catalogo=self.catalogo,
            oficina=self.oficina,
            estado_bien='B',
            marca='HP',
            modelo='EliteDesk',
            created_by=self.user
        )
        
        # Configurar cliente API
        self.client = APIClient()
        
        # Obtener token JWT
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

    def test_login_api(self):
        """Test del endpoint de login"""
        url = reverse('mobile:login')
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)

    def test_bienes_list_api(self):
        """Test del endpoint de lista de bienes"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        url = reverse('mobile:bienes-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['codigo_patrimonial'], 'PAT001')

    def test_buscar_por_qr(self):
        """Test del endpoint de búsqueda por QR"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        url = reverse('mobile:bienes-buscar-por-qr', kwargs={'qr_code': self.bien.qr_code})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['codigo_patrimonial'], 'PAT001')

    def test_actualizar_estado_movil(self):
        """Test del endpoint de actualización de estado móvil"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        url = reverse('mobile:bienes-actualizar-estado', kwargs={'pk': self.bien.pk})
        data = {
            'estado_bien': 'R',
            'observaciones': 'Estado actualizado desde móvil',
            'ubicacion_gps': '-15.8402,-70.0219'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar que el bien se actualizó
        self.bien.refresh_from_db()
        self.assertEqual(self.bien.estado_bien, 'R')

    def test_scan_qr_mobile(self):
        """Test del endpoint de escaneo QR móvil"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        url = reverse('mobile:scan_qr_mobile')
        data = {'qr_code': self.bien.qr_code}
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('bien', response.data)
        self.assertTrue(response.data['puede_actualizar_estado'])

    def test_dashboard_mobile(self):
        """Test del endpoint de dashboard móvil"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        url = reverse('mobile:dashboard_mobile')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_bienes', response.data)
        self.assertIn('usuario', response.data)
        self.assertEqual(response.data['total_bienes'], 1)

    def test_sincronizar_cambios(self):
        """Test del endpoint de sincronización de cambios"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        url = reverse('mobile:sincronizar_cambios')
        data = {
            'dispositivo_id': 'TEST_DEVICE_001',
            'cambios': [
                {
                    'tipo_cambio': 'CAMBIAR_ESTADO',
                    'timestamp_local': '2024-01-01T10:00:00Z',
                    'bien_qr_code': self.bien.qr_code,
                    'datos_cambio': {
                        'estado_bien': 'M',
                        'observaciones': 'Cambio desde móvil'
                    },
                    'ubicacion_gps': '-15.8402,-70.0219'
                }
            ]
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn('sesion_id', response.data)
        
        # Verificar que se creó el cambio offline
        self.assertTrue(CambioOffline.objects.filter(usuario=self.user).exists())

    def test_unauthorized_access(self):
        """Test de acceso no autorizado"""
        url = reverse('mobile:bienes-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)