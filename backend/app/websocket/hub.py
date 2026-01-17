import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Set

from fastapi import WebSocket, WebSocketDisconnect

from ..config import settings
from ..models import WebSocketMessage

logger = logging.getLogger(__name__)


class WebSocketHub:
    """Manages WebSocket connections and broadcasts updates to all clients."""

    def __init__(self):
        self._clients: Set[WebSocket] = set()
        self._lock = asyncio.Lock()
        self._heartbeat_task: asyncio.Task | None = None

    async def connect(self, websocket: WebSocket) -> None:
        """Accept a new WebSocket connection."""
        await websocket.accept()
        async with self._lock:
            self._clients.add(websocket)
        logger.info(f"Client connected. Total clients: {len(self._clients)}")

    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection."""
        async with self._lock:
            self._clients.discard(websocket)
        logger.info(f"Client disconnected. Total clients: {len(self._clients)}")

    async def broadcast(self, message: WebSocketMessage) -> None:
        """Broadcast a message to all connected clients."""
        if not self._clients:
            return

        # Serialize message once for all clients
        data = message.model_dump_json()

        async with self._lock:
            disconnected = []
            for client in self._clients:
                try:
                    await client.send_text(data)
                except Exception as e:
                    logger.debug(f"Failed to send to client: {e}")
                    disconnected.append(client)

            # Clean up disconnected clients
            for client in disconnected:
                self._clients.discard(client)

    async def broadcast_dict(self, data: dict) -> None:
        """Broadcast a dictionary as a message."""
        message = WebSocketMessage(type=data.get("type", "update"), data=data)
        await self.broadcast(message)

    async def broadcast_metrics(self, metrics: dict) -> None:
        """Broadcast metrics update to all clients."""
        message = WebSocketMessage(type="metrics_update", data=metrics)
        await self.broadcast(message)

    async def broadcast_room_update(self, room_data: dict) -> None:
        """Broadcast room update to all clients."""
        message = WebSocketMessage(type="room_update", data=room_data)
        await self.broadcast(message)

    async def broadcast_alert(self, alert_data: dict) -> None:
        """Broadcast alert to all clients."""
        message = WebSocketMessage(type="alert", data=alert_data)
        await self.broadcast(message)

    async def send_heartbeat(self) -> None:
        """Send heartbeat to all clients."""
        message = WebSocketMessage(type="heartbeat", data={"timestamp": datetime.now(timezone.utc).isoformat()})
        await self.broadcast(message)

    async def start_heartbeat(self) -> None:
        """Start the heartbeat background task."""
        if self._heartbeat_task is None:
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    async def stop_heartbeat(self) -> None:
        """Stop the heartbeat background task."""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            self._heartbeat_task = None

    async def _heartbeat_loop(self) -> None:
        """Background loop for sending heartbeats."""
        while True:
            try:
                await asyncio.sleep(settings.websocket_heartbeat_interval)
                await self.send_heartbeat()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")

    @property
    def client_count(self) -> int:
        """Get the number of connected clients."""
        return len(self._clients)

    async def handle_client(self, websocket: WebSocket) -> None:
        """Handle a WebSocket client connection lifecycle."""
        await self.connect(websocket)
        try:
            while True:
                # Receive and echo or handle client messages
                data = await websocket.receive_text()
                try:
                    message = json.loads(data)
                    if message.get("type") == "ping":
                        await websocket.send_json({"type": "pong"})
                except json.JSONDecodeError:
                    pass
        except WebSocketDisconnect:
            pass
        finally:
            await self.disconnect(websocket)
