import threading
from collections import deque
from datetime import datetime, timedelta, timezone
from typing import Optional

from ..config import settings
from ..models import (
    Room,
    Participant,
    SystemMetrics,
    MetricsSnapshot,
    ConnectionQuality,
)


class RingBuffer:
    """Thread-safe ring buffer for time-series metrics."""

    def __init__(self, max_size: int):
        self._buffer: deque[SystemMetrics] = deque(maxlen=max_size)
        self._lock = threading.RLock()

    def append(self, item: SystemMetrics) -> None:
        with self._lock:
            self._buffer.append(item)

    def get_all(self) -> list[SystemMetrics]:
        with self._lock:
            return list(self._buffer)

    def get_latest(self) -> Optional[SystemMetrics]:
        with self._lock:
            return self._buffer[-1] if self._buffer else None

    def __len__(self) -> int:
        with self._lock:
            return len(self._buffer)


class MetricsStore:
    """In-memory store for LiveKit metrics with time-series history."""

    def __init__(self):
        # Calculate buffer size based on retention and update interval
        buffer_size = int(
            settings.metrics_retention_seconds / settings.metrics_update_interval
        )
        self._metrics_history = RingBuffer(buffer_size)
        self._rooms: dict[str, Room] = {}  # room_sid -> Room
        self._lock = threading.RLock()

        # Event counters for rate calculations
        self._join_events: deque[datetime] = deque()
        self._leave_events: deque[datetime] = deque()
        self._disconnect_events: deque[datetime] = deque()
        self._rate_window = timedelta(minutes=1)

    def add_room(self, room: Room) -> None:
        with self._lock:
            self._rooms[room.sid] = room

    def remove_room(self, room_sid: str) -> Optional[Room]:
        with self._lock:
            return self._rooms.pop(room_sid, None)

    def get_room(self, room_sid: str) -> Optional[Room]:
        with self._lock:
            return self._rooms.get(room_sid)

    def get_room_by_name(self, room_name: str) -> Optional[Room]:
        with self._lock:
            for room in self._rooms.values():
                if room.name == room_name:
                    return room
            return None

    def get_all_rooms(self) -> list[Room]:
        with self._lock:
            return list(self._rooms.values())

    def add_participant(self, room_sid: str, participant: Participant) -> bool:
        with self._lock:
            room = self._rooms.get(room_sid)
            if not room:
                return False

            # Check if participant already exists
            existing = next(
                (p for p in room.participants if p.sid == participant.sid), None
            )
            if existing:
                # Update existing participant
                idx = room.participants.index(existing)
                room.participants[idx] = participant
            else:
                room.participants.append(participant)
                room.participant_count = len(room.participants)
                room.max_participants = max(
                    room.max_participants, room.participant_count
                )
                self._record_join()

            return True

    def remove_participant(
        self, room_sid: str, participant_sid: str, is_disconnect: bool = False
    ) -> bool:
        with self._lock:
            room = self._rooms.get(room_sid)
            if not room:
                return False

            room.participants = [
                p for p in room.participants if p.sid != participant_sid
            ]
            room.participant_count = len(room.participants)

            if is_disconnect:
                self._record_disconnect()
            else:
                self._record_leave()

            return True

    def _record_join(self) -> None:
        now = datetime.now(timezone.utc)
        self._join_events.append(now)
        self._cleanup_old_events()

    def _record_leave(self) -> None:
        now = datetime.now(timezone.utc)
        self._leave_events.append(now)
        self._cleanup_old_events()

    def _record_disconnect(self) -> None:
        now = datetime.now(timezone.utc)
        self._disconnect_events.append(now)
        self._cleanup_old_events()

    def _cleanup_old_events(self) -> None:
        cutoff = datetime.now(timezone.utc) - self._rate_window
        while self._join_events and self._join_events[0] < cutoff:
            self._join_events.popleft()
        while self._leave_events and self._leave_events[0] < cutoff:
            self._leave_events.popleft()
        while self._disconnect_events and self._disconnect_events[0] < cutoff:
            self._disconnect_events.popleft()

    def _calculate_rates(self) -> tuple[float, float, float]:
        """Calculate joins/leaves/disconnects per minute."""
        self._cleanup_old_events()
        return (
            float(len(self._join_events)),
            float(len(self._leave_events)),
            float(len(self._disconnect_events)),
        )

    def compute_current_metrics(self) -> SystemMetrics:
        with self._lock:
            now = datetime.now(timezone.utc)
            rooms = list(self._rooms.values())

            total_participants = sum(r.participant_count for r in rooms)
            join_rate, leave_rate, disconnect_rate = self._calculate_rates()

            # Calculate average room duration
            room_durations = []
            for room in rooms:
                duration = (now - room.created_at).total_seconds()
                room_durations.append(duration)
            avg_duration = (
                sum(room_durations) / len(room_durations) if room_durations else 0.0
            )

            # Calculate average connection quality
            quality_scores = []
            for room in rooms:
                for participant in room.participants:
                    if participant.connection_quality == ConnectionQuality.EXCELLENT:
                        quality_scores.append(1.0)
                    elif participant.connection_quality == ConnectionQuality.GOOD:
                        quality_scores.append(0.75)
                    elif participant.connection_quality == ConnectionQuality.POOR:
                        quality_scores.append(0.25)
            avg_quality = (
                sum(quality_scores) / len(quality_scores) if quality_scores else 1.0
            )

            return SystemMetrics(
                timestamp=now,
                active_rooms=len(rooms),
                total_participants=total_participants,
                join_rate=join_rate,
                leave_rate=leave_rate,
                disconnect_rate=disconnect_rate,
                avg_room_duration_seconds=avg_duration,
                avg_connection_quality=avg_quality,
            )

    def record_metrics_snapshot(self) -> SystemMetrics:
        """Compute and store current metrics."""
        metrics = self.compute_current_metrics()
        self._metrics_history.append(metrics)
        return metrics

    def get_snapshot(self) -> MetricsSnapshot:
        """Get complete metrics snapshot for API response."""
        current = self.compute_current_metrics()
        history = self._metrics_history.get_all()
        rooms = self.get_all_rooms()

        return MetricsSnapshot(current=current, history=history, rooms=rooms)

    def get_history(self) -> list[SystemMetrics]:
        """Get metrics history."""
        return self._metrics_history.get_all()

    def clear(self) -> None:
        """Clear all data (useful for testing)."""
        with self._lock:
            self._rooms.clear()
            self._join_events.clear()
            self._leave_events.clear()
            self._disconnect_events.clear()
