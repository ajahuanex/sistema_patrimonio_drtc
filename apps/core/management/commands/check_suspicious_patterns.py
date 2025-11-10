"""
Comando de management para verificar patrones sospechosos en logs de auditoría
y enviar alertas automáticas a administradores.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Count, Q
from django.db.models.functions import ExtractHour
from datetime import timedelta

from apps.core.models import DeletionAuditLog
from apps.notificaciones.models import Notificacion


class Command(BaseCommand):
    help = 'Verifica patrones sospechosos en logs de auditoría y envía alertas'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Número de horas hacia atrás para analizar (por defecto: 24)'
        )
        
        parser.add_argument(
            '--send-notifications',
            action='store_true',
            help='Enviar notificaciones a administradores'
        )
        
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Mostrar información detallada'
        )
    
    def handle(self, *args, **options):
        hours = options['hours']
        send_notifications = options['send_notifications']
        verbose = options['verbose']
        
        self.stdout.write(self.style.SUCCESS(
            f'Analizando logs de auditoría de las últimas {hours} horas...'
        ))
        
        # Obtener logs del período especificado
        cutoff_time = timezone.now() - timedelta(hours=hours)
        queryset = DeletionAuditLog.objects.filter(timestamp__gte=cutoff_time)
        
        # Detectar patrones sospechosos
        patterns = self._detect_all_patterns(queryset, hours)
        
        if not patterns:
            self.stdout.write(self.style.SUCCESS(
                '✓ No se detectaron patrones sospechosos'
            ))
            return
        
        # Mostrar patrones detectados
        self.stdout.write(self.style.WARNING(
            f'\n⚠️  Se detectaron {len(patterns)} patrones sospechosos:\n'
        ))
        
        for pattern in patterns:
            severity_color = {
                'high': self.style.ERROR,
                'medium': self.style.WARNING,
                'low': self.style.NOTICE
            }.get(pattern['severity'], self.style.NOTICE)
            
            self.stdout.write(severity_color(
                f"  {pattern['icon']} [{pattern['severity'].upper()}] {pattern['message']}"
            ))
            
            if verbose and 'details' in pattern:
                for key, value in pattern['details'].items():
                    self.stdout.write(f"      - {key}: {value}")
        
        # Enviar notificaciones si se solicitó
        if send_notifications:
            self._send_alerts(patterns)
            self.stdout.write(self.style.SUCCESS(
                '\n✓ Alertas enviadas a administradores'
            ))
        else:
            self.stdout.write(self.style.NOTICE(
                '\nℹ️  Use --send-notifications para enviar alertas a administradores'
            ))
    
    def _detect_all_patterns(self, queryset, hours):
        """
        Detecta todos los patrones sospechosos en el queryset.
        
        Args:
            queryset: QuerySet de DeletionAuditLog
            hours: Número de horas del período analizado
            
        Returns:
            list: Lista de patrones detectados
        """
        patterns = []
        now = timezone.now()
        
        # Patrón 1: Múltiples eliminaciones permanentes
        permanent_deletes = queryset.filter(
            action='permanent_delete'
        ).values('user__username').annotate(
            count=Count('id')
        ).filter(count__gte=5)
        
        for item in permanent_deletes:
            patterns.append({
                'type': 'high_permanent_deletes',
                'severity': 'high',
                'message': f"Usuario {item['user__username']} realizó {item['count']} eliminaciones permanentes",
                'icon': '⚠️',
                'user': item['user__username'],
                'count': item['count'],
                'details': {
                    'Período': f'{hours} horas',
                    'Umbral': '5 eliminaciones'
                }
            })
        
        # Patrón 2: Múltiples intentos fallidos
        failures = queryset.filter(
            success=False
        ).values('user__username').annotate(
            count=Count('id')
        ).filter(count__gte=3)
        
        for item in failures:
            patterns.append({
                'type': 'multiple_failures',
                'severity': 'medium',
                'message': f"Usuario {item['user__username']} tuvo {item['count']} operaciones fallidas",
                'icon': '⚡',
                'user': item['user__username'],
                'count': item['count'],
                'details': {
                    'Período': f'{hours} horas',
                    'Umbral': '3 fallos'
                }
            })
        
        # Patrón 3: Eliminaciones masivas por módulo
        massive_deletes = queryset.filter(
            action__in=['soft_delete', 'permanent_delete']
        ).values('module_name', 'user__username').annotate(
            count=Count('id')
        ).filter(count__gte=20)
        
        for item in massive_deletes:
            patterns.append({
                'type': 'massive_deletes',
                'severity': 'high',
                'message': f"Usuario {item['user__username']} eliminó {item['count']} elementos del módulo {item['module_name']}",
                'icon': '🔥',
                'user': item['user__username'],
                'module': item['module_name'],
                'count': item['count'],
                'details': {
                    'Período': f'{hours} horas',
                    'Umbral': '20 eliminaciones'
                }
            })
        
        # Patrón 4: Actividad fuera de horario laboral
        off_hours = queryset.annotate(
            hour=ExtractHour('timestamp')
        ).filter(
            Q(hour__gte=22) | Q(hour__lt=6)
        ).values('user__username').annotate(
            count=Count('id')
        ).filter(count__gte=5)
        
        for item in off_hours:
            patterns.append({
                'type': 'off_hours_activity',
                'severity': 'low',
                'message': f"Usuario {item['user__username']} realizó {item['count']} operaciones fuera de horario laboral",
                'icon': '🌙',
                'user': item['user__username'],
                'count': item['count'],
                'details': {
                    'Horario sospechoso': '10pm - 6am',
                    'Umbral': '5 operaciones'
                }
            })
        
        # Patrón 5: Restauraciones seguidas de eliminaciones permanentes
        users_with_activity = queryset.values_list('user__username', flat=True).distinct()
        
        for username in users_with_activity:
            user_logs = queryset.filter(user__username=username).order_by('timestamp')
            
            restore_count = user_logs.filter(action='restore').count()
            permanent_delete_count = user_logs.filter(action='permanent_delete').count()
            
            if restore_count >= 3 and permanent_delete_count >= 3:
                patterns.append({
                    'type': 'restore_then_delete',
                    'severity': 'medium',
                    'message': f"Usuario {username} restauró {restore_count} elementos y luego eliminó permanentemente {permanent_delete_count}",
                    'icon': '🔄',
                    'user': username,
                    'restore_count': restore_count,
                    'delete_count': permanent_delete_count,
                    'details': {
                        'Patrón': 'Restaurar y eliminar permanentemente',
                        'Umbral': '3 de cada tipo'
                    }
                })
        
        # Patrón 6: Uso excesivo del código de seguridad
        security_code_usage = queryset.filter(
            security_code_used=True
        ).values('user__username').annotate(
            count=Count('id')
        ).filter(count__gte=10)
        
        for item in security_code_usage:
            patterns.append({
                'type': 'excessive_security_code_usage',
                'severity': 'high',
                'message': f"Usuario {item['user__username']} usó el código de seguridad {item['count']} veces",
                'icon': '🔐',
                'user': item['user__username'],
                'count': item['count'],
                'details': {
                    'Período': f'{hours} horas',
                    'Umbral': '10 usos'
                }
            })
        
        return patterns
    
    def _send_alerts(self, patterns):
        """
        Envía notificaciones de alerta a todos los administradores.
        
        Args:
            patterns: Lista de patrones detectados
        """
        # Obtener todos los administradores
        admins = User.objects.filter(
            profile__role='administrador',
            profile__is_active=True
        )
        
        if not admins.exists():
            self.stdout.write(self.style.WARNING(
                'No se encontraron administradores activos para enviar alertas'
            ))
            return
        
        # Agrupar patrones por severidad
        high_severity = [p for p in patterns if p['severity'] == 'high']
        medium_severity = [p for p in patterns if p['severity'] == 'medium']
        low_severity = [p for p in patterns if p['severity'] == 'low']
        
        # Crear mensaje de alerta
        message = "Se detectaron patrones sospechosos en el sistema de auditoría:\n\n"
        
        if high_severity:
            message += f"🔴 ALTA PRIORIDAD ({len(high_severity)}):\n"
            for pattern in high_severity:
                message += f"  • {pattern['message']}\n"
            message += "\n"
        
        if medium_severity:
            message += f"🟡 PRIORIDAD MEDIA ({len(medium_severity)}):\n"
            for pattern in medium_severity:
                message += f"  • {pattern['message']}\n"
            message += "\n"
        
        if low_severity:
            message += f"🟢 PRIORIDAD BAJA ({len(low_severity)}):\n"
            for pattern in low_severity:
                message += f"  • {pattern['message']}\n"
        
        # Enviar notificación a cada administrador
        for admin in admins:
            try:
                Notificacion.objects.create(
                    usuario=admin,
                    tipo='alerta_seguridad',
                    titulo='⚠️ Patrones Sospechosos Detectados',
                    mensaje=message,
                    prioridad='alta' if high_severity else 'media',
                    leida=False
                )
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f'Error al enviar notificación a {admin.username}: {str(e)}'
                ))
