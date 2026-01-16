import asyncio
import logging
from datetime import datetime
from typing import Optional

from ..config import settings
from ..models import Room, Participant, ConnectionQuality

logger = logging.getLogger(__name__)


class LiveKitClient:
    """Wrapper for LiveKit Server SDK to poll room/participant data."""

    def __init__(self):
        self._api = None
        self._initialized = False

    async def initialize(self) -> bool:
        """Initialize the LiveKit API client."""
        if settings.mock_mode:
            logger.info("Running in mock mode - LiveKit client disabled")
            return False

        if not settings.livekit_api_key or not settings.livekit_api_secret:
            logger.warning("LiveKit credentials not configured")
            return False

        try:
            from livekit import api

            self._api = api.LiveKitAPI(
                settings.livekit_url,
                settings.livekit_api_key,
                settings.livekit_api_secret,
            )
            self._initialized = True
            logger.info("LiveKit client initialized successfully")
            return True
        except ImportError:
            logger.warning("livekit-api package not installed")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize LiveKit client: {e}")
            return False

    async def list_rooms(self) -> list[Room]:
        """Fetch all active rooms from LiveKit server."""
        if not self._initialized or not self._api:
            return []

        try:
            rooms_response = await self._api.room.list_rooms()
            rooms = []

            for lk_room in rooms_response.rooms:
                room = Room(
                    sid=lk_room.sid,
                    name=lk_room.name,
                    created_at=datetime.fromtimestamp(lk_room.creation_time),
                    participant_count=lk_room.num_participants,
                    max_participants=lk_room.max_participants or 0,
                )
                rooms.append(room)

            return rooms
        except Exception as e:
            logger.error(f"Failed to list rooms: {e}")
            return []

    async def list_participants(self, room_name: str) -> list[Participant]:
        """Fetch all participants in a specific room."""
        if not self._initialized or not self._api:
            return []

        try:
            response = await self._api.room.list_participants(room_name)
            participants = []

            for lk_participant in response.participants:
                quality = self._map_connection_quality(
                    getattr(lk_participant, "connection_quality", None)
                )
                participant = Participant(
                    sid=lk_participant.sid,
                    identity=lk_participant.identity,
                    name=lk_participant.name or lk_participant.identity,
                    joined_at=datetime.fromtimestamp(lk_participant.joined_at),
                    connection_quality=quality,
                    is_publisher=len(lk_participant.tracks) > 0,
                    tracks_published=len(lk_participant.tracks),
                )
                participants.append(participant)

            return participants
        except Exception as e:
            logger.error(f"Failed to list participants for room {room_name}: {e}")
            return []

    def _map_connection_quality(self, quality) -> ConnectionQuality:
        """Map LiveKit connection quality enum to our model."""
        if quality is None:
            return ConnectionQuality.UNKNOWN
        quality_str = str(quality).lower()
        if "excellent" in quality_str:
            return ConnectionQuality.EXCELLENT
        elif "good" in quality_str:
            return ConnectionQuality.GOOD
        elif "poor" in quality_str:
            return ConnectionQuality.POOR
        return ConnectionQuality.UNKNOWN

    async def sync_rooms(self, metrics_store) -> int:
        """Sync rooms from LiveKit server to metrics store.

        Returns the number of rooms synced.
        """
        if not self._initialized:
            return 0

        rooms = await self.list_rooms()
        synced = 0

        for room in rooms:
            participants = await self.list_participants(room.name)
            room.participants = participants
            room.participant_count = len(participants)
            metrics_store.add_room(room)
            synced += 1

        return synced

    async def close(self) -> None:
        """Close the client connection."""
        if self._api:
            try:
                await self._api.aclose()
            except Exception:
                pass
            self._api = None
            self._initialized = False
