from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from apps.bienes.models import BienPatrimonial
from apps.catalogo.models import Catalogo
from apps.oficinas.models import Oficina
from apps.reportes.models import ReporteGenerado
from apps.core.models import UserProfile


class Command(BaseCommand):
    help = 'Configura grupos de usuarios y permisos del sistema'

    def handle(self, *args, **options):
        self.stdout.write('Configurando grupos y permisos...')
        
        # Crear grupos
        grupos = {
            'Administrador': {
                'description': 'Acceso completo al sistema',
                'permissions': [
                    # Bienes patrimoniales
                    'add_bienpatrimonial',
                    'change_bienpatrimonial',
                    'delete_bienpatrimonial',
                    'view_bienpatrimonial',
                    
                    # Catálogo
                    'add_catalogo',
                    'change_catalogo',
                    'delete_catalogo',
                    'view_catalogo',
                    
                    # Oficinas
                    'add_oficina',
                    'change_oficina',
                    'delete_oficina',
                    'view_oficina',
                    
                    # Reportes
                    'add_reportegenerado',
                    'change_reportegenerado',
                    'delete_reportegenerado',
                    'view_reportegenerado',
                    
                    # Usuarios
                    'add_user',
                    'change_user',
                    'delete_user',
                    'view_user',
                    'add_userprofile',
                    'change_userprofile',
                    'delete_userprofile',
                    'view_userprofile',
                ]
            },
            'Funcionario': {
                'description': 'Gestión de inventario y reportes',
                'permissions': [
                    # Bienes patrimoniales
                    'add_bienpatrimonial',
                    'change_bienpatrimonial',
                    'view_bienpatrimonial',
                    
                    # Catálogo (solo lectura)
                    'view_catalogo',
                    
                    # Oficinas (solo lectura)
                    'view_oficina',
                    
                    # Reportes
                    'add_reportegenerado',
                    'view_reportegenerado',
                ]
            },
            'Auditor': {
                'description': 'Acceso de lectura y generación de reportes',
                'permissions': [
                    # Bienes patrimoniales (solo lectura)
                    'view_bienpatrimonial',
                    
                    # Catálogo (solo lectura)
                    'view_catalogo',
                    
                    # Oficinas (solo lectura)
                    'view_oficina',
                    
                    # Reportes
                    'add_reportegenerado',
                    'view_reportegenerado',
                ]
            },
            'Consulta': {
                'description': 'Solo consulta de información',
                'permissions': [
                    # Bienes patrimoniales (solo lectura)
                    'view_bienpatrimonial',
                    
                    # Catálogo (solo lectura)
                    'view_catalogo',
                    
                    # Oficinas (solo lectura)
                    'view_oficina',
                    
                    # Reportes (solo lectura)
                    'view_reportegenerado',
                ]
            }
        }

        # Crear permisos personalizados
        custom_permissions = [
            ('can_import_data', 'Puede importar datos desde Excel'),
            ('can_export_data', 'Puede exportar datos'),
            ('can_generate_qr', 'Puede generar códigos QR'),
            ('can_print_stickers', 'Puede imprimir stickers'),
            ('can_update_mobile', 'Puede actualizar desde móvil'),
            ('can_manage_users', 'Puede gestionar usuarios'),
            ('can_view_audit_logs', 'Puede ver registros de auditoría'),
        ]

        # Obtener content type para permisos personalizados
        content_type = ContentType.objects.get_for_model(BienPatrimonial)

        # Crear permisos personalizados
        for codename, name in custom_permissions:
            permission, created = Permission.objects.get_or_create(
                codename=codename,
                content_type=content_type,
                defaults={'name': name}
            )
            if created:
                self.stdout.write(f'  Creado permiso personalizado: {name}')

        # Crear grupos y asignar permisos
        for grupo_name, grupo_data in grupos.items():
            grupo, created = Group.objects.get_or_create(name=grupo_name)
            if created:
                self.stdout.write(f'  Creado grupo: {grupo_name}')
            else:
                self.stdout.write(f'  Grupo existente: {grupo_name}')

            # Limpiar permisos existentes
            grupo.permissions.clear()

            # Asignar permisos básicos
            for perm_codename in grupo_data['permissions']:
                try:
                    permission = Permission.objects.get(codename=perm_codename)
                    grupo.permissions.add(permission)
                except Permission.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f'    Permiso no encontrado: {perm_codename}')
                    )

            # Asignar permisos personalizados según el grupo
            if grupo_name == 'Administrador':
                # Administradores tienen todos los permisos personalizados
                for codename, _ in custom_permissions:
                    try:
                        permission = Permission.objects.get(codename=codename)
                        grupo.permissions.add(permission)
                    except Permission.DoesNotExist:
                        pass

            elif grupo_name == 'Funcionario':
                # Funcionarios pueden importar, exportar, generar QR y actualizar móvil
                funcionario_perms = [
                    'can_import_data', 'can_export_data', 
                    'can_generate_qr', 'can_print_stickers', 
                    'can_update_mobile'
                ]
                for codename in funcionario_perms:
                    try:
                        permission = Permission.objects.get(codename=codename)
                        grupo.permissions.add(permission)
                    except Permission.DoesNotExist:
                        pass

            elif grupo_name == 'Auditor':
                # Auditores pueden exportar y ver logs de auditoría
                auditor_perms = ['can_export_data', 'can_view_audit_logs']
                for codename in auditor_perms:
                    try:
                        permission = Permission.objects.get(codename=codename)
                        grupo.permissions.add(permission)
                    except Permission.DoesNotExist:
                        pass

            self.stdout.write(f'    Asignados {grupo.permissions.count()} permisos')

        self.stdout.write(
            self.style.SUCCESS('Configuración de grupos y permisos completada')
        )

        # Mostrar resumen
        self.stdout.write('\nResumen de grupos creados:')
        for grupo in Group.objects.all():
            self.stdout.write(f'  - {grupo.name}: {grupo.permissions.count()} permisos')