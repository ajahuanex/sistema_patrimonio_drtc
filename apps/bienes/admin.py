from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import BienPatrimonial, MovimientoBien, HistorialEstado


@admin.register(BienPatrimonial)
class BienPatrimonialAdmin(admin.ModelAdmin):
    list_display = [
        'codigo_patrimonial',
        'denominacion_truncada',
        'oficina',
        'estado_bien_badge',
        'marca',
        'modelo',
        'placa',
        'qr_link',
        'created_at'
    ]
    list_filter = [
        'estado_bien',
        'oficina',
        'catalogo__grupo',
        'catalogo__clase',
        'created_at'
    ]
    search_fields = [
        'codigo_patrimonial',
        'codigo_interno',
        'catalogo__denominacion',
        'marca',
        'modelo',
        'serie',
        'placa',
        'matricula',
        'nro_motor',
        'nro_chasis'
    ]
    readonly_fields = [
        'qr_code',
        'url_qr',
        'qr_image_display',
        'created_at',
        'updated_at',
        'created_by',
        'updated_by'
    ]
    list_per_page = 50
    ordering = ['codigo_patrimonial']
    
    fieldsets = (
        ('Información Principal', {
            'fields': (
                'codigo_patrimonial',
                'codigo_interno',
                'catalogo',
                'oficina',
                'estado_bien'
            )
        }),
        ('Características', {
            'fields': (
                'marca',
                'modelo',
                'color',
                'serie',
                'dimension'
            )
        }),
        ('Información de Vehículo', {
            'fields': (
                'placa',
                'matricula',
                'nro_motor',
                'nro_chasis'
            ),
            'classes': ('collapse',)
        }),
        ('Información Adicional', {
            'fields': (
                'fecha_adquisicion',
                'valor_adquisicion',
                'observaciones'
            )
        }),
        ('Código QR', {
            'fields': (
                'qr_code',
                'url_qr',
                'qr_image_display'
            ),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': (
                'created_at',
                'updated_at',
                'created_by',
                'updated_by'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def denominacion_truncada(self, obj):
        """Muestra denominación truncada"""
        denominacion = obj.denominacion
        if len(denominacion) > 40:
            return f"{denominacion[:40]}..."
        return denominacion
    denominacion_truncada.short_description = 'Denominación'
    
    def estado_bien_badge(self, obj):
        """Muestra el estado con colores"""
        colors = {
            'N': 'blue',
            'B': 'green',
            'R': 'orange',
            'M': 'red',
            'E': 'purple',
            'C': 'gray'
        }
        color = colors.get(obj.estado_bien, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">●</span> {}',
            color,
            obj.get_estado_bien_display()
        )
    estado_bien_badge.short_description = 'Estado'
    
    def qr_link(self, obj):
        """Muestra enlace al QR"""
        if obj.qr_code:
            return format_html(
                '<a href="{}" target="_blank">Ver QR</a>',
                obj.url_qr
            )
        return '-'
    qr_link.short_description = 'QR'
    
    def qr_image_display(self, obj):
        """Muestra la imagen del QR"""
        if obj.qr_code:
            try:
                img = obj.generar_qr_image()
                # En un caso real, guardarías la imagen y mostrarías la URL
                return format_html(
                    '<div>Código QR: {}</div><div>URL: <a href="{}" target="_blank">{}</a></div>',
                    obj.qr_code,
                    obj.url_qr,
                    obj.url_qr
                )
            except Exception as e:
                return f"Error generando QR: {e}"
        return 'No generado'
    qr_image_display.short_description = 'Imagen QR'
    
    def save_model(self, request, obj, form, change):
        """Guarda el modelo con información del usuario"""
        if not change:  # Nuevo objeto
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    actions = ['generar_qr_masivo', 'cambiar_estado_bueno']
    
    def generar_qr_masivo(self, request, queryset):
        """Acción para regenerar códigos QR"""
        count = 0
        for bien in queryset:
            if not bien.qr_code:
                bien.save()  # Esto generará el QR automáticamente
                count += 1
        
        self.message_user(
            request,
            f'Se generaron {count} códigos QR exitosamente.'
        )
    generar_qr_masivo.short_description = "Generar códigos QR faltantes"
    
    def cambiar_estado_bueno(self, request, queryset):
        """Acción para cambiar estado a Bueno"""
        updated = queryset.update(estado_bien='B')
        self.message_user(
            request,
            f'{updated} bienes cambiaron a estado "Bueno".'
        )
    cambiar_estado_bueno.short_description = "Cambiar estado a Bueno"


@admin.register(MovimientoBien)
class MovimientoBienAdmin(admin.ModelAdmin):
    list_display = [
        'bien',
        'oficina_origen',
        'oficina_destino',
        'motivo',
        'confirmado_badge',
        'fecha_movimiento',
        'created_by'
    ]
    list_filter = [
        'confirmado',
        'oficina_origen',
        'oficina_destino',
        'fecha_movimiento'
    ]
    search_fields = [
        'bien__codigo_patrimonial',
        'motivo',
        'observaciones'
    ]
    readonly_fields = [
        'fecha_movimiento',
        'fecha_confirmacion',
        'created_at',
        'updated_at',
        'created_by',
        'updated_by'
    ]
    ordering = ['-fecha_movimiento']
    
    def confirmado_badge(self, obj):
        """Muestra el estado de confirmación"""
        if obj.confirmado:
            return format_html(
                '<span style="color: green; font-weight: bold;">●</span> Confirmado'
            )
        else:
            return format_html(
                '<span style="color: orange; font-weight: bold;">●</span> Pendiente'
            )
    confirmado_badge.short_description = 'Estado'
    
    def save_model(self, request, obj, form, change):
        """Guarda el modelo con información del usuario"""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    actions = ['confirmar_movimientos']
    
    def confirmar_movimientos(self, request, queryset):
        """Acción para confirmar movimientos"""
        count = 0
        for movimiento in queryset.filter(confirmado=False):
            movimiento.confirmar_movimiento()
            count += 1
        
        self.message_user(
            request,
            f'{count} movimientos fueron confirmados exitosamente.'
        )
    confirmar_movimientos.short_description = "Confirmar movimientos seleccionados"


@admin.register(HistorialEstado)
class HistorialEstadoAdmin(admin.ModelAdmin):
    list_display = [
        'bien',
        'estado_anterior_badge',
        'estado_nuevo_badge',
        'fecha_cambio',
        'ubicacion_gps',
        'tiene_foto',
        'created_by'
    ]
    list_filter = [
        'estado_anterior',
        'estado_nuevo',
        'fecha_cambio'
    ]
    search_fields = [
        'bien__codigo_patrimonial',
        'observaciones'
    ]
    readonly_fields = [
        'fecha_cambio',
        'created_at',
        'updated_at',
        'created_by',
        'updated_by'
    ]
    ordering = ['-fecha_cambio']
    
    def estado_anterior_badge(self, obj):
        """Muestra el estado anterior con color"""
        colors = {
            'N': 'blue', 'B': 'green', 'R': 'orange',
            'M': 'red', 'E': 'purple', 'C': 'gray'
        }
        color = colors.get(obj.estado_anterior, 'black')
        return format_html(
            '<span style="color: {};">●</span> {}',
            color,
            obj.get_estado_anterior_display()
        )
    estado_anterior_badge.short_description = 'Estado Anterior'
    
    def estado_nuevo_badge(self, obj):
        """Muestra el estado nuevo con color"""
        colors = {
            'N': 'blue', 'B': 'green', 'R': 'orange',
            'M': 'red', 'E': 'purple', 'C': 'gray'
        }
        color = colors.get(obj.estado_nuevo, 'black')
        return format_html(
            '<span style="color: {};">●</span> {}',
            color,
            obj.get_estado_nuevo_display()
        )
    estado_nuevo_badge.short_description = 'Estado Nuevo'
    
    def tiene_foto(self, obj):
        """Indica si tiene foto"""
        if obj.foto:
            return format_html(
                '<span style="color: green;">●</span> Sí'
            )
        return format_html(
            '<span style="color: gray;">●</span> No'
        )
    tiene_foto.short_description = 'Foto'
    
    def save_model(self, request, obj, form, change):
        """Guarda el modelo con información del usuario"""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)