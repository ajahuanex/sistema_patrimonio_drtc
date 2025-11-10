"""
Vistas optimizadas para el sistema de papelera de reciclaje.
Implementa caché, optimización de consultas y paginación eficiente.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone

from .models import RecycleBin
from .permissions import permission_required_custom
from .filters import RecycleBinFilterForm
from .cache_utils import RecycleBinCache, QueryOptimizer, PaginationOptimizer


@login_required
@permission_required_custom('can_view_recycle_bin')
def recycle_bin_list_optimized(request):
    """
    Vista optimizada de la papelera de reciclaje con caché y consultas eficientes.
    """
    # Verificar permisos
    can_view_all = request.user.profile.can_view_all_recycle_items()
    
    # Queryset base con optimizaciones
    queryset = RecycleBin.objects.all()
    
    # Aplicar optimizaciones de select_related
    queryset = QueryOptimizer.optimize_recycle_bin_queryset(queryset)
    
    # Segregación de datos por usuario
    if not can_view_all:
        queryset = queryset.filter(deleted_by=request.user)
    
    # Filtrar solo elementos no restaurados por defecto
    show_restored = request.GET.get('show_restored', 'false') == 'true'
    if not show_restored:
        queryset = queryset.filter(restored_at__isnull=True)
    
    # Crear formulario de filtros
    filter_form = RecycleBinFilterForm(request.GET or None)
    
    # Aplicar filtros
    if filter_form.is_valid():
        queryset = filter_form.apply_filters(queryset, request.user)
    
    # Ordenamiento
    order_by = request.GET.get('order_by', '-deleted_at')
    valid_order_fields = [
        'deleted_at', '-deleted_at',
        'module_name', '-module_name',
        'auto_delete_at', '-auto_delete_at',
        'object_repr', '-object_repr'
    ]
    if order_by in valid_order_fields:
        queryset = queryset.order_by(order_by)
    
    # Paginación optimizada con caché
    page_number = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 20))
    
    # Usar paginación optimizada
    page_items, total_count, total_pages = PaginationOptimizer.get_optimized_page(
        queryset, page_number, page_size, use_cache=True
    )
    
    # Obtener estadísticas rápidas con caché
    quick_stats = RecycleBinCache.get_general_stats(
        user_id=None if can_view_all else request.user.id,
        days=30
    )
    
    context = {
        'entries': page_items,
        'page_number': page_number,
        'total_pages': total_pages,
        'total_count': total_count,
        'page_size': page_size,
        'filter_form': filter_form,
        'show_restored': show_restored,
        'order_by': order_by,
        'can_view_all': can_view_all,
        'can_restore': request.user.profile.can_restore_items(),
        'can_permanent_delete': request.user.profile.can_permanent_delete(),
        'quick_stats': quick_stats,
    }
    
    return render(request, 'core/recycle_bin_list.html', context)


@login_required
def recycle_bin_dashboard_optimized(request):
    """
    Dashboard optimizado con caché de estadísticas.
    """
    # Verificar permisos
    is_admin = hasattr(request.user, 'profile') and request.user.profile.is_administrador
    
    # Obtener rango de fechas
    date_filter = request.GET.get('date_range', '30')
    try:
        days = int(date_filter)
    except (ValueError, TypeError):
        days = 30
    
    # Obtener datos del dashboard con caché
    dashboard_data = RecycleBinCache.get_dashboard_data(
        user_id=request.user.id,
        is_admin=is_admin,
        days=days
    )
    
    # Obtener elementos recientes (sin caché, son pocos)
    if is_admin:
        recent_queryset = RecycleBin.objects.all()
    else:
        recent_queryset = RecycleBin.objects.filter(deleted_by=request.user)
    
    recent_queryset = QueryOptimizer.optimize_recycle_bin_queryset(recent_queryset)
    
    recent_deletions = list(recent_queryset.filter(
        restored_at__isnull=True
    ).order_by('-deleted_at')[:5])
    
    recent_restorations = list(recent_queryset.filter(
        restored_at__isnull=False
    ).order_by('-restored_at')[:5])
    
    # Preparar datos para gráficos
    import json
    
    module_stats = dashboard_data.get('module_stats', [])
    module_names_map = {
        'oficinas': 'Oficinas',
        'bienes': 'Bienes Patrimoniales',
        'catalogo': 'Catálogo',
        'core': 'Sistema',
    }
    
    module_labels = [module_names_map.get(s['module_name'], s['module_name']) for s in module_stats]
    module_deleted = [s['total'] for s in module_stats]
    module_restored = [s['restored'] for s in module_stats]
    module_pending = [s['pending'] for s in module_stats]
    
    # Datos de usuarios (solo para admin)
    user_labels = []
    user_deleted = []
    user_restored = []
    
    if is_admin and 'user_stats' in dashboard_data:
        user_stats = dashboard_data['user_stats']
        for stat in user_stats:
            username = stat['deleted_by__username']
            first_name = stat.get('deleted_by__first_name', '')
            last_name = stat.get('deleted_by__last_name', '')
            
            if first_name and last_name:
                display_name = f"{first_name} {last_name}"
            else:
                display_name = username
            
            user_labels.append(display_name)
            user_deleted.append(stat['total'])
            user_restored.append(stat['restored'])
    
    # Calcular tasas
    general_stats = dashboard_data.get('general_stats', {})
    total_deleted = general_stats.get('total_deleted', 0)
    total_restored = general_stats.get('total_restored', 0)
    
    restoration_rate = 0
    if total_deleted > 0:
        restoration_rate = round((total_restored / total_deleted) * 100, 1)
    
    context = {
        'is_admin': is_admin,
        'date_range': days,
        'total_deleted': total_deleted,
        'total_restored': total_restored,
        'total_pending': general_stats.get('total_pending', 0),
        'near_auto_delete': general_stats.get('near_auto_delete', 0),
        'ready_for_auto_delete': general_stats.get('ready_for_auto_delete', 0),
        'restoration_rate': restoration_rate,
        'recent_deletions': recent_deletions,
        'recent_restorations': recent_restorations,
        'module_chart_data': json.dumps({
            'labels': module_labels,
            'deleted': module_deleted,
            'restored': module_restored,
            'pending': module_pending,
        }),
        'user_chart_data': json.dumps({
            'labels': user_labels,
            'deleted': user_deleted,
            'restored': user_restored,
        }),
    }
    
    return render(request, 'core/recycle_bin_dashboard.html', context)


def invalidate_recycle_bin_cache(user_id=None, module_name=None):
    """
    Helper para invalidar el caché de la papelera.
    Debe llamarse después de operaciones que modifiquen datos.
    
    Args:
        user_id: ID del usuario afectado (None para invalidar todo)
        module_name: Nombre del módulo afectado (None para invalidar todo)
    """
    if user_id:
        RecycleBinCache.invalidate_user(user_id)
    elif module_name:
        RecycleBinCache.invalidate_module(module_name)
    else:
        RecycleBinCache.invalidate_all()
