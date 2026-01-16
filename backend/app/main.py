import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, WebSocket, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .models import WebhookEvent, MetricsSnapshot
from .metrics import MetricsStore
from .alerts import AlertEngine
from .websocket import WebSocketHub
from .livekit import LiveKitClient, process_webhook_event
from .mock import MockDataGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global instances
metrics_store = MetricsStore()
alert_engine = AlertEngine()
websocket_hub = WebSocketHub()
livekit_client = LiveKitClient()
mock_generator: Optional[MockDataGenerator] = None

# Background tasks
background_tasks: list[asyncio.Task] = []


async def metrics_update_loop():
    """Background task to periodically update metrics."""
    while True:
        try:
            # Record metrics snapshot
            metrics = metrics_store.record_metrics_snapshot()

            # Check for alerts
            new_alerts = alert_engine.check_metrics(metrics)
            resolved_alerts = alert_engine.auto_resolve_alerts(metrics)

            # Broadcast to WebSocket clients (if not in mock mode, mock generator handles this)
            if not settings.mock_mode:
                await websocket_hub.broadcast_metrics(metrics.model_dump(mode="json"))

                for alert in new_alerts:
                    await websocket_hub.broadcast_alert(alert.model_dump(mode="json"))

                for alert in resolved_alerts:
                    await websocket_hub.broadcast_alert(alert.model_dump(mode="json"))

            await asyncio.sleep(settings.metrics_update_interval)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in metrics update loop: {e}")
            await asyncio.sleep(settings.metrics_update_interval)


async def sdk_poll_loop():
    """Background task to periodically sync with LiveKit SDK."""
    if settings.mock_mode:
        return

    while True:
        try:
            synced = await livekit_client.sync_rooms(metrics_store)
            if synced > 0:
                logger.debug(f"Synced {synced} rooms from LiveKit SDK")

            await asyncio.sleep(settings.sdk_poll_interval_seconds)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in SDK poll loop: {e}")
            await asyncio.sleep(settings.sdk_poll_interval_seconds)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global mock_generator

    logger.info("Starting LiveKit Operations Console...")
    logger.info(f"Mock mode: {settings.mock_mode}")

    # Initialize LiveKit client (if not mock mode)
    if not settings.mock_mode:
        await livekit_client.initialize()

    # Start WebSocket heartbeat
    await websocket_hub.start_heartbeat()

    # Start background tasks
    if settings.mock_mode:
        mock_generator = MockDataGenerator(
            metrics_store=metrics_store,
            alert_engine=alert_engine,
            websocket_hub=websocket_hub,
        )
        await mock_generator.start()
    else:
        # Start metrics update loop (only in non-mock mode)
        background_tasks.append(asyncio.create_task(metrics_update_loop()))
        # Start SDK polling loop
        background_tasks.append(asyncio.create_task(sdk_poll_loop()))

    logger.info("LiveKit Operations Console started successfully")

    yield

    # Cleanup
    logger.info("Shutting down LiveKit Operations Console...")

    # Stop mock generator
    if mock_generator:
        await mock_generator.stop()

    # Stop background tasks
    for task in background_tasks:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    # Stop WebSocket heartbeat
    await websocket_hub.stop_heartbeat()

    # Close LiveKit client
    await livekit_client.close()

    logger.info("LiveKit Operations Console stopped")


# Create FastAPI app
app = FastAPI(
    title="LiveKit Operations Console",
    description="Real-time monitoring dashboard for LiveKit infrastructure",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# API Endpoints


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "mock_mode": settings.mock_mode,
        "websocket_clients": websocket_hub.client_count,
    }


@app.get("/api/metrics/current")
async def get_current_metrics():
    """Get current system metrics snapshot."""
    metrics = metrics_store.compute_current_metrics()
    return metrics.model_dump(mode="json")


@app.get("/api/metrics/history")
async def get_metrics_history():
    """Get metrics history (time-series data)."""
    history = metrics_store.get_history()
    return [m.model_dump(mode="json") for m in history]


@app.get("/api/metrics/snapshot")
async def get_full_snapshot() -> MetricsSnapshot:
    """Get complete metrics snapshot including rooms."""
    return metrics_store.get_snapshot()


@app.get("/api/rooms")
async def get_rooms():
    """Get list of active rooms."""
    rooms = metrics_store.get_all_rooms()
    return [r.model_dump(mode="json") for r in rooms]


@app.get("/api/rooms/{room_name}")
async def get_room(room_name: str):
    """Get details of a specific room."""
    room = metrics_store.get_room_by_name(room_name)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room.model_dump(mode="json")


@app.get("/api/alerts")
async def get_alerts():
    """Get active and recent alerts."""
    return alert_engine.get_all_alerts()


@app.post("/api/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str):
    """Manually resolve an alert."""
    alert = alert_engine.resolve_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    # Broadcast resolution
    await websocket_hub.broadcast_alert(alert.model_dump(mode="json"))

    return alert.model_dump(mode="json")


@app.post("/api/livekit/webhook")
async def receive_webhook(request: Request):
    """Receive LiveKit webhook events."""
    try:
        body = await request.json()
        event = WebhookEvent(**body)

        # Process the webhook event
        result = process_webhook_event(event, metrics_store)

        # Broadcast if there's relevant data
        if result:
            await websocket_hub.broadcast_dict(result)

        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/test/alert")
async def trigger_test_alert(severity: str = "warning"):
    """Trigger a test alert (for testing purposes)."""
    if mock_generator:
        mock_generator.trigger_test_alert(severity)
        return {"status": "ok", "message": "Test alert triggered"}
    else:
        raise HTTPException(
            status_code=400,
            detail="Test alerts only available in mock mode",
        )


# WebSocket endpoint


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await websocket_hub.handle_client(websocket)
