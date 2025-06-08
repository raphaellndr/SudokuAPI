from django.contrib import admin

from .models import GameRecord


class GameRecordAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "sudoku",
        "score",
        "hints_used",
        "checks_used",
        "deletions",
        "time_taken",
        "won",
        "status",
    )
    list_filter = ("status", "won", "user")
    search_fields = ("user__email", "id")
    readonly_fields = ("id", "created_at", "updated_at")

    fieldsets = (
        (None, {"fields": ("id", "user", "sudoku", "status")}),
        (
            "Game Statistics",
            {"fields": ("score", "hints_used", "checks_used", "deletions", "time_taken", "won")},
        ),
        ("Game Metadata", {"fields": ("original_puzzle", "solution", "final_state")}),
        ("Timestamps", {"fields": ("started_at", "completed_at", "created_at", "updated_at")}),
    )


admin.site.register(GameRecord, GameRecordAdmin)
