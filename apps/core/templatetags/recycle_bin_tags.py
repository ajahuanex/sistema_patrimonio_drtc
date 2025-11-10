"""
Template tags personalizados para la papelera de reciclaje
"""
from django import template
from django.utils.http import urlencode

register = template.Library()


@register.simple_tag
def url_replace(request, **kwargs):
    """
    Reemplaza o agrega parámetros a la URL actual preservando los existentes
    
    Uso en template:
        {% url_replace request page=2 %}
    """
    query = request.GET.copy()
    for key, value in kwargs.items():
        if value is not None:
            query[key] = value
        elif key in query:
            del query[key]
    return '?' + query.urlencode()


@register.filter
def get_time_remaining_badge_class(days):
    """
    Retorna la clase CSS del badge según los días restantes
    
    Args:
        days: Días restantes hasta eliminación automática
        
    Returns:
        str: Clase CSS del badge
    """
    if days is None:
        return 'badge-secondary'
    elif days == 0:
        return 'badge-danger'
    elif days <= 3:
        return 'badge-danger'
    elif days <= 7:
        return 'badge-warning'
    elif days <= 14:
        return 'badge-info'
    else:
        return 'badge-success'


@register.filter
def get_time_remaining_icon(days):
    """
    Retorna el icono apropiado según los días restantes
    
    Args:
        days: Días restantes hasta eliminación automática
        
    Returns:
        str: Clase del icono Font Awesome
    """
    if days is None:
        return 'fa-question'
    elif days == 0:
        return 'fa-exclamation-circle'
    elif days <= 3:
        return 'fa-exclamation-triangle'
    elif days <= 7:
        return 'fa-clock'
    else:
        return 'fa-check-circle'


@register.filter
def get_module_icon(module_name):
    """
    Retorna el icono apropiado para cada módulo
    
    Args:
        module_name: Nombre del módulo
        
    Returns:
        str: Clase del icono Font Awesome
    """
    icons = {
        'oficinas': 'fa-building',
        'bienes': 'fa-box',
        'catalogo': 'fa-list',
        'core': 'fa-cog',
    }
    return icons.get(module_name, 'fa-file')


@register.filter
def get_module_color(module_name):
    """
    Retorna el color apropiado para cada módulo
    
    Args:
        module_name: Nombre del módulo
        
    Returns:
        str: Clase CSS de color
    """
    colors = {
        'oficinas': 'primary',
        'bienes': 'success',
        'catalogo': 'info',
        'core': 'secondary',
    }
    return colors.get(module_name, 'secondary')


@register.inclusion_tag('core/recycle_bin_time_badge.html')
def time_remaining_badge(entry):
    """
    Renderiza un badge con el tiempo restante hasta eliminación automática
    
    Args:
        entry: Instancia de RecycleBin
        
    Returns:
        dict: Contexto para el template
    """
    days = entry.days_until_auto_delete
    
    if days is None:
        text = 'Restaurado'
        badge_class = 'badge-secondary'
        icon = 'fa-check'
    elif days == 0:
        text = 'Hoy'
        badge_class = 'badge-danger'
        icon = 'fa-exclamation-circle'
    elif days == 1:
        text = '1 día'
        badge_class = 'badge-danger'
        icon = 'fa-exclamation-triangle'
    elif days <= 3:
        text = f'{days} días'
        badge_class = 'badge-danger'
        icon = 'fa-exclamation-triangle'
    elif days <= 7:
        text = f'{days} días'
        badge_class = 'badge-warning'
        icon = 'fa-clock'
    elif days <= 14:
        text = f'{days} días'
        badge_class = 'badge-info'
        icon = 'fa-clock'
    else:
        text = f'{days} días'
        badge_class = 'badge-success'
        icon = 'fa-check-circle'
    
    return {
        'text': text,
        'badge_class': badge_class,
        'icon': icon,
        'days': days
    }


@register.inclusion_tag('core/recycle_bin_status_badge.html')
def status_badge(entry):
    """
    Renderiza un badge con el estado del elemento
    
    Args:
        entry: Instancia de RecycleBin
        
    Returns:
        dict: Contexto para el template
    """
    if entry.is_restored:
        return {
            'text': 'Restaurado',
            'badge_class': 'badge-success',
            'icon': 'fa-check'
        }
    elif entry.is_ready_for_auto_delete:
        return {
            'text': 'Listo para eliminar',
            'badge_class': 'badge-danger',
            'icon': 'fa-exclamation-circle'
        }
    elif entry.is_near_auto_delete:
        return {
            'text': 'Próximo a eliminar',
            'badge_class': 'badge-warning',
            'icon': 'fa-clock'
        }
    else:
        return {
            'text': 'En papelera',
            'badge_class': 'badge-info',
            'icon': 'fa-trash'
        }
