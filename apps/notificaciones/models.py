"""
Modelos para el sistema de notificaciones
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


class TipoNotificacion(models.Model):
    """
    Tipos de notificaciones del sistema
    """
    TIPOS_CHOICES = [
        ('MANTENIMIENTO', 'Mantenimiento'),
        ('DEPRECIACION', 'Depreciación'),
        ('MOVIMIENTO', 'Movimiento de Bien'),
        ('IMPORTACION', 'Importación Completada'),
        ('REPORTE', 'Reporte Generado'),
        ('SISTEMA', 'Sistema'),
        ('INVENTARIO', 'Inventario'),
        ('ALERTA', 'Alerta General'),
    ]
    
    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)
    enviar_email = models.BooleanField(default=True)
    plantilla_email = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Tipo de Notificación"
        verbose_name_plural = "Tipos de Notificaciones"
    
    def __str__(self):
        return self.nombre


class ConfiguracionNotificacion(models.Model):
    """
    Configuración de notificaciones por usuario
    """
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='configuraciones_notificacion')
    tipo_notificacion = models.ForeignKey(TipoNotificacion, on_delete=models.CASCADE)
    activa = models.BooleanField(default=True)
    enviar_email = models.BooleanField(default=True)
    frecuencia_dias = models.IntegerField(default=1, help_text="Frecuencia en días para notificaciones recurrentes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['usuario', 'tipo_notificacion']
        verbose_name = "Configuración de Notificación"
        verbose_name_plural = "Configuraciones de Notificaciones"
    
    def __str__(self):
        return f"{self.usuario.username} - {self.tipo_notificacion.nombre}"


class Notificacion(models.Model):
    """
    Notificaciones del sistema
    """
    ESTADOS_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('ENVIADA', 'Enviada'),
        ('LEIDA', 'Leída'),
        ('ERROR', 'Error'),
    ]
    
    PRIORIDADES_CHOICES = [
        ('BAJA', 'Baja'),
        ('MEDIA', 'Media'),
        ('ALTA', 'Alta'),
        ('CRITICA', 'Crítica'),
    ]
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notificaciones')
    tipo_notificacion = models.ForeignKey(TipoNotificacion, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    prioridad = models.CharField(max_length=10, choices=PRIORIDADES_CHOICES, default='MEDIA')
    estado = models.CharField(max_length=10, choices=ESTADOS_CHOICES, default='PENDIENTE')
    
    # Datos adicionales
    datos_contexto = models.JSONField(default=dict, blank=True)
    url_accion = models.URLField(blank=True, help_text="URL para acción relacionada")
    
    # Fechas
    fecha_programada = models.DateTimeField(default=timezone.now)
    fecha_enviada = models.DateTimeField(null=True, blank=True)
    fecha_leida = models.DateTimeField(null=True, blank=True)
    fecha_expiracion = models.DateTimeField(null=True, blank=True)
    
    # Control de envío
    intentos_envio = models.IntegerField(default=0)
    ultimo_error = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"
    
    def __str__(self):
        return f"{self.usuario.username} - {self.titulo}"
    
    def marcar_como_leida(self):
        """Marca la notificación como leída"""
        if self.estado != 'LEIDA':
            self.estado = 'LEIDA'
            self.fecha_leida = timezone.now()
            self.save()
    
    def marcar_como_enviada(self):
        """Marca la notificación como enviada"""
        self.estado = 'ENVIADA'
        self.fecha_enviada = timezone.now()
        self.save()
    
    def marcar_error(self, error_msg):
        """Marca la notificación con error"""
        self.estado = 'ERROR'
        self.ultimo_error = error_msg
        self.intentos_envio += 1
        self.save()
    
    def esta_expirada(self):
        """Verifica si la notificación está expirada"""
        if self.fecha_expiracion:
            return timezone.now() > self.fecha_expiracion
        return False
    
    @property
    def es_urgente(self):
        """Determina si la notificación es urgente"""
        return self.prioridad in ['ALTA', 'CRITICA']


class AlertaMantenimiento(models.Model):
    """
    Configuración de alertas de mantenimiento
    """
    TIPOS_BIEN_CHOICES = [
        ('VEHICULO', 'Vehículo'),
        ('EQUIPO', 'Equipo'),
        ('MOBILIARIO', 'Mobiliario'),
        ('TODOS', 'Todos los tipos'),
    ]
    
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    tipo_bien = models.CharField(max_length=20, choices=TIPOS_BIEN_CHOICES, default='TODOS')
    
    # Criterios de alerta
    dias_anticipacion = models.IntegerField(default=30, help_text="Días de anticipación para la alerta")
    frecuencia_meses = models.IntegerField(default=6, help_text="Frecuencia de mantenimiento en meses")
    
    # Configuración
    activa = models.BooleanField(default=True)
    usuarios_notificar = models.ManyToManyField(User, blank=True, help_text="Usuarios a notificar")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Alerta de Mantenimiento"
        verbose_name_plural = "Alertas de Mantenimiento"
    
    def __str__(self):
        return self.nombre


class AlertaDepreciacion(models.Model):
    """
    Configuración de alertas de depreciación
    """
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    
    # Criterios de alerta
    meses_anticipacion = models.IntegerField(default=6, help_text="Meses de anticipación para la alerta")
    vida_util_anos = models.IntegerField(default=10, help_text="Vida útil en años")
    
    # Filtros
    grupos_catalogo = models.JSONField(default=list, blank=True, help_text="Grupos de catálogo a incluir")
    oficinas = models.JSONField(default=list, blank=True, help_text="Oficinas a incluir")
    
    # Configuración
    activa = models.BooleanField(default=True)
    usuarios_notificar = models.ManyToManyField(User, blank=True, help_text="Usuarios a notificar")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Alerta de Depreciación"
        verbose_name_plural = "Alertas de Depreciación"
    
    def __str__(self):
        return self.nombre


class HistorialNotificacion(models.Model):
    """
    Historial de notificaciones enviadas
    """
    notificacion = models.ForeignKey(Notificacion, on_delete=models.CASCADE, related_name='historial')
    accion = models.CharField(max_length=50)
    detalles = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Historial de Notificación"
        verbose_name_plural = "Historiales de Notificaciones"
    
    def __str__(self):
        return f"{self.notificacion.titulo} - {self.accion}"