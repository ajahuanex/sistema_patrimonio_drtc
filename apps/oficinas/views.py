import os
import tempfile
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Count
from django.core.paginator import Paginator
from .models import Oficina
from .utils import importar_oficinas_desde_excel, validar_estructura_oficinas


@login_required
def lista_oficinas_view(request):
    """Vista para listar oficinas"""
    oficinas = Oficina.objects.all().order_by('codigo')
    
    # Filtros
    estado_filtro = request.GET.get('estado')
    busqueda = request.GET.get('q')
    
    if estado_filtro == 'activa':
        oficinas = oficinas.filter(estado=True)
    elif estado_filtro == 'inactiva':
        oficinas = oficinas.filter(estado=False)
    
    if busqueda:
        oficinas = oficinas.filter(
            Q(codigo__icontains=busqueda) |
            Q(nombre__icontains=busqueda) |
            Q(responsable__icontains=busqueda)
        )
    
    # Paginación
    paginator = Paginator(oficinas, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estadísticas
    total_oficinas = Oficina.objects.count()
    oficinas_activas = Oficina.objects.filter(estado=True).count()
    oficinas_inactivas = Oficina.objects.filter(estado=False).count()
    
    context = {
        'page_obj': page_obj,
        'estado_filtro': estado_filtro,
        'busqueda': busqueda,
        'total_oficinas': total_oficinas,
        'oficinas_activas': oficinas_activas,
        'oficinas_inactivas': oficinas_inactivas,
    }
    
    return render(request, 'oficinas/lista.html', context)


@login_required
def detalle_oficina_view(request, oficina_id):
    """Vista para mostrar detalle de una oficina"""
    oficina = get_object_or_404(Oficina, id=oficina_id)
    
    # Obtener bienes de la oficina (cuando esté implementado)
    # bienes = oficina.bienpatrimonial_set.all()[:10]
    
    context = {
        'oficina': oficina,
        # 'bienes': bienes,
    }
    
    return render(request, 'oficinas/detalle.html', context)


@login_required
@permission_required('oficinas.add_oficina', raise_exception=True)
def importar_oficinas_view(request):
    """Vista para importar oficinas desde Excel"""
    if request.method == 'POST':
        if 'archivo_excel' not in request.FILES:
            messages.error(request, 'No se seleccionó ningún archivo.')
            return redirect('oficinas:importar')
        
        archivo = request.FILES['archivo_excel']
        actualizar_existentes = request.POST.get('actualizar_existentes') == 'on'
        
        # Validar extensión
        if not archivo.name.lower().endswith(('.xlsx', '.xls')):
            messages.error(request, 'El archivo debe ser un Excel (.xlsx o .xls).')
            return redirect('oficinas:importar')
        
        # Guardar archivo temporalmente
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_file:
                for chunk in archivo.chunks():
                    temp_file.write(chunk)
                temp_path = temp_file.name
            
            # Procesar archivo
            resultado = importar_oficinas_desde_excel(temp_path, actualizar_existentes)
            
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
            
            return redirect('oficinas:importar')
            
        except Exception as e:
            messages.error(request, f'Error al procesar el archivo: {str(e)}')
            return redirect('oficinas:importar')
    
    # GET request - mostrar formulario
    context = {
        'total_oficinas': Oficina.objects.count(),
        'oficinas_activas': Oficina.objects.filter(estado=True).count(),
        'oficinas_inactivas': Oficina.objects.filter(estado=False).count(),
    }
    
    return render(request, 'oficinas/importar.html', context)


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def validar_archivo_oficinas(request):
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
        resultado = validar_estructura_oficinas(temp_path)
        
        # Limpiar archivo temporal
        os.unlink(temp_path)
        
        return JsonResponse(resultado)
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error al validar archivo: {str(e)}'
        }, status=500)


@login_required
def buscar_oficinas_api(request):
    """API para buscar oficinas (para autocompletado)"""
    termino = request.GET.get('q', '')
    limite = int(request.GET.get('limit', 10))
    solo_activas = request.GET.get('activas', 'true').lower() == 'true'
    
    if len(termino) < 2:
        return JsonResponse({'resultados': []})
    
    oficinas = Oficina.buscar_por_nombre(termino)
    
    if solo_activas:
        oficinas = oficinas.filter(estado=True)
    
    oficinas = oficinas[:limite]
    
    resultados = []
    for oficina in oficinas:
        resultados.append({
            'id': oficina.id,
            'codigo': oficina.codigo,
            'nombre': oficina.nombre,
            'responsable': oficina.responsable,
            'estado': oficina.estado,
            'texto': f"{oficina.codigo} - {oficina.nombre}"
        })
    
    return JsonResponse({'resultados': resultados})


@login_required
def estadisticas_oficinas_view(request):
    """Vista para mostrar estadísticas de oficinas"""
    # Estadísticas generales
    total = Oficina.objects.count()
    activas = Oficina.objects.filter(estado=True).count()
    inactivas = Oficina.objects.filter(estado=False).count()
    
    # Oficinas con más bienes (cuando esté implementado)
    # oficinas_con_bienes = Oficina.objects.annotate(
    #     total_bienes=Count('bienpatrimonial')
    # ).order_by('-total_bienes')[:10]
    
    # Oficinas por responsable
    responsables = Oficina.objects.values('responsable').annotate(
        total=Count('id')
    ).order_by('-total')[:10]
    
    context = {
        'total': total,
        'activas': activas,
        'inactivas': inactivas,
        'responsables': responsables,
        # 'oficinas_con_bienes': oficinas_con_bienes,
    }
    
    return render(request, 'oficinas/estadisticas.html', context)


@login_required
@permission_required('oficinas.change_oficina', raise_exception=True)
def activar_oficina_view(request, oficina_id):
    """Vista para activar una oficina"""
    oficina = get_object_or_404(Oficina, id=oficina_id)
    oficina.activar()
    messages.success(request, f'La oficina "{oficina.nombre}" ha sido activada.')
    return redirect('oficinas:detalle', oficina_id=oficina.id)


@login_required
@permission_required('oficinas.change_oficina', raise_exception=True)
def desactivar_oficina_view(request, oficina_id):
    """Vista para desactivar una oficina"""
    oficina = get_object_or_404(Oficina, id=oficina_id)
    
    # Verificar si tiene bienes asignados
    if oficina.total_bienes > 0:
        messages.error(
            request, 
            f'No se puede desactivar la oficina "{oficina.nombre}" porque tiene {oficina.total_bienes} bienes asignados.'
        )
    else:
        oficina.desactivar()
        messages.success(request, f'La oficina "{oficina.nombre}" ha sido desactivada.')
    
    return redirect('oficinas:detalle', oficina_id=oficina.id)