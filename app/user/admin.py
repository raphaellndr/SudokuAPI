"""Django admin configuration for user app."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from app.user.models import User, UserStats


class UserStatsInline(admin.StackedInline):
    """Inline for UserStats in User admin."""

    model = UserStats
    can_delete = False
    verbose_name_plural = "Statistics"
    readonly_fields = ("created_at", "updated_at")


class UserAdmin(BaseUserAdmin):  # type: ignore
    """Custom user admin."""

    ordering = ["-created_at"]
    inlines = (UserStatsInline,)

    # Displayed fields in the users list
    list_display = ["email", "username", "is_staff", "is_active", "created_at", "updated_at"]

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
