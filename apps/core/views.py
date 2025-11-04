from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Q
import json

from .models import UserProfile, AuditLog
from .permissions import role_required, permission_required_custom
from .utils import (
    create_user_with_profile, update_user_role, 
    deactivate_user, activate_user, validate_user_data,
    get_user_permissions_summary, get_audit_logs_for_user
)
from apps.oficinas.models import Oficina


@login_required
@role_required(['administrador'])
def user_list(request):
    """Lista de usuarios del sistema"""
    search_query = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    status_filter = request.GET.get('status', '')
    
    users = User.objects.select_related('profile', 'profile__oficina').all()
    
    # Aplicar filtros
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    if role_filter:
        users = users.filter(profile__role=role_filter)
    
    if status_filter == 'active':
        users = users.filter(profile__is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(profile__is_active=False)
    
    # Paginación
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'roles': UserProfile.ROLES,
    }
    
    return render(request, 'core/user_list.html', context)


@login_required
@role_required(['administrador'])
def user_create(request):
    """Crear nuevo usuario"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password')
        role = request.POST.get('role', 'consulta')
        telefono = request.POST.get('telefono', '')
        cargo = request.POST.get('cargo', '')
        oficina_id = request.POST.get('oficina')
        
        # Validar datos
        errors = validate_user_data(username, email, role)
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'core/user_form.html', {
                'oficinas': Oficina.objects.filter(estado=True),
                'roles': UserProfile.ROLES,
                'form_data': request.POST
            })
        
        # Obtener oficina si se especificó
        oficina = None
        if oficina_id:
            try:
                oficina = Oficina.objects.get(id=oficina_id)
            except Oficina.DoesNotExist:
                pass
        
        # Crear usuario
        user, error = create_user_with_profile(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
            role=role,
            telefono=telefono,
            cargo=cargo,
            oficina=oficina
        )
        
        if user:
            messages.success(request, f'Usuario {username} creado correctamente')
            return redirect('core:user_list')
        else:
            messages.error(request, f'Error al crear usuario: {error}')
    
    context = {
        'oficinas': Oficina.objects.filter(estado=True),
        'roles': UserProfile.ROLES,
    }
    
    return render(request, 'core/user_form.html', context)


@login_required
@role_required(['administrador'])
def user_edit(request, user_id):
    """Editar usuario existente"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        # Actualizar datos básicos del usuario
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        
        # Actualizar perfil
        profile = user.profile
        old_role = profile.role
        new_role = request.POST.get('role', profile.role)
        profile.telefono = request.POST.get('telefono', '')
        profile.cargo = request.POST.get('cargo', '')
        
        # Actualizar oficina
        oficina_id = request.POST.get('oficina')
        if oficina_id:
            try:
                profile.oficina = Oficina.objects.get(id=oficina_id)
            except Oficina.DoesNotExist:
                profile.oficina = None
        else:
            profile.oficina = None
        
        try:
            user.save()
            profile.save()
            
            # Actualizar rol si cambió
            if old_role != new_role:
                success, message = update_user_role(user, new_role)
                if success:
                    messages.success(request, f'Usuario actualizado. {message}')
                else:
                    messages.error(request, f'Error al actualizar rol: {message}')
            else:
                messages.success(request, 'Usuario actualizado correctamente')
            
            return redirect('core:user_list')
            
        except Exception as e:
            messages.error(request, f'Error al actualizar usuario: {str(e)}')
    
    context = {
        'user_obj': user,
        'oficinas': Oficina.objects.filter(estado=True),
        'roles': UserProfile.ROLES,
    }
    
    return render(request, 'core/user_form.html', context)


@login_required
@role_required(['administrador'])
def user_detail(request, user_id):
    """Detalle de usuario con historial de auditoría"""
    user = get_object_or_404(User, id=user_id)
    permissions = get_user_permissions_summary(user)
    audit_logs = get_audit_logs_for_user(user, limit=20)
    
    context = {
        'user_obj': user,
        'permissions': permissions,
        'audit_logs': audit_logs,
    }
    
    return render(request, 'core/user_detail.html', context)


@login_required
@role_required(['administrador'])
@require_http_methods(["POST"])
def user_toggle_status(request, user_id):
    """Activar/desactivar usuario"""
    user = get_object_or_404(User, id=user_id)
    
    if user.profile.is_active:
        success, message = deactivate_user(user, request.user)
        action = 'desactivado'
    else:
        success, message = activate_user(user, request.user)
        action = 'activado'
    
    if success:
        messages.success(request, f'Usuario {action} correctamente')
    else:
        messages.error(request, f'Error: {message}')
    
    return redirect('core:user_list')


@login_required
@role_required(['administrador'])
@require_http_methods(["POST"])
def user_reset_password(request, user_id):
    """Resetear contraseña de usuario"""
    user = get_object_or_404(User, id=user_id)
    new_password = request.POST.get('new_password')
    
    if not new_password:
        messages.error(request, 'Debe proporcionar una nueva contraseña')
        return redirect('core:user_detail', user_id=user_id)
    
    try:
        user.set_password(new_password)
        user.save()
        
        # Registrar en auditoría
        AuditLog.objects.create(
            user=request.user,
            action='update',
            model_name='User',
            object_id=str(user.id),
            object_repr=f"{user.username}",
            changes={'password': 'reset'}
        )
        
        messages.success(request, 'Contraseña actualizada correctamente')
        
    except Exception as e:
        messages.error(request, f'Error al actualizar contraseña: {str(e)}')
    
    return redirect('core:user_detail', user_id=user_id)


@login_required
@role_required(['administrador', 'auditor'])
def audit_logs(request):
    """Lista de logs de auditoría"""
    user_filter = request.GET.get('user', '')
    action_filter = request.GET.get('action', '')
    model_filter = request.GET.get('model', '')
    
    logs = AuditLog.objects.select_related('user').all()
    
    # Aplicar filtros
    if user_filter:
        logs = logs.filter(user__username__icontains=user_filter)
    
    if action_filter:
        logs = logs.filter(action=action_filter)
    
    if model_filter:
        logs = logs.filter(model_name__icontains=model_filter)
    
    # Paginación
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'user_filter': user_filter,
        'action_filter': action_filter,
        'model_filter': model_filter,
        'actions': AuditLog.ACTION_CHOICES,
    }
    
    return render(request, 'core/audit_logs.html', context)


# API Views para el frontend React
@csrf_exempt
@login_required
@permission_required_custom('can_manage_users')
def api_users_list(request):
    """API para listar usuarios"""
    if request.method == 'GET':
        users = User.objects.select_related('profile', 'profile__oficina').all()
        
        users_data = []
        for user in users:
            users_data.append({
                'id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'role': user.profile.role if hasattr(user, 'profile') else 'consulta',
                'role_display': user.profile.get_role_display() if hasattr(user, 'profile') else 'Consulta',
                'is_active': user.profile.is_active if hasattr(user, 'profile') else True,
                'oficina': user.profile.oficina.nombre if hasattr(user, 'profile') and user.profile.oficina else None,
                'cargo': user.profile.cargo if hasattr(user, 'profile') else '',
                'created_at': user.date_joined.isoformat(),
            })
        
        return JsonResponse({'users': users_data})
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)


@csrf_exempt
@login_required
@permission_required_custom('can_manage_users')
def api_user_create(request):
    """API para crear usuario"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Validar datos
            errors = validate_user_data(
                data.get('username'), 
                data.get('email'), 
                data.get('role', 'consulta')
            )
            
            if errors:
                return JsonResponse({'error': errors}, status=400)
            
            # Obtener oficina si se especificó
            oficina = None
            if data.get('oficina_id'):
                try:
                    oficina = Oficina.objects.get(id=data['oficina_id'])
                except Oficina.DoesNotExist:
                    pass
            
            # Crear usuario
            user, error = create_user_with_profile(
                username=data.get('username'),
                email=data.get('email', ''),
                first_name=data.get('first_name', ''),
                last_name=data.get('last_name', ''),
                password=data.get('password'),
                role=data.get('role', 'consulta'),
                telefono=data.get('telefono', ''),
                cargo=data.get('cargo', ''),
                oficina=oficina
            )
            
            if user:
                return JsonResponse({
                    'success': True,
                    'message': f'Usuario {user.username} creado correctamente',
                    'user_id': user.id
                })
            else:
                return JsonResponse({'error': error}, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON inválido'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)