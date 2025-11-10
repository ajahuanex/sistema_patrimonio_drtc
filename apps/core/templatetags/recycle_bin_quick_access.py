"""
Template tags para accesos rápidos a la papelera de reciclaje desde listados de módulos.
"""
from django import template
from django.urls import reverse
from django.utils.safestring import mark_safe
from apps.core.models import RecycleBin

register = template.Library()


@register.simple_tag(takes_context=True)
def recycle_bin_quick_access(context, module_name):
    """
    Genera un botón de acceso rápido a la papelera filtrada por módulo.
    
    Args:
        context: Contexto del template
        module_name: Nombre del módulo (oficinas, bienes, catalogo)
        
    Returns:
        HTML del botón de acceso rápido
    """
    request = context.get('request')
    if not request or not request.user.is_authenticated:
        return ''
    
    # Verificar permisos
    if not hasattr(request.user, 'profile') or not request.user.profile.can_view_recycle_bin():
        return ''
    
    # Contar elementos en papelera para este módulo
    if request.user.profile.can_view_all_recycle_items():
        count = RecycleBin.objects.filter(
            module_name=module_name,
            restored_at__isnull=True
        ).count()
    else:
        count = RecycleBin.objects.filter(
            module_name=module_name,
            deleted_by=request.user,
            restored_at__isnull=True
        ).count()
    
    if count == 0:
        return ''
    
    # Generar URL con filtro de módulo
    url = f"{reverse('core:recycle_bin_list')}?module={module_name}"
    
    # Generar HTML del botón
    html = f'''
    <div class="alert alert-info d-flex align-items-center justify-content-between mb-3" role="alert">
        <div>
            <i class="fas fa-trash-restore me-2"></i>
            <strong>{count}</strong> elemento{'s' if count != 1 else ''} de este módulo en la papelera de reciclaje.
        </div>
        <a href="{url}" class="btn btn-sm btn-outline-info">
            <i class="fas fa-eye"></i> Ver en papelera
        </a>
    </div>
    '''
    
    return mark_safe(html)


@register.simple_tag(takes_context=True)
def recycle_bin_module_badge(context, module_name):
    """
    Genera un badge con el contador de elementos en papelera para un módulo.
    
    Args:
        context: Contexto del template
        module_name: Nombre del módulo
        
    Returns:
        HTML del badge
    """
    request = context.get('request')
    if not request or not request.user.is_authenticated:
        return ''
    
    # Verificar permisos
    if not hasattr(request.user, 'profile') or not request.user.profile.can_view_recycle_bin():
        return ''
    
    # Contar elementos
    if request.user.profile.can_view_all_recycle_items():
        count = RecycleBin.objects.filter(
            module_name=module_name,
            restored_at__isnull=True
        ).count()
    else:
        count = RecycleBin.objects.filter(
            module_name=module_name,
            deleted_by=request.user,
            restored_at__isnull=True
        ).count()
    
    if count == 0:
        return ''
    
    url = f"{reverse('core:recycle_bin_list')}?module={module_name}"
    
    html = f'''
    <a href="{url}" class="badge bg-secondary text-decoration-none" title="Elementos en papelera">
        <i class="fas fa-trash-restore"></i> {count}
    </a>
    '''
    
    return mark_safe(html)


@register.inclusion_tag('core/recycle_bin_notification_widget.html', takes_context=True)
def recycle_bin_notification_widget(context):
    """
    Widget de notificaciones de papelera para mostrar en el dashboard.
    Muestra elementos próximos a eliminarse con acciones rápidas.
    
    Args:
        context: Contexto del template
        
    Returns:
        dict: Contexto para el template del widget
    """
    request = context.get('request')
    
    widget_context = {
        'show_widget': False,
        'near_delete_items': [],
        'total_items': 0,
    }
    
    if not request or not request.user.is_authenticated:
        return widget_context
    
    # Verificar permisos
    if not hasattr(request.user, 'profile') or not request.user.profile.can_view_recycle_bin():
        return widget_context
    
    # Obtener elementos próximos a eliminarse (7 días o menos)
    from django.utils import timezone
    seven_days_from_now = timezone.now() + timezone.timedelta(days=7)
    
    if request.user.profile.can_view_all_recycle_items():
        near_delete_items = RecycleBin.objects.filter(
            restored_at__isnull=True,
            auto_delete_at__lte=seven_days_from_now
        ).select_related('deleted_by', 'content_type').order_by('auto_delete_at')[:5]
    else:
        near_delete_items = RecycleBin.objects.filter(
            deleted_by=request.user,
            restored_at__isnull=True,
            auto_delete_at__lte=seven_days_from_now
        ).select_related('deleted_by', 'content_type').order_by('auto_delete_at')[:5]
    
    widget_context['show_widget'] = near_delete_items.exists()
    widget_context['near_delete_items'] = near_delete_items
    widget_context['total_items'] = near_delete_items.count()
    
    return widget_context


@register.filter
def days_until_delete(recycle_item):
    """
    Filtro para calcular días restantes hasta eliminación automática.
    
    Args:
        recycle_item: Instancia de RecycleBin
        
    Returns:
        int: Días restantes
    """
    if not recycle_item or recycle_item.is_restored:
        return None
    
    return recycle_item.days_until_auto_delete


@register.filter
def delete_urgency_class(days_remaining):
    """
    Filtro para determinar la clase CSS según urgencia de eliminación.
    
    Args:
        days_remaining: Días restantes hasta eliminación
        
    Returns:
        str: Clase CSS (danger, warning, info)
    """
    if days_remaining is None:
        return 'info'
    
    if days_remaining <= 1:
        return 'danger'
    elif days_remaining <= 3:
        return 'warning'
    else:
        return 'info'
