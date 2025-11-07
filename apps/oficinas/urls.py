from django.urls import path
from . import views

app_name = 'oficinas'

urlpatterns = [
    path('', views.lista_oficinas_view, name='lista'),
    path('crear/', views.crear_oficina_view, name='crear'),
    path('<int:oficina_id>/', views.detalle_oficina_view, name='detalle'),
    path('<int:oficina_id>/editar/', views.editar_oficina_view, name='editar'),
    path('<int:oficina_id>/obtener/', views.obtener_oficina_view, name='obtener'),
    path('importar/', views.importar_oficinas_view, name='importar'),
    path('exportar/', views.exportar_oficinas_view, name='exportar'),
    path('plantilla/', views.descargar_plantilla_oficinas, name='plantilla'),
    path('estadisticas/', views.estadisticas_oficinas_view, name='estadisticas'),
    path('reportes/', views.reportes_oficinas_view, name='reportes'),
    path('reportes/exportar/', views.exportar_oficinas_view, name='exportar_reporte'),
    path('<int:oficina_id>/activar/', views.activar_oficina_view, name='activar'),
    path('<int:oficina_id>/desactivar/', views.desactivar_oficina_view, name='desactivar'),
    path('<int:oficina_id>/eliminar/', views.eliminar_oficina_view, name='eliminar'),
    
    # APIs
    path('api/validar-archivo/', views.validar_archivo_oficinas, name='validar_archivo'),
    path('api/preview-archivo/', views.preview_oficinas, name='preview_archivo'),
    path('api/buscar/', views.buscar_oficinas_api, name='buscar_api'),
]