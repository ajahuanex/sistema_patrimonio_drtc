import os
import tempfile
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.conf import settings
from .models import Catalogo
from .utils import importar_catalogo_desde_excel, validar_estructura_catalogo


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
    from django.core.paginator import Paginator
    paginator = Paginator(catalogos, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Obtener grupos únicos para filtro
    grupos = Catalogo.objects.values_list('grupo', flat=True).distinct().order_by('grupo')
    
    context = {
        'page_obj': page_obj,
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