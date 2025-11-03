"""
Tareas asíncronas para sincronización móvil
"""
from celery import shared_task
from django.utils import timezone
from django.db import transaction
from django.contrib.auth.models import User
import logging

from .models import CambioOffline, SesionSync, ConflictoSync
from apps.bienes.models import BienPatrimonial, HistorialEstado
from apps.catalogo.models import Catalogo
from apps.oficinas.models import Oficina

logger = logging.getLogger(__name__)


@shared_task
def procesar_sincronizacion_async(sesion_id, cambios_ids):
    """
    Procesar sincronización de cambios offline de forma asíncrona
    """
    try:
        sesion = SesionSync.objects.get(id=sesion_id)
        cambios = CambioOffline.objects.filter(id__in=cambios_ids)
        
        sesion.cambios_procesados = 0
        sesion.cambios_exitosos = 0
        sesion.cambios_con_error = 0
        sesion.cambios_con_conflicto = 0
        
        for cambio in cambios:
            try:
                resultado = procesar_cambio_individual(cambio)
                
                if resultado['estado'] == 'COMPLETADO':
                    sesion.cambios_exitosos += 1
                elif resultado['estado'] == 'ERROR':
                    sesion.cambios_con_error += 1
                elif resultado['estado'] == 'CONFLICTO':
                    sesion.cambios_con_conflicto += 1
                
                sesion.cambios_procesados += 1
                
            except Exception as e:
                logger.error(f"Error procesando cambio {cambio.id}: {str(e)}")
                cambio.estado_sync = 'ERROR'
                cambio.mensaje_error = str(e)
                cambio.intentos_sync += 1
                cambio.ultimo_intento = timezone.now()
                cambio.save()
                
                sesion.cambios_con_error += 1
                sesion.cambios_procesados += 1
        
        # Finalizar sesión
        sesion.fin_sync = timezone.now()
        sesion.completada = True
        sesion.mensaje_resultado = f"Procesados: {sesion.cambios_procesados}, " \
                                 f"Exitosos: {sesion.cambios_exitosos}, " \
                                 f"Errores: {sesion.cambios_con_error}, " \
                                 f"Conflictos: {sesion.cambios_con_conflicto}"
        sesion.save()
        
        logger.info(f"Sincronización completada para sesión {sesion_id}")
        
    except Exception as e:
        logger.error(f"Error en sincronización {sesion_id}: {str(e)}")
        try:
            sesion = SesionSync.objects.get(id=sesion_id)
            sesion.fin_sync = timezone.now()
            sesion.completada = True
            sesion.mensaje_resultado = f"Error general: {str(e)}"
            sesion.save()
        except:
            pass


def procesar_cambio_individual(cambio):
    """
    Procesar un cambio individual
    """
    try:
        cambio.estado_sync = 'PROCESANDO'
        cambio.intentos_sync += 1
        cambio.ultimo_intento = timezone.now()
        cambio.save()
        
        if cambio.tipo_cambio == 'CREAR':
            return procesar_crear_bien(cambio)
        elif cambio.tipo_cambio == 'ACTUALIZAR':
            return procesar_actualizar_bien(cambio)
        elif cambio.tipo_cambio == 'CAMBIAR_ESTADO':
            return procesar_cambiar_estado(cambio)
        elif cambio.tipo_cambio == 'AGREGAR_FOTO':
            return procesar_agregar_foto(cambio)
        elif cambio.tipo_cambio == 'INVENTARIO':
            return procesar_inventario(cambio)
        else:
            raise ValueError(f"Tipo de cambio no soportado: {cambio.tipo_cambio}")
            
    except Exception as e:
        cambio.estado_sync = 'ERROR'
        cambio.mensaje_error = str(e)
        cambio.save()
        return {'estado': 'ERROR', 'mensaje': str(e)}


def procesar_crear_bien(cambio):
    """
    Procesar creación de un nuevo bien
    """
    datos = cambio.get_datos_cambio()
    
    # Verificar si ya existe un bien con el mismo código
    if BienPatrimonial.objects.filter(codigo_patrimonial=datos['codigo_patrimonial']).exists():
        return crear_conflicto(cambio, 'CODIGO_DUPLICADO', 
                             {'mensaje': 'Ya existe un bien con este código patrimonial'})
    
    try:
        with transaction.atomic():
            # Obtener catálogo y oficina
            catalogo = Catalogo.objects.get(id=datos['catalogo_id'])
            oficina = Oficina.objects.get(id=datos['oficina_id'])
            
            # Crear el bien
            bien = BienPatrimonial.objects.create(
                codigo_patrimonial=datos['codigo_patrimonial'],
                codigo_interno=datos.get('codigo_interno', ''),
                catalogo=catalogo,
                oficina=oficina,
                estado_bien=datos['estado_bien'],
                marca=datos.get('marca', ''),
                modelo=datos.get('modelo', ''),
                color=datos.get('color', ''),
                serie=datos.get('serie', ''),
                dimension=datos.get('dimension', ''),
                placa=datos.get('placa', ''),
                matricula=datos.get('matricula', ''),
                nro_motor=datos.get('nro_motor', ''),
                nro_chasis=datos.get('nro_chasis', ''),
                observaciones=datos.get('observaciones', ''),
                created_by=cambio.usuario
            )
            
            cambio.estado_sync = 'COMPLETADO'
            cambio.save()
            
            return {'estado': 'COMPLETADO', 'bien_id': bien.id}
            
    except (Catalogo.DoesNotExist, Oficina.DoesNotExist) as e:
        return crear_conflicto(cambio, 'DATOS_INCONSISTENTES', 
                             {'mensaje': f'Referencia no encontrada: {str(e)}'})


def procesar_actualizar_bien(cambio):
    """
    Procesar actualización de un bien existente
    """
    datos = cambio.get_datos_cambio()
    
    try:
        # Buscar el bien
        if cambio.bien_qr_code:
            bien = BienPatrimonial.objects.get(qr_code=cambio.bien_qr_code)
        else:
            bien = BienPatrimonial.objects.get(codigo_patrimonial=cambio.bien_codigo_patrimonial)
        
        # Verificar si el bien fue modificado después del timestamp local
        if bien.updated_at > cambio.timestamp_local:
            return crear_conflicto(cambio, 'BIEN_MODIFICADO', {
                'bien_servidor': {
                    'updated_at': bien.updated_at.isoformat(),
                    'estado_bien': bien.estado_bien,
                    'marca': bien.marca,
                    'modelo': bien.modelo,
                }
            })
        
        with transaction.atomic():
            # Actualizar campos
            for campo, valor in datos.items():
                if hasattr(bien, campo) and campo not in ['id', 'qr_code', 'url_qr', 'created_at', 'updated_at']:
                    setattr(bien, campo, valor)
            
            bien.save()
            
            cambio.estado_sync = 'COMPLETADO'
            cambio.save()
            
            return {'estado': 'COMPLETADO', 'bien_id': bien.id}
            
    except BienPatrimonial.DoesNotExist:
        return crear_conflicto(cambio, 'BIEN_ELIMINADO', 
                             {'mensaje': 'El bien no existe en el servidor'})


def procesar_cambiar_estado(cambio):
    """
    Procesar cambio de estado de un bien
    """
    datos = cambio.get_datos_cambio()
    
    try:
        # Buscar el bien
        if cambio.bien_qr_code:
            bien = BienPatrimonial.objects.get(qr_code=cambio.bien_qr_code)
        else:
            bien = BienPatrimonial.objects.get(codigo_patrimonial=cambio.bien_codigo_patrimonial)
        
        with transaction.atomic():
            estado_anterior = bien.estado_bien
            nuevo_estado = datos['estado_bien']
            
            # Actualizar estado del bien
            bien.estado_bien = nuevo_estado
            bien.save()
            
            # Crear registro en historial
            HistorialEstado.objects.create(
                bien=bien,
                estado_anterior=estado_anterior,
                estado_nuevo=nuevo_estado,
                observaciones=datos.get('observaciones', ''),
                usuario=cambio.usuario,
                ubicacion_gps=cambio.ubicacion_gps,
                # Nota: Las fotos se manejan por separado
            )
            
            cambio.estado_sync = 'COMPLETADO'
            cambio.save()
            
            return {'estado': 'COMPLETADO', 'bien_id': bien.id}
            
    except BienPatrimonial.DoesNotExist:
        return crear_conflicto(cambio, 'BIEN_ELIMINADO', 
                             {'mensaje': 'El bien no existe en el servidor'})


def procesar_agregar_foto(cambio):
    """
    Procesar adición de foto a un bien
    """
    datos = cambio.get_datos_cambio()
    
    try:
        # Buscar el bien
        if cambio.bien_qr_code:
            bien = BienPatrimonial.objects.get(qr_code=cambio.bien_qr_code)
        else:
            bien = BienPatrimonial.objects.get(codigo_patrimonial=cambio.bien_codigo_patrimonial)
        
        # Crear registro en historial con la foto
        # Nota: En una implementación real, la foto debería ser enviada como archivo
        # Por ahora, solo registramos el evento
        HistorialEstado.objects.create(
            bien=bien,
            estado_anterior=bien.estado_bien,
            estado_nuevo=bien.estado_bien,
            observaciones=datos.get('observaciones', 'Foto agregada desde dispositivo móvil'),
            usuario=cambio.usuario,
            ubicacion_gps=cambio.ubicacion_gps,
        )
        
        cambio.estado_sync = 'COMPLETADO'
        cambio.save()
        
        return {'estado': 'COMPLETADO', 'bien_id': bien.id}
        
    except BienPatrimonial.DoesNotExist:
        return crear_conflicto(cambio, 'BIEN_ELIMINADO', 
                             {'mensaje': 'El bien no existe en el servidor'})


def procesar_inventario(cambio):
    """
    Procesar registro de inventario
    """
    datos = cambio.get_datos_cambio()
    
    try:
        # Buscar el bien
        if cambio.bien_qr_code:
            bien = BienPatrimonial.objects.get(qr_code=cambio.bien_qr_code)
        else:
            bien = BienPatrimonial.objects.get(codigo_patrimonial=cambio.bien_codigo_patrimonial)
        
        # Crear registro de inventario
        HistorialEstado.objects.create(
            bien=bien,
            estado_anterior=bien.estado_bien,
            estado_nuevo=bien.estado_bien,
            observaciones=datos.get('observaciones', 'Inventario desde dispositivo móvil'),
            usuario=cambio.usuario,
            ubicacion_gps=cambio.ubicacion_gps,
        )
        
        cambio.estado_sync = 'COMPLETADO'
        cambio.save()
        
        return {'estado': 'COMPLETADO', 'bien_id': bien.id}
        
    except BienPatrimonial.DoesNotExist:
        return crear_conflicto(cambio, 'BIEN_ELIMINADO', 
                             {'mensaje': 'El bien no existe en el servidor'})


def crear_conflicto(cambio, tipo_conflicto, datos_servidor):
    """
    Crear un registro de conflicto
    """
    ConflictoSync.objects.create(
        cambio_offline=cambio,
        tipo_conflicto=tipo_conflicto,
        datos_servidor=datos_servidor,
        datos_cliente=cambio.get_datos_cambio()
    )
    
    cambio.estado_sync = 'CONFLICTO'
    cambio.save()
    
    return {'estado': 'CONFLICTO', 'tipo': tipo_conflicto}