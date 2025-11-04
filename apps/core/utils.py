from django.contrib.auth.models import User, Group
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from .models import UserProfile, AuditLog


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