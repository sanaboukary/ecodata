from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Role, Permission, RolePermission, AuditLog, DataSourceAccess


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'created_at']
    search_fields = ['code', 'name']
    readonly_fields = ['created_at']


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'category']
    list_filter = ['category']
    search_fields = ['code', 'name']


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ['role', 'permission', 'granted_at']
    list_filter = ['role']
    search_fields = ['role__name', 'permission__name']
    readonly_fields = ['granted_at']


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'get_role_display', 'mfa_enabled', 'is_active', 'created_at']
    list_filter = ['role', 'mfa_enabled', 'is_active', 'is_staff']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'organization']
    readonly_fields = ['created_at', 'updated_at', 'last_login', 'api_token_created_at']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Informations supplémentaires', {
            'fields': ('organization', 'phone', 'role')
        }),
        ('Sécurité MFA', {
            'fields': ('mfa_enabled', 'mfa_secret', 'mfa_backup_codes')
        }),
        ('API Access', {
            'fields': ('api_token', 'api_token_created_at', 'api_rate_limit')
        }),
        ('Sécurité du compte', {
            'fields': ('last_login_ip', 'failed_login_attempts', 'account_locked_until')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'user', 'action', 'level', 'resource', 'ip_address']
    list_filter = ['action', 'level', 'timestamp']
    search_fields = ['user__username', 'resource', 'ip_address']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        return False  # Les logs d'audit ne peuvent pas être créés manuellement
    
    def has_change_permission(self, request, obj=None):
        return False  # Les logs d'audit ne peuvent pas être modifiés


@admin.register(DataSourceAccess)
class DataSourceAccessAdmin(admin.ModelAdmin):
    list_display = ['user', 'source', 'can_read', 'can_export', 'granted_at', 'granted_by']
    list_filter = ['source', 'can_read', 'can_export']
    search_fields = ['user__username', 'source']
    readonly_fields = ['granted_at']
