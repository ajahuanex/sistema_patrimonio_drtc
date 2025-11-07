from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from .models import Catalogo


class CatalogoModelTest(TestCase):
    """Pruebas para el modelo Catalogo"""
    
    def setUp(self):
        """Configuración inicial para las pruebas"""
        self.catalogo_data = {
            'codigo': '04220001',
            'denominacion': 'ELECTROEYACULADOR PARA BOVINOS',
            'grupo': '04 AGRICOLA Y PESQUERO',
            'clase': '22 EQUIPO',
            'resolucion': '011-2019/SBN',
            'estado': 'ACTIVO'
        }
    
    def test_crear_catalogo_valido(self):
        """Prueba crear un catálogo válido"""
        catalogo = Catalogo.objects.create(**self.catalogo_data)
        self.assertEqual(catalogo.codigo, '04220001')
        self.assertEqual(catalogo.denominacion, 'ELECTROEYACULADOR PARA BOVINOS')
        self.assertEqual(catalogo.estado, 'ACTIVO')
    
    def test_codigo_unico(self):
        """Prueba que el código sea único"""
        Catalogo.objects.create(**self.catalogo_data)
        
        # Intentar crear otro con el mismo código
        with self.assertRaises(ValidationError):
            Catalogo.objects.create(**self.catalogo_data)
    
    def test_denominacion_unica(self):
        """Prueba que la denominación sea única"""
        Catalogo.objects.create(**self.catalogo_data)
        
        # Intentar crear otro con la misma denominación
        data_duplicada = self.catalogo_data.copy()
        data_duplicada['codigo'] = '04220002'
        
        with self.assertRaises(ValidationError):
            Catalogo.objects.create(**data_duplicada)
    
    def test_validacion_codigo_formato(self):
        """Prueba validación del formato del código"""
        data_invalida = self.catalogo_data.copy()
        data_invalida['codigo'] = 'ABC12345'
        
        catalogo = Catalogo(**data_invalida)
        with self.assertRaises(ValidationError):
            catalogo.full_clean()
    
    def test_validacion_codigo_longitud(self):
        """Prueba validación de la longitud del código"""
        data_invalida = self.catalogo_data.copy()
        data_invalida['codigo'] = '123'
        
        catalogo = Catalogo(**data_invalida)
        with self.assertRaises(ValidationError):
            catalogo.full_clean()
    
    def test_denominacion_normalizada(self):
        """Prueba que la denominación se normalice a mayúsculas"""
        data_minusculas = self.catalogo_data.copy()
        data_minusculas['denominacion'] = 'electroeyaculador para bovinos'
        
        catalogo = Catalogo(**data_minusculas)
        catalogo.full_clean()
        self.assertEqual(catalogo.denominacion, 'ELECTROEYACULADOR PARA BOVINOS')
    
    def test_propiedades_grupo(self):
        """Prueba las propiedades del grupo"""
        catalogo = Catalogo(**self.catalogo_data)
        self.assertEqual(catalogo.grupo_codigo, '04')
        self.assertEqual(catalogo.grupo_descripcion, 'AGRICOLA Y PESQUERO')
    
    def test_propiedades_clase(self):
        """Prueba las propiedades de la clase"""
        catalogo = Catalogo(**self.catalogo_data)
        self.assertEqual(catalogo.clase_codigo, '22')
        self.assertEqual(catalogo.clase_descripcion, 'EQUIPO')
    
    def test_buscar_por_denominacion(self):
        """Prueba la búsqueda por denominación"""
        Catalogo.objects.create(**self.catalogo_data)
        
        resultados = Catalogo.buscar_por_denominacion('ELECTROEYACULADOR')
        self.assertEqual(resultados.count(), 1)
        self.assertEqual(resultados.first().codigo, '04220001')
    
    def test_obtener_grupos(self):
        """Prueba obtener lista de grupos"""
        Catalogo.objects.create(**self.catalogo_data)
        
        grupos = Catalogo.obtener_grupos()
        self.assertIn('04 AGRICOLA Y PESQUERO', grupos)
    
    def test_obtener_clases_por_grupo(self):
        """Prueba obtener clases por grupo"""
        Catalogo.objects.create(**self.catalogo_data)
        
        clases = Catalogo.obtener_clases_por_grupo('04 AGRICOLA Y PESQUERO')
        self.assertIn('22 EQUIPO', clases)
    
    def test_str_representation(self):
        """Prueba la representación string del modelo"""
        catalogo = Catalogo(**self.catalogo_data)
        expected = "04220001 - ELECTROEYACULADOR PARA BOVINOS"
        self.assertEqual(str(catalogo), expected)