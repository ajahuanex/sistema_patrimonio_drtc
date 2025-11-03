from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import json
from apps.core.models import BaseModel


class ConfiguracionFiltro(BaseModel):
    """Modelo para guardar configuraciones de filtros reutilizables"""
    
    OPERADORES_LOGICOS = [
        ('AND', 'Y (AND)'),
        ('OR', 'O (OR)'),
    ]
    
    nombre = models.CharField(
        max_length=200,
        verbose_name='Nombre de la Configuración',
        help_text='Nombre descriptivo para la configuración de filtros'
    )
    descripcion = models.TextField(
        blank=True,
        verbose_name='Descripción',
        help_text='Descripción detallada de los filtros aplicados'
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Usuario',
        help_text='Usuario que creó la configuración'
    )
    es_publica = models.BooleanField(
        default=False,
        verbose_name='Es Pública',
        help_text='Si está marcado, otros usuarios pueden usar esta configuración'
    )
    
    # Filtros básicos
    oficinas = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Oficinas',
        help_text='Lista de IDs de oficinas seleccionadas'
    )
    estados_bien = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Estados del Bien',
        help_text='Lista de estados seleccionados (N, B, R, M, E, C)'
    )
    grupos_catalogo = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Grupos de Catálogo',
        help_text='Lista de grupos de catálogo seleccionados'
    )
    clases_catalogo = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Clases de Catálogo',
        help_text='Lista de clases de catálogo seleccionadas'
    )
    marcas = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Marcas',
        help_text='Lista de marcas seleccionadas'
    )
    modelos = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Modelos',
        help_text='Lista de modelos seleccionados'
    )
    
    # Filtros de fechas
    fecha_adquisicion_desde = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha Adquisición Desde',
        help_text='Fecha de inicio para filtro de adquisición'
    )
    fecha_adquisicion_hasta = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha Adquisición Hasta',
        help_text='Fecha de fin para filtro de adquisición'
    )
    fecha_registro_desde = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha Registro Desde',
        help_text='Fecha de inicio para filtro de registro'
    )
    fecha_registro_hasta = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha Registro Hasta',
        help_text='Fecha de fin para filtro de registro'
    )
    
    # Filtros de valor
    valor_minimo = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Valor Mínimo',
        help_text='Valor mínimo de adquisición'
    )
    valor_maximo = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Valor Máximo',
        help_text='Valor máximo de adquisición'
    )
    
    # Filtros de texto
    codigo_patrimonial = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Código Patrimonial',
        help_text='Filtro por código patrimonial (búsqueda parcial)'
    )
    denominacion = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Denominación',
        help_text='Filtro por denominación del bien (búsqueda parcial)'
    )
    serie = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Serie',
        help_text='Filtro por número de serie (búsqueda parcial)'
    )
    placa = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Placa',
        help_text='Filtro por placa (búsqueda parcial)'
    )
    
    # Configuración de operadores lógicos
    operador_principal = models.CharField(
        max_length=3,
        choices=OPERADORES_LOGICOS,
        default='AND',
        verbose_name='Operador Principal',
        help_text='Operador lógico principal para combinar filtros'
    )
    
    # Configuración avanzada (JSON para filtros complejos)
    configuracion_avanzada = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Configuración Avanzada',
        help_text='Configuración JSON para filtros complejos'
    )
    
    # Estadísticas de uso
    veces_usado = models.PositiveIntegerField(
        default=0,
        verbose_name='Veces Usado',
        help_text='Número de veces que se ha usado esta configuración'
    )
    ultima_vez_usado = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Última Vez Usado',
        help_text='Fecha y hora del último uso'
    )
    
    class Meta:
        verbose_name = 'Configuración de Filtro'
        verbose_name_plural = 'Configuraciones de Filtros'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['usuario']),
            models.Index(fields=['es_publica']),
            models.Index(fields=['nombre']),
        ]
        unique_together = [['usuario', 'nombre']]
    
    def __str__(self):
        return f"{self.nombre} ({self.usuario.username})"
    
    def clean(self):
        """Validaciones personalizadas"""
        super().clean()
        
        # Validar que el nombre no esté vacío
        if not self.nombre or not self.nombre.strip():
            raise ValidationError({
                'nombre': 'El nombre de la configuración no puede estar vacío'
            })
        
        # Validar fechas
        if (self.fecha_adquisicion_desde and self.fecha_adquisicion_hasta and 
            self.fecha_adquisicion_desde > self.fecha_adquisicion_hasta):
            raise ValidationError({
                'fecha_adquisicion_hasta': 'La fecha hasta debe ser mayor o igual a la fecha desde'
            })
        
        if (self.fecha_registro_desde and self.fecha_registro_hasta and 
            self.fecha_registro_desde > self.fecha_registro_hasta):
            raise ValidationError({
                'fecha_registro_hasta': 'La fecha hasta debe ser mayor o igual a la fecha desde'
            })
        
        # Validar valores
        if (self.valor_minimo and self.valor_maximo and 
            self.valor_minimo > self.valor_maximo):
            raise ValidationError({
                'valor_maximo': 'El valor máximo debe ser mayor o igual al valor mínimo'
            })
    
    def save(self, *args, **kwargs):
        """Override save para ejecutar validaciones"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    def incrementar_uso(self):
        """Incrementa el contador de uso y actualiza la fecha"""
        from django.utils import timezone
        self.veces_usado += 1
        self.ultima_vez_usado = timezone.now()
        self.save(update_fields=['veces_usado', 'ultima_vez_usado'])
    
    def to_dict(self):
        """Convierte la configuración a diccionario para uso en filtros"""
        return {
            'oficinas': self.oficinas,
            'estados_bien': self.estados_bien,
            'grupos_catalogo': self.grupos_catalogo,
            'clases_catalogo': self.clases_catalogo,
            'marcas': self.marcas,
            'modelos': self.modelos,
            'fecha_adquisicion_desde': self.fecha_adquisicion_desde,
            'fecha_adquisicion_hasta': self.fecha_adquisicion_hasta,
            'fecha_registro_desde': self.fecha_registro_desde,
            'fecha_registro_hasta': self.fecha_registro_hasta,
            'valor_minimo': self.valor_minimo,
            'valor_maximo': self.valor_maximo,
            'codigo_patrimonial': self.codigo_patrimonial,
            'denominacion': self.denominacion,
            'serie': self.serie,
            'placa': self.placa,
            'operador_principal': self.operador_principal,
            'configuracion_avanzada': self.configuracion_avanzada,
        }
    
    @classmethod
    def obtener_publicas(cls):
        """Obtiene configuraciones públicas"""
        return cls.objects.filter(es_publica=True).order_by('nombre')
    
    @classmethod
    def obtener_por_usuario(cls, usuario):
        """Obtiene configuraciones de un usuario específico"""
        return cls.objects.filter(usuario=usuario).order_by('nombre')
    
    @classmethod
    def obtener_disponibles_para_usuario(cls, usuario):
        """Obtiene configuraciones disponibles para un usuario (propias + públicas)"""
        from django.db.models import Q
        return cls.objects.filter(
            Q(usuario=usuario) | Q(es_publica=True)
        ).order_by('nombre')


class ReporteGenerado(BaseModel):
    """Modelo para almacenar información de reportes generados"""
    
    TIPOS_REPORTE = [
        ('INVENTARIO', 'Inventario General'),
        ('ESTADISTICO', 'Reporte Estadístico'),
        ('EJECUTIVO', 'Reporte Ejecutivo'),
        ('STICKERS', 'Plantilla de Stickers'),
        ('PERSONALIZADO', 'Reporte Personalizado'),
    ]
    
    FORMATOS_EXPORTACION = [
        ('EXCEL', 'Excel (.xlsx)'),
        ('PDF', 'PDF'),
        ('CSV', 'CSV'),
        ('ZPL', 'Plantilla ZPL'),
    ]
    
    ESTADOS_REPORTE = [
        ('GENERANDO', 'Generando'),
        ('COMPLETADO', 'Completado'),
        ('ERROR', 'Error'),
        ('EXPIRADO', 'Expirado'),
    ]
    
    nombre = models.CharField(
        max_length=200,
        verbose_name='Nombre del Reporte',
        help_text='Nombre descriptivo del reporte'
    )
    tipo_reporte = models.CharField(
        max_length=20,
        choices=TIPOS_REPORTE,
        verbose_name='Tipo de Reporte',
        help_text='Tipo de reporte generado'
    )
    formato = models.CharField(
        max_length=10,
        choices=FORMATOS_EXPORTACION,
        verbose_name='Formato',
        help_text='Formato de exportación del reporte'
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Usuario',
        help_text='Usuario que generó el reporte'
    )
    configuracion_filtro = models.ForeignKey(
        ConfiguracionFiltro,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Configuración de Filtro',
        help_text='Configuración de filtros utilizada'
    )
    
    # Parámetros del reporte
    parametros = models.JSONField(
        default=dict,
        verbose_name='Parámetros',
        help_text='Parámetros utilizados para generar el reporte'
    )
    
    # Estado y resultados
    estado = models.CharField(
        max_length=15,
        choices=ESTADOS_REPORTE,
        default='GENERANDO',
        verbose_name='Estado',
        help_text='Estado actual del reporte'
    )
    total_registros = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Total de Registros',
        help_text='Número total de registros en el reporte'
    )
    archivo_generado = models.FileField(
        upload_to='reportes/',
        blank=True,
        verbose_name='Archivo Generado',
        help_text='Archivo del reporte generado'
    )
    
    # Información de procesamiento
    fecha_inicio = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Inicio',
        help_text='Fecha y hora de inicio de generación'
    )
    fecha_completado = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Completado',
        help_text='Fecha y hora de completado'
    )
    tiempo_procesamiento = models.DurationField(
        null=True,
        blank=True,
        verbose_name='Tiempo de Procesamiento',
        help_text='Tiempo total de procesamiento'
    )
    mensaje_error = models.TextField(
        blank=True,
        verbose_name='Mensaje de Error',
        help_text='Mensaje de error si el reporte falló'
    )
    
    # Configuración de expiración
    fecha_expiracion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Expiración',
        help_text='Fecha de expiración del archivo'
    )
    
    class Meta:
        verbose_name = 'Reporte Generado'
        verbose_name_plural = 'Reportes Generados'
        ordering = ['-fecha_inicio']
        indexes = [
            models.Index(fields=['usuario']),
            models.Index(fields=['tipo_reporte']),
            models.Index(fields=['estado']),
            models.Index(fields=['fecha_inicio']),
        ]
    
    def __str__(self):
        return f"{self.nombre} - {self.get_tipo_reporte_display()} ({self.usuario.username})"
    
    def marcar_completado(self):
        """Marca el reporte como completado"""
        from django.utils import timezone
        self.estado = 'COMPLETADO'
        self.fecha_completado = timezone.now()
        if self.fecha_inicio:
            self.tiempo_procesamiento = self.fecha_completado - self.fecha_inicio
        self.save()
    
    def marcar_error(self, mensaje_error):
        """Marca el reporte como error"""
        from django.utils import timezone
        self.estado = 'ERROR'
        self.mensaje_error = mensaje_error
        self.fecha_completado = timezone.now()
        if self.fecha_inicio:
            self.tiempo_procesamiento = self.fecha_completado - self.fecha_inicio
        self.save()
    
    def esta_expirado(self):
        """Verifica si el reporte está expirado"""
        from django.utils import timezone
        return (self.fecha_expiracion and 
                timezone.now() > self.fecha_expiracion)
    
    def puede_descargarse(self):
        """Verifica si el reporte puede descargarse"""
        return (self.estado == 'COMPLETADO' and 
                self.archivo_generado and 
                not self.esta_expirado())
    
    @classmethod
    def limpiar_expirados(cls):
        """Limpia reportes expirados"""
        from django.utils import timezone
        import os
        
        reportes_expirados = cls.objects.filter(
            fecha_expiracion__lt=timezone.now(),
            estado='COMPLETADO'
        )
        
        for reporte in reportes_expirados:
            # Eliminar archivo físico
            if reporte.archivo_generado:
                try:
                    os.remove(reporte.archivo_generado.path)
                except (OSError, ValueError):
                    pass
            
            # Marcar como expirado
            reporte.estado = 'EXPIRADO'
            reporte.archivo_generado = None
            reporte.save()
        
        return reportes_expirados.count()