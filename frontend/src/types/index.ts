// Connection quality levels
export type ConnectionQuality = 'excellent' | 'good' | 'poor' | 'unknown';

// Alert types
export type AlertSeverity = 'info' | 'warning' | 'critical';
export type AlertStatus = 'active' | 'resolved';

// Participant in a room
export interface Participant {
  sid: string;
  identity: string;
  name: string | null;
  joined_at: string;
  connection_quality: ConnectionQuality;
  is_publisher: boolean;
  tracks_published: number;
}

// Room information
export interface Room {
  sid: string;
  name: string;
  created_at: string;
  participant_count: number;
  max_participants: number;
  participants: Participant[];
}

// System metrics at a point in time
export interface SystemMetrics {
  timestamp: string;
  active_rooms: number;
  total_participants: number;
  join_rate: number;
  leave_rate: number;
  disconnect_rate: number;
  avg_room_duration_seconds: number;
  avg_connection_quality: number;
}

// Full metrics snapshot
export interface MetricsSnapshot {
  current: SystemMetrics;
  history: SystemMetrics[];
  rooms: Room[];
}

// Alert
export interface Alert {
  id: string;
  severity: AlertSeverity;
  status: AlertStatus;
  title: string;
  description: string;
  room_name: string | null;
  created_at: string;
  resolved_at: string | null;
}

// Alerts response
export interface AlertsResponse {
  active: Alert[];
  resolved: Alert[];
}

// WebSocket message types
export type WebSocketMessageType =
  | 'metrics_update'
  | 'room_update'
  | 'alert'
  | 'heartbeat'
  | 'pong';

export interface WebSocketMessage {
  type: WebSocketMessageType;
  data?: Record<string, unknown>;
}

// Connection status for WebSocket
export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

// Chart data point for time series
export interface ChartDataPoint {
  time: string;
  rooms: number;
  participants: number;
  joinRate: number;
  disconnectRate: number;
}
