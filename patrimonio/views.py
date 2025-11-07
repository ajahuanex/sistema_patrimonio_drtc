from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

class ReactAppView(TemplateView):
    """
    Serve the React application
    """
    template_name = 'react_app.html'

def home_view(request):
    """
    Home view that shows basic information
    """
    if request.user.is_authenticated:
        # Estadísticas básicas sin consultas complejas
        from apps.bienes.models import BienPatrimonial
        from apps.oficinas.models import Oficina
        
        context = {
            'total_bienes': BienPatrimonial.objects.count(),
            'total_oficinas': Oficina.objects.filter(estado=True).count(),
        }
        return render(request, 'home.html', context)
    else:
        return render(request, 'home.html')