from django.urls import path
from . import views

app_name = 'catalogo'

urlpatterns = [
    path('', views.lista_catalogo_view, name='lista'),
    path('importar/', views.importar_catalogo_view, name='importar'),
    path('estadisticas/', views.estadisticas_catalogo_view, name='estadisticas'),
    
    # APIs
    path('api/validar-archivo/', views.validar_archivo_catalogo, name='validar_archivo'),
    path('api/buscar/', views.buscar_catalogo_api, name='buscar_api'),
]