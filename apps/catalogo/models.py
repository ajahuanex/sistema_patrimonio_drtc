from django.db import models
from django.core.exceptions import ValidationError
from apps.core.models import BaseModel


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
        unique=True,
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