import io
import os
from datetime import datetime, timedelta
from django.conf import settings
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from django.template.loader import render_to_string
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_pdf import PdfPages
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.lib.colors import HexColor

from apps.bienes.models import BienPatrimonial
from apps.catalogo.models import Catalogo
from apps.oficinas.models import Oficina
from .utils import FiltroAvanzado, GeneradorEstadisticas
import logging

logger = logging.getLogger(__name__)

# Configurar estilo de matplotlib
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")


class GeneradorReporteEstadistico:
    """Generador de reportes estadísticos con gráficos"""
    
    def __init__(self, queryset=None, parametros=None):
        """
        Inicializa el generador
        
        Args:
            queryset: QuerySet de bienes a analizar
            parametros: Parámetros adicionales para el reporte
        """
        self.queryset = queryset or BienPatrimonial.objects.all()
        self.parametros = parametros or {}
        self.estadisticas = None
        self.graficos_generados = []
    
    def generar_estadisticas(self):
        """Genera todas las estadísticas necesarias"""
        filtro = FiltroAvanzado()
        self.estadisticas = filtro.obtener_estadisticas(self.queryset)
        
        # Estadísticas adicionales
        self.estadisticas.update({
            'resumen_ejecutivo': GeneradorEstadisticas.generar_resumen_ejecutivo(self.queryset),
            'alertas': GeneradorEstadisticas.generar_alertas_mantenimiento(self.queryset),
            'tendencias': self._generar_tendencias(),
            'comparativas': self._generar_comparativas(),
        })
        
        return self.estadisticas
    
    def _generar_tendencias(self):
        """Genera análisis de tendencias temporales"""
        # Tendencias por año de registro
        tendencias_año = list(self.queryset.extra(
            select={'año': 'EXTRACT(year FROM created_at)'}
        ).values('año').annotate(
            total=Count('id')
        ).order_by('año'))
        
        # Tendencias por mes (últimos 12 meses)
        fecha_limite = timezone.now() - timedelta(days=365)
        tendencias_mes = list(self.queryset.filter(
            created_at__gte=fecha_limite
        ).extra(
            select={
                'año': 'EXTRACT(year FROM created_at)',
                'mes': 'EXTRACT(month FROM created_at)'
            }
        ).values('año', 'mes').annotate(
            total=Count('id')
        ).order_by('año', 'mes'))
        
        return {
            'por_año': tendencias_año,
            'por_mes': tendencias_mes,
        }
    
    def _generar_comparativas(self):
        """Genera análisis comparativos"""
        # Comparativa por estado vs oficina
        comparativa_estado_oficina = list(self.queryset.values(
            'estado_bien', 'oficina__nombre'
        ).annotate(
            total=Count('id')
        ).order_by('oficina__nombre', 'estado_bien'))
        
        # Comparativa por grupo vs estado
        comparativa_grupo_estado = list(self.queryset.values(
            'catalogo__grupo', 'estado_bien'
        ).annotate(
            total=Count('id')
        ).order_by('catalogo__grupo', 'estado_bien'))
        
        return {
            'estado_oficina': comparativa_estado_oficina,
            'grupo_estado': comparativa_grupo_estado,
        }
    
    def generar_grafico_estados(self, archivo_salida=None):
        """Genera gráfico de distribución por estados"""
        if not self.estadisticas:
            self.generar_estadisticas()
        
        # Preparar datos
        estados_data = self.estadisticas['por_estado']
        if not estados_data:
            return None
        
        estados_nombres = []
        estados_valores = []
        estados_colores = []
        
        color_map = {
            'N': '#28a745',  # Verde para Nuevo
            'B': '#17a2b8',  # Azul para Bueno
            'R': '#ffc107',  # Amarillo para Regular
            'M': '#fd7e14',  # Naranja para Malo
            'E': '#6f42c1',  # Púrpura para RAEE
            'C': '#dc3545'   # Rojo para Chatarra
        }
        
        estados_texto = {
            'N': 'Nuevo',
            'B': 'Bueno',
            'R': 'Regular',
            'M': 'Malo',
            'E': 'RAEE',
            'C': 'Chatarra'
        }
        
        for estado in estados_data:
            codigo = estado['estado_bien']
            estados_nombres.append(estados_texto.get(codigo, codigo))
            estados_valores.append(estado['total'])
            estados_colores.append(color_map.get(codigo, '#6c757d'))
        
        # Crear gráfico
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Gráfico de torta
        wedges, texts, autotexts = ax1.pie(
            estados_valores, 
            labels=estados_nombres,
            colors=estados_colores,
            autopct='%1.1f%%',
            startangle=90
        )
        ax1.set_title('Distribución de Bienes por Estado', fontsize=14, fontweight='bold')
        
        # Gráfico de barras
        bars = ax2.bar(estados_nombres, estados_valores, color=estados_colores)
        ax2.set_title('Cantidad de Bienes por Estado', fontsize=14, fontweight='bold')
        ax2.set_ylabel('Cantidad de Bienes')
        ax2.tick_params(axis='x', rotation=45)
        
        # Agregar valores en las barras
        for bar in bars:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}',
                    ha='center', va='bottom')
        
        plt.tight_layout()
        
        # Guardar archivo
        if archivo_salida:
            plt.savefig(archivo_salida, dpi=300, bbox_inches='tight')
            self.graficos_generados.append(archivo_salida)
        
        return fig
    
    def generar_grafico_oficinas(self, archivo_salida=None, top_n=10):
        """Genera gráfico de distribución por oficinas"""
        if not self.estadisticas:
            self.generar_estadisticas()
        
        # Preparar datos (top N oficinas)
        oficinas_data = self.estadisticas['por_oficina'][:top_n]
        if not oficinas_data:
            return None
        
        oficinas_nombres = [item['oficina__nombre'] or 'Sin nombre' for item in oficinas_data]
        oficinas_valores = [item['total'] for item in oficinas_data]
        
        # Crear gráfico
        fig, ax = plt.subplots(figsize=(12, 8))
        
        bars = ax.barh(oficinas_nombres, oficinas_valores, color='skyblue')
        ax.set_title(f'Top {top_n} Oficinas con Más Bienes', fontsize=14, fontweight='bold')
        ax.set_xlabel('Cantidad de Bienes')
        
        # Agregar valores en las barras
        for bar in bars:
            width = bar.get_width()
            ax.text(width, bar.get_y() + bar.get_height()/2.,
                   f'{int(width)}',
                   ha='left', va='center', fontweight='bold')
        
        plt.tight_layout()
        
        # Guardar archivo
        if archivo_salida:
            plt.savefig(archivo_salida, dpi=300, bbox_inches='tight')
            self.graficos_generados.append(archivo_salida)
        
        return fig
    
    def generar_grafico_tendencias(self, archivo_salida=None):
        """Genera gráfico de tendencias temporales"""
        if not self.estadisticas:
            self.generar_estadisticas()
        
        tendencias = self.estadisticas.get('tendencias', {})
        tendencias_año = tendencias.get('por_año', [])
        
        if not tendencias_año:
            return None
        
        # Preparar datos
        años = [int(item['año']) for item in tendencias_año]
        totales = [item['total'] for item in tendencias_año]
        
        # Crear gráfico
        fig, ax = plt.subplots(figsize=(12, 6))
        
        ax.plot(años, totales, marker='o', linewidth=2, markersize=8, color='#007bff')
        ax.fill_between(años, totales, alpha=0.3, color='#007bff')
        
        ax.set_title('Tendencia de Registro de Bienes por Año', fontsize=14, fontweight='bold')
        ax.set_xlabel('Año')
        ax.set_ylabel('Cantidad de Bienes Registrados')
        ax.grid(True, alpha=0.3)
        
        # Agregar valores en los puntos
        for x, y in zip(años, totales):
            ax.annotate(f'{y}', (x, y), textcoords="offset points", 
                       xytext=(0,10), ha='center', fontweight='bold')
        
        plt.tight_layout()
        
        # Guardar archivo
        if archivo_salida:
            plt.savefig(archivo_salida, dpi=300, bbox_inches='tight')
            self.graficos_generados.append(archivo_salida)
        
        return fig
    
    def generar_grafico_grupos(self, archivo_salida=None, top_n=8):
        """Genera gráfico de distribución por grupos de catálogo"""
        if not self.estadisticas:
            self.generar_estadisticas()
        
        # Preparar datos
        grupos_data = self.estadisticas['por_grupo'][:top_n]
        if not grupos_data:
            return None
        
        grupos_nombres = []
        grupos_valores = []
        
        for item in grupos_data:
            grupo = item['catalogo__grupo'] or 'Sin grupo'
            # Truncar nombres largos
            if len(grupo) > 30:
                grupo = grupo[:27] + '...'
            grupos_nombres.append(grupo)
            grupos_valores.append(item['total'])
        
        # Crear gráfico
        fig, ax = plt.subplots(figsize=(12, 8))
        
        bars = ax.bar(range(len(grupos_nombres)), grupos_valores, 
                     color=plt.cm.Set3(range(len(grupos_nombres))))
        
        ax.set_title(f'Top {top_n} Grupos de Catálogo', fontsize=14, fontweight='bold')
        ax.set_ylabel('Cantidad de Bienes')
        ax.set_xticks(range(len(grupos_nombres)))
        ax.set_xticklabels(grupos_nombres, rotation=45, ha='right')
        
        # Agregar valores en las barras
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height)}',
                   ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        
        # Guardar archivo
        if archivo_salida:
            plt.savefig(archivo_salida, dpi=300, bbox_inches='tight')
            self.graficos_generados.append(archivo_salida)
        
        return fig
    
    def generar_todos_los_graficos(self, directorio_salida=None):
        """Genera todos los gráficos estadísticos"""
        if not directorio_salida:
            directorio_salida = os.path.join(settings.MEDIA_ROOT, 'reportes', 'graficos')
        
        os.makedirs(directorio_salida, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        graficos = {}
        
        try:
            # Gráfico de estados
            archivo_estados = os.path.join(directorio_salida, f'estados_{timestamp}.png')
            fig_estados = self.generar_grafico_estados(archivo_estados)
            if fig_estados:
                graficos['estados'] = archivo_estados
                plt.close(fig_estados)
            
            # Gráfico de oficinas
            archivo_oficinas = os.path.join(directorio_salida, f'oficinas_{timestamp}.png')
            fig_oficinas = self.generar_grafico_oficinas(archivo_oficinas)
            if fig_oficinas:
                graficos['oficinas'] = archivo_oficinas
                plt.close(fig_oficinas)
            
            # Gráfico de tendencias
            archivo_tendencias = os.path.join(directorio_salida, f'tendencias_{timestamp}.png')
            fig_tendencias = self.generar_grafico_tendencias(archivo_tendencias)
            if fig_tendencias:
                graficos['tendencias'] = archivo_tendencias
                plt.close(fig_tendencias)
            
            # Gráfico de grupos
            archivo_grupos = os.path.join(directorio_salida, f'grupos_{timestamp}.png')
            fig_grupos = self.generar_grafico_grupos(archivo_grupos)
            if fig_grupos:
                graficos['grupos'] = archivo_grupos
                plt.close(fig_grupos)
            
        except Exception as e:
            logger.error(f"Error generando gráficos: {str(e)}")
            raise
        
        return graficos


class GeneradorReportePDF:
    """Generador de reportes en formato PDF con gráficos"""
    
    def __init__(self, queryset=None, parametros=None):
        """
        Inicializa el generador de PDF
        
        Args:
            queryset: QuerySet de bienes
            parametros: Parámetros del reporte
        """
        self.queryset = queryset or BienPatrimonial.objects.all()
        self.parametros = parametros or {}
        self.generador_estadistico = GeneradorReporteEstadistico(queryset, parametros)
        self.styles = getSampleStyleSheet()
        self._configurar_estilos()
    
    def _configurar_estilos(self):
        """Configura estilos personalizados para el PDF"""
        # Estilo para títulos principales
        self.styles.add(ParagraphStyle(
            name='TituloPrincipal',
            parent=self.styles['Title'],
            fontSize=18,
            spaceAfter=20,
            textColor=colors.darkblue,
            alignment=1  # Centrado
        ))
        
        # Estilo para subtítulos
        self.styles.add(ParagraphStyle(
            name='Subtitulo',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.darkblue
        ))
        
        # Estilo para texto normal
        self.styles.add(ParagraphStyle(
            name='TextoNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6
        ))
    
    def generar_reporte_completo(self, archivo_salida):
        """
        Genera un reporte PDF completo con estadísticas y gráficos
        
        Args:
            archivo_salida: Ruta del archivo PDF a generar
            
        Returns:
            str: Ruta del archivo generado
        """
        # Crear documento PDF
        doc = SimpleDocTemplate(
            archivo_salida,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Contenido del reporte
        story = []
        
        # Generar estadísticas
        estadisticas = self.generador_estadistico.generar_estadisticas()
        
        # Generar gráficos
        graficos = self.generador_estadistico.generar_todos_los_graficos()
        
        # Portada
        story.extend(self._generar_portada(estadisticas))
        
        # Resumen ejecutivo
        story.extend(self._generar_resumen_ejecutivo(estadisticas))
        
        # Estadísticas detalladas
        story.extend(self._generar_estadisticas_detalladas(estadisticas, graficos))
        
        # Análisis de tendencias
        story.extend(self._generar_analisis_tendencias(estadisticas, graficos))
        
        # Alertas y recomendaciones
        story.extend(self._generar_alertas_recomendaciones(estadisticas))
        
        # Construir PDF
        doc.build(story)
        
        # Limpiar archivos temporales de gráficos
        self._limpiar_graficos_temporales(graficos)
        
        return archivo_salida
    
    def _generar_portada(self, estadisticas):
        """Genera la portada del reporte"""
        story = []
        
        # Título principal
        titulo = Paragraph(
            "REPORTE ESTADÍSTICO DE PATRIMONIO",
            self.styles['TituloPrincipal']
        )
        story.append(titulo)
        story.append(Spacer(1, 20))
        
        # Información institucional
        info_institucional = Paragraph(
            "Dirección Regional de Transportes y Comunicaciones - Puno<br/>"
            "Sistema de Registro de Patrimonio",
            self.styles['TextoNormal']
        )
        story.append(info_institucional)
        story.append(Spacer(1, 30))
        
        # Fecha de generación
        fecha_generacion = Paragraph(
            f"Fecha de generación: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            self.styles['TextoNormal']
        )
        story.append(fecha_generacion)
        story.append(Spacer(1, 20))
        
        # Resumen de datos
        total_bienes = estadisticas.get('total_bienes', 0)
        resumen_datos = Paragraph(
            f"Total de bienes analizados: <b>{total_bienes:,}</b>",
            self.styles['TextoNormal']
        )
        story.append(resumen_datos)
        
        # Salto de página
        story.append(Spacer(1, 400))
        
        return story
    
    def _generar_resumen_ejecutivo(self, estadisticas):
        """Genera el resumen ejecutivo"""
        story = []
        
        # Título de sección
        titulo = Paragraph("RESUMEN EJECUTIVO", self.styles['Subtitulo'])
        story.append(titulo)
        story.append(Spacer(1, 12))
        
        resumen = estadisticas.get('resumen_ejecutivo', {})
        
        # Indicadores clave
        indicadores_data = [
            ['Indicador', 'Valor'],
            ['Total de Bienes', f"{resumen.get('total_bienes', 0):,}"],
            ['Total de Oficinas', f"{resumen.get('total_oficinas', 0):,}"],
            ['Valor Total (S/)', f"S/ {resumen.get('total_valor', 0):,.2f}"],
            ['Valor Promedio (S/)', f"S/ {resumen.get('valor_promedio', 0):,.2f}"],
        ]
        
        tabla_indicadores = Table(indicadores_data, colWidths=[3*inch, 2*inch])
        tabla_indicadores.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(tabla_indicadores)
        story.append(Spacer(1, 20))
        
        return story
    
    def _generar_estadisticas_detalladas(self, estadisticas, graficos):
        """Genera las estadísticas detalladas con gráficos"""
        story = []
        
        # Título de sección
        titulo = Paragraph("ESTADÍSTICAS DETALLADAS", self.styles['Subtitulo'])
        story.append(titulo)
        story.append(Spacer(1, 12))
        
        # Distribución por estados
        if 'estados' in graficos:
            subtitulo_estados = Paragraph("Distribución por Estado de Conservación", self.styles['Heading3'])
            story.append(subtitulo_estados)
            story.append(Spacer(1, 6))
            
            # Insertar gráfico
            img_estados = Image(graficos['estados'], width=6*inch, height=3*inch)
            story.append(img_estados)
            story.append(Spacer(1, 12))
            
            # Tabla de datos
            estados_data = [['Estado', 'Cantidad', 'Porcentaje']]
            for estado in estadisticas.get('por_estado', []):
                estados_data.append([
                    estado.get('estado_bien', 'N/A'),
                    str(estado.get('total', 0)),
                    f"{estado.get('porcentaje', 0):.1f}%"
                ])
            
            tabla_estados = Table(estados_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
            tabla_estados.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(tabla_estados)
            story.append(Spacer(1, 20))
        
        # Distribución por oficinas
        if 'oficinas' in graficos:
            subtitulo_oficinas = Paragraph("Top 10 Oficinas con Más Bienes", self.styles['Heading3'])
            story.append(subtitulo_oficinas)
            story.append(Spacer(1, 6))
            
            # Insertar gráfico
            img_oficinas = Image(graficos['oficinas'], width=6*inch, height=4*inch)
            story.append(img_oficinas)
            story.append(Spacer(1, 20))
        
        return story
    
    def _generar_analisis_tendencias(self, estadisticas, graficos):
        """Genera el análisis de tendencias"""
        story = []
        
        # Título de sección
        titulo = Paragraph("ANÁLISIS DE TENDENCIAS", self.styles['Subtitulo'])
        story.append(titulo)
        story.append(Spacer(1, 12))
        
        if 'tendencias' in graficos:
            # Insertar gráfico de tendencias
            img_tendencias = Image(graficos['tendencias'], width=6*inch, height=3*inch)
            story.append(img_tendencias)
            story.append(Spacer(1, 12))
            
            # Análisis textual
            tendencias = estadisticas.get('tendencias', {})
            tendencias_año = tendencias.get('por_año', [])
            
            if tendencias_año:
                ultimo_año = max(tendencias_año, key=lambda x: x['año'])
                primer_año = min(tendencias_año, key=lambda x: x['año'])
                
                analisis_texto = f"""
                <b>Análisis de Tendencias:</b><br/>
                • Período analizado: {primer_año['año']} - {ultimo_año['año']}<br/>
                • Registros en {ultimo_año['año']}: {ultimo_año['total']} bienes<br/>
                • Registros en {primer_año['año']}: {primer_año['total']} bienes<br/>
                • Crecimiento total: {ultimo_año['total'] - primer_año['total']} bienes
                """
                
                parrafo_analisis = Paragraph(analisis_texto, self.styles['TextoNormal'])
                story.append(parrafo_analisis)
                story.append(Spacer(1, 20))
        
        return story
    
    def _generar_alertas_recomendaciones(self, estadisticas):
        """Genera alertas y recomendaciones"""
        story = []
        
        # Título de sección
        titulo = Paragraph("ALERTAS Y RECOMENDACIONES", self.styles['Subtitulo'])
        story.append(titulo)
        story.append(Spacer(1, 12))
        
        alertas = estadisticas.get('alertas', {})
        
        # Alertas críticas
        alertas_data = [['Tipo de Alerta', 'Cantidad', 'Recomendación']]
        
        if alertas.get('bienes_malo_estado', 0) > 0:
            alertas_data.append([
                'Bienes en Mal Estado',
                str(alertas['bienes_malo_estado']),
                'Evaluar reparación o baja'
            ])
        
        if alertas.get('bienes_raee', 0) > 0:
            alertas_data.append([
                'Bienes RAEE',
                str(alertas['bienes_raee']),
                'Gestionar disposición final'
            ])
        
        if alertas.get('bienes_chatarra', 0) > 0:
            alertas_data.append([
                'Bienes Chatarra',
                str(alertas['bienes_chatarra']),
                'Proceder con baja patrimonial'
            ])
        
        if alertas.get('sin_valor_adquisicion', 0) > 0:
            alertas_data.append([
                'Sin Valor de Adquisición',
                str(alertas['sin_valor_adquisicion']),
                'Completar información faltante'
            ])
        
        if len(alertas_data) > 1:  # Si hay alertas además del header
            tabla_alertas = Table(alertas_data, colWidths=[2*inch, 1*inch, 2.5*inch])
            tabla_alertas.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.red),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightpink),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            story.append(tabla_alertas)
        else:
            no_alertas = Paragraph(
                "✓ No se encontraron alertas críticas en el inventario.",
                self.styles['TextoNormal']
            )
            story.append(no_alertas)
        
        story.append(Spacer(1, 20))
        
        return story
    
    def _limpiar_graficos_temporales(self, graficos):
        """Limpia los archivos temporales de gráficos"""
        for archivo in graficos.values():
            try:
                if os.path.exists(archivo):
                    os.remove(archivo)
            except Exception as e:
                logger.warning(f"No se pudo eliminar archivo temporal {archivo}: {str(e)}")


class GeneradorIndicadoresClave:
    """Generador de indicadores clave de rendimiento (KPIs)"""
    
    def __init__(self, queryset=None):
        self.queryset = queryset or BienPatrimonial.objects.all()
    
    def calcular_kpis(self):
        """Calcula todos los KPIs del sistema"""
        total_bienes = self.queryset.count()
        
        if total_bienes == 0:
            return self._kpis_vacios()
        
        # KPIs básicos
        kpis = {
            'total_bienes': total_bienes,
            'bienes_operativos': self._calcular_bienes_operativos(),
            'bienes_requieren_atencion': self._calcular_bienes_atencion(),
            'valor_total_inventario': self._calcular_valor_total(),
            'valor_promedio_bien': self._calcular_valor_promedio(),
            'distribucion_estados': self._calcular_distribucion_estados(),
            'cobertura_oficinas': self._calcular_cobertura_oficinas(),
            'completitud_datos': self._calcular_completitud_datos(),
            'antiguedad_promedio': self._calcular_antiguedad_promedio(),
            'tendencia_registro': self._calcular_tendencia_registro(),
        }
        
        # Calcular porcentajes
        kpis.update(self._calcular_porcentajes(kpis, total_bienes))
        
        return kpis
    
    def _kpis_vacios(self):
        """Retorna KPIs con valores cero"""
        return {
            'total_bienes': 0,
            'bienes_operativos': 0,
            'bienes_requieren_atencion': 0,
            'valor_total_inventario': 0,
            'valor_promedio_bien': 0,
            'distribucion_estados': {},
            'cobertura_oficinas': 0,
            'completitud_datos': 0,
            'antiguedad_promedio': 0,
            'tendencia_registro': [],
        }
    
    def _calcular_bienes_operativos(self):
        """Calcula bienes en estado operativo (N, B, R)"""
        return self.queryset.filter(estado_bien__in=['N', 'B', 'R']).count()
    
    def _calcular_bienes_atencion(self):
        """Calcula bienes que requieren atención (M, E, C)"""
        return self.queryset.filter(estado_bien__in=['M', 'E', 'C']).count()
    
    def _calcular_valor_total(self):
        """Calcula el valor total del inventario"""
        resultado = self.queryset.aggregate(
            total=Sum('valor_adquisicion')
        )
        return resultado['total'] or 0
    
    def _calcular_valor_promedio(self):
        """Calcula el valor promedio por bien"""
        resultado = self.queryset.aggregate(
            promedio=Avg('valor_adquisicion')
        )
        return resultado['promedio'] or 0
    
    def _calcular_distribucion_estados(self):
        """Calcula la distribución por estados"""
        distribucion = self.queryset.values('estado_bien').annotate(
            total=Count('id')
        ).order_by('estado_bien')
        
        return {item['estado_bien']: item['total'] for item in distribucion}
    
    def _calcular_cobertura_oficinas(self):
        """Calcula el número de oficinas con bienes asignados"""
        return self.queryset.values('oficina').distinct().count()
    
    def _calcular_completitud_datos(self):
        """Calcula el porcentaje de completitud de datos críticos"""
        total = self.queryset.count()
        if total == 0:
            return 0
        
        # Campos críticos que deben estar completos
        con_valor = self.queryset.filter(valor_adquisicion__isnull=False).count()
        con_fecha = self.queryset.filter(fecha_adquisicion__isnull=False).count()
        con_serie = self.queryset.exclude(serie='').count()
        
        # Promedio de completitud
        completitud = ((con_valor + con_fecha + con_serie) / (total * 3)) * 100
        return round(completitud, 2)
    
    def _calcular_antiguedad_promedio(self):
        """Calcula la antigüedad promedio de los bienes"""
        bienes_con_fecha = self.queryset.filter(fecha_adquisicion__isnull=False)
        if not bienes_con_fecha.exists():
            return 0
        
        from django.utils import timezone
        fecha_actual = timezone.now().date()
        
        total_dias = 0
        count = 0
        
        for bien in bienes_con_fecha:
            dias = (fecha_actual - bien.fecha_adquisicion).days
            total_dias += dias
            count += 1
        
        if count == 0:
            return 0
        
        return round(total_dias / count / 365.25, 1)  # Años
    
    def _calcular_tendencia_registro(self):
        """Calcula la tendencia de registro de bienes"""
        tendencia = list(self.queryset.extra(
            select={'año': 'EXTRACT(year FROM created_at)'}
        ).values('año').annotate(
            total=Count('id')
        ).order_by('año'))
        
        return tendencia
    
    def _calcular_porcentajes(self, kpis, total):
        """Calcula porcentajes basados en los KPIs"""
        if total == 0:
            return {}
        
        return {
            'porcentaje_operativos': round((kpis['bienes_operativos'] / total) * 100, 2),
            'porcentaje_atencion': round((kpis['bienes_requieren_atencion'] / total) * 100, 2),
            'porcentaje_completitud': kpis['completitud_datos'],
        }