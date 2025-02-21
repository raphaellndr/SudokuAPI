"""Django admin configuration for core app."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from core import models


class UserAdmin(BaseUserAdmin):  # type: ignore
    """Custom user admin."""

    ordering = ["id"]

    # Displayed fields in the users list
    list_display = ["email", "name", "is_staff", "date_joined"]

    # Available fields in the user creation form
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "name",
                    "is_active",
                    "is_staff",
                ),
            },
        ),
    )

    # Available fields in the user edit form
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal Info"), {"fields": ("name",)}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    # Searching fields in the user list
    search_fields = ["email", "name"]

    # Fields to filter by user status and activity
    list_filter = ["is_staff", "is_superuser", "is_active"]

    # Fields to display in the user edit form
    readonly_fields = ["date_joined", "last_login"]


admin.site.register(models.User, UserAdmin)
admin.site.register(models.Sudoku)
