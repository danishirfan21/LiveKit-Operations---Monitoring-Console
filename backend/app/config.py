import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LiveKit Configuration
    livekit_url: str = "wss://your-livekit-server.livekit.cloud"
    livekit_api_key: str = ""
    livekit_api_secret: str = ""

    # Application Settings
    mock_mode: bool = True  # Enable mock data generation by default
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Metrics Settings
    metrics_retention_seconds: int = 300  # 5 minutes
    metrics_update_interval: float = 1.0  # 1 second

    # Alert Thresholds
    alert_disconnect_rate_threshold: float = 0.1  # 10% disconnect rate
    alert_high_participant_threshold: int = 100
    alert_room_duration_warning_minutes: int = 120  # 2 hours

    # WebSocket Settings
    websocket_heartbeat_interval: float = 30.0

    # SDK Polling Interval (fallback for webhooks)
    sdk_poll_interval_seconds: int = 30

    class Config:
        env_file = ".env"
        env_prefix = ""
        case_sensitive = False


settings = Settings()
