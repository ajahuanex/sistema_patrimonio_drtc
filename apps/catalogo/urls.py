from django.urls import path
from . import views

app_name = 'catalogo'

urlpatterns = [
    path('', views.lista_catalogo_view, name='lista'),
    path('importar/', views.importar_catalogo_view, name='importar'),
    path('importar/plantilla/', views.descargar_plantilla_catalogo, name='descargar_plantilla'),
    path('agregar/', views.agregar_catalogo_view, name='agregar'),
    path('exportar/', views.exportar_catalogo_view, name='exportar'),
    path('<int:pk>/', views.detalle_catalogo_view, name='detalle'),
    path('<int:pk>/editar/', views.editar_catalogo_view, name='editar'),
    path('<int:pk>/eliminar/', views.eliminar_catalogo_view, name='eliminar'),
    path('estadisticas/', views.estadisticas_catalogo_view, name='estadisticas'),
    
    # APIs
    path('api/validar-archivo/', views.validar_archivo_catalogo, name='validar_archivo'),
    path('api/buscar/', views.buscar_catalogo_api, name='buscar_api'),
]