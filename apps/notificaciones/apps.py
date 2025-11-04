"""
Configuración de la app de notificaciones
"""
from django.apps import AppConfig


class NotificacionesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.notificaciones'
    verbose_name = 'Notificaciones'
    
    def ready(self):
        # Importar signals si los hay
        try:
            import apps.notificaciones.signals
        except ImportError:
            pass