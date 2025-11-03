from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Oficina


@admin.register(Oficina)
class OficinaAdmin(admin.ModelAdmin):
    list_display = [
        'codigo',
        'nombre',
        'responsable',
        'total_bienes_display',
        'estado_badge',
        'telefono',
        'created_at'
    ]
    list_filter = [
        'estado',
        'created_at',
        'updated_at'
    ]
    search_fields = [
        'codigo',
        'nombre',
        'responsable',
        'descripcion',
        'ubicacion'
    ]
    readonly_fields = [
        'total_bienes_display',
        'bienes_activos_display',
        'created_at',
        'updated_at',
        'created_by',
        'updated_by'
    ]
    list_per_page = 25
    ordering = ['codigo']
    
    fieldsets = (
        ('Información Principal', {
            'fields': ('codigo', 'nombre', 'descripcion', 'estado')
        }),
        ('Responsable', {
            'fields': ('responsable', 'cargo_responsable')
        }),
        ('Contacto', {
            'fields': ('telefono', 'email', 'ubicacion')
        }),
        ('Estadísticas', {
            'fields': ('total_bienes_display', 'bienes_activos_display'),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def estado_badge(self, obj):
        """Muestra el estado con colores"""
        if obj.estado:
            return format_html(
                '<span style="color: green; font-weight: bold;">●</span> Activa'
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">●</span> Inactiva'
            )
    estado_badge.short_description = 'Estado'
    
    def total_bienes_display(self, obj):
        """Muestra el total de bienes con enlace"""
        total = obj.total_bienes
        if total > 0:
            # Aquí se podría agregar un enlace a la lista de bienes filtrada
            return format_html(
                '<strong>{}</strong> bienes',
                total
            )
        return '0 bienes'
    total_bienes_display.short_description = 'Total Bienes'
    
    def bienes_activos_display(self, obj):
        """Muestra los bienes activos"""
        activos = obj.bienes_activos
        total = obj.total_bienes
        if total > 0:
            porcentaje = (activos / total) * 100
            return format_html(
                '{} activos ({:.1f}%)',
                activos,
                porcentaje
            )
        return '0 activos'
    bienes_activos_display.short_description = 'Bienes Activos'
    
    def save_model(self, request, obj, form, change):
        """Guarda el modelo con información del usuario"""
        if not change:  # Nuevo objeto
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    actions = ['activar_oficinas', 'desactivar_oficinas']
    
    def activar_oficinas(self, request, queryset):
        """Acción para activar oficinas seleccionadas"""
        updated = queryset.update(estado=True)
        self.message_user(
            request,
            f'{updated} oficinas fueron activadas exitosamente.'
        )
    activar_oficinas.short_description = "Activar oficinas seleccionadas"
    
    def desactivar_oficinas(self, request, queryset):
        """Acción para desactivar oficinas seleccionadas"""
        # Verificar que no tengan bienes asignados
        oficinas_con_bienes = []
        for oficina in queryset:
            if oficina.total_bienes > 0:
                oficinas_con_bienes.append(oficina.nombre)
        
        if oficinas_con_bienes:
            self.message_user(
                request,
                f'No se pueden desactivar las siguientes oficinas porque tienen bienes asignados: {", ".join(oficinas_con_bienes)}',
                level='ERROR'
            )
            return
        
        updated = queryset.update(estado=False)
        self.message_user(
            request,
            f'{updated} oficinas fueron desactivadas exitosamente.'
        )
    desactivar_oficinas.short_description = "Desactivar oficinas seleccionadas"
    
    def delete_model(self, request, obj):
        """Override delete para verificar bienes asignados"""
        if not obj.puede_eliminarse():
            self.message_user(
                request,
                f'No se puede eliminar la oficina "{obj.nombre}" porque tiene {obj.total_bienes} bienes asignados.',
                level='ERROR'
            )
            return
        super().delete_model(request, obj)
    
    def delete_queryset(self, request, queryset):
        """Override delete masivo para verificar bienes asignados"""
        oficinas_con_bienes = []
        oficinas_eliminables = []
        
        for oficina in queryset:
            if oficina.puede_eliminarse():
                oficinas_eliminables.append(oficina)
            else:
                oficinas_con_bienes.append(f"{oficina.nombre} ({oficina.total_bienes} bienes)")
        
        if oficinas_con_bienes:
            self.message_user(
                request,
                f'No se pueden eliminar las siguientes oficinas porque tienen bienes asignados: {", ".join(oficinas_con_bienes)}',
                level='ERROR'
            )
        
        if oficinas_eliminables:
            count = len(oficinas_eliminables)
            for oficina in oficinas_eliminables:
                oficina.delete()
            self.message_user(
                request,
                f'{count} oficinas fueron eliminadas exitosamente.'
            )