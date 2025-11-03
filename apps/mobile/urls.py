"""
URLs para la API móvil
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

app_name = 'mobile'

# Router para ViewSets
router = DefaultRouter()
router.register(r'bienes', views.BienPatrimonialViewSet, basename='bienes')
router.register(r'catalogo', views.CatalogoViewSet, basename='catalogo')
router.register(r'oficinas', views.OficinaViewSet, basename='oficinas')

urlpatterns = [
    # Autenticación JWT
    path('auth/login/', views.login_view, name='login'),
    path('auth/logout/', views.logout_view, name='logout'),
    path('auth/token/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', views.CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('auth/profile/', views.user_profile_view, name='user_profile'),
    
    # Endpoints móviles específicos
    path('mobile/scan/', views.scan_qr_mobile, name='scan_qr_mobile'),
    path('mobile/inventario-rapido/', views.inventario_rapido, name='inventario_rapido'),
    path('mobile/dashboard/', views.dashboard_mobile, name='dashboard_mobile'),
    
    # Endpoints de sincronización offline
    path('sync/cambios/', views.sincronizar_cambios, name='sincronizar_cambios'),
    path('sync/estado/<int:sesion_id>/', views.estado_sincronizacion, name='estado_sincronizacion'),
    path('sync/resolver-conflicto/', views.resolver_conflicto, name='resolver_conflicto'),
    path('sync/cambios-pendientes/', views.cambios_pendientes, name='cambios_pendientes'),
    path('sync/reintentar/', views.reintentar_sincronizacion, name='reintentar_sincronizacion'),
    
    # Incluir URLs del router
    path('', include(router.urls)),
]