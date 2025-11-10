"""
Tareas asíncronas generales del sistema
"""
import os
import tempfile
from datetime import datetime, timedelta
from django.conf import settings
from django.core.files import File
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.auth.models import User
from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


@shared_task(bind=True)
def importacion_masiva_excel(self, archivo_path, tipo_importacion, usuario_id, parametros=None):
    """
    Tarea asíncrona para importaciones masivas desde Excel
    
    Args:
        archivo_path: Ruta del archivo Excel a procesar
        tipo_importacion: 'catalogo', 'oficinas', 'bienes'
        usuario_id: ID del usuario que inició la importación
        parametros: Parámetros adicionales para la importación
    """
    try:
        from apps.catalogo.utils import ImportadorCatalogo
        from apps.oficinas.utils import ImportadorOficinas
        from apps.bienes.utils import ImportadorBienes
        
        usuario = User.objects.get(id=usuario_id)
        logger.info(f"Iniciando importación masiva {tipo_importacion} por usuario {usuario.username}")
        
        # Actualizar progreso inicial
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Iniciando importación...'}
        )
        
        resultado = None
        
        if tipo_importacion == 'catalogo':
            importador = ImportadorCatalogo()
            resultado = importador.importar_desde_excel(archivo_path, usuario)
            
        elif tipo_importacion == 'oficinas':
            importador = ImportadorOficinas()
            resultado = importador.importar_desde_excel(archivo_path, usuario)
            
        elif tipo_importacion == 'bienes':
            importador = ImportadorBienes()
            resultado = importador.importar_desde_excel(archivo_path, usuario, parametros)
            
        else:
            raise ValueError(f"Tipo de importación no soportado: {tipo_importacion}")
        
        # Actualizar progreso final
        self.update_state(
            state='SUCCESS',
            meta={
                'current': 100,
                'total': 100,
                'status': 'Importación completada',
                'resultado': resultado
            }
        )
        
        # Enviar notificación por email
        _enviar_notificacion_importacion_completada(usuario, tipo_importacion, resultado)
        
        logger.info(f"Importación {tipo_importacion} completada: {resultado}")
        
        # Limpiar archivo temporal
        try:
            if os.path.exists(archivo_path):
                os.remove(archivo_path)
        except OSError:
            pass
        
        return resultado
        
    except Exception as e:
        logger.error(f"Error en importación masiva {tipo_importacion}: {str(e)}")
        
        # Actualizar estado de error
        self.update_state(
            state='FAILURE',
            meta={
                'current': 0,
                'total': 100,
                'status': f'Error: {str(e)}',
                'error': str(e)
            }
        )
        
        # Limpiar archivo temporal
        try:
            if os.path.exists(archivo_path):
                os.remove(archivo_path)
        except OSError:
            pass
        
        raise


@shared_task
def generar_codigos_qr_masivo(bien_ids, usuario_id):
    """
    Tarea para generar códigos QR de forma masiva
    
    Args:
        bien_ids: Lista de IDs de bienes
        usuario_id: ID del usuario
    """
    try:
        from apps.bienes.models import BienPatrimonial
        from apps.bienes.utils import generar_qr_code
        
        usuario = User.objects.get(id=usuario_id)
        bienes = BienPatrimonial.objects.filter(id__in=bien_ids)
        
        logger.info(f"Generando {bienes.count()} códigos QR para usuario {usuario.username}")
        
        generados = 0
        errores = []
        
        for bien in bienes:
            try:
                if not bien.qr_code or not bien.url_qr:
                    qr_data = generar_qr_code(bien)
                    bien.qr_code = qr_data['qr_code']
                    bien.url_qr = qr_data['url_qr']
                    bien.save()
                    generados += 1
                    
            except Exception as e:
                errores.append({
                    'bien_id': bien.id,
                    'codigo_patrimonial': bien.codigo_patrimonial,
                    'error': str(e)
                })
        
        resultado = {
            'total_procesados': bienes.count(),
            'generados': generados,
            'errores': errores
        }
        
        logger.info(f"Generación QR completada: {resultado}")
        
        return resultado
        
    except Exception as e:
        logger.error(f"Error en generación masiva de QR: {str(e)}")
        raise


@shared_task
def limpiar_archivos_temporales():
    """
    Tarea programada para limpiar archivos temporales
    """
    try:
        import glob
        
        # Limpiar archivos temporales de más de 24 horas
        temp_dir = tempfile.gettempdir()
        patron = os.path.join(temp_dir, 'patrimonio_*')
        
        archivos_eliminados = 0
        limite_tiempo = timezone.now() - timedelta(hours=24)
        
        for archivo in glob.glob(patron):
            try:
                tiempo_modificacion = datetime.fromtimestamp(os.path.getmtime(archivo))
                if timezone.make_aware(tiempo_modificacion) < limite_tiempo:
                    os.remove(archivo)
                    archivos_eliminados += 1
            except OSError:
                continue
        
        logger.info(f"Se eliminaron {archivos_eliminados} archivos temporales")
        
        return {'archivos_eliminados': archivos_eliminados}
        
    except Exception as e:
        logger.error(f"Error limpiando archivos temporales: {str(e)}")
        raise


@shared_task
def backup_base_datos():
    """
    Tarea para realizar backup de la base de datos
    """
    try:
        import subprocess
        from django.conf import settings
        
        # Solo funciona con PostgreSQL
        db_config = settings.DATABASES['default']
        if db_config['ENGINE'] != 'django.db.backends.postgresql':
            logger.warning("Backup solo soportado para PostgreSQL")
            return {'status': 'skipped', 'reason': 'Base de datos no soportada'}
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"patrimonio_backup_{timestamp}.sql"
        backup_path = os.path.join(settings.MEDIA_ROOT, 'backups', backup_filename)
        
        # Crear directorio de backups si no existe
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        
        # Comando pg_dump
        comando = [
            'pg_dump',
            f"--host={db_config['HOST']}",
            f"--port={db_config['PORT']}",
            f"--username={db_config['USER']}",
            f"--dbname={db_config['NAME']}",
            f"--file={backup_path}",
            '--verbose',
            '--no-password'
        ]
        
        # Configurar variable de entorno para password
        env = os.environ.copy()
        env['PGPASSWORD'] = db_config['PASSWORD']
        
        # Ejecutar backup
        resultado = subprocess.run(comando, env=env, capture_output=True, text=True)
        
        if resultado.returncode == 0:
            # Comprimir backup
            import gzip
            with open(backup_path, 'rb') as f_in:
                with gzip.open(f"{backup_path}.gz", 'wb') as f_out:
                    f_out.writelines(f_in)
            
            # Eliminar archivo sin comprimir
            os.remove(backup_path)
            
            logger.info(f"Backup creado exitosamente: {backup_filename}.gz")
            
            return {
                'status': 'success',
                'archivo': f"{backup_filename}.gz",
                'timestamp': timestamp
            }
        else:
            logger.error(f"Error en backup: {resultado.stderr}")
            return {
                'status': 'error',
                'error': resultado.stderr
            }
            
    except Exception as e:
        logger.error(f"Error realizando backup: {str(e)}")
        raise


@shared_task
def cleanup_recycle_bin_task():
    """
    Tarea programada para limpiar la papelera de reciclaje
    Elimina permanentemente elementos que han excedido su tiempo de retención
    """
    try:
        from apps.core.models import RecycleBin, RecycleBinConfig, AuditLog
        from django.db import transaction
        
        logger.info("Iniciando limpieza automática de papelera de reciclaje")
        
        # Obtener elementos listos para eliminación automática
        elementos_para_eliminar = RecycleBin.objects.filter(
            restored_at__isnull=True,  # No restaurados
            auto_delete_at__lte=timezone.now()  # Tiempo de eliminación alcanzado
        )
        
        total_elementos = elementos_para_eliminar.count()
        
        if total_elementos == 0:
            logger.info("No hay elementos para eliminar en la papelera")
            return {'status': 'success', 'eliminados': 0, 'mensaje': 'No hay elementos para eliminar'}
        
        logger.info(f"Encontrados {total_elementos} elementos para eliminación automática")
        
        # Agrupar por módulo y verificar configuración
        modulos = elementos_para_eliminar.values('module_name').distinct()
        
        eliminados_total = 0
        errores = []
        modulos_procesados = {}
        
        for modulo_data in modulos:
            module_name = modulo_data['module_name']
            elementos_modulo = elementos_para_eliminar.filter(module_name=module_name)
            
            try:
                # Verificar configuración del módulo
                config = RecycleBinConfig.objects.get(module_name=module_name)
                
                if not config.auto_delete_enabled:
                    logger.info(
                        f"Eliminación automática deshabilitada para {module_name}, "
                        f"omitiendo {elementos_modulo.count()} elementos"
                    )
                    modulos_procesados[module_name] = {
                        'eliminados': 0,
                        'omitidos': elementos_modulo.count(),
                        'razon': 'auto_delete_disabled'
                    }
                    continue
                
            except RecycleBinConfig.DoesNotExist:
                logger.warning(
                    f"No hay configuración para {module_name}, "
                    f"usando configuración por defecto"
                )
            
            # Procesar eliminación para este módulo
            eliminados_modulo = 0
            
            for item in elementos_modulo:
                try:
                    with transaction.atomic():
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
                                    'deletion_reason': item.deletion_reason,
                                    'auto_delete_at': item.auto_delete_at.isoformat()
                                }
                            )
                            
                            # Eliminar permanentemente el objeto
                            obj.hard_delete()
                            
                            logger.info(
                                f"Eliminado permanentemente: {item.object_repr} "
                                f"(módulo: {item.module_name}, ID: {item.object_id})"
                            )
                        
                        # Eliminar entrada de RecycleBin
                        item.delete()
                        eliminados_modulo += 1
                        eliminados_total += 1
                        
                except Exception as e:
                    error_msg = f"Error eliminando {item.object_repr} (ID: {item.object_id}): {str(e)}"
                    logger.error(error_msg)
                    errores.append({
                        'object_repr': item.object_repr,
                        'object_id': item.object_id,
                        'module_name': item.module_name,
                        'error': str(e)
                    })
                    continue
            
            modulos_procesados[module_name] = {
                'eliminados': eliminados_modulo,
                'omitidos': 0,
                'razon': 'success'
            }
            
            logger.info(f"Módulo {module_name}: {eliminados_modulo} elementos eliminados")
        
        resultado = {
            'status': 'success',
            'eliminados': eliminados_total,
            'total_encontrados': total_elementos,
            'modulos': modulos_procesados,
            'errores': errores,
            'timestamp': timezone.now().isoformat()
        }
        
        logger.info(
            f"Limpieza automática completada: {eliminados_total} elementos eliminados, "
            f"{len(errores)} errores"
        )
        
        return resultado
        
    except Exception as e:
        logger.error(f"Error en limpieza automática de papelera: {str(e)}")
        raise


@shared_task
def send_recycle_bin_warnings():
    """
    Tarea programada para enviar notificaciones de advertencia
    sobre elementos próximos a eliminación automática (7 días antes)
    """
    try:
        from apps.core.models import RecycleBin, RecycleBinConfig
        from apps.notificaciones.models import Notificacion, TipoNotificacion, ConfiguracionNotificacion
        from django.db.models import Count
        
        logger.info("Iniciando verificación de advertencias de papelera (7 días)")
        
        # Obtener configuraciones de módulos con auto-delete habilitado
        configs = RecycleBinConfig.objects.filter(auto_delete_enabled=True)
        
        notificaciones_enviadas = 0
        usuarios_notificados = set()
        
        for config in configs:
            # Calcular fecha de advertencia (7 días antes de auto_delete_at)
            warning_date = timezone.now() + timedelta(days=7)
            warning_date_end = timezone.now() + timedelta(days=8)  # Ventana de 24 horas
            
            # Buscar elementos que necesitan advertencia
            items_warning = RecycleBin.objects.filter(
                module_name=config.module_name,
                restored_at__isnull=True,
                auto_delete_at__gte=warning_date,
                auto_delete_at__lt=warning_date_end
            )
            
            if not items_warning.exists():
                continue
            
            logger.info(
                f"Encontrados {items_warning.count()} elementos en {config.module_name} "
                f"que requieren advertencia de 7 días"
            )
            
            # Agrupar por usuario que eliminó
            usuarios_items = {}
            for item in items_warning:
                if not item.deleted_by:
                    continue
                    
                user_id = item.deleted_by.id
                if user_id not in usuarios_items:
                    usuarios_items[user_id] = {
                        'user': item.deleted_by,
                        'items': []
                    }
                usuarios_items[user_id]['items'].append(item)
            
            # Enviar notificaciones por usuario
            for user_id, data in usuarios_items.items():
                usuario = data['user']
                items = data['items']
                
                # Verificar si ya existe notificación reciente
                notificacion_existente = Notificacion.objects.filter(
                    usuario=usuario,
                    tipo_notificacion__codigo='RECYCLE_WARNING',
                    created_at__gte=timezone.now() - timedelta(days=6)
                ).exists()
                
                if notificacion_existente:
                    logger.info(
                        f"Usuario {usuario.username} ya tiene notificación reciente de advertencia"
                    )
                    continue
                
                # Verificar configuración del usuario
                try:
                    tipo_notificacion = TipoNotificacion.objects.get(codigo='RECYCLE_WARNING')
                except TipoNotificacion.DoesNotExist:
                    logger.warning("Tipo de notificación RECYCLE_WARNING no existe")
                    continue
                
                config_usuario = ConfiguracionNotificacion.objects.filter(
                    usuario=usuario,
                    tipo_notificacion=tipo_notificacion
                ).first()
                
                if config_usuario and not config_usuario.activa:
                    logger.info(
                        f"Usuario {usuario.username} tiene deshabilitadas notificaciones de advertencia"
                    )
                    continue
                
                # Preparar datos del contexto
                total_items = len(items)
                sample_items = []
                
                for item in items[:5]:  # Máximo 5 ejemplos
                    sample_items.append({
                        'module_display': item.get_module_display(),
                        'object_repr': item.object_repr,
                        'deleted_at': item.deleted_at.isoformat(),
                        'auto_delete_at': item.auto_delete_at.isoformat()
                    })
                
                datos_contexto = {
                    'total_items': total_items,
                    'retention_days': config.retention_days,
                    'sample_items': sample_items,
                    'module_name': config.module_name,
                    'module_display': config.get_module_name_display(),
                    'days_remaining': 7
                }
                
                # Crear notificación
                Notificacion.objects.create(
                    usuario=usuario,
                    tipo_notificacion=tipo_notificacion,
                    titulo=f"⚠️ Advertencia: {total_items} elemento(s) se eliminarán en 7 días",
                    mensaje=f"Tienes {total_items} elemento(s) en la papelera que serán eliminados permanentemente en 7 días. Revisa y restaura los que necesites conservar.",
                    prioridad='ALTA',
                    datos_contexto=datos_contexto,
                    url_accion='/core/recycle-bin/',
                    fecha_expiracion=timezone.now() + timedelta(days=7)
                )
                
                notificaciones_enviadas += 1
                usuarios_notificados.add(usuario.username)
                
                logger.info(
                    f"Notificación de advertencia (7 días) creada para {usuario.username}: "
                    f"{total_items} elementos"
                )
        
        resultado = {
            'status': 'success',
            'notificaciones_enviadas': notificaciones_enviadas,
            'usuarios_notificados': len(usuarios_notificados),
            'usuarios': list(usuarios_notificados),
            'timestamp': timezone.now().isoformat()
        }
        
        logger.info(
            f"Verificación de advertencias completada: {notificaciones_enviadas} notificaciones enviadas "
            f"a {len(usuarios_notificados)} usuarios"
        )
        
        return resultado
        
    except Exception as e:
        logger.error(f"Error enviando advertencias de papelera: {str(e)}")
        raise


@shared_task
def send_recycle_bin_final_warnings():
    """
    Tarea programada para enviar notificaciones finales de advertencia
    sobre elementos próximos a eliminación automática (1 día antes)
    """
    try:
        from apps.core.models import RecycleBin, RecycleBinConfig
        from apps.notificaciones.models import Notificacion, TipoNotificacion, ConfiguracionNotificacion
        
        logger.info("Iniciando verificación de advertencias finales de papelera (1 día)")
        
        # Obtener configuraciones de módulos con auto-delete habilitado
        configs = RecycleBinConfig.objects.filter(auto_delete_enabled=True)
        
        notificaciones_enviadas = 0
        usuarios_notificados = set()
        
        for config in configs:
            # Calcular fecha de advertencia final (1 día antes de auto_delete_at)
            final_warning_date = timezone.now() + timedelta(days=1)
            final_warning_date_end = timezone.now() + timedelta(days=2)  # Ventana de 24 horas
            
            # Buscar elementos que necesitan advertencia final
            items_final_warning = RecycleBin.objects.filter(
                module_name=config.module_name,
                restored_at__isnull=True,
                auto_delete_at__gte=final_warning_date,
                auto_delete_at__lt=final_warning_date_end
            )
            
            if not items_final_warning.exists():
                continue
            
            logger.info(
                f"Encontrados {items_final_warning.count()} elementos en {config.module_name} "
                f"que requieren advertencia final de 1 día"
            )
            
            # Agrupar por usuario que eliminó
            usuarios_items = {}
            for item in items_final_warning:
                if not item.deleted_by:
                    continue
                    
                user_id = item.deleted_by.id
                if user_id not in usuarios_items:
                    usuarios_items[user_id] = {
                        'user': item.deleted_by,
                        'items': []
                    }
                usuarios_items[user_id]['items'].append(item)
            
            # Enviar notificaciones por usuario
            for user_id, data in usuarios_items.items():
                usuario = data['user']
                items = data['items']
                
                # Verificar si ya existe notificación reciente
                notificacion_existente = Notificacion.objects.filter(
                    usuario=usuario,
                    tipo_notificacion__codigo='RECYCLE_FINAL_WARNING',
                    created_at__gte=timezone.now() - timedelta(hours=12)
                ).exists()
                
                if notificacion_existente:
                    logger.info(
                        f"Usuario {usuario.username} ya tiene notificación reciente de advertencia final"
                    )
                    continue
                
                # Verificar configuración del usuario
                try:
                    tipo_notificacion = TipoNotificacion.objects.get(codigo='RECYCLE_FINAL_WARNING')
                except TipoNotificacion.DoesNotExist:
                    logger.warning("Tipo de notificación RECYCLE_FINAL_WARNING no existe")
                    continue
                
                config_usuario = ConfiguracionNotificacion.objects.filter(
                    usuario=usuario,
                    tipo_notificacion=tipo_notificacion
                ).first()
                
                if config_usuario and not config_usuario.activa:
                    logger.info(
                        f"Usuario {usuario.username} tiene deshabilitadas notificaciones de advertencia final"
                    )
                    continue
                
                # Preparar datos del contexto
                total_items = len(items)
                sample_items = []
                
                # Calcular horas hasta eliminación
                min_hours = min([
                    int((item.auto_delete_at - timezone.now()).total_seconds() / 3600)
                    for item in items
                ])
                
                for item in items[:5]:  # Máximo 5 ejemplos
                    sample_items.append({
                        'module_display': item.get_module_display(),
                        'object_repr': item.object_repr,
                        'deleted_at': item.deleted_at.isoformat(),
                        'auto_delete_at': item.auto_delete_at.isoformat(),
                        'hours_remaining': max(0, int((item.auto_delete_at - timezone.now()).total_seconds() / 3600))
                    })
                
                datos_contexto = {
                    'total_items': total_items,
                    'retention_days': config.retention_days,
                    'sample_items': sample_items,
                    'module_name': config.module_name,
                    'module_display': config.get_module_name_display(),
                    'hours_remaining': max(0, min_hours),
                    'days_remaining': 1
                }
                
                # Crear notificación
                Notificacion.objects.create(
                    usuario=usuario,
                    tipo_notificacion=tipo_notificacion,
                    titulo=f"🚨 ADVERTENCIA FINAL: {total_items} elemento(s) se eliminarán en 24 horas",
                    mensaje=f"Tienes {total_items} elemento(s) en la papelera que serán eliminados permanentemente en las próximas 24 horas. Esta es tu última oportunidad para restaurarlos.",
                    prioridad='CRITICA',
                    datos_contexto=datos_contexto,
                    url_accion='/core/recycle-bin/',
                    fecha_expiracion=timezone.now() + timedelta(days=1)
                )
                
                notificaciones_enviadas += 1
                usuarios_notificados.add(usuario.username)
                
                logger.info(
                    f"Notificación de advertencia final (1 día) creada para {usuario.username}: "
                    f"{total_items} elementos"
                )
        
        resultado = {
            'status': 'success',
            'notificaciones_enviadas': notificaciones_enviadas,
            'usuarios_notificados': len(usuarios_notificados),
            'usuarios': list(usuarios_notificados),
            'timestamp': timezone.now().isoformat()
        }
        
        logger.info(
            f"Verificación de advertencias finales completada: {notificaciones_enviadas} notificaciones enviadas "
            f"a {len(usuarios_notificados)} usuarios"
        )
        
        return resultado
        
    except Exception as e:
        logger.error(f"Error enviando advertencias finales de papelera: {str(e)}")
        raise


def _enviar_notificacion_importacion_completada(usuario, tipo_importacion, resultado):
    """
    Envía notificación por email cuando se completa una importación
    """
    try:
        if not usuario.email:
            return
        
        tipo_nombres = {
            'catalogo': 'Catálogo',
            'oficinas': 'Oficinas',
            'bienes': 'Bienes Patrimoniales'
        }
        
        asunto = f"Importación de {tipo_nombres.get(tipo_importacion, tipo_importacion)} completada"
        
        contexto = {
            'usuario': usuario,
            'tipo_importacion': tipo_nombres.get(tipo_importacion, tipo_importacion),
            'resultado': resultado,
            'timestamp': timezone.now()
        }
        
        mensaje = render_to_string('core/email_importacion_completada.html', contexto)
        
        send_mail(
            asunto,
            mensaje,
            settings.DEFAULT_FROM_EMAIL,
            [usuario.email],
            html_message=mensaje,
            fail_silently=True
        )
        
        logger.info(f"Notificación de importación enviada a {usuario.email}")
        
    except Exception as e:
        logger.warning(f"No se pudo enviar notificación de importación: {str(e)}")