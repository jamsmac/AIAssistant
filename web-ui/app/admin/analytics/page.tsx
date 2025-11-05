'use client'

import { useState, useEffect } from 'react'
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import {
  TrendingUp,
  Users,
  Eye,
  MessageSquare,
  Share2,
  Heart,
  Calendar,
  Download,
  Filter
} from 'lucide-react'

export default function AdvancedAnalyticsDashboard() {
  const [loading, setLoading] = useState(true)
  const [timeRange, setTimeRange] = useState('7d')
  const [analytics, setAnalytics] = useState<any>(null)

  useEffect(() => {
    fetchAnalytics()
  }, [timeRange])

  const fetchAnalytics = async () => {
    try {
      // Fetch blog analytics
      const blogResponse = await fetch('/api/blog/analytics/overview')
      const blogData = await blogResponse.json()

      // Fetch agent analytics
      const agentResponse = await fetch('/api/fractal/system-status')
      const agentData = await agentResponse.json()

      setAnalytics({
        blog: blogData,
        agents: agentData,
      })
    } catch (error) {
      console.error('Failed to fetch analytics:', error)
    } finally {
      setLoading(false)
    }
  }

  const exportData = () => {
    const dataStr = JSON.stringify(analytics, null, 2)
    const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr)
    const exportFileDefaultName = `analytics_${new Date().toISOString()}.json`

    const linkElement = document.createElement('a')
    linkElement.setAttribute('href', dataUri)
    linkElement.setAttribute('download', exportFileDefaultName)
    linkElement.click()
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 p-8 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading analytics...</p>
        </div>
      </div>
    )
  }

  // Sample data for charts (replace with real data from API)
  const revenueData = [
    { month: 'Jan', revenue: 4000, views: 2400 },
    { month: 'Feb', revenue: 3000, views: 1398 },
    { month: 'Mar', revenue: 2000, views: 9800 },
    { month: 'Apr', revenue: 2780, views: 3908 },
    { month: 'May', revenue: 1890, views: 4800 },
    { month: 'Jun', revenue: 2390, views: 3800 },
  ]

  const categoryData = [
    { name: 'Technology', value: 35, color: '#3b82f6' },
    { name: 'Tutorial', value: 25, color: '#10b981' },
    { name: 'News', value: 20, color: '#f59e0b' },
    { name: 'Opinion', value: 15, color: '#8b5cf6' },
    { name: 'Other', value: 5, color: '#6b7280' },
  ]

  const trafficData = [
    { source: 'Direct', visitors: 4500 },
    { source: 'Google', visitors: 3200 },
    { source: 'Social', visitors: 2100 },
    { source: 'Referral', visitors: 1800 },
    { source: 'Email', visitors: 900 },
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              Advanced Analytics
            </h1>
            <p className="text-gray-600 mt-2">Comprehensive insights into your platform performance</p>
          </div>
          <div className="flex gap-3">
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="7d">Last 7 Days</option>
              <option value="30d">Last 30 Days</option>
              <option value="90d">Last 90 Days</option>
              <option value="1y">Last Year</option>
            </select>
            <button
              onClick={exportData}
              className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:shadow-lg"
            >
              <Download size={18} />
              Export
            </button>
          </div>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-blue-500">
            <div className="flex items-center justify-between mb-4">
              <Eye className="text-blue-500" size={24} />
              <span className="text-green-600 text-sm font-semibold flex items-center gap-1">
                <TrendingUp size={14} />
                +12.5%
              </span>
            </div>
            <p className="text-gray-600 text-sm">Total Views</p>
            <p className="text-3xl font-bold text-gray-800">{analytics?.blog?.total_views?.toLocaleString() || '0'}</p>
            <p className="text-xs text-gray-500 mt-1">vs previous period</p>
          </div>

          <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-green-500">
            <div className="flex items-center justify-between mb-4">
              <Users className="text-green-500" size={24} />
              <span className="text-green-600 text-sm font-semibold flex items-center gap-1">
                <TrendingUp size={14} />
                +8.3%
              </span>
            </div>
            <p className="text-gray-600 text-sm">Unique Visitors</p>
            <p className="text-3xl font-bold text-gray-800">12,456</p>
            <p className="text-xs text-gray-500 mt-1">vs previous period</p>
          </div>

          <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-purple-500">
            <div className="flex items-center justify-between mb-4">
              <Heart className="text-purple-500" size={24} />
              <span className="text-green-600 text-sm font-semibold flex items-center gap-1">
                <TrendingUp size={14} />
                +15.2%
              </span>
            </div>
            <p className="text-gray-600 text-sm">Engagement Rate</p>
            <p className="text-3xl font-bold text-gray-800">68.4%</p>
            <p className="text-xs text-gray-500 mt-1">vs previous period</p>
          </div>

          <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-yellow-500">
            <div className="flex items-center justify-between mb-4">
              <MessageSquare className="text-yellow-500" size={24} />
              <span className="text-green-600 text-sm font-semibold flex items-center gap-1">
                <TrendingUp size={14} />
                +22.1%
              </span>
            </div>
            <p className="text-gray-600 text-sm">Comments</p>
            <p className="text-3xl font-bold text-gray-800">1,284</p>
            <p className="text-xs text-gray-500 mt-1">vs previous period</p>
          </div>
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Views & Revenue Over Time */}
          <div className="bg-white rounded-xl shadow-md p-6">
            <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
              <TrendingUp size={20} />
              Views & Revenue Trend
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={revenueData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="views" stroke="#3b82f6" strokeWidth={2} name="Views" />
                <Line type="monotone" dataKey="revenue" stroke="#10b981" strokeWidth={2} name="Revenue" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Category Distribution */}
          <div className="bg-white rounded-xl shadow-md p-6">
            <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
              <Filter size={20} />
              Content by Category
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={categoryData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(entry: any) => `${entry.name}: ${(entry.percent * 100).toFixed(0)}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {categoryData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Traffic Sources */}
        <div className="bg-white rounded-xl shadow-md p-6 mb-8">
          <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
            <Share2 size={20} />
            Traffic Sources
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={trafficData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="source" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="visitors" fill="#3b82f6" name="Visitors" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Agent Performance */}
        {analytics?.agents && (
          <div className="bg-white rounded-xl shadow-md p-6 mb-8">
            <h3 className="text-xl font-bold text-gray-800 mb-4">Agent System Performance</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="p-4 bg-blue-50 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">Active Agents</p>
                <p className="text-2xl font-bold text-blue-600">{analytics.agents.agents?.total || 0}</p>
              </div>
              <div className="p-4 bg-green-50 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">Success Rate</p>
                <p className="text-2xl font-bold text-green-600">
                  {((analytics.agents.collective_memory?.success_rate || 0) * 100).toFixed(1)}%
                </p>
              </div>
              <div className="p-4 bg-purple-50 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">Memory Entries</p>
                <p className="text-2xl font-bold text-purple-600">
                  {analytics.agents.collective_memory?.total_entries || 0}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Top Performing Content */}
        <div className="bg-white rounded-xl shadow-md overflow-hidden">
          <div className="p-6 bg-gradient-to-r from-blue-600 to-purple-600 text-white">
            <h3 className="text-xl font-bold">Top Performing Content</h3>
            <p className="text-blue-100 text-sm mt-1">Your most popular posts this period</p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase">Title</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase">Views</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase">Likes</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase">Comments</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase">Shares</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {[1, 2, 3, 4, 5].map((i) => (
                  <tr key={i} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <p className="font-semibold text-gray-900">Sample Post Title {i}</p>
                      <p className="text-sm text-gray-500">Published on Jan {i}, 2025</p>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <Eye size={16} className="text-gray-400" />
                        <span className="font-semibold">{(5000 - i * 500).toLocaleString()}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <Heart size={16} className="text-gray-400" />
                        <span className="font-semibold">{(350 - i * 30).toLocaleString()}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <MessageSquare size={16} className="text-gray-400" />
                        <span className="font-semibold">{(89 - i * 10).toLocaleString()}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <Share2 size={16} className="text-gray-400" />
                        <span className="font-semibold">{(156 - i * 20).toLocaleString()}</span>
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
