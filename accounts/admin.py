from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import AuthorizedHospitalCredential, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Hospital Information', {'fields': ('role',)}),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Hospital Information', {'fields': ('role',)}),
    )

    list_display = (
        'username',
        'email',
        'role',
        'is_active',
        'is_staff',
    )


@admin.register(AuthorizedHospitalCredential)
class AuthorizedHospitalCredentialAdmin(admin.ModelAdmin):
    list_display = (
        'credential_code',
        'credential_type',
        'is_active',
        'redeemed_by',
        'redeemed_at',
        'created_at',
    )
    list_filter = ('credential_type', 'is_active')
    search_fields = ('credential_code',)
    ordering = ('credential_type', 'credential_code')
    readonly_fields = ('created_at', 'redeemed_by', 'redeemed_at')
