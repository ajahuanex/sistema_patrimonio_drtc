# Task 23: Ejemplos de Uso - Optimizaciones de Rendimiento

## 📖 Guía de Ejemplos Prácticos

Esta guía proporciona ejemplos prácticos de cómo usar las optimizaciones de rendimiento implementadas.

## 1. Uso del Sistema de Caché

### Ejemplo 1: Obtener Estadísticas Generales

```python
from apps.core.cache_utils import RecycleBinCache

# En una vista
def my_dashboard_view(request):
    # Obtener estadísticas con caché (se cachea por 15 minutos)
    stats = RecycleBinCache.get_general_stats(days=30)
    
    print(f"Total eliminados: {stats['total_deleted']}")
    print(f"Total restaurados: {stats['total_restored']}")
    print(f"Pendientes: {stats['total_pending']}")
    print(f"Cerca de auto-eliminar: {stats['near_auto_delete']}")
    print(f"Listos para auto-eliminar: {stats['ready_for_auto_delete']}")
    
    return render(request, 'dashboard.html', {'stats': stats})
```

### Ejemplo 2: Estadísticas por Módulo

```python
from apps.core.cache_utils import RecycleBinCache

# Obtener estadísticas por módulo
module_stats = RecycleBinCache.get_module_stats(days=30)

# Iterar sobre los resultados
for stat in module_stats:
    print(f"Módulo: {stat['module_name']}")
    print(f"  Total: {stat['total']}")
    print(f"  Restaurados: {stat['restored']}")
    print(f"  Pendientes: {stat['pending']}")
```

### Ejemplo 3: Estadísticas por Usuario (Admin)

```python
from apps.core.cache_utils import RecycleBinCache

# Solo para administradores
if request.user.profile.is_administrador:
    user_stats = RecycleBinCache.get_user_stats(days=30, limit=10)
    
    for stat in user_stats:
        username = stat['deleted_by__username']
        total = stat['total']
        restored = stat['restored']
        print(f"{username}: {total} eliminados, {restored} restaurados")
```

### Ejemplo 4: Dashboard Completo con Caché

```python
from apps.core.cache_utils import RecycleBinCache

def optimized_dashboard(request):
    is_admin = request.user.profile.is_administrador
    
    # Obtener todos los datos del dashboard con caché
    dashboard_data = RecycleBinCache.get_dashboard_data(
        user_id=request.user.id,
        is_admin=is_admin,
        days=30
    )
    
    # Los datos incluyen:
    # - general_stats: estadísticas generales
    # - module_stats: estadísticas por módulo
    # - user_stats: estadísticas por usuario (si es admin)
    
    context = {
        'general': dashboard_data['general_stats'],
        'modules': dashboard_data['module_stats'],
        'users': dashboard_data.get('user_stats', []),
    }
    
    return render(request, 'dashboard.html', context)
```

## 2. Invalidación de Caché

### Ejemplo 5: Invalidar Después de Soft Delete

```python
from apps.core.cache_utils import RecycleBinCache
from apps.core.utils import RecycleBinService

def delete_oficina(request, oficina_id):
    oficina = get_object_or_404(Oficina, id=oficina_id)
    
    # Realizar soft delete
    success, message, entry = RecycleBinService.soft_delete_object(
        obj=oficina,
        user=request.user,
        reason=request.POST.get('reason', '')
    )
    
    if success:
        # Invalidar caché del usuario y módulo
        RecycleBinCache.invalidate_user(request.user.id)
        RecycleBinCache.invalidate_module('oficinas')
        
        messages.success(request, message)
    else:
        messages.error(request, message)
    
    return redirect('oficinas:lista')
```

### Ejemplo 6: Invalidar Después de Restaurar

```python
from apps.core.cache_utils import RecycleBinCache

def restore_item(request, entry_id):
    entry = get_object_or_404(RecycleBin, id=entry_id)
    
    # Restaurar
    success, message, obj = RecycleBinService.restore_object(
        recycle_entry=entry,
        user=request.user
    )
    
    if success:
        # Invalidar caché
        RecycleBinCache.invalidate_user(request.user.id)
        RecycleBinCache.invalidate_module(entry.module_name)
        
        messages.success(request, message)
    
    return redirect('core:recycle_bin_list')
```

### Ejemplo 7: Invalidar Todo el Caché

```python
from apps.core.cache_utils import RecycleBinCache

def cleanup_recycle_bin(request):
    # Realizar limpieza automática
    deleted_count = RecycleBinService.auto_cleanup()
    
    # Invalidar todo el caché después de limpieza masiva
    RecycleBinCache.invalidate_all()
    
    messages.success(request, f"Se eliminaron {deleted_count} elementos")
    return redirect('core:recycle_bin_dashboard')
```

## 3. Optimización de Consultas

### Ejemplo 8: Listado Optimizado Básico

```python
from apps.core.models import RecycleBin
from apps.core.cache_utils import QueryOptimizer

def recycle_bin_list(request):
    # Queryset base
    queryset = RecycleBin.objects.all()
    
    # Aplicar optimización
    queryset = QueryOptimizer.optimize_recycle_bin_queryset(queryset)
    
    # Ahora puedes acceder a relaciones sin consultas adicionales
    entries = queryset[:20]
    
    for entry in entries:
        # Sin consulta adicional
        print(entry.deleted_by.username)
        print(entry.deleted_by.profile.role)
        print(entry.content_type.model)
    
    return render(request, 'list.html', {'entries': entries})
```

### Ejemplo 9: Listado con Filtros Optimizado

```python
from apps.core.cache_utils import QueryOptimizer
from apps.core.filters import RecycleBinFilterForm

def filtered_list(request):
    # Queryset base optimizado
    queryset = RecycleBin.objects.all()
    queryset = QueryOptimizer.optimize_recycle_bin_queryset(queryset)
    
    # Aplicar filtros
    filter_form = RecycleBinFilterForm(request.GET)
    if filter_form.is_valid():
        queryset = filter_form.apply_filters(queryset, request.user)
    
    # Ordenar
    queryset = queryset.order_by('-deleted_at')
    
    # Paginar (ver siguiente sección)
    # ...
    
    return render(request, 'list.html', {
        'entries': queryset,
        'filter_form': filter_form
    })
```

### Ejemplo 10: Optimizar Logs de Auditoría

```python
from apps.core.models import DeletionAuditLog
from apps.core.cache_utils import QueryOptimizer

def audit_logs_view(request):
    # Queryset base
    queryset = DeletionAuditLog.objects.all()
    
    # Optimizar
    queryset = QueryOptimizer.optimize_deletion_audit_queryset(queryset)
    
    # Acceder a relaciones sin consultas adicionales
    logs = queryset[:50]
    
    for log in logs:
        print(log.user.username)  # Sin consulta extra
        print(log.user.profile.role)  # Sin consulta extra
        print(log.content_type.model)  # Sin consulta extra
    
    return render(request, 'audit_logs.html', {'logs': logs})
```

## 4. Paginación Optimizada

### Ejemplo 11: Paginación Tradicional con Caché

```python
from apps.core.cache_utils import PaginationOptimizer, QueryOptimizer

def paginated_list(request):
    # Queryset optimizado
    queryset = RecycleBin.objects.all()
    queryset = QueryOptimizer.optimize_recycle_bin_queryset(queryset)
    queryset = queryset.order_by('-deleted_at')
    
    # Obtener número de página
    page_number = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 20))
    
    # Paginar con caché
    page_items, total_count, total_pages = PaginationOptimizer.get_optimized_page(
        queryset,
        page_number=page_number,
        page_size=page_size,
        use_cache=True
    )
    
    context = {
        'entries': page_items,
        'page_number': page_number,
        'total_pages': total_pages,
        'total_count': total_count,
        'page_size': page_size,
    }
    
    return render(request, 'list.html', context)
```

### Ejemplo 12: Paginación por Cursor (Scroll Infinito)

```python
from apps.core.cache_utils import PaginationOptimizer, QueryOptimizer
from django.http import JsonResponse

def infinite_scroll_api(request):
    # Queryset optimizado
    queryset = RecycleBin.objects.all()
    queryset = QueryOptimizer.optimize_recycle_bin_queryset(queryset)
    queryset = queryset.order_by('-id')
    
    # Obtener cursor de la solicitud
    cursor = request.GET.get('cursor')
    if cursor:
        cursor = int(cursor)
    
    # Paginar por cursor
    page_items, next_cursor, prev_cursor = PaginationOptimizer.get_cursor_page(
        queryset,
        cursor_field='id',
        cursor_value=cursor,
        page_size=20,
        direction='next'
    )
    
    # Serializar datos
    data = {
        'items': [
            {
                'id': item.id,
                'object_repr': item.object_repr,
                'deleted_at': item.deleted_at.isoformat(),
                'deleted_by': item.deleted_by.username,
            }
            for item in page_items
        ],
        'next_cursor': next_cursor,
        'has_more': next_cursor is not None,
    }
    
    return JsonResponse(data)
```

### Ejemplo 13: Paginación con Diferentes Tamaños

```python
from apps.core.cache_utils import PaginationOptimizer

def flexible_pagination(request):
    queryset = RecycleBin.objects.all().order_by('-deleted_at')
    
    # Permitir al usuario elegir tamaño de página
    page_size_options = [10, 20, 50, 100]
    page_size = int(request.GET.get('page_size', 20))
    
    # Validar tamaño
    if page_size not in page_size_options:
        page_size = 20
    
    page_number = int(request.GET.get('page', 1))
    
    # Paginar
    page_items, total_count, total_pages = PaginationOptimizer.get_optimized_page(
        queryset,
        page_number=page_number,
        page_size=page_size,
        use_cache=True
    )
    
    context = {
        'entries': page_items,
        'page_number': page_number,
        'total_pages': total_pages,
        'page_size': page_size,
        'page_size_options': page_size_options,
    }
    
    return render(request, 'list.html', context)
```

## 5. Vistas Optimizadas Completas

### Ejemplo 14: Vista de Listado Completa

```python
from apps.core.cache_utils import (
    RecycleBinCache,
    QueryOptimizer,
    PaginationOptimizer
)
from apps.core.filters import RecycleBinFilterForm

@login_required
def optimized_recycle_bin_list(request):
    # Verificar permisos
    can_view_all = request.user.profile.can_view_all_recycle_items()
    
    # Queryset base optimizado
    queryset = RecycleBin.objects.all()
    queryset = QueryOptimizer.optimize_recycle_bin_queryset(queryset)
    
    # Segregación por usuario
    if not can_view_all:
        queryset = queryset.filter(deleted_by=request.user)
    
    # Filtrar solo no restaurados por defecto
    show_restored = request.GET.get('show_restored') == 'true'
    if not show_restored:
        queryset = queryset.filter(restored_at__isnull=True)
    
    # Aplicar filtros
    filter_form = RecycleBinFilterForm(request.GET)
    if filter_form.is_valid():
        queryset = filter_form.apply_filters(queryset, request.user)
    
    # Ordenar
    order_by = request.GET.get('order_by', '-deleted_at')
    queryset = queryset.order_by(order_by)
    
    # Paginar
    page_number = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 20))
    
    page_items, total_count, total_pages = PaginationOptimizer.get_optimized_page(
        queryset, page_number, page_size, use_cache=True
    )
    
    # Estadísticas rápidas con caché
    quick_stats = RecycleBinCache.get_general_stats(
        user_id=None if can_view_all else request.user.id,
        days=30
    )
    
    context = {
        'entries': page_items,
        'page_number': page_number,
        'total_pages': total_pages,
        'total_count': total_count,
        'filter_form': filter_form,
        'quick_stats': quick_stats,
        'show_restored': show_restored,
    }
    
    return render(request, 'core/recycle_bin_list.html', context)
```

### Ejemplo 15: Dashboard Completo Optimizado

```python
from apps.core.cache_utils import RecycleBinCache, QueryOptimizer
import json

@login_required
def optimized_dashboard(request):
    is_admin = request.user.profile.is_administrador
    days = int(request.GET.get('date_range', 30))
    
    # Obtener datos con caché
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
    module_stats = dashboard_data.get('module_stats', [])
    module_labels = [s['module_name'] for s in module_stats]
    module_deleted = [s['total'] for s in module_stats]
    module_restored = [s['restored'] for s in module_stats]
    
    context = {
        'is_admin': is_admin,
        'date_range': days,
        'general_stats': dashboard_data['general_stats'],
        'recent_deletions': recent_deletions,
        'recent_restorations': recent_restorations,
        'module_chart_data': json.dumps({
            'labels': module_labels,
            'deleted': module_deleted,
            'restored': module_restored,
        }),
    }
    
    return render(request, 'core/recycle_bin_dashboard.html', context)
```

## 6. Integración con Servicios

### Ejemplo 16: Soft Delete con Invalidación

```python
from apps.core.utils import RecycleBinService
from apps.core.cache_utils import RecycleBinCache

def delete_bien(request, bien_id):
    bien = get_object_or_404(BienPatrimonial, id=bien_id)
    
    # Verificar permisos
    if not request.user.profile.can_delete_bienes():
        messages.error(request, 'No tiene permisos para eliminar bienes')
        return redirect('bienes:lista')
    
    # Realizar soft delete
    success, message, entry = RecycleBinService.soft_delete_object(
        obj=bien,
        user=request.user,
        reason=request.POST.get('reason', ''),
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    if success:
        # Invalidar caché
        RecycleBinCache.invalidate_user(request.user.id)
        RecycleBinCache.invalidate_module('bienes')
        
        messages.success(request, message)
        return redirect('bienes:lista')
    else:
        messages.error(request, message)
        return redirect('bienes:detalle', pk=bien_id)
```

### Ejemplo 17: Restauración con Invalidación

```python
from apps.core.utils import RecycleBinService
from apps.core.cache_utils import RecycleBinCache

def restore_from_recycle_bin(request, entry_id):
    entry = get_object_or_404(RecycleBin, id=entry_id)
    
    # Verificar permisos
    if not entry.can_be_restored_by(request.user):
        messages.error(request, 'No tiene permisos para restaurar este elemento')
        return redirect('core:recycle_bin_list')
    
    # Restaurar
    success, message, restored_obj = RecycleBinService.restore_object(
        recycle_entry=entry,
        user=request.user,
        notes=request.POST.get('notes', ''),
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    if success:
        # Invalidar caché
        RecycleBinCache.invalidate_user(request.user.id)
        RecycleBinCache.invalidate_module(entry.module_name)
        
        messages.success(request, message)
        
        # Redirigir al objeto restaurado
        if entry.module_name == 'oficinas':
            return redirect('oficinas:detalle', pk=restored_obj.pk)
        elif entry.module_name == 'bienes':
            return redirect('bienes:detalle', pk=restored_obj.pk)
        else:
            return redirect('core:recycle_bin_list')
    else:
        messages.error(request, message)
        return redirect('core:recycle_bin_detail', entry_id=entry_id)
```

## 7. Monitoreo y Debugging

### Ejemplo 18: Verificar Hit Rate del Caché

```python
from django.core.cache import cache
from apps.core.cache_utils import RecycleBinCache

def cache_stats_view(request):
    # Solo para administradores
    if not request.user.profile.is_administrador:
        return HttpResponseForbidden()
    
    # Intentar obtener estadísticas del caché
    try:
        stats = cache.get_stats()
    except:
        stats = {'error': 'Cache backend no soporta estadísticas'}
    
    # Probar caché
    test_key = 'cache_test'
    cache.set(test_key, 'test_value', 60)
    test_result = cache.get(test_key)
    
    context = {
        'stats': stats,
        'cache_working': test_result == 'test_value',
    }
    
    return render(request, 'admin/cache_stats.html', context)
```

### Ejemplo 19: Limpiar Caché Manualmente

```python
from apps.core.cache_utils import RecycleBinCache

@login_required
@require_POST
def clear_cache(request):
    # Solo administradores
    if not request.user.profile.is_administrador:
        return HttpResponseForbidden()
    
    # Limpiar todo el caché de la papelera
    RecycleBinCache.invalidate_all()
    
    messages.success(request, 'Caché limpiado correctamente')
    return redirect('core:recycle_bin_dashboard')
```

### Ejemplo 20: Benchmark de Rendimiento

```python
import time
from django.db import connection
from django.test.utils import override_settings
from apps.core.cache_utils import QueryOptimizer

@login_required
def performance_test(request):
    # Solo administradores
    if not request.user.profile.is_administrador:
        return HttpResponseForbidden()
    
    results = {}
    
    # Test 1: Sin optimización
    with override_settings(DEBUG=True):
        connection.queries_log.clear()
        start = time.time()
        
        queryset = RecycleBin.objects.all()[:20]
        for entry in queryset:
            _ = entry.deleted_by.username
        
        results['without_optimization'] = {
            'time': time.time() - start,
            'queries': len(connection.queries)
        }
    
    # Test 2: Con optimización
    with override_settings(DEBUG=True):
        connection.queries_log.clear()
        start = time.time()
        
        queryset = RecycleBin.objects.all()
        queryset = QueryOptimizer.optimize_recycle_bin_queryset(queryset)
        queryset = queryset[:20]
        for entry in queryset:
            _ = entry.deleted_by.username
        
        results['with_optimization'] = {
            'time': time.time() - start,
            'queries': len(connection.queries)
        }
    
    # Calcular mejora
    improvement = (
        (results['without_optimization']['time'] - results['with_optimization']['time'])
        / results['without_optimization']['time'] * 100
    )
    
    results['improvement'] = f"{improvement:.1f}%"
    
    return render(request, 'admin/performance_test.html', {'results': results})
```

## 📝 Notas Finales

### Mejores Prácticas

1. **Siempre invalidar caché** después de modificar datos
2. **Usar QueryOptimizer** en todos los listados
3. **Cachear estadísticas** que se consultan frecuentemente
4. **Monitorear hit rate** del caché regularmente
5. **Ajustar timeouts** según volatilidad de datos

### Troubleshooting

Si algo no funciona:
1. Verificar que el caché está configurado correctamente
2. Verificar que se llama a invalidate después de operaciones
3. Verificar que se usa QueryOptimizer en consultas
4. Revisar logs de Django para errores

### Recursos Adicionales

- **Documentación completa:** `TASK_23_IMPLEMENTATION_SUMMARY.md`
- **Guía rápida:** `TASK_23_QUICK_REFERENCE.md`
- **Verificación:** `TASK_23_VERIFICATION.md`
- **Tests:** `tests/test_performance_optimizations.py`
