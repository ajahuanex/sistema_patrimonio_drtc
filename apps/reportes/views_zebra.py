"""
Vistas específicas para configuración e impresión en impresoras Zebra
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from datetime import datetime
import json

from apps.bienes.models import BienPatrimonial
from .zpl_utils import ConfiguracionSticker, GeneradorZPL, ValidadorZPL


class ConfiguradorZebraView(LoginRequiredMixin, TemplateView):
    """Vista para configurar impresión en impresoras Zebra"""
    template_name = 'reportes/configurador_zebra.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Información de impresoras disponibles
        context['impresoras_zebra'] = ConfiguracionSticker.IMPRESORAS_ZEBRA
        context['tamaños_predefinidos'] = ConfiguracionSticker.TAMAÑOS_PREDEFINIDOS
        
        # Bien seleccionado (si viene por parámetro)
        bien_id = self.request.GET.get('bien_id')
        if bien_id:
            try:
                context['bien_seleccionado'] = BienPatrimonial.objects.get(id=bien_id)
            except BienPatrimonial.DoesNotExist:
                pass
        
        # Configuración por defecto
        context['config_defecto'] = {
            'impresora': 'ZD220',
            'dpi': 203,
            'tamaño': 'etiqueta_mediana_203',
            'incluir_qr': True,
            'posicion_qr': 'izquierda',
            'campos_incluir': ['codigo_patrimonial', 'denominacion', 'oficina', 'estado'],
            'bien_id': bien_id if bien_id else ''
        }
        
        return context


@login_required
@require_http_methods(["POST"])
def generar_preview_zebra(request):
    """Genera preview de ticket/etiqueta para impresora Zebra"""
    try:
        # Obtener parámetros
        impresora = request.POST.get('impresora', 'ZD220')
        dpi = int(request.POST.get('dpi', 203))
        tamaño = request.POST.get('tamaño', 'etiqueta_mediana_203')
        bien_id = request.POST.get('bien_id')
        
        # Configuración personalizada
        config_params = {
            'incluir_qr': request.POST.get('incluir_qr') == 'true',
            'posicion_qr': request.POST.get('posicion_qr', 'izquierda'),
            'incluir_fecha': request.POST.get('incluir_fecha') == 'true',
            'incluir_borde': request.POST.get('incluir_borde') == 'true',
            'campos_incluir': request.POST.getlist('campos_incluir[]')
        }
        
        # Crear configuración
        if tamaño == 'personalizado':
            ancho_mm = float(request.POST.get('ancho_mm', 50))
            alto_mm = float(request.POST.get('alto_mm', 30))
            config = ConfiguracionSticker.crear_para_impresora(
                impresora, 
                tamaño_mm=(ancho_mm, alto_mm),
                **config_params
            )
        else:
            config = ConfiguracionSticker(
                tamaño=tamaño,
                impresora=impresora,
                dpi=dpi,
                **config_params
            )
        
        # Validar configuración
        errores = config.validar()
        if errores:
            return JsonResponse({
                'success': False,
                'errors': errores
            })
        
        # Obtener bien para preview
        if bien_id:
            bien = get_object_or_404(BienPatrimonial, id=bien_id)
        else:
            # Usar primer bien disponible para preview
            bien = BienPatrimonial.objects.first()
            if not bien:
                return JsonResponse({
                    'success': False,
                    'errors': ['No hay bienes disponibles para preview']
                })
        
        # Generar código ZPL
        generador = GeneradorZPL(config)
        codigo_zpl = generador.generar_sticker_bien(bien)
        
        # Validar código ZPL
        es_valido, errores_zpl = ValidadorZPL.validar_codigo(codigo_zpl)
        if not es_valido:
            return JsonResponse({
                'success': False,
                'errors': errores_zpl
            })
        
        # Estimar dimensiones
        dimensiones = ValidadorZPL.estimar_tamaño_impresion(codigo_zpl, dpi)
        config_dimensiones = config.obtener_dimensiones_mm()
        
        return JsonResponse({
            'success': True,
            'codigo_zpl': codigo_zpl,
            'dimensiones': dimensiones,
            'config_dimensiones': config_dimensiones,
            'bien_info': {
                'codigo': bien.codigo_patrimonial,
                'denominacion': bien.catalogo.denominacion if bien.catalogo else '',
                'oficina': bien.oficina.nombre if bien.oficina else '',
                'estado': bien.get_estado_bien_display(),
                'marca_modelo': f"{bien.marca or ''} {bien.modelo or ''}".strip(),
                'serie': bien.serie or '',
                'qr_url': bien.url_qr or ''
            },
            'config_info': {
                'impresora': impresora,
                'dpi': dpi,
                'tamaño': tamaño,
                'incluir_qr': config.incluir_qr,
                'posicion_qr': config.posicion_qr,
                'campos_incluidos': config.campos_incluir
            },
            'compatibilidad': config.es_compatible_con_impresora(impresora, dpi),
            'estadisticas': {
                'lineas_codigo': len(codigo_zpl.split('\n')),
                'caracteres': len(codigo_zpl),
                'comandos_texto': codigo_zpl.count('^FD'),
                'comandos_posicion': codigo_zpl.count('^FO')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'errors': [f'Error generando preview: {str(e)}']
        })


@login_required
@require_http_methods(["POST"])
def generar_tickets_masivos_zebra(request):
    """Genera tickets masivos para impresora Zebra"""
    try:
        # Obtener parámetros
        impresora = request.POST.get('impresora', 'ZD220')
        dpi = int(request.POST.get('dpi', 203))
        tamaño = request.POST.get('tamaño', 'etiqueta_mediana_203')
        
        # Filtros para bienes
        filtros = {}
        if request.POST.get('oficina_id'):
            filtros['oficina_id'] = request.POST.get('oficina_id')
        if request.POST.get('estado_bien'):
            filtros['estado_bien'] = request.POST.get('estado_bien')
        if request.POST.get('catalogo_id'):
            filtros['catalogo_id'] = request.POST.get('catalogo_id')
        
        # Búsqueda por texto
        busqueda = request.POST.get('busqueda', '').strip()
        queryset = BienPatrimonial.objects.filter(**filtros)
        
        if busqueda:
            queryset = queryset.filter(
                Q(codigo_patrimonial__icontains=busqueda) |
                Q(catalogo__denominacion__icontains=busqueda) |
                Q(marca__icontains=busqueda) |
                Q(modelo__icontains=busqueda) |
                Q(serie__icontains=busqueda)
            )
        
        # Limitar cantidad para evitar archivos muy grandes
        limite = int(request.POST.get('limite', 100))
        queryset = queryset[:limite]
        
        if not queryset.exists():
            messages.error(request, 'No se encontraron bienes con los filtros especificados')
            return redirect('reportes:configurador_zebra')
        
        # Configuración personalizada
        config_params = {
            'incluir_qr': request.POST.get('incluir_qr') == 'true',
            'posicion_qr': request.POST.get('posicion_qr', 'izquierda'),
            'incluir_fecha': request.POST.get('incluir_fecha') == 'true',
            'incluir_borde': request.POST.get('incluir_borde') == 'true',
            'campos_incluir': request.POST.getlist('campos_incluir[]')
        }
        
        # Crear configuración
        if tamaño == 'personalizado':
            ancho_mm = float(request.POST.get('ancho_mm', 50))
            alto_mm = float(request.POST.get('alto_mm', 30))
            config = ConfiguracionSticker.crear_para_impresora(
                impresora, 
                tamaño_mm=(ancho_mm, alto_mm),
                **config_params
            )
        else:
            config = ConfiguracionSticker(
                tamaño=tamaño,
                impresora=impresora,
                dpi=dpi,
                **config_params
            )
        
        # Validar configuración
        errores = config.validar()
        if errores:
            messages.error(request, f'Configuración inválida: {", ".join(errores)}')
            return redirect('reportes:configurador_zebra')
        
        # Generar código ZPL masivo
        generador = GeneradorZPL(config)
        codigo_zpl = generador.generar_stickers_masivos(queryset)
        
        # Crear respuesta HTTP con archivo ZPL
        response = HttpResponse(codigo_zpl, content_type='text/plain')
        filename = f'tickets_zebra_{impresora}_{queryset.count()}_bienes.zpl'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        messages.success(request, f'Generados {queryset.count()} tickets para {impresora}')
        return response
        
    except Exception as e:
        messages.error(request, f'Error generando tickets: {str(e)}')
        return redirect('reportes:configurador_zebra')


@login_required
def obtener_configuraciones_impresora(request, impresora):
    """Obtiene configuraciones recomendadas para una impresora específica"""
    try:
        if impresora not in ConfiguracionSticker.IMPRESORAS_ZEBRA:
            return JsonResponse({
                'success': False,
                'error': f'Impresora {impresora} no reconocida'
            })
        
        config_impresora = ConfiguracionSticker.IMPRESORAS_ZEBRA[impresora]
        
        # Tamaños recomendados para esta impresora
        tamaños_recomendados = {}
        for nombre, config in ConfiguracionSticker.TAMAÑOS_PREDEFINIDOS.items():
            if config.get('impresora_recomendada') == impresora:
                tamaños_recomendados[nombre] = config
        
        # Configuración por defecto optimizada
        try:
            config_defecto = ConfiguracionSticker.crear_para_impresora(impresora)
            dimensiones_defecto = config_defecto.obtener_dimensiones_mm()
        except:
            dimensiones_defecto = {'ancho_mm': 50, 'alto_mm': 30}
        
        return JsonResponse({
            'success': True,
            'impresora_info': config_impresora,
            'tamaños_recomendados': tamaños_recomendados,
            'dimensiones_defecto': dimensiones_defecto,
            'dpi_recomendado': 300 if impresora.endswith('_300') else 203
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def test_impresora_zebra(request):
    """Genera un ticket de prueba para verificar configuración de impresora"""
    try:
        impresora = request.GET.get('impresora', 'ZD220')
        dpi = int(request.GET.get('dpi', 203))
        
        # Crear configuración de prueba
        config = ConfiguracionSticker.crear_para_impresora(impresora)
        
        # Crear bien de prueba
        class BienPrueba:
            codigo_patrimonial = "TEST-001-2024"
            qr_code = "test-qr-code-123"
            
            class Catalogo:
                denominacion = "BIEN DE PRUEBA PARA IMPRESORA"
            
            class Oficina:
                codigo = "TEST"
                nombre = "OFICINA DE PRUEBA"
            
            catalogo = Catalogo()
            oficina = Oficina()
            estado_bien = "B"
            marca = "MARCA TEST"
            modelo = "MODELO TEST"
            serie = "SN123456789"
            
            def get_estado_bien_display(self):
                return "Bueno"
        
        bien_prueba = BienPrueba()
        
        # Generar código ZPL de prueba
        generador = GeneradorZPL(config)
        codigo_zpl = generador.generar_sticker_bien(bien_prueba)
        
        # Agregar comentarios explicativos
        codigo_con_comentarios = f"""
; Ticket de prueba para {impresora} a {dpi} DPI
; Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
; Dimensiones: {config.obtener_dimensiones_mm()['ancho_mm']}x{config.obtener_dimensiones_mm()['alto_mm']} mm

{codigo_zpl}

; Fin del ticket de prueba
"""
        
        response = HttpResponse(codigo_con_comentarios, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="test_{impresora}_{dpi}dpi.zpl"'
        
        return response
        
    except Exception as e:
        return HttpResponse(f'Error generando ticket de prueba: {str(e)}', status=500)

@login_required
def generar_ticket_individual(request, bien_id):
    """Genera un ticket individual para un bien específico con configuración rápida"""
    try:
        bien = get_object_or_404(BienPatrimonial, id=bien_id)
        
        # Configuración por defecto optimizada
        impresora = request.GET.get('impresora', 'ZD220')
        dpi = int(request.GET.get('dpi', 203))
        tamaño = request.GET.get('tamaño', 'etiqueta_mediana_203')
        
        # Crear configuración optimizada
        if tamaño == 'personalizado':
            ancho_mm = float(request.GET.get('ancho_mm', 75))
            alto_mm = float(request.GET.get('alto_mm', 50))
            config = ConfiguracionSticker.crear_para_impresora(
                impresora, 
                tamaño_mm=(ancho_mm, alto_mm)
            )
        else:
            config = ConfiguracionSticker(
                tamaño=tamaño,
                impresora=impresora,
                dpi=dpi,
                incluir_qr=True,
                posicion_qr='izquierda',
                campos_incluir=['codigo_patrimonial', 'denominacion', 'oficina', 'estado', 'marca_modelo']
            )
        
        # Generar código ZPL
        generador = GeneradorZPL(config)
        codigo_zpl = generador.generar_sticker_bien(bien)
        
        # Crear respuesta HTTP
        response = HttpResponse(codigo_zpl, content_type='text/plain')
        filename = f'ticket_{bien.codigo_patrimonial}_{impresora}.zpl'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        messages.error(request, f'Error generando ticket: {str(e)}')
        return redirect('bienes:detail', pk=bien_id)


@login_required
def menu_impresion_qr(request):
    """Menú principal para opciones de impresión QR"""
    context = {
        'impresoras_zebra': ConfiguracionSticker.IMPRESORAS_ZEBRA,
        'tamaños_populares': {
            'ticket_pequeño': {
                'nombre': 'Ticket Pequeño (50x30mm)',
                'descripcion': 'Ideal para ZD411 - Información básica + QR',
                'config': 'ticket_pequeño_203'
            },
            'etiqueta_mediana': {
                'nombre': 'Etiqueta Mediana (75x50mm)', 
                'descripcion': 'Ideal para ZD220/ZD410 - Información completa + QR',
                'config': 'etiqueta_mediana_203'
            },
            'etiqueta_grande': {
                'nombre': 'Etiqueta Grande (100x75mm)',
                'descripcion': 'Máxima información + QR grande',
                'config': 'etiqueta_grande_203'
            }
        }
    }
    
    return render(request, 'reportes/menu_impresion_qr.html', context)


@login_required
def generar_ticket_pdf(request):
    """Genera una vista HTML optimizada para imprimir como PDF"""
    try:
        # Obtener parámetros
        bien_id = request.GET.get('bien_id')
        impresora = request.GET.get('impresora', 'ZD220')
        dpi = int(request.GET.get('dpi', 203))
        tamaño = request.GET.get('tamaño', 'etiqueta_mediana_203')
        
        if bien_id:
            bien = get_object_or_404(BienPatrimonial, id=bien_id)
        else:
            # Usar primer bien disponible
            bien = BienPatrimonial.objects.first()
            if not bien:
                return HttpResponse('No hay bienes disponibles', status=404)
        
        # Configurar dimensiones según el tamaño
        dimensiones_config = {
            'ticket_pequeño_203': {'ancho': '50mm', 'alto': '30mm', 'qr_size': '25mm'},
            'etiqueta_mediana_203': {'ancho': '75mm', 'alto': '50mm', 'qr_size': '35mm'},
            'etiqueta_grande_203': {'ancho': '100mm', 'alto': '75mm', 'qr_size': '45mm'},
            'personalizado': {
                'ancho': f"{request.GET.get('ancho_mm', 75)}mm",
                'alto': f"{request.GET.get('alto_mm', 50)}mm",
                'qr_size': '35mm'
            }
        }
        
        dimensiones = dimensiones_config.get(tamaño, dimensiones_config['etiqueta_mediana_203'])
        
        # Configurar tamaños de fuente según el tamaño de etiqueta
        font_sizes_config = {
            'ticket_pequeño_203': {'codigo': '12px', 'denominacion': '9px', 'detalle': '8px'},
            'etiqueta_mediana_203': {'codigo': '14px', 'denominacion': '11px', 'detalle': '9px'},
            'etiqueta_grande_203': {'codigo': '16px', 'denominacion': '13px', 'detalle': '10px'},
            'personalizado': {'codigo': '14px', 'denominacion': '11px', 'detalle': '9px'}
        }
        
        font_sizes = font_sizes_config.get(tamaño, font_sizes_config['etiqueta_mediana_203'])
        
        # Nombres amigables para tamaños
        nombres_tamaño = {
            'ticket_pequeño_203': 'Ticket Pequeño (50x30mm)',
            'etiqueta_mediana_203': 'Etiqueta Mediana (75x50mm)',
            'etiqueta_grande_203': 'Etiqueta Grande (100x75mm)',
            'personalizado': f'Personalizado ({dimensiones["ancho"]}x{dimensiones["alto"]})'
        }
        
        context = {
            'bien': bien,
            'impresora': impresora,
            'dpi': dpi,
            'tamaño': nombres_tamaño.get(tamaño, tamaño),
            'dimensiones': dimensiones,
            'font_sizes': font_sizes,
            'fecha_actual': datetime.now().strftime('%d/%m/%Y')
        }
        
        return render(request, 'reportes/ticket_pdf_preview.html', context)
        
    except Exception as e:
        return HttpResponse(f'Error generando preview PDF: {str(e)}', status=500)