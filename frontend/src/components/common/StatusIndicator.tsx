import React from 'react';
import { ConnectionQuality, ConnectionStatus, AlertSeverity } from '../../types';

interface ConnectionStatusIndicatorProps {
  status: ConnectionStatus;
}

export function ConnectionStatusIndicator({ status }: ConnectionStatusIndicatorProps) {
  const statusConfig = {
    connected: {
      color: 'bg-green-500',
      text: 'Connected',
      pulse: true,
    },
    connecting: {
      color: 'bg-yellow-500',
      text: 'Connecting...',
      pulse: true,
    },
    disconnected: {
      color: 'bg-red-500',
      text: 'Disconnected',
      pulse: false,
    },
    error: {
      color: 'bg-red-500',
      text: 'Error',
      pulse: false,
    },
  };

  const config = statusConfig[status];

  return (
    <div className="flex items-center gap-2">
      <div className="relative">
        <div className={`w-3 h-3 rounded-full ${config.color}`} />
        {config.pulse && (
          <div
            className={`absolute inset-0 w-3 h-3 rounded-full ${config.color} animate-ping opacity-75`}
          />
        )}
      </div>
      <span className="text-sm text-gray-600">{config.text}</span>
    </div>
  );
}

interface QualityIndicatorProps {
  quality: ConnectionQuality;
  showLabel?: boolean;
}

export function QualityIndicator({ quality, showLabel = false }: QualityIndicatorProps) {
  const qualityConfig = {
    excellent: {
      color: 'bg-green-500',
      bars: 4,
      label: 'Excellent',
    },
    good: {
      color: 'bg-yellow-500',
      bars: 3,
      label: 'Good',
    },
    poor: {
      color: 'bg-red-500',
      bars: 1,
      label: 'Poor',
    },
    unknown: {
      color: 'bg-gray-400',
      bars: 0,
      label: 'Unknown',
    },
  };

  const config = qualityConfig[quality];

  return (
    <div className="flex items-center gap-2">
      <div className="flex items-end gap-0.5 h-4">
        {[1, 2, 3, 4].map((bar) => (
          <div
            key={bar}
            className={`w-1 rounded-sm transition-all ${
              bar <= config.bars ? config.color : 'bg-gray-200'
            }`}
            style={{ height: `${bar * 25}%` }}
          />
        ))}
      </div>
      {showLabel && <span className="text-xs text-gray-500">{config.label}</span>}
    </div>
  );
}

interface SeverityBadgeProps {
  severity: AlertSeverity;
}

export function SeverityBadge({ severity }: SeverityBadgeProps) {
  const severityConfig = {
    info: {
      bg: 'bg-blue-100',
      text: 'text-blue-800',
      label: 'INFO',
    },
    warning: {
      bg: 'bg-yellow-100',
      text: 'text-yellow-800',
      label: 'WARNING',
    },
    critical: {
      bg: 'bg-red-100',
      text: 'text-red-800',
      label: 'CRITICAL',
    },
  };

  const config = severityConfig[severity];

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${config.bg} ${config.text}`}
    >
      {config.label}
    </span>
  );
}

interface StatusBadgeProps {
  active: boolean;
}

export function StatusBadge({ active }: StatusBadgeProps) {
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
        active
          ? 'bg-red-100 text-red-800'
          : 'bg-green-100 text-green-800'
      }`}
    >
      {active ? 'ACTIVE' : 'RESOLVED'}
    </span>
  );
}
