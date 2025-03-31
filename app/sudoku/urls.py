"""URL mappings for the sudoku app."""

from typing import Final

from django.urls import include, path
from django.urls.resolvers import URLPattern, URLResolver
from rest_framework.routers import DefaultRouter

from .views import SudokuViewSet

router = DefaultRouter()
router.register("", SudokuViewSet)

app_name: Final[str] = "sudokus"

urlpatterns: list[URLResolver | URLPattern] = [
    path("", include(router.urls)),
]
