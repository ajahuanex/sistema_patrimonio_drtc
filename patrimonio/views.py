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
    Home view that redirects to React app or shows login
    """
    if request.user.is_authenticated:
        return render(request, 'react_app.html')
    else:
        return render(request, 'home.html')