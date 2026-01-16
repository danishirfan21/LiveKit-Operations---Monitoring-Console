from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class ParticipantState(str, Enum):
    JOINING = "joining"
    JOINED = "joined"
    ACTIVE = "active"
    DISCONNECTED = "disconnected"


class ConnectionQuality(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    POOR = "poor"
    UNKNOWN = "unknown"


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    ACTIVE = "active"
    RESOLVED = "resolved"


class Participant(BaseModel):
    sid: str
    identity: str
    name: Optional[str] = None
    joined_at: datetime
    connection_quality: ConnectionQuality = ConnectionQuality.UNKNOWN
    is_publisher: bool = False
    tracks_published: int = 0


class Room(BaseModel):
    sid: str
    name: str
    created_at: datetime
    participant_count: int = 0
    max_participants: int = 0
    participants: list[Participant] = Field(default_factory=list)


class SystemMetrics(BaseModel):
    timestamp: datetime
    active_rooms: int = 0
    total_participants: int = 0
    join_rate: float = 0.0  # joins per minute
    leave_rate: float = 0.0  # leaves per minute
    disconnect_rate: float = 0.0  # disconnects per minute (unexpected)
    avg_room_duration_seconds: float = 0.0
    avg_connection_quality: float = 0.0  # 0-1 scale


class MetricsSnapshot(BaseModel):
    current: SystemMetrics
    history: list[SystemMetrics] = Field(default_factory=list)
    rooms: list[Room] = Field(default_factory=list)


class Alert(BaseModel):
    id: str
    severity: AlertSeverity
    status: AlertStatus = AlertStatus.ACTIVE
    title: str
    description: str
    room_name: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None


class WebSocketMessage(BaseModel):
    type: str
    data: Optional[dict] = None


class WebhookEvent(BaseModel):
    event: str
    room: Optional[dict] = None
    participant: Optional[dict] = None
    created_at: Optional[int] = None  # Unix timestamp
