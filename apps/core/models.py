from django.db import models
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from django.dispatch import receiver


class BaseModel(models.Model):
    """Modelo base con campos de auditoría"""
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