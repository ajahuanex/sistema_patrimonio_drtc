"""
Comando de management para asignar usuarios a grupos de permisos de papelera.

Este comando asigna usuarios a los grupos de permisos predefinidos según su rol.
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User, Group


class Command(BaseCommand):
    help = 'Asigna un usuario a un grupo de permisos de papelera de reciclaje'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'username',
            type=str,
            help='Nombre de usuario a asignar'
        )
        parser.add_argument(
            'role',
            type=str,
            choices=['administrador', 'funcionario', 'auditor'],
            help='Rol a asignar (administrador, funcionario, auditor)'
        )
        parser.add_argument(
            '--remove',
            action='store_true',
            help='Remover usuario del grupo en lugar de agregarlo',
        )
    
    def handle(self, *args, **options):
        username = options['username']
        role = options['role']
        remove = options.get('remove', False)
        
        # Obtener usuario
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f'Usuario "{username}" no existe')
        
        # Mapear rol a nombre de grupo
        role_to_group = {
            'administrador': 'Recycle Bin - Administrador',
            'funcionario': 'Recycle Bin - Funcionario',
            'auditor': 'Recycle Bin - Auditor',
        }
        
        group_name = role_to_group[role]
        
        # Obtener grupo
        try:
            group = Group.objects.get(name=group_name)
        except Group.DoesNotExist:
            raise CommandError(
                f'Grupo "{group_name}" no existe. '
                f'Ejecute primero: python manage.py setup_recycle_permissions'
            )
        
        # Asignar o remover
        if remove:
            if group in user.groups.all():
                user.groups.remove(group)
                self.stdout.write(self.style.SUCCESS(
                    f'✓ Usuario "{username}" removido del grupo "{group_name}"'
                ))
            else:
                self.stdout.write(self.style.WARNING(
                    f'Usuario "{username}" no pertenece al grupo "{group_name}"'
                ))
        else:
            # Remover de otros grupos de papelera primero
            for other_group_name in role_to_group.values():
                if other_group_name != group_name:
                    try:
                        other_group = Group.objects.get(name=other_group_name)
                        if other_group in user.groups.all():
                            user.groups.remove(other_group)
                            self.stdout.write(
                                f'  Removido de grupo anterior: {other_group_name}'
                            )
                    except Group.DoesNotExist:
                        pass
            
            # Agregar al nuevo grupo
            user.groups.add(group)
            
            # Actualizar rol en perfil si existe
            if hasattr(user, 'profile'):
                user.profile.role = role
                user.profile.save()
                self.stdout.write(f'  Rol actualizado en perfil: {role}')
            
            self.stdout.write(self.style.SUCCESS(
                f'✓ Usuario "{username}" asignado al grupo "{group_name}"'
            ))
        
        # Mostrar grupos actuales del usuario
        self.stdout.write('')
        self.stdout.write(f'Grupos actuales de "{username}":')
        for g in user.groups.all():
            self.stdout.write(f'  • {g.name}')
