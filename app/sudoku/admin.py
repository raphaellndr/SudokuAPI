"""Django admin configuration for Sudoku models."""

from django.contrib import admin

from app.sudoku.models import Sudoku, SudokuSolution


@admin.register(Sudoku)
class SudokuAdmin(admin.ModelAdmin):
    """Admin configuration for `Sudoku`."""

    list_display = ("id", "title", "user", "difficulty", "status", "created_at")
    list_filter = ("status", "difficulty")
    search_fields = ("id", "title", "user__email")
    ordering = ("-created_at",)
    raw_id_fields = ("user",)


@admin.register(SudokuSolution)
class SudokuSolutionAdmin(admin.ModelAdmin):
    """Admin configuration for `SudokuSolution`."""

    list_display = ("id", "sudoku", "created_at")
    search_fields = ("id", "sudoku__id")
    raw_id_fields = ("sudoku",)
