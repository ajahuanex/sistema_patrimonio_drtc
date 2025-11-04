"""
Tareas asíncronas para el sistema de notificaciones
"""
from datetime import datetime, timedelta
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models import Q
from celery import shared_task
from celery.utils.log import get_task_logger

from .models import (
    Notificacion, TipoNotificacion, ConfiguracionNotificacion,
    AlertaMantenimiento, AlertaDepreciacion, HistorialNotificacion
)
from apps.bienes.models import BienPatrimonial, MovimientoBien

logger = get_task_logger(__name__)


@shared_task
def enviar_notificacion_email(notificacion_id):
    """
    Envía una notificación por email
    
    Args:
        notificacion_id: ID de la notificación a enviar
    """
    try:
        notificacion = Notificacion.objects.get(id=notificacion_id)
        
        # Verificar si el usuario tiene email configurado
        if not notificacion.usuario.email:
            logger.warning(f"Usuario {notificacion.usuario.username} no tiene email configurado")
            notificacion.marcar_error("Usuario sin email configurado")
            return
        
        # Verificar configuración del usuario para este tipo de notificación
        config = ConfiguracionNotificacion.objects.filter(
            usuario=notificacion.usuario,
            tipo_notificacion=notificacion.tipo_notificacion
        ).first()
        
        if config and not config.enviar_email:
            logger.info(f"Usuario {notificacion.usuario.username} tiene deshabilitado email para {notificacion.tipo_notificacion.nombre}")
            notificacion.estado = 'ENVIADA'  # Marcar como enviada aunque no se envíe
            notificacion.save()
            return
        
        # Preparar contexto para el template
        contexto = {
            'notificacion': notificacion,
            'usuario': notificacion.usuario,
            'datos_contexto': notificacion.datos_contexto,
            'url_accion': notificacion.url_accion,
            'base_url': settings.BASE_URL,
        }
        
        # Determinar template a usar
        template_email = notificacion.tipo_notificacion.plantilla_email
        if not template_email:
            template_email = 'notificaciones/email_base.html'
        
        # Renderizar mensaje
        mensaje_html = render_to_string(template_email, contexto)
        mensaje_texto = render_to_string('notificaciones/email_base.txt', contexto)
        
        # Enviar email
        send_mail(
            subject=notificacion.titulo,
            message=mensaje_texto,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[notificacion.usuario.email],
            html_message=mensaje_html,
            fail_silently=False
        )
        
        # Marcar como enviada
        notificacion.marcar_como_enviada()
        
        # Registrar en historial
        HistorialNotificacion.objects.create(
            notificacion=notificacion,
            accion='EMAIL_ENVIADO',
            detalles=f'Email enviado a {notificacion.usuario.email}'
        )
        
        logger.info(f"Notificación {notificacion_id} enviada por email a {notificacion.usuario.email}")
        
    except Notificacion.DoesNotExist:
        logger.error(f"Notificación {notificacion_id} no encontrada")
        
    except Exception as e:
        logger.error(f"Error enviando notificación {notificacion_id}: {str(e)}")
        try:
            notificacion = Notificacion.objects.get(id=notificacion_id)
            notificacion.marcar_error(str(e))
        except:
            pass


@shared_task
def procesar_notificaciones_pendientes():
    """
    Procesa todas las notificaciones pendientes
    """
    try:
        # Obtener notificaciones pendientes que no estén expiradas
        notificaciones = Notificacion.objects.filter(
            estado='PENDIENTE',
            fecha_programada__lte=timezone.now()
        ).exclude(
            fecha_expiracion__lt=timezone.now()
        )
        
        procesadas = 0
        
        for notificacion in notificaciones:
            try:
                # Verificar si el tipo de notificación está activo
                if not notificacion.tipo_notificacion.activo:
                    continue
                
                # Enviar por email si está configurado
                if notificacion.tipo_notificacion.enviar_email:
                    enviar_notificacion_email.delay(notificacion.id)
                else:
                    # Marcar como enviada aunque no se envíe email
                    notificacion.marcar_como_enviada()
                
                procesadas += 1
                
            except Exception as e:
                logger.error(f"Error procesando notificación {notificacion.id}: {str(e)}")
                notificacion.marcar_error(str(e))
        
        logger.info(f"Se procesaron {procesadas} notificaciones pendientes")
        
        return {'procesadas': procesadas}
        
    except Exception as e:
        logger.error(f"Error procesando notificaciones pendientes: {str(e)}")
        raise


@shared_task
def verificar_alertas_mantenimiento():
    """
    Verifica y crea alertas de mantenimiento
    """
    try:
        alertas_activas = AlertaMantenimiento.objects.filter(activa=True)
        alertas_generadas = 0
        
        for alerta in alertas_activas:
            # Calcular fecha límite para la alerta
            fecha_limite = timezone.now() + timedelta(days=alerta.dias_anticipacion)
            
            # Buscar bienes que necesitan mantenimiento
            # Nota: Esta lógica depende de cómo se registre el último mantenimiento
            # Por ahora, usaremos la fecha de creación como referencia
            fecha_mantenimiento = timezone.now() - timedelta(days=alerta.frecuencia_meses * 30)
            
            filtro_bienes = Q(created_at__lte=fecha_mantenimiento)
            
            if alerta.tipo_bien != 'TODOS':
                # Filtrar por tipo de bien según el catálogo
                if alerta.tipo_bien == 'VEHICULO':
                    filtro_bienes &= Q(catalogo__grupo__icontains='TRANSPORTE')
                elif alerta.tipo_bien == 'EQUIPO':
                    filtro_bienes &= Q(catalogo__grupo__icontains='EQUIPO')
                elif alerta.tipo_bien == 'MOBILIARIO':
                    filtro_bienes &= Q(catalogo__grupo__icontains='MOBILIARIO')
            
            bienes_mantenimiento = BienPatrimonial.objects.filter(filtro_bienes)
            
            if bienes_mantenimiento.exists():
                # Crear notificaciones para los usuarios configurados
                for usuario in alerta.usuarios_notificar.all():
                    # Verificar si ya existe una notificación reciente
                    notificacion_existente = Notificacion.objects.filter(
                        usuario=usuario,
                        tipo_notificacion__codigo='MANTENIMIENTO',
                        created_at__gte=timezone.now() - timedelta(days=7)
                    ).exists()
                    
                    if not notificacion_existente:
                        notificacion = Notificacion.objects.create(
                            usuario=usuario,
                            tipo_notificacion=TipoNotificacion.objects.get(codigo='MANTENIMIENTO'),
                            titulo=f"Alerta de Mantenimiento: {alerta.nombre}",
                            mensaje=f"Se han identificado {bienes_mantenimiento.count()} bienes que requieren mantenimiento según la configuración '{alerta.nombre}'.",
                            prioridad='ALTA',
                            datos_contexto={
                                'alerta_id': alerta.id,
                                'alerta_nombre': alerta.nombre,
                                'cantidad_bienes': bienes_mantenimiento.count(),
                                'tipo_bien': alerta.tipo_bien,
                                'bienes_ids': list(bienes_mantenimiento.values_list('id', flat=True)[:10])
                            },
                            fecha_expiracion=timezone.now() + timedelta(days=30)
                        )
                        
                        alertas_generadas += 1
                        logger.info(f"Alerta de mantenimiento creada para usuario {usuario.username}")
        
        logger.info(f"Se generaron {alertas_generadas} alertas de mantenimiento")
        
        return {'alertas_generadas': alertas_generadas}
        
    except Exception as e:
        logger.error(f"Error verificando alertas de mantenimiento: {str(e)}")
        raise


@shared_task
def verificar_alertas_depreciacion():
    """
    Verifica y crea alertas de depreciación
    """
    try:
        alertas_activas = AlertaDepreciacion.objects.filter(activa=True)
        alertas_generadas = 0
        
        for alerta in alertas_activas:
            # Calcular fecha límite para depreciación
            fecha_limite_depreciacion = timezone.now() - timedelta(
                days=(alerta.vida_util_anos * 365) - (alerta.meses_anticipacion * 30)
            )
            
            # Buscar bienes próximos a depreciarse
            filtro_bienes = Q(created_at__lte=fecha_limite_depreciacion)
            
            # Aplicar filtros de grupos de catálogo
            if alerta.grupos_catalogo:
                filtro_bienes &= Q(catalogo__grupo__in=alerta.grupos_catalogo)
            
            # Aplicar filtros de oficinas
            if alerta.oficinas:
                filtro_bienes &= Q(oficina__codigo__in=alerta.oficinas)
            
            bienes_depreciacion = BienPatrimonial.objects.filter(filtro_bienes)
            
            if bienes_depreciacion.exists():
                # Crear notificaciones para los usuarios configurados
                for usuario in alerta.usuarios_notificar.all():
                    # Verificar si ya existe una notificación reciente
                    notificacion_existente = Notificacion.objects.filter(
                        usuario=usuario,
                        tipo_notificacion__codigo='DEPRECIACION',
                        created_at__gte=timezone.now() - timedelta(days=30)
                    ).exists()
                    
                    if not notificacion_existente:
                        notificacion = Notificacion.objects.create(
                            usuario=usuario,
                            tipo_notificacion=TipoNotificacion.objects.get(codigo='DEPRECIACION'),
                            titulo=f"Alerta de Depreciación: {alerta.nombre}",
                            mensaje=f"Se han identificado {bienes_depreciacion.count()} bienes próximos a cumplir su vida útil según la configuración '{alerta.nombre}'.",
                            prioridad='MEDIA',
                            datos_contexto={
                                'alerta_id': alerta.id,
                                'alerta_nombre': alerta.nombre,
                                'cantidad_bienes': bienes_depreciacion.count(),
                                'vida_util_anos': alerta.vida_util_anos,
                                'meses_anticipacion': alerta.meses_anticipacion,
                                'bienes_ids': list(bienes_depreciacion.values_list('id', flat=True)[:10])
                            },
                            fecha_expiracion=timezone.now() + timedelta(days=60)
                        )
                        
                        alertas_generadas += 1
                        logger.info(f"Alerta de depreciación creada para usuario {usuario.username}")
        
        logger.info(f"Se generaron {alertas_generadas} alertas de depreciación")
        
        return {'alertas_generadas': alertas_generadas}
        
    except Exception as e:
        logger.error(f"Error verificando alertas de depreciación: {str(e)}")
        raise


@shared_task
def notificar_movimiento_bien(movimiento_id):
    """
    Envía notificaciones cuando se registra un movimiento de bien
    
    Args:
        movimiento_id: ID del movimiento de bien
    """
    try:
        movimiento = MovimientoBien.objects.get(id=movimiento_id)
        
        # Obtener usuarios a notificar (responsables de origen y destino)
        usuarios_notificar = []
        
        # Agregar responsables de las oficinas
        if hasattr(movimiento.oficina_origen, 'responsable_usuario'):
            usuarios_notificar.append(movimiento.oficina_origen.responsable_usuario)
        
        if hasattr(movimiento.oficina_destino, 'responsable_usuario'):
            usuarios_notificar.append(movimiento.oficina_destino.responsable_usuario)
        
        # Agregar usuario que registró el movimiento
        usuarios_notificar.append(movimiento.usuario)
        
        # Eliminar duplicados
        usuarios_notificar = list(set(usuarios_notificar))
        
        tipo_notificacion = TipoNotificacion.objects.get(codigo='MOVIMIENTO')
        
        for usuario in usuarios_notificar:
            notificacion = Notificacion.objects.create(
                usuario=usuario,
                tipo_notificacion=tipo_notificacion,
                titulo=f"Movimiento de Bien: {movimiento.bien.codigo_patrimonial}",
                mensaje=f"El bien '{movimiento.bien.catalogo.denominacion}' ha sido transferido de {movimiento.oficina_origen.nombre} a {movimiento.oficina_destino.nombre}.",
                prioridad='MEDIA',
                datos_contexto={
                    'movimiento_id': movimiento.id,
                    'bien_id': movimiento.bien.id,
                    'bien_codigo': movimiento.bien.codigo_patrimonial,
                    'bien_denominacion': movimiento.bien.catalogo.denominacion,
                    'oficina_origen': movimiento.oficina_origen.nombre,
                    'oficina_destino': movimiento.oficina_destino.nombre,
                    'motivo': movimiento.motivo,
                    'fecha_movimiento': movimiento.fecha_movimiento.isoformat()
                },
                url_accion=f"/bienes/{movimiento.bien.id}/",
                fecha_expiracion=timezone.now() + timedelta(days=15)
            )
            
            logger.info(f"Notificación de movimiento creada para usuario {usuario.username}")
        
        return {'usuarios_notificados': len(usuarios_notificar)}
        
    except MovimientoBien.DoesNotExist:
        logger.error(f"Movimiento {movimiento_id} no encontrado")
        
    except Exception as e:
        logger.error(f"Error notificando movimiento {movimiento_id}: {str(e)}")
        raise


@shared_task
def limpiar_notificaciones_expiradas():
    """
    Limpia notificaciones expiradas del sistema
    """
    try:
        # Eliminar notificaciones expiradas y leídas de más de 30 días
        fecha_limite = timezone.now() - timedelta(days=30)
        
        notificaciones_expiradas = Notificacion.objects.filter(
            Q(fecha_expiracion__lt=timezone.now()) |
            Q(estado='LEIDA', fecha_leida__lt=fecha_limite)
        )
        
        cantidad_eliminadas = notificaciones_expiradas.count()
        notificaciones_expiradas.delete()
        
        logger.info(f"Se eliminaron {cantidad_eliminadas} notificaciones expiradas")
        
        return {'eliminadas': cantidad_eliminadas}
        
    except Exception as e:
        logger.error(f"Error limpiando notificaciones expiradas: {str(e)}")
        raise


@shared_task
def reenviar_notificaciones_fallidas():
    """
    Reintenta enviar notificaciones que fallaron
    """
    try:
        # Obtener notificaciones con error que tengan menos de 3 intentos
        notificaciones_error = Notificacion.objects.filter(
            estado='ERROR',
            intentos_envio__lt=3,
            created_at__gte=timezone.now() - timedelta(hours=24)
        )
        
        reenviadas = 0
        
        for notificacion in notificaciones_error:
            # Resetear estado para reintento
            notificacion.estado = 'PENDIENTE'
            notificacion.save()
            
            # Programar reenvío
            enviar_notificacion_email.delay(notificacion.id)
            reenviadas += 1
        
        logger.info(f"Se programaron {reenviadas} notificaciones para reenvío")
        
        return {'reenviadas': reenviadas}
        
    except Exception as e:
        logger.error(f"Error reenviando notificaciones fallidas: {str(e)}")
        raise


@shared_task
def crear_notificacion_sistema(usuario_id, titulo, mensaje, prioridad='MEDIA', datos_contexto=None, url_accion=None):
    """
    Crea una notificación del sistema
    
    Args:
        usuario_id: ID del usuario
        titulo: Título de la notificación
        mensaje: Mensaje de la notificación
        prioridad: Prioridad de la notificación
        datos_contexto: Datos adicionales
        url_accion: URL de acción relacionada
    """
    try:
        usuario = User.objects.get(id=usuario_id)
        tipo_notificacion = TipoNotificacion.objects.get(codigo='SISTEMA')
        
        notificacion = Notificacion.objects.create(
            usuario=usuario,
            tipo_notificacion=tipo_notificacion,
            titulo=titulo,
            mensaje=mensaje,
            prioridad=prioridad,
            datos_contexto=datos_contexto or {},
            url_accion=url_accion or '',
            fecha_expiracion=timezone.now() + timedelta(days=7)
        )
        
        logger.info(f"Notificación del sistema creada para usuario {usuario.username}: {titulo}")
        
        return {'notificacion_id': notificacion.id}
        
    except User.DoesNotExist:
        logger.error(f"Usuario {usuario_id} no encontrado")
        
    except Exception as e:
        logger.error(f"Error creando notificación del sistema: {str(e)}")
        raise