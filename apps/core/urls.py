from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Gestión de usuarios
    path('usuarios/', views.user_list, name='user_list'),
    path('usuarios/crear/', views.user_create, name='user_create'),
    path('usuarios/<int:user_id>/', views.user_detail, name='user_detail'),
    path('usuarios/<int:user_id>/editar/', views.user_edit, name='user_edit'),
    path('usuarios/<int:user_id>/toggle-status/', views.user_toggle_status, name='user_toggle_status'),
    path('usuarios/<int:user_id>/reset-password/', views.user_reset_password, name='user_reset_password'),
    
    # Auditoría
    path('auditoria/', views.audit_logs, name='audit_logs'),
    
    # API endpoints
    path('api/usuarios/', views.api_users_list, name='api_users_list'),
    path('api/usuarios/crear/', views.api_user_create, name='api_user_create'),
]