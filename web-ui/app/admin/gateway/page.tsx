"use client";

import { useState, useEffect } from 'react';
import Link from 'next/link';

interface Connection {
  id: string;
  name: string;
  type: string;
  description: string;
  status: string;
  last_sync: string | null;
  auto_sync: boolean;
  sync_frequency: string;
  error_count: number;
  last_error: string | null;
  created_at: string;
}

interface GatewayStats {
  connections: {
    total: number;
    active: number;
    errors: number;
    total_error_count: number;
  };
  syncs_24h: {
    total: number;
    successful: number;
    records_fetched: number;
    avg_duration_ms: number;
  };
}

export default function GatewayAdminPage() {
  const [connections, setConnections] = useState<Connection[]>([]);
  const [stats, setStats] = useState<GatewayStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState<string>('');
  const [filterStatus, setFilterStatus] = useState<string>('');

  useEffect(() => {
    fetchData();
  }, [filterType, filterStatus]);

  const fetchData = async () => {
    try {
      setLoading(true);

      // Build query params
      const params = new URLSearchParams();
      if (filterType) params.append('type', filterType);
      if (filterStatus) params.append('status', filterStatus);

      // Fetch connections
      const connectionsRes = await fetch(`/api/gateway/connections?${params}`);
      if (connectionsRes.ok) {
        const data = await connectionsRes.json();
        setConnections(data);
      }

      // Fetch stats
      const statsRes = await fetch('/api/gateway/stats');
      if (statsRes.ok) {
        const statsData = await statsRes.json();
        setStats(statsData);
      }
    } catch (err) {
      console.error('Failed to fetch gateway data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleTestConnection = async (connectionId: string) => {
    try {
      const res = await fetch(`/api/gateway/connections/${connectionId}/test`, {
        method: 'POST'
      });
      const data = await res.json();

      if (data.success) {
        alert('Connection test successful!');
      } else {
        alert('Connection test failed: ' + data.message);
      }

      // Refresh connections
      fetchData();
    } catch (err) {
      console.error('Test failed:', err);
      alert('Test failed: ' + String(err));
    }
  };

  const handleSync = async (connectionId: string) => {
    try {
      const res = await fetch(`/api/gateway/connections/${connectionId}/sync`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });
      const data = await res.json();

      if (data.success) {
        alert(`Sync successful! Fetched ${data.records_fetched} records in ${data.duration_ms}ms`);
      } else {
        alert('Sync failed: ' + data.error_message);
      }

      // Refresh connections
      fetchData();
    } catch (err) {
      console.error('Sync failed:', err);
      alert('Sync failed: ' + String(err));
    }
  };

  const handleDelete = async (connectionId: string, name: string) => {
    if (!confirm(`Are you sure you want to delete connection "${name}"?`)) {
      return;
    }

    try {
      const res = await fetch(`/api/gateway/connections/${connectionId}`, {
        method: 'DELETE'
      });

      if (res.ok) {
        alert('Connection deleted successfully');
        fetchData();
      } else {
        alert('Failed to delete connection');
      }
    } catch (err) {
      console.error('Delete failed:', err);
      alert('Delete failed: ' + String(err));
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'text-green-600 bg-green-100';
      case 'inactive':
        return 'text-gray-600 bg-gray-100';
      case 'error':
        return 'text-red-600 bg-red-100';
      case 'testing':
        return 'text-blue-600 bg-blue-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'rest':
        return '🌐';
      case 'json':
        return '📄';
      case 'sql':
        return '🗄️';
      case 'graphql':
        return '📊';
      case 'csv':
        return '📑';
      case 'webhook':
        return '🔔';
      default:
        return '🔌';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-1/4 mb-8"></div>
            <div className="grid grid-cols-4 gap-6 mb-8">
              {[1,2,3,4].map(i => <div key={i} className="h-32 bg-gray-200 rounded"></div>)}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">API Gateway</h1>
            <p className="text-gray-600 mt-1">Manage data source connections</p>
          </div>
          <Link
            href="/admin/gateway/new"
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
          >
            + New Connection
          </Link>
        </div>

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="bg-white rounded-lg p-6 shadow-sm border">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-600">Total Connections</span>
                <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                  <span className="text-blue-600 text-lg">🔌</span>
                </div>
              </div>
              <p className="text-3xl font-bold text-gray-900">{stats.connections.total}</p>
              <p className="text-xs text-green-600 mt-1">
                {stats.connections.active} active
              </p>
            </div>

            <div className="bg-white rounded-lg p-6 shadow-sm border">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-600">Syncs (24h)</span>
                <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
                  <span className="text-green-600 text-lg">🔄</span>
                </div>
              </div>
              <p className="text-3xl font-bold text-gray-900">{stats.syncs_24h.total}</p>
              <p className="text-xs text-green-600 mt-1">
                {stats.syncs_24h.successful} successful
              </p>
            </div>

            <div className="bg-white rounded-lg p-6 shadow-sm border">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-600">Records Fetched</span>
                <div className="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center">
                  <span className="text-purple-600 text-lg">📥</span>
                </div>
              </div>
              <p className="text-3xl font-bold text-gray-900">
                {stats.syncs_24h.records_fetched.toLocaleString()}
              </p>
              <p className="text-xs text-gray-600 mt-1">Last 24 hours</p>
            </div>

            <div className="bg-white rounded-lg p-6 shadow-sm border">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-600">Avg Duration</span>
                <div className="w-10 h-10 bg-yellow-100 rounded-full flex items-center justify-center">
                  <span className="text-yellow-600 text-lg">⚡</span>
                </div>
              </div>
              <p className="text-3xl font-bold text-gray-900">
                {stats.syncs_24h.avg_duration_ms.toFixed(0)}
              </p>
              <p className="text-xs text-gray-600 mt-1">milliseconds</p>
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="bg-white rounded-lg p-4 shadow-sm border mb-6">
          <div className="flex gap-4">
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Filter by Type
              </label>
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Types</option>
                <option value="rest">REST API</option>
                <option value="json">JSON</option>
                <option value="sql">SQL Database</option>
                <option value="graphql">GraphQL</option>
                <option value="csv">CSV</option>
                <option value="webhook">Webhook</option>
              </select>
            </div>

            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Filter by Status
              </label>
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Statuses</option>
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
                <option value="error">Error</option>
                <option value="testing">Testing</option>
              </select>
            </div>
          </div>
        </div>

        {/* Connections Table */}
        <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Connection
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Last Sync
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {connections.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-12 text-center text-gray-500">
                    <div className="text-6xl mb-4">🔌</div>
                    <p className="text-lg font-medium">No connections yet</p>
                    <p className="text-sm mt-2">Create your first data source connection</p>
                  </td>
                </tr>
              ) : (
                connections.map((conn) => (
                  <tr key={conn.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div>
                        <p className="font-medium text-gray-900">{conn.name}</p>
                        <p className="text-sm text-gray-500">{conn.description || 'No description'}</p>
                        {conn.error_count > 0 && (
                          <p className="text-xs text-red-600 mt-1">
                            {conn.error_count} error{conn.error_count > 1 ? 's' : ''}
                            {conn.last_error && `: ${conn.last_error.substring(0, 50)}...`}
                          </p>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <span className="text-2xl">{getTypeIcon(conn.type)}</span>
                        <span className="text-sm font-medium capitalize">{conn.type}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-3 py-1 text-xs font-medium rounded-full ${getStatusColor(conn.status)}`}>
                        {conn.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {conn.last_sync
                        ? new Date(conn.last_sync).toLocaleString()
                        : 'Never'}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleTestConnection(conn.id)}
                          className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
                        >
                          Test
                        </button>
                        <button
                          onClick={() => handleSync(conn.id)}
                          className="px-3 py-1 text-sm bg-green-100 text-green-700 rounded hover:bg-green-200"
                        >
                          Sync
                        </button>
                        <Link
                          href={`/admin/gateway/${conn.id}`}
                          className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                        >
                          View
                        </Link>
                        <button
                          onClick={() => handleDelete(conn.id, conn.name)}
                          className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200"
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Info Card */}
        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="font-semibold text-blue-900 mb-3">📚 About API Gateway</h3>
          <p className="text-sm text-blue-800 mb-3">
            The API Gateway allows you to connect external data sources to your platform:
          </p>
          <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
            <li><strong>REST API:</strong> Connect to external REST APIs</li>
            <li><strong>JSON:</strong> Import data from JSON files or URLs</li>
            <li><strong>SQL:</strong> Connect to external databases</li>
            <li><strong>GraphQL:</strong> Query GraphQL APIs</li>
            <li><strong>CSV:</strong> Import/export CSV data</li>
            <li><strong>Webhooks:</strong> Receive real-time data from external services</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
