'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { 
  LayoutDashboard, Users, Settings, Shield, Activity, 
  TrendingUp, Zap, Database, DollarSign, AlertCircle,
  CheckCircle, Clock, Cpu, Network, FileText
} from 'lucide-react'

interface DashboardStats {
  system: {
    uptime: string
    version: string
    status: 'healthy' | 'warning' | 'error'
  }
  users: {
    total: number
    active_today: number
    new_this_week: number
  }
  agents: {
    total: number
    active: number
    tasks_today: number
    success_rate: number
  }
  v3_components: {
    plugins: number
    skills: number
    active_skills: number
    llm_cost_saved: number
    context_saved: number
  }
  performance: {
    avg_response_time: number
    requests_today: number
    errors_today: number
    uptime_percentage: number
  }
}

export default function AdminDashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)
  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  useEffect(() => {
    loadDashboardStats()
  }, [])

  const loadDashboardStats = async () => {
    try {
      // TODO: Implement actual API call
      // const response = await fetch(`${API_BASE}/api/admin/dashboard`)
      // const data = await response.json()
      
      // Mock data for now
      const mockStats: DashboardStats = {
        system: {
          uptime: '15 days, 7 hours',
          version: '3.0.0',
          status: 'healthy'
        },
        users: {
          total: 1247,
          active_today: 89,
          new_this_week: 23
        },
        agents: {
          total: 84,
          active: 42,
          tasks_today: 1523,
          success_rate: 94.5
        },
        v3_components: {
          plugins: 12,
          skills: 45,
          active_skills: 18,
          llm_cost_saved: 77,
          context_saved: 90
        },
        performance: {
          avg_response_time: 245,
          requests_today: 8934,
          errors_today: 12,
          uptime_percentage: 99.8
        }
      }

      setStats(mockStats)
      setLoading(false)
    } catch (error) {
      console.error('Failed to load dashboard stats:', error)
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-8 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 flex items-center gap-3">
            <Shield className="text-blue-600" size={40} />
            Superadmin Dashboard
          </h1>
          <p className="text-gray-600 mt-2">
            AI Assistant Platform v{stats?.system.version} - Complete system overview and management
          </p>
        </div>

        {/* System Status Banner */}
        {stats && (
          <div className={`mb-8 rounded-xl shadow-lg p-6 ${
            stats.system.status === 'healthy' ? 'bg-gradient-to-r from-green-500 to-emerald-500' :
            stats.system.status === 'warning' ? 'bg-gradient-to-r from-yellow-500 to-orange-500' :
            'bg-gradient-to-r from-red-500 to-pink-500'
          } text-white`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                {stats.system.status === 'healthy' ? (
                  <CheckCircle size={48} />
                ) : stats.system.status === 'warning' ? (
                  <AlertCircle size={48} />
                ) : (
                  <AlertCircle size={48} />
                )}
                <div>
                  <h2 className="text-2xl font-bold">System Status: {stats.system.status.toUpperCase()}</h2>
                  <p className="text-white/90">Uptime: {stats.system.uptime} | {stats.performance.uptime_percentage}% availability</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm text-white/80">Version</p>
                <p className="text-3xl font-bold">{stats.system.version}</p>
              </div>
            </div>
          </div>
        )}

        {/* Quick Stats Grid */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {/* Users */}
            <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-blue-500">
              <div className="flex items-center justify-between mb-4">
                <Users className="text-blue-500" size={32} />
                <span className="text-xs font-semibold text-blue-600 bg-blue-100 px-2 py-1 rounded">
                  +{stats.users.new_this_week} this week
                </span>
              </div>
              <p className="text-gray-600 text-sm">Total Users</p>
              <p className="text-3xl font-bold text-gray-900">{stats.users.total.toLocaleString()}</p>
              <p className="text-sm text-gray-500 mt-2">{stats.users.active_today} active today</p>
            </div>

            {/* Agents */}
            <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-purple-500">
              <div className="flex items-center justify-between mb-4">
                <Cpu className="text-purple-500" size={32} />
                <span className="text-xs font-semibold text-purple-600 bg-purple-100 px-2 py-1 rounded">
                  {stats.agents.active} active
                </span>
              </div>
              <p className="text-gray-600 text-sm">Total Agents</p>
              <p className="text-3xl font-bold text-gray-900">{stats.agents.total}</p>
              <p className="text-sm text-gray-500 mt-2">{stats.agents.tasks_today} tasks today</p>
            </div>

            {/* Performance */}
            <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-green-500">
              <div className="flex items-center justify-between mb-4">
                <Activity className="text-green-500" size={32} />
                <span className="text-xs font-semibold text-green-600 bg-green-100 px-2 py-1 rounded">
                  {stats.agents.success_rate}% success
                </span>
              </div>
              <p className="text-gray-600 text-sm">Avg Response Time</p>
              <p className="text-3xl font-bold text-gray-900">{stats.performance.avg_response_time}ms</p>
              <p className="text-sm text-gray-500 mt-2">{stats.performance.requests_today.toLocaleString()} requests today</p>
            </div>

            {/* Cost Savings */}
            <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-yellow-500">
              <div className="flex items-center justify-between mb-4">
                <DollarSign className="text-yellow-500" size={32} />
                <span className="text-xs font-semibold text-yellow-600 bg-yellow-100 px-2 py-1 rounded">
                  v3.0 savings
                </span>
              </div>
              <p className="text-gray-600 text-sm">LLM Cost Reduction</p>
              <p className="text-3xl font-bold text-gray-900">{stats.v3_components.llm_cost_saved}%</p>
              <p className="text-sm text-gray-500 mt-2">{stats.v3_components.context_saved}% context saved</p>
            </div>
          </div>
        )}

        {/* v3.0 Components Status */}
        {stats && (
          <div className="bg-white rounded-xl shadow-md p-6 mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-2">
              <Zap className="text-blue-600" size={28} />
              v3.0 Components Status
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <Database className="text-blue-600" size={24} />
                  <CheckCircle className="text-green-600" size={20} />
                </div>
                <p className="text-sm text-gray-600">Plugin Registry</p>
                <p className="text-2xl font-bold text-gray-900">{stats.v3_components.plugins}</p>
                <p className="text-xs text-gray-500 mt-1">plugins registered</p>
              </div>

              <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <Zap className="text-purple-600" size={24} />
                  <CheckCircle className="text-green-600" size={20} />
                </div>
                <p className="text-sm text-gray-600">Skills Registry</p>
                <p className="text-2xl font-bold text-gray-900">{stats.v3_components.skills}</p>
                <p className="text-xs text-gray-500 mt-1">{stats.v3_components.active_skills} active</p>
              </div>

              <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <TrendingUp className="text-green-600" size={24} />
                  <CheckCircle className="text-green-600" size={20} />
                </div>
                <p className="text-sm text-gray-600">LLM Router</p>
                <p className="text-2xl font-bold text-gray-900">{stats.v3_components.llm_cost_saved}%</p>
                <p className="text-xs text-gray-500 mt-1">cost reduction</p>
              </div>

              <div className="bg-gradient-to-br from-yellow-50 to-yellow-100 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <Network className="text-yellow-600" size={24} />
                  <CheckCircle className="text-green-600" size={20} />
                </div>
                <p className="text-sm text-gray-600">Agent Catalog</p>
                <p className="text-2xl font-bold text-gray-900">{stats.agents.total}</p>
                <p className="text-xs text-gray-500 mt-1">specialized agents</p>
              </div>
            </div>
          </div>
        )}

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          <Link href="/admin/plugins">
            <div className="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow cursor-pointer border-2 border-transparent hover:border-blue-500">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                  <Database className="text-blue-600" size={24} />
                </div>
                <div>
                  <h3 className="font-bold text-gray-900">Plugin Registry</h3>
                  <p className="text-sm text-gray-600">Manage plugins and agents</p>
                </div>
              </div>
            </div>
          </Link>

          <Link href="/admin/llm-router">
            <div className="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow cursor-pointer border-2 border-transparent hover:border-purple-500">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                  <TrendingUp className="text-purple-600" size={24} />
                </div>
                <div>
                  <h3 className="font-bold text-gray-900">LLM Router</h3>
                  <p className="text-sm text-gray-600">Configure model routing</p>
                </div>
              </div>
            </div>
          </Link>

          <Link href="/admin/skills-manager">
            <div className="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow cursor-pointer border-2 border-transparent hover:border-green-500">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                  <Zap className="text-green-600" size={24} />
                </div>
                <div>
                  <h3 className="font-bold text-gray-900">Skills Manager</h3>
                  <p className="text-sm text-gray-600">Manage progressive skills</p>
                </div>
              </div>
            </div>
          </Link>

          <Link href="/admin/users">
            <div className="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow cursor-pointer border-2 border-transparent hover:border-yellow-500">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center">
                  <Users className="text-yellow-600" size={24} />
                </div>
                <div>
                  <h3 className="font-bold text-gray-900">User Management</h3>
                  <p className="text-sm text-gray-600">Manage users and roles</p>
                </div>
              </div>
            </div>
          </Link>

          <Link href="/admin/settings">
            <div className="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow cursor-pointer border-2 border-transparent hover:border-red-500">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center">
                  <Settings className="text-red-600" size={24} />
                </div>
                <div>
                  <h3 className="font-bold text-gray-900">System Settings</h3>
                  <p className="text-sm text-gray-600">Configure system</p>
                </div>
              </div>
            </div>
          </Link>

          <Link href="/admin/audit-logs">
            <div className="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow cursor-pointer border-2 border-transparent hover:border-indigo-500">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center">
                  <FileText className="text-indigo-600" size={24} />
                </div>
                <div>
                  <h3 className="font-bold text-gray-900">Audit Logs</h3>
                  <p className="text-sm text-gray-600">View system activity</p>
                </div>
              </div>
            </div>
          </Link>
        </div>

        {/* Recent Activity */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center gap-2">
            <Clock className="text-blue-600" size={28} />
            Recent Activity
          </h2>
          <div className="space-y-3">
            {[
              { action: 'New plugin registered', user: 'admin@example.com', time: '2 minutes ago', type: 'success' },
              { action: 'LLM Router configuration updated', user: 'admin@example.com', time: '15 minutes ago', type: 'info' },
              { action: 'User role changed', user: 'admin@example.com', time: '1 hour ago', type: 'warning' },
              { action: 'System backup completed', user: 'system', time: '3 hours ago', type: 'success' },
            ].map((activity, i) => (
              <div key={i} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full ${
                    activity.type === 'success' ? 'bg-green-500' :
                    activity.type === 'warning' ? 'bg-yellow-500' :
                    'bg-blue-500'
                  }`}></div>
                  <div>
                    <p className="font-semibold text-gray-900">{activity.action}</p>
                    <p className="text-sm text-gray-600">by {activity.user}</p>
                  </div>
                </div>
                <p className="text-sm text-gray-500">{activity.time}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
