import json
import uuid
from django.test import TestCase, Client
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib.auth.models import User, Permission
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from apps.catalogo.models import Catalogo
from apps.oficinas.models import Oficina
from .models import BienPatrimonial, MovimientoBien, HistorialEstado
from .utils import QRCodeGenerator, QRCodeValidator


class MobileScanningAPITest(APITestCase):
    """Pruebas para las APIs de escaneo móvil"""
    
    def setUp(self):
        """Configuración inicial para las pruebas de API móvil"""
        # Crear usuario con permisos
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        
        # Agregar permisos necesarios
        permission = Permission.objects.get(codename='change_bienpatrimonial')
        self.user.user_permissions.add(permission)
        
        # Crear catálogo
        self.catalogo = Catalogo.objects.create(
            codigo='04220001',
            denominacion='ELECTROEYACULADOR PARA BOVINOS',
            grupo='04-AGRÍCOLA Y PESQUERO',
            clase='22-EQUIPO',
            resolucion='R.D. 001-2024',
            estado='ACTIVO'
        )
        
        # Crear oficina
        self.oficina = Oficina.objects.create(
            codigo='DIR-001',
            nombre='Dirección Regional',
            descripcion='Oficina principal',
            responsable='Juan Pérez',
            estado=True
        )
        
        # Crear bien patrimonial
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
        
        # Autenticar usuario
        self.client.force_authenticate(user=self.user)
    
    def test_qr_scan_api_success(self):
        """Prueba escaneo exitoso de QR"""
        url = reverse('bienes:api_scan')
        data = {
            'qr_code': self.bien.qr_code,
            'device_info': {
                'user_agent': 'Test Mobile Browser',
                'screen_width': 375,
                'screen_height': 667
            }
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['bien']['codigo_patrimonial'], 'PAT-001-2024')
        self.assertEqual(response.data['bien']['denominacion'], 'ELECTROEYACULADOR PARA BOVINOS')
        self.assertIn('permissions', response.data)
        self.assertIn('estados_disponibles', response.data)
    
    def test_qr_scan_api_not_found(self):
        """Prueba escaneo de QR no encontrado"""
        url = reverse('bienes:api_scan')
        fake_qr = str(uuid.uuid4())
        data = {
            'qr_code': fake_qr,
            'device_info': {}
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error_code'], 'BIEN_NOT_FOUND')
    
    def test_qr_scan_api_invalid_format(self):
        """Prueba escaneo de QR con formato inválido"""
        url = reverse('bienes:api_scan')
        data = {
            'qr_code': 'invalid-qr-format',
            'device_info': {}
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 'QR_INVALID_FORMAT')
    
    def test_update_estado_api_success(self):
        """Prueba actualización exitosa de estado desde móvil"""
        url = reverse('bienes:api_update_estado')
        data = {
            'bien_id': self.bien.id,
            'estado': 'R',  # Cambiar a Regular
            'observaciones': 'Cambio de estado desde móvil',
            'ubicacion_gps': '-15.8422,-70.0199',
            'device_info': {
                'user_agent': 'Test Mobile Browser'
            }
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['bien']['estado_nuevo']['codigo'], 'R')
        
        # Verificar que se creó el historial
        historial = HistorialEstado.objects.filter(bien=self.bien).first()
        self.assertIsNotNone(historial)
        self.assertEqual(historial.estado_anterior, 'B')
        self.assertEqual(historial.estado_nuevo, 'R')
        self.assertEqual(historial.ubicacion_gps, '-15.8422,-70.0199')
    
    def test_update_estado_api_no_change(self):
        """Prueba actualización sin cambio de estado"""
        url = reverse('bienes:api_update_estado')
        data = {
            'bien_id': self.bien.id,
            'estado': 'B',  # Mismo estado actual
            'observaciones': 'Sin cambio',
            'device_info': {}
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['warning'], 'NO_CHANGE_NEEDED')
    
    def test_update_estado_api_observations_required(self):
        """Prueba que las observaciones son requeridas para estados críticos"""
        url = reverse('bienes:api_update_estado')
        data = {
            'bien_id': self.bien.id,
            'estado': 'M',  # Estado Malo requiere observaciones
            'observaciones': '',  # Sin observaciones
            'device_info': {}
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], 'OBSERVATIONS_REQUIRED')
    
    def test_batch_scan_api_success(self):
        """Prueba escaneo por lotes exitoso"""
        # Crear otro bien para el lote
        bien2 = BienPatrimonial.objects.create(
            codigo_patrimonial='PAT-002-2024',
            catalogo=self.catalogo,
            oficina=self.oficina,
            estado_bien='N',
            created_by=self.user
        )
        
        url = reverse('bienes:api_batch_scan')
        data = {
            'qr_codes': [self.bien.qr_code, bien2.qr_code],
            'device_info': {
                'user_agent': 'Test Mobile Browser'
            }
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['summary']['total_scanned'], 2)
        self.assertEqual(response.data['summary']['found'], 2)
        self.assertEqual(response.data['summary']['not_found'], 0)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_batch_scan_api_mixed_results(self):
        """Prueba escaneo por lotes con resultados mixtos"""
        fake_qr = str(uuid.uuid4())
        
        url = reverse('bienes:api_batch_scan')
        data = {
            'qr_codes': [self.bien.qr_code, fake_qr, 'invalid-format'],
            'device_info': {}
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['summary']['total_scanned'], 3)
        self.assertEqual(response.data['summary']['found'], 1)
        self.assertEqual(response.data['summary']['not_found'], 1)
        
        # Verificar que hay un resultado inválido
        invalid_results = [r for r in response.data['results'] if r['status'] == 'invalid']
        self.assertEqual(len(invalid_results), 1)
    
    def test_mobile_inventory_api(self):
        """Prueba API de inventario móvil"""
        url = reverse('bienes:api_mobile_inventory')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('pagination', response.data)
        self.assertIn('bienes', response.data)
        self.assertEqual(len(response.data['bienes']), 1)
        self.assertEqual(response.data['bienes'][0]['codigo_patrimonial'], 'PAT-001-2024')
    
    def test_mobile_inventory_api_with_filters(self):
        """Prueba API de inventario móvil con filtros"""
        url = reverse('bienes:api_mobile_inventory')
        params = {
            'oficina_id': self.oficina.id,
            'estado': 'B',
            'search': 'PAT-001'
        }
        
        response = self.client.get(url, params)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['bienes']), 1)
        self.assertEqual(response.data['filters_applied']['oficina_id'], str(self.oficina.id))
        self.assertEqual(response.data['filters_applied']['estado'], 'B')
        self.assertEqual(response.data['filters_applied']['search'], 'PAT-001')
    
    def test_unauthorized_access(self):
        """Prueba acceso no autorizado a las APIs"""
        self.client.force_authenticate(user=None)
        
        # Probar API de escaneo
        url = reverse('bienes:api_scan')
        response = self.client.post(url, {'qr_code': self.bien.qr_code}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Probar API de actualización
        url = reverse('bienes:api_update_estado')
        response = self.client.post(url, {'bien_id': self.bien.id, 'estado': 'R'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_insufficient_permissions(self):
        """Prueba acceso con permisos insuficientes"""
        # Crear usuario sin permisos de cambio
        user_no_perms = User.objects.create_user(
            username='noperms',
            password='testpass123'
        )
        self.client.force_authenticate(user=user_no_perms)
        
        # El escaneo debería funcionar
        url = reverse('bienes:api_scan')
        response = self.client.post(url, {'qr_code': self.bien.qr_code}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['permissions']['can_edit'])
        
        # La actualización debería fallar
        url = reverse('bienes:api_update_estado')
        response = self.client.post(url, {'bien_id': self.bien.id, 'estado': 'R'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['error_code'], 'PERMISSION_DENIED')


class BienPatrimonialModelTest(TestCase):
    """Pruebas para el modelo BienPatrimonial"""
    
    def setUp(self):
        """Configuración inicial para las pruebas"""
        # Crear catálogo
        self.catalogo = Catalogo.objects.create(
            codigo='04220001',
            denominacion='ELECTROEYACULADOR PARA BOVINOS',
            grupo='04 AGRICOLA Y PESQUERO',
            clase='22 EQUIPO',
            resolucion='011-2019/SBN',
            estado='ACTIVO'
        )
        
        # Crear oficina
        self.oficina = Oficina.objects.create(
            codigo='DIR-001',
            nombre='Dirección Regional',
            responsable='Juan Pérez',
            estado=True
        )
        
        self.bien_data = {
            'codigo_patrimonial': 'PAT-001-2024',
            'codigo_interno': 'INT-001',
            'catalogo': self.catalogo,
            'oficina': self.oficina,
            'estado_bien': 'B',
            'marca': 'MARCA TEST',
            'modelo': 'MODELO TEST',
            'color': 'AZUL',
            'serie': 'SER123456'
        }
    
    def test_crear_bien_valido(self):
        """Prueba crear un bien válido"""
        bien = BienPatrimonial.objects.create(**self.bien_data)
        self.assertEqual(bien.codigo_patrimonial, 'PAT-001-2024')
        self.assertEqual(bien.catalogo, self.catalogo)
        self.assertEqual(bien.oficina, self.oficina)
        self.assertTrue(bien.qr_code)  # Se genera automáticamente
        self.assertTrue(bien.url_qr)   # Se genera automáticamente
    
    def test_codigo_patrimonial_unico(self):
        """Prueba que el código patrimonial sea único"""
        BienPatrimonial.objects.create(**self.bien_data)
        
        # Intentar crear otro con el mismo código
        with self.assertRaises(IntegrityError):
            BienPatrimonial.objects.create(**self.bien_data)
    
    def test_qr_code_unico(self):
        """Prueba que el código QR sea único"""
        bien1 = BienPatrimonial.objects.create(**self.bien_data)
        
        bien_data2 = self.bien_data.copy()
        bien_data2['codigo_patrimonial'] = 'PAT-002-2024'
        bien2 = BienPatrimonial.objects.create(**bien_data2)
        
        self.assertNotEqual(bien1.qr_code, bien2.qr_code)
    
    def test_validacion_catalogo_activo(self):
        """Prueba validación de catálogo activo"""
        # Crear catálogo excluido
        catalogo_excluido = Catalogo.objects.create(
            codigo='04220002',
            denominacion='BIEN EXCLUIDO',
            grupo='04 AGRICOLA Y PESQUERO',
            clase='22 EQUIPO',
            resolucion='011-2019/SBN',
            estado='EXCLUIDO'
        )
        
        bien_data_invalida = self.bien_data.copy()
        bien_data_invalida['catalogo'] = catalogo_excluido
        
        bien = BienPatrimonial(**bien_data_invalida)
        with self.assertRaises(ValidationError):
            bien.full_clean()
    
    def test_validacion_oficina_activa(self):
        """Prueba validación de oficina activa"""
        # Crear oficina inactiva
        oficina_inactiva = Oficina.objects.create(
            codigo='INA-001',
            nombre='Oficina Inactiva',
            responsable='Test',
            estado=False
        )
        
        bien_data_invalida = self.bien_data.copy()
        bien_data_invalida['oficina'] = oficina_inactiva
        
        bien = BienPatrimonial(**bien_data_invalida)
        with self.assertRaises(ValidationError):
            bien.full_clean()
    
    def test_propiedades_bien(self):
        """Prueba las propiedades del bien"""
        bien = BienPatrimonial(**self.bien_data)
        
        self.assertEqual(bien.estado_bien_texto, 'Bueno')
        self.assertEqual(bien.denominacion, 'ELECTROEYACULADOR PARA BOVINOS')
        self.assertEqual(bien.ubicacion_completa, 'Dirección Regional')
        self.assertEqual(bien.responsable_actual, 'Juan Pérez')
    
    def test_es_vehiculo_property(self):
        """Prueba la propiedad es_vehiculo"""
        # Bien sin datos de vehículo
        bien = BienPatrimonial(**self.bien_data)
        self.assertFalse(bien.es_vehiculo)
        
        # Bien con placa
        bien.placa = 'ABC-123'
        self.assertTrue(bien.es_vehiculo)
    
    def test_buscar_por_codigo(self):
        """Prueba la búsqueda por código"""
        BienPatrimonial.objects.create(**self.bien_data)
        
        bien = BienPatrimonial.buscar_por_codigo('PAT-001')
        self.assertIsNotNone(bien)
        self.assertEqual(bien.codigo_patrimonial, 'PAT-001-2024')
    
    def test_buscar_por_qr(self):
        """Prueba la búsqueda por QR"""
        bien_creado = BienPatrimonial.objects.create(**self.bien_data)
        
        bien = BienPatrimonial.buscar_por_qr(bien_creado.qr_code)
        self.assertIsNotNone(bien)
        self.assertEqual(bien.codigo_patrimonial, 'PAT-001-2024')
    
    def test_obtener_por_oficina(self):
        """Prueba obtener bienes por oficina"""
        BienPatrimonial.objects.create(**self.bien_data)
        
        bienes = BienPatrimonial.obtener_por_oficina(self.oficina)
        self.assertEqual(bienes.count(), 1)
        self.assertEqual(bienes.first().codigo_patrimonial, 'PAT-001-2024')
    
    def test_estadisticas_por_estado(self):
        """Prueba las estadísticas por estado"""
        BienPatrimonial.objects.create(**self.bien_data)
        
        # Crear otro bien con estado diferente
        bien_data2 = self.bien_data.copy()
        bien_data2['codigo_patrimonial'] = 'PAT-002-2024'
        bien_data2['estado_bien'] = 'R'
        BienPatrimonial.objects.create(**bien_data2)
        
        stats = BienPatrimonial.estadisticas_por_estado()
        self.assertEqual(len(stats), 2)
    
    def test_str_representation(self):
        """Prueba la representación string del modelo"""
        bien = BienPatrimonial(**self.bien_data)
        expected = "PAT-001-2024 - ELECTROEYACULADOR PARA BOVINOS"
        self.assertEqual(str(bien), expected)


class MovimientoBienModelTest(TestCase):
    """Pruebas para el modelo MovimientoBien"""
    
    def setUp(self):
        """Configuración inicial"""
        # Crear catálogo y oficinas
        self.catalogo = Catalogo.objects.create(
            codigo='04220001',
            denominacion='TEST BIEN',
            grupo='04 AGRICOLA Y PESQUERO',
            clase='22 EQUIPO',
            resolucion='011-2019/SBN'
        )
        
        self.oficina_origen = Oficina.objects.create(
            codigo='ORI-001',
            nombre='Oficina Origen',
            responsable='Responsable Origen'
        )
        
        self.oficina_destino = Oficina.objects.create(
            codigo='DES-001',
            nombre='Oficina Destino',
            responsable='Responsable Destino'
        )
        
        self.bien = BienPatrimonial.objects.create(
            codigo_patrimonial='PAT-MOV-001',
            catalogo=self.catalogo,
            oficina=self.oficina_origen
        )
    
    def test_crear_movimiento(self):
        """Prueba crear un movimiento"""
        movimiento = MovimientoBien.objects.create(
            bien=self.bien,
            oficina_origen=self.oficina_origen,
            oficina_destino=self.oficina_destino,
            motivo='Reasignación administrativa'
        )
        
        self.assertEqual(movimiento.bien, self.bien)
        self.assertFalse(movimiento.confirmado)
        self.assertIsNone(movimiento.fecha_confirmacion)
    
    def test_confirmar_movimiento(self):
        """Prueba confirmar un movimiento"""
        movimiento = MovimientoBien.objects.create(
            bien=self.bien,
            oficina_origen=self.oficina_origen,
            oficina_destino=self.oficina_destino,
            motivo='Reasignación administrativa'
        )
        
        # Confirmar movimiento
        movimiento.confirmar_movimiento()
        
        # Verificar que se confirmó
        movimiento.refresh_from_db()
        self.assertTrue(movimiento.confirmado)
        self.assertIsNotNone(movimiento.fecha_confirmacion)
        
        # Verificar que el bien cambió de oficina
        self.bien.refresh_from_db()
        self.assertEqual(self.bien.oficina, self.oficina_destino)


class HistorialEstadoModelTest(TestCase):
    """Pruebas para el modelo HistorialEstado"""
    
    def setUp(self):
        """Configuración inicial"""
        self.catalogo = Catalogo.objects.create(
            codigo='04220001',
            denominacion='TEST BIEN',
            grupo='04 AGRICOLA Y PESQUERO',
            clase='22 EQUIPO',
            resolucion='011-2019/SBN'
        )
        
        self.oficina = Oficina.objects.create(
            codigo='OFI-001',
            nombre='Oficina Test',
            responsable='Responsable Test'
        )
        
        self.bien = BienPatrimonial.objects.create(
            codigo_patrimonial='PAT-HIST-001',
            catalogo=self.catalogo,
            oficina=self.oficina,
            estado_bien='B'
        )
    
    def test_crear_historial_estado(self):
        """Prueba crear un historial de estado"""
        historial = HistorialEstado.objects.create(
            bien=self.bien,
            estado_anterior='B',
            estado_nuevo='R',
            observaciones='Deterioro por uso normal'
        )
        
        self.assertEqual(historial.bien, self.bien)
        self.assertEqual(historial.estado_anterior, 'B')
        self.assertEqual(historial.estado_nuevo, 'R')
        self.assertIsNotNone(historial.fecha_cambio)
    
    def test_str_representation(self):
        """Prueba la representación string del historial"""
        historial = HistorialEstado(
            bien=self.bien,
            estado_anterior='B',
            estado_nuevo='R'
        )
        
        expected = "PAT-HIST-001: Bueno → Regular"
        self.assertEqual(str(historial), expected)


class QRCodeGeneratorTest(TestCase):
    """Tests para el generador de códigos QR"""
    
    def setUp(self):
        self.generator = QRCodeGenerator()
        
        # Crear datos de prueba
        self.catalogo = Catalogo.objects.create(
            codigo='04-22-001',
            denominacion='ELECTROEYACULADOR PARA BOVINOS',
            grupo='04-AGRÍCOLA Y PESQUERO',
            clase='22-EQUIPO',
            resolucion='R.D. 001-2024',
            estado='ACTIVO'
        )
        
        self.oficina = Oficina.objects.create(
            codigo='DIR-001',
            nombre='Dirección Regional',
            descripcion='Oficina principal',
            responsable='Director Regional',
            estado=True
        )
    
    def test_generar_codigo_unico(self):
        """Test generación de código QR único"""
        codigo = self.generator.generar_codigo_unico()
        
        # Verificar que es un UUID válido
        self.assertIsInstance(uuid.UUID(codigo), uuid.UUID)
        
        # Verificar que no existe en la base de datos
        self.assertFalse(BienPatrimonial.objects.filter(qr_code=codigo).exists())
    
    def test_generar_url_qr(self):
        """Test generación de URL QR"""
        qr_code = str(uuid.uuid4())
        url = self.generator.generar_url_qr(qr_code)
        
        self.assertTrue(url.startswith('http'))
        self.assertIn(f'/qr/{qr_code}/', url)
    
    def test_generar_qr_para_bien(self):
        """Test generación de QR para bien patrimonial"""
        bien = BienPatrimonial.objects.create(
            codigo_patrimonial='PAT-001-2024',
            catalogo=self.catalogo,
            oficina=self.oficina,
            estado_bien='B'
        )
        
        # Limpiar QR existente
        bien.qr_code = ''
        bien.url_qr = ''
        
        qr_code, url_qr = self.generator.generar_qr_para_bien(bien)
        
        self.assertIsNotNone(qr_code)
        self.assertIsNotNone(url_qr)
        self.assertIn(qr_code, url_qr)


class QRCodeValidatorTest(TestCase):
    """Tests para el validador de códigos QR"""
    
    def test_validar_formato_qr_valido(self):
        """Test validación de formato QR válido"""
        qr_code = str(uuid.uuid4())
        is_valid, message = QRCodeValidator.validar_formato_qr(qr_code)
        
        self.assertTrue(is_valid)
        self.assertEqual(message, "Código QR válido")
    
    def test_validar_formato_qr_invalido(self):
        """Test validación de formato QR inválido"""
        qr_code = "codigo-invalido"
        is_valid, message = QRCodeValidator.validar_formato_qr(qr_code)
        
        self.assertFalse(is_valid)
        self.assertIn("no tiene formato UUID válido", message)
    
    def test_validar_formato_qr_vacio(self):
        """Test validación de QR vacío"""
        is_valid, message = QRCodeValidator.validar_formato_qr("")
        
        self.assertFalse(is_valid)
        self.assertEqual(message, "Código QR vacío")
    
    def test_extraer_qr_de_url(self):
        """Test extracción de QR de URL"""
        qr_code = str(uuid.uuid4())
        url_qr = f"http://localhost:8000/qr/{qr_code}/"
        
        extracted = QRCodeValidator.extraer_qr_de_url(url_qr)
        
        self.assertEqual(extracted, qr_code)


class QRScanAPITest(APITestCase):
    """Tests para la API de escaneo QR"""
    
    def setUp(self):
        # Crear usuario con permisos
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Agregar permisos
        permission = Permission.objects.get(codename='change_bienpatrimonial')
        self.user.user_permissions.add(permission)
        
        # Crear datos de prueba
        self.catalogo = Catalogo.objects.create(
            codigo='04-22-001',
            denominacion='ELECTROEYACULADOR PARA BOVINOS',
            grupo='04-AGRÍCOLA Y PESQUERO',
            clase='22-EQUIPO',
            resolucion='R.D. 001-2024',
            estado='ACTIVO'
        )
        
        self.oficina = Oficina.objects.create(
            codigo='DIR-001',
            nombre='Dirección Regional',
            descripcion='Oficina principal',
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
    
    def test_scan_qr_success(self):
        """Test escaneo exitoso de QR"""
        self.client.force_authenticate(user=self.user)
        
        url = reverse('bienes:api_scan')
        data = {'qr_code': self.bien.qr_code}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['bien']['codigo_patrimonial'], 'PAT-001-2024')
        self.assertIn('permissions', response.data)
        self.assertIn('estados_disponibles', response.data)
    
    def test_scan_qr_not_found(self):
        """Test escaneo de QR inexistente"""
        self.client.force_authenticate(user=self.user)
        
        url = reverse('bienes:api_scan')
        data = {'qr_code': str(uuid.uuid4())}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
    
    def test_scan_qr_invalid_format(self):
        """Test escaneo de QR con formato inválido"""
        self.client.force_authenticate(user=self.user)
        
        url = reverse('bienes:api_scan')
        data = {'qr_code': 'codigo-invalido'}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Código QR inválido', response.data['error'])


class UpdateEstadoAPITest(APITestCase):
    """Tests para la API de actualización de estado"""
    
    def setUp(self):
        # Crear usuario con permisos
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Agregar permisos
        permission = Permission.objects.get(codename='change_bienpatrimonial')
        self.user.user_permissions.add(permission)
        
        # Crear datos de prueba
        self.catalogo = Catalogo.objects.create(
            codigo='04-22-001',
            denominacion='ELECTROEYACULADOR PARA BOVINOS',
            grupo='04-AGRÍCOLA Y PESQUERO',
            clase='22-EQUIPO',
            resolucion='R.D. 001-2024',
            estado='ACTIVO'
        )
        
        self.oficina = Oficina.objects.create(
            codigo='DIR-001',
            nombre='Dirección Regional',
            descripcion='Oficina principal',
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
    
    def test_update_estado_success(self):
        """Test actualización exitosa de estado"""
        self.client.force_authenticate(user=self.user)
        
        url = reverse('bienes:api_update_estado')
        data = {
            'bien_id': self.bien.id,
            'estado': 'R',
            'observaciones': 'Cambio de estado por inspección',
            'ubicacion_gps': '-15.8422,-70.0199'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verificar que el bien se actualizó
        self.bien.refresh_from_db()
        self.assertEqual(self.bien.estado_bien, 'R')
        
        # Verificar que se creó el historial
        historial = HistorialEstado.objects.filter(bien=self.bien).first()
        self.assertIsNotNone(historial)
        self.assertEqual(historial.estado_anterior, 'B')
        self.assertEqual(historial.estado_nuevo, 'R')
        self.assertEqual(historial.observaciones, 'Cambio de estado por inspección')
        self.assertEqual(historial.ubicacion_gps, '-15.8422,-70.0199')
    
    def test_update_estado_invalid_state(self):
        """Test actualización con estado inválido"""
        self.client.force_authenticate(user=self.user)
        
        url = reverse('bienes:api_update_estado')
        data = {
            'bien_id': self.bien.id,
            'estado': 'X',  # Estado inválido
            'observaciones': 'Test'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Estado inválido', response.data['error'])


class QRCodeViewTest(TestCase):
    """Tests para las vistas de códigos QR"""
    
    def setUp(self):
        self.client = Client()
        
        # Crear datos de prueba
        self.catalogo = Catalogo.objects.create(
            codigo='04-22-001',
            denominacion='ELECTROEYACULADOR PARA BOVINOS',
            grupo='04-AGRÍCOLA Y PESQUERO',
            clase='22-EQUIPO',
            resolucion='R.D. 001-2024',
            estado='ACTIVO'
        )
        
        self.oficina = Oficina.objects.create(
            codigo='DIR-001',
            nombre='Dirección Regional',
            descripcion='Oficina principal',
            responsable='Director Regional',
            estado=True
        )
        
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.bien = BienPatrimonial.objects.create(
            codigo_patrimonial='PAT-001-2024',
            catalogo=self.catalogo,
            oficina=self.oficina,
            estado_bien='B',
            created_by=self.user
        )
    
    def test_qr_detail_view_public(self):
        """Test vista pública de QR"""
        url = reverse('qr_public', kwargs={'qr_code': self.bien.qr_code})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.bien.codigo_patrimonial)
        self.assertContains(response, self.bien.denominacion)
    
    def test_qr_detail_view_not_found(self):
        """Test vista pública con QR inexistente"""
        url = reverse('qr_public', kwargs={'qr_code': str(uuid.uuid4())})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
    
    def test_qr_mobile_view(self):
        """Test vista móvil de QR"""
        url = reverse('bienes:qr_mobile', kwargs={'qr_code': self.bien.qr_code})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.bien.codigo_patrimonial)
    
    def test_qr_image_view(self):
        """Test vista de imagen QR"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('bienes:qr_image', kwargs={'pk': self.bien.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/png')