import asyncio
import logging
import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from ..models import Room, Participant, ConnectionQuality
from ..metrics import MetricsStore
from ..alerts import AlertEngine
from ..websocket import WebSocketHub

logger = logging.getLogger(__name__)

# Sample room name prefixes and suffixes for realistic names
ROOM_PREFIXES = ["meeting", "call", "session", "room", "conference", "standup", "interview", "webinar"]
ROOM_SUFFIXES = ["alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta"]

# Sample participant names
PARTICIPANT_NAMES = [
    "Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Henry",
    "Ivy", "Jack", "Kate", "Leo", "Mia", "Noah", "Olivia", "Peter",
    "Quinn", "Rachel", "Sam", "Tina", "Uma", "Victor", "Wendy", "Xavier"
]


class MockDataGenerator:
    """Generates synthetic LiveKit metrics data for demo/testing."""

    def __init__(
        self,
        metrics_store: MetricsStore,
        alert_engine: AlertEngine,
        websocket_hub: WebSocketHub,
    ):
        self._metrics_store = metrics_store
        self._alert_engine = alert_engine
        self._websocket_hub = websocket_hub
        self._running = False
        self._task: Optional[asyncio.Task] = None

        # Configuration
        self._target_rooms = 5  # Target number of active rooms
        self._participants_per_room = (2, 8)  # Min, max participants per room
        self._room_lifetime = (60, 300)  # Room lifetime in seconds (1-5 minutes)
        self._participant_churn_rate = 0.1  # Probability of participant change per tick
        self._quality_fluctuation_rate = 0.05  # Probability of quality change

    async def start(self) -> None:
        """Start the mock data generator."""
        if self._running:
            return

        self._running = True
        logger.info("Starting mock data generator")

        # Initialize with some rooms
        await self._initialize_rooms()

        # Start the background task
        self._task = asyncio.create_task(self._run_loop())

    async def stop(self) -> None:
        """Stop the mock data generator."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("Mock data generator stopped")

    async def _initialize_rooms(self) -> None:
        """Create initial set of rooms."""
        for _ in range(self._target_rooms):
            await self._create_room()

    async def _run_loop(self) -> None:
        """Main loop for generating mock data."""
        tick_interval = 1.0  # 1 second

        while self._running:
            try:
                await self._tick()
                await asyncio.sleep(tick_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in mock data loop: {e}")
                await asyncio.sleep(tick_interval)

    async def _tick(self) -> None:
        """Single tick of mock data generation."""
        rooms = self._metrics_store.get_all_rooms()
        now = datetime.now(timezone.utc)

        # Maybe end some old rooms
        for room in rooms:
            room_age = (now - room.created_at).total_seconds()
            max_lifetime = random.uniform(*self._room_lifetime)
            if room_age > max_lifetime:
                await self._end_room(room)

        # Ensure we have enough rooms
        current_room_count = len(self._metrics_store.get_all_rooms())
        while current_room_count < self._target_rooms:
            await self._create_room()
            current_room_count += 1

        # Participant churn
        for room in self._metrics_store.get_all_rooms():
            await self._update_room_participants(room)

        # Update connection quality
        for room in self._metrics_store.get_all_rooms():
            self._update_connection_quality(room)

        # Record metrics snapshot
        metrics = self._metrics_store.record_metrics_snapshot()

        # Check for alerts
        new_alerts = self._alert_engine.check_metrics(metrics)
        resolved_alerts = self._alert_engine.auto_resolve_alerts(metrics)

        # Broadcast updates
        await self._websocket_hub.broadcast_metrics(metrics.model_dump(mode="json"))

        for alert in new_alerts:
            await self._websocket_hub.broadcast_alert(alert.model_dump(mode="json"))

        for alert in resolved_alerts:
            await self._websocket_hub.broadcast_alert(alert.model_dump(mode="json"))

    async def _create_room(self) -> Room:
        """Create a new mock room with participants."""
        room_id = str(uuid.uuid4())
        room_name = f"{random.choice(ROOM_PREFIXES)}-{random.choice(ROOM_SUFFIXES)}-{room_id[:4]}"

        room = Room(
            sid=room_id,
            name=room_name,
            created_at=datetime.now(timezone.utc),
            participant_count=0,
            max_participants=0,
        )

        self._metrics_store.add_room(room)

        # Add initial participants
        num_participants = random.randint(*self._participants_per_room)
        for _ in range(num_participants):
            await self._add_participant(room)

        logger.debug(f"Created mock room: {room_name} with {num_participants} participants")

        await self._websocket_hub.broadcast_room_update({
            "type": "room_started",
            "room": room.model_dump(mode="json"),
        })

        return room

    async def _end_room(self, room: Room) -> None:
        """End a mock room."""
        self._metrics_store.remove_room(room.sid)
        logger.debug(f"Ended mock room: {room.name}")

        await self._websocket_hub.broadcast_room_update({
            "type": "room_finished",
            "room": room.model_dump(mode="json"),
        })

    async def _add_participant(self, room: Room) -> Participant:
        """Add a participant to a room."""
        participant_id = str(uuid.uuid4())
        name = random.choice(PARTICIPANT_NAMES)
        identity = f"{name.lower()}-{participant_id[:4]}"

        participant = Participant(
            sid=participant_id,
            identity=identity,
            name=name,
            joined_at=datetime.now(timezone.utc),
            connection_quality=random.choice([
                ConnectionQuality.EXCELLENT,
                ConnectionQuality.EXCELLENT,
                ConnectionQuality.GOOD,
                ConnectionQuality.GOOD,
                ConnectionQuality.GOOD,
                ConnectionQuality.POOR,
            ]),
            is_publisher=random.random() > 0.3,
            tracks_published=random.randint(0, 2) if random.random() > 0.3 else 0,
        )

        self._metrics_store.add_participant(room.sid, participant)
        return participant

    async def _remove_participant(self, room: Room, is_disconnect: bool = False) -> None:
        """Remove a random participant from a room."""
        if not room.participants:
            return

        participant = random.choice(room.participants)
        self._metrics_store.remove_participant(room.sid, participant.sid, is_disconnect)

    async def _update_room_participants(self, room: Room) -> None:
        """Update participants in a room (churn)."""
        if random.random() > self._participant_churn_rate:
            return

        # Decide action: add, remove normally, or disconnect
        action = random.choices(
            ["add", "leave", "disconnect"],
            weights=[0.4, 0.4, 0.2],
            k=1,
        )[0]

        min_participants, max_participants = self._participants_per_room

        if action == "add" and room.participant_count < max_participants:
            await self._add_participant(room)
        elif action == "leave" and room.participant_count > min_participants:
            await self._remove_participant(room, is_disconnect=False)
        elif action == "disconnect" and room.participant_count > min_participants:
            await self._remove_participant(room, is_disconnect=True)

    def _update_connection_quality(self, room: Room) -> None:
        """Randomly fluctuate connection quality for participants."""
        for participant in room.participants:
            if random.random() > self._quality_fluctuation_rate:
                continue

            # Fluctuate quality
            current_quality = participant.connection_quality
            if current_quality == ConnectionQuality.EXCELLENT:
                new_quality = random.choice([
                    ConnectionQuality.EXCELLENT,
                    ConnectionQuality.GOOD,
                ])
            elif current_quality == ConnectionQuality.GOOD:
                new_quality = random.choice([
                    ConnectionQuality.EXCELLENT,
                    ConnectionQuality.GOOD,
                    ConnectionQuality.POOR,
                ])
            else:
                new_quality = random.choice([
                    ConnectionQuality.GOOD,
                    ConnectionQuality.POOR,
                ])

            participant.connection_quality = new_quality

    def trigger_test_alert(self, severity: str = "warning") -> None:
        """Manually trigger a test alert."""
        from ..models import AlertSeverity, AlertStatus, Alert

        alert = Alert(
            id=str(uuid.uuid4()),
            severity=AlertSeverity(severity),
            status=AlertStatus.ACTIVE,
            title="Test Alert",
            description="This is a manually triggered test alert",
            created_at=datetime.now(timezone.utc),
        )

        self._alert_engine._active_alerts[alert.id] = alert
        asyncio.create_task(
            self._websocket_hub.broadcast_alert(alert.model_dump(mode="json"))
        )
