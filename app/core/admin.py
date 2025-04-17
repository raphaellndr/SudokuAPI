"""Django admin configuration for core app."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from app.sudoku.models import Sudoku, SudokuSolution
from app.user.models import User


class UserAdmin(BaseUserAdmin):  # type: ignore
    """Custom user admin."""

    ordering = ["id"]

    # Displayed fields in the users list
    list_display = ["email", "username", "is_staff"]

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
                    "username",
                    "is_active",
                    "is_staff",
                ),
            },
        ),
    )

    # Available fields in the user edit form
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal Info"), {"fields": ("username",)}),
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
        (_("Important dates"), {"fields": ("created_at", "updated_at", "last_login")}),
    )

    # Searching fields in the user list
    search_fields = ["email", "username"]

    # Fields to filter by user status and activity
    list_filter = ["is_staff", "is_superuser", "is_active"]

    # Fields to display in the user edit form
    readonly_fields = ["created_at", "updated_at", "last_login"]


admin.site.register(User, UserAdmin)
admin.site.register(Sudoku)
admin.site.register(SudokuSolution)
