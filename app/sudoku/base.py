"""Base module for Sudoku app."""

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .choices import DetectionStatusChoices, SudokuStatusChoices
from .models import Sudoku


def update_sudoku_status(sudoku: Sudoku, status: SudokuStatusChoices) -> None:
    """Updates the status of a Sudoku.

    Also sends status update via WebSocket.

    :param sudoku: Sudoku to update.
    :param status: new status for the Sudoku to update.
    """
    sudoku.status = status
    sudoku.save(update_fields=["status"])

    channel_layer = get_channel_layer()
    room_group_name = f"sudoku_status_{sudoku.id}"
    async_to_sync(channel_layer.group_send)(
        room_group_name,
        {
            "type": "status_update",
            "sudoku_id": str(sudoku.id),
            "status": status,
        },
    )


def update_sudoku_detection(status: DetectionStatusChoices) -> None:
    """Sends sudoku detection status update via WebSocket.

    :param status: current status for the Sudoku detection.
    """
    channel_layer = get_channel_layer()
    room_group_name = "sudoku_detection_status"
    async_to_sync(channel_layer.group_send)(
        room_group_name,
        {
            "type": "detection_status_update",
            "status": status,
        },
    )
