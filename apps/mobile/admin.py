"""
Configuración del admin para la app móvil
"""
from django.contrib import admin
from .models import CambioOffline, SesionSync, ConflictoSync


@admin.register(CambioOffline)
class CambioOfflineAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'usuario', 'tipo_cambio', 'bien_codigo_patrimonial', 
        'estado_sync', 'timestamp_local', 'intentos_sync'
    ]
    list_filter = [
        'tipo_cambio', 'estado_sync', 'timestamp_local', 'conflicto_resuelto'
    ]
    search_fields = [
        'usuario__username', 'bien_codigo_patrimonial', 'bien_qr_code', 'dispositivo_id'
    ]
    readonly_fields = [
        'timestamp_servidor', 'created_at', 'updated_at', 'ultimo_intento'
    ]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('usuario', 'tipo_cambio', 'timestamp_local', 'timestamp_servidor')
        }),
        ('Identificación del Bien', {
            'fields': ('bien_codigo_patrimonial', 'bien_qr_code')
        }),
        ('Datos del Cambio', {
            'fields': ('datos_cambio',),
            'classes': ('collapse',)
        }),
        ('Estado de Sincronización', {
            'fields': ('estado_sync', 'intentos_sync', 'ultimo_intento', 'mensaje_error')
        }),
        ('Metadatos Móviles', {
            'fields': ('dispositivo_id', 'ubicacion_gps')
        }),
        ('Resolución de Conflictos', {
            'fields': ('conflicto_resuelto', 'resuelto_por', 'fecha_resolucion')
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if obj:  # Editando objeto existente
            readonly.extend(['usuario', 'tipo_cambio', 'timestamp_local', 'datos_cambio'])
        return readonly


@admin.register(SesionSync)
class SesionSyncAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'usuario', 'dispositivo_id', 'inicio_sync', 'fin_sync',
        'cambios_pendientes', 'cambios_exitosos', 'cambios_con_error', 'completada'
    ]
    list_filter = ['completada', 'inicio_sync', 'fin_sync']
    search_fields = ['usuario__username', 'dispositivo_id']
    readonly_fields = ['inicio_sync', 'fin_sync']
    
    fieldsets = (
        ('Información de la Sesión', {
            'fields': ('usuario', 'dispositivo_id', 'inicio_sync', 'fin_sync', 'completada')
        }),
        ('Estadísticas', {
            'fields': (
                'cambios_pendientes', 'cambios_procesados', 'cambios_exitosos',
                'cambios_con_error', 'cambios_con_conflicto'
            )
        }),
        ('Resultado', {
            'fields': ('mensaje_resultado',)
        }),
    )


@admin.register(ConflictoSync)
class ConflictoSyncAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'cambio_offline', 'tipo_conflicto', 'resuelto', 
        'resolucion_elegida', 'created_at'
    ]
    list_filter = ['tipo_conflicto', 'resuelto', 'resolucion_elegida', 'created_at']
    search_fields = [
        'cambio_offline__bien_codigo_patrimonial', 
        'cambio_offline__usuario__username'
    ]
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Información del Conflicto', {
            'fields': ('cambio_offline', 'tipo_conflicto', 'created_at')
        }),
        ('Datos del Conflicto', {
            'fields': ('datos_servidor', 'datos_cliente'),
            'classes': ('collapse',)
        }),
        ('Resolución', {
            'fields': ('resuelto', 'resolucion_elegida')
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if obj:  # Editando objeto existente
            readonly.extend(['cambio_offline', 'tipo_conflicto', 'datos_servidor', 'datos_cliente'])
        return readonly