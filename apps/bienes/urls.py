from django.urls import path
from . import views

app_name = 'bienes'

urlpatterns = [
    # QR Code URLs
    path('qr/<str:qr_code>/', views.QRCodeDetailView.as_view(), name='qr_detail'),
    path('qr/<str:qr_code>/mobile/', views.QRCodeMobileView.as_view(), name='qr_mobile'),
    path('mobile-scanner/', views.MobileScannerView.as_view(), name='mobile_scanner'),
    
    # API URLs for mobile
    path('api/scan/', views.QRScanAPIView.as_view(), name='api_scan'),
    path('api/update-estado/', views.UpdateEstadoAPIView.as_view(), name='api_update_estado'),
    path('api/batch-scan/', views.BatchQRScanAPIView.as_view(), name='api_batch_scan'),
    path('api/mobile-inventory/', views.MobileInventoryAPIView.as_view(), name='api_mobile_inventory'),
    
    # Web URLs
    path('', views.BienListView.as_view(), name='list'),
    path('crear/', views.BienCreateView.as_view(), name='create'),
    path('<int:pk>/', views.BienDetailView.as_view(), name='detail'),
    path('<int:pk>/editar/', views.BienUpdateView.as_view(), name='update'),
    path('<int:pk>/eliminar/', views.BienDeleteView.as_view(), name='delete'),
    
    # Import/Export URLs
    path('importar/', views.ImportarBienesView.as_view(), name='importar'),
    path('importar/plantilla/', views.DescargarPlantillaBienesView.as_view(), name='descargar_plantilla'),
    path('exportar/', views.ExportarBienesView.as_view(), name='exportar'),
    
    # QR Management URLs
    path('regenerar-qr/', views.RegenerarQRView.as_view(), name='regenerar_qr'),
    path('<int:pk>/qr-image/', views.QRImageView.as_view(), name='qr_image'),
]