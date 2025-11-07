from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from apps.core.models import BaseModel
import json


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
    
    # Campos de auditoría
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='oficinas_creadas',
        verbose_name='Creado por',
        null=True,
        blank=True
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='oficinas_modificadas',
        verbose_name='Modificado por',
        null=True,
        blank=True
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
        base_str = f"{self.codigo} - {self.nombre}"
        return self.get_str_with_delete_status(base_str)
    
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


class HistorialOficina(models.Model):
    """Modelo para el historial de cambios de oficinas"""
    
    ACCIONES = [
        ('CREAR', 'Creación'),
        ('EDITAR', 'Edición'),
        ('ACTIVAR', 'Activación'),
        ('DESACTIVAR', 'Desactivación'),
        ('IMPORTAR', 'Importación'),
    ]
    
    oficina = models.ForeignKey(
        Oficina,
        on_delete=models.CASCADE,
        related_name='historial',
        verbose_name='Oficina'
    )
    accion = models.CharField(
        max_length=20,
        choices=ACCIONES,
        verbose_name='Acción'
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        verbose_name='Usuario'
    )
    fecha = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha'
    )
    datos_anteriores = models.JSONField(
        null=True,
        blank=True,
        verbose_name='Datos anteriores',
        help_text='Estado anterior de la oficina'
    )
    datos_nuevos = models.JSONField(
        null=True,
        blank=True,
        verbose_name='Datos nuevos',
        help_text='Estado nuevo de la oficina'
    )
    observaciones = models.TextField(
        blank=True,
        verbose_name='Observaciones',
        help_text='Comentarios adicionales sobre el cambio'
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='Dirección IP'
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name='User Agent'
    )
    
    class Meta:
        verbose_name = 'Historial de Oficina'
        verbose_name_plural = 'Historiales de Oficinas'
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['oficina', '-fecha']),
            models.Index(fields=['usuario', '-fecha']),
            models.Index(fields=['accion', '-fecha']),
        ]
    
    def __str__(self):
        return f"{self.oficina.codigo} - {self.get_accion_display()} por {self.usuario.username} ({self.fecha.strftime('%d/%m/%Y %H:%M')})"
    
    @property
    def cambios_detallados(self):
        """Retorna una lista de cambios específicos"""
        if not self.datos_anteriores or not self.datos_nuevos:
            return []
        
        cambios = []
        campos_nombres = {
            'codigo': 'Código',
            'nombre': 'Nombre',
            'descripcion': 'Descripción',
            'responsable': 'Responsable',
            'cargo_responsable': 'Cargo del Responsable',
            'telefono': 'Teléfono',
            'email': 'Email',
            'ubicacion': 'Ubicación',
            'estado': 'Estado'
        }
        
        for campo, valor_nuevo in self.datos_nuevos.items():
            if campo in self.datos_anteriores:
                valor_anterior = self.datos_anteriores[campo]
                if valor_anterior != valor_nuevo:
                    nombre_campo = campos_nombres.get(campo, campo)
                    cambios.append({
                        'campo': nombre_campo,
                        'anterior': valor_anterior,
                        'nuevo': valor_nuevo
                    })
        
        return cambios
    
    @classmethod
    def registrar_cambio(cls, oficina, accion, usuario, datos_anteriores=None, datos_nuevos=None, observaciones='', request=None):
        """Registra un cambio en el historial"""
        # Obtener información de la request si está disponible
        ip_address = None
        user_agent = ''
        
        if request:
            # Obtener IP real considerando proxies
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0].strip()
            else:
                ip_address = request.META.get('REMOTE_ADDR')
            
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]  # Limitar longitud
        
        return cls.objects.create(
            oficina=oficina,
            accion=accion,
            usuario=usuario,
            datos_anteriores=datos_anteriores,
            datos_nuevos=datos_nuevos,
            observaciones=observaciones,
            ip_address=ip_address,
            user_agent=user_agent
        )