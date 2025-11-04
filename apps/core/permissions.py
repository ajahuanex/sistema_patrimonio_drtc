from functools import wraps
from django.http import JsonResponse
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission


def role_required(allowed_roles):
    """
    Decorador que requiere que el usuario tenga uno de los roles especificados
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if not hasattr(request.user, 'profile'):
                messages.error(request, 'Usuario sin perfil configurado')
                return redirect('home')
            
            if not request.user.profile.is_active:
                messages.error(request, 'Usuario desactivado')
                return redirect('home')
            
            if request.user.profile.role not in allowed_roles:
                messages.error(request, f'Acceso denegado. Roles permitidos: {", ".join(allowed_roles)}')
                return redirect('home')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def permission_required_custom(permission_method):
    """
    Decorador que requiere un permiso específico basado en métodos del perfil
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if not hasattr(request.user, 'profile'):
                messages.error(request, 'Usuario sin perfil configurado')
                return redirect('home')
            
            if not request.user.profile.is_active:
                messages.error(request, 'Usuario desactivado')
                return redirect('home')
            
            # Verificar el permiso usando el método del perfil
            if not getattr(request.user.profile, permission_method, lambda: False)():
                messages.error(request, f'No tiene permisos para realizar esta acción')
                return redirect('home')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


class RoleRequiredMixin(LoginRequiredMixin):
    """
    Mixin que requiere que el usuario tenga uno de los roles especificados
    """
    allowed_roles = []
    
    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, 'profile'):
            messages.error(request, 'Usuario sin perfil configurado')
            return redirect('home')
        
        if not request.user.profile.is_active:
            messages.error(request, 'Usuario desactivado')
            return redirect('home')
        
        if request.user.profile.role not in self.allowed_roles:
            messages.error(request, f'Acceso denegado. Roles permitidos: {", ".join(self.allowed_roles)}')
            return redirect('home')
        
        return super().dispatch(request, *args, **kwargs)


class PermissionRequiredMixin(LoginRequiredMixin):
    """
    Mixin que requiere un permiso específico basado en métodos del perfil
    """
    permission_method = None
    
    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, 'profile'):
            messages.error(request, 'Usuario sin perfil configurado')
            return redirect('home')
        
        if not request.user.profile.is_active:
            messages.error(request, 'Usuario desactivado')
            return redirect('home')
        
        if self.permission_method:
            if not getattr(request.user.profile, self.permission_method, lambda: False)():
                messages.error(request, 'No tiene permisos para realizar esta acción')
                return redirect('home')
        
        return super().dispatch(request, *args, **kwargs)


# Permisos para Django REST Framework
class IsAdministrador(BasePermission):
    """Permiso que solo permite acceso a administradores"""
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            hasattr(request.user, 'profile') and
            request.user.profile.is_active and
            request.user.profile.is_administrador
        )


class IsFuncionarioOrAbove(BasePermission):
    """Permiso que permite acceso a funcionarios y administradores"""
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            hasattr(request.user, 'profile') and
            request.user.profile.is_active and
            request.user.profile.role in ['administrador', 'funcionario']
        )


class IsAuditorOrAbove(BasePermission):
    """Permiso que permite acceso a auditores, funcionarios y administradores"""
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            hasattr(request.user, 'profile') and
            request.user.profile.is_active and
            request.user.profile.role in ['administrador', 'funcionario', 'auditor']
        )


class CanCreateBienes(BasePermission):
    """Permiso para crear bienes patrimoniales"""
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            hasattr(request.user, 'profile') and
            request.user.profile.is_active and
            request.user.profile.can_create_bienes()
        )


class CanEditBienes(BasePermission):
    """Permiso para editar bienes patrimoniales"""
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            hasattr(request.user, 'profile') and
            request.user.profile.is_active and
            request.user.profile.can_edit_bienes()
        )


class CanDeleteBienes(BasePermission):
    """Permiso para eliminar bienes patrimoniales"""
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            hasattr(request.user, 'profile') and
            request.user.profile.is_active and
            request.user.profile.can_delete_bienes()
        )


class CanImportData(BasePermission):
    """Permiso para importar datos"""
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            hasattr(request.user, 'profile') and
            request.user.profile.is_active and
            request.user.profile.can_import_data()
        )


class CanExportData(BasePermission):
    """Permiso para exportar datos"""
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            hasattr(request.user, 'profile') and
            request.user.profile.is_active and
            request.user.profile.can_export_data()
        )


class CanUpdateMobile(BasePermission):
    """Permiso para actualizar desde móvil"""
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            hasattr(request.user, 'profile') and
            request.user.profile.is_active and
            request.user.profile.can_update_mobile()
        )


class CanManageUsers(BasePermission):
    """Permiso para gestionar usuarios"""
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            hasattr(request.user, 'profile') and
            request.user.profile.is_active and
            request.user.profile.can_manage_users()
        )