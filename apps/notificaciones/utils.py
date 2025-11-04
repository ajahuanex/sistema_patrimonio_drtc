"""
Utilidades para el sistema de notificaciones
"""
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.models import User
from .models import Notificacion, TipoNotificacion
from .tasks import enviar_notificacion_email


def crear_notificacion(usuario, tipo_codigo, titulo, mensaje, **kwargs):
    """
    Crea una notificación de forma sencilla
    
    Args:
        usuario: Usuario o ID del usuario
        tipo_codigo: Código del tipo de notificación
        titulo: Título de la notificación
        mensaje: Mensaje de la notificación
        **kwargs: Argumentos adicionales (prioridad, datos_contexto, url_accion, etc.)
    
    Returns:
        Notificacion: La notificación creada
    """
    if isinstance(usuario, int):
        usuario = User.objects.get(id=usuario)
    
    tipo_notificacion = TipoNotificacion.objects.get(codigo=tipo_codigo)
    
    # Valores por defecto
    defaults = {
        'prioridad': 'MEDIA',
        'datos_contexto': {},
        'url_accion': '',
        'fecha_expiracion': timezone.now() + timedelta(days=7)
    }
    
    # Actualizar con kwargs
    defaults.update(kwargs)
    
    notificacion = Notificacion.objects.create(
        usuario=usuario,
        tipo_notificacion=tipo_notificacion,
        titulo=titulo,
        mensaje=mensaje,
        **defaults
    )
    
    return notificacion


def notificar_mantenimiento(usuarios, bienes_count, alerta_nombre, **kwargs):
    """
    Crea notificaciones de mantenimiento para múltiples usuarios
    
    Args:
        usuarios: Lista de usuarios o IDs
        bienes_count: Cantidad de bienes que requieren mantenimiento
        alerta_nombre: Nombre de la alerta de mantenimiento
        **kwargs: Datos adicionales
    """
    if not isinstance(usuarios, list):
        usuarios = [usuarios]
    
    for usuario in usuarios:
        crear_notificacion(
            usuario=usuario,
            tipo_codigo='MANTENIMIENTO',
            titulo=f'Alerta de Mantenimiento: {alerta_nombre}',
            mensaje=f'Se han identificado {bienes_count} bienes que requieren mantenimiento según la configuración "{alerta_nombre}".',
            prioridad='ALTA',
            datos_contexto={
                'alerta_nombre': alerta_nombre,
                'cantidad_bienes': bienes_count,
                **kwargs
            }
        )


def notificar_depreciacion(usuarios, bienes_count, alerta_nombre, **kwargs):
    """
    Crea notificaciones de depreciación para múltiples usuarios
    
    Args:
        usuarios: Lista de usuarios o IDs
        bienes_count: Cantidad de bienes próximos a depreciarse
        alerta_nombre: Nombre de la alerta de depreciación
        **kwargs: Datos adicionales
    """
    if not isinstance(usuarios, list):
        usuarios = [usuarios]
    
    for usuario in usuarios:
        crear_notificacion(
            usuario=usuario,
            tipo_codigo='DEPRECIACION',
            titulo=f'Alerta de Depreciación: {alerta_nombre}',
            mensaje=f'Se han identificado {bienes_count} bienes próximos a cumplir su vida útil según la configuración "{alerta_nombre}".',
            prioridad='MEDIA',
            datos_contexto={
                'alerta_nombre': alerta_nombre,
                'cantidad_bienes': bienes_count,
                **kwargs
            }
        )


def notificar_movimiento_bien(movimiento):
    """
    Crea notificaciones para un movimiento de bien
    
    Args:
        movimiento: Instancia de MovimientoBien
    """
    from apps.bienes.models import MovimientoBien
    from .tasks import notificar_movimiento_bien as task_notificar
    
    # Ejecutar tarea asíncrona
    task_notificar.delay(movimiento.id)


def notificar_importacion_completada(usuario, tipo_importacion, resultado):
    """
    Crea notificación de importación completada
    
    Args:
        usuario: Usuario que realizó la importación
        tipo_importacion: Tipo de importación (catalogo, oficinas, bienes)
        resultado: Resultado de la importación
    """
    tipo_nombres = {
        'catalogo': 'Catálogo',
        'oficinas': 'Oficinas',
        'bienes': 'Bienes Patrimoniales'
    }
    
    tipo_nombre = tipo_nombres.get(tipo_importacion, tipo_importacion)
    
    crear_notificacion(
        usuario=usuario,
        tipo_codigo='IMPORTACION',
        titulo=f'Importación de {tipo_nombre} Completada',
        mensaje=f'La importación de {tipo_nombre} ha sido procesada exitosamente.',
        prioridad='MEDIA',
        datos_contexto={
            'tipo_importacion': tipo_nombre,
            'resultado': resultado
        }
    )


def notificar_reporte_listo(usuario, reporte):
    """
    Crea notificación de reporte listo
    
    Args:
        usuario: Usuario que solicitó el reporte
        reporte: Instancia de ReporteGenerado
    """
    crear_notificacion(
        usuario=usuario,
        tipo_codigo='REPORTE',
        titulo=f'Reporte "{reporte.nombre}" listo para descarga',
        mensaje=f'El reporte "{reporte.nombre}" ha sido generado exitosamente y está listo para descarga.',
        prioridad='MEDIA',
        datos_contexto={
            'reporte_id': reporte.id,
            'reporte_nombre': reporte.nombre,
            'tipo_reporte': reporte.tipo_reporte,
            'formato': reporte.formato
        },
        url_accion=f'/reportes/{reporte.id}/'
    )


def notificar_sistema(usuario, titulo, mensaje, prioridad='MEDIA', **kwargs):
    """
    Crea una notificación del sistema
    
    Args:
        usuario: Usuario destinatario
        titulo: Título de la notificación
        mensaje: Mensaje de la notificación
        prioridad: Prioridad de la notificación
        **kwargs: Datos adicionales
    """
    crear_notificacion(
        usuario=usuario,
        tipo_codigo='SISTEMA',
        titulo=titulo,
        mensaje=mensaje,
        prioridad=prioridad,
        **kwargs
    )


def obtener_notificaciones_usuario(usuario, no_leidas_solo=False, limit=None):
    """
    Obtiene las notificaciones de un usuario
    
    Args:
        usuario: Usuario o ID del usuario
        no_leidas_solo: Si True, solo devuelve notificaciones no leídas
        limit: Límite de notificaciones a devolver
    
    Returns:
        QuerySet: Notificaciones del usuario
    """
    if isinstance(usuario, int):
        usuario = User.objects.get(id=usuario)
    
    queryset = Notificacion.objects.filter(usuario=usuario)
    
    if no_leidas_solo:
        queryset = queryset.exclude(estado='LEIDA')
    
    queryset = queryset.order_by('-created_at')
    
    if limit:
        queryset = queryset[:limit]
    
    return queryset


def marcar_notificaciones_como_leidas(usuario, notificacion_ids=None):
    """
    Marca notificaciones como leídas
    
    Args:
        usuario: Usuario o ID del usuario
        notificacion_ids: Lista de IDs de notificaciones (opcional, si no se proporciona marca todas)
    """
    if isinstance(usuario, int):
        usuario = User.objects.get(id=usuario)
    
    queryset = Notificacion.objects.filter(usuario=usuario).exclude(estado='LEIDA')
    
    if notificacion_ids:
        queryset = queryset.filter(id__in=notificacion_ids)
    
    for notificacion in queryset:
        notificacion.marcar_como_leida()


def contar_notificaciones_no_leidas(usuario):
    """
    Cuenta las notificaciones no leídas de un usuario
    
    Args:
        usuario: Usuario o ID del usuario
    
    Returns:
        int: Cantidad de notificaciones no leídas
    """
    if isinstance(usuario, int):
        usuario = User.objects.get(id=usuario)
    
    return Notificacion.objects.filter(
        usuario=usuario
    ).exclude(estado='LEIDA').count()


def limpiar_notificaciones_usuario(usuario, dias_antiguedad=30):
    """
    Limpia notificaciones antiguas de un usuario
    
    Args:
        usuario: Usuario o ID del usuario
        dias_antiguedad: Días de antigüedad para considerar una notificación como antigua
    
    Returns:
        int: Cantidad de notificaciones eliminadas
    """
    if isinstance(usuario, int):
        usuario = User.objects.get(id=usuario)
    
    fecha_limite = timezone.now() - timedelta(days=dias_antiguedad)
    
    notificaciones_antiguas = Notificacion.objects.filter(
        usuario=usuario,
        estado='LEIDA',
        fecha_leida__lt=fecha_limite
    )
    
    cantidad = notificaciones_antiguas.count()
    notificaciones_antiguas.delete()
    
    return cantidad