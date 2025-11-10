"""
Comando de management para configurar grupos de permisos de papelera de reciclaje.

Este comando crea y configura grupos de permisos predefinidos para diferentes roles:
- Administrador: Todos los permisos
- Funcionario: Permisos de visualización y restauración de propios elementos
- Auditor: Permisos de solo visualización
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from apps.core.models import RecycleBin, RecycleBinConfig, DeletionAuditLog


class Command(BaseCommand):
    help = 'Configura grupos de permisos para el sistema de papelera de reciclaje'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Elimina y recrea los grupos de permisos',
        )
    
    def handle(self, *args, **options):
        reset = options.get('reset', False)
        
        if reset:
            self.stdout.write(self.style.WARNING('Eliminando grupos existentes...'))
            Group.objects.filter(name__in=[
                'Recycle Bin - Administrador',
                'Recycle Bin - Funcionario',
                'Recycle Bin - Auditor'
            ]).delete()
        
        self.stdout.write('Configurando grupos de permisos de papelera...')
        
        # Obtener content types
        recycle_bin_ct = ContentType.objects.get_for_model(RecycleBin)
        recycle_config_ct = ContentType.objects.get_for_model(RecycleBinConfig)
        audit_log_ct = ContentType.objects.get_for_model(DeletionAuditLog)
        
        # ====================================================================
        # GRUPO: ADMINISTRADOR
        # ====================================================================
        admin_group, created = Group.objects.get_or_create(
            name='Recycle Bin - Administrador'
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Grupo "Administrador" creado'))
        else:
            self.stdout.write('  Grupo "Administrador" ya existe')
        
        # Permisos de RecycleBin
        admin_permissions = [
            Permission.objects.get_or_create(
                codename='view_recyclebin',
                name='Can view recycle bin',
                content_type=recycle_bin_ct
            )[0],
            Permission.objects.get_or_create(
                codename='view_all_recyclebin',
                name='Can view all recycle bin items',
                content_type=recycle_bin_ct
            )[0],
            Permission.objects.get_or_create(
                codename='restore_recyclebin',
                name='Can restore items from recycle bin',
                content_type=recycle_bin_ct
            )[0],
            Permission.objects.get_or_create(
                codename='restore_own_recyclebin',
                name='Can restore own items from recycle bin',
                content_type=recycle_bin_ct
            )[0],
            Permission.objects.get_or_create(
                codename='restore_others_recyclebin',
                name='Can restore others items from recycle bin',
                content_type=recycle_bin_ct
            )[0],
            Permission.objects.get_or_create(
                codename='permanent_delete_recyclebin',
                name='Can permanently delete items from recycle bin',
                content_type=recycle_bin_ct
            )[0],
            Permission.objects.get_or_create(
                codename='bulk_restore_recyclebin',
                name='Can bulk restore items from recycle bin',
                content_type=recycle_bin_ct
            )[0],
            Permission.objects.get_or_create(
                codename='bulk_delete_recyclebin',
                name='Can bulk permanently delete items from recycle bin',
                content_type=recycle_bin_ct
            )[0],
        ]
        
        # Permisos de RecycleBinConfig
        admin_permissions.extend([
            Permission.objects.get_or_create(
                codename='view_recyclebinconfig',
                name='Can view recycle bin configuration',
                content_type=recycle_config_ct
            )[0],
            Permission.objects.get_or_create(
                codename='change_recyclebinconfig',
                name='Can change recycle bin configuration',
                content_type=recycle_config_ct
            )[0],
        ])
        
        # Permisos de DeletionAuditLog
        admin_permissions.extend([
            Permission.objects.get_or_create(
                codename='view_deletionauditlog',
                name='Can view deletion audit logs',
                content_type=audit_log_ct
            )[0],
        ])
        
        admin_group.permissions.set(admin_permissions)
        self.stdout.write(self.style.SUCCESS(
            f'  ✓ {len(admin_permissions)} permisos asignados a Administrador'
        ))
        
        # ====================================================================
        # GRUPO: FUNCIONARIO
        # ====================================================================
        func_group, created = Group.objects.get_or_create(
            name='Recycle Bin - Funcionario'
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Grupo "Funcionario" creado'))
        else:
            self.stdout.write('  Grupo "Funcionario" ya existe')
        
        # Permisos limitados para funcionario
        func_permissions = [
            Permission.objects.get_or_create(
                codename='view_recyclebin',
                name='Can view recycle bin',
                content_type=recycle_bin_ct
            )[0],
            Permission.objects.get_or_create(
                codename='restore_recyclebin',
                name='Can restore items from recycle bin',
                content_type=recycle_bin_ct
            )[0],
            Permission.objects.get_or_create(
                codename='restore_own_recyclebin',
                name='Can restore own items from recycle bin',
                content_type=recycle_bin_ct
            )[0],
            Permission.objects.get_or_create(
                codename='bulk_restore_recyclebin',
                name='Can bulk restore items from recycle bin',
                content_type=recycle_bin_ct
            )[0],
        ]
        
        func_group.permissions.set(func_permissions)
        self.stdout.write(self.style.SUCCESS(
            f'  ✓ {len(func_permissions)} permisos asignados a Funcionario'
        ))
        
        # ====================================================================
        # GRUPO: AUDITOR
        # ====================================================================
        auditor_group, created = Group.objects.get_or_create(
            name='Recycle Bin - Auditor'
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Grupo "Auditor" creado'))
        else:
            self.stdout.write('  Grupo "Auditor" ya existe')
        
        # Permisos de solo visualización para auditor
        auditor_permissions = [
            Permission.objects.get_or_create(
                codename='view_recyclebin',
                name='Can view recycle bin',
                content_type=recycle_bin_ct
            )[0],
            Permission.objects.get_or_create(
                codename='view_all_recyclebin',
                name='Can view all recycle bin items',
                content_type=recycle_bin_ct
            )[0],
            Permission.objects.get_or_create(
                codename='view_deletionauditlog',
                name='Can view deletion audit logs',
                content_type=audit_log_ct
            )[0],
            Permission.objects.get_or_create(
                codename='view_recyclebinconfig',
                name='Can view recycle bin configuration',
                content_type=recycle_config_ct
            )[0],
        ]
        
        auditor_group.permissions.set(auditor_permissions)
        self.stdout.write(self.style.SUCCESS(
            f'  ✓ {len(auditor_permissions)} permisos asignados a Auditor'
        ))
        
        # ====================================================================
        # RESUMEN
        # ====================================================================
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('Configuración de permisos completada'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write('')
        self.stdout.write('Grupos creados:')
        self.stdout.write(f'  • Recycle Bin - Administrador ({len(admin_permissions)} permisos)')
        self.stdout.write(f'  • Recycle Bin - Funcionario ({len(func_permissions)} permisos)')
        self.stdout.write(f'  • Recycle Bin - Auditor ({len(auditor_permissions)} permisos)')
        self.stdout.write('')
        self.stdout.write('Para asignar usuarios a estos grupos, use:')
        self.stdout.write('  python manage.py assign_recycle_permissions <username> <role>')
        self.stdout.write('')
