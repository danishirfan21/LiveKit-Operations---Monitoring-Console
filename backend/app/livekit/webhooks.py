import logging
from datetime import datetime
from typing import Optional

from ..models import Room, Participant, ConnectionQuality, WebhookEvent
from ..metrics import MetricsStore

logger = logging.getLogger(__name__)


def process_webhook_event(
    event: WebhookEvent, metrics_store: MetricsStore
) -> Optional[dict]:
    """Process a LiveKit webhook event and update metrics store.

    Returns event data for WebSocket broadcast if applicable.
    """
    event_type = event.event
    logger.info(f"Processing webhook event: {event_type}")

    if event_type == "room_started":
        return _handle_room_started(event, metrics_store)
    elif event_type == "room_finished":
        return _handle_room_finished(event, metrics_store)
    elif event_type == "participant_joined":
        return _handle_participant_joined(event, metrics_store)
    elif event_type == "participant_left":
        return _handle_participant_left(event, metrics_store)
    elif event_type == "track_published":
        return _handle_track_published(event, metrics_store)
    elif event_type == "track_unpublished":
        return _handle_track_unpublished(event, metrics_store)
    else:
        logger.debug(f"Unhandled webhook event type: {event_type}")
        return None


def _handle_room_started(
    event: WebhookEvent, metrics_store: MetricsStore
) -> Optional[dict]:
    """Handle room_started event."""
    if not event.room:
        return None

    room_data = event.room
    created_at = datetime.fromtimestamp(
        event.created_at or room_data.get("creation_time", datetime.utcnow().timestamp())
    )

    room = Room(
        sid=room_data.get("sid", ""),
        name=room_data.get("name", ""),
        created_at=created_at,
        participant_count=0,
        max_participants=0,
    )

    metrics_store.add_room(room)
    logger.info(f"Room started: {room.name} ({room.sid})")

    return {"type": "room_started", "room": room.model_dump(mode="json")}


def _handle_room_finished(
    event: WebhookEvent, metrics_store: MetricsStore
) -> Optional[dict]:
    """Handle room_finished event."""
    if not event.room:
        return None

    room_sid = event.room.get("sid", "")
    room = metrics_store.remove_room(room_sid)

    if room:
        logger.info(f"Room finished: {room.name} ({room.sid})")
        return {"type": "room_finished", "room": room.model_dump(mode="json")}

    return None


def _handle_participant_joined(
    event: WebhookEvent, metrics_store: MetricsStore
) -> Optional[dict]:
    """Handle participant_joined event."""
    if not event.room or not event.participant:
        return None

    room_sid = event.room.get("sid", "")
    participant_data = event.participant

    joined_at = datetime.fromtimestamp(
        participant_data.get("joined_at", datetime.utcnow().timestamp())
    )

    participant = Participant(
        sid=participant_data.get("sid", ""),
        identity=participant_data.get("identity", ""),
        name=participant_data.get("name") or participant_data.get("identity", ""),
        joined_at=joined_at,
        connection_quality=ConnectionQuality.UNKNOWN,
        is_publisher=False,
        tracks_published=0,
    )

    if metrics_store.add_participant(room_sid, participant):
        logger.info(
            f"Participant joined: {participant.identity} in room {event.room.get('name', room_sid)}"
        )
        return {
            "type": "participant_joined",
            "room_sid": room_sid,
            "participant": participant.model_dump(mode="json"),
        }

    return None


def _handle_participant_left(
    event: WebhookEvent, metrics_store: MetricsStore
) -> Optional[dict]:
    """Handle participant_left event."""
    if not event.room or not event.participant:
        return None

    room_sid = event.room.get("sid", "")
    participant_sid = event.participant.get("sid", "")
    participant_identity = event.participant.get("identity", "")

    # Check if this was a disconnect (unexpected leave)
    # LiveKit provides a "state" field - if it's not "ACTIVE" it might be a disconnect
    state = event.participant.get("state", "")
    is_disconnect = state in ("DISCONNECTED", "disconnected")

    if metrics_store.remove_participant(room_sid, participant_sid, is_disconnect):
        logger.info(
            f"Participant left: {participant_identity} from room {event.room.get('name', room_sid)} "
            f"(disconnect: {is_disconnect})"
        )
        return {
            "type": "participant_left",
            "room_sid": room_sid,
            "participant_sid": participant_sid,
            "is_disconnect": is_disconnect,
        }

    return None


def _handle_track_published(
    event: WebhookEvent, metrics_store: MetricsStore
) -> Optional[dict]:
    """Handle track_published event."""
    if not event.room or not event.participant:
        return None

    room_sid = event.room.get("sid", "")
    room = metrics_store.get_room(room_sid)
    if not room:
        return None

    participant_sid = event.participant.get("sid", "")
    for participant in room.participants:
        if participant.sid == participant_sid:
            participant.is_publisher = True
            participant.tracks_published += 1
            break

    return None


def _handle_track_unpublished(
    event: WebhookEvent, metrics_store: MetricsStore
) -> Optional[dict]:
    """Handle track_unpublished event."""
    if not event.room or not event.participant:
        return None

    room_sid = event.room.get("sid", "")
    room = metrics_store.get_room(room_sid)
    if not room:
        return None

    participant_sid = event.participant.get("sid", "")
    for participant in room.participants:
        if participant.sid == participant_sid:
            participant.tracks_published = max(0, participant.tracks_published - 1)
            if participant.tracks_published == 0:
                participant.is_publisher = False
            break

    return None
