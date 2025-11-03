from django.db import models
from django.core.exceptions import ValidationError
from apps.core.models import BaseModel


class Oficina(BaseModel):
    """Modelo para las oficinas de la DRTC Puno"""
    
    codigo = models.CharField(
        max_length=20, 
        unique=True,
        verbose_name='Código de Oficina',
        help_text='Código único de la oficina (ej: DIR-001, ADM-002)'
    )
    nombre = models.CharField(
        max_length=200,
        verbose_name='Nombre de la Oficina',
        help_text='Nombre completo de la oficina'
    )
    descripcion = models.TextField(
        blank=True,
        verbose_name='Descripción',
        help_text='Descripción detallada de la oficina y sus funciones'
    )
    responsable = models.CharField(
        max_length=200,
        verbose_name='Responsable',
        help_text='Nombre del responsable de la oficina'
    )
    cargo_responsable = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Cargo del Responsable',
        help_text='Cargo o puesto del responsable'
    )
    telefono = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Teléfono',
        help_text='Número de teléfono de la oficina'
    )
    email = models.EmailField(
        blank=True,
        verbose_name='Email',
        help_text='Correo electrónico de la oficina'
    )
    ubicacion = models.CharField(
        max_length=300,
        blank=True,
        verbose_name='Ubicación',
        help_text='Ubicación física de la oficina (piso, edificio, etc.)'
    )
    estado = models.BooleanField(
        default=True,
        verbose_name='Estado',
        help_text='Indica si la oficina está activa'
    )
    
    class Meta:
        verbose_name = 'Oficina'
        verbose_name_plural = 'Oficinas'
        ordering = ['codigo']
        indexes = [
            models.Index(fields=['codigo']),
            models.Index(fields=['nombre']),
            models.Index(fields=['estado']),
            models.Index(fields=['responsable']),
        ]
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"
    
    def clean(self):
        """Validaciones personalizadas"""
        super().clean()
        
        # Validar que el código no esté vacío
        if not self.codigo or not self.codigo.strip():
            raise ValidationError({
                'codigo': 'El código de oficina no puede estar vacío'
            })
        
        # Validar que el nombre no esté vacío
        if not self.nombre or not self.nombre.strip():
            raise ValidationError({
                'nombre': 'El nombre de la oficina no puede estar vacío'
            })
        
        # Validar que el responsable no esté vacío
        if not self.responsable or not self.responsable.strip():
            raise ValidationError({
                'responsable': 'El responsable no puede estar vacío'
            })
        
        # Normalizar campos
        if self.codigo:
            self.codigo = self.codigo.upper().strip()
        if self.nombre:
            self.nombre = self.nombre.strip()
        if self.responsable:
            self.responsable = self.responsable.strip()
    
    def save(self, *args, **kwargs):
        """Override save para ejecutar validaciones"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def estado_texto(self):
        """Retorna el estado como texto"""
        return 'Activa' if self.estado else 'Inactiva'
    
    @property
    def total_bienes(self):
        """Retorna el total de bienes asignados a esta oficina"""
        return self.bienpatrimonial_set.count()
    
    @property
    def bienes_activos(self):
        """Retorna el total de bienes activos en esta oficina"""
        return self.bienpatrimonial_set.exclude(
            estado_bien__in=['E', 'C']  # Excluir RAEE y Chatarra
        ).count()
    
    @classmethod
    def obtener_activas(cls):
        """Obtiene solo las oficinas activas"""
        return cls.objects.filter(estado=True).order_by('nombre')
    
    @classmethod
    def buscar_por_nombre(cls, termino):
        """Busca oficinas por nombre o código"""
        return cls.objects.filter(
            models.Q(nombre__icontains=termino) |
            models.Q(codigo__icontains=termino)
        ).order_by('nombre')
    
    @classmethod
    def buscar_por_responsable(cls, termino):
        """Busca oficinas por responsable"""
        return cls.objects.filter(
            responsable__icontains=termino
        ).order_by('nombre')
    
    def puede_eliminarse(self):
        """Verifica si la oficina puede eliminarse"""
        return self.total_bienes == 0
    
    def desactivar(self):
        """Desactiva la oficina"""
        self.estado = False
        self.save()
    
    def activar(self):
        """Activa la oficina"""
        self.estado = True
        self.save()