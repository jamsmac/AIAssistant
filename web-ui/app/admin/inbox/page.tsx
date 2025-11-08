'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

interface Conversation {
  id: string;
  channel_id: string;
  channel_name: string;
  channel_type: string;
  participant_id: string;
  participant_name: string;
  status: string;
  unread_count: number;
  last_message_at: string;
  last_message_preview: string;
  assigned_agent_id?: string;
  created_at: string;
}

interface Message {
  id: string;
  conversation_id: string;
  direction: string;
  sender_id: string;
  sender_name: string;
  content: string;
  message_type: string;
  attachments: any[];
  metadata: any;
  read_at?: string;
  created_at: string;
}

interface Channel {
  id: string;
  type: string;
  name: string;
  status: string;
}

interface Stats {
  total_channels: number;
  active_channels: number;
  total_conversations: number;
  active_conversations: number;
  total_messages: number;
  messages_today: number;
  unread_messages: number;
}

export default function UnifiedInbox() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [channels, setChannels] = useState<Channel[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [messageLoading, setMessageLoading] = useState(false);

  // Filters
  const [filterChannel, setFilterChannel] = useState<string>('');
  const [filterStatus, setFilterStatus] = useState<string>('active');

  // Message compose
  const [replyText, setReplyText] = useState('');
  const [sending, setSending] = useState(false);

  // Fetch data
  useEffect(() => {
    fetchData();
  }, [filterChannel, filterStatus]);

  const fetchData = async () => {
    setLoading(true);
    try {
      // Fetch stats
      const statsRes = await fetch('/api/communications/stats');
      const statsData = await statsRes.json();
      setStats(statsData);

      // Fetch channels
      const channelsRes = await fetch('/api/communications/channels');
      const channelsData = await channelsRes.json();
      setChannels(channelsData);

      // Fetch conversations
      let url = '/api/communications/conversations?limit=50';
      if (filterChannel) url += `&channel_id=${filterChannel}`;
      if (filterStatus) url += `&status=${filterStatus}`;

      const convRes = await fetch(url);
      const convData = await convRes.json();
      setConversations(convData);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const selectConversation = async (conv: Conversation) => {
    setSelectedConversation(conv);
    setMessageLoading(true);
    try {
      const res = await fetch(`/api/communications/conversations/${conv.id}/messages`);
      const data = await res.json();
      setMessages(data);

      // Mark as read
      await fetch(`/api/communications/conversations/${conv.id}/mark-read`, {
        method: 'POST'
      });

      // Update conversation unread count locally
      setConversations(conversations.map(c =>
        c.id === conv.id ? {...c, unread_count: 0} : c
      ));
    } catch (error) {
      console.error('Error fetching messages:', error);
    } finally {
      setMessageLoading(false);
    }
  };

  const sendReply = async () => {
    if (!selectedConversation || !replyText.trim()) return;

    setSending(true);
    try {
      const res = await fetch('/api/communications/messages/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          conversation_id: selectedConversation.id,
          content: replyText,
          message_type: 'text',
          metadata: {}
        })
      });

      if (res.ok) {
        const newMessage = await res.json();
        setMessages([...messages, newMessage]);
        setReplyText('');

        // Update conversation preview
        setConversations(conversations.map(c =>
          c.id === selectedConversation.id
            ? { ...c, last_message_preview: replyText.substring(0, 100), last_message_at: new Date().toISOString() }
            : c
        ));
      }
    } catch (error) {
      console.error('Error sending message:', error);
      alert('Failed to send message');
    } finally {
      setSending(false);
    }
  };

  const closeConversation = async (convId: string) => {
    if (!confirm('Close this conversation?')) return;

    try {
      await fetch(`/api/communications/conversations/${convId}/close`, {
        method: 'POST'
      });

      setConversations(conversations.map(c =>
        c.id === convId ? { ...c, status: 'closed' } : c
      ));

      if (selectedConversation?.id === convId) {
        setSelectedConversation(null);
        setMessages([]);
      }
    } catch (error) {
      console.error('Error closing conversation:', error);
      alert('Failed to close conversation');
    }
  };

  const getChannelIcon = (type: string) => {
    switch (type) {
      case 'telegram': return '💬';
      case 'gmail': return '✉️';
      case 'whatsapp': return '📱';
      case 'slack': return '💼';
      case 'discord': return '🎮';
      default: return '📨';
    }
  };

  const formatTime = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;
    return date.toLocaleDateString();
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading inbox...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">📬 Unified Inbox</h1>
              <p className="text-sm text-gray-600">All conversations in one place</p>
            </div>
            <Link
              href="/admin/inbox/channels"
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              ⚙️ Manage Channels
            </Link>
          </div>
        </div>
      </div>

      {/* Stats Bar */}
      {stats && (
        <div className="bg-white border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
            <div className="grid grid-cols-7 gap-4 text-center">
              <div>
                <div className="text-2xl font-bold text-blue-600">{stats.active_channels}</div>
                <div className="text-xs text-gray-600">Active Channels</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-green-600">{stats.active_conversations}</div>
                <div className="text-xs text-gray-600">Active Chats</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-purple-600">{stats.total_conversations}</div>
                <div className="text-xs text-gray-600">Total Chats</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-orange-600">{stats.unread_messages}</div>
                <div className="text-xs text-gray-600">Unread</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-indigo-600">{stats.messages_today}</div>
                <div className="text-xs text-gray-600">Today</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-gray-600">{stats.total_messages}</div>
                <div className="text-xs text-gray-600">Total Messages</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-teal-600">{stats.total_channels}</div>
                <div className="text-xs text-gray-600">Total Channels</div>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid grid-cols-12 gap-4" style={{ height: 'calc(100vh - 280px)' }}>
          {/* Conversations List */}
          <div className="col-span-4 bg-white rounded-lg shadow overflow-hidden flex flex-col">
            {/* Filters */}
            <div className="p-4 border-b bg-gray-50">
              <div className="space-y-2">
                <select
                  value={filterChannel}
                  onChange={(e) => setFilterChannel(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg text-sm"
                >
                  <option value="">All Channels</option>
                  {channels.map(ch => (
                    <option key={ch.id} value={ch.id}>
                      {getChannelIcon(ch.type)} {ch.name}
                    </option>
                  ))}
                </select>

                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg text-sm"
                >
                  <option value="">All Status</option>
                  <option value="active">Active</option>
                  <option value="archived">Archived</option>
                  <option value="closed">Closed</option>
                </select>
              </div>
            </div>

            {/* Conversation List */}
            <div className="flex-1 overflow-y-auto">
              {conversations.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  <p>No conversations found</p>
                </div>
              ) : (
                conversations.map(conv => (
                  <div
                    key={conv.id}
                    onClick={() => selectConversation(conv)}
                    className={`p-4 border-b cursor-pointer hover:bg-gray-50 ${
                      selectedConversation?.id === conv.id ? 'bg-blue-50 border-l-4 border-l-blue-600' : ''
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-xl">{getChannelIcon(conv.channel_type)}</span>
                          <h3 className="font-semibold text-gray-900 truncate">
                            {conv.participant_name}
                          </h3>
                          {conv.unread_count > 0 && (
                            <span className="px-2 py-0.5 bg-blue-600 text-white text-xs rounded-full">
                              {conv.unread_count}
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-gray-500 mt-1">
                          via {conv.channel_name}
                        </p>
                        <p className="text-sm text-gray-600 mt-1 truncate">
                          {conv.last_message_preview}
                        </p>
                      </div>
                      <div className="text-xs text-gray-500 ml-2">
                        {formatTime(conv.last_message_at)}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Messages Panel */}
          <div className="col-span-8 bg-white rounded-lg shadow overflow-hidden flex flex-col">
            {!selectedConversation ? (
              <div className="flex-1 flex items-center justify-center text-gray-500">
                <div className="text-center">
                  <div className="text-6xl mb-4">💬</div>
                  <p className="text-lg">Select a conversation to view messages</p>
                </div>
              </div>
            ) : (
              <>
                {/* Conversation Header */}
                <div className="p-4 border-b bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">{getChannelIcon(selectedConversation.channel_type)}</span>
                      <div>
                        <h2 className="font-bold text-gray-900">{selectedConversation.participant_name}</h2>
                        <p className="text-sm text-gray-600">
                          {selectedConversation.participant_id} • via {selectedConversation.channel_name}
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={() => closeConversation(selectedConversation.id)}
                      className="px-3 py-1 text-sm bg-gray-200 hover:bg-gray-300 rounded"
                    >
                      Close
                    </button>
                  </div>
                </div>

                {/* Messages */}
                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                  {messageLoading ? (
                    <div className="text-center py-8">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                    </div>
                  ) : messages.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      No messages yet
                    </div>
                  ) : (
                    messages.map(msg => (
                      <div
                        key={msg.id}
                        className={`flex ${msg.direction === 'outbound' ? 'justify-end' : 'justify-start'}`}
                      >
                        <div
                          className={`max-w-md px-4 py-2 rounded-lg ${
                            msg.direction === 'outbound'
                              ? 'bg-blue-600 text-white'
                              : 'bg-gray-100 text-gray-900'
                          }`}
                        >
                          <div className="text-xs opacity-75 mb-1">
                            {msg.sender_name} • {formatTime(msg.created_at)}
                          </div>
                          <div className="whitespace-pre-wrap">{msg.content}</div>
                          {msg.attachments && msg.attachments.length > 0 && (
                            <div className="mt-2 text-xs opacity-75">
                              📎 {msg.attachments.length} attachment(s)
                            </div>
                          )}
                        </div>
                      </div>
                    ))
                  )}
                </div>

                {/* Reply Box */}
                <div className="p-4 border-t bg-gray-50">
                  <div className="flex gap-2">
                    <textarea
                      value={replyText}
                      onChange={(e) => setReplyText(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
                          sendReply();
                        }
                      }}
                      placeholder="Type your reply... (Cmd/Ctrl + Enter to send)"
                      className="flex-1 px-4 py-2 border rounded-lg resize-none"
                      rows={3}
                    />
                    <button
                      onClick={sendReply}
                      disabled={sending || !replyText.trim()}
                      className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {sending ? '...' : 'Send'}
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
