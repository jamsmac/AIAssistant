'use client';

import React, { memo } from 'react';
import { Plus, Trash2, Search, ChevronLeft } from 'lucide-react';

interface ChatSession {
  id: string;
  user_id: number;
  created_at: string;
  updated_at: string;
  message_count: number;
  first_message?: string;
}

interface ChatSidebarProps {
  sessions: ChatSession[];
  currentSessionId: string;
  sidebarOpen: boolean;
  searchQuery: string;
  deleteConfirm: string | null;
  sessionsLoading: boolean;
  onToggleSidebar: () => void;
  onNewSession: () => void;
  onLoadSession: (sessionId: string) => void;
  onDeleteSession: (sessionId: string) => void;
  onSearchChange: (query: string) => void;
  onSetDeleteConfirm: (sessionId: string | null) => void;
}

const ChatSidebar = memo(function ChatSidebar({
  sessions,
  currentSessionId,
  sidebarOpen,
  searchQuery,
  deleteConfirm,
  sessionsLoading,
  onToggleSidebar,
  onNewSession,
  onLoadSession,
  onDeleteSession,
  onSearchChange,
  onSetDeleteConfirm
}: ChatSidebarProps) {
  const getRelativeTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  const filteredSessions = sessions.filter(session =>
    !searchQuery ||
    session.first_message?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    session.id.includes(searchQuery)
  );

  return (
    <div
      className={`${
        sidebarOpen ? 'w-80' : 'w-0'
      } bg-gray-900 border-r border-gray-700 transition-all duration-300 overflow-hidden flex-shrink-0`}
    >
      <div className="w-80 h-full flex flex-col">
        {/* Sidebar Header */}
        <div className="p-4 border-b border-gray-700">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white">Chat History</h2>
            <button
              onClick={onToggleSidebar}
              className="p-2 hover:bg-gray-800 rounded-lg text-gray-400 transition"
              title="Close sidebar"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
          </div>

          {/* New Chat Button */}
          <button
            onClick={onNewSession}
            className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white font-medium transition flex items-center justify-center gap-2"
          >
            <Plus className="w-4 h-4" />
            New Chat
          </button>

          {/* Search */}
          <div className="mt-4 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => onSearchChange(e.target.value)}
              placeholder="Search chats..."
              className="w-full bg-gray-800 border border-gray-700 rounded-lg pl-10 pr-4 py-2 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* Sessions List */}
        <div className="flex-1 overflow-y-auto p-4">
          {sessionsLoading ? (
            <div className="text-center py-8">
              <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
              <div className="text-gray-400 text-sm">Loading sessions...</div>
            </div>
          ) : filteredSessions.length === 0 ? (
            <div className="text-center py-8 text-gray-400">
              {searchQuery ? 'No matching chats found' : 'No chat history yet'}
            </div>
          ) : (
            <div className="space-y-2">
              {filteredSessions.map(session => (
                <div
                  key={session.id}
                  className={`relative group cursor-pointer rounded-lg p-3 transition ${
                    session.id === currentSessionId
                      ? 'bg-blue-600/20 border border-blue-500/50'
                      : 'hover:bg-gray-800 border border-transparent'
                  }`}
                  onClick={() => onLoadSession(session.id)}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="text-sm text-white truncate">
                        {session.first_message || `Chat #${session.id.slice(0, 8)}`}
                      </div>
                      <div className="text-xs text-gray-400 mt-1">
                        {getRelativeTime(session.updated_at)} • {session.message_count} msgs
                      </div>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onSetDeleteConfirm(session.id);
                      }}
                      className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-500/20 rounded text-red-400 transition"
                      title="Delete chat"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>

                  {/* Delete Confirmation */}
                  {deleteConfirm === session.id && (
                    <div className="absolute inset-0 bg-gray-800 rounded-lg p-3 flex flex-col justify-center gap-2 z-10">
                      <div className="text-sm text-white">Delete this chat?</div>
                      <div className="flex gap-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onDeleteSession(session.id);
                          }}
                          className="flex-1 px-3 py-1 bg-red-500 hover:bg-red-600 rounded text-white text-xs transition"
                        >
                          Delete
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onSetDeleteConfirm(null);
                          }}
                          className="flex-1 px-3 py-1 bg-gray-600 hover:bg-gray-700 rounded text-white text-xs transition"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
});

export default ChatSidebar;