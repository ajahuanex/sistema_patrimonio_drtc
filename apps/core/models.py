from django.db import models
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta


class SoftDeleteManager(models.Manager):
    """Manager personalizado que excluye automáticamente registros eliminados"""
    
    def get_queryset(self):
        """Retorna queryset excluyendo registros eliminados"""
        return super().get_queryset().filter(deleted_at__isnull=True)
    
    def deleted_only(self):
        """Retorna solo registros eliminados"""
        return super().get_queryset().filter(deleted_at__isnull=False)
    
    def with_deleted(self):
        """Retorna todos los registros, incluyendo eliminados"""
        return super().get_queryset()


class SoftDeleteMixin(models.Model):
    """Mixin para agregar funcionalidad de soft delete a cualquier modelo"""
    
    deleted_at = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name='Fecha de eliminación',
        help_text='Fecha y hora en que se eliminó el registro'
    )
    deleted_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='%(class)s_deleted',
        verbose_name='Eliminado por',
        help_text='Usuario que eliminó el registro'
    )
    deletion_reason = models.TextField(
        blank=True,
        verbose_name='Motivo de eliminación',
        help_text='Razón por la cual se eliminó el registro'
    )
    
    # Manager por defecto que excluye eliminados
    objects = SoftDeleteManager()
    
    # Manager para acceder a todos los registros
    all_objects = models.Manager()
    
    class Meta:
        abstract = True
    
    def soft_delete(self, user=None, reason=''):
        """
        Marca el registro como eliminado sin borrarlo físicamente
        
        Args:
            user: Usuario que realiza la eliminación
            reason: Motivo de la eliminación
        """
        if self.is_deleted:
            return False
            
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.deletion_reason = reason
        self.save(update_fields=['deleted_at', 'deleted_by', 'deletion_reason'])
        return True
    
    def restore(self, user=None):
        """
        Restaura un registro eliminado
        
        Args:
            user: Usuario que realiza la restauración
        """
        if not self.is_deleted:
            return False
            
        self.deleted_at = None
        self.deleted_by = None
        self.deletion_reason = ''
        
        # Actualizar campos de auditoría si existen
        if hasattr(self, 'updated_by'):
            self.updated_by = user
            
        self.save()
        return True
    
    def hard_delete(self):
        """
        Elimina permanentemente el registro de la base de datos
        """
        super().delete()
    
    @property
    def is_deleted(self):
        """Retorna True si el registro está eliminado"""
        return self.deleted_at is not None
    
    def delete(self, using=None, keep_parents=False):
        """
        Sobrescribe el método delete para usar soft delete por defecto
        Para eliminación permanente usar hard_delete()
        """
        # Por defecto usar soft delete
        return self.soft_delete()


class BaseModel(SoftDeleteMixin, models.Model):
    """Modelo base con campos de auditoría y soft delete"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        related_name='%(class)s_created',
        null=True, 
        blank=True
    )
    updated_by = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        related_name='%(class)s_updated',
        null=True, 
        blank=True
    )

    class Meta:
        abstract = True
    
    def get_str_with_delete_status(self, base_str):
        """
        Helper method para agregar estado de eliminación al __str__
        
        Args:
            base_str: String base del modelo
            
        Returns:
            str: String con indicador de eliminación si aplica
        """
        if self.is_deleted:
            return f"{base_str} [ELIMINADO]"
        return base_str


class UserProfile(models.Model):
    """Perfil extendido de usuario con información adicional"""
    ROLES = [
        ('administrador', 'Administrador'),
        ('funcionario', 'Funcionario'),
        ('auditor', 'Auditor'),
        ('consulta', 'Consulta'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLES, default='consulta')
    telefono = models.CharField(max_length=20, blank=True)
    cargo = models.CharField(max_length=100, blank=True)
    oficina = models.ForeignKey(
        'oficinas.Oficina', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='usuarios'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Perfil de Usuario'
        verbose_name_plural = 'Perfiles de Usuario'

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.get_role_display()}"

    @property
    def is_administrador(self):
        return self.role == 'administrador'

    @property
    def is_funcionario(self):
        return self.role == 'funcionario'

    @property
    def is_auditor(self):
        return self.role == 'auditor'

    @property
    def is_consulta(self):
        return self.role == 'consulta'

    def can_manage_users(self):
        """Solo administradores pueden gestionar usuarios"""
        return self.is_administrador

    def can_create_bienes(self):
        """Administradores y funcionarios pueden crear bienes"""
        return self.role in ['administrador', 'funcionario']

    def can_edit_bienes(self):
        """Administradores y funcionarios pueden editar bienes"""
        return self.role in ['administrador', 'funcionario']

    def can_delete_bienes(self):
        """Solo administradores pueden eliminar bienes"""
        return self.is_administrador

    def can_import_data(self):
        """Administradores y funcionarios pueden importar datos"""
        return self.role in ['administrador', 'funcionario']

    def can_export_data(self):
        """Todos excepto consulta pueden exportar datos"""
        return self.role in ['administrador', 'funcionario', 'auditor']

    def can_generate_reports(self):
        """Todos los roles pueden generar reportes"""
        return True

    def can_manage_catalogo(self):
        """Solo administradores pueden gestionar catálogo"""
        return self.is_administrador

    def can_manage_oficinas(self):
        """Solo administradores pueden gestionar oficinas"""
        return self.is_administrador

    def can_update_mobile(self):
        """Administradores y funcionarios pueden actualizar desde móvil"""
        return self.role in ['administrador', 'funcionario']
    
    # ========================================================================
    # PERMISOS DE PAPELERA DE RECICLAJE
    # ========================================================================
    
    def can_view_recycle_bin(self):
        """
        Verifica si el usuario puede ver la papelera de reciclaje.
        Todos los roles pueden ver la papelera, pero con diferentes niveles de acceso.
        """
        return self.is_active and self.role in ['administrador', 'funcionario', 'auditor']
    
    def can_view_all_recycle_items(self):
        """
        Verifica si el usuario puede ver todos los elementos en la papelera.
        Solo administradores y auditores pueden ver elementos de otros usuarios.
        """
        return self.is_active and self.role in ['administrador', 'auditor']
    
    def can_restore_items(self):
        """
        Verifica si el usuario puede restaurar elementos de la papelera.
        Administradores y funcionarios pueden restaurar elementos.
        """
        return self.is_active and self.role in ['administrador', 'funcionario']
    
    def can_restore_own_items(self):
        """
        Verifica si el usuario puede restaurar sus propios elementos.
        Administradores y funcionarios pueden restaurar sus propios elementos.
        """
        return self.is_active and self.role in ['administrador', 'funcionario']
    
    def can_restore_others_items(self):
        """
        Verifica si el usuario puede restaurar elementos de otros usuarios.
        Solo administradores pueden restaurar elementos de otros.
        """
        return self.is_active and self.is_administrador
    
    def can_permanent_delete(self):
        """
        Verifica si el usuario puede eliminar permanentemente elementos.
        Solo administradores pueden eliminar permanentemente.
        """
        return self.is_active and self.is_administrador
    
    def can_view_deletion_audit_logs(self):
        """
        Verifica si el usuario puede ver logs de auditoría de eliminaciones.
        Administradores y auditores pueden ver logs de auditoría.
        """
        return self.is_active and self.role in ['administrador', 'auditor']
    
    def can_manage_recycle_config(self):
        """
        Verifica si el usuario puede gestionar la configuración de la papelera.
        Solo administradores pueden gestionar la configuración.
        """
        return self.is_active and self.is_administrador
    
    def can_bulk_restore(self):
        """
        Verifica si el usuario puede restaurar elementos en lote.
        Administradores y funcionarios pueden restaurar en lote.
        """
        return self.is_active and self.role in ['administrador', 'funcionario']
    
    def can_bulk_permanent_delete(self):
        """
        Verifica si el usuario puede eliminar permanentemente en lote.
        Solo administradores pueden eliminar permanentemente en lote.
        """
        return self.is_active and self.is_administrador


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Crear perfil automáticamente cuando se crea un usuario"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Guardar perfil cuando se guarda el usuario"""
    if hasattr(instance, 'profile'):
        instance.profile.save()


class AuditLog(models.Model):
    """Registro de auditoría para acciones importantes"""
    ACTION_CHOICES = [
        ('create', 'Crear'),
        ('update', 'Actualizar'),
        ('delete', 'Eliminar'),
        ('login', 'Iniciar Sesión'),
        ('logout', 'Cerrar Sesión'),
        ('export', 'Exportar'),
        ('import', 'Importar'),
        ('view', 'Ver'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100, blank=True)
    object_repr = models.CharField(max_length=200, blank=True)
    changes = models.JSONField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Registro de Auditoría'
        verbose_name_plural = 'Registros de Auditoría'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.username} - {self.get_action_display()} - {self.model_name} - {self.timestamp}"


class RecycleBin(models.Model):
    """
    Modelo centralizado para gestionar elementos en papelera de reciclaje.
    Utiliza GenericForeignKey para referenciar cualquier tipo de objeto eliminado.
    """
    
    # Referencia genérica al objeto eliminado
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name='Tipo de contenido',
        help_text='Tipo de modelo del objeto eliminado'
    )
    object_id = models.PositiveIntegerField(
        verbose_name='ID del objeto',
        help_text='ID del objeto eliminado'
    )
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Metadatos del objeto eliminado
    object_repr = models.CharField(
        max_length=500,
        verbose_name='Representación del objeto',
        help_text='Representación en texto del objeto eliminado'
    )
    module_name = models.CharField(
        max_length=100,
        verbose_name='Nombre del módulo',
        help_text='Módulo al que pertenece el objeto (oficinas, bienes, catalogo)'
    )
    
    # Campos de auditoría
    deleted_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de eliminación',
        help_text='Fecha y hora en que se eliminó el objeto'
    )
    deleted_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='recycle_bin_deletions',
        verbose_name='Eliminado por',
        help_text='Usuario que eliminó el objeto'
    )
    deletion_reason = models.TextField(
        blank=True,
        verbose_name='Motivo de eliminación',
        help_text='Razón por la cual se eliminó el objeto'
    )
    
    # Campos para restauración
    restored_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de restauración',
        help_text='Fecha y hora en que se restauró el objeto'
    )
    restored_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='recycle_bin_restorations',
        verbose_name='Restaurado por',
        help_text='Usuario que restauró el objeto'
    )
    
    # Configuración de eliminación automática
    auto_delete_at = models.DateTimeField(
        verbose_name='Eliminación automática',
        help_text='Fecha y hora en que se eliminará automáticamente'
    )
    
    # Metadatos adicionales
    original_data = models.JSONField(
        blank=True,
        null=True,
        verbose_name='Datos originales',
        help_text='Snapshot de los datos del objeto antes de eliminación'
    )
    
    class Meta:
        verbose_name = 'Elemento en Papelera'
        verbose_name_plural = 'Elementos en Papelera'
        ordering = ['-deleted_at']
        
        # Índices para optimizar consultas frecuentes
        indexes = [
            models.Index(fields=['deleted_at'], name='recycle_deleted_at_idx'),
            models.Index(fields=['deleted_by'], name='recycle_deleted_by_idx'),
            models.Index(fields=['auto_delete_at'], name='recycle_auto_delete_idx'),
            models.Index(fields=['module_name'], name='recycle_module_name_idx'),
            models.Index(fields=['content_type', 'object_id'], name='recycle_content_idx'),
            models.Index(fields=['restored_at'], name='recycle_restored_at_idx'),
        ]
        
        # Constraint para evitar duplicados activos
        constraints = [
            models.UniqueConstraint(
                fields=['content_type', 'object_id'],
                condition=models.Q(restored_at__isnull=True),
                name='unique_active_recycle_entry'
            )
        ]
    
    def __str__(self):
        status = "Restaurado" if self.is_restored else "En papelera"
        return f"{self.object_repr} ({self.module_name}) - {status}"
    
    @property
    def is_restored(self):
        """Retorna True si el objeto ha sido restaurado"""
        return self.restored_at is not None
    
    @property
    def days_until_auto_delete(self):
        """Retorna los días restantes hasta la eliminación automática"""
        if self.is_restored:
            return None
        
        remaining = self.auto_delete_at - timezone.now()
        return max(0, remaining.days)
    
    @property
    def is_near_auto_delete(self):
        """Retorna True si faltan 7 días o menos para la eliminación automática"""
        days_remaining = self.days_until_auto_delete
        return days_remaining is not None and days_remaining <= 7
    
    @property
    def is_ready_for_auto_delete(self):
        """Retorna True si ya es tiempo de eliminación automática"""
        return not self.is_restored and timezone.now() >= self.auto_delete_at
    
    def mark_as_restored(self, user):
        """
        Marca el elemento como restaurado
        
        Args:
            user: Usuario que realiza la restauración
        """
        self.restored_at = timezone.now()
        self.restored_by = user
        self.save(update_fields=['restored_at', 'restored_by'])
    
    def get_module_display(self):
        """Retorna el nombre del módulo en formato legible"""
        module_names = {
            'oficinas': 'Oficinas',
            'bienes': 'Bienes Patrimoniales',
            'catalogo': 'Catálogo',
            'core': 'Sistema',
        }
        return module_names.get(self.module_name, self.module_name.title())
    
    def can_be_restored_by(self, user):
        """
        Verifica si un usuario puede restaurar este elemento
        
        Args:
            user: Usuario a verificar
            
        Returns:
            bool: True si el usuario puede restaurar el elemento
        """
        if self.is_restored:
            return False
        
        # Los administradores pueden restaurar cualquier elemento
        if hasattr(user, 'profile') and user.profile.is_administrador:
            return True
        
        # Los usuarios pueden restaurar solo elementos que ellos eliminaron
        return self.deleted_by == user
    
    def save(self, *args, **kwargs):
        """
        Sobrescribe save para establecer auto_delete_at si no está definido
        """
        if not self.auto_delete_at and not self.is_restored:
            # Establecer deleted_at si no está definido
            if not self.deleted_at:
                self.deleted_at = timezone.now()
            
            # Obtener configuración de retención por módulo (por defecto 30 días)
            retention_days = self.get_retention_days_for_module()
            self.auto_delete_at = self.deleted_at + timedelta(days=retention_days)
        
        super().save(*args, **kwargs)
    
    def get_retention_days_for_module(self):
        """
        Obtiene los días de retención configurados para el módulo
        
        Returns:
            int: Días de retención (por defecto 30)
        """
        try:
            config = RecycleBinConfig.objects.get(module_name=self.module_name)
            return config.retention_days
        except RecycleBinConfig.DoesNotExist:
            return 30  # Valor por defecto


class SecurityCodeAttempt(models.Model):
    """
    Registro de intentos de uso del código de seguridad para eliminación permanente.
    Incluye sistema de rate limiting y bloqueo temporal para protección contra ataques.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Usuario',
        help_text='Usuario que intentó usar el código'
    )
    attempted_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha del intento',
        help_text='Fecha y hora del intento'
    )
    success = models.BooleanField(
        default=False,
        verbose_name='Exitoso',
        help_text='Si el intento fue exitoso'
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='Dirección IP',
        help_text='Dirección IP desde donde se realizó el intento'
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name='User Agent',
        help_text='User Agent del navegador'
    )
    recycle_bin_entry_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='ID de entrada en papelera',
        help_text='ID de la entrada de RecycleBin que se intentó eliminar'
    )
    
    # Campos adicionales para protección contra ataques
    attempt_type = models.CharField(
        max_length=50,
        default='permanent_delete',
        verbose_name='Tipo de intento',
        help_text='Tipo de operación que requirió código de seguridad',
        choices=[
            ('permanent_delete', 'Eliminación Permanente'),
            ('bulk_delete', 'Eliminación en Lote'),
            ('config_change', 'Cambio de Configuración'),
        ]
    )
    blocked_by_rate_limit = models.BooleanField(
        default=False,
        verbose_name='Bloqueado por rate limit',
        help_text='Si el intento fue bloqueado por rate limiting'
    )
    requires_captcha = models.BooleanField(
        default=False,
        verbose_name='Requiere CAPTCHA',
        help_text='Si este intento requirió validación CAPTCHA'
    )
    captcha_passed = models.BooleanField(
        null=True,
        blank=True,
        verbose_name='CAPTCHA aprobado',
        help_text='Si el usuario pasó la validación CAPTCHA'
    )
    session_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='ID de sesión',
        help_text='Identificador de sesión del usuario'
    )
    request_path = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='Ruta de solicitud',
        help_text='Ruta URL de la solicitud'
    )
    referer = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='Referer',
        help_text='URL de referencia de la solicitud'
    )
    
    class Meta:
        verbose_name = 'Intento de Código de Seguridad'
        verbose_name_plural = 'Intentos de Código de Seguridad'
        ordering = ['-attempted_at']
        indexes = [
            models.Index(fields=['user', 'attempted_at'], name='security_user_time_idx'),
            models.Index(fields=['attempted_at'], name='security_time_idx'),
        ]
    
    def __str__(self):
        status = "Exitoso" if self.success else "Fallido"
        return f"{self.user.username} - {status} - {self.attempted_at}"
    
    @classmethod
    def get_recent_failed_attempts(cls, user, minutes=30):
        """
        Obtiene los intentos fallidos recientes de un usuario
        
        Args:
            user: Usuario a verificar
            minutes: Ventana de tiempo en minutos
            
        Returns:
            QuerySet: Intentos fallidos en el período especificado
        """
        from datetime import timedelta
        cutoff_time = timezone.now() - timedelta(minutes=minutes)
        return cls.objects.filter(
            user=user,
            success=False,
            attempted_at__gte=cutoff_time
        )
    
    @classmethod
    def is_user_locked_out(cls, user, max_attempts=3, lockout_minutes=30):
        """
        Verifica si un usuario está bloqueado temporalmente por múltiples intentos fallidos.
        Implementa sistema de bloqueo progresivo.
        
        Args:
            user: Usuario a verificar
            max_attempts: Número máximo de intentos fallidos permitidos
            lockout_minutes: Duración del bloqueo en minutos
            
        Returns:
            tuple: (is_locked: bool, attempts_count: int, time_remaining: int)
        """
        recent_failures = cls.get_recent_failed_attempts(user, lockout_minutes)
        attempts_count = recent_failures.count()
        
        if attempts_count >= max_attempts:
            # Calcular tiempo restante de bloqueo
            oldest_attempt = recent_failures.order_by('attempted_at').first()
            if oldest_attempt:
                from datetime import timedelta
                unlock_time = oldest_attempt.attempted_at + timedelta(minutes=lockout_minutes)
                time_remaining = (unlock_time - timezone.now()).total_seconds() / 60
                return True, attempts_count, max(0, int(time_remaining))
        
        return False, attempts_count, 0
    
    @classmethod
    def requires_captcha_validation(cls, user, captcha_threshold=2):
        """
        Verifica si un usuario requiere validación CAPTCHA basado en intentos fallidos recientes.
        
        Args:
            user: Usuario a verificar
            captcha_threshold: Número de intentos fallidos antes de requerir CAPTCHA
            
        Returns:
            bool: True si requiere CAPTCHA
        """
        recent_failures = cls.get_recent_failed_attempts(user, minutes=30)
        return recent_failures.count() >= captcha_threshold
    
    @classmethod
    def check_rate_limit(cls, user, max_requests=5, time_window_minutes=10):
        """
        Verifica si un usuario ha excedido el límite de intentos en una ventana de tiempo.
        Implementa rate limiting para prevenir ataques de fuerza bruta.
        
        Args:
            user: Usuario a verificar
            max_requests: Número máximo de intentos permitidos
            time_window_minutes: Ventana de tiempo en minutos
            
        Returns:
            tuple: (is_rate_limited: bool, attempts_count: int, time_until_reset: int)
        """
        from datetime import timedelta
        cutoff_time = timezone.now() - timedelta(minutes=time_window_minutes)
        
        recent_attempts = cls.objects.filter(
            user=user,
            attempted_at__gte=cutoff_time
        )
        
        attempts_count = recent_attempts.count()
        
        if attempts_count >= max_requests:
            # Calcular tiempo hasta que se resetee el límite
            oldest_attempt = recent_attempts.order_by('attempted_at').first()
            if oldest_attempt:
                reset_time = oldest_attempt.attempted_at + timedelta(minutes=time_window_minutes)
                time_until_reset = (reset_time - timezone.now()).total_seconds() / 60
                return True, attempts_count, max(0, int(time_until_reset))
        
        return False, attempts_count, 0
    
    @classmethod
    def get_lockout_level(cls, user):
        """
        Determina el nivel de bloqueo del usuario basado en el historial de intentos.
        Implementa bloqueo progresivo: más intentos = bloqueos más largos.
        
        Args:
            user: Usuario a verificar
            
        Returns:
            dict: Información del nivel de bloqueo
        """
        # Contar intentos fallidos en las últimas 24 horas
        from datetime import timedelta
        last_24h = timezone.now() - timedelta(hours=24)
        
        total_failures = cls.objects.filter(
            user=user,
            success=False,
            attempted_at__gte=last_24h
        ).count()
        
        # Definir niveles de bloqueo progresivo
        if total_failures >= 10:
            return {
                'level': 3,
                'name': 'Crítico',
                'lockout_minutes': 120,  # 2 horas
                'max_attempts': 1,
                'requires_admin_unlock': True
            }
        elif total_failures >= 6:
            return {
                'level': 2,
                'name': 'Alto',
                'lockout_minutes': 60,  # 1 hora
                'max_attempts': 2,
                'requires_admin_unlock': False
            }
        elif total_failures >= 3:
            return {
                'level': 1,
                'name': 'Medio',
                'lockout_minutes': 30,
                'max_attempts': 3,
                'requires_admin_unlock': False
            }
        else:
            return {
                'level': 0,
                'name': 'Normal',
                'lockout_minutes': 30,
                'max_attempts': 3,
                'requires_admin_unlock': False
            }
    
    @classmethod
    def record_attempt(cls, user, success, ip_address=None, user_agent=None, 
                      entry_id=None, attempt_type='permanent_delete', 
                      blocked_by_rate_limit=False, requires_captcha=False,
                      captcha_passed=None, session_id='', request_path='', referer=''):
        """
        Registra un intento de uso del código de seguridad con información detallada.
        
        Args:
            user: Usuario que realizó el intento
            success: Si el intento fue exitoso
            ip_address: Dirección IP del usuario
            user_agent: User Agent del navegador
            entry_id: ID de la entrada de RecycleBin
            attempt_type: Tipo de operación
            blocked_by_rate_limit: Si fue bloqueado por rate limiting
            requires_captcha: Si requirió CAPTCHA
            captcha_passed: Si pasó la validación CAPTCHA
            session_id: ID de sesión
            request_path: Ruta de la solicitud
            referer: URL de referencia
            
        Returns:
            SecurityCodeAttempt: Instancia creada
        """
        return cls.objects.create(
            user=user,
            success=success,
            ip_address=ip_address,
            user_agent=user_agent,
            recycle_bin_entry_id=entry_id,
            attempt_type=attempt_type,
            blocked_by_rate_limit=blocked_by_rate_limit,
            requires_captcha=requires_captcha,
            captcha_passed=captcha_passed,
            session_id=session_id,
            request_path=request_path,
            referer=referer
        )
    
    @classmethod
    def get_security_summary(cls, user, hours=24):
        """
        Obtiene un resumen de seguridad del usuario con estadísticas de intentos.
        
        Args:
            user: Usuario a analizar
            hours: Horas hacia atrás para el análisis
            
        Returns:
            dict: Resumen de seguridad
        """
        from datetime import timedelta
        cutoff_time = timezone.now() - timedelta(hours=hours)
        
        attempts = cls.objects.filter(
            user=user,
            attempted_at__gte=cutoff_time
        )
        
        total_attempts = attempts.count()
        failed_attempts = attempts.filter(success=False).count()
        successful_attempts = attempts.filter(success=True).count()
        captcha_required = attempts.filter(requires_captcha=True).count()
        rate_limited = attempts.filter(blocked_by_rate_limit=True).count()
        
        # Obtener nivel de bloqueo actual
        lockout_level = cls.get_lockout_level(user)
        
        # Verificar estado actual
        is_locked, attempts_count, time_remaining = cls.is_user_locked_out(user)
        requires_captcha_now = cls.requires_captcha_validation(user)
        is_rate_limited, rate_count, rate_reset = cls.check_rate_limit(user)
        
        return {
            'total_attempts': total_attempts,
            'failed_attempts': failed_attempts,
            'successful_attempts': successful_attempts,
            'captcha_required_count': captcha_required,
            'rate_limited_count': rate_limited,
            'lockout_level': lockout_level,
            'current_status': {
                'is_locked': is_locked,
                'failed_attempts_count': attempts_count,
                'time_remaining_minutes': time_remaining,
                'requires_captcha': requires_captcha_now,
                'is_rate_limited': is_rate_limited,
                'rate_limit_count': rate_count,
                'rate_limit_reset_minutes': rate_reset
            },
            'period_hours': hours
        }
    
    @classmethod
    def log_unauthorized_access_attempt(cls, user, ip_address, user_agent, 
                                       request_path, referer='', reason=''):
        """
        Registra un intento de acceso no autorizado con información detallada.
        
        Args:
            user: Usuario que intentó el acceso
            ip_address: Dirección IP
            user_agent: User Agent del navegador
            request_path: Ruta solicitada
            referer: URL de referencia
            reason: Razón del rechazo
            
        Returns:
            SecurityCodeAttempt: Instancia creada
        """
        from .models import DeletionAuditLog
        
        # Registrar en SecurityCodeAttempt
        attempt = cls.record_attempt(
            user=user,
            success=False,
            ip_address=ip_address,
            user_agent=user_agent,
            attempt_type='unauthorized_access',
            request_path=request_path,
            referer=referer
        )
        
        # Registrar en DeletionAuditLog para auditoría completa
        DeletionAuditLog.objects.create(
            action='unauthorized_access',
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={
                'reason': reason,
                'request_path': request_path,
                'referer': referer,
                'timestamp': timezone.now().isoformat()
            }
        )
        
        return attempt
    
    @classmethod
    def get_suspicious_activity_report(cls, hours=24):
        """
        Genera un reporte de actividad sospechosa en el sistema.
        
        Args:
            hours: Horas hacia atrás para el análisis
            
        Returns:
            dict: Reporte de actividad sospechosa
        """
        from datetime import timedelta
        from django.db.models import Count
        
        cutoff_time = timezone.now() - timedelta(hours=hours)
        
        attempts = cls.objects.filter(attempted_at__gte=cutoff_time)
        
        # Usuarios con más intentos fallidos
        users_with_failures = attempts.filter(success=False).values(
            'user__username', 'user__id'
        ).annotate(
            failure_count=Count('id')
        ).order_by('-failure_count')[:10]
        
        # IPs con más intentos fallidos
        ips_with_failures = attempts.filter(success=False).values(
            'ip_address'
        ).annotate(
            failure_count=Count('id')
        ).order_by('-failure_count')[:10]
        
        # Intentos bloqueados por rate limiting
        rate_limited_attempts = attempts.filter(blocked_by_rate_limit=True).count()
        
        # Usuarios actualmente bloqueados
        locked_users = []
        for user_data in users_with_failures:
            from django.contrib.auth.models import User
            try:
                user = User.objects.get(id=user_data['user__id'])
                is_locked, _, time_remaining = cls.is_user_locked_out(user)
                if is_locked:
                    locked_users.append({
                        'username': user_data['user__username'],
                        'failure_count': user_data['failure_count'],
                        'time_remaining': time_remaining
                    })
            except User.DoesNotExist:
                pass
        
        return {
            'period_hours': hours,
            'total_attempts': attempts.count(),
            'failed_attempts': attempts.filter(success=False).count(),
            'successful_attempts': attempts.filter(success=True).count(),
            'rate_limited_attempts': rate_limited_attempts,
            'users_with_most_failures': list(users_with_failures),
            'ips_with_most_failures': list(ips_with_failures),
            'currently_locked_users': locked_users,
            'captcha_required_attempts': attempts.filter(requires_captcha=True).count(),
            'unauthorized_access_attempts': attempts.filter(
                attempt_type='unauthorized_access'
            ).count()
        }


class DeletionAuditLog(models.Model):
    """
    Registro de auditoría específico para operaciones de eliminación y papelera.
    Proporciona trazabilidad completa de todas las acciones relacionadas con soft delete,
    restauración y eliminación permanente.
    """
    
    ACTION_CHOICES = [
        ('soft_delete', 'Eliminación Lógica'),
        ('restore', 'Restauración'),
        ('permanent_delete', 'Eliminación Permanente'),
        ('auto_delete', 'Eliminación Automática'),
        ('bulk_restore', 'Restauración en Lote'),
        ('bulk_delete', 'Eliminación en Lote'),
        ('failed_restore', 'Restauración Fallida'),
        ('failed_delete', 'Eliminación Fallida'),
    ]
    
    # Acción realizada
    action = models.CharField(
        max_length=30,
        choices=ACTION_CHOICES,
        verbose_name='Acción',
        help_text='Tipo de acción realizada'
    )
    
    # Usuario que realizó la acción
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='deletion_audit_logs',
        verbose_name='Usuario',
        help_text='Usuario que realizó la acción'
    )
    
    # Información del objeto afectado
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name='Tipo de contenido',
        help_text='Tipo de modelo del objeto afectado'
    )
    object_id = models.PositiveIntegerField(
        verbose_name='ID del objeto',
        help_text='ID del objeto afectado'
    )
    object_repr = models.CharField(
        max_length=500,
        verbose_name='Representación del objeto',
        help_text='Representación en texto del objeto'
    )
    module_name = models.CharField(
        max_length=100,
        verbose_name='Módulo',
        help_text='Módulo al que pertenece el objeto'
    )
    
    # Timestamp de la acción
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha y hora',
        help_text='Fecha y hora en que se realizó la acción',
        db_index=True
    )
    
    # Contexto de la acción
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='Dirección IP',
        help_text='Dirección IP desde donde se realizó la acción'
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name='User Agent',
        help_text='User Agent del navegador utilizado'
    )
    
    # Motivo de la acción
    reason = models.TextField(
        blank=True,
        verbose_name='Motivo',
        help_text='Motivo o razón de la acción'
    )
    
    # Snapshot de datos del objeto (especialmente importante para eliminación permanente)
    object_snapshot = models.JSONField(
        null=True,
        blank=True,
        verbose_name='Snapshot del objeto',
        help_text='Copia de los datos del objeto antes de la acción'
    )
    
    # Estado anterior (para restauraciones)
    previous_state = models.JSONField(
        null=True,
        blank=True,
        verbose_name='Estado anterior',
        help_text='Estado del objeto antes de la acción'
    )
    
    # Información adicional específica de la acción
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Metadatos',
        help_text='Información adicional sobre la acción'
    )
    
    # Resultado de la acción
    success = models.BooleanField(
        default=True,
        verbose_name='Exitoso',
        help_text='Si la acción se completó exitosamente'
    )
    error_message = models.TextField(
        blank=True,
        verbose_name='Mensaje de error',
        help_text='Mensaje de error si la acción falló'
    )
    
    # Referencia a la entrada de RecycleBin (si aplica)
    recycle_bin_entry = models.ForeignKey(
        'RecycleBin',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        verbose_name='Entrada en papelera',
        help_text='Referencia a la entrada en RecycleBin'
    )
    
    # Código de seguridad usado (solo para eliminación permanente)
    security_code_used = models.BooleanField(
        default=False,
        verbose_name='Código de seguridad usado',
        help_text='Si se usó código de seguridad para la eliminación permanente'
    )
    
    class Meta:
        verbose_name = 'Registro de Auditoría de Eliminación'
        verbose_name_plural = 'Registros de Auditoría de Eliminación'
        ordering = ['-timestamp']
        
        # Índices para optimizar consultas frecuentes
        indexes = [
            models.Index(fields=['timestamp'], name='deletion_audit_time_idx'),
            models.Index(fields=['user', 'timestamp'], name='deletion_audit_user_time_idx'),
            models.Index(fields=['action', 'timestamp'], name='deletion_audit_action_time_idx'),
            models.Index(fields=['module_name', 'timestamp'], name='deletion_audit_module_time_idx'),
            models.Index(fields=['content_type', 'object_id'], name='deletion_audit_content_idx'),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_action_display()} - {self.object_repr} - {self.timestamp}"
    
    @classmethod
    def log_soft_delete(cls, obj, user, reason='', ip_address=None, user_agent=None, recycle_bin_entry=None):
        """
        Registra una eliminación lógica (soft delete)
        
        Args:
            obj: Objeto que se está eliminando
            user: Usuario que realiza la eliminación
            reason: Motivo de la eliminación
            ip_address: Dirección IP del usuario
            user_agent: User Agent del navegador
            recycle_bin_entry: Entrada de RecycleBin asociada
            
        Returns:
            DeletionAuditLog: Registro de auditoría creado
        """
        from django.forms.models import model_to_dict
        
        # Crear snapshot del objeto
        try:
            snapshot = model_to_dict(obj, exclude=['deleted_at', 'deleted_by', 'deletion_reason'])
            # Convertir valores no serializables
            for key, value in snapshot.items():
                if hasattr(value, 'pk'):
                    snapshot[key] = {'id': value.pk, 'repr': str(value)}
                elif isinstance(value, (timezone.datetime, timezone.timedelta)):
                    snapshot[key] = str(value)
        except Exception:
            snapshot = {'repr': str(obj)}
        
        return cls.objects.create(
            action='soft_delete',
            user=user,
            content_type=ContentType.objects.get_for_model(obj),
            object_id=obj.pk,
            object_repr=str(obj),
            module_name=obj._meta.app_label,
            reason=reason,
            object_snapshot=snapshot,
            ip_address=ip_address,
            user_agent=user_agent,
            recycle_bin_entry=recycle_bin_entry,
            success=True
        )
    
    @classmethod
    def log_restore(cls, obj, user, ip_address=None, user_agent=None, recycle_bin_entry=None, previous_state=None):
        """
        Registra una restauración de objeto
        
        Args:
            obj: Objeto que se está restaurando
            user: Usuario que realiza la restauración
            ip_address: Dirección IP del usuario
            user_agent: User Agent del navegador
            recycle_bin_entry: Entrada de RecycleBin asociada
            previous_state: Estado anterior del objeto
            
        Returns:
            DeletionAuditLog: Registro de auditoría creado
        """
        return cls.objects.create(
            action='restore',
            user=user,
            content_type=ContentType.objects.get_for_model(obj),
            object_id=obj.pk,
            object_repr=str(obj),
            module_name=obj._meta.app_label,
            previous_state=previous_state or {},
            ip_address=ip_address,
            user_agent=user_agent,
            recycle_bin_entry=recycle_bin_entry,
            success=True
        )
    
    @classmethod
    def log_permanent_delete(cls, obj, user, reason='', ip_address=None, user_agent=None, 
                            recycle_bin_entry=None, security_code_used=False):
        """
        Registra una eliminación permanente
        
        Args:
            obj: Objeto que se está eliminando permanentemente
            user: Usuario que realiza la eliminación
            reason: Motivo de la eliminación
            ip_address: Dirección IP del usuario
            user_agent: User Agent del navegador
            recycle_bin_entry: Entrada de RecycleBin asociada
            security_code_used: Si se usó código de seguridad
            
        Returns:
            DeletionAuditLog: Registro de auditoría creado
        """
        from django.forms.models import model_to_dict
        
        # Crear snapshot completo del objeto antes de eliminación permanente
        try:
            snapshot = model_to_dict(obj)
            # Convertir valores no serializables
            for key, value in snapshot.items():
                if hasattr(value, 'pk'):
                    snapshot[key] = {'id': value.pk, 'repr': str(value)}
                elif isinstance(value, (timezone.datetime, timezone.timedelta)):
                    snapshot[key] = str(value)
        except Exception:
            snapshot = {'repr': str(obj)}
        
        return cls.objects.create(
            action='permanent_delete',
            user=user,
            content_type=ContentType.objects.get_for_model(obj),
            object_id=obj.pk,
            object_repr=str(obj),
            module_name=obj._meta.app_label,
            reason=reason,
            object_snapshot=snapshot,
            ip_address=ip_address,
            user_agent=user_agent,
            recycle_bin_entry=recycle_bin_entry,
            security_code_used=security_code_used,
            success=True
        )
    
    @classmethod
    def log_auto_delete(cls, obj, reason='', recycle_bin_entry=None):
        """
        Registra una eliminación automática
        
        Args:
            obj: Objeto que se está eliminando automáticamente
            reason: Motivo de la eliminación
            recycle_bin_entry: Entrada de RecycleBin asociada
            
        Returns:
            DeletionAuditLog: Registro de auditoría creado
        """
        from django.forms.models import model_to_dict
        from django.contrib.auth.models import User
        
        # Crear snapshot completo del objeto
        try:
            snapshot = model_to_dict(obj)
            for key, value in snapshot.items():
                if hasattr(value, 'pk'):
                    snapshot[key] = {'id': value.pk, 'repr': str(value)}
                elif isinstance(value, (timezone.datetime, timezone.timedelta)):
                    snapshot[key] = str(value)
        except Exception:
            snapshot = {'repr': str(obj)}
        
        # Usar un usuario del sistema para eliminaciones automáticas
        system_user = User.objects.filter(username='system').first()
        if not system_user:
            system_user = User.objects.filter(is_superuser=True).first()
        
        return cls.objects.create(
            action='auto_delete',
            user=system_user,
            content_type=ContentType.objects.get_for_model(obj),
            object_id=obj.pk,
            object_repr=str(obj),
            module_name=obj._meta.app_label,
            reason=reason or 'Eliminación automática por tiempo de retención',
            object_snapshot=snapshot,
            recycle_bin_entry=recycle_bin_entry,
            success=True
        )
    
    @classmethod
    def log_bulk_operation(cls, action, objects, user, ip_address=None, user_agent=None, metadata=None):
        """
        Registra una operación en lote
        
        Args:
            action: Tipo de acción ('bulk_restore' o 'bulk_delete')
            objects: Lista de objetos afectados
            user: Usuario que realiza la operación
            ip_address: Dirección IP del usuario
            user_agent: User Agent del navegador
            metadata: Metadatos adicionales
            
        Returns:
            list: Lista de registros de auditoría creados
        """
        logs = []
        for obj in objects:
            log = cls.objects.create(
                action=action,
                user=user,
                content_type=ContentType.objects.get_for_model(obj),
                object_id=obj.pk,
                object_repr=str(obj),
                module_name=obj._meta.app_label,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata=metadata or {},
                success=True
            )
            logs.append(log)
        return logs
    
    @classmethod
    def log_failed_operation(cls, action, obj, user, error_message, ip_address=None, user_agent=None):
        """
        Registra una operación fallida
        
        Args:
            action: Tipo de acción que falló
            obj: Objeto afectado
            user: Usuario que intentó la operación
            error_message: Mensaje de error
            ip_address: Dirección IP del usuario
            user_agent: User Agent del navegador
            
        Returns:
            DeletionAuditLog: Registro de auditoría creado
        """
        return cls.objects.create(
            action=f'failed_{action}',
            user=user,
            content_type=ContentType.objects.get_for_model(obj),
            object_id=obj.pk,
            object_repr=str(obj),
            module_name=obj._meta.app_label,
            error_message=error_message,
            ip_address=ip_address,
            user_agent=user_agent,
            success=False
        )
    
    def get_action_icon(self):
        """Retorna el icono apropiado para la acción"""
        icons = {
            'soft_delete': '🗑️',
            'restore': '♻️',
            'permanent_delete': '❌',
            'auto_delete': '⏰',
            'bulk_restore': '♻️📦',
            'bulk_delete': '❌📦',
            'failed_restore': '⚠️♻️',
            'failed_delete': '⚠️❌',
        }
        return icons.get(self.action, '📝')
    
    def get_action_color(self):
        """Retorna el color apropiado para la acción"""
        colors = {
            'soft_delete': 'warning',
            'restore': 'success',
            'permanent_delete': 'danger',
            'auto_delete': 'info',
            'bulk_restore': 'success',
            'bulk_delete': 'danger',
            'failed_restore': 'danger',
            'failed_delete': 'danger',
        }
        return colors.get(self.action, 'secondary')


class RecycleBinConfig(models.Model):
    """
    Configuración del sistema de papelera de reciclaje por módulo.
    Permite personalizar el comportamiento de la papelera para cada módulo del sistema.
    """
    
    MODULE_CHOICES = [
        ('oficinas', 'Oficinas'),
        ('bienes', 'Bienes Patrimoniales'),
        ('catalogo', 'Catálogo'),
        ('core', 'Sistema'),
    ]
    
    module_name = models.CharField(
        max_length=50,
        choices=MODULE_CHOICES,
        unique=True,
        verbose_name='Módulo',
        help_text='Módulo al que aplica la configuración'
    )
    
    # Configuración de retención
    retention_days = models.PositiveIntegerField(
        default=30,
        verbose_name='Días de retención',
        help_text='Número de días que los elementos permanecen en papelera antes de eliminación automática'
    )
    
    auto_delete_enabled = models.BooleanField(
        default=True,
        verbose_name='Eliminación automática habilitada',
        help_text='Si está habilitada la eliminación automática por tiempo'
    )
    
    # Configuración de notificaciones
    warning_days_before = models.PositiveIntegerField(
        default=7,
        verbose_name='Días de advertencia',
        help_text='Días antes de eliminación automática para enviar advertencia'
    )
    
    final_warning_days_before = models.PositiveIntegerField(
        default=1,
        verbose_name='Días de advertencia final',
        help_text='Días antes de eliminación automática para enviar advertencia final'
    )
    
    # Configuración de permisos
    can_restore_own = models.BooleanField(
        default=True,
        verbose_name='Puede restaurar propios',
        help_text='Los usuarios pueden restaurar elementos que ellos eliminaron'
    )
    
    can_restore_others = models.BooleanField(
        default=False,
        verbose_name='Puede restaurar de otros',
        help_text='Los usuarios pueden restaurar elementos eliminados por otros'
    )
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name='Actualizado por'
    )
    
    class Meta:
        verbose_name = 'Configuración de Papelera'
        verbose_name_plural = 'Configuraciones de Papelera'
        ordering = ['module_name']
    
    def __str__(self):
        return f"Configuración de {self.get_module_name_display()}"
    
    def clean(self):
        """
        Validaciones personalizadas para la configuración
        """
        from django.core.exceptions import ValidationError
        
        # Validar que retention_days sea mayor a 0
        if self.retention_days <= 0:
            raise ValidationError({
                'retention_days': 'Los días de retención deben ser mayor a 0'
            })
        
        # Validar que warning_days_before sea menor que retention_days
        if self.warning_days_before >= self.retention_days:
            raise ValidationError({
                'warning_days_before': 'Los días de advertencia deben ser menores que los días de retención'
            })
        
        # Validar que final_warning_days_before sea menor que warning_days_before
        if self.final_warning_days_before >= self.warning_days_before:
            raise ValidationError({
                'final_warning_days_before': 'Los días de advertencia final deben ser menores que los días de advertencia'
            })
        
        # Validar que final_warning_days_before sea mayor a 0
        if self.final_warning_days_before <= 0:
            raise ValidationError({
                'final_warning_days_before': 'Los días de advertencia final deben ser mayor a 0'
            })
    
    def save(self, *args, **kwargs):
        """
        Sobrescribe save para ejecutar validaciones
        """
        self.full_clean()
        super().save(*args, **kwargs)
    
    @classmethod
    def get_config_for_module(cls, module_name):
        """
        Obtiene la configuración para un módulo específico
        
        Args:
            module_name: Nombre del módulo
            
        Returns:
            RecycleBinConfig: Configuración del módulo o configuración por defecto
        """
        try:
            return cls.objects.get(module_name=module_name)
        except cls.DoesNotExist:
            # Crear configuración por defecto si no existe
            return cls.objects.create(
                module_name=module_name,
                retention_days=30,
                auto_delete_enabled=True,
                warning_days_before=7,
                final_warning_days_before=1,
                can_restore_own=True,
                can_restore_others=False
            )
    
    def get_effective_permissions(self, user):
        """
        Obtiene los permisos efectivos para un usuario en este módulo
        
        Args:
            user: Usuario para verificar permisos
            
        Returns:
            dict: Diccionario con permisos efectivos
        """
        # Los administradores siempre tienen todos los permisos
        if hasattr(user, 'profile') and user.profile.is_administrador:
            return {
                'can_restore_own': True,
                'can_restore_others': True,
                'can_permanent_delete': True,
                'can_view_all': True
            }
        
        return {
            'can_restore_own': self.can_restore_own,
            'can_restore_others': self.can_restore_others,
            'can_permanent_delete': False,
            'can_view_all': False
        }


# Alias para compatibilidad con tests
SecurityAttempt = SecurityCodeAttempt
