"""
Servicios centralizados para el sistema de papelera de reciclaje
"""
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from datetime import timedelta
from .models import RecycleBin, RecycleBinConfig, DeletionAuditLog, SecurityCodeAttempt


class RecycleBinService:
    """
    Servicio centralizado para operaciones de papelera de reciclaje
    """
    
    def soft_delete_object(self, obj, user, reason='', context=None):
        """
        Elimina lógicamente un objeto y crea entrada en papelera
        
        Args:
            obj: Objeto a eliminar
            user: Usuario que realiza la eliminación
            reason: Razón de la eliminación
            context: Contexto adicional (IP, user agent, etc.)
        
        Returns:
            dict: Resultado de la operación
        """
        try:
            # Realizar soft delete en el objeto
            if hasattr(obj, 'soft_delete'):
                obj.soft_delete(user=user, reason=reason)
            else:
                # Fallback si el objeto no tiene soft_delete
                obj.deleted_at = timezone.now()
                obj.deleted_by = user
                obj.deletion_reason = reason
                obj.save()
            
            # Crear entrada en papelera
            content_type = ContentType.objects.get_for_model(obj)
            recycle_entry = RecycleBin.objects.create(
                content_type=content_type,
                object_id=obj.id,
                object_repr=str(obj),
                module_name=obj._meta.app_label,
                deleted_by=user,
                deletion_reason=reason
            )
            
            # Registrar en auditoría
            DeletionAuditLog.log_soft_delete(
                obj=obj,
                user=user,
                reason=reason,
                ip_address=context.get('ip') if context else None,
                user_agent=context.get('user_agent') if context else None,
                recycle_bin_entry=recycle_entry
            )
            
            return {
                'success': True,
                'message': 'Objeto eliminado correctamente',
                'recycle_entry': recycle_entry
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error al eliminar objeto: {str(e)}'
            }
    
    def restore_object(self, obj, user, context=None):
        """
        Restaura un objeto eliminado lógicamente
        
        Args:
            obj: Objeto a restaurar
            user: Usuario que realiza la restauración
            context: Contexto adicional
        
        Returns:
            dict: Resultado de la operación
        """
        try:
            # Verificar que el objeto está eliminado
            if not hasattr(obj, 'is_deleted') or not obj.is_deleted:
                return {
                    'success': False,
                    'message': 'El objeto no está eliminado'
                }
            
            # Restaurar el objeto
            if hasattr(obj, 'restore'):
                obj.restore(user=user)
            else:
                # Fallback
                obj.deleted_at = None
                obj.deleted_by = None
                obj.deletion_reason = ''
                obj.save()
            
            # Actualizar entrada en papelera
            content_type = ContentType.objects.get_for_model(obj)
            recycle_entry = RecycleBin.objects.filter(
                content_type=content_type,
                object_id=obj.id,
                permanently_deleted_at__isnull=True
            ).first()
            
            if recycle_entry:
                recycle_entry.restored_at = timezone.now()
                recycle_entry.restored_by = user
                recycle_entry.save()
            
            # Registrar en auditoría
            DeletionAuditLog.log_restore(
                obj=obj,
                user=user,
                ip_address=context.get('ip') if context else None,
                user_agent=context.get('user_agent') if context else None,
                recycle_bin_entry=recycle_entry
            )
            
            return {
                'success': True,
                'message': 'Objeto restaurado correctamente',
                'recycle_entry': recycle_entry
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error al restaurar objeto: {str(e)}'
            }
    
    def permanent_delete(self, obj, user, security_code, context=None):
        """
        Elimina permanentemente un objeto de la base de datos
        
        Args:
            obj: Objeto a eliminar permanentemente
            user: Usuario que realiza la eliminación
            security_code: Código de seguridad para autorizar
            context: Contexto adicional
        
        Returns:
            dict: Resultado de la operación
        """
        try:
            # Validar código de seguridad
            expected_code = getattr(settings, 'PERMANENT_DELETE_CODE', 'PERMANENT_DELETE_2024')
            
            if security_code != expected_code:
                # Registrar intento fallido
                SecurityCodeAttempt.objects.create(
                    user=user,
                    attempt_type='permanent_delete',
                    success=False,
                    ip_address=context.get('ip') if context else None,
                    user_agent=context.get('user_agent') if context else None
                )
                
                return {
                    'success': False,
                    'message': 'Código de seguridad incorrecto'
                }
            
            # Obtener entrada en papelera antes de eliminar
            content_type = ContentType.objects.get_for_model(obj)
            recycle_entry = RecycleBin.objects.filter(
                content_type=content_type,
                object_id=obj.id
            ).first()
            
            # Registrar en auditoría ANTES de eliminar (para capturar snapshot)
            audit_log = DeletionAuditLog.log_permanent_delete(
                obj=obj,
                user=user,
                security_code_used=True,
                ip_address=context.get('ip') if context else None,
                user_agent=context.get('user_agent') if context else None,
                recycle_bin_entry=recycle_entry
            )
            
            # Actualizar entrada en papelera
            if recycle_entry:
                recycle_entry.permanently_deleted_at = timezone.now()
                recycle_entry.save()
            
            # Eliminar físicamente el objeto
            if hasattr(obj, 'hard_delete'):
                obj.hard_delete()
            else:
                obj.delete(force=True)
            
            # Registrar intento exitoso
            SecurityCodeAttempt.objects.create(
                user=user,
                attempt_type='permanent_delete',
                success=True,
                ip_address=context.get('ip') if context else None,
                user_agent=context.get('user_agent') if context else None
            )
            
            return {
                'success': True,
                'message': 'Objeto eliminado permanentemente',
                'audit_log': audit_log
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error al eliminar permanentemente: {str(e)}'
            }
    
    def auto_cleanup(self):
        """
        Ejecuta limpieza automática de elementos vencidos en papelera
        
        Returns:
            dict: Resultado de la operación con contadores
        """
        try:
            deleted_count = 0
            errors = []
            
            # Obtener elementos que deben ser eliminados automáticamente
            now = timezone.now()
            entries_to_delete = RecycleBin.objects.filter(
                auto_delete_at__lte=now,
                permanently_deleted_at__isnull=True,
                restored_at__isnull=True
            )
            
            for entry in entries_to_delete:
                try:
                    # Obtener el objeto original
                    obj = entry.get_deleted_object()
                    
                    if obj:
                        # Eliminar permanentemente (sin código de seguridad para auto-cleanup)
                        # Registrar en auditoría
                        audit_log = DeletionAuditLog.log_permanent_delete(
                            obj=obj,
                            user=None,  # Sistema automático
                            security_code_used=False,
                            recycle_bin_entry=entry
                        )
                        
                        # Actualizar entrada en papelera
                        entry.permanently_deleted_at = now
                        entry.save()
                        
                        # Eliminar físicamente
                        if hasattr(obj, 'hard_delete'):
                            obj.hard_delete()
                        else:
                            # Usar el manager all_objects para acceder a eliminados
                            obj.__class__.all_objects.filter(id=obj.id).delete()
                        
                        deleted_count += 1
                    else:
                        # El objeto ya no existe, solo actualizar entrada
                        entry.permanently_deleted_at = now
                        entry.save()
                        deleted_count += 1
                        
                except Exception as e:
                    errors.append(f'Error al eliminar {entry}: {str(e)}')
            
            return {
                'success': True,
                'deleted_count': deleted_count,
                'errors': errors
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error en limpieza automática: {str(e)}',
                'deleted_count': 0
            }
