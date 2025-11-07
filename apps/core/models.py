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


class RecycleBinConfig(models.Model):
    """
    Configuración del sistema de papelera por módulo
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