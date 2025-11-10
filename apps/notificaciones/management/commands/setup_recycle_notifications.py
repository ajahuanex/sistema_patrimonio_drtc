"""
Comando para configurar tipos de notificaciones de papelera de reciclaje
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.notificaciones.models import TipoNotificacion


class Command(BaseCommand):
    help = 'Configura los tipos de notificaciones para el sistema de papelera de reciclaje'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Configurando tipos de notificaciones de papelera...'))
        
        # Crear o actualizar tipo de notificación de advertencia
        tipo_warning, created = TipoNotificacion.objects.update_or_create(
            codigo='RECYCLE_WARNING',
            defaults={
                'nombre': 'Advertencia de Papelera',
                'descripcion': 'Notificaciones de elementos próximos a eliminación automática (7 días antes)',
                'activo': True,
                'enviar_email': True,
                'plantilla_email': 'notificaciones/email_recycle_warning.html'
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Tipo de notificación creado: {tipo_warning.nombre}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'✓ Tipo de notificación actualizado: {tipo_warning.nombre}'))
        
        # Crear o actualizar tipo de notificación de advertencia final
        tipo_final, created = TipoNotificacion.objects.update_or_create(
            codigo='RECYCLE_FINAL_WARNING',
            defaults={
                'nombre': 'Advertencia Final de Papelera',
                'descripcion': 'Notificaciones finales antes de eliminación automática (1 día antes)',
                'activo': True,
                'enviar_email': True,
                'plantilla_email': 'notificaciones/email_recycle_final_warning.html'
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Tipo de notificación creado: {tipo_final.nombre}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'✓ Tipo de notificación actualizado: {tipo_final.nombre}'))
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('Configuración completada exitosamente'))
        self.stdout.write(self.style.SUCCESS('='*60))
        
        self.stdout.write('\nTipos de notificaciones configurados:')
        self.stdout.write(f'  • {tipo_warning.nombre} ({tipo_warning.codigo})')
        self.stdout.write(f'  • {tipo_final.nombre} ({tipo_final.codigo})')
        
        self.stdout.write('\nPara configurar las tareas automáticas, agrega a Celery Beat:')
        self.stdout.write('  • verificar_alertas_papelera: Ejecutar diariamente')
        self.stdout.write('  • procesar_notificaciones_pendientes: Ejecutar cada hora')
