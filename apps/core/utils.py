from django.contrib.auth.models import User, Group
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.db import transaction
from .models import UserProfile, AuditLog, RecycleBin, RecycleBinConfig
import json


def create_user_with_profile(username, email, first_name, last_name, password, 
                           role='consulta', telefono='', cargo='', oficina=None):
    """
    Crea un usuario con su perfil asociado
    """
    try:
        # Crear usuario
        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password
        )
        
        # Actualizar perfil (se crea automáticamente por la señal)
        profile = user.profile
        profile.role = role
        profile.telefono = telefono
        profile.cargo = cargo
        profile.oficina = oficina
        profile.save()
        
        # Asignar grupo correspondiente
        assign_user_to_group(user, role)
        
        return user, None
        
    except Exception as e:
        return None, str(e)


def assign_user_to_group(user, role):
    """
    Asigna un usuario al grupo correspondiente según su rol
    """
    role_to_group = {
        'administrador': 'Administrador',
        'funcionario': 'Funcionario',
        'auditor': 'Auditor',
        'consulta': 'Consulta',
    }
    
    # Remover de todos los grupos existentes
    user.groups.clear()
    
    # Asignar al grupo correspondiente
    group_name = role_to_group.get(role)
    if group_name:
        try:
            group = Group.objects.get(name=group_name)
            user.groups.add(group)
        except Group.DoesNotExist:
            pass


def update_user_role(user, new_role):
    """
    Actualiza el rol de un usuario y sus permisos
    """
    try:
        profile = user.profile
        old_role = profile.role
        profile.role = new_role
        profile.save()
        
        # Actualizar grupos
        assign_user_to_group(user, new_role)
        
        return True, f"Rol actualizado de {old_role} a {new_role}"
        
    except Exception as e:
        return False, str(e)


def deactivate_user(user, deactivated_by=None):
    """
    Desactiva un usuario
    """
    try:
        user.is_active = False
        user.save()
        
        if hasattr(user, 'profile'):
            user.profile.is_active = False
            user.profile.save()
        
        # Registrar en auditoría
        if deactivated_by:
            AuditLog.objects.create(
                user=deactivated_by,
                action='update',
                model_name='User',
                object_id=str(user.id),
                object_repr=f"{user.username}",
                changes={'is_active': False, 'profile.is_active': False}
            )
        
        return True, "Usuario desactivado correctamente"
        
    except Exception as e:
        return False, str(e)


def activate_user(user, activated_by=None):
    """
    Activa un usuario
    """
    try:
        user.is_active = True
        user.save()
        
        if hasattr(user, 'profile'):
            user.profile.is_active = True
            user.profile.save()
        
        # Registrar en auditoría
        if activated_by:
            AuditLog.objects.create(
                user=activated_by,
                action='update',
                model_name='User',
                object_id=str(user.id),
                object_repr=f"{user.username}",
                changes={'is_active': True, 'profile.is_active': True}
            )
        
        return True, "Usuario activado correctamente"
        
    except Exception as e:
        return False, str(e)


def get_users_by_role(role):
    """
    Obtiene todos los usuarios con un rol específico
    """
    return User.objects.filter(profile__role=role, profile__is_active=True)


def get_user_permissions_summary(user):
    """
    Obtiene un resumen de los permisos de un usuario
    """
    if not hasattr(user, 'profile'):
        return {}
    
    profile = user.profile
    
    return {
        'role': profile.get_role_display(),
        'can_manage_users': profile.can_manage_users(),
        'can_create_bienes': profile.can_create_bienes(),
        'can_edit_bienes': profile.can_edit_bienes(),
        'can_delete_bienes': profile.can_delete_bienes(),
        'can_import_data': profile.can_import_data(),
        'can_export_data': profile.can_export_data(),
        'can_generate_reports': profile.can_generate_reports(),
        'can_manage_catalogo': profile.can_manage_catalogo(),
        'can_manage_oficinas': profile.can_manage_oficinas(),
        'can_update_mobile': profile.can_update_mobile(),
    }


def validate_user_data(username, email, role):
    """
    Valida los datos de un usuario antes de crearlo
    """
    errors = []
    
    # Validar username único
    if User.objects.filter(username=username).exists():
        errors.append("El nombre de usuario ya existe")
    
    # Validar email único
    if email and User.objects.filter(email=email).exists():
        errors.append("El email ya está registrado")
    
    # Validar rol válido
    valid_roles = ['administrador', 'funcionario', 'auditor', 'consulta']
    if role not in valid_roles:
        errors.append(f"Rol inválido. Roles válidos: {', '.join(valid_roles)}")
    
    return errors


def get_audit_logs_for_user(user, limit=50):
    """
    Obtiene los logs de auditoría para un usuario específico
    """
    return AuditLog.objects.filter(user=user).order_by('-timestamp')[:limit]


def get_recent_audit_logs(limit=100):
    """
    Obtiene los logs de auditoría más recientes
    """
    return AuditLog.objects.all().order_by('-timestamp')[:limit]


def check_user_can_access_object(user, obj, action='view'):
    """
    Verifica si un usuario puede acceder a un objeto específico
    """
    if not hasattr(user, 'profile'):
        return False
    
    profile = user.profile
    
    # Administradores pueden hacer todo
    if profile.is_administrador:
        return True
    
    # Verificar permisos específicos según el tipo de objeto y acción
    obj_type = obj.__class__.__name__.lower()
    
    if obj_type == 'bienpatrimonial':
        if action == 'view':
            return True  # Todos pueden ver bienes
        elif action == 'create':
            return profile.can_create_bienes()
        elif action == 'edit':
            return profile.can_edit_bienes()
        elif action == 'delete':
            return profile.can_delete_bienes()
    
    elif obj_type in ['catalogo', 'oficina']:
        if action == 'view':
            return True  # Todos pueden ver catálogo y oficinas
        else:
            return profile.is_administrador  # Solo admin puede modificar
    
    return False



class RecycleBinService:
    """
    Servicio centralizado para gestionar operaciones de papelera de reciclaje
    """
    
    @staticmethod
    def soft_delete_object(obj, user, reason='', ip_address=None, user_agent=None):
        """
        Elimina lógicamente un objeto y crea entrada en RecycleBin
        
        Args:
            obj: Objeto a eliminar
            user: Usuario que realiza la eliminación
            reason: Motivo de la eliminación
            ip_address: Dirección IP del usuario
            user_agent: User Agent del navegador
            
        Returns:
            tuple: (success: bool, message: str, recycle_entry: RecycleBin or None)
        """
        from .models import DeletionAuditLog
        
        try:
            with transaction.atomic():
                # Verificar que el objeto tenga soft delete
                if not hasattr(obj, 'soft_delete'):
                    return False, "El objeto no soporta soft delete", None
                
                # Realizar soft delete en el objeto
                if not obj.soft_delete(user=user, reason=reason):
                    return False, "El objeto ya está eliminado", None
                
                # Obtener información del módulo
                module_name = obj._meta.app_label
                
                # Crear entrada en RecycleBin
                content_type = ContentType.objects.get_for_model(obj)
                
                # Preparar snapshot de datos
                original_data = RecycleBinService._create_object_snapshot(obj)
                
                recycle_entry = RecycleBin.objects.create(
                    content_type=content_type,
                    object_id=obj.pk,
                    object_repr=str(obj),
                    module_name=module_name,
                    deleted_by=user,
                    deletion_reason=reason,
                    original_data=original_data
                )
                
                # Registrar en auditoría general
                AuditLog.objects.create(
                    user=user,
                    action='delete',
                    model_name=obj.__class__.__name__,
                    object_id=str(obj.pk),
                    object_repr=str(obj),
                    changes={'deleted': True, 'reason': reason}
                )
                
                # Registrar en auditoría de eliminación específica
                DeletionAuditLog.log_soft_delete(
                    obj=obj,
                    user=user,
                    reason=reason,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    recycle_bin_entry=recycle_entry
                )
                
                return True, "Objeto eliminado correctamente", recycle_entry
                
        except Exception as e:
            return False, f"Error al eliminar objeto: {str(e)}", None
    
    @staticmethod
    def restore_object(recycle_entry, user, notes='', ip_address=None, user_agent=None):
        """
        Restaura un objeto desde la papelera
        
        Args:
            recycle_entry: Entrada de RecycleBin a restaurar
            user: Usuario que realiza la restauración
            notes: Notas adicionales sobre la restauración
            ip_address: Dirección IP del usuario
            user_agent: User Agent del navegador
            
        Returns:
            tuple: (success: bool, message: str, restored_object or None)
        """
        from .models import DeletionAuditLog
        
        try:
            with transaction.atomic():
                # Verificar que no esté ya restaurado
                if recycle_entry.is_restored:
                    return False, "El objeto ya ha sido restaurado", None
                
                # Obtener el objeto
                obj = recycle_entry.content_object
                if not obj:
                    return False, "El objeto ya no existe en la base de datos", None
                
                # Verificar permisos
                if not recycle_entry.can_be_restored_by(user):
                    return False, "No tiene permisos para restaurar este objeto", None
                
                # Validar conflictos (ej: códigos duplicados)
                conflict_check = RecycleBinService._check_restore_conflicts(obj)
                if conflict_check:
                    # Registrar intento fallido
                    DeletionAuditLog.log_failed_operation(
                        action='restore',
                        obj=obj,
                        user=user,
                        error_message=f"Conflicto al restaurar: {conflict_check}",
                        ip_address=ip_address,
                        user_agent=user_agent
                    )
                    return False, f"Conflicto al restaurar: {conflict_check}", None
                
                # Guardar estado anterior para auditoría
                previous_state = {
                    'deleted_at': str(obj.deleted_at) if obj.deleted_at else None,
                    'deleted_by': obj.deleted_by.username if obj.deleted_by else None,
                    'deletion_reason': obj.deletion_reason
                }
                
                # Restaurar el objeto
                if not obj.restore(user=user):
                    return False, "Error al restaurar el objeto", None
                
                # Marcar entrada como restaurada
                recycle_entry.mark_as_restored(user)
                
                # Registrar en auditoría general
                AuditLog.objects.create(
                    user=user,
                    action='update',
                    model_name=obj.__class__.__name__,
                    object_id=str(obj.pk),
                    object_repr=str(obj),
                    changes={'restored': True, 'restored_from_recycle_bin': True, 'notes': notes}
                )
                
                # Registrar en auditoría de eliminación específica
                DeletionAuditLog.log_restore(
                    obj=obj,
                    user=user,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    recycle_bin_entry=recycle_entry,
                    previous_state=previous_state
                )
                
                return True, "Objeto restaurado correctamente", obj
                
        except Exception as e:
            # Registrar error en auditoría
            if obj:
                DeletionAuditLog.log_failed_operation(
                    action='restore',
                    obj=obj,
                    user=user,
                    error_message=str(e),
                    ip_address=ip_address,
                    user_agent=user_agent
                )
            return False, f"Error al restaurar objeto: {str(e)}", None
    
    @staticmethod
    def permanent_delete(recycle_entry, user, security_code, reason='', ip_address=None, 
                        user_agent=None, session_id='', request_path='', referer='', 
                        captcha_response=None):
        """
        Elimina permanentemente un objeto de la papelera con validación de código de seguridad,
        sistema de bloqueo temporal, rate limiting y CAPTCHA.
        
        Args:
            recycle_entry: Entrada de RecycleBin a eliminar permanentemente
            user: Usuario que realiza la eliminación
            security_code: Código de seguridad para confirmar
            reason: Motivo de la eliminación permanente
            ip_address: Dirección IP del usuario
            user_agent: User Agent del navegador
            session_id: ID de sesión del usuario
            request_path: Ruta de la solicitud
            referer: URL de referencia
            captcha_response: Respuesta del CAPTCHA si es requerido
            
        Returns:
            tuple: (success: bool, message: str)
        """
        from django.conf import settings
        from .models import SecurityCodeAttempt
        
        try:
            # Verificar permisos de administrador primero
            if not (hasattr(user, 'profile') and user.profile.is_administrador):
                # Registrar intento de acceso no autorizado
                SecurityCodeAttempt.log_unauthorized_access_attempt(
                    user=user,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    request_path=request_path,
                    referer=referer,
                    reason='Usuario sin permisos de administrador intentó eliminación permanente'
                )
                return False, "Solo administradores pueden eliminar permanentemente"
            
            # Verificar rate limiting primero
            is_rate_limited, rate_count, time_until_reset = SecurityCodeAttempt.check_rate_limit(user)
            if is_rate_limited:
                # Registrar intento bloqueado por rate limit
                SecurityCodeAttempt.record_attempt(
                    user=user,
                    success=False,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    entry_id=recycle_entry.pk,
                    blocked_by_rate_limit=True,
                    session_id=session_id,
                    request_path=request_path,
                    referer=referer
                )
                return False, f"Demasiados intentos. Por favor espere {time_until_reset} minutos antes de intentar nuevamente."
            
            # Verificar si el usuario está bloqueado temporalmente
            lockout_level = SecurityCodeAttempt.get_lockout_level(user)
            is_locked, attempts, time_remaining = SecurityCodeAttempt.is_user_locked_out(
                user, 
                max_attempts=lockout_level['max_attempts'],
                lockout_minutes=lockout_level['lockout_minutes']
            )
            
            if is_locked:
                # Registrar intento durante bloqueo
                SecurityCodeAttempt.record_attempt(
                    user=user,
                    success=False,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    entry_id=recycle_entry.pk,
                    session_id=session_id,
                    request_path=request_path,
                    referer=referer
                )
                
                if lockout_level['requires_admin_unlock']:
                    return False, f"Su cuenta ha sido bloqueada por seguridad (Nivel {lockout_level['name']}). Contacte a un administrador para desbloquearla."
                else:
                    return False, f"Usuario bloqueado temporalmente por múltiples intentos fallidos (Nivel {lockout_level['name']}). Intente nuevamente en {time_remaining} minutos."
            
            # Verificar si requiere CAPTCHA
            requires_captcha = SecurityCodeAttempt.requires_captcha_validation(user)
            
            if requires_captcha:
                # Validar CAPTCHA si es requerido
                if not captcha_response:
                    SecurityCodeAttempt.record_attempt(
                        user=user,
                        success=False,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        entry_id=recycle_entry.pk,
                        requires_captcha=True,
                        captcha_passed=False,
                        session_id=session_id,
                        request_path=request_path,
                        referer=referer
                    )
                    return False, "Se requiere validación CAPTCHA. Por favor complete el CAPTCHA e intente nuevamente."
                
                # Validar respuesta del CAPTCHA
                captcha_valid = RecycleBinService._validate_captcha(captcha_response, ip_address)
                if not captcha_valid:
                    SecurityCodeAttempt.record_attempt(
                        user=user,
                        success=False,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        entry_id=recycle_entry.pk,
                        requires_captcha=True,
                        captcha_passed=False,
                        session_id=session_id,
                        request_path=request_path,
                        referer=referer
                    )
                    return False, "Validación CAPTCHA fallida. Por favor intente nuevamente."
            
            # Verificar código de seguridad
            expected_code = getattr(settings, 'PERMANENT_DELETE_CODE', None)
            if not expected_code:
                return False, "Código de seguridad no configurado en el sistema"
            
            if security_code != expected_code:
                # Registrar intento fallido en SecurityCodeAttempt
                SecurityCodeAttempt.record_attempt(
                    user=user,
                    success=False,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    entry_id=recycle_entry.pk,
                    requires_captcha=requires_captcha,
                    captcha_passed=True if requires_captcha and captcha_response else None,
                    session_id=session_id,
                    request_path=request_path,
                    referer=referer
                )
                
                # Registrar en auditoría
                AuditLog.objects.create(
                    user=user,
                    action='security_violation',
                    model_name='RecycleBin',
                    object_id=str(recycle_entry.pk),
                    object_repr=f"Intento fallido: {recycle_entry.object_repr}",
                    ip_address=ip_address,
                    user_agent=user_agent,
                    changes={
                        'permanent_delete_attempt': 'failed',
                        'reason': 'invalid_code',
                        'ip_address': ip_address,
                        'user_agent': user_agent,
                        'session_id': session_id,
                        'request_path': request_path,
                        'lockout_level': lockout_level['name']
                    }
                )
                
                # Verificar cuántos intentos lleva
                recent_failures = SecurityCodeAttempt.get_recent_failed_attempts(user)
                attempts_count = recent_failures.count()
                remaining_attempts = lockout_level['max_attempts'] - attempts_count
                
                if remaining_attempts > 0:
                    captcha_warning = " Se requerirá CAPTCHA en el próximo intento." if attempts_count >= 1 else ""
                    return False, f"Código de seguridad incorrecto. Le quedan {remaining_attempts} intento(s) antes del bloqueo temporal.{captcha_warning}"
                else:
                    return False, f"Código de seguridad incorrecto. Usuario bloqueado temporalmente por {lockout_level['lockout_minutes']} minutos."
            
            with transaction.atomic():
                # Registrar intento exitoso
                SecurityCodeAttempt.record_attempt(
                    user=user,
                    success=True,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    entry_id=recycle_entry.pk,
                    requires_captcha=requires_captcha,
                    captcha_passed=True if requires_captcha else None,
                    session_id=session_id,
                    request_path=request_path,
                    referer=referer
                )
                
                # Obtener el objeto antes de eliminarlo
                obj = recycle_entry.content_object
                obj_repr = recycle_entry.object_repr
                obj_class = recycle_entry.content_type.model
                obj_id = recycle_entry.object_id
                
                # Registrar en auditoría general antes de eliminar
                AuditLog.objects.create(
                    user=user,
                    action='delete',
                    model_name=obj_class,
                    object_id=str(obj_id),
                    object_repr=obj_repr,
                    changes={
                        'permanent_delete': True,
                        'reason': reason,
                        'original_data': recycle_entry.original_data,
                        'deleted_at': str(recycle_entry.deleted_at),
                        'deleted_by': recycle_entry.deleted_by.username,
                        'permanently_deleted_by': user.username,
                        'ip_address': ip_address,
                        'user_agent': user_agent
                    }
                )
                
                # Registrar en auditoría de eliminación específica antes de eliminar
                if obj:
                    from .models import DeletionAuditLog
                    DeletionAuditLog.log_permanent_delete(
                        obj=obj,
                        user=user,
                        reason=reason,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        recycle_bin_entry=recycle_entry,
                        security_code_used=True
                    )
                
                # Eliminar físicamente el objeto si existe
                if obj:
                    obj.hard_delete()
                
                # Eliminar entrada de RecycleBin
                recycle_entry.delete()
                
                return True, "Objeto eliminado permanentemente"
                
        except Exception as e:
            return False, f"Error al eliminar permanentemente: {str(e)}"
    
    @staticmethod
    def auto_cleanup():
        """
        Elimina automáticamente objetos que han superado el tiempo de retención
        
        Returns:
            dict: Estadísticas de la limpieza
        """
        stats = {
            'total_checked': 0,
            'deleted': 0,
            'errors': 0,
            'by_module': {}
        }
        
        try:
            # Obtener entradas listas para eliminación automática
            entries_to_delete = RecycleBin.objects.filter(
                restored_at__isnull=True,
                auto_delete_at__lte=timezone.now()
            )
            
            stats['total_checked'] = entries_to_delete.count()
            
            for entry in entries_to_delete:
                try:
                    # Verificar si la eliminación automática está habilitada para el módulo
                    config = RecycleBinConfig.get_config_for_module(entry.module_name)
                    
                    if not config.auto_delete_enabled:
                        continue
                    
                    # Eliminar el objeto
                    obj = entry.content_object
                    
                    # Registrar en auditoría de eliminación específica antes de eliminar
                    if obj:
                        from .models import DeletionAuditLog
                        DeletionAuditLog.log_auto_delete(
                            obj=obj,
                            reason=f'Eliminación automática por tiempo de retención ({config.retention_days} días)',
                            recycle_bin_entry=entry
                        )
                        obj.hard_delete()
                    
                    # Registrar en auditoría general
                    AuditLog.objects.create(
                        user=entry.deleted_by,  # Usuario original que eliminó
                        action='delete',
                        model_name=entry.content_type.model,
                        object_id=str(entry.object_id),
                        object_repr=entry.object_repr,
                        changes={
                            'auto_deleted': True,
                            'auto_delete_at': str(entry.auto_delete_at),
                            'original_data': entry.original_data
                        }
                    )
                    
                    # Eliminar entrada de RecycleBin
                    entry.delete()
                    
                    stats['deleted'] += 1
                    
                    # Actualizar estadísticas por módulo
                    if entry.module_name not in stats['by_module']:
                        stats['by_module'][entry.module_name] = 0
                    stats['by_module'][entry.module_name] += 1
                    
                except Exception as e:
                    stats['errors'] += 1
                    print(f"Error al eliminar automáticamente {entry}: {str(e)}")
            
            return stats
            
        except Exception as e:
            stats['errors'] += 1
            print(f"Error en auto_cleanup: {str(e)}")
            return stats
    
    @staticmethod
    def _create_object_snapshot(obj):
        """
        Crea un snapshot JSON de los datos del objeto
        
        Args:
            obj: Objeto del cual crear snapshot
            
        Returns:
            dict: Datos del objeto en formato JSON serializable
        """
        snapshot = {
            'model': obj.__class__.__name__,
            'pk': obj.pk,
            'fields': {}
        }
        
        # Obtener campos del modelo
        for field in obj._meta.fields:
            field_name = field.name
            try:
                value = getattr(obj, field_name)
                
                # Convertir a formato serializable
                if hasattr(value, 'pk'):  # ForeignKey
                    snapshot['fields'][field_name] = {
                        'pk': value.pk,
                        'repr': str(value)
                    }
                elif isinstance(value, (list, dict)):
                    snapshot['fields'][field_name] = value
                else:
                    snapshot['fields'][field_name] = str(value) if value is not None else None
                    
            except Exception:
                snapshot['fields'][field_name] = None
        
        return snapshot
    
    @staticmethod
    def _check_restore_conflicts(obj):
        """
        Verifica si hay conflictos al restaurar un objeto
        
        Args:
            obj: Objeto a verificar
            
        Returns:
            str: Mensaje de conflicto o None si no hay conflictos
        """
        # Verificar campos únicos
        for field in obj._meta.fields:
            if field.unique and not field.primary_key:
                field_name = field.name
                field_value = getattr(obj, field_name)
                
                if field_value:
                    # Buscar objetos activos con el mismo valor
                    existing = obj.__class__.objects.filter(**{field_name: field_value})
                    if existing.exists():
                        return f"Ya existe un registro activo con {field.verbose_name}: {field_value}"
        
        return None
    
    @staticmethod
    def _validate_captcha(captcha_response, ip_address=None):
        """
        Valida la respuesta del CAPTCHA usando Google reCAPTCHA v2.
        
        Args:
            captcha_response: Token de respuesta del CAPTCHA
            ip_address: Dirección IP del usuario (opcional)
            
        Returns:
            bool: True si el CAPTCHA es válido
        """
        from django.conf import settings
        import requests
        
        # Verificar si CAPTCHA está habilitado
        recaptcha_secret = getattr(settings, 'RECAPTCHA_SECRET_KEY', None)
        if not recaptcha_secret:
            # Si no está configurado, permitir por defecto (modo desarrollo)
            return True
        
        if not captcha_response:
            return False
        
        try:
            # Validar con Google reCAPTCHA API
            verify_url = 'https://www.google.com/recaptcha/api/siteverify'
            data = {
                'secret': recaptcha_secret,
                'response': captcha_response
            }
            
            if ip_address:
                data['remoteip'] = ip_address
            
            response = requests.post(verify_url, data=data, timeout=5)
            result = response.json()
            
            return result.get('success', False)
            
        except Exception as e:
            # En caso de error, registrar y denegar por seguridad
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error validando CAPTCHA: {str(e)}")
            return False
    
    @staticmethod
    def get_recycle_bin_stats(user=None):
        """
        Obtiene estadísticas de la papelera
        
        Args:
            user: Usuario para filtrar estadísticas (None para todas)
            
        Returns:
            dict: Estadísticas de la papelera
        """
        queryset = RecycleBin.objects.filter(restored_at__isnull=True)
        
        if user and not (hasattr(user, 'profile') and user.profile.is_administrador):
            queryset = queryset.filter(deleted_by=user)
        
        stats = {
            'total': queryset.count(),
            'by_module': {},
            'near_auto_delete': 0,
            'ready_for_auto_delete': 0
        }
        
        # Estadísticas por módulo
        for module in ['oficinas', 'bienes', 'catalogo', 'core']:
            count = queryset.filter(module_name=module).count()
            if count > 0:
                stats['by_module'][module] = count
        
        # Elementos cerca de eliminación automática
        for entry in queryset:
            if entry.is_near_auto_delete:
                stats['near_auto_delete'] += 1
            if entry.is_ready_for_auto_delete:
                stats['ready_for_auto_delete'] += 1
        
        return stats
