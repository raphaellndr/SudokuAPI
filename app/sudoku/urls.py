"""URL mappings for the sudoku app."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from sudoku import views

router = DefaultRouter()
router.register("sudokus", views.SudokuViewSet)

app_name = "sudoku"

urlpatterns = [
    path("", include(router.urls))
]
