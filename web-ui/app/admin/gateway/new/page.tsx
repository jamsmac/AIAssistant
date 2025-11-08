"use client";

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

const CONNECTION_TYPES = [
  { value: 'rest', label: 'REST API', icon: '🌐', description: 'Connect to external REST APIs' },
  { value: 'json', label: 'JSON', icon: '📄', description: 'Import data from JSON files or URLs' },
  { value: 'sql', label: 'SQL Database', icon: '🗄️', description: 'Connect to external databases' },
  { value: 'graphql', label: 'GraphQL', icon: '📊', description: 'Query GraphQL APIs' },
  { value: 'csv', label: 'CSV', icon: '📑', description: 'Import/export CSV data' },
  { value: 'webhook', label: 'Webhook', icon: '🔔', description: 'Receive real-time data' },
];

export default function NewConnectionPage() {
  const router = useRouter();
  const [name, setName] = useState('');
  const [type, setType] = useState('rest');
  const [description, setDescription] = useState('');
  const [config, setConfig] = useState({
    base_url: '',
    endpoint: '',
    method: 'GET',
    timeout: 30,
    retry_count: 3
  });
  const [credentials, setCredentials] = useState({
    auth_type: 'bearer',
    token: '',
    key_name: 'X-API-Key',
    key_value: ''
  });
  const [autoSync, setAutoSync] = useState(false);
  const [syncFrequency, setSyncFrequency] = useState('manual');
  const [saving, setSaving] = useState(false);

  const handleConfigChange = (key: string, value: any) => {
    setConfig(prev => ({ ...prev, [key]: value }));
  };

  const handleCredentialChange = (key: string, value: any) => {
    setCredentials(prev => ({ ...prev, [key]: value }));
  };

  const handleSave = async () => {
    if (!name || !type) {
      alert('Please provide a name and type');
      return;
    }

    setSaving(true);
    try {
      const payload = {
        name,
        type,
        description,
        config,
        credentials: credentials.token || credentials.key_value ? credentials : undefined,
        auto_sync: autoSync,
        sync_frequency: syncFrequency
      };

      const res = await fetch('/api/gateway/connections', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        router.push('/admin/gateway');
      } else {
        const error = await res.json();
        alert('Failed to create connection: ' + (error.detail || 'Unknown error'));
      }
    } catch (err) {
      console.error(err);
      alert('Error creating connection: ' + String(err));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <Link href="/admin/gateway" className="text-blue-600 hover:underline mb-4 inline-block">
            ← Back to Gateway
          </Link>
          <h1 className="text-3xl font-bold">Create New Connection</h1>
          <p className="text-gray-600 mt-1">Connect to an external data source</p>
        </div>

        <div className="bg-white rounded-lg shadow p-6 space-y-6">
          {/* Basic Info */}
          <div>
            <h2 className="text-lg font-semibold mb-4">Basic Information</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Connection Name *</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., JSONPlaceholder API, User Data Source"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Connection Type *</label>
                <div className="grid grid-cols-2 gap-3">
                  {CONNECTION_TYPES.map((ct) => (
                    <button
                      key={ct.value}
                      onClick={() => setType(ct.value)}
                      className={`p-4 border-2 rounded-lg text-left transition-colors ${
                        type === ct.value
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-3xl">{ct.icon}</span>
                        <div>
                          <p className="font-medium">{ct.label}</p>
                          <p className="text-xs text-gray-500">{ct.description}</p>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Description</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  rows={3}
                  placeholder="Describe this data source..."
                />
              </div>
            </div>
          </div>

          {/* Connection Config */}
          {type === 'rest' && (
            <div className="pt-6 border-t">
              <h2 className="text-lg font-semibold mb-4">REST API Configuration</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Base URL *</label>
                  <input
                    type="text"
                    value={config.base_url}
                    onChange={(e) => handleConfigChange('base_url', e.target.value)}
                    className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="https://api.example.com"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Endpoint</label>
                    <input
                      type="text"
                      value={config.endpoint}
                      onChange={(e) => handleConfigChange('endpoint', e.target.value)}
                      className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                      placeholder="/users"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">HTTP Method</label>
                    <select
                      value={config.method}
                      onChange={(e) => handleConfigChange('method', e.target.value)}
                      className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="GET">GET</option>
                      <option value="POST">POST</option>
                      <option value="PUT">PUT</option>
                      <option value="DELETE">DELETE</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Timeout (seconds)</label>
                    <input
                      type="number"
                      value={config.timeout}
                      onChange={(e) => handleConfigChange('timeout', parseInt(e.target.value))}
                      className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">Retry Count</label>
                    <input
                      type="number"
                      value={config.retry_count}
                      onChange={(e) => handleConfigChange('retry_count', parseInt(e.target.value))}
                      className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          {type === 'json' && (
            <div className="pt-6 border-t">
              <h2 className="text-lg font-semibold mb-4">JSON Configuration</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Source Type</label>
                  <select
                    value={config.source_type || 'url'}
                    onChange={(e) => handleConfigChange('source_type', e.target.value)}
                    className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="url">URL</option>
                    <option value="file">File Path</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">
                    {config.source_type === 'file' ? 'File Path' : 'URL'} *
                  </label>
                  <input
                    type="text"
                    value={config.source_path || ''}
                    onChange={(e) => handleConfigChange('source_path', e.target.value)}
                    className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder={
                      config.source_type === 'file'
                        ? '/path/to/data.json'
                        : 'https://example.com/data.json'
                    }
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Data Path (optional)</label>
                  <input
                    type="text"
                    value={config.data_path || ''}
                    onChange={(e) => handleConfigChange('data_path', e.target.value)}
                    className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="e.g., data.results or items"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Path to the actual data within the JSON (use dot notation)
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Authentication */}
          <div className="pt-6 border-t">
            <h2 className="text-lg font-semibold mb-4">Authentication (Optional)</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Auth Type</label>
                <select
                  value={credentials.auth_type}
                  onChange={(e) => handleCredentialChange('auth_type', e.target.value)}
                  className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="none">None</option>
                  <option value="bearer">Bearer Token</option>
                  <option value="api_key">API Key</option>
                  <option value="basic">Basic Auth</option>
                </select>
              </div>

              {credentials.auth_type === 'bearer' && (
                <div>
                  <label className="block text-sm font-medium mb-2">Bearer Token</label>
                  <input
                    type="password"
                    value={credentials.token}
                    onChange={(e) => handleCredentialChange('token', e.target.value)}
                    className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="your-bearer-token"
                  />
                </div>
              )}

              {credentials.auth_type === 'api_key' && (
                <>
                  <div>
                    <label className="block text-sm font-medium mb-2">Header Name</label>
                    <input
                      type="text"
                      value={credentials.key_name}
                      onChange={(e) => handleCredentialChange('key_name', e.target.value)}
                      className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                      placeholder="X-API-Key"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">API Key Value</label>
                    <input
                      type="password"
                      value={credentials.key_value}
                      onChange={(e) => handleCredentialChange('key_value', e.target.value)}
                      className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                      placeholder="your-api-key"
                    />
                  </div>
                </>
              )}

              {credentials.auth_type === 'basic' && (
                <>
                  <div>
                    <label className="block text-sm font-medium mb-2">Username</label>
                    <input
                      type="text"
                      value={credentials.username || ''}
                      onChange={(e) => handleCredentialChange('username', e.target.value)}
                      className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">Password</label>
                    <input
                      type="password"
                      value={credentials.password || ''}
                      onChange={(e) => handleCredentialChange('password', e.target.value)}
                      className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Sync Settings */}
          <div className="pt-6 border-t">
            <h2 className="text-lg font-semibold mb-4">Sync Settings</h2>
            <div className="space-y-4">
              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={autoSync}
                    onChange={(e) => setAutoSync(e.target.checked)}
                    className="w-4 h-4"
                  />
                  <span className="text-sm">Enable Auto-Sync</span>
                </label>
              </div>

              {autoSync && (
                <div>
                  <label className="block text-sm font-medium mb-2">Sync Frequency</label>
                  <select
                    value={syncFrequency}
                    onChange={(e) => setSyncFrequency(e.target.value)}
                    className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="manual">Manual</option>
                    <option value="hourly">Hourly</option>
                    <option value="daily">Daily</option>
                    <option value="weekly">Weekly</option>
                  </select>
                </div>
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center justify-between pt-6 border-t">
            <p className="text-sm text-gray-600">* Required fields</p>
            <div className="flex gap-3">
              <Link
                href="/admin/gateway"
                className="px-6 py-2 border rounded-lg hover:bg-gray-50"
              >
                Cancel
              </Link>
              <button
                onClick={handleSave}
                disabled={saving || !name || !type}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {saving ? 'Creating...' : 'Create Connection'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
