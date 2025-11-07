'use client';

import { useState, useEffect } from 'react';
import { Users, DollarSign, TrendingUp, TrendingDown, Coins, BarChart3, Loader2 } from 'lucide-react';
import Link from 'next/link';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('access_token');
}

async function fetchWithAuth(url: string) {
  const token = getAuthToken();
  if (!token) throw new Error('Not authenticated');

  const response = await fetch(url, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  return response.json();
}

export default function AdminCreditsPage() {
  const [analytics, setAnalytics] = useState<any>(null);
  const [users, setUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [analyticsData, usersData] = await Promise.all([
        fetchWithAuth(`${API_URL}/api/credits/admin/analytics`),
        fetchWithAuth(`${API_URL}/api/credits/admin/users?limit=10`)
      ]);

      setAnalytics(analyticsData);
      setUsers(usersData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 text-white flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-950 text-white p-8">
        <div className="max-w-7xl mx-auto">
          <div className="bg-red-900/20 border border-red-800 rounded-lg p-6">
            <p className="text-red-400">{error}</p>
            <button
              onClick={loadData}
              className="mt-4 px-4 py-2 bg-red-800 hover:bg-red-700 rounded-lg"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            Credit System Admin
          </h1>
          <p className="text-gray-400">
            Manage credit packages, users, and view analytics
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-gradient-to-br from-blue-900/50 to-blue-800/30 rounded-xl p-6 border border-blue-700">
            <div className="flex items-center justify-between mb-4">
              <Users className="w-8 h-8 text-blue-400" />
              <div className="text-xs text-blue-400 uppercase tracking-wide">Total Users</div>
            </div>
            <div className="text-3xl font-bold">{analytics?.total_users?.toLocaleString()}</div>
            <div className="text-sm text-gray-400 mt-2">
              {analytics?.users_with_balance} with balance
            </div>
          </div>

          <div className="bg-gradient-to-br from-yellow-900/50 to-yellow-800/30 rounded-xl p-6 border border-yellow-700">
            <div className="flex items-center justify-between mb-4">
              <Coins className="w-8 h-8 text-yellow-400" />
              <div className="text-xs text-yellow-400 uppercase tracking-wide">Total Balance</div>
            </div>
            <div className="text-3xl font-bold">{analytics?.total_balance?.toLocaleString()}</div>
            <div className="text-sm text-gray-400 mt-2">
              Credits in circulation
            </div>
          </div>

          <div className="bg-gradient-to-br from-green-900/50 to-green-800/30 rounded-xl p-6 border border-green-700">
            <div className="flex items-center justify-between mb-4">
              <TrendingUp className="w-8 h-8 text-green-400" />
              <div className="text-xs text-green-400 uppercase tracking-wide">Purchased</div>
            </div>
            <div className="text-3xl font-bold">{analytics?.total_purchased?.toLocaleString()}</div>
            <div className="text-sm text-gray-400 mt-2">
              Total credits sold
            </div>
          </div>

          <div className="bg-gradient-to-br from-purple-900/50 to-purple-800/30 rounded-xl p-6 border border-purple-700">
            <div className="flex items-center justify-between mb-4">
              <DollarSign className="w-8 h-8 text-purple-400" />
              <div className="text-xs text-purple-400 uppercase tracking-wide">Revenue</div>
            </div>
            <div className="text-3xl font-bold">
              ${analytics?.estimated_revenue_usd?.toFixed(2)}
            </div>
            <div className="text-sm text-gray-400 mt-2">
              Estimated total
            </div>
          </div>
        </div>

        {/* Usage Stats */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
            <div className="flex items-center gap-2 mb-4">
              <BarChart3 className="w-6 h-6 text-blue-400" />
              <h2 className="text-xl font-semibold">Usage Statistics</h2>
            </div>
            <div className="space-y-4">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-gray-400">Total Purchased</span>
                  <span className="font-semibold text-green-400">
                    {analytics?.total_purchased?.toLocaleString()}
                  </span>
                </div>
                <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-green-500"
                    style={{
                      width: `${(analytics?.total_purchased / (analytics?.total_purchased + analytics?.total_spent)) * 100}%`
                    }}
                  />
                </div>
              </div>
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-gray-400">Total Spent</span>
                  <span className="font-semibold text-red-400">
                    {analytics?.total_spent?.toLocaleString()}
                  </span>
                </div>
                <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-red-500"
                    style={{
                      width: `${(analytics?.total_spent / (analytics?.total_purchased + analytics?.total_spent)) * 100}%`
                    }}
                  />
                </div>
              </div>
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-gray-400">Remaining Balance</span>
                  <span className="font-semibold text-yellow-400">
                    {analytics?.total_balance?.toLocaleString()}
                  </span>
                </div>
                <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-yellow-500"
                    style={{
                      width: `${(analytics?.total_balance / analytics?.total_purchased) * 100}%`
                    }}
                  />
                </div>
              </div>
            </div>
          </div>

          <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
            <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
            <div className="space-y-3">
              <Link
                href="/admin/credits/packages"
                className="block px-4 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
              >
                Manage Credit Packages
              </Link>
              <Link
                href="/admin/credits/users"
                className="block px-4 py-3 bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors"
              >
                Manage User Credits
              </Link>
              <Link
                href="/admin/credits/pricing"
                className="block px-4 py-3 bg-green-600 hover:bg-green-700 rounded-lg transition-colors"
              >
                Configure Model Pricing
              </Link>
            </div>
          </div>
        </div>

        {/* Recent Users */}
        <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
          <div className="p-6 border-b border-gray-700">
            <h2 className="text-xl font-semibold">Recent Users</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-900">
                <tr>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">ID</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">Email</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">Role</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">Balance</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">Purchased</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">Spent</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {users.map((user) => (
                  <tr key={user.id} className="hover:bg-gray-750">
                    <td className="px-6 py-4 text-gray-300">{user.id}</td>
                    <td className="px-6 py-4 text-gray-300">{user.email}</td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 rounded text-xs font-semibold ${
                        user.role === 'superadmin' ? 'bg-red-900/30 text-red-400' :
                        user.role === 'admin' ? 'bg-purple-900/30 text-purple-400' :
                        'bg-gray-700 text-gray-300'
                      }`}>
                        {user.role}
                      </span>
                    </td>
                    <td className="px-6 py-4 font-semibold text-yellow-400">
                      {user.balance.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 text-green-400">
                      {user.total_purchased.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 text-red-400">
                      {user.total_spent.toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="p-4 border-t border-gray-700">
            <Link
              href="/admin/credits/users"
              className="text-blue-400 hover:text-blue-300 text-sm"
            >
              View all users →
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
