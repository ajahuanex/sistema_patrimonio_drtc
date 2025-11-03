from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.decorators.http import require_http_methods
from django.utils import timezone
import json
import logging

from apps.bienes.models import BienPatrimonial
from apps.catalogo.models import Catalogo
from apps.oficinas.models import Oficina
from .models import ConfiguracionFiltro, ReporteGenerado
from .forms import (
    FiltroAvanzadoForm, ConfiguracionFiltroForm, 
    CargarConfiguracionForm, GenerarReporteForm
)
from .utils import FiltroAvanzado, GeneradorEstadisticas, aplicar_filtros_desde_request

logger = logging.getLogger(__name__)


@login_required
def dashboard_reportes(request):
    """Vista principal del módulo de reportes"""
    
    # Estadísticas generales
    total_bienes = BienPatrimonial.objects.count()
    total_oficinas = Oficina.objects.filter(estado=True).count()
    
    # Configuraciones del usuario
    mis_configuraciones = ConfiguracionFiltro.obtener_por_usuario(request.user)[:5]
    configuraciones_publicas = ConfiguracionFiltro.obtener_publicas()[:5]
    
    # Reportes recientes
    reportes_recientes = ReporteGenerado.objects.filter(
        usuario=request.user
    ).order_by('-fecha_inicio')[:10]
    
    # Estadísticas rápidas
    generador = GeneradorEstadisticas()
    resumen = generador.generar_resumen_ejecutivo()
    alertas = generador.generar_alertas_mantenimiento()
    
    context = {
        'total_bienes': total_bienes,
        'total_oficinas': total_oficinas,
        'mis_configuraciones': mis_configuraciones,
        'configuraciones_publicas': configuraciones_publicas,
        'reportes_recientes': reportes_recientes,
        'resumen_ejecutivo': resumen,
        'alertas': alertas,
    }
    
    return render(request, 'reportes/dashboard.html', context)


@login_required
def filtros_avanzados(request):
    """Vista para configurar filtros avanzados"""
    
    form = FiltroAvanzadoForm(user=request.user)
    cargar_form = CargarConfiguracionForm(user=request.user)
    resultados = None
    estadisticas = None
    configuracion_guardada = None
    
    if request.method == 'POST':
        if 'aplicar_filtros' in request.POST:
            form = FiltroAvanzadoForm(request.POST, user=request.user)
            if form.is_valid():
                # Aplicar filtros
                filtro = FiltroAvanzado(parametros=form.cleaned_data)
                queryset = filtro.aplicar_filtros()
                
                # Paginación
                paginator = Paginator(queryset, 25)
                page_number = request.GET.get('page', 1)
                resultados = paginator.get_page(page_number)
                
                # Estadísticas
                estadisticas = filtro.obtener_estadisticas(queryset)
                
                # Guardar configuración si fue solicitado
                configuracion_guardada = form.guardar_configuracion_si_solicitado()
                if configuracion_guardada:
                    messages.success(
                        request, 
                        f'Configuración "{configuracion_guardada.nombre}" guardada exitosamente'
                    )
        
        elif 'cargar_configuracion' in request.POST:
            cargar_form = CargarConfiguracionForm(request.POST, user=request.user)
            if cargar_form.is_valid():
                configuracion = cargar_form.cleaned_data['configuracion']
                
                # Cargar datos en el formulario
                form = FiltroAvanzadoForm(
                    initial=configuracion.to_dict(),
                    user=request.user
                )
                
                # Incrementar contador de uso
                configuracion.incrementar_uso()
                
                messages.info(
                    request,
                    f'Configuración "{configuracion.nombre}" cargada'
                )
    
    context = {
        'form': form,
        'cargar_form': cargar_form,
        'resultados': resultados,
        'estadisticas': estadisticas,
        'configuracion_guardada': configuracion_guardada,
    }
    
    return render(request, 'reportes/filtros_avanzados.html', context)


@login_required
def configuraciones_filtros(request):
    """Vista para gestionar configuraciones de filtros"""
    
    # Obtener configuraciones del usuario
    mis_configuraciones = ConfiguracionFiltro.obtener_por_usuario(request.user)
    configuraciones_publicas = ConfiguracionFiltro.obtener_publicas().exclude(
        usuario=request.user
    )
    
    context = {
        'mis_configuraciones': mis_configuraciones,
        'configuraciones_publicas': configuraciones_publicas,
    }
    
    return render(request, 'reportes/configuraciones_filtros.html', context)


@login_required
def crear_configuracion_filtro(request):
    """Vista para crear una nueva configuración de filtro"""
    
    if request.method == 'POST':
        form = ConfiguracionFiltroForm(request.POST, user=request.user)
        if form.is_valid():
            configuracion = form.save()
            messages.success(
                request,
                f'Configuración "{configuracion.nombre}" creada exitosamente'
            )
            return redirect('reportes:configuraciones_filtros')
    else:
        form = ConfiguracionFiltroForm(user=request.user)
    
    context = {
        'form': form,
        'titulo': 'Crear Configuración de Filtro',
        'accion': 'Crear',
    }
    
    return render(request, 'reportes/form_configuracion.html', context)


@login_required
def editar_configuracion_filtro(request, pk):
    """Vista para editar una configuración de filtro"""
    
    configuracion = get_object_or_404(
        ConfiguracionFiltro,
        pk=pk,
        usuario=request.user
    )
    
    if request.method == 'POST':
        form = ConfiguracionFiltroForm(
            request.POST,
            instance=configuracion,
            user=request.user
        )
        if form.is_valid():
            configuracion = form.save()
            messages.success(
                request,
                f'Configuración "{configuracion.nombre}" actualizada exitosamente'
            )
            return redirect('reportes:configuraciones_filtros')
    else:
        form = ConfiguracionFiltroForm(instance=configuracion, user=request.user)
    
    context = {
        'form': form,
        'configuracion': configuracion,
        'titulo': 'Editar Configuración de Filtro',
        'accion': 'Actualizar',
    }
    
    return render(request, 'reportes/form_configuracion.html', context)


@login_required
def eliminar_configuracion_filtro(request, pk):
    """Vista para eliminar una configuración de filtro"""
    
    configuracion = get_object_or_404(
        ConfiguracionFiltro,
        pk=pk,
        usuario=request.user
    )
    
    if request.method == 'POST':
        nombre = configuracion.nombre
        configuracion.delete()
        messages.success(
            request,
            f'Configuración "{nombre}" eliminada exitosamente'
        )
        return redirect('reportes:configuraciones_filtros')
    
    context = {
        'configuracion': configuracion,
    }
    
    return render(request, 'reportes/confirmar_eliminar_configuracion.html', context)


@login_required
def vista_previa_filtros(request):
    """Vista AJAX para previsualizar resultados de filtros"""
    
    if request.method == 'POST':
        try:
            # Obtener parámetros del POST
            parametros = {}
            
            # Procesar parámetros del formulario
            for key, value in request.POST.items():
                if key.startswith('oficinas'):
                    parametros.setdefault('oficinas', []).append(value)
                elif key.startswith('estados_bien'):
                    parametros.setdefault('estados_bien', []).append(value)
                elif key in ['fecha_adquisicion_desde', 'fecha_adquisicion_hasta',
                           'fecha_registro_desde', 'fecha_registro_hasta']:
                    if value:
                        from datetime import datetime
                        parametros[key] = datetime.strptime(value, '%Y-%m-%d').date()
                elif key in ['valor_minimo', 'valor_maximo']:
                    if value:
                        parametros[key] = float(value)
                elif value and key not in ['csrfmiddlewaretoken']:
                    parametros[key] = value
            
            # Aplicar filtros
            filtro = FiltroAvanzado(parametros=parametros)
            queryset = filtro.aplicar_filtros()
            
            # Obtener estadísticas básicas
            total = queryset.count()
            por_estado = list(queryset.values('estado_bien').annotate(
                total=Count('id')
            ).order_by('estado_bien'))
            
            return JsonResponse({
                'success': True,
                'total_resultados': total,
                'estadisticas_estado': por_estado,
                'mensaje': f'Se encontraron {total} bienes que coinciden con los filtros'
            })
            
        except Exception as e:
            logger.error(f"Error en vista previa de filtros: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Error al procesar los filtros'
            })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


@login_required
def generar_reporte(request):
    """Vista para generar reportes con filtros aplicados"""
    
    form = GenerarReporteForm()
    
    if request.method == 'POST':
        form = GenerarReporteForm(request.POST)
        if form.is_valid():
            # Obtener parámetros de filtros de la sesión o request
            parametros_filtros = request.session.get('filtros_aplicados', {})
            
            # Crear registro de reporte
            reporte = ReporteGenerado.objects.create(
                nombre=form.cleaned_data['nombre_reporte'],
                tipo_reporte=form.cleaned_data['tipo_reporte'],
                formato=form.cleaned_data['formato'],
                usuario=request.user,
                parametros={
                    'filtros': parametros_filtros,
                    'incluir_graficos': form.cleaned_data.get('incluir_graficos', False),
                    'incluir_historial': form.cleaned_data.get('incluir_historial', False),
                    'agrupar_por': form.cleaned_data.get('agrupar_por', ''),
                }
            )
            
            # Programar tarea asíncrona para generar el reporte
            from .tasks import generar_reporte_async
            generar_reporte_async.delay(reporte.id)
            
            messages.success(
                request,
                f'Reporte "{reporte.nombre}" programado para generación. '
                'Recibirá una notificación cuando esté listo.'
            )
            
            return redirect('reportes:mis_reportes')
    
    context = {
        'form': form,
    }
    
    return render(request, 'reportes/generar_reporte.html', context)


@login_required
def mis_reportes(request):
    """Vista para mostrar los reportes del usuario"""
    
    reportes = ReporteGenerado.objects.filter(
        usuario=request.user
    ).order_by('-fecha_inicio')
    
    # Paginación
    paginator = Paginator(reportes, 20)
    page_number = request.GET.get('page')
    reportes_paginados = paginator.get_page(page_number)
    
    context = {
        'reportes': reportes_paginados,
    }
    
    return render(request, 'reportes/mis_reportes.html', context)


@login_required
def descargar_reporte(request, pk):
    """Vista para descargar un reporte generado"""
    
    reporte = get_object_or_404(
        ReporteGenerado,
        pk=pk,
        usuario=request.user
    )
    
    if not reporte.puede_descargarse():
        messages.error(
            request,
            'El reporte no está disponible para descarga o ha expirado'
        )
        return redirect('reportes:mis_reportes')
    
    try:
        response = HttpResponse(
            reporte.archivo_generado.read(),
            content_type='application/octet-stream'
        )
        
        # Determinar nombre del archivo
        extension = {
            'EXCEL': '.xlsx',
            'PDF': '.pdf',
            'CSV': '.csv',
            'ZPL': '.zpl'
        }.get(reporte.formato, '.txt')
        
        filename = f"{reporte.nombre}_{reporte.fecha_inicio.strftime('%Y%m%d_%H%M')}{extension}"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        logger.error(f"Error al descargar reporte {pk}: {str(e)}")
        messages.error(request, 'Error al descargar el reporte')
        return redirect('reportes:mis_reportes')


@login_required
def eliminar_reporte(request, pk):
    """Vista para eliminar un reporte generado"""
    
    reporte = get_object_or_404(
        ReporteGenerado,
        pk=pk,
        usuario=request.user
    )
    
    if request.method == 'POST':
        nombre = reporte.nombre
        
        # Eliminar archivo físico si existe
        if reporte.archivo_generado:
            try:
                reporte.archivo_generado.delete()
            except Exception as e:
                logger.warning(f"No se pudo eliminar archivo de reporte {pk}: {str(e)}")
        
        reporte.delete()
        
        messages.success(
            request,
            f'Reporte "{nombre}" eliminado exitosamente'
        )
        
        return redirect('reportes:mis_reportes')
    
    context = {
        'reporte': reporte,
    }
    
    return render(request, 'reportes/confirmar_eliminar_reporte.html', context)


# APIs AJAX para autocompletado y datos dinámicos

@login_required
@require_http_methods(["GET"])
def api_marcas_autocomplete(request):
    """API para autocompletado de marcas"""
    
    termino = request.GET.get('q', '').strip()
    if len(termino) < 2:
        return JsonResponse({'results': []})
    
    marcas = BienPatrimonial.objects.filter(
        marca__icontains=termino
    ).exclude(
        marca=''
    ).values_list('marca', flat=True).distinct()[:10]
    
    results = [{'id': marca, 'text': marca} for marca in marcas]
    
    return JsonResponse({'results': results})


@login_required
@require_http_methods(["GET"])
def api_modelos_autocomplete(request):
    """API para autocompletado de modelos"""
    
    termino = request.GET.get('q', '').strip()
    marca = request.GET.get('marca', '').strip()
    
    if len(termino) < 2:
        return JsonResponse({'results': []})
    
    queryset = BienPatrimonial.objects.filter(
        modelo__icontains=termino
    ).exclude(modelo='')
    
    if marca:
        queryset = queryset.filter(marca__icontains=marca)
    
    modelos = queryset.values_list('modelo', flat=True).distinct()[:10]
    results = [{'id': modelo, 'text': modelo} for modelo in modelos]
    
    return JsonResponse({'results': results})


@login_required
@require_http_methods(["GET"])
def api_clases_por_grupo(request):
    """API para obtener clases de catálogo por grupo"""
    
    grupo = request.GET.get('grupo', '').strip()
    if not grupo:
        return JsonResponse({'clases': []})
    
    clases = Catalogo.obtener_clases_por_grupo(grupo)
    results = [{'value': clase, 'text': clase} for clase in clases]
    
    return JsonResponse({'clases': results})


@login_required
@require_http_methods(["GET"])
def api_estadisticas_filtros(request):
    """API para obtener estadísticas en tiempo real de filtros"""
    
    try:
        # Aplicar filtros desde request
        queryset = aplicar_filtros_desde_request(request)
        
        # Generar estadísticas
        filtro = FiltroAvanzado()
        estadisticas = filtro.obtener_estadisticas(queryset)
        
        return JsonResponse({
            'success': True,
            'estadisticas': estadisticas
        })
        
    except Exception as e:
        logger.error(f"Error en API estadísticas: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Error al obtener estadísticas'
        })


@login_required
def exportar_filtros_excel(request):
    """Vista para exportar resultados de filtros a Excel"""
    
    try:
        # Aplicar filtros
        queryset = aplicar_filtros_desde_request(request)
        
        # Generar Excel
        from .exportadores import ExportadorExcel
        exportador = ExportadorExcel()
        archivo = exportador.exportar_bienes(queryset)
        
        response = HttpResponse(
            archivo,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        filename = f"inventario_filtrado_{timezone.now().strftime('%Y%m%d_%H%M')}.xlsx"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        logger.error(f"Error al exportar Excel: {str(e)}")
        messages.error(request, 'Error al generar el archivo Excel')
        return redirect('reportes:filtros_avanzados')


@login_required
def limpiar_reportes_expirados(request):
    """Vista para limpiar reportes expirados (solo administradores)"""
    
    if not request.user.is_staff:
        messages.error(request, 'No tiene permisos para realizar esta acción')
        return redirect('reportes:dashboard_reportes')
    
    try:
        cantidad = ReporteGenerado.limpiar_expirados()
        messages.success(
            request,
            f'Se limpiaron {cantidad} reportes expirados'
        )
    except Exception as e:
        logger.error(f"Error al limpiar reportes: {str(e)}")
        messages.error(request, 'Error al limpiar reportes expirados')
    
    return redirect('reportes:dashboard_reportes')
# Vistas a
dicionales para generación de stickers ZPL

@login_required
def configurar_stickers(request):
    """Vista para configurar plantillas de stickers ZPL"""
    from .zpl_utils import ConfiguracionSticker, generar_plantilla_configuracion
    
    configuracion_inicial = generar_plantilla_configuracion()
    
    if request.method == 'POST':
        # Procesar configuración personalizada
        configuracion_datos = {}
        
        # Obtener parámetros del formulario
        configuracion_datos['tamaño'] = request.POST.get('tamaño', 'mediano')
        configuracion_datos['incluir_qr'] = request.POST.get('incluir_qr') == 'on'
        configuracion_datos['posicion_qr'] = request.POST.get('posicion_qr', 'izquierda')
        configuracion_datos['incluir_borde'] = request.POST.get('incluir_borde') == 'on'
        configuracion_datos['incluir_fecha'] = request.POST.get('incluir_fecha') == 'on'
        
        # Campos a incluir
        campos_incluir = request.POST.getlist('campos_incluir')
        configuracion_datos['campos_incluir'] = campos_incluir
        
        # Configuración personalizada de tamaño
        if configuracion_datos['tamaño'] == 'personalizado':
            try:
                configuracion_datos['ancho'] = int(request.POST.get('ancho_personalizado', 400))
                configuracion_datos['alto'] = int(request.POST.get('alto_personalizado', 300))
            except ValueError:
                messages.error(request, 'Dimensiones personalizadas inválidas')
                return redirect('reportes:configurar_stickers')
        
        # Guardar configuración en sesión
        request.session['configuracion_stickers'] = configuracion_datos
        
        messages.success(request, 'Configuración de stickers guardada')
        return redirect('reportes:generar_stickers')
    
    # Obtener configuración de la sesión si existe
    configuracion_guardada = request.session.get('configuracion_stickers', configuracion_inicial)
    
    context = {
        'configuracion': configuracion_guardada,
        'tamaños_predefinidos': ConfiguracionSticker.TAMAÑOS_PREDEFINIDOS,
        'campos_disponibles': [
            ('codigo_patrimonial', 'Código Patrimonial'),
            ('denominacion', 'Denominación'),
            ('oficina', 'Oficina'),
            ('estado', 'Estado'),
            ('marca_modelo', 'Marca/Modelo'),
            ('serie', 'Serie'),
            ('placa', 'Placa'),
        ],
        'posiciones_qr': [
            ('izquierda', 'Izquierda'),
            ('derecha', 'Derecha'),
            ('arriba', 'Arriba'),
            ('abajo', 'Abajo'),
        ]
    }
    
    return render(request, 'reportes/configurar_stickers.html', context)


@login_required
def generar_stickers(request):
    """Vista para generar stickers ZPL"""
    from .zpl_utils import ConfiguracionSticker, GeneradorZPL
    
    # Obtener configuración de la sesión
    config_datos = request.session.get('configuracion_stickers', {})
    
    if request.method == 'POST':
        # Obtener bienes seleccionados
        bienes_ids = request.POST.getlist('bienes_seleccionados')
        
        if not bienes_ids:
            messages.error(request, 'Debe seleccionar al menos un bien')
            return redirect('reportes:generar_stickers')
        
        try:
            # Crear configuración
            configuracion = ConfiguracionSticker(**config_datos)
            
            # Validar configuración
            errores = configuracion.validar()
            if errores:
                for error in errores:
                    messages.error(request, error)
                return redirect('reportes:configurar_stickers')
            
            # Obtener bienes
            queryset = BienPatrimonial.objects.filter(id__in=bienes_ids)
            
            # Generar ZPL
            generador = GeneradorZPL(configuracion)
            
            # Crear archivo temporal
            import tempfile
            archivo_temp = tempfile.NamedTemporaryFile(
                suffix='.zpl',
                delete=False,
                prefix=f'stickers_{timezone.now().strftime("%Y%m%d_%H%M%S")}_'
            )
            archivo_temp.close()
            
            # Generar stickers
            generador.generar_stickers_masivos(queryset, archivo_temp.name)
            
            # Crear registro de reporte
            reporte = ReporteGenerado.objects.create(
                nombre=f"Stickers ZPL - {queryset.count()} bienes",
                tipo_reporte='STICKERS',
                formato='ZPL',
                usuario=request.user,
                total_registros=queryset.count(),
                parametros={
                    'configuracion_stickers': config_datos,
                    'bienes_ids': bienes_ids
                }
            )
            
            # Guardar archivo
            with open(archivo_temp.name, 'rb') as f:
                reporte.archivo_generado.save(
                    f'stickers_{reporte.id}.zpl',
                    File(f),
                    save=False
                )
            
            reporte.marcar_completado()
            
            # Limpiar archivo temporal
            try:
                os.remove(archivo_temp.name)
            except OSError:
                pass
            
            messages.success(
                request,
                f'Plantilla ZPL generada exitosamente para {queryset.count()} bienes'
            )
            
            return redirect('reportes:descargar_reporte', pk=reporte.pk)
            
        except Exception as e:
            logger.error(f"Error generando stickers ZPL: {str(e)}")
            messages.error(request, f'Error generando stickers: {str(e)}')
            return redirect('reportes:generar_stickers')
    
    # Obtener bienes para selección
    # Aplicar filtros si existen
    queryset = aplicar_filtros_desde_request(request)
    
    # Paginación
    paginator = Paginator(queryset, 50)
    page_number = request.GET.get('page')
    bienes = paginator.get_page(page_number)
    
    context = {
        'bienes': bienes,
        'configuracion': config_datos,
        'total_bienes': queryset.count(),
    }
    
    return render(request, 'reportes/generar_stickers.html', context)


@login_required
def vista_previa_sticker(request, bien_id):
    """Vista previa de un sticker individual"""
    from .zpl_utils import ConfiguracionSticker, GeneradorZPL, ValidadorZPL
    
    bien = get_object_or_404(BienPatrimonial, id=bien_id)
    
    # Obtener configuración de la sesión
    config_datos = request.session.get('configuracion_stickers', {})
    
    try:
        # Crear configuración y generador
        configuracion = ConfiguracionSticker(**config_datos)
        generador = GeneradorZPL(configuracion)
        
        # Generar código ZPL
        codigo_zpl = generador.generar_sticker_bien(bien)
        
        # Validar código
        es_valido, errores = ValidadorZPL.validar_codigo(codigo_zpl)
        
        # Estimar tamaño
        dimensiones = ValidadorZPL.estimar_tamaño_impresion(codigo_zpl)
        
        context = {
            'bien': bien,
            'codigo_zpl': codigo_zpl,
            'es_valido': es_valido,
            'errores': errores,
            'dimensiones': dimensiones,
            'configuracion': config_datos,
        }
        
        return render(request, 'reportes/vista_previa_sticker.html', context)
        
    except Exception as e:
        logger.error(f"Error en vista previa de sticker: {str(e)}")
        messages.error(request, f'Error generando vista previa: {str(e)}')
        return redirect('reportes:configurar_stickers')


@login_required
def descargar_sticker_individual(request, bien_id):
    """Descarga sticker individual en formato ZPL"""
    from .zpl_utils import ConfiguracionSticker, GeneradorZPL
    
    bien = get_object_or_404(BienPatrimonial, id=bien_id)
    
    # Obtener configuración
    config_datos = request.session.get('configuracion_stickers', {})
    
    try:
        configuracion = ConfiguracionSticker(**config_datos)
        generador = GeneradorZPL(configuracion)
        
        # Generar código ZPL
        codigo_zpl = generador.generar_sticker_bien(bien)
        
        # Crear respuesta HTTP
        response = HttpResponse(codigo_zpl, content_type='text/plain')
        filename = f"sticker_{bien.codigo_patrimonial}_{timezone.now().strftime('%Y%m%d_%H%M')}.zpl"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        logger.error(f"Error descargando sticker individual: {str(e)}")
        messages.error(request, f'Error generando sticker: {str(e)}')
        return redirect('reportes:vista_previa_sticker', bien_id=bien_id)


@login_required
def plantillas_stickers_predefinidas(request):
    """Vista para gestionar plantillas predefinidas de stickers"""
    from .zpl_utils import ConfiguracionSticker
    
    plantillas = {
        'basico': {
            'nombre': 'Básico',
            'descripcion': 'Sticker básico con código patrimonial y QR',
            'configuracion': {
                'tamaño': 'pequeño',
                'campos_incluir': ['codigo_patrimonial'],
                'incluir_qr': True,
                'posicion_qr': 'izquierda'
            }
        },
        'completo': {
            'nombre': 'Completo',
            'descripcion': 'Sticker con toda la información disponible',
            'configuracion': {
                'tamaño': 'grande',
                'campos_incluir': [
                    'codigo_patrimonial', 'denominacion', 'oficina', 
                    'estado', 'marca_modelo', 'serie'
                ],
                'incluir_qr': True,
                'posicion_qr': 'izquierda'
            }
        },
        'vehiculos': {
            'nombre': 'Vehículos',
            'descripción': 'Especializado para vehículos con placa',
            'configuracion': {
                'tamaño': 'mediano',
                'campos_incluir': [
                    'codigo_patrimonial', 'denominacion', 'placa', 
                    'marca_modelo', 'estado'
                ],
                'incluir_qr': True,
                'posicion_qr': 'derecha'
            }
        },
        'inventario': {
            'nombre': 'Inventario',
            'descripcion': 'Para inventarios rápidos',
            'configuracion': {
                'tamaño': 'mediano',
                'campos_incluir': ['codigo_patrimonial', 'oficina', 'estado'],
                'incluir_qr': True,
                'posicion_qr': 'arriba'
            }
        }
    }
    
    if request.method == 'POST':
        plantilla_seleccionada = request.POST.get('plantilla')
        
        if plantilla_seleccionada in plantillas:
            # Guardar configuración en sesión
            request.session['configuracion_stickers'] = plantillas[plantilla_seleccionada]['configuracion']
            
            messages.success(
                request,
                f'Plantilla "{plantillas[plantilla_seleccionada]["nombre"]}" aplicada'
            )
            
            return redirect('reportes:generar_stickers')
        else:
            messages.error(request, 'Plantilla no válida')
    
    context = {
        'plantillas': plantillas,
        'tamaños_info': ConfiguracionSticker.TAMAÑOS_PREDEFINIDOS,
    }
    
    return render(request, 'reportes/plantillas_stickers.html', context)


@login_required
@require_http_methods(["POST"])
def api_validar_configuracion_sticker(request):
    """API para validar configuración de sticker"""
    from .zpl_utils import ConfiguracionSticker
    
    try:
        # Obtener datos de configuración
        config_datos = json.loads(request.body)
        
        # Crear configuración
        configuracion = ConfiguracionSticker(**config_datos)
        
        # Validar
        errores = configuracion.validar()
        
        # Calcular área de texto
        area_texto = configuracion.calcular_area_texto()
        
        return JsonResponse({
            'success': True,
            'es_valida': len(errores) == 0,
            'errores': errores,
            'area_texto': area_texto,
            'dimensiones': {
                'ancho': configuracion.ancho,
                'alto': configuracion.alto,
                'ancho_pulgadas': round(configuracion.ancho / 203, 2),
                'alto_pulgadas': round(configuracion.alto / 203, 2),
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def tutorial_stickers_zpl(request):
    """Vista con tutorial para usar stickers ZPL"""
    
    context = {
        'impresoras_compatibles': [
            'Zebra ZD410',
            'Zebra ZD420',
            'Zebra ZD620',
            'Zebra GK420d',
            'Zebra GX420d',
            'Zebra ZT410',
            'Zebra ZT420',
        ],
        'software_recomendado': [
            'ZebraDesigner',
            'Zebra Setup Utilities',
            'PrintNode',
            'BarTender',
        ]
    }
    
    return render(request, 'reportes/tutorial_stickers.html', context)
# V
istas adicionales para exportación en múltiples formatos

@login_required
def centro_exportacion(request):
    """Centro unificado de exportación en múltiples formatos"""
    from .export_manager import ExportManager
    
    export_manager = ExportManager()
    
    context = {
        'formatos_disponibles': export_manager.FORMATOS_DISPONIBLES,
        'tipos_reporte': export_manager.TIPOS_REPORTE,
    }
    
    return render(request, 'reportes/centro_exportacion.html', context)


@login_required
def exportacion_rapida(request):
    """Vista para exportación rápida con filtros aplicados"""
    from .export_manager import ExportManager
    
    if request.method == 'POST':
        try:
            # Obtener parámetros
            tipo_reporte = request.POST.get('tipo_reporte', 'INVENTARIO')
            formato = request.POST.get('formato', 'EXCEL')
            
            # Aplicar filtros
            queryset = aplicar_filtros_desde_request(request)
            
            # Validar exportación
            export_manager = ExportManager()
            es_valida, mensaje = export_manager.validar_exportacion(tipo_reporte, formato, queryset)
            
            if not es_valida:
                messages.error(request, mensaje)
                return redirect('reportes:centro_exportacion')
            
            # Generar exportación
            parametros = {
                'incluir_graficos': request.POST.get('incluir_graficos') == 'on',
                'incluir_historial': request.POST.get('incluir_historial') == 'on',
                'agrupar_por': request.POST.get('agrupar_por', ''),
            }
            
            resultado = export_manager.exportar(
                queryset=queryset,
                tipo_reporte=tipo_reporte,
                formato=formato,
                parametros=parametros,
                usuario=request.user
            )
            
            # Crear registro de reporte
            reporte = ReporteGenerado.objects.create(
                nombre=f"Exportación Rápida - {tipo_reporte}",
                tipo_reporte=tipo_reporte,
                formato=formato,
                usuario=request.user,
                total_registros=resultado['total_registros'],
                parametros=parametros
            )
            
            # Guardar archivo
            with open(resultado['archivo_path'], 'rb') as f:
                reporte.archivo_generado.save(
                    resultado['nombre_archivo'],
                    File(f),
                    save=False
                )
            
            reporte.marcar_completado()
            
            # Limpiar archivo temporal
            export_manager.limpiar_archivos_temporales()
            
            messages.success(
                request,
                f'Exportación completada: {resultado["total_registros"]} registros'
            )
            
            return redirect('reportes:descargar_reporte', pk=reporte.pk)
            
        except Exception as e:
            logger.error(f"Error en exportación rápida: {str(e)}")
            messages.error(request, f'Error en la exportación: {str(e)}')
            return redirect('reportes:centro_exportacion')
    
    # GET request - mostrar formulario
    from .export_manager import ExportManager
    export_manager = ExportManager()
    
    # Aplicar filtros actuales para mostrar preview
    queryset = aplicar_filtros_desde_request(request)
    
    context = {
        'formatos_disponibles': export_manager.FORMATOS_DISPONIBLES,
        'tipos_reporte': export_manager.TIPOS_REPORTE,
        'total_registros': queryset.count(),
        'filtros_aplicados': bool(request.GET),
    }
    
    return render(request, 'reportes/exportacion_rapida.html', context)


@login_required
def exportacion_masiva(request):
    """Vista para exportación masiva en múltiples formatos"""
    from .export_manager import ExportManager, BatchExportManager
    
    if request.method == 'POST':
        try:
            # Obtener configuraciones de exportación
            configuraciones = []
            
            # Procesar formulario de exportación masiva
            tipos_reporte = request.POST.getlist('tipos_reporte')
            formatos = request.POST.getlist('formatos')
            
            if not tipos_reporte or not formatos:
                messages.error(request, 'Debe seleccionar al menos un tipo de reporte y formato')
                return redirect('reportes:exportacion_masiva')
            
            # Aplicar filtros base
            queryset_base = aplicar_filtros_desde_request(request)
            
            # Crear configuraciones para cada combinación
            for tipo_reporte in tipos_reporte:
                for formato in formatos:
                    # Validar combinación
                    export_manager = ExportManager()
                    es_valida, _ = export_manager.validar_exportacion(tipo_reporte, formato, queryset_base)
                    
                    if es_valida:
                        configuraciones.append({
                            'queryset': queryset_base,
                            'tipo_reporte': tipo_reporte,
                            'formato': formato,
                            'parametros': {
                                'incluir_graficos': request.POST.get('incluir_graficos') == 'on',
                                'incluir_historial': request.POST.get('incluir_historial') == 'on',
                                'masivo': True
                            }
                        })
            
            if not configuraciones:
                messages.error(request, 'No hay combinaciones válidas para exportar')
                return redirect('reportes:exportacion_masiva')
            
            # Ejecutar exportación masiva
            batch_manager = BatchExportManager()
            resultados = batch_manager.exportar_por_lotes(configuraciones, request.user)
            
            # Crear reportes individuales
            reportes_creados = []
            archivos_exitosos = []
            
            for resultado in resultados:
                if resultado['estado'] == 'EXITOSO':
                    reporte = ReporteGenerado.objects.create(
                        nombre=f"Masivo {resultado['lote_indice']}/{resultado['lote_total']} - {resultado['tipo_reporte']}",
                        tipo_reporte=resultado['tipo_reporte'],
                        formato=resultado['formato'],
                        usuario=request.user,
                        total_registros=resultado['total_registros'],
                        parametros=resultado['parametros']
                    )
                    
                    # Guardar archivo
                    with open(resultado['archivo_path'], 'rb') as f:
                        reporte.archivo_generado.save(
                            resultado['nombre_archivo'],
                            File(f),
                            save=False
                        )
                    
                    reporte.marcar_completado()
                    reportes_creados.append(reporte)
                    archivos_exitosos.append(resultado['archivo_path'])
            
            # Crear ZIP con todos los archivos
            if len(archivos_exitosos) > 1:
                archivo_zip = batch_manager.crear_zip_exportaciones(archivos_exitosos)
                
                # Crear reporte para el ZIP
                reporte_zip = ReporteGenerado.objects.create(
                    nombre=f"Exportación Masiva - {len(archivos_exitosos)} archivos",
                    tipo_reporte='PERSONALIZADO',
                    formato='ZIP',
                    usuario=request.user,
                    total_registros=queryset_base.count(),
                    parametros={'archivos_incluidos': len(archivos_exitosos)}
                )
                
                with open(archivo_zip, 'rb') as f:
                    reporte_zip.archivo_generado.save(
                        f'exportacion_masiva_{timezone.now().strftime("%Y%m%d_%H%M")}.zip',
                        File(f),
                        save=False
                    )
                
                reporte_zip.marcar_completado()
                
                # Limpiar archivo temporal
                try:
                    os.remove(archivo_zip)
                except OSError:
                    pass
            
            # Limpiar archivos temporales
            batch_manager.export_manager.limpiar_archivos_temporales()
            
            messages.success(
                request,
                f'Exportación masiva completada: {len(reportes_creados)} archivos generados'
            )
            
            return redirect('reportes:mis_reportes')
            
        except Exception as e:
            logger.error(f"Error en exportación masiva: {str(e)}")
            messages.error(request, f'Error en la exportación masiva: {str(e)}')
            return redirect('reportes:exportacion_masiva')
    
    # GET request
    from .export_manager import ExportManager
    export_manager = ExportManager()
    
    queryset = aplicar_filtros_desde_request(request)
    
    context = {
        'formatos_disponibles': export_manager.FORMATOS_DISPONIBLES,
        'tipos_reporte': export_manager.TIPOS_REPORTE,
        'total_registros': queryset.count(),
        'filtros_aplicados': bool(request.GET),
    }
    
    return render(request, 'reportes/exportacion_masiva.html', context)


@login_required
@require_http_methods(["POST"])
def api_validar_exportacion(request):
    """API para validar una exportación antes de ejecutarla"""
    from .export_manager import ExportManager
    
    try:
        data = json.loads(request.body)
        tipo_reporte = data.get('tipo_reporte')
        formato = data.get('formato')
        
        # Aplicar filtros si se proporcionan
        if 'filtros' in data:
            # Simular request con filtros
            from django.http import QueryDict
            query_dict = QueryDict('', mutable=True)
            query_dict.update(data['filtros'])
            
            # Crear request simulado
            class MockRequest:
                def __init__(self, get_data):
                    self.GET = get_data
            
            mock_request = MockRequest(query_dict)
            queryset = aplicar_filtros_desde_request(mock_request)
        else:
            queryset = BienPatrimonial.objects.all()
        
        export_manager = ExportManager()
        es_valida, mensaje = export_manager.validar_exportacion(tipo_reporte, formato, queryset)
        
        tiempo_estimado = export_manager.estimar_tiempo_exportacion(
            tipo_reporte, formato, queryset.count()
        )
        
        return JsonResponse({
            'success': True,
            'es_valida': es_valida,
            'mensaje': mensaje,
            'total_registros': queryset.count(),
            'tiempo_estimado_segundos': tiempo_estimado,
            'tiempo_estimado_texto': f"{tiempo_estimado // 60}m {tiempo_estimado % 60}s" if tiempo_estimado >= 60 else f"{tiempo_estimado}s"
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_http_methods(["GET"])
def api_formatos_por_tipo(request):
    """API para obtener formatos disponibles por tipo de reporte"""
    from .export_manager import ExportManager
    
    tipo_reporte = request.GET.get('tipo_reporte')
    
    export_manager = ExportManager()
    formatos = export_manager.obtener_formatos_disponibles(tipo_reporte)
    
    return JsonResponse({
        'success': True,
        'formatos': formatos
    })


@login_required
def historial_exportaciones(request):
    """Vista del historial de exportaciones del usuario"""
    
    # Filtros
    tipo_reporte = request.GET.get('tipo_reporte')
    formato = request.GET.get('formato')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    # Query base
    reportes = ReporteGenerado.objects.filter(usuario=request.user)
    
    # Aplicar filtros
    if tipo_reporte:
        reportes = reportes.filter(tipo_reporte=tipo_reporte)
    
    if formato:
        reportes = reportes.filter(formato=formato)
    
    if fecha_desde:
        try:
            from datetime import datetime
            fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d')
            reportes = reportes.filter(fecha_inicio__gte=fecha_desde_dt)
        except ValueError:
            pass
    
    if fecha_hasta:
        try:
            from datetime import datetime
            fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d')
            reportes = reportes.filter(fecha_inicio__lte=fecha_hasta_dt)
        except ValueError:
            pass
    
    # Ordenar por fecha más reciente
    reportes = reportes.order_by('-fecha_inicio')
    
    # Paginación
    paginator = Paginator(reportes, 20)
    page_number = request.GET.get('page')
    reportes_paginados = paginator.get_page(page_number)
    
    # Estadísticas
    from .export_manager import ExportManager
    export_manager = ExportManager()
    
    estadisticas = {
        'total_exportaciones': ReporteGenerado.objects.filter(usuario=request.user).count(),
        'exportaciones_mes': ReporteGenerado.objects.filter(
            usuario=request.user,
            fecha_inicio__gte=timezone.now().replace(day=1)
        ).count(),
        'formatos_mas_usados': list(ReporteGenerado.objects.filter(
            usuario=request.user
        ).values('formato').annotate(
            total=Count('id')
        ).order_by('-total')[:5]),
        'tipos_mas_usados': list(ReporteGenerado.objects.filter(
            usuario=request.user
        ).values('tipo_reporte').annotate(
            total=Count('id')
        ).order_by('-total')[:5])
    }
    
    context = {
        'reportes': reportes_paginados,
        'estadisticas': estadisticas,
        'formatos_disponibles': export_manager.FORMATOS_DISPONIBLES,
        'tipos_reporte': export_manager.TIPOS_REPORTE,
        'filtros_aplicados': {
            'tipo_reporte': tipo_reporte,
            'formato': formato,
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
        }
    }
    
    return render(request, 'reportes/historial_exportaciones.html', context)


@login_required
def comparar_formatos(request):
    """Vista para comparar diferentes formatos de exportación"""
    from .export_manager import ExportManager
    
    # Aplicar filtros actuales
    queryset = aplicar_filtros_desde_request(request)
    total_registros = queryset.count()
    
    export_manager = ExportManager()
    
    # Generar comparación para cada formato
    comparaciones = {}
    
    for formato, info in export_manager.FORMATOS_DISPONIBLES.items():
        # Verificar qué tipos de reporte soportan este formato
        tipos_soportados = []
        for tipo, tipo_info in export_manager.TIPOS_REPORTE.items():
            if formato in tipo_info['formatos_soportados']:
                tipos_soportados.append({
                    'tipo': tipo,
                    'nombre': tipo_info['nombre'],
                    'tiempo_estimado': export_manager.estimar_tiempo_exportacion(tipo, formato, total_registros)
                })
        
        comparaciones[formato] = {
            'info': info,
            'tipos_soportados': tipos_soportados,
            'ventajas': _obtener_ventajas_formato(formato),
            'desventajas': _obtener_desventajas_formato(formato),
            'casos_uso': _obtener_casos_uso_formato(formato)
        }
    
    context = {
        'comparaciones': comparaciones,
        'total_registros': total_registros,
        'filtros_aplicados': bool(request.GET)
    }
    
    return render(request, 'reportes/comparar_formatos.html', context)


def _obtener_ventajas_formato(formato):
    """Obtiene las ventajas de un formato específico"""
    ventajas = {
        'EXCEL': [
            'Permite análisis y manipulación de datos',
            'Soporta fórmulas y gráficos',
            'Ampliamente compatible',
            'Permite filtros y ordenamiento'
        ],
        'PDF': [
            'Formato fijo, ideal para reportes oficiales',
            'Incluye gráficos y formato visual',
            'No se puede modificar accidentalmente',
            'Perfecto para impresión'
        ],
        'CSV': [
            'Formato ligero y rápido',
            'Compatible con cualquier sistema',
            'Ideal para importación a otras bases de datos',
            'Fácil de procesar programáticamente'
        ],
        'ZPL': [
            'Diseñado específicamente para impresoras Zebra',
            'Optimizado para etiquetas y stickers',
            'Control preciso del diseño',
            'Impresión rápida y eficiente'
        ]
    }
    return ventajas.get(formato, [])


def _obtener_desventajas_formato(formato):
    """Obtiene las desventajas de un formato específico"""
    desventajas = {
        'EXCEL': [
            'Archivos más pesados',
            'Requiere software específico para editar',
            'Puede ser lento con muchos datos'
        ],
        'PDF': [
            'No se puede editar fácilmente',
            'Archivos pueden ser pesados con gráficos',
            'Menos útil para análisis de datos'
        ],
        'CSV': [
            'No soporta formato visual',
            'Sin gráficos ni imágenes',
            'Puede perder información de tipos de datos'
        ],
        'ZPL': [
            'Solo útil para impresoras Zebra',
            'Requiere conocimiento técnico',
            'No es legible por humanos'
        ]
    }
    return desventajas.get(formato, [])


def _obtener_casos_uso_formato(formato):
    """Obtiene los casos de uso típicos de un formato"""
    casos_uso = {
        'EXCEL': [
            'Análisis de inventario',
            'Reportes para gerencia',
            'Manipulación de datos',
            'Creación de dashboards'
        ],
        'PDF': [
            'Reportes oficiales',
            'Documentos para archivo',
            'Presentaciones ejecutivas',
            'Reportes para auditoría'
        ],
        'CSV': [
            'Migración de datos',
            'Integración con otros sistemas',
            'Procesamiento automatizado',
            'Backup de datos'
        ],
        'ZPL': [
            'Etiquetas de inventario',
            'Stickers de identificación',
            'Códigos de barras',
            'Etiquetas de activos'
        ]
    }
    return casos_uso.get(formato, [])