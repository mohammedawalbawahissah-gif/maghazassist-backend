from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Organisation, BusinessUnit, Department, User, DeviceToken


@admin.register(Organisation)
class OrganisationAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'email', 'is_active', 'created_at']
    search_fields = ['name', 'email']
    list_filter = ['is_active']


@admin.register(BusinessUnit)
class BusinessUnitAdmin(admin.ModelAdmin):
    list_display = ['name', 'organisation', 'unit_type', 'is_active']
    list_filter = ['unit_type', 'is_active']
    search_fields = ['name']


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'organisation', 'business_unit', 'is_active']
    search_fields = ['name']


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'get_full_name', 'role', 'organisation', 'is_active']
    list_filter = ['role', 'is_active', 'organisation']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['email']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone', 'avatar')}),
        ('Organisation', {'fields': ('role', 'organisation', 'department')}),
        ('Notifications', {'fields': ('notify_email', 'notify_sms', 'notify_push', 'notify_whatsapp')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates', {'fields': ('date_joined', 'last_login')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'role', 'organisation', 'password1', 'password2'),
        }),
    )


@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'device_type', 'is_active', 'last_used']
    list_filter = ['device_type', 'is_active']
