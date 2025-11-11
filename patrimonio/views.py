from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Sum, Q
from apps.bienes.models import BienPatrimonial
from apps.catalogo.models import Catalogo
from apps.oficinas.models import Oficina
from apps.core.models import RecycleBin
from django.contrib.auth.models import User
from datetime import datetime, timedelta

class ReactAppView(TemplateView):
    """
    Serve the React application
    """
    template_name = 'react_app.html'

def home_view(request):
    """Vista principal del sistema con estadísticas dinámicas"""
    
    # Estadísticas de bienes patrimoniales
    total_bienes = BienPatrimonial.objects.filter(deleted_at__isnull=True).count()
    bienes_nuevos = BienPatrimonial.objects.filter(
        deleted_at__isnull=True,
        estado_bien='N'
    ).count()
    bienes_buenos = BienPatrimonial.objects.filter(
        deleted_at__isnull=True,
        estado_bien='B'
    ).count()
    bienes_regulares = BienPatrimonial.objects.filter(
        deleted_at__isnull=True,
        estado_bien='R'
    ).count()
    bienes_malos = BienPatrimonial.objects.filter(
        deleted_at__isnull=True,
        estado_bien__in=['M', 'E', 'C']
    ).count()
    
    # Estadísticas de catálogo y oficinas
    total_catalogo = Catalogo.objects.filter(deleted_at__isnull=True).count()
    total_oficinas = Oficina.objects.filter(deleted_at__isnull=True).count()
    
    # Estadísticas de papelera de reciclaje
    items_papelera = RecycleBin.objects.count()
    
    # Estadísticas de usuarios
    total_usuarios = User.objects.filter(is_active=True).count()
    
    # Bienes registrados este mes
    inicio_mes = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    bienes_este_mes = BienPatrimonial.objects.filter(
        deleted_at__isnull=True,
        created_at__gte=inicio_mes
    ).count()
    
    # Valor total estimado (si existe el campo)
    try:
        valor_total = BienPatrimonial.objects.filter(
            deleted_at__isnull=True,
            valor_adquisicion__isnull=False
        ).aggregate(total=Sum('valor_adquisicion'))['total'] or 0
    except:
        valor_total = 0
    
    # Top 5 oficinas con más bienes
    top_oficinas = BienPatrimonial.objects.filter(
        deleted_at__isnull=True
    ).values(
        'oficina__nombre'
    ).annotate(
        total=Count('id')
    ).order_by('-total')[:5]
    
    # Distribución por estado
    distribucion_estados = [
        {'estado': 'Nuevo', 'cantidad': bienes_nuevos, 'color': '#28a745'},
        {'estado': 'Bueno', 'cantidad': bienes_buenos, 'color': '#17a2b8'},
        {'estado': 'Regular', 'cantidad': bienes_regulares, 'color': '#ffc107'},
        {'estado': 'Malo/RAEE/Chatarra', 'cantidad': bienes_malos, 'color': '#dc3545'},
    ]
    
    context = {
        'title': 'Sistema de Registro de Patrimonio - DRTC Puno',
        'user': request.user if request.user.is_authenticated else None,
        
        # Estadísticas principales
        'total_bienes': total_bienes,
        'total_catalogo': total_catalogo,
        'total_oficinas': total_oficinas,
        'items_papelera': items_papelera,
        'total_usuarios': total_usuarios,
        'bienes_este_mes': bienes_este_mes,
        'valor_total': valor_total,
        
        # Distribución por estado
        'bienes_nuevos': bienes_nuevos,
        'bienes_buenos': bienes_buenos,
        'bienes_regulares': bienes_regulares,
        'bienes_malos': bienes_malos,
        'distribucion_estados': distribucion_estados,
        
        # Top oficinas
        'top_oficinas': top_oficinas,
        
        # Porcentajes para gráficos
        'porcentaje_nuevos': round((bienes_nuevos / total_bienes * 100) if total_bienes > 0 else 0, 1),
        'porcentaje_buenos': round((bienes_buenos / total_bienes * 100) if total_bienes > 0 else 0, 1),
        'porcentaje_regulares': round((bienes_regulares / total_bienes * 100) if total_bienes > 0 else 0, 1),
        'porcentaje_malos': round((bienes_malos / total_bienes * 100) if total_bienes > 0 else 0, 1),
    }
    
    return render(request, 'home.html', context)