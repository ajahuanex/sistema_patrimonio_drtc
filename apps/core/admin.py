from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, AuditLog


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


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)