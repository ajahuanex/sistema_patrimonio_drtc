import uuid
import qrcode
from io import BytesIO
from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from django.urls import reverse
from apps.core.models import BaseModel
from apps.catalogo.models import Catalogo
from apps.oficinas.models import Oficina


class BienPatrimonial(BaseModel):
    """Modelo principal para los bienes patrimoniales"""
    
    ESTADOS_BIEN = [
        ('N', 'Nuevo'),
        ('B', 'Bueno'),
        ('R', 'Regular'),
        ('M', 'Malo'),
        ('E', 'RAEE'),
        ('C', 'Chatarra')
    ]
    
    # Campos principales del Excel
    codigo_patrimonial = models.CharField(
        max_length=50, 
        unique=True,
        verbose_name='Código Patrimonial',
        help_text='Código único del bien patrimonial'
    )
    codigo_interno = models.CharField(
        max_length=50, 
        blank=True,
        verbose_name='Código Interno',
        help_text='Código interno de la institución'
    )
    
    # Relaciones
    catalogo = models.ForeignKey(
        Catalogo, 
        on_delete=models.PROTECT,
        verbose_name='Catálogo',
        help_text='Denominación del bien según catálogo oficial'
    )
    oficina = models.ForeignKey(
        Oficina, 
        on_delete=models.PROTECT,
        verbose_name='Oficina',
        help_text='Oficina donde se encuentra ubicado el bien'
    )
    
    # Estado y características
    estado_bien = models.CharField(
        max_length=1, 
        choices=ESTADOS_BIEN,
        default='B',
        verbose_name='Estado del Bien',
        help_text='Estado de conservación del bien'
    )
    marca = models.CharField(
        max_length=100, 
        blank=True,
        verbose_name='Marca',
        help_text='Marca del bien'
    )
    modelo = models.CharField(
        max_length=100, 
        blank=True,
        verbose_name='Modelo',
        help_text='Modelo del bien'
    )
    color = models.CharField(
        max_length=50, 
        blank=True,
        verbose_name='Color',
        help_text='Color del bien'
    )
    serie = models.CharField(
        max_length=100, 
        blank=True,
        verbose_name='Serie',
        help_text='Número de serie del bien'
    )
    dimension = models.CharField(
        max_length=100, 
        blank=True,
        verbose_name='Dimensión',
        help_text='Dimensiones del bien'
    )
    
    # Campos específicos para vehículos
    placa = models.CharField(
        max_length=20, 
        blank=True,
        verbose_name='Placa',
        help_text='Placa del vehículo'
    )
    matricula = models.CharField(
        max_length=20, 
        blank=True,
        verbose_name='Matrícula',
        help_text='Matrícula del vehículo'
    )
    nro_motor = models.CharField(
        max_length=50, 
        blank=True,
        verbose_name='Número de Motor',
        help_text='Número de motor del vehículo'
    )
    nro_chasis = models.CharField(
        max_length=50, 
        blank=True,
        verbose_name='Número de Chasis',
        help_text='Número de chasis del vehículo'
    )
    
    # Observaciones
    observaciones = models.TextField(
        blank=True,
        verbose_name='Observaciones',
        help_text='Observaciones adicionales sobre el bien'
    )
    
    # Campos para QR y URL
    qr_code = models.CharField(
        max_length=200, 
        unique=True,
        blank=True,
        verbose_name='Código QR',
        help_text='Código QR único del bien'
    )
    url_qr = models.URLField(
        blank=True,
        verbose_name='URL QR',
        help_text='URL única para acceso mediante QR'
    )
    
    # Campos adicionales
    fecha_adquisicion = models.DateField(
        null=True, 
        blank=True,
        verbose_name='Fecha de Adquisición',
        help_text='Fecha de adquisición del bien'
    )
    valor_adquisicion = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        null=True, 
        blank=True,
        verbose_name='Valor de Adquisición',
        help_text='Valor de adquisición en soles'
    )
    
    class Meta:
        verbose_name = 'Bien Patrimonial'
        verbose_name_plural = 'Bienes Patrimoniales'
        ordering = ['codigo_patrimonial']
        indexes = [
            models.Index(fields=['codigo_patrimonial']),
            models.Index(fields=['qr_code']),
            models.Index(fields=['estado_bien']),
            models.Index(fields=['catalogo']),
            models.Index(fields=['oficina']),
            models.Index(fields=['placa']),
            models.Index(fields=['serie']),
        ]
    
    def __str__(self):
        base_str = f"{self.codigo_patrimonial} - {self.catalogo.denominacion}"
        return self.get_str_with_delete_status(base_str)
    
    def clean(self):
        """Validaciones personalizadas"""
        super().clean()
        
        # Validar que el código patrimonial no esté vacío
        if not self.codigo_patrimonial or not self.codigo_patrimonial.strip():
            raise ValidationError({
                'codigo_patrimonial': 'El código patrimonial no puede estar vacío'
            })
        
        # Validar que el catálogo esté activo
        if self.catalogo and self.catalogo.estado != 'ACTIVO':
            raise ValidationError({
                'catalogo': 'No se puede asignar un bien con catálogo excluido'
            })
        
        # Validar que la oficina esté activa
        if self.oficina and not self.oficina.estado:
            raise ValidationError({
                'oficina': 'No se puede asignar un bien a una oficina inactiva'
            })
        
        # Normalizar campos
        if self.codigo_patrimonial:
            self.codigo_patrimonial = self.codigo_patrimonial.strip()
        if self.placa:
            self.placa = self.placa.upper().strip()
        if self.matricula:
            self.matricula = self.matricula.upper().strip()
    
    def save(self, *args, **kwargs):
        """Override save para generar QR automáticamente"""
        # Generar QR code y URL si no existen
        if not self.qr_code or not self.url_qr:
            from .utils import QRCodeGenerator
            generator = QRCodeGenerator()
            generator.generar_qr_para_bien(self)
        
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def estado_bien_texto(self):
        """Retorna el estado del bien como texto"""
        return dict(self.ESTADOS_BIEN).get(self.estado_bien, '')
    
    @property
    def es_vehiculo(self):
        """Determina si el bien es un vehículo"""
        return bool(self.placa or self.matricula or self.nro_motor or self.nro_chasis)
    
    @property
    def denominacion(self):
        """Retorna la denominación del catálogo"""
        return self.catalogo.denominacion if self.catalogo else ''
    
    @property
    def grupo_clase(self):
        """Retorna grupo y clase del catálogo"""
        if self.catalogo:
            return f"{self.catalogo.grupo} - {self.catalogo.clase}"
        return ''
    
    @property
    def ubicacion_completa(self):
        """Retorna la ubicación completa"""
        ubicacion = self.oficina.nombre if self.oficina else ''
        if self.oficina and self.oficina.ubicacion:
            ubicacion += f" ({self.oficina.ubicacion})"
        return ubicacion
    
    @property
    def responsable_actual(self):
        """Retorna el responsable actual"""
        return self.oficina.responsable if self.oficina else ''
    
    def generar_qr_image(self):
        """Genera la imagen del código QR"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(self.url_qr)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        return img
    
    @classmethod
    def buscar_por_codigo(cls, codigo):
        """Busca bien por código patrimonial"""
        return cls.objects.filter(
            codigo_patrimonial__icontains=codigo
        ).first()
    
    @classmethod
    def buscar_por_qr(cls, qr_code):
        """Busca bien por código QR"""
        return cls.objects.filter(qr_code=qr_code).first()
    
    @classmethod
    def buscar_por_placa(cls, placa):
        """Busca bien por placa"""
        return cls.objects.filter(
            placa__icontains=placa
        ).exclude(placa='')
    
    @classmethod
    def buscar_por_serie(cls, serie):
        """Busca bien por serie"""
        return cls.objects.filter(
            serie__icontains=serie
        ).exclude(serie='')
    
    @classmethod
    def obtener_por_oficina(cls, oficina):
        """Obtiene bienes de una oficina específica"""
        return cls.objects.filter(oficina=oficina).order_by('codigo_patrimonial')
    
    @classmethod
    def obtener_por_estado(cls, estado):
        """Obtiene bienes por estado"""
        return cls.objects.filter(estado_bien=estado).order_by('codigo_patrimonial')
    
    @classmethod
    def estadisticas_por_estado(cls):
        """Obtiene estadísticas por estado"""
        from django.db.models import Count
        return cls.objects.values('estado_bien').annotate(
            total=Count('id')
        ).order_by('estado_bien')
    
    @classmethod
    def estadisticas_por_oficina(cls):
        """Obtiene estadísticas por oficina"""
        from django.db.models import Count
        return cls.objects.values(
            'oficina__nombre'
        ).annotate(
            total=Count('id')
        ).order_by('oficina__nombre')


class MovimientoBien(BaseModel):
    """Modelo para registrar movimientos de bienes entre oficinas"""
    
    bien = models.ForeignKey(
        BienPatrimonial, 
        on_delete=models.CASCADE,
        verbose_name='Bien',
        help_text='Bien que se está moviendo'
    )
    oficina_origen = models.ForeignKey(
        Oficina, 
        related_name='movimientos_origen', 
        on_delete=models.PROTECT,
        verbose_name='Oficina Origen',
        help_text='Oficina de origen del movimiento'
    )
    oficina_destino = models.ForeignKey(
        Oficina, 
        related_name='movimientos_destino', 
        on_delete=models.PROTECT,
        verbose_name='Oficina Destino',
        help_text='Oficina de destino del movimiento'
    )
    motivo = models.CharField(
        max_length=200,
        verbose_name='Motivo',
        help_text='Motivo del movimiento'
    )
    observaciones = models.TextField(
        blank=True,
        verbose_name='Observaciones',
        help_text='Observaciones adicionales del movimiento'
    )
    fecha_movimiento = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Movimiento'
    )
    confirmado = models.BooleanField(
        default=False,
        verbose_name='Confirmado',
        help_text='Indica si el movimiento ha sido confirmado'
    )
    fecha_confirmacion = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name='Fecha de Confirmación'
    )
    
    class Meta:
        verbose_name = 'Movimiento de Bien'
        verbose_name_plural = 'Movimientos de Bienes'
        ordering = ['-fecha_movimiento']
    
    def __str__(self):
        base_str = f"{self.bien.codigo_patrimonial}: {self.oficina_origen} → {self.oficina_destino}"
        return self.get_str_with_delete_status(base_str)
    
    def confirmar_movimiento(self):
        """Confirma el movimiento y actualiza la oficina del bien"""
        from django.utils import timezone
        
        if not self.confirmado:
            self.confirmado = True
            self.fecha_confirmacion = timezone.now()
            self.save()
            
            # Actualizar la oficina del bien
            self.bien.oficina = self.oficina_destino
            self.bien.save()


class HistorialEstado(BaseModel):
    """Modelo para registrar cambios de estado de los bienes"""
    
    bien = models.ForeignKey(
        BienPatrimonial, 
        on_delete=models.CASCADE,
        verbose_name='Bien'
    )
    estado_anterior = models.CharField(
        max_length=1, 
        choices=BienPatrimonial.ESTADOS_BIEN,
        verbose_name='Estado Anterior'
    )
    estado_nuevo = models.CharField(
        max_length=1, 
        choices=BienPatrimonial.ESTADOS_BIEN,
        verbose_name='Estado Nuevo'
    )
    observaciones = models.TextField(
        blank=True,
        verbose_name='Observaciones',
        help_text='Justificación del cambio de estado'
    )
    fecha_cambio = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Cambio'
    )
    ubicacion_gps = models.CharField(
        max_length=100, 
        blank=True,
        verbose_name='Ubicación GPS',
        help_text='Coordenadas GPS del cambio (desde móvil)'
    )
    foto = models.ImageField(
        upload_to='estados/', 
        blank=True,
        verbose_name='Foto',
        help_text='Foto del bien en el momento del cambio'
    )
    
    class Meta:
        verbose_name = 'Historial de Estado'
        verbose_name_plural = 'Historiales de Estado'
        ordering = ['-fecha_cambio']
    
    def __str__(self):
        base_str = f"{self.bien.codigo_patrimonial}: {self.get_estado_anterior_display()} → {self.get_estado_nuevo_display()}"
        return self.get_str_with_delete_status(base_str)