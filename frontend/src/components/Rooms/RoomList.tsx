import React from 'react';
import { Card } from '../common/Card';
import { Room } from '../../types';

interface RoomListProps {
  rooms: Room[];
  selectedRoom: Room | null;
  onSelectRoom: (room: Room) => void;
}

export function RoomList({ rooms, selectedRoom, onSelectRoom }: RoomListProps) {
  const formatDuration = (createdAt: string): string => {
    const created = new Date(createdAt);
    const now = new Date();
    const diffSeconds = Math.floor((now.getTime() - created.getTime()) / 1000);

    if (diffSeconds < 60) return `${diffSeconds}s`;
    if (diffSeconds < 3600) return `${Math.floor(diffSeconds / 60)}m`;
    return `${(diffSeconds / 3600).toFixed(1)}h`;
  };

  if (rooms.length === 0) {
    return (
      <Card title="Active Rooms">
        <div className="text-center py-8 text-gray-500">
          <svg
            className="w-12 h-12 mx-auto mb-4 text-gray-300"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
            />
          </svg>
          <p>No active rooms</p>
        </div>
      </Card>
    );
  }

  return (
    <Card
      title="Active Rooms"
      headerAction={
        <span className="text-sm text-gray-500">{rooms.length} rooms</span>
      }
    >
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {rooms.map((room) => (
          <button
            key={room.sid}
            onClick={() => onSelectRoom(room)}
            className={`w-full text-left p-3 rounded-lg border transition-all ${
              selectedRoom?.sid === room.sid
                ? 'bg-primary-50 border-primary-200'
                : 'bg-gray-50 border-gray-200 hover:bg-gray-100'
            }`}
          >
            <div className="flex items-center justify-between">
              <div className="flex-1 min-w-0">
                <p className="font-medium text-gray-900 truncate">{room.name}</p>
                <div className="flex items-center gap-3 mt-1">
                  <span className="flex items-center text-sm text-gray-500">
                    <svg
                      className="w-4 h-4 mr-1"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"
                      />
                    </svg>
                    {room.participant_count}
                  </span>
                  <span className="flex items-center text-sm text-gray-500">
                    <svg
                      className="w-4 h-4 mr-1"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                    {formatDuration(room.created_at)}
                  </span>
                </div>
              </div>
              <svg
                className="w-5 h-5 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5l7 7-7 7"
                />
              </svg>
            </div>
          </button>
        ))}
      </div>
    </Card>
  );
}
