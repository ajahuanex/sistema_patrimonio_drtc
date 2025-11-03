from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from .models import Oficina


class OficinaModelTest(TestCase):
    """Pruebas para el modelo Oficina"""
    
    def setUp(self):
        """Configuración inicial para las pruebas"""
        self.oficina_data = {
            'codigo': 'DIR-001',
            'nombre': 'Dirección Regional',
            'descripcion': 'Oficina principal de la Dirección Regional de Transportes',
            'responsable': 'Juan Pérez García',
            'cargo_responsable': 'Director Regional',
            'telefono': '051-123456',
            'email': 'direccion@drtcpuno.gob.pe',
            'ubicacion': 'Primer piso, oficina 101',
            'estado': True
        }
    
    def test_crear_oficina_valida(self):
        """Prueba crear una oficina válida"""
        oficina = Oficina.objects.create(**self.oficina_data)
        self.assertEqual(oficina.codigo, 'DIR-001')
        self.assertEqual(oficina.nombre, 'Dirección Regional')
        self.assertTrue(oficina.estado)
    
    def test_codigo_unico(self):
        """Prueba que el código sea único"""
        Oficina.objects.create(**self.oficina_data)
        
        # Intentar crear otra con el mismo código
        with self.assertRaises(IntegrityError):
            Oficina.objects.create(**self.oficina_data)
    
    def test_validacion_codigo_vacio(self):
        """Prueba validación de código vacío"""
        data_invalida = self.oficina_data.copy()
        data_invalida['codigo'] = ''
        
        oficina = Oficina(**data_invalida)
        with self.assertRaises(ValidationError):
            oficina.full_clean()
    
    def test_validacion_nombre_vacio(self):
        """Prueba validación de nombre vacío"""
        data_invalida = self.oficina_data.copy()
        data_invalida['nombre'] = ''
        
        oficina = Oficina(**data_invalida)
        with self.assertRaises(ValidationError):
            oficina.full_clean()
    
    def test_validacion_responsable_vacio(self):
        """Prueba validación de responsable vacío"""
        data_invalida = self.oficina_data.copy()
        data_invalida['responsable'] = ''
        
        oficina = Oficina(**data_invalida)
        with self.assertRaises(ValidationError):
            oficina.full_clean()
    
    def test_normalizacion_codigo(self):
        """Prueba que el código se normalice a mayúsculas"""
        data_minusculas = self.oficina_data.copy()
        data_minusculas['codigo'] = 'dir-001'
        
        oficina = Oficina(**data_minusculas)
        oficina.full_clean()
        self.assertEqual(oficina.codigo, 'DIR-001')
    
    def test_estado_texto_property(self):
        """Prueba la propiedad estado_texto"""
        oficina = Oficina(**self.oficina_data)
        self.assertEqual(oficina.estado_texto, 'Activa')
        
        oficina.estado = False
        self.assertEqual(oficina.estado_texto, 'Inactiva')
    
    def test_obtener_activas(self):
        """Prueba el método obtener_activas"""
        # Crear oficina activa
        Oficina.objects.create(**self.oficina_data)
        
        # Crear oficina inactiva
        data_inactiva = self.oficina_data.copy()
        data_inactiva['codigo'] = 'ADM-001'
        data_inactiva['nombre'] = 'Administración'
        data_inactiva['estado'] = False
        Oficina.objects.create(**data_inactiva)
        
        activas = Oficina.obtener_activas()
        self.assertEqual(activas.count(), 1)
        self.assertEqual(activas.first().codigo, 'DIR-001')
    
    def test_buscar_por_nombre(self):
        """Prueba la búsqueda por nombre"""
        Oficina.objects.create(**self.oficina_data)
        
        resultados = Oficina.buscar_por_nombre('Dirección')
        self.assertEqual(resultados.count(), 1)
        self.assertEqual(resultados.first().codigo, 'DIR-001')
    
    def test_buscar_por_codigo(self):
        """Prueba la búsqueda por código"""
        Oficina.objects.create(**self.oficina_data)
        
        resultados = Oficina.buscar_por_nombre('DIR-001')
        self.assertEqual(resultados.count(), 1)
        self.assertEqual(resultados.first().nombre, 'Dirección Regional')
    
    def test_buscar_por_responsable(self):
        """Prueba la búsqueda por responsable"""
        Oficina.objects.create(**self.oficina_data)
        
        resultados = Oficina.buscar_por_responsable('Juan Pérez')
        self.assertEqual(resultados.count(), 1)
        self.assertEqual(resultados.first().codigo, 'DIR-001')
    
    def test_puede_eliminarse_sin_bienes(self):
        """Prueba que se puede eliminar oficina sin bienes"""
        oficina = Oficina.objects.create(**self.oficina_data)
        self.assertTrue(oficina.puede_eliminarse())
    
    def test_activar_desactivar(self):
        """Prueba los métodos activar y desactivar"""
        oficina = Oficina.objects.create(**self.oficina_data)
        
        # Desactivar
        oficina.desactivar()
        oficina.refresh_from_db()
        self.assertFalse(oficina.estado)
        
        # Activar
        oficina.activar()
        oficina.refresh_from_db()
        self.assertTrue(oficina.estado)
    
    def test_str_representation(self):
        """Prueba la representación string del modelo"""
        oficina = Oficina(**self.oficina_data)
        expected = "DIR-001 - Dirección Regional"
        self.assertEqual(str(oficina), expected)
    
    def test_campos_opcionales(self):
        """Prueba que los campos opcionales funcionen correctamente"""
        data_minima = {
            'codigo': 'MIN-001',
            'nombre': 'Oficina Mínima',
            'responsable': 'Responsable Test'
        }
        
        oficina = Oficina.objects.create(**data_minima)
        self.assertEqual(oficina.descripcion, '')
        self.assertEqual(oficina.telefono, '')
        self.assertEqual(oficina.email, '')
        self.assertTrue(oficina.estado)  # Default True