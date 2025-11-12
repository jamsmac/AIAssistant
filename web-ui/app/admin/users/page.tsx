'use client'

import { useState, useEffect } from 'react'
import { Users, Plus, Shield, Edit, Trash2, Search, Filter } from 'lucide-react'

interface User {
  id: string
  email: string
  name: string
  role: 'superadmin' | 'admin' | 'user'
  status: 'active' | 'suspended' | 'pending'
  created_at: string
  last_login: string
  tasks_count: number
  credits_used: number
}

export default function UserManagementPage() {
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [roleFilter, setRoleFilter] = useState<string>('all')

  useEffect(() => {
    loadUsers()
  }, [])

  const loadUsers = async () => {
    try {
      // Mock data
      const mockUsers: User[] = [
        {
          id: '1',
          email: 'admin@example.com',
          name: 'Super Admin',
          role: 'superadmin',
          status: 'active',
          created_at: '2025-01-01',
          last_login: '2025-11-12 10:30',
          tasks_count: 1523,
          credits_used: 45000
        },
        {
          id: '2',
          email: 'john@example.com',
          name: 'John Doe',
          role: 'admin',
          status: 'active',
          created_at: '2025-02-15',
          last_login: '2025-11-11 15:20',
          tasks_count: 892,
          credits_used: 28000
        },
        {
          id: '3',
          email: 'jane@example.com',
          name: 'Jane Smith',
          role: 'user',
          status: 'active',
          created_at: '2025-03-20',
          last_login: '2025-11-10 09:45',
          tasks_count: 345,
          credits_used: 12000
        },
        {
          id: '4',
          email: 'suspended@example.com',
          name: 'Suspended User',
          role: 'user',
          status: 'suspended',
          created_at: '2025-04-10',
          last_login: '2025-10-15 14:30',
          tasks_count: 23,
          credits_used: 1500
        }
      ]

      setUsers(mockUsers)
      setLoading(false)
    } catch (error) {
      console.error('Failed to load users:', error)
      setLoading(false)
    }
  }

  const filteredUsers = users.filter(user => {
    const matchesSearch = user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         user.name.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesRole = roleFilter === 'all' || user.role === roleFilter
    return matchesSearch && matchesRole
  })

  const deleteUser = async (userId: string) => {
    if (!confirm('Delete this user?')) return
    setUsers(users.filter(u => u.id !== userId))
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-8 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading users...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 flex items-center gap-3">
              <Users className="text-blue-600" size={40} />
              User Management
            </h1>
            <p className="text-gray-600 mt-2">
              Manage users, roles, and permissions
            </p>
          </div>
          <button className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-semibold hover:shadow-lg transition-all flex items-center gap-2">
            <Plus size={20} />
            Add User
          </button>
        </div>

        {/* Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-blue-500">
            <p className="text-gray-600 text-sm">Total Users</p>
            <p className="text-3xl font-bold text-gray-900">{users.length}</p>
          </div>

          <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-green-500">
            <p className="text-gray-600 text-sm">Active Users</p>
            <p className="text-3xl font-bold text-gray-900">
              {users.filter(u => u.status === 'active').length}
            </p>
          </div>

          <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-purple-500">
            <p className="text-gray-600 text-sm">Admins</p>
            <p className="text-3xl font-bold text-gray-900">
              {users.filter(u => u.role === 'admin' || u.role === 'superadmin').length}
            </p>
          </div>

          <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-red-500">
            <p className="text-gray-600 text-sm">Suspended</p>
            <p className="text-3xl font-bold text-gray-900">
              {users.filter(u => u.status === 'suspended').length}
            </p>
          </div>
        </div>

        {/* Search and Filters */}
        <div className="bg-white rounded-xl shadow-md p-6 mb-6">
          <div className="flex gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
              <input
                type="text"
                placeholder="Search users..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <div className="flex gap-2">
              {['all', 'superadmin', 'admin', 'user'].map(role => (
                <button
                  key={role}
                  onClick={() => setRoleFilter(role)}
                  className={`px-4 py-2 rounded-lg font-semibold transition-all ${
                    roleFilter === role
                      ? 'bg-blue-600 text-white shadow-md'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {role.charAt(0).toUpperCase() + role.slice(1)}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Users Table */}
        <div className="bg-white rounded-xl shadow-md overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase">User</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase">Role</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase">Status</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase">Tasks</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase">Credits</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase">Last Login</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {filteredUsers.map((user) => (
                  <tr key={user.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div>
                        <p className="font-semibold text-gray-900">{user.name}</p>
                        <p className="text-sm text-gray-600">{user.email}</p>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        {user.role === 'superadmin' && <Shield size={16} className="text-red-600" />}
                        {user.role === 'admin' && <Shield size={16} className="text-blue-600" />}
                        <span className={`px-2 py-1 rounded text-xs font-semibold ${
                          user.role === 'superadmin' ? 'bg-red-100 text-red-800' :
                          user.role === 'admin' ? 'bg-blue-100 text-blue-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {user.role}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                        user.status === 'active' ? 'bg-green-100 text-green-800' :
                        user.status === 'suspended' ? 'bg-red-100 text-red-800' :
                        'bg-yellow-100 text-yellow-800'
                      }`}>
                        {user.status}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className="font-semibold text-gray-900">{user.tasks_count}</span>
                    </td>
                    <td className="px-6 py-4">
                      <span className="font-semibold text-gray-900">{user.credits_used.toLocaleString()}</span>
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-sm text-gray-600">{user.last_login}</span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex gap-2">
                        <button className="p-2 hover:bg-blue-100 rounded-lg transition-colors">
                          <Edit size={16} className="text-blue-600" />
                        </button>
                        <button 
                          onClick={() => deleteUser(user.id)}
                          className="p-2 hover:bg-red-100 rounded-lg transition-colors"
                        >
                          <Trash2 size={16} className="text-red-600" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}
