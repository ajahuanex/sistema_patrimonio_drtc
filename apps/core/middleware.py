import json
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser
from .models import AuditLog


class PermissionMiddleware(MiddlewareMixin):
    """
    Middleware para verificar permisos granulares según el rol del usuario
    """
    
    # URLs que requieren permisos específicos
    PROTECTED_URLS = {
        # Gestión de usuarios (solo administradores)
        '/admin/auth/user/': 'can_manage_users',
        '/admin/core/userprofile/': 'can_manage_users',
        
        # Importación de datos
        '/catalogo/importar/': 'can_import_data',
        '/oficinas/importar/': 'can_import_data',
        '/bienes/importar/': 'can_import_data',
        
        # Exportación de datos
        '/reportes/exportar/': 'can_export_data',
        '/bienes/exportar/': 'can_export_data',
        
        # Generación de QR y stickers
        '/bienes/generar-qr/': 'can_generate_qr',
        '/reportes/stickers/': 'can_print_stickers',
        
        # Actualización móvil
        '/api/mobile/': 'can_update_mobile',
        
        # Gestión de catálogo (solo administradores)
        '/catalogo/crear/': 'can_manage_users',  # Solo admin puede crear catálogo
        '/catalogo/editar/': 'can_manage_users',
        '/catalogo/eliminar/': 'can_manage_users',
        
        # Gestión de oficinas (solo administradores)
        '/oficinas/crear/': 'can_manage_users',
        '/oficinas/editar/': 'can_manage_users',
        '/oficinas/eliminar/': 'can_manage_users',
        
        # Eliminación de bienes (solo administradores)
        '/bienes/eliminar/': 'can_manage_users',
    }

    # URLs que requieren roles específicos
    ROLE_PROTECTED_URLS = {
        '/admin/': ['administrador'],
        '/reportes/auditoria/': ['administrador', 'auditor'],
    }

    def process_request(self, request):
        # Saltar verificación para usuarios anónimos en URLs públicas
        if isinstance(request.user, AnonymousUser):
            return None

        # Saltar verificación para superusuarios
        if request.user.is_superuser:
            return None

        # Verificar si el usuario tiene perfil
        if not hasattr(request.user, 'profile'):
            if request.path.startswith('/api/'):
                return JsonResponse({
                    'error': 'Usuario sin perfil configurado'
                }, status=403)
            else:
                messages.error(request, 'Su usuario no tiene un perfil configurado. Contacte al administrador.')
                return redirect('home')

        # Verificar si el usuario está activo
        if not request.user.profile.is_active:
            if request.path.startswith('/api/'):
                return JsonResponse({
                    'error': 'Usuario desactivado'
                }, status=403)
            else:
                messages.error(request, 'Su usuario ha sido desactivado. Contacte al administrador.')
                return redirect('home')

        # Verificar permisos específicos por URL
        for url_pattern, required_permission in self.PROTECTED_URLS.items():
            if request.path.startswith(url_pattern):
                if not request.user.has_perm(f'bienes.{required_permission}'):
                    return self._handle_permission_denied(request, f'Permiso requerido: {required_permission}')

        # Verificar roles específicos por URL
        for url_pattern, required_roles in self.ROLE_PROTECTED_URLS.items():
            if request.path.startswith(url_pattern):
                if request.user.profile.role not in required_roles:
                    return self._handle_permission_denied(request, f'Rol requerido: {", ".join(required_roles)}')

        return None

    def _handle_permission_denied(self, request, message):
        """Maneja la denegación de permisos"""
        if request.path.startswith('/api/'):
            return JsonResponse({
                'error': 'Permisos insuficientes',
                'detail': message
            }, status=403)
        else:
            messages.error(request, f'No tiene permisos para acceder a esta función. {message}')
            return redirect('home')


class AuditMiddleware(MiddlewareMixin):
    """
    Middleware para registrar acciones importantes en el sistema
    """
    
    # Métodos HTTP que se deben auditar
    AUDITABLE_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE']
    
    # URLs que se deben auditar
    AUDITABLE_URLS = [
        '/bienes/',
        '/catalogo/',
        '/oficinas/',
        '/reportes/',
        '/api/',
        '/admin/',
    ]

    def process_response(self, request, response):
        # Solo auditar usuarios autenticados
        if isinstance(request.user, AnonymousUser):
            return response

        # Solo auditar métodos específicos
        if request.method not in self.AUDITABLE_METHODS:
            return response

        # Solo auditar URLs específicas
        if not any(request.path.startswith(url) for url in self.AUDITABLE_URLS):
            return response

        # Solo auditar respuestas exitosas
        if response.status_code >= 400:
            return response

        # Determinar la acción basada en el método HTTP
        action_map = {
            'POST': 'create',
            'PUT': 'update',
            'PATCH': 'update',
            'DELETE': 'delete',
        }
        action = action_map.get(request.method, 'unknown')

        # Obtener información del objeto si está disponible
        model_name = self._extract_model_name(request.path)
        object_id = self._extract_object_id(request.path)
        
        # Obtener cambios del request
        changes = None
        try:
            if request.content_type == 'application/json' and hasattr(request, '_body'):
                # Solo para requests JSON que no han sido procesados
                changes = json.loads(request._body.decode('utf-8'))
            elif hasattr(request, 'POST') and request.POST:
                # Para formularios HTML, usar request.POST
                changes = dict(request.POST.items())
            
            # Remover campos sensibles
            if isinstance(changes, dict):
                changes.pop('password', None)
                changes.pop('password1', None)
                changes.pop('password2', None)
                changes.pop('csrfmiddlewaretoken', None)
        except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
            changes = None

        # Crear registro de auditoría
        try:
            AuditLog.objects.create(
                user=request.user,
                action=action,
                model_name=model_name,
                object_id=str(object_id) if object_id else '',
                object_repr=f"{model_name} {object_id}" if object_id else model_name,
                changes=changes,
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
            )
        except Exception as e:
            # No fallar si no se puede crear el log de auditoría
            pass

        return response

    def _extract_model_name(self, path):
        """Extrae el nombre del modelo de la URL"""
        path_parts = path.strip('/').split('/')
        if len(path_parts) > 0:
            return path_parts[0]
        return 'unknown'

    def _extract_object_id(self, path):
        """Extrae el ID del objeto de la URL"""
        path_parts = path.strip('/').split('/')
        for part in path_parts:
            if part.isdigit():
                return int(part)
        return None

    def _get_client_ip(self, request):
        """Obtiene la IP del cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip