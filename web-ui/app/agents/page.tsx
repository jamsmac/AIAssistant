'use client'

import { useState, useEffect } from 'react'
import dynamic from 'next/dynamic'
import { Loader2, Activity, Cpu, TrendingUp, Zap, Network, CheckCircle } from 'lucide-react'

const AgentNetworkGraph = dynamic(() => import('@/components/agents/AgentNetworkGraph'), {
  ssr: false,
  loading: () => (
    <div className="flex h-64 items-center justify-center rounded-xl border border-gray-800 bg-gray-900/60">
      <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
    </div>
  ),
})

interface Agent {
  id: string;
  agent_name: string;
  agent_type: string;
  status: string;
  skills: string[];
  task_count: number;
  success_rate: number;
  total_cost: number;
}

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [systemStatus, setSystemStatus] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  useEffect(() => {
    Promise.all([
      fetch(`${API_BASE}/api/fractal/agents`).then(res => res.json()),
      fetch(`${API_BASE}/api/fractal/system-status`).then(res => res.json())
    ])
      .then(([agentsData, statusData]) => {
        setAgents(agentsData.agents || [])
        setSystemStatus(statusData)
        setLoading(false)
      })
      .catch(err => {
        console.error(err)
        setLoading(false)
      })
  }, [API_BASE])

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 p-8 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading agents...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            FractalAgents Dashboard
          </h1>
          <p className="text-gray-600 mt-2">Monitor and manage your self-organizing agent network</p>
        </div>

        {/* System Status Cards */}
        {systemStatus && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-blue-500">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-600 text-sm">Total Agents</p>
                  <p className="text-3xl font-bold text-gray-800">{systemStatus.agents?.total || 0}</p>
                </div>
                <Cpu className="text-blue-500" size={32} />
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-green-500">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-600 text-sm">Connectors</p>
                  <p className="text-3xl font-bold text-gray-800">{systemStatus.connectors?.total || 0}</p>
                </div>
                <Network className="text-green-500" size={32} />
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-purple-500">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-600 text-sm">Avg Success Rate</p>
                  <p className="text-3xl font-bold text-gray-800">
                    {((systemStatus.collective_memory?.success_rate || 0) * 100).toFixed(0)}%
                  </p>
                </div>
                <TrendingUp className="text-purple-500" size={32} />
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-yellow-500">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-600 text-sm">Memory Entries</p>
                  <p className="text-3xl font-bold text-gray-800">{systemStatus.collective_memory?.total_entries || 0}</p>
                </div>
                <Activity className="text-yellow-500" size={32} />
              </div>
            </div>
          </div>
        )}

        {/* Network Visualization */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-800 mb-4 flex items-center gap-2">
            <Network size={24} />
            Agent Network
          </h2>
          <AgentNetworkGraph />
        </div>

        {/* Agents Table */}
        <div className="bg-white rounded-xl shadow-md overflow-hidden">
          <div className="p-6 bg-gradient-to-r from-blue-600 to-purple-600 text-white">
            <h2 className="text-2xl font-bold">All Agents</h2>
            <p className="text-blue-100 mt-1">Detailed list of all agents in the network</p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Agent
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Skills
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Tasks
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Success Rate
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {agents.map((agent) => (
                  <tr key={agent.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white ${
                          agent.agent_type === 'root' ? 'bg-gradient-to-r from-purple-500 to-pink-500' :
                          agent.agent_type === 'specialist' ? 'bg-gradient-to-r from-blue-500 to-cyan-500' :
                          'bg-gradient-to-r from-green-500 to-emerald-500'
                        }`}>
                          {agent.agent_type === 'root' ? <Cpu size={20} /> : <Zap size={20} />}
                        </div>
                        <div>
                          <p className="font-semibold text-gray-900">{agent.agent_name}</p>
                          <p className="text-sm text-gray-500">{agent.id.slice(0, 8)}...</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                        agent.agent_type === 'root' ? 'bg-purple-100 text-purple-800' :
                        agent.agent_type === 'specialist' ? 'bg-blue-100 text-blue-800' :
                        'bg-green-100 text-green-800'
                      }`}>
                        {agent.agent_type}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex flex-wrap gap-1">
                        {agent.skills.slice(0, 3).map((skill: string, i: number) => (
                          <span key={i} className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">
                            {skill}
                          </span>
                        ))}
                        {agent.skills.length > 3 && (
                          <span className="px-2 py-1 bg-gray-200 text-gray-600 rounded text-xs">
                            +{agent.skills.length - 3}
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-gray-900 font-semibold">{agent.task_count || 0}</span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 bg-gray-200 rounded-full h-2 max-w-[100px]">
                          <div
                            className="bg-gradient-to-r from-green-500 to-emerald-500 h-2 rounded-full"
                            style={{ width: `${(agent.success_rate || 0) * 100}%` }}
                          ></div>
                        </div>
                        <span className="text-sm font-semibold text-gray-700">
                          {((agent.success_rate || 0) * 100).toFixed(0)}%
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2 text-green-600">
                        <CheckCircle size={18} />
                        <span className="text-sm font-semibold">Active</span>
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
