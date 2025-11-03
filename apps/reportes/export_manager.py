"""
Gestor centralizado de exportaciones en múltiples formatos
"""

import os
import tempfile
from datetime import datetime
from django.conf import settings
from django.core.files import File
from django.utils import timezone
from django.template.loader import render_to_string
import logging

from .exportadores import ExportadorExcel, ExportadorCSV, ExportadorZPL
from .generadores import GeneradorReportePDF, GeneradorReporteEstadistico, GeneradorIndicadoresClave
from .models import ReporteGenerado
from .utils import FiltroAvanzado

logger = logging.getLogger(__name__)


class ExportManager:
    """Gestor centralizado para todas las exportaciones"""
    
    FORMATOS_DISPONIBLES = {
        'EXCEL': {
            'extension': '.xlsx',
            'content_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'descripcion': 'Microsoft Excel',
            'icono': 'fas fa-file-excel',
            'color': '#1d6f42'
        },
        'PDF': {
            'extension': '.pdf',
            'content_type': 'application/pdf',
            'descripcion': 'Documento PDF',
            'icono': 'fas fa-file-pdf',
            'color': '#dc3545'
        },
        'CSV': {
            'extension': '.csv',
            'content_type': 'text/csv',
            'descripcion': 'Valores Separados por Comas',
            'icono': 'fas fa-file-csv',
            'color': '#28a745'
        },
        'ZPL': {
            'extension': '.zpl',
            'content_type': 'text/plain',
            'descripcion': 'Plantilla ZPL para Zebra',
            'icono': 'fas fa-print',
            'color': '#6f42c1'
        }
    }
    
    TIPOS_REPORTE = {
        'INVENTARIO': {
            'nombre': 'Inventario General',
            'descripcion': 'Lista completa de bienes con todos los detalles',
            'formatos_soportados': ['EXCEL', 'PDF', 'CSV'],
            'icono': 'fas fa-list'
        },
        'ESTADISTICO': {
            'nombre': 'Reporte Estadístico',
            'descripcion': 'Análisis estadístico con gráficos y tendencias',
            'formatos_soportados': ['PDF', 'EXCEL'],
            'icono': 'fas fa-chart-bar'
        },
        'EJECUTIVO': {
            'nombre': 'Reporte Ejecutivo',
            'descripcion': 'Resumen ejecutivo con KPIs e indicadores clave',
            'formatos_soportados': ['PDF', 'EXCEL'],
            'icono': 'fas fa-chart-line'
        },
        'STICKERS': {
            'nombre': 'Plantilla de Stickers',
            'descripcion': 'Plantilla ZPL para impresión de etiquetas',
            'formatos_soportados': ['ZPL'],
            'icono': 'fas fa-tags'
        },
        'PERSONALIZADO': {
            'nombre': 'Reporte Personalizado',
            'descripcion': 'Reporte configurado según parámetros específicos',
            'formatos_soportados': ['EXCEL', 'PDF', 'CSV'],
            'icono': 'fas fa-cogs'
        }
    }
    
    def __init__(self):
        self.temp_files = []
    
    def exportar(self, queryset, tipo_reporte, formato, parametros=None, usuario=None):
        """
        Exporta datos en el formato especificado
        
        Args:
            queryset: QuerySet de bienes a exportar
            tipo_reporte: Tipo de reporte (INVENTARIO, ESTADISTICO, etc.)
            formato: Formato de exportación (EXCEL, PDF, CSV, ZPL)
            parametros: Parámetros adicionales para la exportación
            usuario: Usuario que solicita la exportación
            
        Returns:
            dict: Información del archivo generado
        """
        if formato not in self.FORMATOS_DISPONIBLES:
            raise ValueError(f"Formato {formato} no soportado")
        
        if tipo_reporte not in self.TIPOS_REPORTE:
            raise ValueError(f"Tipo de reporte {tipo_reporte} no soportado")
        
        if formato not in self.TIPOS_REPORTE[tipo_reporte]['formatos_soportados']:
            raise ValueError(f"Formato {formato} no soportado para tipo {tipo_reporte}")
        
        parametros = parametros or {}
        
        try:
            # Generar archivo según tipo y formato
            archivo_info = self._generar_archivo(queryset, tipo_reporte, formato, parametros)
            
            # Agregar metadatos
            archivo_info.update({
                'tipo_reporte': tipo_reporte,
                'formato': formato,
                'total_registros': queryset.count(),
                'fecha_generacion': timezone.now(),
                'usuario': usuario.username if usuario else None,
                'parametros': parametros
            })
            
            return archivo_info
            
        except Exception as e:
            logger.error(f"Error exportando {tipo_reporte} en formato {formato}: {str(e)}")
            raise
    
    def _generar_archivo(self, queryset, tipo_reporte, formato, parametros):
        """Genera el archivo según el tipo y formato especificado"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if tipo_reporte == 'INVENTARIO':
            return self._generar_inventario(queryset, formato, timestamp, parametros)
        elif tipo_reporte == 'ESTADISTICO':
            return self._generar_estadistico(queryset, formato, timestamp, parametros)
        elif tipo_reporte == 'EJECUTIVO':
            return self._generar_ejecutivo(queryset, formato, timestamp, parametros)
        elif tipo_reporte == 'STICKERS':
            return self._generar_stickers(queryset, formato, timestamp, parametros)
        elif tipo_reporte == 'PERSONALIZADO':
            return self._generar_personalizado(queryset, formato, timestamp, parametros)
        else:
            raise ValueError(f"Tipo de reporte {tipo_reporte} no implementado")
    
    def _generar_inventario(self, queryset, formato, timestamp, parametros):
        """Genera reporte de inventario"""
        if formato == 'EXCEL':
            exportador = ExportadorExcel()
            archivo_temp = self._crear_archivo_temporal('.xlsx', f'inventario_{timestamp}_')
            exportador.exportar_bienes(queryset, archivo_temp)
            
        elif formato == 'CSV':
            exportador = ExportadorCSV()
            archivo_temp = self._crear_archivo_temporal('.csv', f'inventario_{timestamp}_')
            exportador.exportar_bienes(queryset, archivo_temp)
            
        elif formato == 'PDF':
            generador = GeneradorReportePDF(queryset, parametros)
            archivo_temp = self._crear_archivo_temporal('.pdf', f'inventario_{timestamp}_')
            generador.generar_reporte_completo(archivo_temp)
        
        return {
            'archivo_path': archivo_temp,
            'nombre_archivo': f'inventario_{timestamp}{self.FORMATOS_DISPONIBLES[formato]["extension"]}',
            'content_type': self.FORMATOS_DISPONIBLES[formato]['content_type']
        }
    
    def _generar_estadistico(self, queryset, formato, timestamp, parametros):
        """Genera reporte estadístico"""
        if formato == 'PDF':
            generador = GeneradorReportePDF(queryset, parametros)
            archivo_temp = self._crear_archivo_temporal('.pdf', f'estadistico_{timestamp}_')
            generador.generar_reporte_completo(archivo_temp)
            
        elif formato == 'EXCEL':
            # Generar estadísticas
            generador_stats = GeneradorReporteEstadistico(queryset, parametros)
            estadisticas = generador_stats.generar_estadisticas()
            
            exportador = ExportadorExcel()
            archivo_temp = self._crear_archivo_temporal('.xlsx', f'estadistico_{timestamp}_')
            exportador.exportar_estadisticas(estadisticas, archivo_temp)
        
        return {
            'archivo_path': archivo_temp,
            'nombre_archivo': f'estadistico_{timestamp}{self.FORMATOS_DISPONIBLES[formato]["extension"]}',
            'content_type': self.FORMATOS_DISPONIBLES[formato]['content_type']
        }
    
    def _generar_ejecutivo(self, queryset, formato, timestamp, parametros):
        """Genera reporte ejecutivo"""
        # Generar KPIs
        generador_kpis = GeneradorIndicadoresClave(queryset)
        kpis = generador_kpis.calcular_kpis()
        
        # Agregar KPIs a parámetros
        parametros_con_kpis = parametros.copy()
        parametros_con_kpis['kpis'] = kpis
        
        if formato == 'PDF':
            generador = GeneradorReportePDF(queryset, parametros_con_kpis)
            archivo_temp = self._crear_archivo_temporal('.pdf', f'ejecutivo_{timestamp}_')
            generador.generar_reporte_completo(archivo_temp)
            
        elif formato == 'EXCEL':
            # Crear Excel con KPIs
            exportador = ExportadorExcel()
            archivo_temp = self._crear_archivo_temporal('.xlsx', f'ejecutivo_{timestamp}_')
            
            # Generar estadísticas completas
            generador_stats = GeneradorReporteEstadistico(queryset, parametros_con_kpis)
            estadisticas = generador_stats.generar_estadisticas()
            estadisticas['kpis'] = kpis
            
            exportador.exportar_estadisticas(estadisticas, archivo_temp)
        
        return {
            'archivo_path': archivo_temp,
            'nombre_archivo': f'ejecutivo_{timestamp}{self.FORMATOS_DISPONIBLES[formato]["extension"]}',
            'content_type': self.FORMATOS_DISPONIBLES[formato]['content_type']
        }
    
    def _generar_stickers(self, queryset, formato, timestamp, parametros):
        """Genera plantilla de stickers"""
        if formato == 'ZPL':
            exportador = ExportadorZPL()
            archivo_temp = self._crear_archivo_temporal('.zpl', f'stickers_{timestamp}_')
            exportador.generar_plantilla_stickers(queryset, archivo_temp)
        
        return {
            'archivo_path': archivo_temp,
            'nombre_archivo': f'stickers_{timestamp}{self.FORMATOS_DISPONIBLES[formato]["extension"]}',
            'content_type': self.FORMATOS_DISPONIBLES[formato]['content_type']
        }
    
    def _generar_personalizado(self, queryset, formato, timestamp, parametros):
        """Genera reporte personalizado"""
        # Determinar qué tipo de reporte generar según parámetros
        incluir_graficos = parametros.get('incluir_graficos', False)
        incluir_kpis = parametros.get('incluir_kpis', False)
        
        if incluir_kpis:
            return self._generar_ejecutivo(queryset, formato, timestamp, parametros)
        elif incluir_graficos:
            return self._generar_estadistico(queryset, formato, timestamp, parametros)
        else:
            return self._generar_inventario(queryset, formato, timestamp, parametros)
    
    def _crear_archivo_temporal(self, extension, prefix):
        """Crea un archivo temporal y lo registra para limpieza"""
        archivo_temp = tempfile.NamedTemporaryFile(
            suffix=extension,
            delete=False,
            prefix=prefix
        )
        archivo_temp.close()
        self.temp_files.append(archivo_temp.name)
        return archivo_temp.name
    
    def limpiar_archivos_temporales(self):
        """Limpia todos los archivos temporales creados"""
        for archivo in self.temp_files:
            try:
                if os.path.exists(archivo):
                    os.remove(archivo)
            except OSError as e:
                logger.warning(f"No se pudo eliminar archivo temporal {archivo}: {str(e)}")
        
        self.temp_files.clear()
    
    def obtener_formatos_disponibles(self, tipo_reporte=None):
        """
        Obtiene los formatos disponibles para un tipo de reporte
        
        Args:
            tipo_reporte: Tipo de reporte (opcional)
            
        Returns:
            dict: Formatos disponibles con información
        """
        if tipo_reporte and tipo_reporte in self.TIPOS_REPORTE:
            formatos_soportados = self.TIPOS_REPORTE[tipo_reporte]['formatos_soportados']
            return {
                formato: info for formato, info in self.FORMATOS_DISPONIBLES.items()
                if formato in formatos_soportados
            }
        
        return self.FORMATOS_DISPONIBLES.copy()
    
    def validar_exportacion(self, tipo_reporte, formato, queryset=None):
        """
        Valida si una exportación es posible
        
        Args:
            tipo_reporte: Tipo de reporte
            formato: Formato de exportación
            queryset: QuerySet de datos (opcional)
            
        Returns:
            tuple: (es_valida, mensaje_error)
        """
        if tipo_reporte not in self.TIPOS_REPORTE:
            return False, f"Tipo de reporte '{tipo_reporte}' no válido"
        
        if formato not in self.FORMATOS_DISPONIBLES:
            return False, f"Formato '{formato}' no válido"
        
        if formato not in self.TIPOS_REPORTE[tipo_reporte]['formatos_soportados']:
            return False, f"Formato '{formato}' no soportado para tipo '{tipo_reporte}'"
        
        if queryset is not None and queryset.count() == 0:
            return False, "No hay datos para exportar"
        
        if queryset is not None and queryset.count() > 10000:
            return False, "Demasiados registros para exportar (máximo 10,000)"
        
        return True, "Exportación válida"
    
    def estimar_tiempo_exportacion(self, tipo_reporte, formato, total_registros):
        """
        Estima el tiempo de exportación
        
        Args:
            tipo_reporte: Tipo de reporte
            formato: Formato de exportación
            total_registros: Número de registros
            
        Returns:
            int: Tiempo estimado en segundos
        """
        # Tiempos base por formato (segundos por 1000 registros)
        tiempos_base = {
            'CSV': 2,
            'EXCEL': 5,
            'PDF': 10,
            'ZPL': 3
        }
        
        # Multiplicadores por tipo de reporte
        multiplicadores = {
            'INVENTARIO': 1.0,
            'ESTADISTICO': 2.0,
            'EJECUTIVO': 1.5,
            'STICKERS': 0.8,
            'PERSONALIZADO': 1.2
        }
        
        tiempo_base = tiempos_base.get(formato, 5)
        multiplicador = multiplicadores.get(tipo_reporte, 1.0)
        
        tiempo_estimado = (total_registros / 1000) * tiempo_base * multiplicador
        
        # Mínimo 5 segundos, máximo 300 segundos (5 minutos)
        return max(5, min(300, int(tiempo_estimado)))
    
    def generar_nombre_archivo(self, tipo_reporte, formato, timestamp=None, prefijo=None):
        """
        Genera un nombre de archivo estándar
        
        Args:
            tipo_reporte: Tipo de reporte
            formato: Formato del archivo
            timestamp: Timestamp personalizado (opcional)
            prefijo: Prefijo personalizado (opcional)
            
        Returns:
            str: Nombre del archivo
        """
        if not timestamp:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if not prefijo:
            prefijo = tipo_reporte.lower()
        
        extension = self.FORMATOS_DISPONIBLES[formato]['extension']
        
        return f"{prefijo}_{timestamp}{extension}"
    
    def obtener_metadatos_exportacion(self, archivo_path):
        """
        Obtiene metadatos de un archivo exportado
        
        Args:
            archivo_path: Ruta del archivo
            
        Returns:
            dict: Metadatos del archivo
        """
        try:
            stat = os.stat(archivo_path)
            
            return {
                'tamaño_bytes': stat.st_size,
                'tamaño_mb': round(stat.st_size / (1024 * 1024), 2),
                'fecha_creacion': datetime.fromtimestamp(stat.st_ctime),
                'fecha_modificacion': datetime.fromtimestamp(stat.st_mtime),
                'extension': os.path.splitext(archivo_path)[1],
                'nombre_archivo': os.path.basename(archivo_path)
            }
            
        except OSError:
            return {}


class BatchExportManager:
    """Gestor para exportaciones masivas"""
    
    def __init__(self):
        self.export_manager = ExportManager()
    
    def exportar_por_lotes(self, configuraciones_exportacion, usuario=None):
        """
        Exporta múltiples reportes en lote
        
        Args:
            configuraciones_exportacion: Lista de configuraciones
            usuario: Usuario que solicita las exportaciones
            
        Returns:
            list: Lista de resultados de exportación
        """
        resultados = []
        
        for i, config in enumerate(configuraciones_exportacion):
            try:
                resultado = self.export_manager.exportar(
                    queryset=config['queryset'],
                    tipo_reporte=config['tipo_reporte'],
                    formato=config['formato'],
                    parametros=config.get('parametros', {}),
                    usuario=usuario
                )
                
                resultado['lote_indice'] = i + 1
                resultado['lote_total'] = len(configuraciones_exportacion)
                resultado['estado'] = 'EXITOSO'
                
                resultados.append(resultado)
                
            except Exception as e:
                logger.error(f"Error en exportación de lote {i+1}: {str(e)}")
                
                resultados.append({
                    'lote_indice': i + 1,
                    'lote_total': len(configuraciones_exportacion),
                    'estado': 'ERROR',
                    'error': str(e),
                    'configuracion': config
                })
        
        return resultados
    
    def crear_zip_exportaciones(self, archivos_exportacion, nombre_zip=None):
        """
        Crea un archivo ZIP con múltiples exportaciones
        
        Args:
            archivos_exportacion: Lista de rutas de archivos
            nombre_zip: Nombre del archivo ZIP (opcional)
            
        Returns:
            str: Ruta del archivo ZIP creado
        """
        import zipfile
        
        if not nombre_zip:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            nombre_zip = f'exportaciones_masivas_{timestamp}.zip'
        
        archivo_zip = tempfile.NamedTemporaryFile(
            suffix='.zip',
            delete=False,
            prefix='exportaciones_'
        )
        archivo_zip.close()
        
        try:
            with zipfile.ZipFile(archivo_zip.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for archivo_path in archivos_exportacion:
                    if os.path.exists(archivo_path):
                        nombre_en_zip = os.path.basename(archivo_path)
                        zipf.write(archivo_path, nombre_en_zip)
            
            return archivo_zip.name
            
        except Exception as e:
            logger.error(f"Error creando ZIP: {str(e)}")
            try:
                os.remove(archivo_zip.name)
            except OSError:
                pass
            raise