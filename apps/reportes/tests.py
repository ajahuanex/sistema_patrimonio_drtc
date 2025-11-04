import os
import tempfile
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase
from rest_framework import status
from apps.catalogo.models import Catalogo
from apps.oficinas.models import Oficina
from apps.bienes.models import BienPatrimonial
from .models import ConfiguracionFiltro, HistorialReporte
from .utils import ReportGenerator, FilterManager
from .exportadores import ExcelExporter, PDFExporter, CSVExporter
from .zpl_utils import ZPLGenerator
from .generadores import EstadisticasGenerator


class ReportGeneratorTest(TestCase):
    """Pruebas para el generador de reportes"""
    
    def setUp(self):
        """Configuración inicial para las pruebas"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        
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
            responsable='Director Regional',
            estado=True
        )
        
        # Crear bienes de prueba
        self.bien1 = BienPatrimonial.objects.create(
            codigo_patrimonial='PAT-001-2024',
            catalogo=self.catalogo,
            oficina=self.oficina,
            estado_bien='B',
            marca='MARCA A',
            modelo='MODELO A',
            created_by=self.user
        )
        
        self.bien2 = BienPatrimonial.objects.create(
            codigo_patrimonial='PAT-002-2024',
            catalogo=self.catalogo,
            oficina=self.oficina,
            estado_bien='R',
            marca='MARCA B',
            modelo='MODELO B',
            created_by=self.user
        )
        
        self.generator = ReportGenerator()
    
    def test_generar_reporte_basico(self):
        """Prueba generación de reporte básico"""
        filtros = {}
        resultado = self.generator.generar_reporte(filtros, self.user)
        
        self.assertTrue(resultado['success'])
        self.assertEqual(len(resultado['data']), 2)
        self.assertIn('estadisticas', resultado)
        self.assertIn('total_bienes', resultado['estadisticas'])
    
    def test_generar_reporte_con_filtros(self):
        """Prueba generación de reporte con filtros"""
        filtros = {
            'estado_bien': 'B',
            'oficina_id': self.oficina.id
        }
        resultado = self.generator.generar_reporte(filtros, self.user)
        
        self.assertTrue(resultado['success'])
        self.assertEqual(len(resultado['data']), 1)
        self.assertEqual(resultado['data'][0]['codigo_patrimonial'], 'PAT-001-2024')
    
    def test_generar_reporte_por_fechas(self):
        """Prueba generación de reporte filtrado por fechas"""
        from datetime import date, timedelta
        
        filtros = {
            'fecha_inicio': (date.today() - timedelta(days=1)).isoformat(),
            'fecha_fin': date.today().isoformat()
        }
        resultado = self.generator.generar_reporte(filtros, self.user)
        
        self.assertTrue(resultado['success'])
        self.assertEqual(len(resultado['data']), 2)
    
    def test_generar_estadisticas(self):
        """Prueba generación de estadísticas"""
        stats = self.generator.generar_estadisticas()
        
        self.assertIn('total_bienes', stats)
        self.assertIn('por_estado', stats)
        self.assertIn('por_oficina', stats)
        self.assertEqual(stats['total_bienes'], 2)
        self.assertEqual(len(stats['por_estado']), 2)  # B y R
    
    def test_aplicar_filtros_avanzados(self):
        """Prueba aplicación de filtros avanzados"""
        filtros = {
            'marca': 'MARCA A',
            'modelo': 'MODELO A',
            'search': 'PAT-001'
        }
        
        queryset = BienPatrimonial.objects.all()
        resultado = self.generator.aplicar_filtros(queryset, filtros)
        
        self.assertEqual(resultado.count(), 1)
        self.assertEqual(resultado.first().codigo_patrimonial, 'PAT-001-2024')


class FilterManagerTest(TestCase):
    """Pruebas para el gestor de filtros"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.filter_manager = FilterManager()
    
    def test_guardar_configuracion_filtro(self):
        """Prueba guardar configuración de filtro"""
        config_data = {
            'nombre': 'Filtro Test',
            'descripcion': 'Filtro de prueba',
            'filtros': {
                'estado_bien': 'B',
                'marca': 'MARCA A'
            }
        }
        
        config = self.filter_manager.guardar_configuracion(config_data, self.user)
        
        self.assertIsNotNone(config)
        self.assertEqual(config.nombre, 'Filtro Test')
        self.assertEqual(config.usuario, self.user)
        self.assertIn('estado_bien', config.filtros)
    
    def test_obtener_configuraciones_usuario(self):
        """Prueba obtener configuraciones de usuario"""
        # Crear configuración
        ConfiguracionFiltro.objects.create(
            nombre='Config 1',
            usuario=self.user,
            filtros={'estado_bien': 'B'}
        )
        
        configs = self.filter_manager.obtener_configuraciones_usuario(self.user)
        
        self.assertEqual(configs.count(), 1)
        self.assertEqual(configs.first().nombre, 'Config 1')
    
    def test_aplicar_configuracion_filtro(self):
        """Prueba aplicar configuración de filtro"""
        config = ConfiguracionFiltro.objects.create(
            nombre='Config Test',
            usuario=self.user,
            filtros={'estado_bien': 'B', 'marca': 'MARCA A'}
        )
        
        filtros_aplicados = self.filter_manager.aplicar_configuracion(config)
        
        self.assertEqual(filtros_aplicados['estado_bien'], 'B')
        self.assertEqual(filtros_aplicados['marca'], 'MARCA A')


class ExportadoresTest(TestCase):
    """Pruebas para los exportadores"""
    
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
            marca='MARCA TEST',
            modelo='MODELO TEST',
            created_by=self.user
        )
    
    def test_excel_exporter(self):
        """Prueba exportador Excel"""
        exporter = ExcelExporter()
        bienes = BienPatrimonial.objects.all()
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
            resultado = exporter.exportar(bienes, tmp_file.name)
            
            self.assertTrue(resultado['success'])
            self.assertTrue(os.path.exists(tmp_file.name))
            
            # Limpiar archivo temporal
            os.unlink(tmp_file.name)
    
    def test_pdf_exporter(self):
        """Prueba exportador PDF"""
        exporter = PDFExporter()
        bienes = BienPatrimonial.objects.all()
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            resultado = exporter.exportar(bienes, tmp_file.name)
            
            self.assertTrue(resultado['success'])
            self.assertTrue(os.path.exists(tmp_file.name))
            
            # Limpiar archivo temporal
            os.unlink(tmp_file.name)
    
    def test_csv_exporter(self):
        """Prueba exportador CSV"""
        exporter = CSVExporter()
        bienes = BienPatrimonial.objects.all()
        
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp_file:
            resultado = exporter.exportar(bienes, tmp_file.name)
            
            self.assertTrue(resultado['success'])
            self.assertTrue(os.path.exists(tmp_file.name))
            
            # Limpiar archivo temporal
            os.unlink(tmp_file.name)


class ZPLGeneratorTest(TestCase):
    """Pruebas para el generador ZPL"""
    
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
        
        self.zpl_generator = ZPLGenerator()
    
    def test_generar_zpl_individual(self):
        """Prueba generación ZPL individual"""
        zpl_code = self.zpl_generator.generar_sticker_individual(self.bien)
        
        self.assertIsInstance(zpl_code, str)
        self.assertIn('^XA', zpl_code)  # Inicio de comando ZPL
        self.assertIn('^XZ', zpl_code)  # Fin de comando ZPL
        self.assertIn('PAT-001-2024', zpl_code)  # Código patrimonial
        self.assertIn('^BQ', zpl_code)  # Comando QR code
    
    def test_generar_zpl_masivo(self):
        """Prueba generación ZPL masiva"""
        # Crear otro bien
        bien2 = BienPatrimonial.objects.create(
            codigo_patrimonial='PAT-002-2024',
            catalogo=self.catalogo,
            oficina=self.oficina,
            estado_bien='B',
            created_by=self.user
        )
        
        bienes = [self.bien, bien2]
        zpl_code = self.zpl_generator.generar_stickers_masivos(bienes)
        
        self.assertIsInstance(zpl_code, str)
        self.assertIn('PAT-001-2024', zpl_code)
        self.assertIn('PAT-002-2024', zpl_code)
        # Debe tener múltiples bloques ZPL
        self.assertEqual(zpl_code.count('^XA'), 2)
        self.assertEqual(zpl_code.count('^XZ'), 2)
    
    def test_configurar_tamano_sticker(self):
        """Prueba configuración de tamaño de sticker"""
        config = {
            'ancho': 50,
            'alto': 30,
            'orientacion': 'horizontal'
        }
        
        self.zpl_generator.configurar_tamano(config)
        zpl_code = self.zpl_generator.generar_sticker_individual(self.bien)
        
        # Verificar que se aplicó la configuración
        self.assertIn('^PW50', zpl_code)  # Ancho de página
        self.assertIn('^LL30', zpl_code)  # Largo de etiqueta


class EstadisticasGeneratorTest(TestCase):
    """Pruebas para el generador de estadísticas"""
    
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
        
        self.oficina1 = Oficina.objects.create(
            codigo='DIR-001',
            nombre='Dirección Regional',
            responsable='Director Regional',
            estado=True
        )
        
        self.oficina2 = Oficina.objects.create(
            codigo='ADM-001',
            nombre='Administración',
            responsable='Administrador',
            estado=True
        )
        
        # Crear bienes con diferentes estados y oficinas
        BienPatrimonial.objects.create(
            codigo_patrimonial='PAT-001-2024',
            catalogo=self.catalogo,
            oficina=self.oficina1,
            estado_bien='B',
            created_by=self.user
        )
        
        BienPatrimonial.objects.create(
            codigo_patrimonial='PAT-002-2024',
            catalogo=self.catalogo,
            oficina=self.oficina1,
            estado_bien='R',
            created_by=self.user
        )
        
        BienPatrimonial.objects.create(
            codigo_patrimonial='PAT-003-2024',
            catalogo=self.catalogo,
            oficina=self.oficina2,
            estado_bien='B',
            created_by=self.user
        )
        
        self.stats_generator = EstadisticasGenerator()
    
    def test_estadisticas_por_estado(self):
        """Prueba estadísticas por estado"""
        stats = self.stats_generator.por_estado()
        
        self.assertIn('B', stats)
        self.assertIn('R', stats)
        self.assertEqual(stats['B']['count'], 2)
        self.assertEqual(stats['R']['count'], 1)
        self.assertEqual(stats['B']['percentage'], 66.67)
        self.assertEqual(stats['R']['percentage'], 33.33)
    
    def test_estadisticas_por_oficina(self):
        """Prueba estadísticas por oficina"""
        stats = self.stats_generator.por_oficina()
        
        self.assertEqual(len(stats), 2)
        
        # Verificar oficina 1 (2 bienes)
        oficina1_stats = next(s for s in stats if s['oficina_codigo'] == 'DIR-001')
        self.assertEqual(oficina1_stats['count'], 2)
        
        # Verificar oficina 2 (1 bien)
        oficina2_stats = next(s for s in stats if s['oficina_codigo'] == 'ADM-001')
        self.assertEqual(oficina2_stats['count'], 1)
    
    def test_estadisticas_por_categoria(self):
        """Prueba estadísticas por categoría"""
        stats = self.stats_generator.por_categoria()
        
        self.assertEqual(len(stats), 1)
        self.assertEqual(stats[0]['grupo'], '04-AGRÍCOLA Y PESQUERO')
        self.assertEqual(stats[0]['clase'], '22-EQUIPO')
        self.assertEqual(stats[0]['count'], 3)
    
    def test_resumen_ejecutivo(self):
        """Prueba resumen ejecutivo"""
        resumen = self.stats_generator.resumen_ejecutivo()
        
        self.assertIn('total_bienes', resumen)
        self.assertIn('total_oficinas', resumen)
        self.assertIn('estado_predominante', resumen)
        self.assertIn('oficina_con_mas_bienes', resumen)
        
        self.assertEqual(resumen['total_bienes'], 3)
        self.assertEqual(resumen['total_oficinas'], 2)
        self.assertEqual(resumen['estado_predominante']['codigo'], 'B')


class HistorialReporteTest(TestCase):
    """Pruebas para el modelo HistorialReporte"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_crear_historial_reporte(self):
        """Prueba crear historial de reporte"""
        historial = HistorialReporte.objects.create(
            usuario=self.user,
            tipo_reporte='inventario_completo',
            filtros_aplicados={'estado_bien': 'B'},
            formato_exportacion='excel',
            total_registros=100
        )
        
        self.assertEqual(historial.usuario, self.user)
        self.assertEqual(historial.tipo_reporte, 'inventario_completo')
        self.assertEqual(historial.total_registros, 100)
        self.assertIsNotNone(historial.fecha_generacion)
    
    def test_str_representation(self):
        """Prueba representación string del historial"""
        historial = HistorialReporte(
            usuario=self.user,
            tipo_reporte='inventario_completo',
            formato_exportacion='excel'
        )
        
        expected = f"Reporte inventario_completo - {self.user.username} - excel"
        self.assertEqual(str(historial), expected)


class ReportesViewsTest(TestCase):
    """Pruebas para las vistas de reportes"""
    
    def setUp(self):
        self.client = Client()
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
    
    def test_dashboard_reportes_view(self):
        """Prueba vista del dashboard de reportes"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('reportes:dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard de Reportes')
        self.assertIn('estadisticas', response.context)
    
    def test_generar_reporte_view(self):
        """Prueba vista de generación de reportes"""
        self.client.login(username='testuser', password='testpass123')
        
        data = {
            'tipo_reporte': 'inventario_completo',
            'formato': 'excel',
            'filtros': '{"estado_bien": "B"}'
        }
        
        response = self.client.post(reverse('reportes:generar'), data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    
    def test_configurar_stickers_view(self):
        """Prueba vista de configuración de stickers"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('reportes:configurar_stickers'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Configurar Stickers')
    
    def test_generar_stickers_zpl(self):
        """Prueba generación de stickers ZPL"""
        self.client.login(username='testuser', password='testpass123')
        
        data = {
            'bienes_ids': [self.bien.id],
            'tamano_sticker': 'pequeno',
            'incluir_qr': True,
            'incluir_codigo': True
        }
        
        response = self.client.post(reverse('reportes:generar_stickers'), data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/octet-stream')
        self.assertIn('attachment', response['Content-Disposition'])


class ReportesAPITest(APITestCase):
    """Pruebas para la API de reportes"""
    
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
        
        self.client.force_authenticate(user=self.user)
    
    def test_api_estadisticas(self):
        """Prueba API de estadísticas"""
        url = reverse('reportes:api_estadisticas')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_bienes', response.data)
        self.assertIn('por_estado', response.data)
        self.assertIn('por_oficina', response.data)
    
    def test_api_generar_reporte(self):
        """Prueba API de generación de reportes"""
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
    
    def test_api_historial_reportes(self):
        """Prueba API de historial de reportes"""
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
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['tipo_reporte'], 'inventario_completo')