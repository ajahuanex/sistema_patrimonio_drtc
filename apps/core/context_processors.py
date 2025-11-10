"""
Context processors para agregar variables globales a todos los templates.
"""
from django.utils import timezone
from .models import RecycleBin


def recycle_bin_context(request):
    """
    Context processor que agrega información de la papelera de reciclaje
    a todos los templates.
    
    Proporciona:
    - Contador de elementos en papelera
    - Contador de elementos próximos a eliminarse
    - Indicador de si el usuario puede acceder a la papelera
    """
    context = {
        'recycle_bin_count': 0,
        'recycle_bin_near_delete_count': 0,
        'can_view_recycle_bin': False,
    }
    
    # Solo calcular si el usuario está autenticado
    if request.user.is_authenticated and hasattr(request.user, 'profile'):
        profile = request.user.profile
        
        # Verificar si puede ver la papelera
        context['can_view_recycle_bin'] = profile.can_view_recycle_bin()
        
        if context['can_view_recycle_bin']:
            # Obtener elementos en papelera según permisos
            if profile.can_view_all_recycle_items():
                # Administradores y auditores ven todos los elementos
                recycle_items = RecycleBin.objects.filter(restored_at__isnull=True)
            else:
                # Funcionarios ven solo sus elementos
                recycle_items = RecycleBin.objects.filter(
                    deleted_by=request.user,
                    restored_at__isnull=True
                )
            
            # Contar elementos totales
            context['recycle_bin_count'] = recycle_items.count()
            
            # Contar elementos próximos a eliminarse (7 días o menos)
            context['recycle_bin_near_delete_count'] = recycle_items.filter(
                auto_delete_at__lte=timezone.now() + timezone.timedelta(days=7)
            ).count()
    
    return context
