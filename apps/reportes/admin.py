from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import ConfiguracionFiltro, ReporteGenerado


@admin.register(ConfiguracionFiltro)
class ConfiguracionFiltroAdmin(admin.ModelAdmin):
    """Administración de configuraciones de filtros"""
    
    list_display = [
        'nombre', 'usuario', 'es_publica', 'veces_usado', 
        'ultima_vez_usado', 'created_at'
    ]
    list_filter = [
        'es_publica', 'created_at', 'updated_at', 'ultima_vez_usado'
    ]
    search_fields = ['nombre', 'descripcion', 'usuario__username']
    readonly_fields = ['veces_usado', 'ultima_vez_usado', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Información General', {
            'fields': ('nombre', 'descripcion', 'usuario', 'es_publica')
        }),
        ('Filtros Básicos', {
            'fields': ('oficinas', 'estados_bien', 'grupos_catalogo', 'clases_catalogo'),
            'classes': ('collapse',)
        }),
        ('Filtros de Texto', {
            'fields': ('marcas', 'modelos', 'codigo_patrimonial', 'denominacion', 'serie', 'placa'),
            'classes': ('collapse',)
        }),
        ('Filtros de Fechas', {
            'fields': (
                'fecha_adquisicion_desde', 'fecha_adquisicion_hasta',
                'fecha_registro_desde', 'fecha_registro_hasta'
            ),
            'classes': ('collapse',)
        }),
        ('Filtros de Valores', {
            'fields': ('valor_minimo', 'valor_maximo'),
            'classes': ('collapse',)
        }),
        ('Configuración Avanzada', {
            'fields': ('operador_principal', 'configuracion_avanzada'),
            'classes': ('collapse',)
        }),
        ('Estadísticas de Uso', {
            'fields': ('veces_usado', 'ultima_vez_usado'),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimizar consultas"""
        return super().get_queryset(request).select_related('usuario')
    
    def has_change_permission(self, request, obj=None):
        """Solo el propietario o superusuarios pueden editar"""
        if obj and not request.user.is_superuser:
            return obj.usuario == request.user
        return super().has_change_permission(request, obj)
    
    def has_delete_permission(self, request, obj=None):
        """Solo el propietario o superusuarios pueden eliminar"""
        if obj and not request.user.is_superuser:
            return obj.usuario == request.user
        return super().has_delete_permission(request, obj)


@admin.register(ReporteGenerado)
class ReporteGeneradoAdmin(admin.ModelAdmin):
    """Administración de reportes generados"""
    
    list_display = [
        'nombre', 'tipo_reporte', 'formato', 'usuario', 'estado',
        'total_registros', 'fecha_inicio', 'tiempo_procesamiento_display',
        'archivo_disponible'
    ]
    list_filter = [
        'tipo_reporte', 'formato', 'estado', 'fecha_inicio', 'fecha_completado'
    ]
    search_fields = ['nombre', 'usuario__username']
    readonly_fields = [
        'fecha_inicio', 'fecha_completado', 'tiempo_procesamiento',
        'total_registros', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Información General', {
            'fields': ('nombre', 'tipo_reporte', 'formato', 'usuario')
        }),
        ('Configuración', {
            'fields': ('configuracion_filtro', 'parametros'),
            'classes': ('collapse',)
        }),
        ('Estado y Resultados', {
            'fields': (
                'estado', 'total_registros', 'archivo_generado',
                'mensaje_error', 'fecha_expiracion'
            )
        }),
        ('Tiempos de Procesamiento', {
            'fields': (
                'fecha_inicio', 'fecha_completado', 'tiempo_procesamiento'
            ),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimizar consultas"""
        return super().get_queryset(request).select_related(
            'usuario', 'configuracion_filtro'
        )
    
    def tiempo_procesamiento_display(self, obj):
        """Mostrar tiempo de procesamiento formateado"""
        if obj.tiempo_procesamiento:
            total_seconds = int(obj.tiempo_procesamiento.total_seconds())
            minutes, seconds = divmod(total_seconds, 60)
            if minutes > 0:
                return f"{minutes}m {seconds}s"
            return f"{seconds}s"
        return "-"
    tiempo_procesamiento_display.short_description = "Tiempo"
    
    def archivo_disponible(self, obj):
        """Indicar si el archivo está disponible"""
        if obj.puede_descargarse():
            return format_html(
                '<span style="color: green;">✓ Disponible</span>'
            )
        elif obj.estado == 'GENERANDO':
            return format_html(
                '<span style="color: orange;">⏳ Generando</span>'
            )
        elif obj.estado == 'ERROR':
            return format_html(
                '<span style="color: red;">✗ Error</span>'
            )
        elif obj.esta_expirado():
            return format_html(
                '<span style="color: gray;">⌛ Expirado</span>'
            )
        return format_html(
            '<span style="color: gray;">- No disponible</span>'
        )
    archivo_disponible.short_description = "Archivo"
    
    def has_change_permission(self, request, obj=None):
        """Solo el propietario o superusuarios pueden editar"""
        if obj and not request.user.is_superuser:
            return obj.usuario == request.user
        return super().has_change_permission(request, obj)
    
    def has_delete_permission(self, request, obj=None):
        """Solo el propietario o superusuarios pueden eliminar"""
        if obj and not request.user.is_superuser:
            return obj.usuario == request.user
        return super().has_delete_permission(request, obj)
    
    actions = ['limpiar_reportes_expirados', 'marcar_como_expirado']
    
    def limpiar_reportes_expirados(self, request, queryset):
        """Acción para limpiar reportes expirados"""
        cantidad = ReporteGenerado.limpiar_expirados()
        self.message_user(
            request,
            f"Se limpiaron {cantidad} reportes expirados del sistema."
        )
    limpiar_reportes_expirados.short_description = "Limpiar reportes expirados"
    
    def marcar_como_expirado(self, request, queryset):
        """Acción para marcar reportes como expirados"""
        cantidad = 0
        for reporte in queryset:
            if reporte.estado == 'COMPLETADO':
                # Eliminar archivo físico
                if reporte.archivo_generado:
                    try:
                        reporte.archivo_generado.delete()
                    except Exception:
                        pass
                
                # Marcar como expirado
                reporte.estado = 'EXPIRADO'
                reporte.archivo_generado = None
                reporte.fecha_expiracion = timezone.now()
                reporte.save()
                cantidad += 1
        
        self.message_user(
            request,
            f"Se marcaron {cantidad} reportes como expirados."
        )
    marcar_como_expirado.short_description = "Marcar como expirado"