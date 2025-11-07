import os
import tempfile
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.conf import settings
from django.db import models
from django.core.paginator import Paginator
from .models import Catalogo
from .utils import importar_catalogo_desde_excel, validar_estructura_catalogo
from .forms import CatalogoForm


@login_required
@permission_required('catalogo.add_catalogo', raise_exception=True)
def importar_catalogo_view(request):
    """Vista para importar catálogo desde Excel"""
    if request.method == 'POST':
        if 'archivo_excel' not in request.FILES:
            messages.error(request, 'No se seleccionó ningún archivo.')
            return redirect('catalogo:importar')
        
        archivo = request.FILES['archivo_excel']
        actualizar_existentes = request.POST.get('actualizar_existentes') == 'on'
        
        # Validar extensión
        if not archivo.name.lower().endswith(('.xlsx', '.xls')):
            messages.error(request, 'El archivo debe ser un Excel (.xlsx o .xls).')
            return redirect('catalogo:importar')
        
        # Guardar archivo temporalmente
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_file:
                for chunk in archivo.chunks():
                    temp_file.write(chunk)
                temp_path = temp_file.name
            
            # Procesar archivo
            resultado = importar_catalogo_desde_excel(temp_path, actualizar_existentes)
            
            # Limpiar archivo temporal
            os.unlink(temp_path)
            
            # Mostrar resultados
            if resultado['exito']:
                messages.success(request, f"Importación exitosa: {resultado['resumen']}")
                
                # Mostrar advertencias si las hay
                for warning in resultado['warnings']:
                    messages.warning(request, warning)
            else:
                messages.error(request, "Error en la importación:")
                for error in resultado['errores']:
                    messages.error(request, error)
            
            return redirect('catalogo:importar')
            
        except Exception as e:
            messages.error(request, f'Error al procesar el archivo: {str(e)}')
            return redirect('catalogo:importar')
    
    # GET request - mostrar formulario
    context = {
        'total_catalogos': Catalogo.objects.count(),
        'catalogos_activos': Catalogo.objects.filter(estado='ACTIVO').count(),
        'catalogos_excluidos': Catalogo.objects.filter(estado='EXCLUIDO').count(),
    }
    
    return render(request, 'catalogo/importar.html', context)


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def validar_archivo_catalogo(request):
    """API endpoint para validar estructura del archivo Excel"""
    if 'archivo' not in request.FILES:
        return JsonResponse({
            'error': 'No se proporcionó archivo'
        }, status=400)
    
    archivo = request.FILES['archivo']
    
    try:
        # Guardar archivo temporalmente
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_file:
            for chunk in archivo.chunks():
                temp_file.write(chunk)
            temp_path = temp_file.name
        
        # Validar estructura
        resultado = validar_estructura_catalogo(temp_path)
        
        # Limpiar archivo temporal
        os.unlink(temp_path)
        
        return JsonResponse(resultado)
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error al validar archivo: {str(e)}'
        }, status=500)


@login_required
def lista_catalogo_view(request):
    """Vista para listar el catálogo"""
    catalogos = Catalogo.objects.all().order_by('codigo')
    
    # Filtros
    estado_filtro = request.GET.get('estado')
    grupo_filtro = request.GET.get('grupo')
    busqueda = request.GET.get('q')
    
    if estado_filtro:
        catalogos = catalogos.filter(estado=estado_filtro)
    
    if grupo_filtro:
        catalogos = catalogos.filter(grupo__icontains=grupo_filtro)
    
    if busqueda:
        catalogos = catalogos.filter(
            models.Q(codigo__icontains=busqueda) |
            models.Q(denominacion__icontains=busqueda)
        )
    
    # Paginación
    paginator = Paginator(catalogos, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Obtener grupos únicos para filtro
    grupos = Catalogo.objects.values_list('grupo', flat=True).distinct().order_by('grupo')
    
    context = {
        'catalogos': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'paginator': paginator,
        'grupos': grupos,
        'estado_filtro': estado_filtro,
        'grupo_filtro': grupo_filtro,
        'busqueda': busqueda,
    }
    
    return render(request, 'catalogo/lista.html', context)


@login_required
def buscar_catalogo_api(request):
    """API para buscar en el catálogo (para autocompletado)"""
    termino = request.GET.get('q', '')
    limite = int(request.GET.get('limit', 10))
    
    if len(termino) < 2:
        return JsonResponse({'resultados': []})
    
    catalogos = Catalogo.buscar_por_denominacion(termino)[:limite]
    
    resultados = []
    for catalogo in catalogos:
        resultados.append({
            'id': catalogo.id,
            'codigo': catalogo.codigo,
            'denominacion': catalogo.denominacion,
            'grupo': catalogo.grupo,
            'clase': catalogo.clase,
            'texto': f"{catalogo.codigo} - {catalogo.denominacion}"
        })
    
    return JsonResponse({'resultados': resultados})


@login_required
def estadisticas_catalogo_view(request):
    """Vista para mostrar estadísticas del catálogo"""
    from django.db.models import Count
    
    # Estadísticas generales
    total = Catalogo.objects.count()
    activos = Catalogo.objects.filter(estado='ACTIVO').count()
    excluidos = Catalogo.objects.filter(estado='EXCLUIDO').count()
    
    # Estadísticas por grupo
    por_grupo = Catalogo.objects.values('grupo').annotate(
        total=Count('id')
    ).order_by('-total')[:10]
    
    # Estadísticas por clase
    por_clase = Catalogo.objects.values('clase').annotate(
        total=Count('id')
    ).order_by('-total')[:10]
    
    context = {
        'total': total,
        'activos': activos,
        'excluidos': excluidos,
        'por_grupo': por_grupo,
        'por_clase': por_clase,
    }
    
    return render(request, 'catalogo/estadisticas.html', context)

@login_required
@permission_required('catalogo.add_catalogo', raise_exception=True)
def agregar_catalogo_view(request):
    """Vista para agregar un nuevo catálogo"""
    if request.method == 'POST':
        form = CatalogoForm(request.POST)
        if form.is_valid():
            catalogo = form.save()
            messages.success(request, f'Catálogo "{catalogo.codigo}" creado exitosamente.')
            return redirect('catalogo:detalle', pk=catalogo.pk)
    else:
        form = CatalogoForm()
    
    context = {
        'form': form,
        'titulo': 'Agregar Catálogo'
    }
    return render(request, 'catalogo/formulario.html', context)


@login_required
def detalle_catalogo_view(request, pk):
    """Vista para ver detalles de un catálogo"""
    catalogo = get_object_or_404(Catalogo, pk=pk)
    
    # Obtener bienes relacionados si existen
    bienes_count = 0
    try:
        from apps.bienes.models import BienPatrimonial
        bienes_count = BienPatrimonial.objects.filter(catalogo=catalogo).count()
    except ImportError:
        pass
    
    context = {
        'catalogo': catalogo,
        'bienes_count': bienes_count,
    }
    return render(request, 'catalogo/detalle.html', context)


@login_required
@permission_required('catalogo.change_catalogo', raise_exception=True)
def editar_catalogo_view(request, pk):
    """Vista para editar un catálogo"""
    catalogo = get_object_or_404(Catalogo, pk=pk)
    
    if request.method == 'POST':
        form = CatalogoForm(request.POST, instance=catalogo)
        if form.is_valid():
            catalogo = form.save()
            messages.success(request, f'Catálogo "{catalogo.codigo}" actualizado exitosamente.')
            return redirect('catalogo:detalle', pk=catalogo.pk)
    else:
        form = CatalogoForm(instance=catalogo)
    
    context = {
        'form': form,
        'catalogo': catalogo,
        'titulo': f'Editar Catálogo {catalogo.codigo}'
    }
    return render(request, 'catalogo/formulario.html', context)


@login_required
@permission_required('catalogo.view_catalogo', raise_exception=True)
def exportar_catalogo_view(request):
    """Vista para exportar catálogo a Excel"""
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    from django.utils import timezone
    
    # Crear workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Catálogo SBN"
    
    # Encabezados
    headers = ['CÓDIGO', 'DENOMINACIÓN', 'GRUPO', 'CLASE', 'RESOLUCIÓN', 'ESTADO']
    ws.append(headers)
    
    # Estilo para encabezados
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")
    
    # Datos
    catalogos = Catalogo.objects.all().order_by('codigo')
    for catalogo in catalogos:
        ws.append([
            catalogo.codigo,
            catalogo.denominacion,
            catalogo.grupo or '',
            catalogo.clase or '',
            catalogo.resolucion or '',
            catalogo.estado
        ])
    
    # Ajustar ancho de columnas
    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column_letter].width = adjusted_width
    
    # Preparar respuesta
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f"catalogo_sbn_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    wb.save(response)
    return response