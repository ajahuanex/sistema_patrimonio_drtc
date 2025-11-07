from django.urls import path
from . import views
from .views_zebra import (
    ConfiguradorZebraView, generar_preview_zebra, generar_tickets_masivos_zebra,
    obtener_configuraciones_impresora, test_impresora_zebra, generar_ticket_individual,
    menu_impresion_qr, generar_ticket_pdf
)

app_name = 'reportes'

urlpatterns = [
    # Dashboard principal
    path('', views.dashboard_reportes, name='dashboard_reportes'),
    
    # Filtros avanzados
    path('filtros/', views.filtros_avanzados, name='filtros_avanzados'),
    path('filtros/vista-previa/', views.vista_previa_filtros, name='vista_previa_filtros'),
    path('filtros/exportar-excel/', views.exportar_filtros_excel, name='exportar_filtros_excel'),
    
    # Configuraciones de filtros
    path('configuraciones/', views.configuraciones_filtros, name='configuraciones_filtros'),
    path('configuraciones/crear/', views.crear_configuracion_filtro, name='crear_configuracion_filtro'),
    path('configuraciones/<int:pk>/editar/', views.editar_configuracion_filtro, name='editar_configuracion_filtro'),
    path('configuraciones/<int:pk>/eliminar/', views.eliminar_configuracion_filtro, name='eliminar_configuracion_filtro'),
    
    # Generación de reportes
    path('generar/', views.generar_reporte, name='generar_reporte'),
    path('mis-reportes/', views.mis_reportes, name='mis_reportes'),
    path('reportes/<int:pk>/descargar/', views.descargar_reporte, name='descargar_reporte'),
    path('reportes/<int:pk>/eliminar/', views.eliminar_reporte, name='eliminar_reporte'),
    
    # APIs AJAX
    path('api/marcas/', views.api_marcas_autocomplete, name='api_marcas_autocomplete'),
    path('api/modelos/', views.api_modelos_autocomplete, name='api_modelos_autocomplete'),
    path('api/clases-por-grupo/', views.api_clases_por_grupo, name='api_clases_por_grupo'),
    path('api/estadisticas/', views.api_estadisticas_filtros, name='api_estadisticas_filtros'),
    
    # Stickers ZPL
    path('stickers/configurar/', views.configurar_stickers, name='configurar_stickers'),
    path('stickers/generar/', views.generar_stickers, name='generar_stickers'),
    path('stickers/plantillas/', views.plantillas_stickers_predefinidas, name='plantillas_stickers'),
    path('stickers/vista-previa/<int:bien_id>/', views.vista_previa_sticker, name='vista_previa_sticker'),
    path('stickers/descargar/<int:bien_id>/', views.descargar_sticker_individual, name='descargar_sticker_individual'),
    path('stickers/tutorial/', views.tutorial_stickers_zpl, name='tutorial_stickers'),
    
    # APIs para stickers
    path('api/validar-sticker/', views.api_validar_configuracion_sticker, name='api_validar_sticker'),
    
    # Centro de exportación
    path('exportacion/', views.centro_exportacion, name='centro_exportacion'),
    path('exportacion/rapida/', views.exportacion_rapida, name='exportacion_rapida'),
    path('exportacion/masiva/', views.exportacion_masiva, name='exportacion_masiva'),
    path('exportacion/historial/', views.historial_exportaciones, name='historial_exportaciones'),
    path('exportacion/comparar/', views.comparar_formatos, name='comparar_formatos'),
    
    # APIs para exportación
    path('api/validar-exportacion/', views.api_validar_exportacion, name='api_validar_exportacion'),
    path('api/formatos-por-tipo/', views.api_formatos_por_tipo, name='api_formatos_por_tipo'),
    
    # Utilidades
    path('limpiar-expirados/', views.limpiar_reportes_expirados, name='limpiar_reportes_expirados'),
    
    # Configurador Impresoras Zebra
    path('zebra/', ConfiguradorZebraView.as_view(), name='configurador_zebra'),
    path('zebra/preview/', generar_preview_zebra, name='generar_preview_zebra'),
    path('zebra/masivo/', generar_tickets_masivos_zebra, name='generar_tickets_masivos_zebra'),
    path('zebra/configuracion/<str:impresora>/', obtener_configuraciones_impresora, name='configuracion_impresora'),
    path('zebra/test/', test_impresora_zebra, name='test_impresora_zebra'),
    
    # Impresión QR
    path('qr/', menu_impresion_qr, name='menu_impresion_qr'),
    path('qr/ticket/<int:bien_id>/', generar_ticket_individual, name='generar_ticket_individual'),
    path('zebra/pdf/', generar_ticket_pdf, name='generar_ticket_pdf'),
]