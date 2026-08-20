"""
WebSocket connection manager for real-time features.
Handles broadcasting leaderboard updates, timer sync, and game events.
"""

import json
from typing import Dict, List, Set, Optional
from fastapi import WebSocket
from datetime import datetime


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""

    def __init__(self):
        # room_id -> set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # user_id -> WebSocket connection (for targeted messages)
        self.user_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, room_id: str, user_id: Optional[str] = None):
        """Accept a WebSocket connection and add to a room."""
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = set()
        self.active_connections[room_id].add(websocket)
        if user_id:
            self.user_connections[user_id] = websocket

    def disconnect(self, websocket: WebSocket, room_id: str, user_id: Optional[str] = None):
        """Remove a WebSocket connection from a room."""
        if room_id in self.active_connections:
            self.active_connections[room_id].discard(websocket)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]
        if user_id and user_id in self.user_connections:
            del self.user_connections[user_id]

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific connection."""
        await websocket.send_json(message)

    async def send_to_user(self, message: dict, user_id: str):
        """Send a message to a specific user."""
        if user_id in self.user_connections:
            try:
                await self.user_connections[user_id].send_json(message)
            except Exception:
                pass

    async def broadcast_to_room(self, message: dict, room_id: str, exclude: Optional[WebSocket] = None):
        """Broadcast a message to all connections in a room."""
        if room_id in self.active_connections:
            dead_connections = []
            for connection in self.active_connections[room_id]:
                if connection != exclude:
                    try:
                        await connection.send_json(message)
                    except Exception:
                        dead_connections.append(connection)
            # Clean up dead connections
            for dead in dead_connections:
                self.active_connections[room_id].discard(dead)

    async def broadcast_leaderboard(self, round_id: str, leaderboard_data: list):
        """Broadcast leaderboard update to all connections in a round's room."""
        message = {
            "type": "leaderboard_update",
            "data": leaderboard_data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await self.broadcast_to_room(message, f"round_{round_id}")

    async def broadcast_timer(self, round_id: str, remaining_seconds: int):
        """Broadcast timer update."""
        message = {
            "type": "timer_update",
            "data": {"remaining_seconds": remaining_seconds},
            "timestamp": datetime.utcnow().isoformat(),
        }
        await self.broadcast_to_room(message, f"round_{round_id}")

    async def broadcast_round_event(self, round_id: str, event: str, data: dict = None):
        """Broadcast a round event (start, pause, end, etc.)."""
        message = {
            "type": f"round_{event}",
            "data": data or {},
            "timestamp": datetime.utcnow().isoformat(),
        }
        await self.broadcast_to_room(message, f"round_{round_id}")

    async def broadcast_notification(self, room_id: str, notification: str, level: str = "info"):
        """Broadcast a notification to a room."""
        message = {
            "type": "notification",
            "data": {"message": notification, "level": level},
            "timestamp": datetime.utcnow().isoformat(),
        }
        await self.broadcast_to_room(message, room_id)

    def get_room_count(self, room_id: str) -> int:
        """Get the number of connections in a room."""
        return len(self.active_connections.get(room_id, set()))


# Global connection manager instance
manager = ConnectionManager()
