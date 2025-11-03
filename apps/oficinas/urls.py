from django.urls import path
from . import views

app_name = 'oficinas'

urlpatterns = [
    path('', views.lista_oficinas_view, name='lista'),
    path('<int:oficina_id>/', views.detalle_oficina_view, name='detalle'),
    path('importar/', views.importar_oficinas_view, name='importar'),
    path('estadisticas/', views.estadisticas_oficinas_view, name='estadisticas'),
    path('<int:oficina_id>/activar/', views.activar_oficina_view, name='activar'),
    path('<int:oficina_id>/desactivar/', views.desactivar_oficina_view, name='desactivar'),
    
    # APIs
    path('api/validar-archivo/', views.validar_archivo_oficinas, name='validar_archivo'),
    path('api/buscar/', views.buscar_oficinas_api, name='buscar_api'),
]