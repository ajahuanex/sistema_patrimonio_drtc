"""
Comando de management para limpiar la papelera de reciclaje
Elimina permanentemente elementos que han excedido su tiempo de retención
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from apps.core.models import RecycleBin, RecycleBinConfig, AuditLog
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Limpia la papelera de reciclaje eliminando permanentemente elementos que han excedido su tiempo de retención'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra qué elementos se eliminarían sin eliminarlos realmente',
        )
        parser.add_argument(
            '--module',
            type=str,
            help='Limpia solo elementos de un módulo específico (oficinas, bienes, catalogo, core)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Fuerza la eliminación incluso si auto_delete_enabled está deshabilitado',
        )
        parser.add_argument(
            '--days',
            type=int,
            help='Sobrescribe los días de retención configurados',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        module_filter = options['module']
        force = options['force']
        override_days = options['days']

        self.stdout.write(self.style.SUCCESS('=== Iniciando limpieza de papelera de reciclaje ==='))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('MODO DRY-RUN: No se eliminarán elementos realmente'))
        
        # Obtener elementos listos para eliminación automática
        queryset = RecycleBin.objects.filter(
            restored_at__isnull=True,  # No restaurados
            auto_delete_at__lte=timezone.now()  # Tiempo de eliminación alcanzado
        )
        
        # Filtrar por módulo si se especificó
        if module_filter:
            queryset = queryset.filter(module_name=module_filter)
            self.stdout.write(f'Filtrando por módulo: {module_filter}')
        
        total_elementos = queryset.count()
        
        if total_elementos == 0:
            self.stdout.write(self.style.SUCCESS('No hay elementos para eliminar'))
            return
        
        self.stdout.write(f'Elementos encontrados para eliminación: {total_elementos}')
        
        # Agrupar por módulo para mostrar estadísticas
        modulos = queryset.values('module_name').distinct()
        
        for modulo_data in modulos:
            module_name = modulo_data['module_name']
            elementos_modulo = queryset.filter(module_name=module_name)
            count = elementos_modulo.count()
            
            self.stdout.write(f'\n{module_name}: {count} elementos')
            
            # Verificar configuración del módulo
            try:
                config = RecycleBinConfig.objects.get(module_name=module_name)
                
                if not config.auto_delete_enabled and not force:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  ⚠ Eliminación automática deshabilitada para {module_name}. '
                            f'Use --force para eliminar de todas formas.'
                        )
                    )
                    continue
                
                retention_days = override_days if override_days else config.retention_days
                self.stdout.write(f'  Días de retención: {retention_days}')
                
            except RecycleBinConfig.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(
                        f'  ⚠ No hay configuración para {module_name}, usando valores por defecto'
                    )
                )
            
            # Procesar eliminación
            if not dry_run:
                eliminados = self._eliminar_elementos(elementos_modulo)
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Eliminados: {eliminados} elementos')
                )
            else:
                # En dry-run, mostrar algunos ejemplos
                ejemplos = elementos_modulo[:5]
                for item in ejemplos:
                    dias_en_papelera = (timezone.now() - item.deleted_at).days
                    self.stdout.write(
                        f'    - {item.object_repr} (ID: {item.object_id}, '
                        f'{dias_en_papelera} días en papelera)'
                    )
                if elementos_modulo.count() > 5:
                    self.stdout.write(f'    ... y {elementos_modulo.count() - 5} más')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'\nDRY-RUN: Se eliminarían {total_elementos} elementos en total'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n=== Limpieza completada: {total_elementos} elementos eliminados ==='
                )
            )

    @transaction.atomic
    def _eliminar_elementos(self, queryset):
        """
        Elimina permanentemente los elementos del queryset
        
        Args:
            queryset: QuerySet de RecycleBin a eliminar
            
        Returns:
            int: Número de elementos eliminados
        """
        eliminados = 0
        recycle_bin_ids = []
        
        for item in queryset:
            try:
                # Guardar ID para notificación posterior
                recycle_bin_ids.append(item.id)
                
                # Obtener el objeto real antes de eliminarlo
                obj = item.content_object
                
                if obj:
                    # Registrar en auditoría antes de eliminar
                    AuditLog.objects.create(
                        user_id=1,  # Sistema
                        action='delete',
                        model_name=item.content_type.model,
                        object_id=str(item.object_id),
                        object_repr=item.object_repr,
                        changes={
                            'tipo': 'eliminacion_automatica',
                            'dias_en_papelera': (timezone.now() - item.deleted_at).days,
                            'module_name': item.module_name,
                            'deleted_by': item.deleted_by.username if item.deleted_by else 'Sistema',
                            'deletion_reason': item.deletion_reason
                        }
                    )
                    
                    # Eliminar permanentemente el objeto
                    obj.hard_delete()
                    
                    logger.info(
                        f'Eliminado permanentemente: {item.object_repr} '
                        f'(módulo: {item.module_name}, ID: {item.object_id})'
                    )
                
                # Eliminar entrada de RecycleBin
                item.delete()
                eliminados += 1
                
            except Exception as e:
                logger.error(
                    f'Error eliminando {item.object_repr} (ID: {item.object_id}): {str(e)}'
                )
                self.stdout.write(
                    self.style.ERROR(
                        f'  ✗ Error eliminando {item.object_repr}: {str(e)}'
                    )
                )
                continue
        
        # Enviar notificaciones de eliminación automática
        if recycle_bin_ids:
            try:
                from apps.notificaciones.tasks import notificar_eliminacion_automatica
                notificar_eliminacion_automatica.delay(recycle_bin_ids)
                logger.info(f'Notificaciones de eliminación programadas para {len(recycle_bin_ids)} elementos')
            except Exception as e:
                logger.warning(f'No se pudieron programar notificaciones: {str(e)}')
        
        return eliminados
