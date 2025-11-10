from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from apps.core.models import BaseModel


class ImportObservation(models.Model):
    """
    Modelo para registrar observaciones durante la importación de datos.
    Permite continuar con la importación incluso cuando hay problemas menores.
    """
    TIPO_CHOICES = [
        ('duplicado_denominacion', 'Denominación Duplicada'),
        ('dato_incompleto', 'Dato Incompleto'),
        ('formato_invalido', 'Formato Inválido'),
        ('referencia_faltante', 'Referencia Faltante'),
        ('otro', 'Otro'),
    ]
    
    SEVERIDAD_CHOICES = [
        ('info', 'Información'),
        ('warning', 'Advertencia'),
        ('error', 'Error'),
    ]
    
    MODULO_CHOICES = [
        ('catalogo', 'Catálogo'),
        ('bienes', 'Bienes Patrimoniales'),
        ('oficinas', 'Oficinas'),
    ]
    
    modulo = models.CharField(
        max_length=50,
        choices=MODULO_CHOICES,
        verbose_name='Módulo',
        help_text='Módulo donde se generó la observación'
    )
    tipo = models.CharField(
        max_length=50,
        choices=TIPO_CHOICES,
        verbose_name='Tipo de Observación',
        help_text='Tipo de problema detectado'
    )
    severidad = models.CharField(
        max_length=20,
        choices=SEVERIDAD_CHOICES,
        default='warning',
        verbose_name='Severidad',
        help_text='Nivel de severidad de la observación'
    )
    fila_excel = models.IntegerField(
        verbose_name='Fila en Excel',
        help_text='Número de fila en el archivo Excel'
    )
    campo = models.CharField(
        max_length=100,
        verbose_name='Campo',
        help_text='Campo que generó la observación'
    )
    valor_original = models.TextField(
        blank=True,
        verbose_name='Valor Original',
        help_text='Valor original del campo'
    )
    valor_procesado = models.TextField(
        blank=True,
        verbose_name='Valor Procesado',
        help_text='Valor después del procesamiento'
    )
    mensaje = models.TextField(
        verbose_name='Mensaje',
        help_text='Descripción detallada de la observación'
    )
    datos_adicionales = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Datos Adicionales',
        help_text='Información adicional en formato JSON'
    )
    fecha_importacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Importación',
        help_text='Fecha y hora de la importación'
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Usuario',
        help_text='Usuario que realizó la importación'
    )
    archivo_nombre = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Nombre del Archivo',
        help_text='Nombre del archivo importado'
    )
    resuelto = models.BooleanField(
        default=False,
        verbose_name='Resuelto',
        help_text='Indica si la observación fue revisada y resuelta'
    )
    resuelto_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='observaciones_resueltas',
        verbose_name='Resuelto Por',
        help_text='Usuario que resolvió la observación'
    )
    fecha_resolucion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Resolución',
        help_text='Fecha y hora en que se resolvió'
    )
    notas_resolucion = models.TextField(
        blank=True,
        verbose_name='Notas de Resolución',
        help_text='Notas sobre cómo se resolvió la observación'
    )
    
    class Meta:
        verbose_name = 'Observación de Importación'
        verbose_name_plural = 'Observaciones de Importación'
        ordering = ['-fecha_importacion', 'fila_excel']
        indexes = [
            models.Index(fields=['modulo', 'fecha_importacion']),
            models.Index(fields=['tipo', 'severidad']),
            models.Index(fields=['resuelto']),
            models.Index(fields=['usuario']),
        ]
    
    def __str__(self):
        return f"{self.get_modulo_display()} - Fila {self.fila_excel}: {self.get_tipo_display()}"
    
    def marcar_como_resuelto(self, usuario, notas=''):
        """Marca la observación como resuelta"""
        from django.utils import timezone
        self.resuelto = True
        self.resuelto_por = usuario
        self.fecha_resolucion = timezone.now()
        self.notas_resolucion = notas
        self.save()
    
    @classmethod
    def crear_observacion(cls, modulo, tipo, fila_excel, campo, mensaje, 
                         valor_original='', valor_procesado='', severidad='warning',
                         usuario=None, archivo_nombre='', datos_adicionales=None):
        """Helper para crear una observación"""
        return cls.objects.create(
            modulo=modulo,
            tipo=tipo,
            severidad=severidad,
            fila_excel=fila_excel,
            campo=campo,
            valor_original=valor_original,
            valor_procesado=valor_procesado,
            mensaje=mensaje,
            usuario=usuario,
            archivo_nombre=archivo_nombre,
            datos_adicionales=datos_adicionales or {}
        )
    
    @classmethod
    def obtener_pendientes(cls, modulo=None):
        """Obtiene observaciones pendientes de resolver"""
        queryset = cls.objects.filter(resuelto=False)
        if modulo:
            queryset = queryset.filter(modulo=modulo)
        return queryset.order_by('-fecha_importacion', 'fila_excel')
    
    @classmethod
    def obtener_por_archivo(cls, archivo_nombre):
        """Obtiene todas las observaciones de un archivo específico"""
        return cls.objects.filter(archivo_nombre=archivo_nombre).order_by('fila_excel')


class Catalogo(BaseModel):
    """Modelo para el catálogo oficial de bienes del SBN"""
    
    ESTADO_CHOICES = [
        ('ACTIVO', 'Activo'),
        ('EXCLUIDO', 'Excluido'),
    ]
    
    codigo = models.CharField(
        max_length=20, 
        unique=True,
        verbose_name='Código de Catálogo',
        help_text='Código único del catálogo SBN (ej: 04220001)'
    )
    denominacion = models.CharField(
        max_length=500, 
        verbose_name='Denominación del Bien',
        help_text='Nombre oficial del bien según catálogo SBN'
    )
    grupo = models.CharField(
        max_length=50,
        verbose_name='Grupo',
        help_text='Código y descripción del grupo (ej: 04 AGRICOLA Y PESQUERO)'
    )
    clase = models.CharField(
        max_length=50,
        verbose_name='Clase',
        help_text='Código y descripción de la clase (ej: 22 EQUIPO)'
    )
    resolucion = models.CharField(
        max_length=100,
        verbose_name='Resolución',
        help_text='Resolución que aprueba el bien (ej: 011-2019/SBN)'
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='ACTIVO',
        verbose_name='Estado',
        help_text='Estado del bien en el catálogo'
    )
    
    class Meta:
        verbose_name = 'Catálogo'
        verbose_name_plural = 'Catálogos'
        ordering = ['codigo']
        indexes = [
            models.Index(fields=['codigo']),
            models.Index(fields=['denominacion']),
            models.Index(fields=['grupo']),
            models.Index(fields=['clase']),
            models.Index(fields=['estado']),
        ]
    
    def __str__(self):
        base_str = f"{self.codigo} - {self.denominacion}"
        return self.get_str_with_delete_status(base_str)
    
    def clean(self):
        """Validaciones personalizadas"""
        super().clean()
        
        # Validar formato del código
        if self.codigo and not self.codigo.isdigit():
            raise ValidationError({
                'codigo': 'El código debe contener solo números'
            })
        
        # Validar longitud del código
        if self.codigo and len(self.codigo) != 8:
            raise ValidationError({
                'codigo': 'El código debe tener exactamente 8 dígitos'
            })
        
        # Validar que la denominación no esté vacía
        if not self.denominacion or not self.denominacion.strip():
            raise ValidationError({
                'denominacion': 'La denominación no puede estar vacía'
            })
        
        # Normalizar denominación (mayúsculas)
        if self.denominacion:
            self.denominacion = self.denominacion.upper().strip()
    
    def save(self, *args, **kwargs):
        """Override save para ejecutar validaciones"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def grupo_codigo(self):
        """Extrae el código del grupo"""
        if self.grupo:
            return self.grupo.split()[0] if self.grupo.split() else ''
        return ''
    
    @property
    def grupo_descripcion(self):
        """Extrae la descripción del grupo"""
        if self.grupo:
            parts = self.grupo.split(' ', 1)
            return parts[1] if len(parts) > 1 else ''
        return ''
    
    @property
    def clase_codigo(self):
        """Extrae el código de la clase"""
        if self.clase:
            return self.clase.split()[0] if self.clase.split() else ''
        return ''
    
    @property
    def clase_descripcion(self):
        """Extrae la descripción de la clase"""
        if self.clase:
            parts = self.clase.split(' ', 1)
            return parts[1] if len(parts) > 1 else ''
        return ''
    
    @classmethod
    def buscar_por_denominacion(cls, termino):
        """Busca bienes por denominación"""
        return cls.objects.filter(
            denominacion__icontains=termino,
            estado='ACTIVO'
        ).order_by('denominacion')
    
    @classmethod
    def obtener_grupos(cls):
        """Obtiene lista única de grupos"""
        return cls.objects.filter(
            estado='ACTIVO'
        ).values_list('grupo', flat=True).distinct().order_by('grupo')
    
    @classmethod
    def obtener_clases_por_grupo(cls, grupo):
        """Obtiene clases de un grupo específico"""
        return cls.objects.filter(
            grupo=grupo,
            estado='ACTIVO'
        ).values_list('clase', flat=True).distinct().order_by('clase')
    
    def delete(self, user=None, reason='', *args, **kwargs):
        """
        Override delete para usar soft delete por defecto.
        Valida que no haya bienes activos antes de eliminar.
        """
        from django.core.exceptions import ValidationError
        
        # Validar que no haya bienes activos
        if not self.puede_eliminarse():
            raise ValidationError(
                'No se puede eliminar este catálogo porque tiene bienes patrimoniales activos asociados. '
                'Primero debe eliminar o reasignar los bienes.'
            )
        
        # Usar soft delete
        return self.soft_delete(user=user, reason=reason)
    
    def puede_eliminarse(self):
        """
        Verifica si el catálogo puede eliminarse.
        Solo puede eliminarse si no tiene bienes activos (no eliminados).
        """
        try:
            from apps.bienes.models import BienPatrimonial
            # Contar solo bienes activos (no eliminados)
            bienes_activos = BienPatrimonial.objects.filter(catalogo=self).count()
            return bienes_activos == 0
        except ImportError:
            # Si no existe el modelo BienPatrimonial, permitir eliminación
            return True