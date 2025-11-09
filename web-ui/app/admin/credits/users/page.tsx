'use client';

import { useState, useEffect } from 'react';
import { Search, Gift, Loader2, ChevronLeft } from 'lucide-react';
import Link from 'next/link';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Auth token now comes from httpOnly cookies automatically
// No need to manually get or send token
async function fetchWithAuth(url: string, options?: RequestInit) {
  const response = await fetch(url, {
    ...options,
    credentials: 'include', // Include httpOnly cookies
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  return response.json();
}

export default function AdminUsersPage() {
  const [users, setUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [grantingTo, setGrantingTo] = useState<number | null>(null);
  const [grantAmount, setGrantAmount] = useState('1000');

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchWithAuth(`${API_URL}/api/credits/admin/users?limit=100`);
      setUsers(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const grantCredits = async (userId: number) => {
    try {
      const amount = parseInt(grantAmount);
      if (isNaN(amount) || amount <= 0) {
        alert('Please enter a valid amount');
        return;
      }

      await fetchWithAuth(`${API_URL}/api/credits/admin/grant-bonus`, {
        method: 'POST',
        body: JSON.stringify({
          user_id: userId,
          amount: amount,
          description: 'Admin bonus'
        }),
      });

      setGrantingTo(null);
      await loadUsers();
      alert(`Successfully granted ${amount} credits!`);
    } catch (err) {
      alert('Failed to grant credits: ' + (err instanceof Error ? err.message : 'Unknown error'));
    }
  };

  const filteredUsers = users.filter(user =>
    user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.id.toString().includes(searchTerm)
  );

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 text-white flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <Link
            href="/admin/credits"
            className="text-sm text-gray-400 hover:text-gray-300 mb-2 inline-flex items-center gap-1"
          >
            <ChevronLeft className="w-4 h-4" />
            Back to Admin
          </Link>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            User Credit Management
          </h1>
          <p className="text-gray-400 mt-2">
            View and manage user credit balances
          </p>
        </div>

        {/* Search */}
        <div className="mb-6">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search by email or ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-12 pr-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {error && (
          <div className="mb-6 bg-red-900/20 border border-red-800 rounded-lg p-4 text-red-400">
            {error}
          </div>
        )}

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <div className="text-sm text-gray-400">Total Users</div>
            <div className="text-2xl font-bold">{users.length}</div>
          </div>
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <div className="text-sm text-gray-400">Users with Balance</div>
            <div className="text-2xl font-bold">
              {users.filter(u => u.balance > 0).length}
            </div>
          </div>
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <div className="text-sm text-gray-400">Showing</div>
            <div className="text-2xl font-bold">{filteredUsers.length}</div>
          </div>
        </div>

        {/* Users Table */}
        <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-900 border-b border-gray-700">
                <tr>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">ID</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">Email</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">Role</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">Balance</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">Purchased</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">Spent</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {filteredUsers.map((user) => (
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
                    <td className="px-6 py-4">
                      <span className={`font-semibold ${
                        user.balance > 1000 ? 'text-green-400' :
                        user.balance > 100 ? 'text-yellow-400' :
                        'text-red-400'
                      }`}>
                        {user.balance.toLocaleString()}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-green-400">
                      {user.total_purchased.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 text-red-400">
                      {user.total_spent.toLocaleString()}
                    </td>
                    <td className="px-6 py-4">
                      {grantingTo === user.id ? (
                        <div className="flex items-center gap-2">
                          <input
                            type="number"
                            value={grantAmount}
                            onChange={(e) => setGrantAmount(e.target.value)}
                            className="w-24 px-2 py-1 bg-gray-700 border border-gray-600 rounded text-sm"
                            placeholder="Amount"
                          />
                          <button
                            onClick={() => grantCredits(user.id)}
                            className="px-3 py-1 bg-green-600 hover:bg-green-700 rounded text-sm"
                          >
                            Grant
                          </button>
                          <button
                            onClick={() => setGrantingTo(null)}
                            className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-sm"
                          >
                            Cancel
                          </button>
                        </div>
                      ) : (
                        <button
                          onClick={() => setGrantingTo(user.id)}
                          className="flex items-center gap-1 px-3 py-1 bg-blue-600 hover:bg-blue-700 rounded text-sm"
                        >
                          <Gift className="w-4 h-4" />
                          Grant Credits
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
