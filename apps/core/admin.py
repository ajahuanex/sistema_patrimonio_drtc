from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from .models import UserProfile, AuditLog, RecycleBin, RecycleBinConfig


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Perfil'
    fields = ('role', 'telefono', 'cargo', 'oficina', 'is_active')


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_role', 'get_is_active', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'profile__role', 'profile__is_active')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    
    def get_role(self, obj):
        if hasattr(obj, 'profile'):
            return obj.profile.get_role_display()
        return 'Sin perfil'
    get_role.short_description = 'Rol'
    
    def get_is_active(self, obj):
        if hasattr(obj, 'profile'):
            return obj.profile.is_active
        return False
    get_is_active.short_description = 'Activo'
    get_is_active.boolean = True


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'cargo', 'oficina', 'is_active', 'created_at')
    list_filter = ('role', 'is_active', 'oficina')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'cargo')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Información del Usuario', {
            'fields': ('user', 'role')
        }),
        ('Información Profesional', {
            'fields': ('cargo', 'telefono', 'oficina')
        }),
        ('Estado', {
            'fields': ('is_active',)
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'model_name', 'object_repr', 'timestamp', 'ip_address')
    list_filter = ('action', 'model_name', 'timestamp')
    search_fields = ('user__username', 'object_repr', 'ip_address')
    readonly_fields = ('user', 'action', 'model_name', 'object_id', 'object_repr', 
                      'changes', 'ip_address', 'user_agent', 'timestamp')
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Solo administradores pueden eliminar logs de auditoría
        return request.user.is_superuser or (
            hasattr(request.user, 'profile') and 
            request.user.profile.is_administrador
        )


@admin.register(RecycleBin)
class RecycleBinAdmin(admin.ModelAdmin):
    list_display = ('object_repr', 'module_name', 'deleted_by', 'deleted_at', 
                   'days_until_auto_delete_display', 'is_restored', 'restored_by')
    list_filter = ('module_name', 'deleted_at', 'restored_at', 'content_type')
    search_fields = ('object_repr', 'deleted_by__username', 'deletion_reason')
    readonly_fields = ('content_type', 'object_id', 'object_repr', 'module_name',
                      'deleted_at', 'deleted_by', 'deletion_reason', 'original_data',
                      'days_until_auto_delete_display', 'is_restored')
    date_hierarchy = 'deleted_at'
    
    fieldsets = (
        ('Información del Objeto', {
            'fields': ('content_type', 'object_id', 'object_repr', 'module_name')
        }),
        ('Eliminación', {
            'fields': ('deleted_at', 'deleted_by', 'deletion_reason')
        }),
        ('Restauración', {
            'fields': ('restored_at', 'restored_by')
        }),
        ('Eliminación Automática', {
            'fields': ('auto_delete_at', 'days_until_auto_delete_display')
        }),
        ('Datos Originales', {
            'fields': ('original_data',),
            'classes': ('collapse',)
        }),
    )
    
    def days_until_auto_delete_display(self, obj):
        days = obj.days_until_auto_delete
        if days is None:
            return "N/A (Restaurado)"
        elif days == 0:
            return format_html('<span style="color: red; font-weight: bold;">¡HOY!</span>')
        elif days <= 3:
            return format_html('<span style="color: red;">{} días</span>', days)
        elif days <= 7:
            return format_html('<span style="color: orange;">{} días</span>', days)
        else:
            return f"{days} días"
    days_until_auto_delete_display.short_description = 'Días hasta eliminación'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        # Solo permitir cambios en campos de restauración
        return True
    
    def has_delete_permission(self, request, obj=None):
        # Solo administradores pueden eliminar permanentemente
        return request.user.is_superuser or (
            hasattr(request.user, 'profile') and 
            request.user.profile.is_administrador
        )


@admin.register(RecycleBinConfig)
class RecycleBinConfigAdmin(admin.ModelAdmin):
    list_display = ('module_name', 'retention_days', 'auto_delete_enabled', 
                   'warning_days_before', 'can_restore_own', 'updated_at')
    list_filter = ('auto_delete_enabled', 'can_restore_own', 'can_restore_others')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Configuración del Módulo', {
            'fields': ('module_name',)
        }),
        ('Retención y Eliminación Automática', {
            'fields': ('retention_days', 'auto_delete_enabled')
        }),
        ('Notificaciones', {
            'fields': ('warning_days_before', 'final_warning_days_before')
        }),
        ('Permisos de Restauración', {
            'fields': ('can_restore_own', 'can_restore_others')
        }),
        ('Auditoría', {
            'fields': ('updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change or not obj.updated_by:
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)