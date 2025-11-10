"""
Comando de management para generar reportes de auditoría de la papelera de reciclaje
Genera reportes detallados en formato JSON, CSV o texto plano
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db.models import Count, Q
from apps.core.models import RecycleBin, AuditLog, RecycleBinConfig
from datetime import datetime, timedelta
import json
import csv
import os
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Genera reportes de auditoría de la papelera de reciclaje'

    def add_arguments(self, parser):
        parser.add_argument(
            '--format',
            type=str,
            choices=['json', 'csv', 'txt'],
            default='txt',
            help='Formato del reporte (json, csv, txt)',
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Ruta del archivo de salida (opcional, por defecto imprime en consola)',
        )
        parser.add_argument(
            '--date-from',
            type=str,
            help='Fecha desde (formato: YYYY-MM-DD)',
        )
        parser.add_argument(
            '--date-to',
            type=str,
            help='Fecha hasta (formato: YYYY-MM-DD)',
        )
        parser.add_argument(
            '--module',
            type=str,
            choices=['oficinas', 'bienes', 'catalogo', 'core'],
            help='Filtrar por módulo específico',
        )
        parser.add_argument(
            '--user',
            type=str,
            help='Filtrar por usuario que eliminó',
        )
        parser.add_argument(
            '--include-restored',
            action='store_true',
            help='Incluir elementos restaurados en el reporte',
        )
        parser.add_argument(
            '--include-deleted',
            action='store_true',
            help='Incluir elementos eliminados permanentemente',
        )
        parser.add_argument(
            '--statistics-only',
            action='store_true',
            help='Generar solo estadísticas sin detalles de elementos',
        )
        parser.add_argument(
            '--audit-logs',
            action='store_true',
            help='Incluir logs de auditoría en el reporte',
        )

    def handle(self, *args, **options):
        output_format = options['format']
        output_file = options['output']
        date_from = options['date_from']
        date_to = options['date_to']
        module_filter = options['module']
        user_filter = options['user']
        include_restored = options['include_restored']
        include_deleted = options['include_deleted']
        statistics_only = options['statistics_only']
        include_audit = options['audit_logs']

        self.stdout.write(self.style.SUCCESS('=== Generando Reporte de Papelera de Reciclaje ==='))

        # Parsear fechas
        date_from_obj = None
        date_to_obj = None
        
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
                self.stdout.write(f'Desde: {date_from}')
            except ValueError:
                raise CommandError('Formato de fecha inválido. Use YYYY-MM-DD')
        
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
                self.stdout.write(f'Hasta: {date_to}')
            except ValueError:
                raise CommandError('Formato de fecha inválido. Use YYYY-MM-DD')

        # Generar reporte
        report_data = self._generar_datos_reporte(
            date_from_obj, date_to_obj, module_filter, user_filter,
            include_restored, include_deleted, statistics_only, include_audit
        )

        # Formatear y exportar
        if output_format == 'json':
            output_content = self._format_json(report_data)
        elif output_format == 'csv':
            output_content = self._format_csv(report_data)
        else:  # txt
            output_content = self._format_txt(report_data)

        # Guardar o imprimir
        if output_file:
            self._save_to_file(output_file, output_content, output_format)
            self.stdout.write(
                self.style.SUCCESS(f'\n✓ Reporte guardado en: {output_file}')
            )
        else:
            self.stdout.write('\n' + '='*70)
            self.stdout.write(output_content)
            self.stdout.write('='*70)

        self.stdout.write(self.style.SUCCESS('\n=== Reporte generado exitosamente ==='))

    def _generar_datos_reporte(self, date_from, date_to, module_filter, user_filter,
                                include_restored, include_deleted, statistics_only, include_audit):
        """Genera los datos del reporte"""
        
        # Construir queryset base
        queryset = RecycleBin.objects.all()

        # Aplicar filtros de fecha
        if date_from:
            queryset = queryset.filter(deleted_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(deleted_at__lte=date_to)
        
        # Filtrar por módulo
        if module_filter:
            queryset = queryset.filter(module_name=module_filter)
        
        # Filtrar por usuario
        if user_filter:
            queryset = queryset.filter(deleted_by__username=user_filter)

        # Filtrar por estado
        if not include_restored:
            queryset = queryset.filter(restored_at__isnull=True)
        
        # Estadísticas generales
        total_elementos = queryset.count()
        elementos_activos = queryset.filter(restored_at__isnull=True).count()
        elementos_restaurados = queryset.filter(restored_at__isnull=False).count()
        
        # Estadísticas por módulo
        stats_por_modulo = queryset.values('module_name').annotate(
            total=Count('id'),
            activos=Count('id', filter=Q(restored_at__isnull=True)),
            restaurados=Count('id', filter=Q(restored_at__isnull=False))
        ).order_by('-total')

        # Estadísticas por usuario
        stats_por_usuario = queryset.values('deleted_by__username').annotate(
            total=Count('id')
        ).order_by('-total')[:10]  # Top 10 usuarios

        # Elementos próximos a eliminarse
        now = timezone.now()
        proximos_eliminar = queryset.filter(
            restored_at__isnull=True,
            auto_delete_at__lte=now + timedelta(days=7),
            auto_delete_at__gte=now
        ).order_by('auto_delete_at')

        # Configuraciones de módulos
        configs = RecycleBinConfig.objects.all()

        report_data = {
            'metadata': {
                'fecha_generacion': timezone.now().isoformat(),
                'periodo': {
                    'desde': date_from.isoformat() if date_from else None,
                    'hasta': date_to.isoformat() if date_to else None,
                },
                'filtros': {
                    'modulo': module_filter,
                    'usuario': user_filter,
                    'incluye_restaurados': include_restored,
                    'incluye_eliminados': include_deleted,
                }
            },
            'estadisticas': {
                'total_elementos': total_elementos,
                'elementos_activos': elementos_activos,
                'elementos_restaurados': elementos_restaurados,
                'tasa_restauracion': round(
                    (elementos_restaurados / total_elementos * 100) if total_elementos > 0 else 0, 2
                ),
                'por_modulo': list(stats_por_modulo),
                'por_usuario': list(stats_por_usuario),
                'proximos_eliminar': proximos_eliminar.count(),
            },
            'configuraciones': [
                {
                    'modulo': config.module_name,
                    'dias_retencion': config.retention_days,
                    'auto_delete_enabled': config.auto_delete_enabled,
                    'warning_days': config.warning_days_before,
                }
                for config in configs
            ],
        }

        # Agregar detalles de elementos si no es solo estadísticas
        if not statistics_only:
            elementos_detalle = []
            for item in queryset[:1000]:  # Limitar a 1000 elementos
                elementos_detalle.append({
                    'id': item.id,
                    'objeto': item.object_repr,
                    'modulo': item.module_name,
                    'eliminado_por': item.deleted_by.username if item.deleted_by else None,
                    'fecha_eliminacion': item.deleted_at.isoformat() if item.deleted_at else None,
                    'motivo': item.deletion_reason,
                    'restaurado': item.restored_at is not None,
                    'fecha_restauracion': item.restored_at.isoformat() if item.restored_at else None,
                    'restaurado_por': item.restored_by.username if item.restored_by else None,
                    'auto_delete_at': item.auto_delete_at.isoformat() if item.auto_delete_at else None,
                    'dias_restantes': (item.auto_delete_at - now).days if item.auto_delete_at and item.auto_delete_at > now else 0,
                })
            
            report_data['elementos'] = elementos_detalle

        # Agregar logs de auditoría si se solicita
        if include_audit:
            audit_queryset = AuditLog.objects.filter(
                action__in=['delete', 'restore', 'permanent_delete']
            )
            
            if date_from:
                audit_queryset = audit_queryset.filter(timestamp__gte=date_from)
            if date_to:
                audit_queryset = audit_queryset.filter(timestamp__lte=date_to)
            
            audit_logs = []
            for log in audit_queryset[:500]:  # Limitar a 500 logs
                audit_logs.append({
                    'id': log.id,
                    'accion': log.action,
                    'usuario': log.user.username if log.user else None,
                    'timestamp': log.timestamp.isoformat(),
                    'modelo': log.model_name,
                    'objeto': log.object_repr,
                    'cambios': log.changes,
                })
            
            report_data['audit_logs'] = audit_logs

        # Agregar elementos próximos a eliminarse
        proximos_detalle = []
        for item in proximos_eliminar[:50]:
            dias_restantes = (item.auto_delete_at - now).days
            proximos_detalle.append({
                'objeto': item.object_repr,
                'modulo': item.module_name,
                'dias_restantes': dias_restantes,
                'fecha_eliminacion_automatica': item.auto_delete_at.isoformat(),
            })
        
        report_data['proximos_eliminar_detalle'] = proximos_detalle

        return report_data

    def _format_json(self, data):
        """Formatea el reporte como JSON"""
        return json.dumps(data, indent=2, ensure_ascii=False)

    def _format_csv(self, data):
        """Formatea el reporte como CSV"""
        import io
        output = io.StringIO()
        
        # Escribir estadísticas generales
        writer = csv.writer(output)
        writer.writerow(['ESTADÍSTICAS GENERALES'])
        writer.writerow(['Métrica', 'Valor'])
        writer.writerow(['Total Elementos', data['estadisticas']['total_elementos']])
        writer.writerow(['Elementos Activos', data['estadisticas']['elementos_activos']])
        writer.writerow(['Elementos Restaurados', data['estadisticas']['elementos_restaurados']])
        writer.writerow(['Tasa Restauración (%)', data['estadisticas']['tasa_restauracion']])
        writer.writerow([])
        
        # Estadísticas por módulo
        writer.writerow(['ESTADÍSTICAS POR MÓDULO'])
        writer.writerow(['Módulo', 'Total', 'Activos', 'Restaurados'])
        for stat in data['estadisticas']['por_modulo']:
            writer.writerow([
                stat['module_name'],
                stat['total'],
                stat['activos'],
                stat['restaurados']
            ])
        writer.writerow([])
        
        # Elementos (si existen)
        if 'elementos' in data:
            writer.writerow(['ELEMENTOS EN PAPELERA'])
            writer.writerow([
                'ID', 'Objeto', 'Módulo', 'Eliminado Por', 'Fecha Eliminación',
                'Restaurado', 'Días Restantes'
            ])
            for elem in data['elementos']:
                writer.writerow([
                    elem['id'],
                    elem['objeto'],
                    elem['modulo'],
                    elem['eliminado_por'],
                    elem['fecha_eliminacion'],
                    'Sí' if elem['restaurado'] else 'No',
                    elem['dias_restantes']
                ])
        
        return output.getvalue()

    def _format_txt(self, data):
        """Formatea el reporte como texto plano"""
        lines = []
        lines.append('='*70)
        lines.append('REPORTE DE PAPELERA DE RECICLAJE')
        lines.append('='*70)
        lines.append(f"Fecha de generación: {data['metadata']['fecha_generacion']}")
        
        if data['metadata']['periodo']['desde']:
            lines.append(f"Período: {data['metadata']['periodo']['desde']} - {data['metadata']['periodo']['hasta']}")
        
        lines.append('')
        lines.append('ESTADÍSTICAS GENERALES')
        lines.append('-'*70)
        lines.append(f"Total de elementos: {data['estadisticas']['total_elementos']}")
        lines.append(f"Elementos activos en papelera: {data['estadisticas']['elementos_activos']}")
        lines.append(f"Elementos restaurados: {data['estadisticas']['elementos_restaurados']}")
        lines.append(f"Tasa de restauración: {data['estadisticas']['tasa_restauracion']}%")
        lines.append(f"Próximos a eliminarse: {data['estadisticas']['proximos_eliminar']}")
        
        lines.append('')
        lines.append('ESTADÍSTICAS POR MÓDULO')
        lines.append('-'*70)
        for stat in data['estadisticas']['por_modulo']:
            lines.append(
                f"  {stat['module_name']}: {stat['total']} total "
                f"({stat['activos']} activos, {stat['restaurados']} restaurados)"
            )
        
        lines.append('')
        lines.append('ESTADÍSTICAS POR USUARIO')
        lines.append('-'*70)
        for stat in data['estadisticas']['por_usuario']:
            username = stat['deleted_by__username'] or 'Sin usuario'
            lines.append(f"  {username}: {stat['total']} eliminaciones")
        
        lines.append('')
        lines.append('CONFIGURACIONES DE MÓDULOS')
        lines.append('-'*70)
        for config in data['configuraciones']:
            lines.append(
                f"  {config['modulo']}: {config['dias_retencion']} días retención, "
                f"Auto-delete: {'Sí' if config['auto_delete_enabled'] else 'No'}"
            )
        
        if data.get('proximos_eliminar_detalle'):
            lines.append('')
            lines.append('ELEMENTOS PRÓXIMOS A ELIMINARSE (7 días)')
            lines.append('-'*70)
            for item in data['proximos_eliminar_detalle']:
                lines.append(
                    f"  {item['objeto']} ({item['modulo']}) - "
                    f"{item['dias_restantes']} días restantes"
                )
        
        if 'elementos' in data and data['elementos']:
            lines.append('')
            lines.append(f"ELEMENTOS EN PAPELERA (mostrando {len(data['elementos'])})")
            lines.append('-'*70)
            for elem in data['elementos'][:50]:  # Limitar a 50 en texto
                status = 'Restaurado' if elem['restaurado'] else f"{elem['dias_restantes']} días restantes"
                lines.append(
                    f"  [{elem['id']}] {elem['objeto']} ({elem['modulo']}) - {status}"
                )
        
        lines.append('')
        lines.append('='*70)
        
        return '\n'.join(lines)

    def _save_to_file(self, filepath, content, format_type):
        """Guarda el contenido en un archivo"""
        try:
            # Crear directorio si no existe
            directory = os.path.dirname(filepath)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
            
            # Determinar modo de escritura
            mode = 'w' if format_type in ['json', 'csv', 'txt'] else 'wb'
            
            with open(filepath, mode, encoding='utf-8' if mode == 'w' else None) as f:
                f.write(content)
            
            logger.info(f'Reporte guardado en: {filepath}')
            
        except Exception as e:
            raise CommandError(f'Error guardando archivo: {str(e)}')
