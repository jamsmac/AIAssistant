'use client';

import { useEffect, useState, useCallback } from 'react';
import { Mail, HardDrive, MessageCircle, CheckCircle, XCircle, AlertCircle, Loader2, RefreshCw, Settings, X } from 'lucide-react';
import { useApi } from '@/lib/useApi';
import { useToast } from '@/components/ui/Toast';

interface Integration {
  type: 'gmail' | 'google_drive' | 'telegram';
  name: string;
  description: string;
  icon: string;
  requires_oauth: boolean;
  status: 'connected' | 'disconnected' | 'error';
  last_sync: string | null;
}

interface TelegramConnectData {
  integration_type: string;
  bot_token: string;
}

export default function IntegrationsPage() {
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Modal states
  const [telegramModalOpen, setTelegramModalOpen] = useState(false);
  const [telegramBotToken, setTelegramBotToken] = useState('');
  const [telegramConnecting, setTelegramConnecting] = useState(false);

  const [disconnectModalOpen, setDisconnectModalOpen] = useState(false);
  const [disconnectTarget, setDisconnectTarget] = useState<Integration | null>(null);
  const [disconnecting, setDisconnecting] = useState(false);

  const [settingsModalOpen, setSettingsModalOpen] = useState(false);
  const [settingsTarget, setSettingsTarget] = useState<Integration | null>(null);

  const [testingConnection, setTestingConnection] = useState<string | null>(null);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  // Fetch integrations from API
  const fetchIntegrations = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        setError('Not authenticated');
        setLoading(false);
        return;
      }

      const response = await fetch(`${API_URL}/api/integrations`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch integrations');
      }

      const data = await response.json();
      setIntegrations(data);
      setError('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load integrations');
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial fetch
  useEffect(() => {
    fetchIntegrations();
  }, [fetchIntegrations]);

  // Auto-refresh every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      fetchIntegrations();
    }, 30000);

    return () => clearInterval(interval);
  }, [fetchIntegrations]);

  // Handle OAuth callback via postMessage
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      if (event.data.type === 'oauth-success') {
        showToast('Integration connected successfully', 'success');
        fetchIntegrations();
      } else if (event.data.type === 'oauth-error') {
        showToast('Failed to connect integration', 'error');
      }
    };

    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, [fetchIntegrations]);

  // Show toast notification
  const showToast = (message: string, type: 'success' | 'error') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  // Get icon component for integration
  const getIcon = (iconName: string) => {
    const iconProps = { className: 'w-12 h-12', strokeWidth: 1.5 };
    switch (iconName) {
      case 'mail':
        return <Mail {...iconProps} />;
      case 'hard-drive':
        return <HardDrive {...iconProps} />;
      case 'message-circle':
        return <MessageCircle {...iconProps} />;
      default:
        return <AlertCircle {...iconProps} />;
    }
  };

  // Get status badge
  const getStatusBadge = (status: Integration['status']) => {
    switch (status) {
      case 'connected':
        return (
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-green-500/20 text-green-400 text-sm font-medium">
            <CheckCircle className="w-4 h-4" />
            Connected
          </div>
        );
      case 'error':
        return (
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-red-500/20 text-red-400 text-sm font-medium">
            <XCircle className="w-4 h-4" />
            Error
          </div>
        );
      case 'disconnected':
      default:
        return (
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-gray-500/20 text-gray-400 text-sm font-medium">
            <AlertCircle className="w-4 h-4" />
            Disconnected
          </div>
        );
    }
  };

  // Handle connect button click
  const handleConnect = async (integration: Integration) => {
    if (integration.type === 'telegram') {
      // Show Telegram bot token modal
      setTelegramModalOpen(true);
      setTelegramBotToken('');
    } else {
      // Handle OAuth flow
      await handleOAuthConnect(integration.type);
    }
  };

  // Handle OAuth connection
  const handleOAuthConnect = async (integrationType: string) => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        showToast('Not authenticated', 'error');
        return;
      }

      const response = await fetch(`${API_URL}/api/integrations/connect`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ integration_type: integrationType }),
      });

      if (!response.ok) {
        throw new Error('Failed to initiate OAuth');
      }

      const data = await response.json();

      if (data.oauth_url) {
        // Open OAuth popup
        const width = 600;
        const height = 700;
        const left = window.screenX + (window.outerWidth - width) / 2;
        const top = window.screenY + (window.outerHeight - height) / 2;

        window.open(
          data.oauth_url,
          'oauth-popup',
          `width=${width},height=${height},left=${left},top=${top}`
        );
      }
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Failed to connect', 'error');
    }
  };

  // Handle Telegram bot token submission
  const handleTelegramConnect = async () => {
    if (!telegramBotToken.trim()) {
      showToast('Please enter a bot token', 'error');
      return;
    }

    setTelegramConnecting(true);

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        showToast('Not authenticated', 'error');
        return;
      }

      const response = await fetch(`${API_URL}/api/integrations/connect`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          integration_type: 'telegram',
          bot_token: telegramBotToken,
        } as TelegramConnectData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to connect Telegram');
      }

      showToast('Telegram bot connected successfully', 'success');
      setTelegramModalOpen(false);
      setTelegramBotToken('');
      fetchIntegrations();
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Failed to connect', 'error');
    } finally {
      setTelegramConnecting(false);
    }
  };

  // Handle disconnect
  const handleDisconnect = async () => {
    if (!disconnectTarget) return;

    setDisconnecting(true);

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        showToast('Not authenticated', 'error');
        return;
      }

      const response = await fetch(
        `${API_URL}/api/integrations/disconnect?integration_type=${disconnectTarget.type}`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to disconnect integration');
      }

      showToast(`${disconnectTarget.name} disconnected successfully`, 'success');
      setDisconnectModalOpen(false);
      setDisconnectTarget(null);
      fetchIntegrations();
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Failed to disconnect', 'error');
    } finally {
      setDisconnecting(false);
    }
  };

  // Handle test connection
  const handleTestConnection = async (integration: Integration) => {
    setTestingConnection(integration.type);

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        showToast('Not authenticated', 'error');
        return;
      }

      const response = await fetch(
        `${API_URL}/api/integrations/test?integration_type=${integration.type}`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to test connection');
      }

      const data = await response.json();

      if (data.success) {
        showToast('Connection successful', 'success');
      } else {
        showToast(`Connection failed: ${data.message}`, 'error');
      }
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Test failed', 'error');
    } finally {
      setTestingConnection(null);
    }
  };

  // Open settings modal
  const handleSettings = (integration: Integration) => {
    setSettingsTarget(integration);
    setSettingsModalOpen(true);
  };

  // Format last sync time
  const formatLastSync = (lastSync: string | null) => {
    if (!lastSync) return 'Never';

    const date = new Date(lastSync);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} minutes ago`;

    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours} hours ago`;

    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays} days ago`;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 text-white flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white p-8">
      {/* Header */}
      <div className="max-w-6xl mx-auto mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">Integrations</h1>
            <p className="text-gray-400">Connect external services to extend functionality</p>
          </div>
          <button
            onClick={fetchIntegrations}
            className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>
      </div>

      {/* Error message */}
      {error && (
        <div className="max-w-6xl mx-auto mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400">
          {error}
        </div>
      )}

      {/* Integrations Grid */}
      <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-6">
        {integrations.map((integration) => (
          <div
            key={integration.type}
            className="bg-gray-900 rounded-xl p-6 border border-gray-800 hover:border-gray-700 transition-all hover:shadow-lg hover:shadow-blue-500/10 group"
          >
            {/* Icon and Status */}
            <div className="flex items-start justify-between mb-4">
              <div className="p-3 bg-gray-800 rounded-lg text-blue-400 group-hover:bg-gradient-to-br group-hover:from-blue-500 group-hover:to-purple-600 group-hover:text-white transition-all">
                {getIcon(integration.icon)}
              </div>
              {getStatusBadge(integration.status)}
            </div>

            {/* Name and Description */}
            <h3 className="text-xl font-semibold mb-2">{integration.name}</h3>
            <p className="text-gray-400 text-sm mb-4">{integration.description}</p>

            {/* Last Sync */}
            {integration.status === 'connected' && (
              <div className="text-xs text-gray-500 mb-4">
                Last synced: {formatLastSync(integration.last_sync)}
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-2 mt-4">
              {integration.status === 'connected' ? (
                <>
                  <button
                    onClick={() => handleTestConnection(integration)}
                    disabled={testingConnection === integration.type}
                    className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    {testingConnection === integration.type ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : null}
                    Test Connection
                  </button>
                  <button
                    onClick={() => handleSettings(integration)}
                    className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors"
                  >
                    <Settings className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => {
                      setDisconnectTarget(integration);
                      setDisconnectModalOpen(true);
                    }}
                    className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg font-medium transition-colors"
                  >
                    Disconnect
                  </button>
                </>
              ) : (
                <button
                  onClick={() => handleConnect(integration)}
                  className="w-full px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 rounded-lg font-medium transition-all"
                >
                  Connect
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Telegram Bot Token Modal */}
      {telegramModalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-900 rounded-xl p-6 max-w-md w-full border border-gray-800">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-semibold">Connect Telegram Bot</h3>
              <button
                onClick={() => setTelegramModalOpen(false)}
                className="text-gray-400 hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="mb-6">
              <p className="text-gray-400 text-sm mb-4">
                To connect a Telegram bot, you need to get a bot token from @BotFather:
              </p>
              <ol className="text-gray-400 text-sm space-y-2 mb-4 list-decimal list-inside">
                <li>Open Telegram and search for @BotFather</li>
                <li>Send the command /newbot (or use existing bot with /token)</li>
                <li>Follow the instructions to create a bot</li>
                <li>Copy the bot token and paste it below</li>
              </ol>

              <label className="block text-sm font-medium mb-2">Bot Token</label>
              <input
                type="text"
                value={telegramBotToken}
                onChange={(e) => setTelegramBotToken(e.target.value)}
                placeholder="123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
                className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:border-blue-500 transition-colors"
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !telegramConnecting) {
                    handleTelegramConnect();
                  }
                }}
              />
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => setTelegramModalOpen(false)}
                disabled={telegramConnecting}
                className="flex-1 px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleTelegramConnect}
                disabled={telegramConnecting || !telegramBotToken.trim()}
                className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {telegramConnecting && <Loader2 className="w-4 h-4 animate-spin" />}
                Save
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Disconnect Confirmation Modal */}
      {disconnectModalOpen && disconnectTarget && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-900 rounded-xl p-6 max-w-md w-full border border-gray-800">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-semibold">Disconnect {disconnectTarget.name}?</h3>
              <button
                onClick={() => setDisconnectModalOpen(false)}
                className="text-gray-400 hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <p className="text-gray-400 mb-6">
              Are you sure you want to disconnect {disconnectTarget.name}? This will revoke access and remove all stored credentials.
            </p>

            <div className="flex gap-3">
              <button
                onClick={() => setDisconnectModalOpen(false)}
                disabled={disconnecting}
                className="flex-1 px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleDisconnect}
                disabled={disconnecting}
                className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {disconnecting && <Loader2 className="w-4 h-4 animate-spin" />}
                Disconnect
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Settings Modal */}
      {settingsModalOpen && settingsTarget && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-900 rounded-xl p-6 max-w-md w-full border border-gray-800">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-semibold">{settingsTarget.name} Settings</h3>
              <button
                onClick={() => setSettingsModalOpen(false)}
                className="text-gray-400 hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4 mb-6">
              {/* Status */}
              <div>
                <label className="block text-sm font-medium mb-2 text-gray-400">Status</label>
                {getStatusBadge(settingsTarget.status)}
              </div>

              {/* Last Sync */}
              <div>
                <label className="block text-sm font-medium mb-2 text-gray-400">Last Sync</label>
                <p className="text-white">{formatLastSync(settingsTarget.last_sync)}</p>
              </div>

              {/* Permissions */}
              <div>
                <label className="block text-sm font-medium mb-2 text-gray-400">Permissions</label>
                <div className="space-y-1">
                  {settingsTarget.type === 'gmail' && (
                    <>
                      <div className="flex items-center gap-2 text-sm">
                        <CheckCircle className="w-4 h-4 text-green-400" />
                        <span>Send emails</span>
                      </div>
                      <div className="flex items-center gap-2 text-sm">
                        <CheckCircle className="w-4 h-4 text-green-400" />
                        <span>Read emails</span>
                      </div>
                    </>
                  )}
                  {settingsTarget.type === 'google_drive' && (
                    <div className="flex items-center gap-2 text-sm">
                      <CheckCircle className="w-4 h-4 text-green-400" />
                      <span>Manage files</span>
                    </div>
                  )}
                  {settingsTarget.type === 'telegram' && (
                    <div className="flex items-center gap-2 text-sm">
                      <CheckCircle className="w-4 h-4 text-green-400" />
                      <span>Send messages</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Usage Stats (placeholder) */}
              <div>
                <label className="block text-sm font-medium mb-2 text-gray-400">Usage Today</label>
                <p className="text-white">0 API calls</p>
              </div>
            </div>

            <div className="flex gap-3">
              {settingsTarget.requires_oauth && (
                <button
                  onClick={() => {
                    setSettingsModalOpen(false);
                    handleConnect(settingsTarget);
                  }}
                  className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg font-medium transition-colors"
                >
                  Re-authenticate
                </button>
              )}
              <button
                onClick={() => {
                  setSettingsModalOpen(false);
                  setDisconnectTarget(settingsTarget);
                  setDisconnectModalOpen(true);
                }}
                className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg font-medium transition-colors"
              >
                Revoke Access
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Toast Notification */}
      {toast && (
        <div
          className={`fixed bottom-8 right-8 px-6 py-4 rounded-lg shadow-lg border animate-in slide-in-from-bottom-5 z-50 ${
            toast.type === 'success'
              ? 'bg-green-500/10 border-green-500/20 text-green-400'
              : 'bg-red-500/10 border-red-500/20 text-red-400'
          }`}
        >
          <div className="flex items-center gap-3">
            {toast.type === 'success' ? (
              <CheckCircle className="w-5 h-5" />
            ) : (
              <XCircle className="w-5 h-5" />
            )}
            <span className="font-medium">{toast.message}</span>
          </div>
        </div>
      )}
    </div>
  );
}
