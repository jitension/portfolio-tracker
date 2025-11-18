"""
Django admin configuration for authentication app.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model

User = get_user_model()


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for User model."""
    
    list_display = [
        'email',
        'username',
        'first_name',
        'last_name',
        'is_active',
        'is_staff',
        'created_at',
        'last_login',
    ]
    
    list_filter = [
        'is_active',
        'is_staff',
        'is_superuser',
        'created_at',
    ]
    
    search_fields = [
        'email',
        'username',
        'first_name',
        'last_name',
    ]
    
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {
            'fields': ('email', 'username', 'password')
        }),
        ('Personal Info', {
            'fields': ('first_name', 'last_name', 'phone_number')
        }),
        ('Permissions', {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions',
            )
        }),
        ('Settings', {
            'fields': ('settings',),
            'classes': ('collapse',),
        }),
        ('Important Dates', {
            'fields': ('last_login', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'username',
                'password1',
                'password2',
                'first_name',
                'last_name',
                'is_active',
                'is_staff',
            ),
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'last_login']
    
    def get_readonly_fields(self, request, obj=None):
        """Make certain fields read-only for non-superusers."""
        readonly = list(self.readonly_fields)
        if not request.user.is_superuser and obj is not None:
            readonly.extend(['is_superuser', 'user_permissions', 'groups'])
        return readonly
