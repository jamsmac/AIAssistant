'use client'

import { useState, useEffect } from 'react'
import { FileText, Search, Filter, Download, AlertCircle, CheckCircle, Info, XCircle } from 'lucide-react'

interface AuditLog {
  id: string
  timestamp: string
  user: string
  action: string
  resource: string
  details: string
  ip_address: string
  status: 'success' | 'failure' | 'warning' | 'info'
  category: string
}

export default function AuditLogsPage() {
  const [logs, setLogs] = useState<AuditLog[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [categoryFilter, setCategoryFilter] = useState<string>('all')

  useEffect(() => {
    loadLogs()
  }, [])

  const loadLogs = async () => {
    try {
      // Mock data
      const mockLogs: AuditLog[] = [
        {
          id: '1',
          timestamp: '2025-11-12 10:30:45',
          user: 'admin@example.com',
          action: 'Plugin Registered',
          resource: 'development-agents',
          details: 'Registered new plugin with 25 agents',
          ip_address: '192.168.1.100',
          status: 'success',
          category: 'plugin'
        },
        {
          id: '2',
          timestamp: '2025-11-12 10:25:12',
          user: 'admin@example.com',
          action: 'LLM Router Updated',
          resource: 'router-config',
          details: 'Updated model selection preferences',
          ip_address: '192.168.1.100',
          status: 'success',
          category: 'config'
        },
        {
          id: '3',
          timestamp: '2025-11-12 10:20:33',
          user: 'john@example.com',
          action: 'Login Failed',
          resource: 'auth',
          details: 'Invalid password attempt',
          ip_address: '192.168.1.105',
          status: 'failure',
          category: 'security'
        },
        {
          id: '4',
          timestamp: '2025-11-12 10:15:22',
          user: 'admin@example.com',
          action: 'User Role Changed',
          resource: 'user:john@example.com',
          details: 'Changed role from user to admin',
          ip_address: '192.168.1.100',
          status: 'warning',
          category: 'user'
        },
        {
          id: '5',
          timestamp: '2025-11-12 10:10:15',
          user: 'system',
          action: 'Backup Completed',
          resource: 'database',
          details: 'Automated daily backup successful',
          ip_address: 'localhost',
          status: 'success',
          category: 'system'
        },
        {
          id: '6',
          timestamp: '2025-11-12 10:05:08',
          user: 'jane@example.com',
          action: 'Skill Activated',
          resource: 'backend-development',
          details: 'Activated skill for task execution',
          ip_address: '192.168.1.110',
          status: 'info',
          category: 'skill'
        },
        {
          id: '7',
          timestamp: '2025-11-12 10:00:45',
          user: 'admin@example.com',
          action: 'API Key Updated',
          resource: 'anthropic-api',
          details: 'Updated Anthropic API key',
          ip_address: '192.168.1.100',
          status: 'warning',
          category: 'security'
        },
        {
          id: '8',
          timestamp: '2025-11-12 09:55:30',
          user: 'system',
          action: 'Cost Analysis',
          resource: 'llm-router',
          details: 'Monthly cost savings: $785.30 (77%)',
          ip_address: 'localhost',
          status: 'info',
          category: 'analytics'
        }
      ]

      setLogs(mockLogs)
      setLoading(false)
    } catch (error) {
      console.error('Failed to load logs:', error)
      setLoading(false)
    }
  }

  const categories = ['all', ...Array.from(new Set(logs.map(l => l.category)))]
  const statuses = ['all', 'success', 'failure', 'warning', 'info']

  const filteredLogs = logs.filter(log => {
    const matchesSearch = log.action.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         log.user.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         log.details.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesStatus = statusFilter === 'all' || log.status === statusFilter
    const matchesCategory = categoryFilter === 'all' || log.category === categoryFilter
    return matchesSearch && matchesStatus && matchesCategory
  })

  const exportLogs = () => {
    // TODO: Implement actual export
    alert('Export functionality (API integration pending)')
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="text-green-600" size={20} />
      case 'failure':
        return <XCircle className="text-red-600" size={20} />
      case 'warning':
        return <AlertCircle className="text-yellow-600" size={20} />
      case 'info':
        return <Info className="text-blue-600" size={20} />
      default:
        return <Info className="text-gray-600" size={20} />
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-8 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading audit logs...</p>
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
              <FileText className="text-blue-600" size={40} />
              Audit Logs
            </h1>
            <p className="text-gray-600 mt-2">
              Track all system activity and user actions
            </p>
          </div>
          <button
            onClick={exportLogs}
            className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-semibold hover:shadow-lg transition-all flex items-center gap-2"
          >
            <Download size={20} />
            Export Logs
          </button>
        </div>

        {/* Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-blue-500">
            <p className="text-gray-600 text-sm">Total Events</p>
            <p className="text-3xl font-bold text-gray-900">{logs.length}</p>
          </div>

          <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-green-500">
            <p className="text-gray-600 text-sm">Successful</p>
            <p className="text-3xl font-bold text-gray-900">
              {logs.filter(l => l.status === 'success').length}
            </p>
          </div>

          <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-red-500">
            <p className="text-gray-600 text-sm">Failures</p>
            <p className="text-3xl font-bold text-gray-900">
              {logs.filter(l => l.status === 'failure').length}
            </p>
          </div>

          <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-yellow-500">
            <p className="text-gray-600 text-sm">Warnings</p>
            <p className="text-3xl font-bold text-gray-900">
              {logs.filter(l => l.status === 'warning').length}
            </p>
          </div>
        </div>

        {/* Search and Filters */}
        <div className="bg-white rounded-xl shadow-md p-6 mb-6">
          <div className="space-y-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
              <input
                type="text"
                placeholder="Search logs..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <div className="flex gap-4">
              <div className="flex-1">
                <label className="block text-sm font-semibold text-gray-700 mb-2">Status</label>
                <div className="flex gap-2">
                  {statuses.map(status => (
                    <button
                      key={status}
                      onClick={() => setStatusFilter(status)}
                      className={`px-4 py-2 rounded-lg font-semibold transition-all text-sm ${
                        statusFilter === status
                          ? 'bg-blue-600 text-white shadow-md'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      }`}
                    >
                      {status.charAt(0).toUpperCase() + status.slice(1)}
                    </button>
                  ))}
                </div>
              </div>
              <div className="flex-1">
                <label className="block text-sm font-semibold text-gray-700 mb-2">Category</label>
                <div className="flex gap-2 flex-wrap">
                  {categories.map(category => (
                    <button
                      key={category}
                      onClick={() => setCategoryFilter(category)}
                      className={`px-4 py-2 rounded-lg font-semibold transition-all text-sm ${
                        categoryFilter === category
                          ? 'bg-purple-600 text-white shadow-md'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      }`}
                    >
                      {category.charAt(0).toUpperCase() + category.slice(1)}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Logs Table */}
        <div className="bg-white rounded-xl shadow-md overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase">Timestamp</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase">User</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase">Action</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase">Resource</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase">Details</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase">IP Address</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {filteredLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm text-gray-900 whitespace-nowrap">
                      {log.timestamp}
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-sm font-semibold text-gray-900">{log.user}</span>
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-sm font-semibold text-gray-900">{log.action}</span>
                    </td>
                    <td className="px-6 py-4">
                      <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs font-mono">
                        {log.resource}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-sm text-gray-600">{log.details}</span>
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-sm text-gray-600 font-mono">{log.ip_address}</span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        {getStatusIcon(log.status)}
                        <span className={`px-2 py-1 rounded text-xs font-semibold ${
                          log.status === 'success' ? 'bg-green-100 text-green-800' :
                          log.status === 'failure' ? 'bg-red-100 text-red-800' :
                          log.status === 'warning' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-blue-100 text-blue-800'
                        }`}>
                          {log.status}
                        </span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Empty State */}
        {filteredLogs.length === 0 && (
          <div className="bg-white rounded-xl shadow-md p-12 text-center mt-6">
            <FileText className="mx-auto text-gray-400 mb-4" size={64} />
            <h3 className="text-xl font-bold text-gray-800 mb-2">No logs found</h3>
            <p className="text-gray-600">Try adjusting your search criteria</p>
          </div>
        )}
      </div>
    </div>
  )
}
