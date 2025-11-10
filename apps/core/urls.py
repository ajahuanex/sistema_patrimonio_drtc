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
    
    # Auditoría de Eliminaciones
    path('auditoria/eliminaciones/', views.deletion_audit_reports, name='deletion_audit_reports'),
    path('auditoria/eliminaciones/exportar/', views.deletion_audit_export, name='deletion_audit_export'),
    path('auditoria/eliminaciones/<int:log_id>/', views.deletion_audit_detail, name='deletion_audit_detail'),
    
    # Papelera de Reciclaje
    path('papelera/', views.recycle_bin_list, name='recycle_bin_list'),
    path('papelera/dashboard/', views.recycle_bin_dashboard, name='recycle_bin_dashboard'),
    path('papelera/exportar/', views.recycle_bin_export_report, name='recycle_bin_export_report'),
    path('papelera/<int:entry_id>/', views.recycle_bin_detail, name='recycle_bin_detail'),
    path('papelera/<int:entry_id>/restaurar/', views.recycle_bin_restore, name='recycle_bin_restore'),
    path('papelera/restaurar-lote/', views.recycle_bin_bulk_restore, name='recycle_bin_bulk_restore'),
    path('papelera/<int:entry_id>/eliminar-permanente/', views.recycle_bin_permanent_delete, name='recycle_bin_permanent_delete'),
    path('papelera/eliminar-permanente-lote/', views.recycle_bin_bulk_permanent_delete, name='recycle_bin_bulk_permanent_delete'),
    
    # Monitoreo de Seguridad
    path('seguridad/monitoreo/', views.security_monitoring_dashboard, name='security_monitoring_dashboard'),
    path('seguridad/intentos/<int:attempt_id>/', views.security_attempt_detail, name='security_attempt_detail'),
    path('seguridad/desbloquear/<int:user_id>/', views.unlock_user_security, name='unlock_user_security'),
    
    # API endpoints
    path('api/usuarios/', views.api_users_list, name='api_users_list'),
    path('api/usuarios/crear/', views.api_user_create, name='api_user_create'),
    path('api/recycle-bin/status/', views.recycle_bin_status_api, name='recycle_bin_status_api'),
]