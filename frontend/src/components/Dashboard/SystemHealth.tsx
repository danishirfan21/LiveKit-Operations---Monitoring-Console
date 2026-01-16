import React from 'react';
import { Card } from '../common/Card';
import { ConnectionStatusIndicator } from '../common/StatusIndicator';
import { ConnectionStatus, SystemMetrics } from '../../types';

interface SystemHealthProps {
  connectionStatus: ConnectionStatus;
  metrics: SystemMetrics | null;
  activeAlertCount: number;
}

export function SystemHealth({
  connectionStatus,
  metrics,
  activeAlertCount,
}: SystemHealthProps) {
  const getOverallHealth = (): {
    status: 'healthy' | 'warning' | 'critical';
    label: string;
  } => {
    if (connectionStatus !== 'connected') {
      return { status: 'critical', label: 'Disconnected' };
    }
    if (activeAlertCount > 0) {
      return { status: 'warning', label: 'Issues Detected' };
    }
    if (metrics && metrics.avg_connection_quality < 0.5) {
      return { status: 'warning', label: 'Degraded Performance' };
    }
    return { status: 'healthy', label: 'All Systems Operational' };
  };

  const health = getOverallHealth();

  const healthColors = {
    healthy: 'bg-green-500',
    warning: 'bg-yellow-500',
    critical: 'bg-red-500',
  };

  const healthBgColors = {
    healthy: 'bg-green-50 border-green-200',
    warning: 'bg-yellow-50 border-yellow-200',
    critical: 'bg-red-50 border-red-200',
  };

  const healthTextColors = {
    healthy: 'text-green-800',
    warning: 'text-yellow-800',
    critical: 'text-red-800',
  };

  return (
    <Card title="System Health">
      <div className="space-y-4">
        {/* Overall Health Status */}
        <div
          className={`p-4 rounded-lg border ${healthBgColors[health.status]}`}
        >
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className={`w-4 h-4 rounded-full ${healthColors[health.status]}`} />
              {health.status === 'healthy' && (
                <div
                  className={`absolute inset-0 w-4 h-4 rounded-full ${healthColors[health.status]} animate-ping opacity-75`}
                />
              )}
            </div>
            <span className={`font-semibold ${healthTextColors[health.status]}`}>
              {health.label}
            </span>
          </div>
        </div>

        {/* Connection Status */}
        <div className="flex items-center justify-between py-2 border-b border-gray-100">
          <span className="text-sm text-gray-600">WebSocket Connection</span>
          <ConnectionStatusIndicator status={connectionStatus} />
        </div>

        {/* Metrics Summary */}
        {metrics && (
          <>
            <div className="flex items-center justify-between py-2 border-b border-gray-100">
              <span className="text-sm text-gray-600">Active Rooms</span>
              <span className="font-medium text-gray-900">{metrics.active_rooms}</span>
            </div>

            <div className="flex items-center justify-between py-2 border-b border-gray-100">
              <span className="text-sm text-gray-600">Total Participants</span>
              <span className="font-medium text-gray-900">{metrics.total_participants}</span>
            </div>

            <div className="flex items-center justify-between py-2 border-b border-gray-100">
              <span className="text-sm text-gray-600">Connection Quality</span>
              <div className="flex items-center gap-2">
                <div className="w-24 bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${
                      metrics.avg_connection_quality > 0.8
                        ? 'bg-green-500'
                        : metrics.avg_connection_quality > 0.5
                        ? 'bg-yellow-500'
                        : 'bg-red-500'
                    }`}
                    style={{ width: `${metrics.avg_connection_quality * 100}%` }}
                  />
                </div>
                <span className="text-sm font-medium text-gray-900">
                  {Math.round(metrics.avg_connection_quality * 100)}%
                </span>
              </div>
            </div>
          </>
        )}

        {/* Active Alerts */}
        <div className="flex items-center justify-between py-2">
          <span className="text-sm text-gray-600">Active Alerts</span>
          <span
            className={`px-2 py-0.5 rounded-full text-sm font-medium ${
              activeAlertCount === 0
                ? 'bg-green-100 text-green-800'
                : activeAlertCount < 3
                ? 'bg-yellow-100 text-yellow-800'
                : 'bg-red-100 text-red-800'
            }`}
          >
            {activeAlertCount}
          </span>
        </div>
      </div>
    </Card>
  );
}
