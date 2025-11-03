import os
import tempfile
from datetime import datetime, timedelta
from django.conf import settings
from django.core.files import File
from django.utils import timezone
from celery import shared_task
from celery.utils.log import get_task_logger

from apps.bienes.models import BienPatrimonial
from .models import ReporteGenerado, ConfiguracionFiltro
from .utils import FiltroAvanzado
from .generadores import GeneradorReporteEstadistico, GeneradorReportePDF, GeneradorIndicadoresClave
from .exportadores import ExportadorExcel, ExportadorCSV

logger = get_task_logger(__name__)


@shared_task(bind=True)
def generar_reporte_async(self, reporte_id):
    """
    Tarea asíncrona para generar reportes
    
    Args:
        reporte_id: ID del ReporteGenerado
    """
    try:
        # Obtener el reporte
        reporte = ReporteGenerado.objects.get(id=reporte_id)
        logger.info(f"Iniciando generación de reporte {reporte_id}: {reporte.nombre}")
        
        # Aplicar filtros si existen
        queryset = BienPatrimonial.objects.all()
        parametros_filtros = reporte.parametros.get('filtros', {})
        
        if parametros_filtros:
            filtro = FiltroAvanzado(parametros=parametros_filtros)
            queryset = filtro.aplicar_filtros()
        
        # Actualizar total de registros
        reporte.total_registros = queryset.count()
        reporte.save()
        
        # Generar el reporte según el tipo y formato
        archivo_generado = None
        
        if reporte.tipo_reporte == 'INVENTARIO':
            archivo_generado = _generar_reporte_inventario(reporte, queryset)
        elif reporte.tipo_reporte == 'ESTADISTICO':
            archivo_generado = _generar_reporte_estadistico(reporte, queryset)
        elif reporte.tipo_reporte == 'EJECUTIVO':
            archivo_generado = _generar_reporte_ejecutivo(reporte, queryset)
        elif reporte.tipo_reporte == 'STICKERS':
            archivo_generado = _generar_plantilla_stickers(reporte, queryset)
        elif reporte.tipo_reporte == 'PERSONALIZADO':
            archivo_generado = _generar_reporte_personalizado(reporte, queryset)
        
        if archivo_generado:
            # Guardar archivo en el modelo
            with open(archivo_generado, 'rb') as f:
                reporte.archivo_generado.save(
                    os.path.basename(archivo_generado),
                    File(f),
                    save=False
                )
            
            # Establecer fecha de expiración (30 días)
            reporte.fecha_expiracion = timezone.now() + timedelta(days=30)
            
            # Marcar como completado
            reporte.marcar_completado()
            
            # Limpiar archivo temporal
            try:
                os.remove(archivo_generado)
            except OSError:
                pass
            
            logger.info(f"Reporte {reporte_id} generado exitosamente")
            
            # Enviar notificación al usuario (opcional)
            _enviar_notificacion_reporte_listo(reporte)
            
        else:
            raise Exception("No se pudo generar el archivo del reporte")
            
    except ReporteGenerado.DoesNotExist:
        logger.error(f"Reporte {reporte_id} no encontrado")
        raise
        
    except Exception as e:
        logger.error(f"Error generando reporte {reporte_id}: {str(e)}")
        
        try:
            reporte = ReporteGenerado.objects.get(id=reporte_id)
            reporte.marcar_error(str(e))
        except:
            pass
        
        raise


def _generar_reporte_inventario(reporte, queryset):
    """Genera reporte de inventario básico"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if reporte.formato == 'EXCEL':
        exportador = ExportadorExcel()
        archivo_temp = tempfile.NamedTemporaryFile(
            suffix='.xlsx', 
            delete=False,
            prefix=f'inventario_{timestamp}_'
        )
        archivo_temp.close()
        
        exportador.exportar_bienes(queryset, archivo_temp.name)
        return archivo_temp.name
        
    elif reporte.formato == 'CSV':
        exportador = ExportadorCSV()
        archivo_temp = tempfile.NamedTemporaryFile(
            suffix='.csv', 
            delete=False,
            prefix=f'inventario_{timestamp}_'
        )
        archivo_temp.close()
        
        exportador.exportar_bienes(queryset, archivo_temp.name)
        return archivo_temp.name
        
    elif reporte.formato == 'PDF':
        generador = GeneradorReportePDF(queryset, reporte.parametros)
        archivo_temp = tempfile.NamedTemporaryFile(
            suffix='.pdf', 
            delete=False,
            prefix=f'inventario_{timestamp}_'
        )
        archivo_temp.close()
        
        generador.generar_reporte_completo(archivo_temp.name)
        return archivo_temp.name
    
    return None


def _generar_reporte_estadistico(reporte, queryset):
    """Genera reporte estadístico con gráficos"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if reporte.formato == 'PDF':
        generador = GeneradorReportePDF(queryset, reporte.parametros)
        archivo_temp = tempfile.NamedTemporaryFile(
            suffix='.pdf', 
            delete=False,
            prefix=f'estadistico_{timestamp}_'
        )
        archivo_temp.close()
        
        generador.generar_reporte_completo(archivo_temp.name)
        return archivo_temp.name
        
    elif reporte.formato == 'EXCEL':
        # Generar Excel con estadísticas
        generador_stats = GeneradorReporteEstadistico(queryset, reporte.parametros)
        estadisticas = generador_stats.generar_estadisticas()
        
        exportador = ExportadorExcel()
        archivo_temp = tempfile.NamedTemporaryFile(
            suffix='.xlsx', 
            delete=False,
            prefix=f'estadistico_{timestamp}_'
        )
        archivo_temp.close()
        
        exportador.exportar_estadisticas(estadisticas, archivo_temp.name)
        return archivo_temp.name
    
    return None


def _generar_reporte_ejecutivo(reporte, queryset):
    """Genera reporte ejecutivo con KPIs"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Generar KPIs
    generador_kpis = GeneradorIndicadoresClave(queryset)
    kpis = generador_kpis.calcular_kpis()
    
    if reporte.formato == 'PDF':
        generador = GeneradorReportePDF(queryset, reporte.parametros)
        archivo_temp = tempfile.NamedTemporaryFile(
            suffix='.pdf', 
            delete=False,
            prefix=f'ejecutivo_{timestamp}_'
        )
        archivo_temp.close()
        
        # Agregar KPIs a los parámetros
        parametros_con_kpis = reporte.parametros.copy()
        parametros_con_kpis['kpis'] = kpis
        
        generador.parametros = parametros_con_kpis
        generador.generar_reporte_completo(archivo_temp.name)
        return archivo_temp.name
    
    return None


def _generar_plantilla_stickers(reporte, queryset):
    """Genera plantilla ZPL para stickers"""
    from .exportadores import ExportadorZPL
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    exportador = ExportadorZPL()
    archivo_temp = tempfile.NamedTemporaryFile(
        suffix='.zpl', 
        delete=False,
        prefix=f'stickers_{timestamp}_'
    )
    archivo_temp.close()
    
    exportador.generar_plantilla_stickers(queryset, archivo_temp.name)
    return archivo_temp.name


def _generar_reporte_personalizado(reporte, queryset):
    """Genera reporte personalizado según parámetros"""
    # Implementar lógica personalizada según los parámetros
    parametros = reporte.parametros
    
    # Por ahora, generar como inventario básico
    return _generar_reporte_inventario(reporte, queryset)


def _enviar_notificacion_reporte_listo(reporte):
    """Envía notificación al usuario cuando el reporte está listo"""
    try:
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        
        if not reporte.usuario.email:
            return
        
        asunto = f"Reporte '{reporte.nombre}' listo para descarga"
        
        mensaje = render_to_string('reportes/email_reporte_listo.html', {
            'reporte': reporte,
            'usuario': reporte.usuario,
        })
        
        send_mail(
            asunto,
            mensaje,
            settings.DEFAULT_FROM_EMAIL,
            [reporte.usuario.email],
            html_message=mensaje,
            fail_silently=True
        )
        
        logger.info(f"Notificación enviada a {reporte.usuario.email} para reporte {reporte.id}")
        
    except Exception as e:
        logger.warning(f"No se pudo enviar notificación para reporte {reporte.id}: {str(e)}")


@shared_task
def limpiar_reportes_expirados():
    """
    Tarea programada para limpiar reportes expirados
    """
    try:
        cantidad = ReporteGenerado.limpiar_expirados()
        logger.info(f"Se limpiaron {cantidad} reportes expirados")
        return cantidad
        
    except Exception as e:
        logger.error(f"Error limpiando reportes expirados: {str(e)}")
        raise


@shared_task
def generar_reporte_programado(configuracion_filtro_id, tipo_reporte, formato, usuario_id):
    """
    Tarea para generar reportes programados
    
    Args:
        configuracion_filtro_id: ID de la configuración de filtros
        tipo_reporte: Tipo de reporte a generar
        formato: Formato del reporte
        usuario_id: ID del usuario
    """
    try:
        from django.contrib.auth.models import User
        
        usuario = User.objects.get(id=usuario_id)
        configuracion = ConfiguracionFiltro.objects.get(id=configuracion_filtro_id)
        
        # Crear reporte programado
        reporte = ReporteGenerado.objects.create(
            nombre=f"Reporte Programado - {configuracion.nombre}",
            tipo_reporte=tipo_reporte,
            formato=formato,
            usuario=usuario,
            configuracion_filtro=configuracion,
            parametros={
                'filtros': configuracion.to_dict(),
                'programado': True,
                'fecha_programacion': timezone.now().isoformat()
            }
        )
        
        # Generar el reporte
        generar_reporte_async.delay(reporte.id)
        
        logger.info(f"Reporte programado {reporte.id} creado para usuario {usuario.username}")
        
        return reporte.id
        
    except Exception as e:
        logger.error(f"Error generando reporte programado: {str(e)}")
        raise


@shared_task
def actualizar_estadisticas_cache():
    """
    Tarea para actualizar estadísticas en caché
    """
    try:
        from django.core.cache import cache
        
        # Generar estadísticas generales
        generador_stats = GeneradorReporteEstadistico()
        estadisticas = generador_stats.generar_estadisticas()
        
        # Guardar en caché por 1 hora
        cache.set('estadisticas_generales', estadisticas, 3600)
        
        # Generar KPIs
        generador_kpis = GeneradorIndicadoresClave()
        kpis = generador_kpis.calcular_kpis()
        
        # Guardar KPIs en caché por 1 hora
        cache.set('kpis_generales', kpis, 3600)
        
        logger.info("Estadísticas y KPIs actualizados en caché")
        
        return {
            'estadisticas_actualizadas': True,
            'kpis_actualizados': True,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error actualizando estadísticas en caché: {str(e)}")
        raise


@shared_task
def generar_reporte_masivo(filtros_list, tipo_reporte, formato, usuario_id):
    """
    Tarea para generar múltiples reportes con diferentes filtros
    
    Args:
        filtros_list: Lista de configuraciones de filtros
        tipo_reporte: Tipo de reporte
        formato: Formato del reporte
        usuario_id: ID del usuario
    """
    try:
        from django.contrib.auth.models import User
        
        usuario = User.objects.get(id=usuario_id)
        reportes_generados = []
        
        for i, filtros in enumerate(filtros_list):
            # Crear reporte individual
            reporte = ReporteGenerado.objects.create(
                nombre=f"Reporte Masivo {i+1}",
                tipo_reporte=tipo_reporte,
                formato=formato,
                usuario=usuario,
                parametros={
                    'filtros': filtros,
                    'masivo': True,
                    'indice': i+1,
                    'total': len(filtros_list)
                }
            )
            
            # Generar el reporte
            generar_reporte_async.delay(reporte.id)
            reportes_generados.append(reporte.id)
        
        logger.info(f"Generación masiva iniciada: {len(reportes_generados)} reportes para usuario {usuario.username}")
        
        return {
            'reportes_generados': reportes_generados,
            'total': len(reportes_generados)
        }
        
    except Exception as e:
        logger.error(f"Error en generación masiva: {str(e)}")
        raise