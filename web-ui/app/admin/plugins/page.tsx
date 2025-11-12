'use client'

import { useState, useEffect } from 'react'
import { Plus, Download, Upload, Package, CheckCircle, XCircle, AlertTriangle, Search } from 'lucide-react'

interface Plugin {
  name: string
  version: string
  description: string
  category: string
  author: string
  status: 'active' | 'inactive' | 'error'
  dependencies: string[]
  agents_count: number
  skills_count: number
  tools_count: number
  installed_at: string
}

export default function PluginRegistryPage() {
  const [plugins, setPlugins] = useState<Plugin[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('all')
  const [showAddModal, setShowAddModal] = useState(false)

  useEffect(() => {
    loadPlugins()
  }, [])

  const loadPlugins = async () => {
    try {
      // TODO: Implement actual API call
      // const response = await fetch(`${API_BASE}/api/admin/plugins`)
      // const data = await response.json()

      // Mock data
      const mockPlugins: Plugin[] = [
        {
          name: 'core-agents',
          version: '3.0.0',
          description: 'Core agent functionality',
          category: 'core',
          author: 'AI Assistant Team',
          status: 'active',
          dependencies: [],
          agents_count: 10,
          skills_count: 15,
          tools_count: 8,
          installed_at: '2025-01-01'
        },
        {
          name: 'development-agents',
          version: '1.2.0',
          description: 'Software development agents',
          category: 'development',
          author: 'Dev Team',
          status: 'active',
          dependencies: ['core-agents'],
          agents_count: 25,
          skills_count: 30,
          tools_count: 12,
          installed_at: '2025-01-15'
        },
        {
          name: 'financial-agents',
          version: '1.0.0',
          description: 'Financial analysis agents',
          category: 'finance',
          author: 'Finance Team',
          status: 'active',
          dependencies: ['core-agents'],
          agents_count: 8,
          skills_count: 10,
          tools_count: 5,
          installed_at: '2025-02-01'
        }
      ]

      setPlugins(mockPlugins)
      setLoading(false)
    } catch (error) {
      console.error('Failed to load plugins:', error)
      setLoading(false)
    }
  }

  const categories = ['all', ...Array.from(new Set(plugins.map(p => p.category)))]
  const filteredPlugins = plugins.filter(p => {
    const matchesSearch = p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         p.description.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesCategory = selectedCategory === 'all' || p.category === selectedCategory
    return matchesSearch && matchesCategory
  })

  const togglePluginStatus = async (pluginName: string) => {
    // TODO: Implement actual API call
    setPlugins(plugins.map(p => 
      p.name === pluginName 
        ? { ...p, status: p.status === 'active' ? 'inactive' : 'active' }
        : p
    ))
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-8 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading plugins...</p>
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
              <Package className="text-blue-600" size={40} />
              Plugin Registry
            </h1>
            <p className="text-gray-600 mt-2">
              Manage plugins, agents, skills, and tools
            </p>
          </div>
          <div className="flex gap-3">
            <button className="px-4 py-2 bg-white text-gray-700 rounded-lg font-semibold hover:shadow-md transition-all flex items-center gap-2 border border-gray-300">
              <Download size={20} />
              Export
            </button>
            <button className="px-4 py-2 bg-white text-gray-700 rounded-lg font-semibold hover:shadow-md transition-all flex items-center gap-2 border border-gray-300">
              <Upload size={20} />
              Import
            </button>
            <button 
              onClick={() => setShowAddModal(true)}
              className="px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-semibold hover:shadow-lg transition-all flex items-center gap-2"
            >
              <Plus size={20} />
              Add Plugin
            </button>
          </div>
        </div>

        {/* Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-blue-500">
            <p className="text-gray-600 text-sm">Total Plugins</p>
            <p className="text-3xl font-bold text-gray-900">{plugins.length}</p>
            <p className="text-sm text-gray-500 mt-1">
              {plugins.filter(p => p.status === 'active').length} active
            </p>
          </div>

          <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-purple-500">
            <p className="text-gray-600 text-sm">Total Agents</p>
            <p className="text-3xl font-bold text-gray-900">
              {plugins.reduce((sum, p) => sum + p.agents_count, 0)}
            </p>
            <p className="text-sm text-gray-500 mt-1">across all plugins</p>
          </div>

          <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-green-500">
            <p className="text-gray-600 text-sm">Total Skills</p>
            <p className="text-3xl font-bold text-gray-900">
              {plugins.reduce((sum, p) => sum + p.skills_count, 0)}
            </p>
            <p className="text-sm text-gray-500 mt-1">registered skills</p>
          </div>

          <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-yellow-500">
            <p className="text-gray-600 text-sm">Total Tools</p>
            <p className="text-3xl font-bold text-gray-900">
              {plugins.reduce((sum, p) => sum + p.tools_count, 0)}
            </p>
            <p className="text-sm text-gray-500 mt-1">available tools</p>
          </div>
        </div>

        {/* Search and Filters */}
        <div className="bg-white rounded-xl shadow-md p-6 mb-6">
          <div className="flex gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
              <input
                type="text"
                placeholder="Search plugins..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <div className="flex gap-2">
              {categories.map(category => (
                <button
                  key={category}
                  onClick={() => setSelectedCategory(category)}
                  className={`px-4 py-2 rounded-lg font-semibold transition-all ${
                    selectedCategory === category
                      ? 'bg-blue-600 text-white shadow-md'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {category.charAt(0).toUpperCase() + category.slice(1)}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Plugins Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredPlugins.map((plugin) => (
            <div
              key={plugin.name}
              className="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow"
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="text-lg font-bold text-gray-900 mb-1">{plugin.name}</h3>
                  <p className="text-sm text-gray-600">{plugin.description}</p>
                </div>
                <div className={`ml-4 p-2 rounded-lg ${
                  plugin.status === 'active' ? 'bg-green-100' :
                  plugin.status === 'inactive' ? 'bg-gray-100' :
                  'bg-red-100'
                }`}>
                  {plugin.status === 'active' ? (
                    <CheckCircle className="text-green-600" size={20} />
                  ) : plugin.status === 'inactive' ? (
                    <XCircle className="text-gray-600" size={20} />
                  ) : (
                    <AlertTriangle className="text-red-600" size={20} />
                  )}
                </div>
              </div>

              {/* Details */}
              <div className="space-y-2 mb-4">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Version:</span>
                  <span className="font-semibold text-gray-800">{plugin.version}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Category:</span>
                  <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs font-semibold">
                    {plugin.category}
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Author:</span>
                  <span className="font-semibold text-gray-800">{plugin.author}</span>
                </div>
              </div>

              {/* Counts */}
              <div className="grid grid-cols-3 gap-2 mb-4">
                <div className="bg-blue-50 rounded-lg p-2 text-center">
                  <p className="text-xs text-gray-600">Agents</p>
                  <p className="text-lg font-bold text-blue-600">{plugin.agents_count}</p>
                </div>
                <div className="bg-purple-50 rounded-lg p-2 text-center">
                  <p className="text-xs text-gray-600">Skills</p>
                  <p className="text-lg font-bold text-purple-600">{plugin.skills_count}</p>
                </div>
                <div className="bg-green-50 rounded-lg p-2 text-center">
                  <p className="text-xs text-gray-600">Tools</p>
                  <p className="text-lg font-bold text-green-600">{plugin.tools_count}</p>
                </div>
              </div>

              {/* Dependencies */}
              {plugin.dependencies.length > 0 && (
                <div className="mb-4">
                  <p className="text-xs text-gray-600 mb-1">Dependencies:</p>
                  <div className="flex flex-wrap gap-1">
                    {plugin.dependencies.map((dep, i) => (
                      <span key={i} className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">
                        {dep}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="flex gap-2">
                <button
                  onClick={() => togglePluginStatus(plugin.name)}
                  className={`flex-1 px-4 py-2 rounded-lg font-semibold transition-all ${
                    plugin.status === 'active'
                      ? 'bg-red-100 text-red-700 hover:bg-red-200'
                      : 'bg-green-100 text-green-700 hover:bg-green-200'
                  }`}
                >
                  {plugin.status === 'active' ? 'Deactivate' : 'Activate'}
                </button>
                <button className="px-4 py-2 bg-blue-100 text-blue-700 rounded-lg font-semibold hover:bg-blue-200 transition-all">
                  Configure
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Empty State */}
        {filteredPlugins.length === 0 && (
          <div className="bg-white rounded-xl shadow-md p-12 text-center">
            <Package className="mx-auto text-gray-400 mb-4" size={64} />
            <h3 className="text-xl font-bold text-gray-800 mb-2">No plugins found</h3>
            <p className="text-gray-600">
              {searchTerm ? 'Try adjusting your search criteria' : 'Add your first plugin to get started'}
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
