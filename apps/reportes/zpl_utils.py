"""
Utilidades específicas para generación de plantillas ZPL (Zebra Programming Language)
"""

import math
from datetime import datetime
from django.conf import settings
from apps.bienes.models import BienPatrimonial
import logging

logger = logging.getLogger(__name__)


class ConfiguracionSticker:
    """Configuración para stickers ZPL"""
    
    # Configuraciones específicas para impresoras Zebra
    IMPRESORAS_ZEBRA = {
        'ZD220': {
            'ancho_maximo_mm': 112,
            'ancho_maximo_dots_203dpi': 897,  # 112mm * 203dpi / 25.4mm
            'ancho_maximo_dots_300dpi': 1323, # 112mm * 300dpi / 25.4mm
            'descripcion': 'Zebra ZD220 - Etiquetas hasta 112mm'
        },
        'ZD410': {
            'ancho_maximo_mm': 112,
            'ancho_maximo_dots_203dpi': 897,
            'ancho_maximo_dots_300dpi': 1323,
            'descripcion': 'Zebra ZD410 - Tickets hasta 112mm'
        },
        'ZD411_203': {
            'ancho_maximo_mm': 56,
            'ancho_maximo_dots_203dpi': 449,  # 56mm * 203dpi / 25.4mm
            'descripcion': 'Zebra ZD411 (203 DPI) - Tickets hasta 56mm'
        },
        'ZD411_300': {
            'ancho_maximo_mm': 54,
            'ancho_maximo_dots_300dpi': 638,  # 54mm * 300dpi / 25.4mm
            'descripcion': 'Zebra ZD411 (300 DPI) - Tickets hasta 54mm'
        }
    }
    
    # Tamaños predefinidos optimizados para impresoras Zebra
    TAMAÑOS_PREDEFINIDOS = {
        # Para ZD411 (tickets pequeños)
        'ticket_pequeño_203': {
            'ancho': 400,  # ~50mm a 203 DPI
            'alto': 200,   # ~25mm a 203 DPI
            'descripcion': 'Ticket Pequeño ZD411 (50x25mm) - 203 DPI',
            'impresora_recomendada': 'ZD411_203'
        },
        'ticket_pequeño_300': {
            'ancho': 590,  # ~50mm a 300 DPI
            'alto': 295,   # ~25mm a 300 DPI
            'descripcion': 'Ticket Pequeño ZD411 (50x25mm) - 300 DPI',
            'impresora_recomendada': 'ZD411_300'
        },
        
        # Para ZD220/ZD410 (etiquetas medianas)
        'etiqueta_mediana_203': {
            'ancho': 600,  # ~75mm a 203 DPI
            'alto': 400,   # ~50mm a 203 DPI
            'descripcion': 'Etiqueta Mediana ZD220/ZD410 (75x50mm) - 203 DPI',
            'impresora_recomendada': 'ZD220'
        },
        'etiqueta_mediana_300': {
            'ancho': 885,  # ~75mm a 300 DPI
            'alto': 590,   # ~50mm a 300 DPI
            'descripcion': 'Etiqueta Mediana ZD220/ZD410 (75x50mm) - 300 DPI',
            'impresora_recomendada': 'ZD220'
        },
        
        # Para ZD220/ZD410 (etiquetas grandes)
        'etiqueta_grande_203': {
            'ancho': 800,  # ~100mm a 203 DPI
            'alto': 600,   # ~75mm a 203 DPI
            'descripcion': 'Etiqueta Grande ZD220/ZD410 (100x75mm) - 203 DPI',
            'impresora_recomendada': 'ZD220'
        },
        'etiqueta_grande_300': {
            'ancho': 1181, # ~100mm a 300 DPI
            'alto': 885,   # ~75mm a 300 DPI
            'descripcion': 'Etiqueta Grande ZD220/ZD410 (100x75mm) - 300 DPI',
            'impresora_recomendada': 'ZD220'
        },
        
        # Compatibilidad con tamaños anteriores
        'pequeño': {
            'ancho': 300,  # ~1.5 pulgadas
            'alto': 200,   # ~1 pulgada
            'descripcion': 'Pequeño (1.5" x 1")'
        },
        'mediano': {
            'ancho': 400,  # ~2 pulgadas
            'alto': 300,   # ~1.5 pulgadas
            'descripcion': 'Mediano (2" x 1.5")'
        },
        'grande': {
            'ancho': 600,  # ~3 pulgadas
            'alto': 400,   # ~2 pulgadas
            'descripcion': 'Grande (3" x 2")'
        },
        'extra_grande': {
            'ancho': 800,  # ~4 pulgadas
            'alto': 600,   # ~3 pulgadas
            'descripcion': 'Extra Grande (4" x 3")'
        }
    }
    
    def __init__(self, tamaño='mediano', impresora=None, dpi=203, **kwargs):
        """
        Inicializa la configuración del sticker
        
        Args:
            tamaño: Tamaño predefinido o 'personalizado'
            impresora: Modelo de impresora Zebra (ZD220, ZD410, ZD411_203, ZD411_300)
            dpi: DPI de la impresora (203 o 300)
            **kwargs: Parámetros personalizados
        """
        self.impresora = impresora
        self.dpi = dpi
        
        if tamaño in self.TAMAÑOS_PREDEFINIDOS:
            config = self.TAMAÑOS_PREDEFINIDOS[tamaño].copy()
            self.ancho = config['ancho']
            self.alto = config['alto']
            self.impresora_recomendada = config.get('impresora_recomendada')
        else:
            self.ancho = kwargs.get('ancho', 400)
            self.alto = kwargs.get('alto', 300)
            self.impresora_recomendada = None
        
        # Configuración general
        self.margen = kwargs.get('margen', 15 if self.ancho < 500 else 20)
        self.espaciado_linea = kwargs.get('espaciado_linea', 20 if self.ancho < 500 else 25)
        
        # Configuración del QR
        self.incluir_qr = kwargs.get('incluir_qr', True)
        self.tamaño_qr = kwargs.get('tamaño_qr', min(100, (self.alto - 2*self.margen) // 2))
        self.posicion_qr = kwargs.get('posicion_qr', 'izquierda')  # izquierda, derecha, arriba, abajo
        
        # Configuración de fuentes
        self.fuente_titulo = kwargs.get('fuente_titulo', 'A')  # A, B, C, D, E, F, G, H
        self.tamaño_titulo = kwargs.get('tamaño_titulo', 'N')  # N=normal, R=rotado
        self.altura_titulo = kwargs.get('altura_titulo', 30)
        
        self.fuente_texto = kwargs.get('fuente_texto', 'A')
        self.tamaño_texto = kwargs.get('tamaño_texto', 'N')
        self.altura_texto = kwargs.get('altura_texto', 20)
        
        self.fuente_pequeña = kwargs.get('fuente_pequeña', 'A')
        self.altura_pequeña = kwargs.get('altura_pequeña', 15)
        
        # Campos a incluir
        self.campos_incluir = kwargs.get('campos_incluir', [
            'codigo_patrimonial',
            'denominacion',
            'oficina',
            'estado',
            'marca_modelo',
            'serie'
        ])
        
        # Configuración de bordes y líneas
        self.incluir_borde = kwargs.get('incluir_borde', True)
        self.grosor_borde = kwargs.get('grosor_borde', 2)
        self.incluir_linea_separadora = kwargs.get('incluir_linea_separadora', True)
        
        # Configuración institucional
        self.incluir_logo = kwargs.get('incluir_logo', False)
        self.incluir_fecha = kwargs.get('incluir_fecha', True)
        self.incluir_url = kwargs.get('incluir_url', False)
    
    def validar(self):
        """Valida la configuración"""
        errores = []
        
        # Validaciones básicas
        if self.ancho < 200 or self.ancho > 1400:
            errores.append("El ancho debe estar entre 200 y 1400 dots")
        
        if self.alto < 150 or self.alto > 1000:
            errores.append("El alto debe estar entre 150 y 1000 dots")
        
        if self.margen < 5 or self.margen > 50:
            errores.append("El margen debe estar entre 5 y 50 dots")
        
        if self.tamaño_qr > min(self.ancho, self.alto) - 2*self.margen:
            errores.append("El tamaño del QR es muy grande para el sticker")
        
        # Validaciones específicas para impresoras Zebra
        if self.impresora and self.impresora in self.IMPRESORAS_ZEBRA:
            config_impresora = self.IMPRESORAS_ZEBRA[self.impresora]
            
            # Verificar ancho máximo según DPI
            if self.dpi == 203 and 'ancho_maximo_dots_203dpi' in config_impresora:
                ancho_max = config_impresora['ancho_maximo_dots_203dpi']
                if self.ancho > ancho_max:
                    errores.append(f"El ancho ({self.ancho} dots) excede el máximo para {self.impresora} a 203 DPI ({ancho_max} dots)")
            
            elif self.dpi == 300 and 'ancho_maximo_dots_300dpi' in config_impresora:
                ancho_max = config_impresora['ancho_maximo_dots_300dpi']
                if self.ancho > ancho_max:
                    errores.append(f"El ancho ({self.ancho} dots) excede el máximo para {self.impresora} a 300 DPI ({ancho_max} dots)")
        
        return errores
    
    def es_compatible_con_impresora(self, impresora, dpi=203):
        """
        Verifica si la configuración es compatible con una impresora específica
        
        Args:
            impresora: Modelo de impresora
            dpi: DPI de la impresora
            
        Returns:
            tuple: (es_compatible, mensaje)
        """
        if impresora not in self.IMPRESORAS_ZEBRA:
            return False, f"Impresora {impresora} no reconocida"
        
        config_impresora = self.IMPRESORAS_ZEBRA[impresora]
        
        # Verificar ancho máximo
        if dpi == 203 and 'ancho_maximo_dots_203dpi' in config_impresora:
            ancho_max = config_impresora['ancho_maximo_dots_203dpi']
            if self.ancho > ancho_max:
                ancho_mm = round(self.ancho * 25.4 / 203, 1)
                return False, f"Ancho {ancho_mm}mm excede el máximo de {config_impresora['ancho_maximo_mm']}mm para {impresora}"
        
        elif dpi == 300 and 'ancho_maximo_dots_300dpi' in config_impresora:
            ancho_max = config_impresora['ancho_maximo_dots_300dpi']
            if self.ancho > ancho_max:
                ancho_mm = round(self.ancho * 25.4 / 300, 1)
                return False, f"Ancho {ancho_mm}mm excede el máximo de {config_impresora['ancho_maximo_mm']}mm para {impresora}"
        
        return True, f"Compatible con {impresora} a {dpi} DPI"
    
    def obtener_dimensiones_mm(self):
        """
        Obtiene las dimensiones en milímetros
        
        Returns:
            dict: Dimensiones en mm
        """
        factor_conversion = 25.4 / self.dpi
        
        return {
            'ancho_mm': round(self.ancho * factor_conversion, 1),
            'alto_mm': round(self.alto * factor_conversion, 1),
            'ancho_dots': self.ancho,
            'alto_dots': self.alto,
            'dpi': self.dpi
        }
    
    @classmethod
    def crear_para_impresora(cls, impresora, tamaño_mm=None, **kwargs):
        """
        Crea una configuración optimizada para una impresora específica
        
        Args:
            impresora: Modelo de impresora (ZD220, ZD410, ZD411_203, ZD411_300)
            tamaño_mm: Tupla (ancho_mm, alto_mm) o None para usar tamaño recomendado
            **kwargs: Parámetros adicionales
            
        Returns:
            ConfiguracionSticker: Configuración optimizada
        """
        if impresora not in cls.IMPRESORAS_ZEBRA:
            raise ValueError(f"Impresora {impresora} no reconocida")
        
        config_impresora = cls.IMPRESORAS_ZEBRA[impresora]
        
        # Determinar DPI
        if impresora.endswith('_300'):
            dpi = 300
            ancho_max_dots = config_impresora.get('ancho_maximo_dots_300dpi', 1200)
        else:
            dpi = 203
            ancho_max_dots = config_impresora.get('ancho_maximo_dots_203dpi', 900)
        
        # Calcular dimensiones
        if tamaño_mm:
            ancho_mm, alto_mm = tamaño_mm
            ancho_dots = int(ancho_mm * dpi / 25.4)
            alto_dots = int(alto_mm * dpi / 25.4)
        else:
            # Usar tamaño recomendado según la impresora
            if impresora.startswith('ZD411'):
                # Ticket pequeño para ZD411
                ancho_dots = min(400, ancho_max_dots - 50)
                alto_dots = 250
            else:
                # Etiqueta mediana para ZD220/ZD410
                ancho_dots = min(600, ancho_max_dots - 50)
                alto_dots = 400
        
        # Validar que no exceda el ancho máximo
        if ancho_dots > ancho_max_dots:
            ancho_dots = ancho_max_dots - 20  # Margen de seguridad
        
        # Configuración optimizada según el tamaño
        if ancho_dots < 500:
            # Configuración para tickets pequeños
            config_kwargs = {
                'margen': 10,
                'tamaño_qr': min(80, alto_dots - 40),
                'posicion_qr': 'izquierda',
                'altura_titulo': 20,
                'altura_texto': 15,
                'altura_pequeña': 12,
                'campos_incluir': ['codigo_patrimonial', 'denominacion', 'oficina', 'estado'],
                'incluir_fecha': False,
                'incluir_linea_separadora': False
            }
        else:
            # Configuración para etiquetas medianas/grandes
            config_kwargs = {
                'margen': 15,
                'tamaño_qr': min(120, alto_dots - 60),
                'posicion_qr': 'izquierda',
                'altura_titulo': 25,
                'altura_texto': 18,
                'altura_pequeña': 14,
                'campos_incluir': ['codigo_patrimonial', 'denominacion', 'oficina', 'estado', 'marca_modelo', 'serie'],
                'incluir_fecha': True,
                'incluir_linea_separadora': True
            }
        
        # Combinar con kwargs proporcionados
        config_kwargs.update(kwargs)
        
        return cls(
            tamaño='personalizado',
            impresora=impresora,
            dpi=dpi,
            ancho=ancho_dots,
            alto=alto_dots,
            **config_kwargs
        )
    
    def calcular_area_texto(self):
        """Calcula el área disponible para texto"""
        if not self.incluir_qr:
            return {
                'x': self.margen,
                'y': self.margen,
                'ancho': self.ancho - 2*self.margen,
                'alto': self.alto - 2*self.margen
            }
        
        if self.posicion_qr == 'izquierda':
            return {
                'x': self.margen + self.tamaño_qr + 10,
                'y': self.margen,
                'ancho': self.ancho - self.margen - self.tamaño_qr - 20,
                'alto': self.alto - 2*self.margen
            }
        elif self.posicion_qr == 'derecha':
            return {
                'x': self.margen,
                'y': self.margen,
                'ancho': self.ancho - self.margen - self.tamaño_qr - 20,
                'alto': self.alto - 2*self.margen
            }
        elif self.posicion_qr == 'arriba':
            return {
                'x': self.margen,
                'y': self.margen + self.tamaño_qr + 10,
                'ancho': self.ancho - 2*self.margen,
                'alto': self.alto - self.margen - self.tamaño_qr - 20
            }
        else:  # abajo
            return {
                'x': self.margen,
                'y': self.margen,
                'ancho': self.ancho - 2*self.margen,
                'alto': self.alto - self.margen - self.tamaño_qr - 20
            }


class GeneradorZPL:
    """Generador avanzado de código ZPL"""
    
    def __init__(self, configuracion=None):
        """
        Inicializa el generador
        
        Args:
            configuracion: Instancia de ConfiguracionSticker
        """
        self.config = configuracion or ConfiguracionSticker()
        self.comandos_zpl = []
    
    def generar_sticker_bien(self, bien):
        """
        Genera código ZPL para un bien específico
        
        Args:
            bien: Instancia de BienPatrimonial
            
        Returns:
            str: Código ZPL completo
        """
        self.comandos_zpl = []
        
        # Validar configuración
        errores = self.config.validar()
        if errores:
            raise ValueError(f"Configuración inválida: {', '.join(errores)}")
        
        # Inicio de etiqueta
        self._agregar_comando("^XA")
        self._agregar_comando("^LH0,0")  # Origen en 0,0
        
        # Configurar densidad de impresión
        self._agregar_comando("^PR4")  # Velocidad de impresión
        
        # Borde del sticker (opcional)
        if self.config.incluir_borde:
            self._agregar_borde()
        
        # Código QR
        if self.config.incluir_qr and bien.qr_code:
            self._agregar_qr(bien.qr_code)
        
        # Contenido del sticker
        self._agregar_contenido_bien(bien)
        
        # Elementos adicionales
        if self.config.incluir_fecha:
            self._agregar_fecha()
        
        if self.config.incluir_linea_separadora:
            self._agregar_linea_separadora()
        
        # Fin de etiqueta
        self._agregar_comando("^XZ")
        
        return '\n'.join(self.comandos_zpl)
    
    def generar_stickers_masivos(self, queryset, archivo_salida=None):
        """
        Genera código ZPL para múltiples bienes
        
        Args:
            queryset: QuerySet de bienes
            archivo_salida: Archivo de salida (opcional)
            
        Returns:
            str: Código ZPL completo o ruta del archivo
        """
        todos_los_comandos = []
        
        for bien in queryset:
            codigo_bien = self.generar_sticker_bien(bien)
            todos_los_comandos.append(codigo_bien)
        
        codigo_completo = '\n\n'.join(todos_los_comandos)
        
        if archivo_salida:
            with open(archivo_salida, 'w', encoding='utf-8') as f:
                f.write(codigo_completo)
            return archivo_salida
        
        return codigo_completo
    
    def _agregar_comando(self, comando):
        """Agrega un comando ZPL"""
        self.comandos_zpl.append(comando)
    
    def _agregar_borde(self):
        """Agrega borde al sticker"""
        # Borde superior
        self._agregar_comando(f"^FO0,0")
        self._agregar_comando(f"^GB{self.config.ancho},{self.config.grosor_borde},{self.config.grosor_borde}^FS")
        
        # Borde inferior
        self._agregar_comando(f"^FO0,{self.config.alto - self.config.grosor_borde}")
        self._agregar_comando(f"^GB{self.config.ancho},{self.config.grosor_borde},{self.config.grosor_borde}^FS")
        
        # Borde izquierdo
        self._agregar_comando(f"^FO0,0")
        self._agregar_comando(f"^GB{self.config.grosor_borde},{self.config.alto},{self.config.grosor_borde}^FS")
        
        # Borde derecho
        self._agregar_comando(f"^FO{self.config.ancho - self.config.grosor_borde},0")
        self._agregar_comando(f"^GB{self.config.grosor_borde},{self.config.alto},{self.config.grosor_borde}^FS")
    
    def _agregar_qr(self, qr_code):
        """Agrega código QR"""
        # Calcular posición del QR
        if self.config.posicion_qr == 'izquierda':
            x_qr = self.config.margen
            y_qr = self.config.margen
        elif self.config.posicion_qr == 'derecha':
            x_qr = self.config.ancho - self.config.margen - self.config.tamaño_qr
            y_qr = self.config.margen
        elif self.config.posicion_qr == 'arriba':
            x_qr = self.config.margen
            y_qr = self.config.margen
        else:  # abajo
            x_qr = self.config.margen
            y_qr = self.config.alto - self.config.margen - self.config.tamaño_qr
        
        # Generar QR
        self._agregar_comando(f"^FO{x_qr},{y_qr}")
        
        # Calcular factor de escala para el QR
        factor_qr = max(2, self.config.tamaño_qr // 50)
        
        self._agregar_comando(f"^BQN,2,{factor_qr}")
        self._agregar_comando(f"^FDQA,{qr_code}^FS")
    
    def _agregar_contenido_bien(self, bien):
        """Agrega el contenido principal del bien"""
        area_texto = self.config.calcular_area_texto()
        
        x_texto = area_texto['x']
        y_actual = area_texto['y']
        ancho_disponible = area_texto['ancho']
        
        # Código patrimonial (título principal)
        if 'codigo_patrimonial' in self.config.campos_incluir:
            self._agregar_comando(f"^FO{x_texto},{y_actual}")
            self._agregar_comando(f"^{self.config.fuente_titulo}{self.config.tamaño_titulo},{self.config.altura_titulo},{self.config.altura_titulo}")
            self._agregar_comando(f"^FD{bien.codigo_patrimonial}^FS")
            y_actual += self.config.altura_titulo + 5
        
        # Denominación
        if 'denominacion' in self.config.campos_incluir and bien.catalogo:
            denominacion = self._truncar_texto(bien.catalogo.denominacion, ancho_disponible, self.config.altura_texto)
            self._agregar_comando(f"^FO{x_texto},{y_actual}")
            self._agregar_comando(f"^{self.config.fuente_texto}{self.config.tamaño_texto},{self.config.altura_texto},{self.config.altura_texto}")
            self._agregar_comando(f"^FD{denominacion}^FS")
            y_actual += self.config.altura_texto + 3
        
        # Oficina
        if 'oficina' in self.config.campos_incluir and bien.oficina:
            oficina_texto = f"{bien.oficina.codigo} - {bien.oficina.nombre}"
            oficina_texto = self._truncar_texto(oficina_texto, ancho_disponible, self.config.altura_texto)
            self._agregar_comando(f"^FO{x_texto},{y_actual}")
            self._agregar_comando(f"^{self.config.fuente_texto}{self.config.tamaño_texto},{self.config.altura_texto},{self.config.altura_texto}")
            self._agregar_comando(f"^FDOficina: {oficina_texto}^FS")
            y_actual += self.config.altura_texto + 3
        
        # Estado
        if 'estado' in self.config.campos_incluir:
            estado_texto = f"Estado: {bien.get_estado_bien_display()}"
            self._agregar_comando(f"^FO{x_texto},{y_actual}")
            self._agregar_comando(f"^{self.config.fuente_texto}{self.config.tamaño_texto},{self.config.altura_texto},{self.config.altura_texto}")
            self._agregar_comando(f"^FD{estado_texto}^FS")
            y_actual += self.config.altura_texto + 3
        
        # Marca y modelo
        if 'marca_modelo' in self.config.campos_incluir and (bien.marca or bien.modelo):
            marca_modelo = f"{bien.marca or ''} {bien.modelo or ''}".strip()
            marca_modelo = self._truncar_texto(marca_modelo, ancho_disponible, self.config.altura_pequeña)
            self._agregar_comando(f"^FO{x_texto},{y_actual}")
            self._agregar_comando(f"^{self.config.fuente_pequeña}{self.config.tamaño_texto},{self.config.altura_pequeña},{self.config.altura_pequeña}")
            self._agregar_comando(f"^FD{marca_modelo}^FS")
            y_actual += self.config.altura_pequeña + 2
        
        # Serie
        if 'serie' in self.config.campos_incluir and bien.serie:
            serie_texto = f"S/N: {bien.serie}"
            serie_texto = self._truncar_texto(serie_texto, ancho_disponible, self.config.altura_pequeña)
            self._agregar_comando(f"^FO{x_texto},{y_actual}")
            self._agregar_comando(f"^{self.config.fuente_pequeña}{self.config.tamaño_texto},{self.config.altura_pequeña},{self.config.altura_pequeña}")
            self._agregar_comando(f"^FD{serie_texto}^FS")
            y_actual += self.config.altura_pequeña + 2
        
        # Placa (para vehículos)
        if 'placa' in self.config.campos_incluir and bien.placa:
            placa_texto = f"Placa: {bien.placa}"
            self._agregar_comando(f"^FO{x_texto},{y_actual}")
            self._agregar_comando(f"^{self.config.fuente_pequeña}{self.config.tamaño_texto},{self.config.altura_pequeña},{self.config.altura_pequeña}")
            self._agregar_comando(f"^FD{placa_texto}^FS")
            y_actual += self.config.altura_pequeña + 2
    
    def _agregar_fecha(self):
        """Agrega fecha de generación"""
        fecha_texto = datetime.now().strftime('%d/%m/%Y')
        
        # Posicionar en la esquina inferior derecha
        x_fecha = self.config.ancho - self.config.margen - 80
        y_fecha = self.config.alto - self.config.margen - self.config.altura_pequeña
        
        self._agregar_comando(f"^FO{x_fecha},{y_fecha}")
        self._agregar_comando(f"^{self.config.fuente_pequeña}{self.config.tamaño_texto},{self.config.altura_pequeña},{self.config.altura_pequeña}")
        self._agregar_comando(f"^FD{fecha_texto}^FS")
    
    def _agregar_linea_separadora(self):
        """Agrega línea separadora"""
        y_linea = self.config.alto - 40
        x_inicio = self.config.margen
        ancho_linea = self.config.ancho - 2*self.config.margen
        
        self._agregar_comando(f"^FO{x_inicio},{y_linea}")
        self._agregar_comando(f"^GB{ancho_linea},1,1^FS")
    
    def _truncar_texto(self, texto, ancho_disponible, altura_fuente):
        """
        Trunca texto para que quepa en el ancho disponible
        
        Args:
            texto: Texto a truncar
            ancho_disponible: Ancho disponible en dots
            altura_fuente: Altura de la fuente
            
        Returns:
            str: Texto truncado
        """
        if not texto:
            return ""
        
        # Estimación aproximada: cada carácter ocupa ~60% de la altura de la fuente
        caracteres_por_dot = 0.6 / altura_fuente
        max_caracteres = int(ancho_disponible * caracteres_por_dot)
        
        if len(texto) <= max_caracteres:
            return texto
        
        return texto[:max_caracteres-3] + "..."


class ValidadorZPL:
    """Validador de código ZPL"""
    
    @staticmethod
    def validar_codigo(codigo_zpl):
        """
        Valida código ZPL básico
        
        Args:
            codigo_zpl: Código ZPL a validar
            
        Returns:
            tuple: (es_valido, errores)
        """
        errores = []
        
        if not codigo_zpl:
            errores.append("El código ZPL está vacío")
            return False, errores
        
        # Verificar comandos básicos
        if "^XA" not in codigo_zpl:
            errores.append("Falta comando de inicio ^XA")
        
        if "^XZ" not in codigo_zpl:
            errores.append("Falta comando de fin ^XZ")
        
        # Contar comandos de inicio y fin
        inicios = codigo_zpl.count("^XA")
        fines = codigo_zpl.count("^XZ")
        
        if inicios != fines:
            errores.append(f"Desbalance de comandos: {inicios} ^XA vs {fines} ^XZ")
        
        # Verificar comandos de campo
        if "^FD" in codigo_zpl and "^FS" not in codigo_zpl:
            errores.append("Comandos de campo ^FD sin cierre ^FS")
        
        return len(errores) == 0, errores
    
    @staticmethod
    def estimar_tamaño_impresion(codigo_zpl, dpi=203):
        """
        Estima el tamaño de impresión del código ZPL
        
        Args:
            codigo_zpl: Código ZPL
            dpi: DPI de la impresora (por defecto 203)
            
        Returns:
            dict: Dimensiones estimadas
        """
        # Buscar comandos de gráficos para estimar tamaño
        import re
        
        # Buscar comandos ^GB (graphic box) para estimar dimensiones
        gb_matches = re.findall(r'\^GB(\d+),(\d+),', codigo_zpl)
        
        max_ancho = 0
        max_alto = 0
        
        for ancho, alto in gb_matches:
            max_ancho = max(max_ancho, int(ancho))
            max_alto = max(max_alto, int(alto))
        
        # Buscar posiciones ^FO para estimar área utilizada
        fo_matches = re.findall(r'\^FO(\d+),(\d+)', codigo_zpl)
        
        for x, y in fo_matches:
            max_ancho = max(max_ancho, int(x) + 100)  # Estimación
            max_alto = max(max_alto, int(y) + 30)     # Estimación
        
        return {
            'ancho_dots': max_ancho,
            'alto_dots': max_alto,
            'ancho_pulgadas': round(max_ancho / dpi, 2),
            'alto_pulgadas': round(max_alto / dpi, 2),
            'ancho_mm': round(max_ancho / dpi * 25.4, 1),
            'alto_mm': round(max_alto / dpi * 25.4, 1),
        }


def generar_plantilla_configuracion():
    """
    Genera una plantilla de configuración para stickers
    
    Returns:
        dict: Configuración por defecto
    """
    return {
        'tamaño': 'mediano',
        'incluir_qr': True,
        'posicion_qr': 'izquierda',
        'campos_incluir': [
            'codigo_patrimonial',
            'denominacion',
            'oficina',
            'estado',
            'marca_modelo',
            'serie'
        ],
        'incluir_borde': True,
        'incluir_fecha': True,
        'incluir_linea_separadora': True,
        'fuente_titulo': 'A',
        'altura_titulo': 30,
        'fuente_texto': 'A',
        'altura_texto': 20,
        'altura_pequeña': 15,
        'margen': 20,
    }