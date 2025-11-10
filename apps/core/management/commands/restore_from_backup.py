"""
Comando de management para restaurar elementos desde un backup de emergencia
Permite restaurar elementos eliminados permanentemente usando datos de auditoría
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from apps.core.models import AuditLog, RecycleBin
import json
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Restaura elementos desde backup de emergencia usando logs de auditoría'

    def add_arguments(self, parser):
        parser.add_argument(
            '--audit-log-id',
            type=int,
            help='ID del log de auditoría a restaurar',
        )
        parser.add_argument(
            '--date-from',
            type=str,
            help='Fecha desde (formato: YYYY-MM-DD) para buscar eliminaciones',
        )
        parser.add_argument(
            '--date-to',
            type=str,
            help='Fecha hasta (formato: YYYY-MM-DD) para buscar eliminaciones',
        )
        parser.add_argument(
            '--module',
            type=str,
            choices=['oficinas', 'bienes', 'catalogo', 'core'],
            help='Módulo específico a restaurar',
        )
        parser.add_argument(
            '--user',
            type=str,
            help='Usuario que eliminó los elementos',
        )
        parser.add_argument(
            '--list-only',
            action='store_true',
            help='Solo listar elementos disponibles para restaurar sin restaurarlos',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar restauración incluso si hay conflictos',
        )
        parser.add_argument(
            '--recreate-recycle-entry',
            action='store_true',
            help='Recrear entrada en RecycleBin para elementos restaurados',
        )

    def handle(self, *args, **options):
        audit_log_id = options['audit_log_id']
        date_from = options['date_from']
        date_to = options['date_to']
        module_filter = options['module']
        user_filter = options['user']
        list_only = options['list_only']
        force = options['force']
        recreate_recycle = options['recreate_recycle_entry']

        self.stdout.write(self.style.SUCCESS('=== Restauración desde Backup de Emergencia ==='))
        
        if list_only:
            self.stdout.write(self.style.WARNING('MODO LISTA: Solo se mostrarán elementos disponibles'))

        # Construir queryset de logs de auditoría
        queryset = AuditLog.objects.filter(action='delete')

        # Aplicar filtros
        if audit_log_id:
            queryset = queryset.filter(id=audit_log_id)
            self.stdout.write(f'Filtrando por audit log ID: {audit_log_id}')
        
        if date_from:
            try:
                from datetime import datetime
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
                queryset = queryset.filter(timestamp__gte=date_from_obj)
                self.stdout.write(f'Filtrando desde: {date_from}')
            except ValueError:
                raise CommandError('Formato de fecha inválido. Use YYYY-MM-DD')
        
        if date_to:
            try:
                from datetime import datetime
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
                queryset = queryset.filter(timestamp__lte=date_to_obj)
                self.stdout.write(f'Filtrando hasta: {date_to}')
            except ValueError:
                raise CommandError('Formato de fecha inválido. Use YYYY-MM-DD')
        
        if module_filter:
            queryset = queryset.filter(changes__module_name=module_filter)
            self.stdout.write(f'Filtrando por módulo: {module_filter}')
        
        if user_filter:
            queryset = queryset.filter(user__username=user_filter)
            self.stdout.write(f'Filtrando por usuario: {user_filter}')

        # Ordenar por fecha descendente
        queryset = queryset.order_by('-timestamp')

        total_logs = queryset.count()
        
        if total_logs == 0:
            self.stdout.write(self.style.WARNING('No se encontraron logs de auditoría que coincidan con los criterios'))
            return

        self.stdout.write(f'\nLogs de auditoría encontrados: {total_logs}')
        
        if list_only:
            self._listar_elementos(queryset)
            return

        # Confirmar antes de proceder
        if not force and total_logs > 10:
            self.stdout.write(
                self.style.WARNING(
                    f'\n⚠ Se encontraron {total_logs} elementos para restaurar. '
                    'Use --force para confirmar la operación.'
                )
            )
            return

        # Procesar restauración
        restaurados = 0
        errores = 0
        
        for log in queryset:
            try:
                resultado = self._restaurar_desde_log(log, force, recreate_recycle)
                if resultado:
                    restaurados += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✓ Restaurado: {log.object_repr}')
                    )
                else:
                    errores += 1
                    self.stdout.write(
                        self.style.WARNING(f'  ⚠ No se pudo restaurar: {log.object_repr}')
                    )
            except Exception as e:
                errores += 1
                logger.error(f'Error restaurando {log.object_repr}: {str(e)}')
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Error: {log.object_repr} - {str(e)}')
                )

        # Resumen
        self.stdout.write('\n' + '='*50)
        self.stdout.write(f'Elementos restaurados: {restaurados}')
        self.stdout.write(f'Errores: {errores}')
        self.stdout.write(self.style.SUCCESS('\n=== Restauración completada ==='))

    def _listar_elementos(self, queryset):
        """Lista elementos disponibles para restaurar"""
        self.stdout.write('\n' + '='*70)
        self.stdout.write('ELEMENTOS DISPONIBLES PARA RESTAURAR:')
        self.stdout.write('='*70)
        
        for log in queryset[:50]:  # Limitar a 50 para no saturar
            changes = log.changes if isinstance(log.changes, dict) else {}
            module_name = changes.get('module_name', 'desconocido')
            deleted_by = changes.get('deleted_by', 'desconocido')
            tipo = changes.get('tipo', 'eliminacion_manual')
            
            self.stdout.write(
                f'\nID: {log.id} | {log.timestamp.strftime("%Y-%m-%d %H:%M")}'
            )
            self.stdout.write(f'  Objeto: {log.object_repr}')
            self.stdout.write(f'  Modelo: {log.model_name}')
            self.stdout.write(f'  Módulo: {module_name}')
            self.stdout.write(f'  Eliminado por: {deleted_by}')
            self.stdout.write(f'  Tipo: {tipo}')
            
            if 'snapshot' in changes:
                self.stdout.write('  ✓ Tiene snapshot de datos')
        
        if queryset.count() > 50:
            self.stdout.write(f'\n... y {queryset.count() - 50} elementos más')
        
        self.stdout.write('\n' + '='*70)
        self.stdout.write('Use --audit-log-id <ID> para restaurar un elemento específico')
        self.stdout.write('='*70)

    @transaction.atomic
    def _restaurar_desde_log(self, log, force=False, recreate_recycle=False):
        """
        Intenta restaurar un elemento desde un log de auditoría
        
        Args:
            log: AuditLog instance
            force: Forzar restauración incluso con conflictos
            recreate_recycle: Recrear entrada en RecycleBin
            
        Returns:
            bool: True si se restauró exitosamente
        """
        changes = log.changes if isinstance(log.changes, dict) else {}
        
        # Verificar si tiene snapshot de datos
        if 'snapshot' not in changes:
            logger.warning(f'Log {log.id} no tiene snapshot de datos')
            if not force:
                return False
        
        # Obtener el ContentType
        try:
            content_type = ContentType.objects.get(model=log.model_name.lower())
            model_class = content_type.model_class()
        except ContentType.DoesNotExist:
            logger.error(f'No se encontró ContentType para modelo: {log.model_name}')
            return False
        
        # Verificar si el objeto ya existe
        try:
            existing_obj = model_class.all_objects.get(pk=log.object_id)
            
            # Si existe y está eliminado, restaurarlo
            if hasattr(existing_obj, 'is_deleted') and existing_obj.is_deleted:
                existing_obj.restore()
                logger.info(f'Objeto {log.object_repr} restaurado desde soft delete')
                
                if recreate_recycle:
                    self._recrear_entrada_recycle_bin(existing_obj, log, changes)
                
                return True
            else:
                logger.warning(f'Objeto {log.object_repr} ya existe y no está eliminado')
                return False
                
        except model_class.DoesNotExist:
            # El objeto no existe, intentar recrearlo desde snapshot
            if 'snapshot' in changes and force:
                logger.info(f'Intentando recrear objeto {log.object_repr} desde snapshot')
                # Nota: La recreación desde snapshot requiere lógica específica por modelo
                # que debería implementarse según las necesidades del negocio
                logger.warning('Recreación desde snapshot no implementada completamente')
                return False
        
        return False

    def _recrear_entrada_recycle_bin(self, obj, log, changes):
        """Recrea una entrada en RecycleBin para el objeto restaurado"""
        try:
            module_name = changes.get('module_name', 'core')
            deleted_by_username = changes.get('deleted_by', None)
            
            # Obtener usuario
            from django.contrib.auth.models import User
            deleted_by = None
            if deleted_by_username:
                try:
                    deleted_by = User.objects.get(username=deleted_by_username)
                except User.DoesNotExist:
                    pass
            
            # Crear entrada en RecycleBin
            RecycleBin.objects.create(
                content_object=obj,
                object_repr=str(obj),
                module_name=module_name,
                deleted_by=deleted_by,
                deletion_reason=f'Restaurado desde backup (audit log {log.id})',
                restored_at=timezone.now(),
                restored_by=None
            )
            
            logger.info(f'Entrada RecycleBin recreada para {obj}')
            
        except Exception as e:
            logger.error(f'Error recreando entrada RecycleBin: {str(e)}')
