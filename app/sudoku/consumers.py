"""Sudoku status consumer."""

from uuid import UUID

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from user.models import User

from sudoku.choices import SudokuStatusChoices
from sudoku.models import Sudoku


class SudokuStatusConsumer(AsyncJsonWebsocketConsumer):
    """Consumer for sudoku status updates."""

    async def connect(self) -> None:
        """Handles connection.

        This method is called when the WebSocket connection is established.
        """
        print("Connecting to websocket...")

        user: User = self.scope["user"]
        if not user.is_authenticated:
            await self.close()
            return

        # Add user to a group for receiving sudoku status updates
        await self.channel_layer.group_add(
            f"sudoku_status_{user.id}",
            self.channel_name,
        )
        await self.accept()

    async def disconnect(self, close_code: int) -> None:
        """Handles disconnection.

        This method is called when the WebSocket connection is closed.
        """
        print("Disconnecting from websocket...")

        user: User = self.scope["user"]

        # Remove user from the group for receiving sudoku status updates
        await self.channel_layer.group_discard(
            f"sudoku_status_{user.id}",
            self.channel_name,
        )

    async def receive_json(self, content, **kwargs):
        """Handles incoming JSON messages.

        Expected format: {"action": "get_status", "sudoku_id": "<uuid>"}
        Returned format: {"type": "status_update", "sudoku_id": "<uuid>", "status": "status"}
        """
        action = content.get("action")
        sudoku_id = content.get("sudoku_id")

        if action == "get_status" and sudoku_id:
            try:
                print("Sending status update")
                status = await self.get_sudoku_status(sudoku_id)
                await self.send_json(
                    {
                        "type": "status_update",
                        "sudoku_id": sudoku_id,
                        "status": status,
                    }
                )
            except Exception as e:
                print(f"Error getting sudoku status: {e!s}")
                await self.send_json({"type": "error", "message": str(e)})

    @sync_to_async
    def get_sudoku_status(self, sudoku_id: UUID) -> SudokuStatusChoices:
        """Gets the sudoku status.

        :param sudoku_id: id of the sudoku to get the status from.
        :returns: The status of the sudoku.
        """
        try:
            sudoku = Sudoku.objects.get(id=sudoku_id)
            return sudoku.status
        except Sudoku.DoesNotExist:
            raise ValueError(f"No sudoku found with id {sudoku_id}")


__all__ = ["SudokuStatusConsumer"]
