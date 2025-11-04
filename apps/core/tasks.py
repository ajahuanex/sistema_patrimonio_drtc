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