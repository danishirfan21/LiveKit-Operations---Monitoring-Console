# LiveKit Operations & Monitoring Console

A production-style operations console for monitoring LiveKit real-time communication systems. The console provides real-time metrics, alerts, and drill-down capabilities for engineering/ops teams.

## Features

- **Real-time Dashboard**: Live metrics including active rooms, participants, join/leave rates
- **Time Series Charts**: Visual representation of system metrics over time
- **Room Drill-down**: Detailed view of individual rooms and participants
- **Alert System**: Threshold-based alerts for disconnect rates, participant counts, and more
- **WebSocket Updates**: Real-time data streaming to the frontend
- **Mock Mode**: Built-in synthetic data generation for demo/testing

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React + TS)                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  Dashboard  │  │ Room Detail │  │     Alerts Panel        │  │
│  │  - Metrics  │  │ - Participants│ │  - Connection failures │  │
│  │  - Charts   │  │ - Quality   │  │  - Disconnect rates     │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
│                           │                                      │
│                    WebSocket Client                              │
└───────────────────────────┼─────────────────────────────────────┘
                            │
┌───────────────────────────┼─────────────────────────────────────┐
│                    Backend (FastAPI)                             │
│  ┌────────────────┐  ┌─────────────┐  ┌─────────────────────┐   │
│  │ WebSocket Hub  │  │ Metrics     │  │  Alert Engine       │   │
│  │ - Broadcast    │  │ Aggregator  │  │  - Threshold checks │   │
│  │ - Client mgmt  │  │ - In-memory │  │  - Rate monitoring  │   │
│  └────────────────┘  └─────────────┘  └─────────────────────┘   │
│                           │                                      │
│                    LiveKit Integration                           │
│  ┌────────────────────────┴────────────────────────────────┐    │
│  │  Webhook Receiver  │  Server SDK (rooms/participants)   │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- npm or yarn

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run in mock mode (default)
python run.py
```

The backend will start at `http://localhost:8000`.

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will start at `http://localhost:5173`.

## Configuration

### Backend Environment Variables

Create a `.env` file in the `backend` directory:

```env
# LiveKit Configuration (optional - only needed for real LiveKit)
LIVEKIT_URL=wss://your-livekit-server.livekit.cloud
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret

# Application Settings
MOCK_MODE=true  # Set to false to connect to real LiveKit

# Alert Thresholds
ALERT_DISCONNECT_RATE_THRESHOLD=0.1
ALERT_HIGH_PARTICIPANT_THRESHOLD=100
ALERT_ROOM_DURATION_WARNING_MINUTES=120
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/metrics/current` | GET | Current system metrics |
| `/api/metrics/history` | GET | Time-series metrics history |
| `/api/rooms` | GET | List of active rooms |
| `/api/rooms/{room_name}` | GET | Room details with participants |
| `/api/alerts` | GET | Active and resolved alerts |
| `/api/alerts/{alert_id}/resolve` | POST | Manually resolve an alert |
| `/api/livekit/webhook` | POST | LiveKit webhook receiver |
| `/ws` | WebSocket | Real-time updates stream |

## WebSocket Protocol

The WebSocket connection streams real-time updates to the frontend:

```typescript
// Server -> Client messages
{ type: "metrics_update", data: SystemMetrics }
{ type: "room_update", data: { type: "room_started" | "room_finished", room: Room } }
{ type: "alert", data: Alert }
{ type: "heartbeat", data: { timestamp: string } }
```

## Metrics Tracked

| Metric | Description |
|--------|-------------|
| Active Rooms | Number of currently active rooms |
| Total Participants | Sum of participants across all rooms |
| Join Rate | Participants joining per minute |
| Leave Rate | Participants leaving normally per minute |
| Disconnect Rate | Unexpected disconnects per minute |
| Avg Room Duration | Average time rooms have been active |
| Avg Connection Quality | Average connection quality (0-100%) |

## Alert Types

- **High Disconnect Rate**: Triggered when disconnect rate exceeds threshold
- **High Participant Count**: Triggered when total participants exceed limit
- **Low Connection Quality**: Triggered when average quality drops below 50%
- **Long Running Rooms**: Informational alert for rooms exceeding duration threshold

## Project Structure

```
livekit-console/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry
│   │   ├── config.py            # Settings & env vars
│   │   ├── models.py            # Pydantic models
│   │   ├── metrics/
│   │   │   └── store.py         # In-memory metrics store
│   │   ├── livekit/
│   │   │   ├── client.py        # LiveKit Server SDK wrapper
│   │   │   └── webhooks.py      # Webhook event handlers
│   │   ├── alerts/
│   │   │   └── engine.py        # Alert detection & management
│   │   ├── websocket/
│   │   │   └── hub.py           # WebSocket connection manager
│   │   └── mock/
│   │       └── generator.py     # Synthetic data for demo mode
│   ├── requirements.txt
│   └── run.py
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard/       # Metrics grid, charts, health
│   │   │   ├── Rooms/           # Room list and details
│   │   │   ├── Alerts/          # Alerts panel
│   │   │   └── common/          # Reusable components
│   │   ├── hooks/               # React hooks (WebSocket, metrics)
│   │   ├── types/               # TypeScript definitions
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
└── README.md
```

## Scaling Considerations

For production deployments:

1. **Horizontal Scaling**: WebSocket connections can be distributed via Redis pub/sub
2. **Metric Retention**: Replace in-memory ring buffer with time-series DB (InfluxDB, TimescaleDB)
3. **Alert Persistence**: Add PostgreSQL for alert history
4. **Multi-region**: Deploy backend instances per region, aggregate in central dashboard

## Development

### Running Tests

```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

### Building for Production

```bash
# Frontend
cd frontend
npm run build
# Output in frontend/dist/

# Backend - use production ASGI server
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## License

MIT
