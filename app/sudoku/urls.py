"""URL mappings for the sudoku app."""

from django.urls import include
from django.urls import path
from django.urls.resolvers import URLPattern
from django.urls.resolvers import URLResolver
from rest_framework.routers import DefaultRouter

from sudoku import views

router = DefaultRouter()
router.register("sudokus", views.SudokuViewSet)

app_name = "sudoku"

urlpatterns: list[URLResolver | URLPattern] = [path("", include(router.urls))]
