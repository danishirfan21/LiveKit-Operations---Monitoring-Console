import React from 'react';
import { Card } from '../common/Card';
import { QualityIndicator } from '../common/StatusIndicator';
import { Room, Participant } from '../../types';

interface RoomDetailProps {
  room: Room | null;
  onClose: () => void;
}

export function RoomDetail({ room, onClose }: RoomDetailProps) {
  if (!room) {
    return (
      <Card title="Room Details">
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
              d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122"
            />
          </svg>
          <p>Select a room to view details</p>
        </div>
      </Card>
    );
  }

  const formatTime = (isoString: string): string => {
    return new Date(isoString).toLocaleTimeString();
  };

  const formatDuration = (createdAt: string): string => {
    const created = new Date(createdAt);
    const now = new Date();
    const diffSeconds = Math.floor((now.getTime() - created.getTime()) / 1000);

    const hours = Math.floor(diffSeconds / 3600);
    const minutes = Math.floor((diffSeconds % 3600) / 60);
    const seconds = diffSeconds % 60;

    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    if (minutes > 0) {
      return `${minutes}m ${seconds}s`;
    }
    return `${seconds}s`;
  };

  return (
    <Card
      title={room.name}
      headerAction={
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600 transition-colors"
        >
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      }
    >
      <div className="space-y-4">
        {/* Room Info */}
        <div className="grid grid-cols-2 gap-4 p-3 bg-gray-50 rounded-lg">
          <div>
            <p className="text-xs text-gray-500">Created</p>
            <p className="font-medium text-gray-900">{formatTime(room.created_at)}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Duration</p>
            <p className="font-medium text-gray-900">{formatDuration(room.created_at)}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Participants</p>
            <p className="font-medium text-gray-900">{room.participant_count}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Max Participants</p>
            <p className="font-medium text-gray-900">{room.max_participants}</p>
          </div>
        </div>

        {/* Participants */}
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-2">
            Participants ({room.participants.length})
          </h4>

          {room.participants.length === 0 ? (
            <p className="text-sm text-gray-500 text-center py-4">No participants</p>
          ) : (
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {room.participants.map((participant) => (
                <ParticipantRow key={participant.sid} participant={participant} />
              ))}
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}

interface ParticipantRowProps {
  participant: Participant;
}

function ParticipantRow({ participant }: ParticipantRowProps) {
  const formatJoinTime = (isoString: string): string => {
    return new Date(isoString).toLocaleTimeString();
  };

  return (
    <div className="flex items-center justify-between p-2 bg-gray-50 rounded-lg">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
          <span className="text-primary-600 font-medium text-sm">
            {(participant.name || participant.identity).charAt(0).toUpperCase()}
          </span>
        </div>
        <div>
          <p className="font-medium text-gray-900 text-sm">
            {participant.name || participant.identity}
          </p>
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <span>Joined {formatJoinTime(participant.joined_at)}</span>
            {participant.is_publisher && (
              <span className="px-1.5 py-0.5 bg-green-100 text-green-700 rounded">
                Publisher
              </span>
            )}
            {participant.tracks_published > 0 && (
              <span className="px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded">
                {participant.tracks_published} tracks
              </span>
            )}
          </div>
        </div>
      </div>
      <QualityIndicator quality={participant.connection_quality} showLabel />
    </div>
  );
}
