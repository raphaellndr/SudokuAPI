"""Sudoku WebSocket routing."""

from django.urls import re_path

from .consumers import SudokuStatusConsumer

websocket_urlpatterns = [re_path(r"ws/sudoku/status/$", SudokuStatusConsumer.as_asgi())]
