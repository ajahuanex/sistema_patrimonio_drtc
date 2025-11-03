from django.contrib import admin
from django.utils.html import format_html
from .models import Catalogo


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