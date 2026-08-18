from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from apps.auth_manager.models import User


class UserAdmin(BaseUserAdmin):
    list_display = ("id", "email", "username", "display_name", "is_active", "is_staff", "is_superuser", "date_joined")
    list_filter = ("is_active", "is_staff", "is_superuser")
    search_fields = ("email", "username", "display_name")
    ordering = ("-date_joined",) if hasattr(User, "date_joined") else ("id",)

    fieldsets = (
        (None, {"fields": ("email", "username", "password")}),
        ("Personal Info", {"fields": ("display_name",)}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Metadata", {"fields": ("metadata",)}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "username", "display_name", "password1", "password2", "is_active", "is_staff"),
        }),
    )


admin.site.register(User, UserAdmin)