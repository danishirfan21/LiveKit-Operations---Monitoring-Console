import React, { useState } from 'react';
import { Card } from '../common/Card';
import { SeverityBadge, StatusBadge } from '../common/StatusIndicator';
import { Alert } from '../../types';

interface AlertsPanelProps {
  activeAlerts: Alert[];
  resolvedAlerts: Alert[];
  onResolveAlert: (alertId: string) => void;
}

export function AlertsPanel({
  activeAlerts,
  resolvedAlerts,
  onResolveAlert,
}: AlertsPanelProps) {
  const [showResolved, setShowResolved] = useState(false);

  const formatTime = (isoString: string): string => {
    const date = new Date(isoString);
    return date.toLocaleTimeString();
  };

  const formatTimeAgo = (isoString: string): string => {
    const date = new Date(isoString);
    const now = new Date();
    const diffSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (diffSeconds < 60) return `${diffSeconds}s ago`;
    if (diffSeconds < 3600) return `${Math.floor(diffSeconds / 60)}m ago`;
    return `${Math.floor(diffSeconds / 3600)}h ago`;
  };

  return (
    <Card
      title="Alerts"
      headerAction={
        <div className="flex items-center gap-2">
          {activeAlerts.length > 0 && (
            <span className="px-2 py-0.5 bg-red-100 text-red-800 rounded-full text-xs font-medium">
              {activeAlerts.length} active
            </span>
          )}
          <button
            onClick={() => setShowResolved(!showResolved)}
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            {showResolved ? 'Hide resolved' : 'Show resolved'}
          </button>
        </div>
      }
    >
      <div className="space-y-3">
        {/* Active Alerts */}
        {activeAlerts.length === 0 && !showResolved && (
          <div className="text-center py-8 text-gray-500">
            <svg
              className="w-12 h-12 mx-auto mb-4 text-green-300"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <p>No active alerts</p>
            <p className="text-sm text-gray-400">System is running normally</p>
          </div>
        )}

        {activeAlerts.map((alert) => (
          <AlertItem
            key={alert.id}
            alert={alert}
            onResolve={() => onResolveAlert(alert.id)}
            formatTime={formatTime}
            formatTimeAgo={formatTimeAgo}
          />
        ))}

        {/* Resolved Alerts */}
        {showResolved && resolvedAlerts.length > 0 && (
          <>
            <div className="border-t border-gray-200 my-4 pt-4">
              <h4 className="text-sm font-medium text-gray-500 mb-3">
                Recently Resolved
              </h4>
            </div>
            {resolvedAlerts.map((alert) => (
              <AlertItem
                key={alert.id}
                alert={alert}
                formatTime={formatTime}
                formatTimeAgo={formatTimeAgo}
              />
            ))}
          </>
        )}
      </div>
    </Card>
  );
}

interface AlertItemProps {
  alert: Alert;
  onResolve?: () => void;
  formatTime: (isoString: string) => string;
  formatTimeAgo: (isoString: string) => string;
}

function AlertItem({ alert, onResolve, formatTime, formatTimeAgo }: AlertItemProps) {
  const isActive = alert.status === 'active';

  const severityBorders = {
    info: 'border-l-blue-500',
    warning: 'border-l-yellow-500',
    critical: 'border-l-red-500',
  };

  const severityBgs = {
    info: isActive ? 'bg-blue-50' : 'bg-gray-50',
    warning: isActive ? 'bg-yellow-50' : 'bg-gray-50',
    critical: isActive ? 'bg-red-50' : 'bg-gray-50',
  };

  return (
    <div
      className={`p-3 rounded-lg border-l-4 ${severityBorders[alert.severity]} ${
        severityBgs[alert.severity]
      } ${!isActive ? 'opacity-60' : ''}`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <SeverityBadge severity={alert.severity} />
            {!isActive && <StatusBadge active={false} />}
          </div>
          <p className="font-medium text-gray-900">{alert.title}</p>
          <p className="text-sm text-gray-600 mt-1">{alert.description}</p>
          <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
            <span title={formatTime(alert.created_at)}>
              {formatTimeAgo(alert.created_at)}
            </span>
            {alert.room_name && (
              <span className="flex items-center">
                <svg
                  className="w-3 h-3 mr-1"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5"
                  />
                </svg>
                {alert.room_name}
              </span>
            )}
            {alert.resolved_at && (
              <span>Resolved {formatTimeAgo(alert.resolved_at)}</span>
            )}
          </div>
        </div>
        {isActive && onResolve && (
          <button
            onClick={onResolve}
            className="px-3 py-1 text-sm bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
          >
            Resolve
          </button>
        )}
      </div>
    </div>
  );
}
