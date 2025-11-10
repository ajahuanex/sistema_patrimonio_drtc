from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Catalogo, ImportObservation


@admin.register(Catalogo)
class CatalogoAdmin(admin.ModelAdmin):
    list_display = [
        'codigo', 
        'denominacion_truncada', 
        'grupo_codigo', 
        'clase_codigo', 
        'estado_badge',
        'resolucion',
        'created_at'
    ]
    list_filter = [
        'estado', 
        'grupo', 
        'clase',
        'created_at'
    ]
    search_fields = [
        'codigo', 
        'denominacion', 
        'grupo', 
        'clase',
        'resolucion'
    ]
    readonly_fields = [
        'created_at', 
        'updated_at', 
        'created_by', 
        'updated_by'
    ]
    list_per_page = 50
    ordering = ['codigo']
    
    fieldsets = (
        ('Información Principal', {
            'fields': ('codigo', 'denominacion', 'estado')
        }),
        ('Clasificación', {
            'fields': ('grupo', 'clase', 'resolucion')
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def denominacion_truncada(self, obj):
        """Muestra denominación truncada"""
        if len(obj.denominacion) > 50:
            return f"{obj.denominacion[:50]}..."
        return obj.denominacion
    denominacion_truncada.short_description = 'Denominación'
    
    def grupo_codigo(self, obj):
        """Muestra solo el código del grupo"""
        return obj.grupo_codigo
    grupo_codigo.short_description = 'Grupo'
    
    def clase_codigo(self, obj):
        """Muestra solo el código de la clase"""
        return obj.clase_codigo
    clase_codigo.short_description = 'Clase'
    
    def estado_badge(self, obj):
        """Muestra el estado con colores"""
        if obj.estado == 'ACTIVO':
            return format_html(
                '<span style="color: green; font-weight: bold;">●</span> {}',
                obj.estado
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">●</span> {}',
                obj.estado
            )
    estado_badge.short_description = 'Estado'
    
    def save_model(self, request, obj, form, change):
        """Guarda el modelo con información del usuario"""
        if not change:  # Nuevo objeto
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    actions = ['activar_bienes', 'excluir_bienes']
    
    def activar_bienes(self, request, queryset):
        """Acción para activar bienes seleccionados"""
        updated = queryset.update(estado='ACTIVO')
        self.message_user(
            request,
            f'{updated} bienes fueron activados exitosamente.'
        )
    activar_bienes.short_description = "Activar bienes seleccionados"
    
    def excluir_bienes(self, request, queryset):
        """Acción para excluir bienes seleccionados"""
        updated = queryset.update(estado='EXCLUIDO')
        self.message_user(
            request,
            f'{updated} bienes fueron excluidos exitosamente.'
        )
    excluir_bienes.short_description = "Excluir bienes seleccionados"



@admin.register(ImportObservation)
class ImportObservationAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'modulo_badge',
        'tipo_badge',
        'severidad_badge',
        'fila_excel',
        'campo',
        'mensaje_truncado',
        'fecha_importacion',
        'resuelto_badge',
        'usuario'
    ]
    list_filter = [
        'modulo',
        'tipo',
        'severidad',
        'resuelto',
        'fecha_importacion'
    ]
    search_fields = [
        'mensaje',
        'campo',
        'valor_original',
        'archivo_nombre'
    ]
    readonly_fields = [
        'modulo',
        'tipo',
        'severidad',
        'fila_excel',
        'campo',
        'valor_original',
        'valor_procesado',
        'mensaje',
        'datos_adicionales',
        'fecha_importacion',
        'usuario',
        'archivo_nombre'
    ]
    list_per_page = 50
    ordering = ['-fecha_importacion', 'fila_excel']
    date_hierarchy = 'fecha_importacion'
    
    fieldsets = (
        ('Información de la Observación', {
            'fields': ('modulo', 'tipo', 'severidad', 'fila_excel', 'campo')
        }),
        ('Valores', {
            'fields': ('valor_original', 'valor_procesado', 'mensaje')
        }),
        ('Datos Adicionales', {
            'fields': ('datos_adicionales',),
            'classes': ('collapse',)
        }),
        ('Información de Importación', {
            'fields': ('fecha_importacion', 'usuario', 'archivo_nombre')
        }),
        ('Resolución', {
            'fields': ('resuelto', 'resuelto_por', 'fecha_resolucion', 'notas_resolucion')
        }),
    )
    
    def modulo_badge(self, obj):
        """Muestra el módulo con color"""
        colors = {
            'catalogo': '#3498db',
            'bienes': '#2ecc71',
            'oficinas': '#9b59b6'
        }
        color = colors.get(obj.modulo, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_modulo_display()
        )
    modulo_badge.short_description = 'Módulo'
    
    def tipo_badge(self, obj):
        """Muestra el tipo con color"""
        colors = {
            'duplicado_denominacion': '#f39c12',
            'dato_incompleto': '#e74c3c',
            'formato_invalido': '#e67e22',
            'referencia_faltante': '#c0392b',
            'otro': '#95a5a6'
        }
        color = colors.get(obj.tipo, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_tipo_display()
        )
    tipo_badge.short_description = 'Tipo'
    
    def severidad_badge(self, obj):
        """Muestra la severidad con color"""
        colors = {
            'info': '#3498db',
            'warning': '#f39c12',
            'error': '#e74c3c'
        }
        icons = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'error': '❌'
        }
        color = colors.get(obj.severidad, '#95a5a6')
        icon = icons.get(obj.severidad, '•')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">{} {}</span>',
            color,
            icon,
            obj.get_severidad_display()
        )
    severidad_badge.short_description = 'Severidad'
    
    def mensaje_truncado(self, obj):
        """Muestra el mensaje truncado"""
        if len(obj.mensaje) > 60:
            return f"{obj.mensaje[:60]}..."
        return obj.mensaje
    mensaje_truncado.short_description = 'Mensaje'
    
    def resuelto_badge(self, obj):
        """Muestra el estado de resolución"""
        if obj.resuelto:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Resuelto</span>'
            )
        else:
            return format_html(
                '<span style="color: orange; font-weight: bold;">⏳ Pendiente</span>'
            )
    resuelto_badge.short_description = 'Estado'
    
    actions = ['marcar_como_resuelto', 'marcar_como_pendiente']
    
    def marcar_como_resuelto(self, request, queryset):
        """Marca observaciones como resueltas"""
        for obs in queryset:
            if not obs.resuelto:
                obs.marcar_como_resuelto(
                    usuario=request.user,
                    notas='Marcado como resuelto desde el admin'
                )
        count = queryset.filter(resuelto=True).count()
        self.message_user(
            request,
            f'{count} observación(es) marcada(s) como resuelta(s).'
        )
    marcar_como_resuelto.short_description = "Marcar como resuelto"
    
    def marcar_como_pendiente(self, request, queryset):
        """Marca observaciones como pendientes"""
        updated = queryset.update(
            resuelto=False,
            resuelto_por=None,
            fecha_resolucion=None,
            notas_resolucion=''
        )
        self.message_user(
            request,
            f'{updated} observación(es) marcada(s) como pendiente(s).'
        )
    marcar_como_pendiente.short_description = "Marcar como pendiente"
    
    def has_add_permission(self, request):
        """No permitir agregar observaciones manualmente"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Solo administradores pueden eliminar observaciones"""
        return request.user.is_superuser
