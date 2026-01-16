import React, { useState } from 'react';
import { useMetrics } from './hooks/useMetrics';
import { MetricsGrid } from './components/Dashboard/MetricsGrid';
import { TimeSeriesChart } from './components/Dashboard/TimeSeriesChart';
import { SystemHealth } from './components/Dashboard/SystemHealth';
import { RoomList } from './components/Rooms/RoomList';
import { RoomDetail } from './components/Rooms/RoomDetail';
import { AlertsPanel } from './components/Alerts/AlertsPanel';
import { ConnectionStatusIndicator } from './components/common/StatusIndicator';
import { Room } from './types';

function App() {
  const {
    currentMetrics,
    rooms,
    activeAlerts,
    resolvedAlerts,
    chartData,
    connectionStatus,
    refreshData,
    resolveAlert,
  } = useMetrics();

  const [selectedRoom, setSelectedRoom] = useState<Room | null>(null);

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <svg
                className="w-8 h-8 text-primary-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                />
              </svg>
              <div>
                <h1 className="text-xl font-bold text-gray-900">
                  LiveKit Operations Console
                </h1>
                <p className="text-sm text-gray-500">Real-time monitoring dashboard</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <ConnectionStatusIndicator status={connectionStatus} />
              <button
                onClick={refreshData}
                className="px-3 py-1.5 text-sm bg-primary-600 text-white rounded-md hover:bg-primary-700 transition-colors flex items-center gap-1"
              >
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                  />
                </svg>
                Refresh
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="space-y-6">
          {/* Metrics Grid */}
          <section>
            <h2 className="text-lg font-semibold text-gray-800 mb-4">
              System Overview
            </h2>
            <MetricsGrid metrics={currentMetrics} />
          </section>

          {/* Charts and Health */}
          <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <TimeSeriesChart data={chartData} />
            </div>
            <div>
              <SystemHealth
                connectionStatus={connectionStatus}
                metrics={currentMetrics}
                activeAlertCount={activeAlerts.length}
              />
            </div>
          </section>

          {/* Rooms and Alerts */}
          <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div>
              <RoomList
                rooms={rooms}
                selectedRoom={selectedRoom}
                onSelectRoom={setSelectedRoom}
              />
            </div>
            <div>
              <RoomDetail room={selectedRoom} onClose={() => setSelectedRoom(null)} />
            </div>
            <div>
              <AlertsPanel
                activeAlerts={activeAlerts}
                resolvedAlerts={resolvedAlerts}
                onResolveAlert={resolveAlert}
              />
            </div>
          </section>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-200 bg-white mt-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <p className="text-center text-sm text-gray-500">
            LiveKit Operations Console - Real-time monitoring for LiveKit infrastructure
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
