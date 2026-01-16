import logging
import uuid
from collections import deque
from datetime import datetime, timedelta
from typing import Optional

from ..config import settings
from ..models import Alert, AlertSeverity, AlertStatus, SystemMetrics, Room

logger = logging.getLogger(__name__)


class AlertEngine:
    """Detects and manages alerts based on metric thresholds."""

    def __init__(self):
        self._active_alerts: dict[str, Alert] = {}  # alert_id -> Alert
        self._resolved_alerts: deque[Alert] = deque(maxlen=100)  # Keep last 100 resolved
        self._alert_cooldowns: dict[str, datetime] = {}  # alert_type -> last_triggered
        self._cooldown_period = timedelta(minutes=5)

    def check_metrics(self, metrics: SystemMetrics) -> list[Alert]:
        """Check metrics against thresholds and generate alerts."""
        new_alerts = []

        # Check disconnect rate
        if metrics.total_participants > 0:
            disconnect_ratio = metrics.disconnect_rate / max(1, metrics.total_participants)
            if disconnect_ratio > settings.alert_disconnect_rate_threshold:
                alert = self._create_alert_if_not_cooldown(
                    alert_type="high_disconnect_rate",
                    severity=AlertSeverity.CRITICAL,
                    title="High Disconnect Rate",
                    description=f"Disconnect rate is {metrics.disconnect_rate:.1f}/min ({disconnect_ratio:.1%} of participants)",
                )
                if alert:
                    new_alerts.append(alert)

        # Check high participant count
        if metrics.total_participants > settings.alert_high_participant_threshold:
            alert = self._create_alert_if_not_cooldown(
                alert_type="high_participant_count",
                severity=AlertSeverity.WARNING,
                title="High Participant Count",
                description=f"System has {metrics.total_participants} active participants",
            )
            if alert:
                new_alerts.append(alert)

        # Check connection quality
        if metrics.avg_connection_quality < 0.5 and metrics.total_participants > 0:
            alert = self._create_alert_if_not_cooldown(
                alert_type="low_connection_quality",
                severity=AlertSeverity.WARNING,
                title="Low Average Connection Quality",
                description=f"Average connection quality is {metrics.avg_connection_quality:.0%}",
            )
            if alert:
                new_alerts.append(alert)

        # Check for stale rooms (very long duration)
        warning_duration = settings.alert_room_duration_warning_minutes * 60
        if metrics.avg_room_duration_seconds > warning_duration:
            alert = self._create_alert_if_not_cooldown(
                alert_type="long_room_duration",
                severity=AlertSeverity.INFO,
                title="Long Running Rooms Detected",
                description=f"Average room duration is {metrics.avg_room_duration_seconds / 60:.0f} minutes",
            )
            if alert:
                new_alerts.append(alert)

        return new_alerts

    def check_room(self, room: Room) -> list[Alert]:
        """Check individual room for alerts."""
        new_alerts = []
        now = datetime.utcnow()

        # Check room duration
        room_duration_minutes = (now - room.created_at).total_seconds() / 60
        if room_duration_minutes > settings.alert_room_duration_warning_minutes:
            alert = self._create_alert_if_not_cooldown(
                alert_type=f"room_long_duration_{room.sid}",
                severity=AlertSeverity.INFO,
                title=f"Room Running for {room_duration_minutes:.0f}+ Minutes",
                description=f"Room '{room.name}' has been active for {room_duration_minutes:.0f} minutes",
                room_name=room.name,
            )
            if alert:
                new_alerts.append(alert)

        return new_alerts

    def _create_alert_if_not_cooldown(
        self,
        alert_type: str,
        severity: AlertSeverity,
        title: str,
        description: str,
        room_name: Optional[str] = None,
    ) -> Optional[Alert]:
        """Create an alert if not in cooldown period."""
        now = datetime.utcnow()

        # Check cooldown
        if alert_type in self._alert_cooldowns:
            last_triggered = self._alert_cooldowns[alert_type]
            if now - last_triggered < self._cooldown_period:
                return None

        # Create alert
        alert = Alert(
            id=str(uuid.uuid4()),
            severity=severity,
            status=AlertStatus.ACTIVE,
            title=title,
            description=description,
            room_name=room_name,
            created_at=now,
        )

        self._active_alerts[alert.id] = alert
        self._alert_cooldowns[alert_type] = now
        logger.info(f"Alert created: {title}")

        return alert

    def resolve_alert(self, alert_id: str) -> Optional[Alert]:
        """Manually resolve an alert."""
        alert = self._active_alerts.pop(alert_id, None)
        if alert:
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.utcnow()
            self._resolved_alerts.append(alert)
            logger.info(f"Alert resolved: {alert.title}")
        return alert

    def auto_resolve_alerts(self, metrics: SystemMetrics) -> list[Alert]:
        """Automatically resolve alerts when conditions improve."""
        resolved = []

        for alert_id, alert in list(self._active_alerts.items()):
            should_resolve = False

            # Check if conditions have improved
            if "disconnect" in alert.title.lower():
                if metrics.total_participants == 0 or (
                    metrics.disconnect_rate / max(1, metrics.total_participants)
                    <= settings.alert_disconnect_rate_threshold * 0.5
                ):
                    should_resolve = True

            elif "participant count" in alert.title.lower():
                if metrics.total_participants <= settings.alert_high_participant_threshold * 0.8:
                    should_resolve = True

            elif "connection quality" in alert.title.lower():
                if metrics.avg_connection_quality >= 0.7:
                    should_resolve = True

            if should_resolve:
                resolved_alert = self.resolve_alert(alert_id)
                if resolved_alert:
                    resolved.append(resolved_alert)

        return resolved

    def get_active_alerts(self) -> list[Alert]:
        """Get all active alerts."""
        return list(self._active_alerts.values())

    def get_resolved_alerts(self) -> list[Alert]:
        """Get recently resolved alerts."""
        return list(self._resolved_alerts)

    def get_all_alerts(self) -> dict:
        """Get all alerts for API response."""
        return {
            "active": [a.model_dump(mode="json") for a in self.get_active_alerts()],
            "resolved": [a.model_dump(mode="json") for a in self.get_resolved_alerts()],
        }

    def clear(self) -> None:
        """Clear all alerts (useful for testing)."""
        self._active_alerts.clear()
        self._resolved_alerts.clear()
        self._alert_cooldowns.clear()
