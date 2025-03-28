"""Sudoku WebSocket routing."""

from django.urls import re_path

from .consumers import SudokuStatusConsumer

websocket_urlpatterns = [
    re_path(r"ws/sudokus/(?P<sudoku_id>[0-9a-fA-F-]+)/status/$", SudokuStatusConsumer.as_asgi())
]
