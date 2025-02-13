"""URL mappings for the sudoku app."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from sudoku import views

router = DefaultRouter()
router.register("sudokus", views.SudokusViewSet)
router.register("tags", views.TagViewSet)

app_name = "sudoku"

urlpatterns = [
    path("", include(router.urls))
]
