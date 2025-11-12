'use client'

import { useState, useEffect } from 'react'
import { TrendingUp, DollarSign, Zap, Settings, BarChart3, Save } from 'lucide-react'

interface RouterStats {
  total_requests: number
  simple_tasks: number
  moderate_tasks: number
  complex_tasks: number
  expert_tasks: number
  estimated_cost: number
  estimated_cost_saved: number
  cost_savings_percentage: number
}

interface ModelConfig {
  name: string
  enabled: boolean
  max_tokens: number
  temperature: number
  cost_per_1k_input: number
  cost_per_1k_output: number
  priority: number
}

export default function LLMRouterPage() {
  const [stats, setStats] = useState<RouterStats | null>(null)
  const [models, setModels] = useState<ModelConfig[]>([])
  const [loading, setLoading] = useState(true)
  const [preferCostEfficiency, setPreferCostEfficiency] = useState(true)

  useEffect(() => {
    loadRouterData()
  }, [])

  const loadRouterData = async () => {
    try {
      // TODO: Implement actual API calls
      // Mock data
      const mockStats: RouterStats = {
        total_requests: 15234,
        simple_tasks: 8500,
        moderate_tasks: 4200,
        complex_tasks: 2100,
        expert_tasks: 434,
        estimated_cost: 234.50,
        estimated_cost_saved: 785.30,
        cost_savings_percentage: 77
      }

      const mockModels: ModelConfig[] = [
        {
          name: 'haiku',
          enabled: true,
          max_tokens: 4096,
          temperature: 0.7,
          cost_per_1k_input: 0.00025,
          cost_per_1k_output: 0.00125,
          priority: 1
        },
        {
          name: 'sonnet',
          enabled: true,
          max_tokens: 8192,
          temperature: 0.7,
          cost_per_1k_input: 0.003,
          cost_per_1k_output: 0.015,
          priority: 2
        },
        {
          name: 'opus',
          enabled: true,
          max_tokens: 8192,
          temperature: 0.7,
          cost_per_1k_input: 0.015,
          cost_per_1k_output: 0.075,
          priority: 3
        },
        {
          name: 'gpt-4',
          enabled: true,
          max_tokens: 8192,
          temperature: 0.7,
          cost_per_1k_input: 0.03,
          cost_per_1k_output: 0.06,
          priority: 4
        },
        {
          name: 'gpt-3.5-turbo',
          enabled: true,
          max_tokens: 4096,
          temperature: 0.7,
          cost_per_1k_input: 0.0005,
          cost_per_1k_output: 0.0015,
          priority: 1
        },
        {
          name: 'gemini',
          enabled: true,
          max_tokens: 8192,
          temperature: 0.7,
          cost_per_1k_input: 0.000125,
          cost_per_1k_output: 0.000375,
          priority: 1
        }
      ]

      setStats(mockStats)
      setModels(mockModels)
      setLoading(false)
    } catch (error) {
      console.error('Failed to load router data:', error)
      setLoading(false)
    }
  }

  const saveConfiguration = async () => {
    // TODO: Implement actual API call
    alert('Configuration saved! (API integration pending)')
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-8 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading router configuration...</p>
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
              <TrendingUp className="text-blue-600" size={40} />
              LLM Router Configuration
            </h1>
            <p className="text-gray-600 mt-2">
              Intelligent model routing with 77% cost reduction
            </p>
          </div>
          <button
            onClick={saveConfiguration}
            className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-semibold hover:shadow-lg transition-all flex items-center gap-2"
          >
            <Save size={20} />
            Save Configuration
          </button>
        </div>

        {/* Statistics */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-blue-500">
              <p className="text-gray-600 text-sm">Total Requests</p>
              <p className="text-3xl font-bold text-gray-900">{stats.total_requests.toLocaleString()}</p>
              <p className="text-sm text-gray-500 mt-1">all time</p>
            </div>

            <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-green-500">
              <p className="text-gray-600 text-sm">Cost Saved</p>
              <p className="text-3xl font-bold text-green-600">${stats.estimated_cost_saved.toFixed(2)}</p>
              <p className="text-sm text-gray-500 mt-1">{stats.cost_savings_percentage}% reduction</p>
            </div>

            <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-purple-500">
              <p className="text-gray-600 text-sm">Actual Cost</p>
              <p className="text-3xl font-bold text-gray-900">${stats.estimated_cost.toFixed(2)}</p>
              <p className="text-sm text-gray-500 mt-1">total spent</p>
            </div>

            <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-yellow-500">
              <p className="text-gray-600 text-sm">Avg per Request</p>
              <p className="text-3xl font-bold text-gray-900">
                ${(stats.estimated_cost / stats.total_requests).toFixed(4)}
              </p>
              <p className="text-sm text-gray-500 mt-1">optimized</p>
            </div>
          </div>
        )}

        {/* Task Distribution */}
        {stats && (
          <div className="bg-white rounded-xl shadow-md p-6 mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-2">
              <BarChart3 className="text-blue-600" size={28} />
              Task Complexity Distribution
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4">
                <p className="text-sm text-gray-600 mb-1">Simple Tasks</p>
                <p className="text-3xl font-bold text-green-600">{stats.simple_tasks.toLocaleString()}</p>
                <p className="text-xs text-gray-500 mt-1">
                  {((stats.simple_tasks / stats.total_requests) * 100).toFixed(1)}% of total
                </p>
              </div>

              <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4">
                <p className="text-sm text-gray-600 mb-1">Moderate Tasks</p>
                <p className="text-3xl font-bold text-blue-600">{stats.moderate_tasks.toLocaleString()}</p>
                <p className="text-xs text-gray-500 mt-1">
                  {((stats.moderate_tasks / stats.total_requests) * 100).toFixed(1)}% of total
                </p>
              </div>

              <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4">
                <p className="text-sm text-gray-600 mb-1">Complex Tasks</p>
                <p className="text-3xl font-bold text-purple-600">{stats.complex_tasks.toLocaleString()}</p>
                <p className="text-xs text-gray-500 mt-1">
                  {((stats.complex_tasks / stats.total_requests) * 100).toFixed(1)}% of total
                </p>
              </div>

              <div className="bg-gradient-to-br from-red-50 to-red-100 rounded-lg p-4">
                <p className="text-sm text-gray-600 mb-1">Expert Tasks</p>
                <p className="text-3xl font-bold text-red-600">{stats.expert_tasks.toLocaleString()}</p>
                <p className="text-xs text-gray-500 mt-1">
                  {((stats.expert_tasks / stats.total_requests) * 100).toFixed(1)}% of total
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Router Settings */}
        <div className="bg-white rounded-xl shadow-md p-6 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-2">
            <Settings className="text-blue-600" size={28} />
            Router Settings
          </h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div>
                <h3 className="font-semibold text-gray-900">Prefer Cost Efficiency</h3>
                <p className="text-sm text-gray-600">Prioritize cheaper models when possible</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={preferCostEfficiency}
                  onChange={(e) => setPreferCostEfficiency(e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>
          </div>
        </div>

        {/* Model Configuration */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-2">
            <Zap className="text-blue-600" size={28} />
            Model Configuration
          </h2>
          <div className="space-y-4">
            {models.map((model) => (
              <div key={model.name} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className={`w-3 h-3 rounded-full ${model.enabled ? 'bg-green-500' : 'bg-gray-300'}`}></div>
                    <h3 className="text-lg font-bold text-gray-900">{model.name}</h3>
                    <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs font-semibold">
                      Priority {model.priority}
                    </span>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={model.enabled}
                      onChange={(e) => {
                        setModels(models.map(m => 
                          m.name === model.name ? { ...m, enabled: e.target.checked } : m
                        ))
                      }}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <label className="block text-sm text-gray-600 mb-1">Max Tokens</label>
                    <input
                      type="number"
                      value={model.max_tokens}
                      onChange={(e) => {
                        setModels(models.map(m => 
                          m.name === model.name ? { ...m, max_tokens: parseInt(e.target.value) } : m
                        ))
                      }}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>

                  <div>
                    <label className="block text-sm text-gray-600 mb-1">Temperature</label>
                    <input
                      type="number"
                      step="0.1"
                      min="0"
                      max="2"
                      value={model.temperature}
                      onChange={(e) => {
                        setModels(models.map(m => 
                          m.name === model.name ? { ...m, temperature: parseFloat(e.target.value) } : m
                        ))
                      }}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>

                  <div>
                    <label className="block text-sm text-gray-600 mb-1">Cost/1K Input</label>
                    <div className="flex items-center">
                      <span className="text-gray-600 mr-1">$</span>
                      <input
                        type="number"
                        step="0.00001"
                        value={model.cost_per_1k_input}
                        onChange={(e) => {
                          setModels(models.map(m => 
                            m.name === model.name ? { ...m, cost_per_1k_input: parseFloat(e.target.value) } : m
                          ))
                        }}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm text-gray-600 mb-1">Cost/1K Output</label>
                    <div className="flex items-center">
                      <span className="text-gray-600 mr-1">$</span>
                      <input
                        type="number"
                        step="0.00001"
                        value={model.cost_per_1k_output}
                        onChange={(e) => {
                          setModels(models.map(m => 
                            m.name === model.name ? { ...m, cost_per_1k_output: parseFloat(e.target.value) } : m
                          ))
                        }}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
