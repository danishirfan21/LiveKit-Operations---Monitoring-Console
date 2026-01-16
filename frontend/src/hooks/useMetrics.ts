import { useState, useEffect, useCallback } from 'react';
import { useWebSocket } from './useWebSocket';
import {
  SystemMetrics,
  Room,
  Alert,
  WebSocketMessage,
  ConnectionStatus,
  ChartDataPoint,
} from '../types';

interface UseMetricsReturn {
  // Current data
  currentMetrics: SystemMetrics | null;
  rooms: Room[];
  activeAlerts: Alert[];
  resolvedAlerts: Alert[];

  // Time series data for charts
  chartData: ChartDataPoint[];

  // Connection status
  connectionStatus: ConnectionStatus;

  // Actions
  refreshData: () => Promise<void>;
  resolveAlert: (alertId: string) => Promise<void>;
}

const API_BASE = '';  // Relative to the same origin

export function useMetrics(): UseMetricsReturn {
  const [currentMetrics, setCurrentMetrics] = useState<SystemMetrics | null>(null);
  const [rooms, setRooms] = useState<Room[]>([]);
  const [activeAlerts, setActiveAlerts] = useState<Alert[]>([]);
  const [resolvedAlerts, setResolvedAlerts] = useState<Alert[]>([]);
  const [chartData, setChartData] = useState<ChartDataPoint[]>([]);

  // Handle WebSocket messages
  const handleMessage = useCallback((message: WebSocketMessage) => {
    switch (message.type) {
      case 'metrics_update': {
        const metrics = message.data as unknown as SystemMetrics;
        setCurrentMetrics(metrics);

        // Add to chart data
        setChartData(prev => {
          const newPoint: ChartDataPoint = {
            time: new Date(metrics.timestamp).toLocaleTimeString(),
            rooms: metrics.active_rooms,
            participants: metrics.total_participants,
            joinRate: metrics.join_rate,
            disconnectRate: metrics.disconnect_rate,
          };

          // Keep last 60 data points (1 minute at 1/sec)
          const updated = [...prev, newPoint];
          if (updated.length > 60) {
            return updated.slice(-60);
          }
          return updated;
        });
        break;
      }

      case 'room_update': {
        const data = message.data as { type: string; room: Room };
        if (data.type === 'room_started') {
          setRooms(prev => [...prev, data.room]);
        } else if (data.type === 'room_finished') {
          setRooms(prev => prev.filter(r => r.sid !== data.room.sid));
        }
        break;
      }

      case 'alert': {
        const alert = message.data as unknown as Alert;
        if (alert.status === 'active') {
          setActiveAlerts(prev => {
            // Avoid duplicates
            const exists = prev.some(a => a.id === alert.id);
            if (exists) return prev;
            return [...prev, alert];
          });
        } else {
          // Move from active to resolved
          setActiveAlerts(prev => prev.filter(a => a.id !== alert.id));
          setResolvedAlerts(prev => {
            const exists = prev.some(a => a.id === alert.id);
            if (exists) return prev;
            return [alert, ...prev].slice(0, 20);  // Keep last 20
          });
        }
        break;
      }

      case 'heartbeat':
        // Connection is alive
        break;
    }
  }, []);

  // WebSocket connection
  const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws`;
  const { status: connectionStatus } = useWebSocket(wsUrl, {
    onMessage: handleMessage,
  });

  // Fetch initial data
  const refreshData = useCallback(async () => {
    try {
      // Fetch current metrics
      const metricsRes = await fetch(`${API_BASE}/api/metrics/current`);
      if (metricsRes.ok) {
        const metrics = await metricsRes.json();
        setCurrentMetrics(metrics);
      }

      // Fetch rooms
      const roomsRes = await fetch(`${API_BASE}/api/rooms`);
      if (roomsRes.ok) {
        const roomsData = await roomsRes.json();
        setRooms(roomsData);
      }

      // Fetch alerts
      const alertsRes = await fetch(`${API_BASE}/api/alerts`);
      if (alertsRes.ok) {
        const alertsData = await alertsRes.json();
        setActiveAlerts(alertsData.active || []);
        setResolvedAlerts(alertsData.resolved || []);
      }

      // Fetch history for chart
      const historyRes = await fetch(`${API_BASE}/api/metrics/history`);
      if (historyRes.ok) {
        const history: SystemMetrics[] = await historyRes.json();
        const chartPoints: ChartDataPoint[] = history.map(m => ({
          time: new Date(m.timestamp).toLocaleTimeString(),
          rooms: m.active_rooms,
          participants: m.total_participants,
          joinRate: m.join_rate,
          disconnectRate: m.disconnect_rate,
        }));
        setChartData(chartPoints);
      }
    } catch (error) {
      console.error('Failed to fetch data:', error);
    }
  }, []);

  // Resolve an alert
  const resolveAlert = useCallback(async (alertId: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/alerts/${alertId}/resolve`, {
        method: 'POST',
      });
      if (res.ok) {
        const resolved = await res.json();
        setActiveAlerts(prev => prev.filter(a => a.id !== alertId));
        setResolvedAlerts(prev => [resolved, ...prev].slice(0, 20));
      }
    } catch (error) {
      console.error('Failed to resolve alert:', error);
    }
  }, []);

  // Initial data fetch
  useEffect(() => {
    refreshData();
  }, [refreshData]);

  return {
    currentMetrics,
    rooms,
    activeAlerts,
    resolvedAlerts,
    chartData,
    connectionStatus,
    refreshData,
    resolveAlert,
  };
}
