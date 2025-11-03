"""
Modelos para la funcionalidad móvil
"""
from django.db import models
from django.contrib.auth.models import User
from apps.bienes.models import BienPatrimonial
import json


class CambioOffline(models.Model):
    """
    Modelo para almacenar cambios realizados offline que necesitan sincronización
    """
    TIPOS_CAMBIO = [
        ('CREAR', 'Crear Bien'),
        ('ACTUALIZAR', 'Actualizar Bien'),
        ('CAMBIAR_ESTADO', 'Cambiar Estado'),
        ('AGREGAR_FOTO', 'Agregar Foto'),
        ('INVENTARIO', 'Registro de Inventario'),
    ]
    
    ESTADOS_SYNC = [
        ('PENDIENTE', 'Pendiente'),
        ('PROCESANDO', 'Procesando'),
        ('COMPLETADO', 'Completado'),
        ('ERROR', 'Error'),
        ('CONFLICTO', 'Conflicto'),
    ]
    
    # Identificación del cambio
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    tipo_cambio = models.CharField(max_length=20, choices=TIPOS_CAMBIO)
    timestamp_local = models.DateTimeField()  # Timestamp del dispositivo móvil
    timestamp_servidor = models.DateTimeField(auto_now_add=True)
    
    # Datos del cambio
    bien_codigo_patrimonial = models.CharField(max_length=50, blank=True)  # Para identificar el bien
    bien_qr_code = models.CharField(max_length=200, blank=True)  # Alternativa para identificar
    datos_cambio = models.JSONField()  # Datos del cambio en formato JSON
    
    # Estado de sincronización
    estado_sync = models.CharField(max_length=20, choices=ESTADOS_SYNC, default='PENDIENTE')
    intentos_sync = models.IntegerField(default=0)
    ultimo_intento = models.DateTimeField(null=True, blank=True)
    mensaje_error = models.TextField(blank=True)
    
    # Metadatos móviles
    dispositivo_id = models.CharField(max_length=100, blank=True)
    ubicacion_gps = models.CharField(max_length=100, blank=True)
    
    # Resolución de conflictos
    conflicto_resuelto = models.BooleanField(default=False)
    resuelto_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='conflictos_resueltos')
    fecha_resolucion = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-timestamp_local']
        indexes = [
            models.Index(fields=['usuario', 'estado_sync']),
            models.Index(fields=['bien_codigo_patrimonial']),
            models.Index(fields=['bien_qr_code']),
            models.Index(fields=['estado_sync']),
        ]
    
    def __str__(self):
        return f"{self.tipo_cambio} - {self.bien_codigo_patrimonial} - {self.estado_sync}"
    
    def get_datos_cambio(self):
        """Obtener los datos del cambio como diccionario"""
        if isinstance(self.datos_cambio, str):
            return json.loads(self.datos_cambio)
        return self.datos_cambio
    
    def set_datos_cambio(self, datos):
        """Establecer los datos del cambio"""
        if isinstance(datos, dict):
            self.datos_cambio = datos
        else:
            self.datos_cambio = json.loads(datos)


class SesionSync(models.Model):
    """
    Modelo para rastrear sesiones de sincronización
    """
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    dispositivo_id = models.CharField(max_length=100)
    inicio_sync = models.DateTimeField(auto_now_add=True)
    fin_sync = models.DateTimeField(null=True, blank=True)
    
    # Estadísticas de la sincronización
    cambios_pendientes = models.IntegerField(default=0)
    cambios_procesados = models.IntegerField(default=0)
    cambios_exitosos = models.IntegerField(default=0)
    cambios_con_error = models.IntegerField(default=0)
    cambios_con_conflicto = models.IntegerField(default=0)
    
    # Estado de la sesión
    completada = models.BooleanField(default=False)
    mensaje_resultado = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-inicio_sync']
    
    def __str__(self):
        return f"Sync {self.usuario.username} - {self.inicio_sync}"


class ConflictoSync(models.Model):
    """
    Modelo para manejar conflictos de sincronización
    """
    TIPOS_CONFLICTO = [
        ('BIEN_MODIFICADO', 'Bien modificado en servidor'),
        ('BIEN_ELIMINADO', 'Bien eliminado en servidor'),
        ('CODIGO_DUPLICADO', 'Código patrimonial duplicado'),
        ('DATOS_INCONSISTENTES', 'Datos inconsistentes'),
    ]
    
    cambio_offline = models.OneToOneField(CambioOffline, on_delete=models.CASCADE)
    tipo_conflicto = models.CharField(max_length=30, choices=TIPOS_CONFLICTO)
    
    # Datos del conflicto
    datos_servidor = models.JSONField()  # Estado actual en el servidor
    datos_cliente = models.JSONField()   # Datos del cliente que causan conflicto
    
    # Resolución
    resuelto = models.BooleanField(default=False)
    resolucion_elegida = models.CharField(max_length=20, choices=[
        ('SERVIDOR', 'Mantener datos del servidor'),
        ('CLIENTE', 'Aplicar datos del cliente'),
        ('MANUAL', 'Resolución manual'),
    ], blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Conflicto {self.tipo_conflicto} - {self.cambio_offline.bien_codigo_patrimonial}"