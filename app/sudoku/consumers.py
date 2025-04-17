"""Sudoku status consumer."""

from typing import TypedDict

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from app.sudoku.models import Sudoku


class EventParams(TypedDict):
    """Event parameters."""

    type: str
    sudoku_id: str
    status: str


class SudokuStatusConsumer(AsyncJsonWebsocketConsumer):
    """Consumer for sudoku status updates."""

    async def connect(self) -> None:
        """Handles connection.

        This method is called when the WebSocket connection is established.
        """
        sudoku_id = self.scope["url_route"]["kwargs"]["sudoku_id"]
        self.room_group_name = f"sudoku_status_{sudoku_id}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code: int) -> None:
        """Handles disconnection.

        This method is called when the WebSocket connection is closed.
        """
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive_json(self, content, **kwargs) -> None:
        """Handles incoming JSON messages.

        Expected format: {"type": "get_status", "sudoku_id": "<uuid>"}
        Returned format: {"type": "status_update", "sudoku_id": "<uuid>", "status": "status"}
        """
        type_ = content.get("type")
        sudoku_id = content.get("sudoku_id")

        if type_ == "get_status" and sudoku_id:
            sudoku = sync_to_async(Sudoku.objects.get)(id=sudoku_id)
            status = sudoku.status

            await self.send_json(
                {
                    "type": "status_update",
                    "sudoku_id": sudoku_id,
                    "status": status,
                }
            )

    async def status_update(self, event: EventParams) -> None:
        """Handles sudoku status update events."""
        await self.send_json(
            {
                "type": "status_update",
                "sudoku_id": event["sudoku_id"],
                "status": event["status"],
            }
        )


__all__ = ["SudokuStatusConsumer"]
