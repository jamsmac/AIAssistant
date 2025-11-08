'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

interface Channel {
  id: string;
  type: string;
  name: string;
  config: any;
  status: string;
  assigned_agent_id?: string;
  total_messages_received: number;
  total_messages_sent: number;
  auto_response_enabled: boolean;
  created_at: string;
  updated_at: string;
}

export default function ChannelsManagement() {
  const router = useRouter();
  const [channels, setChannels] = useState<Channel[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [channelType, setChannelType] = useState('');

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    type: '',
    botToken: '',
    oauthToken: '',
    accessToken: '',
    phoneNumberId: '',
    autoResponse: false
  });

  useEffect(() => {
    fetchChannels();
  }, []);

  const fetchChannels = async () => {
    try {
      const res = await fetch('/api/communications/channels');
      const data = await res.json();
      setChannels(data);
    } catch (error) {
      console.error('Error fetching channels:', error);
    } finally {
      setLoading(false);
    }
  };

  const testChannel = async (channelId: string) => {
    try {
      const res = await fetch(`/api/communications/channels/${channelId}/test`, {
        method: 'POST'
      });
      const data = await res.json();
      if (data.success) {
        alert('✅ Connection test successful!');
        fetchChannels();
      } else {
        alert('❌ Connection test failed');
      }
    } catch (error) {
      alert('❌ Connection test failed: ' + error);
    }
  };

  const deleteChannel = async (channelId: string, channelName: string) => {
    if (!confirm(`Delete channel "${channelName}"?`)) return;

    try {
      const res = await fetch(`/api/communications/channels/${channelId}`, {
        method: 'DELETE'
      });
      if (res.ok) {
        fetchChannels();
      }
    } catch (error) {
      alert('Failed to delete channel: ' + error);
    }
  };

  const handleAddChannel = async () => {
    if (!formData.name || !formData.type) {
      alert('Please fill in all required fields');
      return;
    }

    const credentials: any = {};
    const config: any = {};

    if (formData.type === 'telegram') {
      if (!formData.botToken) {
        alert('Please provide Telegram bot token');
        return;
      }
      credentials.bot_token = formData.botToken;
    } else if (formData.type === 'gmail') {
      if (!formData.oauthToken) {
        alert('Please authenticate with Gmail first');
        return;
      }
      credentials.oauth_token = JSON.parse(formData.oauthToken);
    } else if (formData.type === 'whatsapp') {
      if (!formData.accessToken || !formData.phoneNumberId) {
        alert('Please provide WhatsApp access token and phone number ID');
        return;
      }
      credentials.access_token = formData.accessToken;
      config.phone_number_id = formData.phoneNumberId;
      config.api_version = 'v18.0';
    }

    try {
      const res = await fetch('/api/communications/channels', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: formData.name,
          type: formData.type,
          config,
          credentials,
          auto_response_enabled: formData.autoResponse
        })
      });

      if (res.ok) {
        alert('✅ Channel added successfully!');
        setShowAddModal(false);
        setFormData({ name: '', type: '', botToken: '', oauthToken: '', accessToken: '', phoneNumberId: '', autoResponse: false });
        fetchChannels();
      } else {
        const error = await res.json();
        alert('❌ Failed to add channel: ' + error.detail);
      }
    } catch (error) {
      alert('❌ Failed to add channel: ' + error);
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

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'inactive': return 'bg-gray-100 text-gray-800';
      case 'error': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading channels...</p>
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
              <h1 className="text-2xl font-bold text-gray-900">⚙️ Communication Channels</h1>
              <p className="text-sm text-gray-600">Manage messaging platform integrations</p>
            </div>
            <div className="flex gap-2">
              <Link
                href="/admin/inbox"
                className="px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded-lg"
              >
                ← Back to Inbox
              </Link>
              <button
                onClick={() => setShowAddModal(true)}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                + Add Channel
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Channels Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {channels.length === 0 ? (
            <div className="col-span-full text-center py-12">
              <div className="text-6xl mb-4">📭</div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">No channels configured</h3>
              <p className="text-gray-600 mb-4">Add your first messaging channel to get started</p>
              <button
                onClick={() => setShowAddModal(true)}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                + Add Channel
              </button>
            </div>
          ) : (
            channels.map(channel => (
              <div key={channel.id} className="bg-white rounded-lg shadow p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <span className="text-3xl">{getChannelIcon(channel.type)}</span>
                    <div>
                      <h3 className="font-bold text-gray-900">{channel.name}</h3>
                      <p className="text-sm text-gray-600 capitalize">{channel.type}</p>
                    </div>
                  </div>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(channel.status)}`}>
                    {channel.status}
                  </span>
                </div>

                <div className="space-y-2 mb-4">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Messages Received:</span>
                    <span className="font-semibold">{channel.total_messages_received}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Messages Sent:</span>
                    <span className="font-semibold">{channel.total_messages_sent}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Auto-Response:</span>
                    <span className={channel.auto_response_enabled ? 'text-green-600' : 'text-gray-400'}>
                      {channel.auto_response_enabled ? '✓ Enabled' : '✗ Disabled'}
                    </span>
                  </div>
                </div>

                <div className="text-xs text-gray-500 mb-4">
                  Created: {new Date(channel.created_at).toLocaleDateString()}
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={() => testChannel(channel.id)}
                    className="flex-1 px-3 py-2 bg-green-50 text-green-700 rounded hover:bg-green-100 text-sm"
                  >
                    Test
                  </button>
                  <button
                    onClick={() => deleteChannel(channel.id, channel.name)}
                    className="flex-1 px-3 py-2 bg-red-50 text-red-700 rounded hover:bg-red-100 text-sm"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Add Channel Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
            <div className="p-6">
              <h2 className="text-xl font-bold mb-4">Add Communication Channel</h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Channel Name *
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-3 py-2 border rounded-lg"
                    placeholder="My Telegram Bot"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Channel Type *
                  </label>
                  <select
                    value={formData.type}
                    onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                    className="w-full px-3 py-2 border rounded-lg"
                  >
                    <option value="">Select type...</option>
                    <option value="telegram">💬 Telegram</option>
                    <option value="gmail">✉️ Gmail</option>
                    <option value="whatsapp">📱 WhatsApp Business</option>
                    <option value="slack">💼 Slack (Coming Soon)</option>
                    <option value="discord">🎮 Discord (Coming Soon)</option>
                  </select>
                </div>

                {formData.type === 'telegram' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Bot Token *
                    </label>
                    <input
                      type="password"
                      value={formData.botToken}
                      onChange={(e) => setFormData({ ...formData, botToken: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg font-mono text-sm"
                      placeholder="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Get your bot token from @BotFather on Telegram
                    </p>
                  </div>
                )}

                {formData.type === 'gmail' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      OAuth Token (JSON) *
                    </label>
                    <textarea
                      value={formData.oauthToken}
                      onChange={(e) => setFormData({ ...formData, oauthToken: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg font-mono text-xs"
                      rows={4}
                      placeholder='{"token": "...", "refresh_token": "...", ...}'
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Authenticate with Google OAuth first and paste the token JSON
                    </p>
                  </div>
                )}

                {formData.type === 'whatsapp' && (
                  <div className="space-y-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Access Token *
                      </label>
                      <input
                        type="password"
                        value={formData.accessToken}
                        onChange={(e) => setFormData({ ...formData, accessToken: e.target.value })}
                        className="w-full px-3 py-2 border rounded-lg font-mono text-sm"
                        placeholder="EAABsC..."
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        Get from Meta Business Suite → WhatsApp → API Setup
                      </p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Phone Number ID *
                      </label>
                      <input
                        type="text"
                        value={formData.phoneNumberId}
                        onChange={(e) => setFormData({ ...formData, phoneNumberId: e.target.value })}
                        className="w-full px-3 py-2 border rounded-lg font-mono text-sm"
                        placeholder="123456789012345"
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        Found in Meta Business Suite → WhatsApp → Phone Numbers
                      </p>
                    </div>
                  </div>
                )}

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="autoResponse"
                    checked={formData.autoResponse}
                    onChange={(e) => setFormData({ ...formData, autoResponse: e.target.checked })}
                    className="mr-2"
                  />
                  <label htmlFor="autoResponse" className="text-sm text-gray-700">
                    Enable auto-response rules
                  </label>
                </div>
              </div>

              <div className="flex gap-2 mt-6">
                <button
                  onClick={() => {
                    setShowAddModal(false);
                    setFormData({ name: '', type: '', botToken: '', oauthToken: '', accessToken: '', phoneNumberId: '', autoResponse: false });
                  }}
                  className="flex-1 px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  onClick={handleAddChannel}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Add Channel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
