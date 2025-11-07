from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from apps.core.models import RecycleBinConfig


class Command(BaseCommand):
    help = 'Configura la configuración inicial del sistema de papelera de reciclaje'

    def add_arguments(self, parser):
        parser.add_argument(
            '--retention-days',
            type=int,
            default=30,
            help='Días de retención por defecto (default: 30)'
        )
        parser.add_argument(
            '--warning-days',
            type=int,
            default=7,
            help='Días de advertencia antes de eliminación (default: 7)'
        )
        parser.add_argument(
            '--final-warning-days',
            type=int,
            default=1,
            help='Días de advertencia final (default: 1)'
        )
        parser.add_argument(
            '--disable-auto-delete',
            action='store_true',
            help='Deshabilitar eliminación automática'
        )
        parser.add_argument(
            '--disable-restore-own',
            action='store_true',
            help='Deshabilitar restauración de elementos propios'
        )
        parser.add_argument(
            '--enable-restore-others',
            action='store_true',
            help='Habilitar restauración de elementos de otros usuarios'
        )
        parser.add_argument(
            '--module',
            choices=['oficinas', 'bienes', 'catalogo', 'core'],
            help='Configurar solo un módulo específico'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Sobrescribir configuraciones existentes'
        )

    def handle(self, *args, **options):
        retention_days = options['retention_days']
        warning_days = options['warning_days']
        final_warning_days = options['final_warning_days']
        auto_delete_enabled = not options['disable_auto_delete']
        can_restore_own = not options['disable_restore_own']
        can_restore_others = options['enable_restore_others']
        target_module = options['module']
        force = options['force']

        # Validar argumentos
        if retention_days <= 0:
            raise CommandError('Los días de retención deben ser mayor a 0')
        
        if warning_days >= retention_days:
            raise CommandError('Los días de advertencia deben ser menores que los días de retención')
        
        if final_warning_days >= warning_days:
            raise CommandError('Los días de advertencia final deben ser menores que los días de advertencia')
        
        if final_warning_days <= 0:
            raise CommandError('Los días de advertencia final deben ser mayor a 0')

        # Determinar módulos a configurar
        modules_to_configure = [target_module] if target_module else ['oficinas', 'bienes', 'catalogo', 'core']

        created_count = 0
        updated_count = 0

        for module_name in modules_to_configure:
            config, created = RecycleBinConfig.objects.get_or_create(
                module_name=module_name,
                defaults={
                    'retention_days': retention_days,
                    'auto_delete_enabled': auto_delete_enabled,
                    'warning_days_before': warning_days,
                    'final_warning_days_before': final_warning_days,
                    'can_restore_own': can_restore_own,
                    'can_restore_others': can_restore_others,
                }
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Configuración creada para módulo: {module_name}')
                )
            elif force:
                # Actualizar configuración existente
                config.retention_days = retention_days
                config.auto_delete_enabled = auto_delete_enabled
                config.warning_days_before = warning_days
                config.final_warning_days_before = final_warning_days
                config.can_restore_own = can_restore_own
                config.can_restore_others = can_restore_others
                config.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'⚠ Configuración actualizada para módulo: {module_name}')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'✗ Configuración ya existe para módulo: {module_name} (usar --force para sobrescribir)')
                )

        # Resumen
        self.stdout.write('\n' + '='*50)
        self.stdout.write(f'Configuraciones creadas: {created_count}')
        self.stdout.write(f'Configuraciones actualizadas: {updated_count}')
        
        if created_count > 0 or updated_count > 0:
            self.stdout.write('\nConfiguración aplicada:')
            self.stdout.write(f'  - Días de retención: {retention_days}')
            self.stdout.write(f'  - Eliminación automática: {"Habilitada" if auto_delete_enabled else "Deshabilitada"}')
            self.stdout.write(f'  - Días de advertencia: {warning_days}')
            self.stdout.write(f'  - Días de advertencia final: {final_warning_days}')
            self.stdout.write(f'  - Restaurar propios: {"Habilitado" if can_restore_own else "Deshabilitado"}')
            self.stdout.write(f'  - Restaurar de otros: {"Habilitado" if can_restore_others else "Deshabilitado"}')
        
        self.stdout.write('\n' + self.style.SUCCESS('Comando completado exitosamente'))