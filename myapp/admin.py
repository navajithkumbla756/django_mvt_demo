# myapp/admin.py
from django.contrib import admin
from .models import CustomUser, Employer, Candidate, Job, Application

class CustomUserAdmin(admin.ModelAdmin):
    """Establishes data columns, list grids, and lookup filters inside the administration panel."""
    
    list_display = ('email', 'name', 'role', 'is_verified', 'is_active', 'is_staff', 'created_at')
    list_filter = ('role', 'is_verified', 'is_active', 'is_staff')
    search_fields = ('email', 'name', 'phone')
    ordering = ('-created_at',)

    fieldsets = (
        ('Authentication Context', {'fields': ('email', 'password')}),
        ('Profile Context Attributes', {'fields': ('name', 'phone', 'role')}),
        ('Permissions & States Controls', {'fields': ('is_active', 'is_verified', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('System Lifecycles Logs', {'fields': ('created_at', 'updated_at')}),
    )
    readonly_fields = ('created_at', 'updated_at')

# Clean registration maps
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Employer)
admin.site.register(Candidate)
admin.site.register(Job)
admin.site.register(Application)