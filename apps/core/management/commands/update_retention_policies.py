"""
Comando de management para actualizar políticas de retención de forma masiva
Permite cambiar configuraciones de múltiples módulos simultáneamente
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction
from apps.core.models import RecycleBinConfig, RecycleBin, AuditLog
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Actualiza políticas de retención de la papelera de forma masiva'

    def add_arguments(self, parser):
        parser.add_argument(
            '--module',
            type=str,
            choices=['oficinas', 'bienes', 'catalogo', 'core', 'all'],
            default='all',
            help='Módulo a actualizar (all para todos)',
        )
        parser.add_argument(
            '--retention-days',
            type=int,
            help='Nuevos días de retención',
        )
        parser.add_argument(
            '--warning-days',
            type=int,
            help='Nuevos días de advertencia antes de eliminación',
        )
        parser.add_argument(
            '--final-warning-days',
            type=int,
            help='Nuevos días de advertencia final',
        )
        parser.add_argument(
            '--enable-auto-delete',
            action='store_true',
            help='Habilitar eliminación automática',
        )
        parser.add_argument(
            '--disable-auto-delete',
            action='store_true',
            help='Deshabilitar eliminación automática',
        )
        parser.add_argument(
            '--enable-restore-own',
            action='store_true',
            help='Habilitar restauración de elementos propios',
        )
        parser.add_argument(
            '--disable-restore-own',
            action='store_true',
            help='Deshabilitar restauración de elementos propios',
        )
        parser.add_argument(
            '--enable-restore-others',
            action='store_true',
            help='Habilitar restauración de elementos de otros',
        )
        parser.add_argument(
            '--disable-restore-others',
            action='store_true',
            help='Deshabilitar restauración de elementos de otros',
        )
        parser.add_argument(
            '--update-existing-items',
            action='store_true',
            help='Actualizar fechas de auto_delete_at de elementos existentes',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostrar cambios sin aplicarlos',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar actualización sin confirmación',
        )
        parser.add_argument(
            '--show-current',
            action='store_true',
            help='Mostrar configuraciones actuales y salir',
        )

    def handle(self, *args, **options):
        module = options['module']
        retention_days = options['retention_days']
        warning_days = options['warning_days']
        final_warning_days = options['final_warning_days']
        enable_auto_delete = options['enable_auto_delete']
        disable_auto_delete = options['disable_auto_delete']
        enable_restore_own = options['enable_restore_own']
        disable_restore_own = options['disable_restore_own']
        enable_restore_others = options['enable_restore_others']
        disable_restore_others = options['disable_restore_others']
        update_existing = options['update_existing_items']
        dry_run = options['dry_run']
        force = options['force']
        show_current = options['show_current']

        self.stdout.write(self.style.SUCCESS('=== Actualización de Políticas de Retención ==='))

        # Mostrar configuraciones actuales si se solicita
        if show_current:
            self._mostrar_configuraciones_actuales(module)
            return

        # Validar que se especificó al menos un cambio
        if not any([
            retention_days, warning_days, final_warning_days,
            enable_auto_delete, disable_auto_delete,
            enable_restore_own, disable_restore_own,
            enable_restore_others, disable_restore_others
        ]):
            raise CommandError(
                'Debe especificar al menos un parámetro a actualizar. '
                'Use --show-current para ver configuraciones actuales.'
            )

        # Validar conflictos
        if enable_auto_delete and disable_auto_delete:
            raise CommandError('No puede habilitar y deshabilitar auto-delete simultáneamente')
        
        if enable_restore_own and disable_restore_own:
            raise CommandError('No puede habilitar y deshabilitar restore-own simultáneamente')
        
        if enable_restore_others and disable_restore_others:
            raise CommandError('No puede habilitar y deshabilitar restore-others simultáneamente')

        # Validar días de retención
        if retention_days is not None and retention_days <= 0:
            raise CommandError('Los días de retención deben ser mayor a 0')
        
        if warning_days is not None and retention_days is not None and warning_days >= retention_days:
            raise CommandError('Los días de advertencia deben ser menores que los días de retención')
        
        if final_warning_days is not None and warning_days is not None and final_warning_days >= warning_days:
            raise CommandError('Los días de advertencia final deben ser menores que los días de advertencia')

        if dry_run:
            self.stdout.write(self.style.WARNING('MODO DRY-RUN: No se aplicarán cambios'))

        # Determinar módulos a actualizar
        if module == 'all':
            modules_to_update = ['oficinas', 'bienes', 'catalogo', 'core']
        else:
            modules_to_update = [module]

        self.stdout.write(f'\nMódulos a actualizar: {", ".join(modules_to_update)}')

        # Mostrar cambios a aplicar
        self._mostrar_cambios_propuestos(
            retention_days, warning_days, final_warning_days,
            enable_auto_delete, disable_auto_delete,
            enable_restore_own, disable_restore_own,
            enable_restore_others, disable_restore_others
        )

        # Confirmar si no es force
        if not force and not dry_run:
            self.stdout.write(
                self.style.WARNING(
                    '\n⚠ Esta operación actualizará las políticas de retención. '
                    'Use --force para confirmar.'
                )
            )
            return

        # Aplicar cambios
        updated_count = 0
        items_updated_count = 0

        for module_name in modules_to_update:
            try:
                config = RecycleBinConfig.objects.get(module_name=module_name)
                
                # Guardar valores anteriores para auditoría
                old_values = {
                    'retention_days': config.retention_days,
                    'auto_delete_enabled': config.auto_delete_enabled,
                    'warning_days_before': config.warning_days_before,
                    'final_warning_days_before': config.final_warning_days_before,
                    'can_restore_own': config.can_restore_own,
                    'can_restore_others': config.can_restore_others,
                }

                # Aplicar cambios
                changed = False
                
                if retention_days is not None:
                    config.retention_days = retention_days
                    changed = True
                
                if warning_days is not None:
                    config.warning_days_before = warning_days
                    changed = True
                
                if final_warning_days is not None:
                    config.final_warning_days_before = final_warning_days
                    changed = True
                
                if enable_auto_delete:
                    config.auto_delete_enabled = True
                    changed = True
                elif disable_auto_delete:
                    config.auto_delete_enabled = False
                    changed = True
                
                if enable_restore_own:
                    config.can_restore_own = True
                    changed = True
                elif disable_restore_own:
                    config.can_restore_own = False
                    changed = True
                
                if enable_restore_others:
                    config.can_restore_others = True
                    changed = True
                elif disable_restore_others:
                    config.can_restore_others = False
                    changed = True

                if changed and not dry_run:
                    config.save()
                    updated_count += 1
                    
                    # Registrar en auditoría
                    AuditLog.objects.create(
                        user_id=1,  # Sistema
                        action='update',
                        model_name='RecycleBinConfig',
                        object_id=str(config.id),
                        object_repr=f'Config {module_name}',
                        changes={
                            'old_values': old_values,
                            'new_values': {
                                'retention_days': config.retention_days,
                                'auto_delete_enabled': config.auto_delete_enabled,
                                'warning_days_before': config.warning_days_before,
                                'final_warning_days_before': config.final_warning_days_before,
                                'can_restore_own': config.can_restore_own,
                                'can_restore_others': config.can_restore_others,
                            }
                        }
                    )
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Configuración actualizada: {module_name}')
                    )
                    
                    # Actualizar elementos existentes si se solicita
                    if update_existing and retention_days is not None:
                        items_count = self._actualizar_elementos_existentes(
                            module_name, retention_days, dry_run
                        )
                        items_updated_count += items_count
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  ✓ Actualizados {items_count} elementos existentes'
                            )
                        )
                
                elif changed and dry_run:
                    self.stdout.write(
                        self.style.WARNING(f'[DRY-RUN] Se actualizaría: {module_name}')
                    )
                else:
                    self.stdout.write(f'Sin cambios para: {module_name}')

            except RecycleBinConfig.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(
                        f'✗ No existe configuración para módulo: {module_name}. '
                        f'Use setup_recycle_bin para crearla.'
                    )
                )

        # Resumen
        self.stdout.write('\n' + '='*50)
        if dry_run:
            self.stdout.write(f'[DRY-RUN] Se actualizarían {updated_count} configuraciones')
            if update_existing:
                self.stdout.write(f'[DRY-RUN] Se actualizarían {items_updated_count} elementos')
        else:
            self.stdout.write(f'Configuraciones actualizadas: {updated_count}')
            if update_existing:
                self.stdout.write(f'Elementos actualizados: {items_updated_count}')
        
        self.stdout.write(self.style.SUCCESS('\n=== Actualización completada ==='))

    def _mostrar_configuraciones_actuales(self, module_filter):
        """Muestra las configuraciones actuales"""
        self.stdout.write('\n' + '='*70)
        self.stdout.write('CONFIGURACIONES ACTUALES DE PAPELERA')
        self.stdout.write('='*70)

        configs = RecycleBinConfig.objects.all()
        
        if module_filter != 'all':
            configs = configs.filter(module_name=module_filter)

        for config in configs:
            self.stdout.write(f'\nMódulo: {config.module_name}')
            self.stdout.write('-'*70)
            self.stdout.write(f'  Días de retención: {config.retention_days}')
            self.stdout.write(f'  Eliminación automática: {"Habilitada" if config.auto_delete_enabled else "Deshabilitada"}')
            self.stdout.write(f'  Días de advertencia: {config.warning_days_before}')
            self.stdout.write(f'  Días de advertencia final: {config.final_warning_days_before}')
            self.stdout.write(f'  Restaurar propios: {"Habilitado" if config.can_restore_own else "Deshabilitado"}')
            self.stdout.write(f'  Restaurar de otros: {"Habilitado" if config.can_restore_others else "Deshabilitado"}')
            
            # Contar elementos en papelera
            items_count = RecycleBin.objects.filter(
                module_name=config.module_name,
                restored_at__isnull=True
            ).count()
            self.stdout.write(f'  Elementos en papelera: {items_count}')

        self.stdout.write('\n' + '='*70)

    def _mostrar_cambios_propuestos(self, retention_days, warning_days, final_warning_days,
                                     enable_auto_delete, disable_auto_delete,
                                     enable_restore_own, disable_restore_own,
                                     enable_restore_others, disable_restore_others):
        """Muestra los cambios que se aplicarán"""
        self.stdout.write('\nCambios a aplicar:')
        self.stdout.write('-'*50)
        
        if retention_days is not None:
            self.stdout.write(f'  • Días de retención: {retention_days}')
        
        if warning_days is not None:
            self.stdout.write(f'  • Días de advertencia: {warning_days}')
        
        if final_warning_days is not None:
            self.stdout.write(f'  • Días de advertencia final: {final_warning_days}')
        
        if enable_auto_delete:
            self.stdout.write('  • Eliminación automática: HABILITAR')
        elif disable_auto_delete:
            self.stdout.write('  • Eliminación automática: DESHABILITAR')
        
        if enable_restore_own:
            self.stdout.write('  • Restaurar propios: HABILITAR')
        elif disable_restore_own:
            self.stdout.write('  • Restaurar propios: DESHABILITAR')
        
        if enable_restore_others:
            self.stdout.write('  • Restaurar de otros: HABILITAR')
        elif disable_restore_others:
            self.stdout.write('  • Restaurar de otros: DESHABILITAR')

    @transaction.atomic
    def _actualizar_elementos_existentes(self, module_name, new_retention_days, dry_run):
        """
        Actualiza las fechas auto_delete_at de elementos existentes
        
        Args:
            module_name: Nombre del módulo
            new_retention_days: Nuevos días de retención
            dry_run: Si es True, no aplica cambios
            
        Returns:
            int: Número de elementos actualizados
        """
        # Obtener elementos activos en papelera
        items = RecycleBin.objects.filter(
            module_name=module_name,
            restored_at__isnull=True
        )

        updated_count = 0

        for item in items:
            # Calcular nueva fecha de auto-eliminación
            new_auto_delete_at = item.deleted_at + timedelta(days=new_retention_days)
            
            if item.auto_delete_at != new_auto_delete_at:
                if not dry_run:
                    item.auto_delete_at = new_auto_delete_at
                    item.save(update_fields=['auto_delete_at'])
                
                updated_count += 1
                
                logger.info(
                    f'Actualizada fecha auto_delete_at para {item.object_repr}: '
                    f'{item.auto_delete_at} -> {new_auto_delete_at}'
                )

        return updated_count
