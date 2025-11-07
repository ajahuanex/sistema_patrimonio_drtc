"""
URL configuration for patrimonio project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render, redirect
from .views import home_view, ReactAppView
from apps.bienes.views import QRCodeDetailView
from .health import health_check, health_detailed

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home'),
    
    # Health checks
    path('health/', health_check, name='health_check'),
    path('health/detailed/', health_detailed, name='health_detailed'),
    
    # Authentication URLs
    path('accounts/', include('django.contrib.auth.urls')),
    path('login/', lambda request: redirect('/accounts/login/')),
    path('logout/', lambda request: redirect('/accounts/logout/')),
    
    # Django views (legacy)
    path('catalogo/', include('apps.catalogo.urls')),
    path('oficinas/', include('apps.oficinas.urls')),
    path('bienes/', include('apps.bienes.urls')),
    path('reportes/', include('apps.reportes.urls')),
    path('core/', include('apps.core.urls')),
    
    # QR Code public access
    path('qr/<str:qr_code>/', QRCodeDetailView.as_view(), name='qr_public'),
    
    # API endpoints
    path('api/', include('apps.mobile.urls')),
    
    # React App routes - catch all remaining routes
    re_path(r'^app/.*$', ReactAppView.as_view(), name='react_app'),
    path('app/', ReactAppView.as_view(), name='react_app_root'),
]

# Servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
