"""
Comando para configurar tipos de notificaciones iniciales
"""
from django.core.management.base import BaseCommand
from apps.notificaciones.models import TipoNotificacion


class Command(BaseCommand):
    help = 'Configura los tipos de notificaciones iniciales del sistema'
    
    def handle(self, *args, **options):
        tipos_notificacion = [
            {
                'codigo': 'MANTENIMIENTO',
                'nombre': 'Alerta de Mantenimiento',
                'descripcion': 'Notificaciones sobre bienes que requieren mantenimiento',
                'enviar_email': True,
                'plantilla_email': 'notificaciones/email_mantenimiento.html'
            },
            {
                'codigo': 'DEPRECIACION',
                'nombre': 'Alerta de Depreciación',
                'descripcion': 'Notificaciones sobre bienes próximos a depreciarse',
                'enviar_email': True,
                'plantilla_email': 'notificaciones/email_depreciacion.html'
            },
            {
                'codigo': 'MOVIMIENTO',
                'nombre': 'Movimiento de Bien',
                'descripcion': 'Notificaciones sobre movimientos de bienes patrimoniales',
                'enviar_email': True,
                'plantilla_email': 'notificaciones/email_movimiento.html'
            },
            {
                'codigo': 'IMPORTACION',
                'nombre': 'Importación Completada',
                'descripcion': 'Notificaciones sobre importaciones masivas completadas',
                'enviar_email': True,
                'plantilla_email': 'core/email_importacion_completada.html'
            },
            {
                'codigo': 'REPORTE',
                'nombre': 'Reporte Generado',
                'descripcion': 'Notificaciones sobre reportes generados',
                'enviar_email': True,
                'plantilla_email': 'reportes/email_reporte_listo.html'
            },
            {
                'codigo': 'SISTEMA',
                'nombre': 'Notificación del Sistema',
                'descripcion': 'Notificaciones generales del sistema',
                'enviar_email': True,
                'plantilla_email': 'notificaciones/email_base.html'
            },
            {
                'codigo': 'INVENTARIO',
                'nombre': 'Inventario',
                'descripcion': 'Notificaciones relacionadas con inventarios',
                'enviar_email': True,
                'plantilla_email': 'notificaciones/email_inventario.html'
            },
            {
                'codigo': 'ALERTA',
                'nombre': 'Alerta General',
                'descripcion': 'Alertas generales del sistema',
                'enviar_email': True,
                'plantilla_email': 'notificaciones/email_base.html'
            },
        ]
        
        creados = 0
        actualizados = 0
        
        for tipo_data in tipos_notificacion:
            tipo, created = TipoNotificacion.objects.get_or_create(
                codigo=tipo_data['codigo'],
                defaults=tipo_data
            )
            
            if created:
                creados += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Creado tipo de notificación: {tipo.nombre}')
                )
            else:
                # Actualizar campos si es necesario
                updated = False
                for field, value in tipo_data.items():
                    if field != 'codigo' and getattr(tipo, field) != value:
                        setattr(tipo, field, value)
                        updated = True
                
                if updated:
                    tipo.save()
                    actualizados += 1
                    self.stdout.write(
                        self.style.WARNING(f'Actualizado tipo de notificación: {tipo.nombre}')
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Configuración completada: {creados} creados, {actualizados} actualizados'
            )
        )