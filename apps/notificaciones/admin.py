"""
Configuración del admin para notificaciones
"""
from django.contrib import admin
from .models import (
    TipoNotificacion, ConfiguracionNotificacion, Notificacion,
    AlertaMantenimiento, AlertaDepreciacion, HistorialNotificacion
)


@admin.register(TipoNotificacion)
class TipoNotificacionAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'activo', 'enviar_email', 'created_at']
    list_filter = ['activo', 'enviar_email']
    search_fields = ['codigo', 'nombre']
    readonly_fields = ['created_at']


@admin.register(ConfiguracionNotificacion)
class ConfiguracionNotificacionAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'tipo_notificacion', 'activa', 'enviar_email', 'frecuencia_dias']
    list_filter = ['activa', 'enviar_email', 'tipo_notificacion']
    search_fields = ['usuario__username', 'tipo_notificacion__nombre']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'usuario', 'tipo_notificacion', 'prioridad', 'estado', 'fecha_programada', 'created_at']
    list_filter = ['estado', 'prioridad', 'tipo_notificacion', 'fecha_programada']
    search_fields = ['titulo', 'mensaje', 'usuario__username']
    readonly_fields = ['created_at', 'updated_at', 'fecha_enviada', 'fecha_leida']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('usuario', 'tipo_notificacion', 'titulo', 'mensaje', 'prioridad')
        }),
        ('Estado y Fechas', {
            'fields': ('estado', 'fecha_programada', 'fecha_enviada', 'fecha_leida', 'fecha_expiracion')
        }),
        ('Datos Adicionales', {
            'fields': ('datos_contexto', 'url_accion'),
            'classes': ('collapse',)
        }),
        ('Control de Envío', {
            'fields': ('intentos_envio', 'ultimo_error'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['marcar_como_leida', 'reenviar_notificacion']
    
    def marcar_como_leida(self, request, queryset):
        for notificacion in queryset:
            notificacion.marcar_como_leida()
        self.message_user(request, f"{queryset.count()} notificaciones marcadas como leídas.")
    marcar_como_leida.short_description = "Marcar como leídas"
    
    def reenviar_notificacion(self, request, queryset):
        from .tasks import enviar_notificacion_email
        count = 0
        for notificacion in queryset.filter(estado__in=['PENDIENTE', 'ERROR']):
            enviar_notificacion_email.delay(notificacion.id)
            count += 1
        self.message_user(request, f"{count} notificaciones programadas para reenvío.")
    reenviar_notificacion.short_description = "Reenviar notificaciones"


@admin.register(AlertaMantenimiento)
class AlertaMantenimientoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo_bien', 'dias_anticipacion', 'frecuencia_meses', 'activa', 'created_at']
    list_filter = ['activa', 'tipo_bien']
    search_fields = ['nombre', 'descripcion']
    filter_horizontal = ['usuarios_notificar']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(AlertaDepreciacion)
class AlertaDepreciacionAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'meses_anticipacion', 'vida_util_anos', 'activa', 'created_at']
    list_filter = ['activa', 'vida_util_anos']
    search_fields = ['nombre', 'descripcion']
    filter_horizontal = ['usuarios_notificar']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(HistorialNotificacion)
class HistorialNotificacionAdmin(admin.ModelAdmin):
    list_display = ['notificacion', 'accion', 'timestamp']
    list_filter = ['accion', 'timestamp']
    search_fields = ['notificacion__titulo', 'detalles']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'