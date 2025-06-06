"""Django admin configuration for Sudoku models."""

from django.contrib import admin

from app.sudoku.models import Sudoku, SudokuSolution

admin.site.register(Sudoku)
admin.site.register(SudokuSolution)
