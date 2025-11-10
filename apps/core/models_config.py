"""
Modelos de configuración del sistema
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
import json


class SystemConfiguration(models.Model):
    """
    Configuración general del sistema (Singleton)
    Solo debe existir un registro de configuración
    """
    
    # Información de la institución
    institucion_nombre = models.CharField(
        max_length=200,
        default='',
        verbose_name='Nombre de la Institución',
        help_text='Nombre oficial de la institución'
    )
    institucion_siglas = models.CharField(
        max_length=50,
        default='',
        verbose_name='Siglas',
        help_text='Siglas de la institución'
    )
    institucion_ruc = models.CharField(
        max_length=20,
        default='',
        verbose_name='RUC',
        help_text='RUC de la institución'
    )
    institucion_direccion = models.TextField(
        default='',
        verbose_name='Dirección',
        help_text='Dirección de la institución'
    )
    institucion_telefono = models.CharField(
        max_length=50,
        default='',
        verbose_name='Teléfono',
        help_text='Teléfono de contacto'
    )
    institucion_email = models.EmailField(
        default='',
        verbose_name='Email',
        help_text='Email de contacto'
    )
    institucion_logo = models.ImageField(
        upload_to='config/logos/',
        null=True,
        blank=True,
        verbose_name='Logo',
        help_text='Logo de la institución'
    )
    
    # Configuración de fecha y hora
    FORMATO_FECHA_CHOICES = [
        ('%d/%m/%Y', 'DD/MM/YYYY (31/12/2025)'),
        ('%m/%d/%Y', 'MM/DD/YYYY (12/31/2025)'),
        ('%Y-%m-%d', 'YYYY-MM-DD (2025-12-31)'),
        ('%d-%m-%Y', 'DD-MM-YYYY (31-12-2025)'),
        ('%d.%m.%Y', 'DD.MM.YYYY (31.12.2025)'),
    ]
    
    formato_fecha = models.CharField(
        max_length=20,
        choices=FORMATO_FECHA_CHOICES,
        default='%d/%m/%Y',
        verbose_name='Formato de Fecha',
        help_text='Formato para mostrar fechas en el sistema'
    )
    
    formato_fecha_hora = models.CharField(
        max_length=30,
        default='%d/%m/%Y %H:%M',
        verbose_name='Formato de Fecha y Hora',
        help_text='Formato para mostrar fecha y hora'
    )
    
    TIMEZONE_CHOICES = [
        ('America/Lima', 'Lima (UTC-5)'),
        ('America/Bogota', 'Bogotá (UTC-5)'),
        ('America/Mexico_City', 'Ciudad de México (UTC-6)'),
        ('America/Argentina/Buenos_Aires', 'Buenos Aires (UTC-3)'),
        ('America/Santiago', 'Santiago (UTC-3/UTC-4)'),
        ('America/Caracas', 'Caracas (UTC-4)'),
        ('America/New_York', 'Nueva York (UTC-5/UTC-4)'),
        ('Europe/Madrid', 'Madrid (UTC+1/UTC+2)'),
        ('UTC', 'UTC (UTC+0)'),
    ]
    
    zona_horaria = models.CharField(
        max_length=50,
        choices=TIMEZONE_CHOICES,
        default='America/Lima',
        verbose_name='Zona Horaria',
        help_text='Zona horaria del sistema'
    )
    
    # Configuración de paginación
    registros_por_pagina = models.IntegerField(
        default=20,
        verbose_name='Registros por Página',
        help_text='Número de registros a mostrar por página en las listas'
    )
    
    # Configuración de códigos
    longitud_codigo_patrimonial = models.IntegerField(
        default=10,
        verbose_name='Longitud Código Patrimonial',
        help_text='Longitud del código patrimonial'
    )
    
    prefijo_codigo_patrimonial = models.CharField(
        max_length=10,
        default='',
        blank=True,
        verbose_name='Prefijo Código Patrimonial',
        help_text='Prefijo para códigos patrimoniales (opcional)'
    )
    
    # Configuración de QR
    tamano_qr = models.IntegerField(
        default=10,
        verbose_name='Tamaño de QR',
        help_text='Tamaño del código QR (1-20)'
    )
    
    # Configuración de reportes
    incluir_logo_reportes = models.BooleanField(
        default=True,
        verbose_name='Incluir Logo en Reportes',
        help_text='Incluir logo de la institución en reportes PDF'
    )
    
    pie_pagina_reportes = models.TextField(
        default='',
        blank=True,
        verbose_name='Pie de Página de Reportes',
        help_text='Texto para el pie de página de reportes'
    )
    
    # Configuración de notificaciones
    habilitar_notificaciones_email = models.BooleanField(
        default=True,
        verbose_name='Habilitar Notificaciones por Email',
        help_text='Enviar notificaciones por correo electrónico'
    )
    
    dias_aviso_mantenimiento = models.IntegerField(
        default=30,
        verbose_name='Días de Aviso de Mantenimiento',
        help_text='Días de anticipación para avisar mantenimientos'
    )
    
    # Configuración de importación
    permitir_duplicados_denominacion = models.BooleanField(
        default=True,
        verbose_name='Permitir Duplicados en Denominación',
        help_text='Permitir denominaciones duplicadas en importación de catálogo'
    )
    
    # Metadatos
    actualizado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Actualizado Por'
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name='Fecha de Actualización'
    )
    
    class Meta:
        verbose_name = 'Configuración del Sistema'
        verbose_name_plural = 'Configuración del Sistema'
    
    def __str__(self):
        return f"Configuración del Sistema - {self.institucion_nombre or 'Sin configurar'}"
    
    def save(self, *args, **kwargs):
        """Asegurar que solo exista un registro de configuración"""
        self.pk = 1
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Prevenir eliminación de la configuración"""
        pass
    
    @classmethod
    def get_config(cls):
        """Obtener o crear la configuración del sistema"""
        config, created = cls.objects.get_or_create(pk=1)
        return config
    
    def get_formato_fecha_display_example(self):
        """Obtener ejemplo del formato de fecha"""
        return timezone.now().strftime(self.formato_fecha)
    
    def get_formato_fecha_hora_display_example(self):
        """Obtener ejemplo del formato de fecha y hora"""
        return timezone.now().strftime(self.formato_fecha_hora)


class FieldConfiguration(models.Model):
    """
    Configuración de campos visibles/ocultos por módulo
    """
    MODULO_CHOICES = [
        ('bienes', 'Bienes Patrimoniales'),
        ('catalogo', 'Catálogo'),
        ('oficinas', 'Oficinas'),
        ('reportes', 'Reportes'),
    ]
    
    modulo = models.CharField(
        max_length=50,
        choices=MODULO_CHOICES,
        verbose_name='Módulo'
    )
    campo_nombre = models.CharField(
        max_length=100,
        verbose_name='Nombre del Campo',
        help_text='Nombre técnico del campo'
    )
    campo_etiqueta = models.CharField(
        max_length=100,
        verbose_name='Etiqueta del Campo',
        help_text='Etiqueta visible para el usuario'
    )
    visible = models.BooleanField(
        default=True,
        verbose_name='Visible',
        help_text='Si el campo es visible en formularios y listas'
    )
    requerido = models.BooleanField(
        default=False,
        verbose_name='Requerido',
        help_text='Si el campo es obligatorio'
    )
    orden = models.IntegerField(
        default=0,
        verbose_name='Orden',
        help_text='Orden de visualización del campo'
    )
    ayuda = models.TextField(
        blank=True,
        verbose_name='Texto de Ayuda',
        help_text='Texto de ayuda para el campo'
    )
    
    class Meta:
        verbose_name = 'Configuración de Campo'
        verbose_name_plural = 'Configuración de Campos'
        ordering = ['modulo', 'orden', 'campo_nombre']
        unique_together = ['modulo', 'campo_nombre']
    
    def __str__(self):
        return f"{self.get_modulo_display()} - {self.campo_etiqueta}"


class EstadoBienConfiguration(models.Model):
    """
    Configuración de estados de bienes patrimoniales
    """
    codigo = models.CharField(
        max_length=5,
        unique=True,
        verbose_name='Código',
        help_text='Código corto del estado (ej: N, B, R, M)'
    )
    nombre = models.CharField(
        max_length=50,
        verbose_name='Nombre',
        help_text='Nombre completo del estado'
    )
    descripcion = models.TextField(
        blank=True,
        verbose_name='Descripción',
        help_text='Descripción detallada del estado'
    )
    color = models.CharField(
        max_length=7,
        default='#6c757d',
        verbose_name='Color',
        help_text='Color hexadecimal para representar el estado (ej: #28a745)'
    )
    icono = models.CharField(
        max_length=50,
        default='fa-circle',
        verbose_name='Icono',
        help_text='Clase de icono FontAwesome'
    )
    activo = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='Si el estado está activo para uso'
    )
    orden = models.IntegerField(
        default=0,
        verbose_name='Orden',
        help_text='Orden de visualización'
    )
    es_sistema = models.BooleanField(
        default=False,
        verbose_name='Es del Sistema',
        help_text='Si es un estado del sistema (no se puede eliminar)'
    )
    
    class Meta:
        verbose_name = 'Estado de Bien'
        verbose_name_plural = 'Estados de Bienes'
        ordering = ['orden', 'nombre']
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"
    
    def delete(self, *args, **kwargs):
        """Prevenir eliminación de estados del sistema"""
        if self.es_sistema:
            raise ValidationError('No se pueden eliminar estados del sistema')
        super().delete(*args, **kwargs)
    
    @classmethod
    def get_estados_activos(cls):
        """Obtener estados activos"""
        return cls.objects.filter(activo=True).order_by('orden')
    
    @classmethod
    def get_choices(cls):
        """Obtener choices para formularios"""
        return [(e.codigo, e.nombre) for e in cls.get_estados_activos()]
    
    @classmethod
    def inicializar_estados_default(cls):
        """Inicializar estados por defecto del sistema"""
        estados_default = [
            {'codigo': 'N', 'nombre': 'Nuevo', 'color': '#28a745', 'icono': 'fa-star', 'orden': 1, 'es_sistema': True},
            {'codigo': 'B', 'nombre': 'Bueno', 'color': '#17a2b8', 'icono': 'fa-check-circle', 'orden': 2, 'es_sistema': True},
            {'codigo': 'R', 'nombre': 'Regular', 'color': '#ffc107', 'icono': 'fa-exclamation-circle', 'orden': 3, 'es_sistema': True},
            {'codigo': 'M', 'nombre': 'Malo', 'color': '#dc3545', 'icono': 'fa-times-circle', 'orden': 4, 'es_sistema': True},
            {'codigo': 'E', 'nombre': 'RAEE', 'color': '#6c757d', 'icono': 'fa-recycle', 'orden': 5, 'es_sistema': True},
            {'codigo': 'C', 'nombre': 'Chatarra', 'color': '#343a40', 'icono': 'fa-trash', 'orden': 6, 'es_sistema': True},
        ]
        
        for estado_data in estados_default:
            cls.objects.get_or_create(
                codigo=estado_data['codigo'],
                defaults=estado_data
            )


class ConfigurationHistory(models.Model):
    """
    Historial de cambios en la configuración
    """
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Usuario'
    )
    fecha = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha'
    )
    tipo_configuracion = models.CharField(
        max_length=50,
        verbose_name='Tipo de Configuración',
        help_text='Tipo de configuración modificada'
    )
    campo_modificado = models.CharField(
        max_length=100,
        verbose_name='Campo Modificado'
    )
    valor_anterior = models.TextField(
        blank=True,
        verbose_name='Valor Anterior'
    )
    valor_nuevo = models.TextField(
        blank=True,
        verbose_name='Valor Nuevo'
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='Dirección IP'
    )
    
    class Meta:
        verbose_name = 'Historial de Configuración'
        verbose_name_plural = 'Historial de Configuraciones'
        ordering = ['-fecha']
    
    def __str__(self):
        return f"{self.tipo_configuracion} - {self.campo_modificado} - {self.fecha}"
    
    @classmethod
    def registrar_cambio(cls, usuario, tipo_config, campo, valor_anterior, valor_nuevo, ip=None):
        """Registrar un cambio en la configuración"""
        return cls.objects.create(
            usuario=usuario,
            tipo_configuracion=tipo_config,
            campo_modificado=campo,
            valor_anterior=str(valor_anterior),
            valor_nuevo=str(valor_nuevo),
            ip_address=ip
        )
