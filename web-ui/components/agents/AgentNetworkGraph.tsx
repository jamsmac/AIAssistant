'use client'

import { useCallback, useEffect, useState } from 'react'
import ReactFlow, {
  Node,
  Edge,
  addEdge,
  Connection,
  useNodesState,
  useEdgesState,
  Background,
  Controls,
  MiniMap,
  NodeTypes,
} from 'reactflow'
import 'reactflow/dist/style.css'
import { Activity, Cpu, TrendingUp, Zap } from 'lucide-react'
import type { AgentNodeData } from '@/types/agents'

interface Agent {
  id: string
  name: string
  agent_type: string
  skills: string[]
  success_rate: number
  task_count: number
  avg_response_time: number
  trust_level: number
}

interface Connector {
  id: string
  from_agent_id: string
  to_agent_id: string
  connector_type: string
  strength: number
  trust: number
}

// Custom Node Component
function AgentNode({ data }: { data: AgentNodeData }) {
  const getTypeColor = (type: string) => {
    switch (type) {
      case 'root': return 'from-purple-500 to-pink-500'
      case 'specialist': return 'from-blue-500 to-cyan-500'
      case 'coordinator': return 'from-green-500 to-emerald-500'
      default: return 'from-gray-500 to-gray-600'
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'root': return <Cpu size={20} />
      case 'specialist': return <Zap size={20} />
      case 'coordinator': return <Activity size={20} />
      default: return <Cpu size={20} />
    }
  }

  return (
    <div className="px-4 py-3 shadow-lg rounded-xl border-2 border-gray-200 bg-white min-w-[200px]">
      <div className={`flex items-center gap-2 mb-2 text-white p-2 rounded-lg bg-gradient-to-r ${getTypeColor(data.type)}`}>
        {getTypeIcon(data.type)}
        <div className="font-bold">{data.label}</div>
      </div>

      <div className="text-xs space-y-1 text-gray-600">
        <div className="flex justify-between">
          <span>Type:</span>
          <span className="font-semibold">{data.type}</span>
        </div>
        <div className="flex justify-between">
          <span>Tasks:</span>
          <span className="font-semibold">{data.taskCount || 0}</span>
        </div>
        <div className="flex justify-between">
          <span>Success:</span>
          <span className="font-semibold text-green-600">{((data.successRate || 0) * 100).toFixed(0)}%</span>
        </div>
      </div>

      {data.capabilities && data.capabilities.length > 0 && (
        <div className="mt-2 pt-2 border-t border-gray-200">
          <div className="text-xs text-gray-500 mb-1">Capabilities:</div>
          <div className="flex flex-wrap gap-1">
            {data.capabilities.slice(0, 3).map((capability: string, i: number) => (
              <span key={i} className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full text-xs">
                {capability}
              </span>
            ))}
            {data.capabilities.length > 3 && (
              <span className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded-full text-xs">
                +{data.capabilities.length - 3}
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

const nodeTypes: NodeTypes = {
  agentNode: AgentNode,
}

export default function AgentNetworkGraph() {
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [loading, setLoading] = useState(true)
  const [agents, setAgents] = useState<Agent[]>([])
  const [connectors, setConnectors] = useState<Connector[]>([])

  useEffect(() => {
    fetchNetworkData()
  }, [])

  const fetchNetworkData = async () => {
    try {
      // Fetch agents
      const agentsResponse = await fetch('/api/fractal/agents')
      const agentsData = await agentsResponse.json()
      setAgents(agentsData.agents || [])

      // Fetch connectors
      const connectorsResponse = await fetch('/api/fractal/connectors')
      const connectorsData = await connectorsResponse.json()
      setConnectors(connectorsData.connectors || [])

      // Build graph
      buildGraph(agentsData.agents || [], connectorsData.connectors || [])
    } catch (error) {
      console.error('Failed to fetch network data:', error)
    } finally {
      setLoading(false)
    }
  }

  const buildGraph = (agentsData: Agent[], connectorsData: Connector[]) => {
    // Create nodes
    const newNodes: Node[] = agentsData.map((agent, index) => {
      // Simple circular layout
      const angle = (index / agentsData.length) * 2 * Math.PI
      const radius = 300
      const x = 400 + radius * Math.cos(angle)
      const y = 300 + radius * Math.sin(angle)

      return {
        id: agent.id,
        type: 'agentNode',
        position: { x, y },
        data: {
          label: agent.name,
          type: agent.agent_type,
          taskCount: agent.task_count,
          successRate: agent.success_rate,
          capabilities: agent.skills || [],
        },
      }
    })

    // Create edges
    const newEdges: Edge[] = connectorsData.map((connector) => ({
      id: connector.id,
      source: connector.from_agent_id,
      target: connector.to_agent_id,
      type: 'smoothstep',
      animated: connector.strength > 0.7,
      style: {
        stroke: connector.connector_type === 'parent_child' ? '#8b5cf6' : '#3b82f6',
        strokeWidth: Math.max(1, connector.strength * 3),
      },
      label: `${(connector.strength * 100).toFixed(0)}%`,
      labelStyle: { fill: '#666', fontSize: 10 },
      labelBgStyle: { fill: '#fff' },
    }))

    setNodes(newNodes)
    setEdges(newEdges)
  }

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  )

  if (loading) {
    return (
      <div className="h-[600px] flex items-center justify-center bg-gray-50 rounded-xl">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading network...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-[600px] bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden">
      <div className="h-full">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          nodeTypes={nodeTypes}
          fitView
          attributionPosition="bottom-left"
        >
          <Background color="#aaa" gap={16} />
          <Controls />
          <MiniMap
            nodeColor={(node: any) => {
              switch (node.data.type) {
                case 'root': return '#a855f7'
                case 'specialist': return '#3b82f6'
                case 'coordinator': return '#10b981'
                default: return '#6b7280'
              }
            }}
            maskColor="rgba(0, 0, 0, 0.1)"
          />
        </ReactFlow>
      </div>

      {/* Legend */}
      <div className="absolute bottom-4 left-4 bg-white/90 backdrop-blur-sm rounded-lg shadow-lg p-3 text-xs">
        <div className="font-semibold mb-2">Agent Types</div>
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-gradient-to-r from-purple-500 to-pink-500"></div>
            <span>Root Agent</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-gradient-to-r from-blue-500 to-cyan-500"></div>
            <span>Specialist</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-gradient-to-r from-green-500 to-emerald-500"></div>
            <span>Coordinator</span>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="absolute top-4 right-4 bg-white/90 backdrop-blur-sm rounded-lg shadow-lg p-3 text-xs">
        <div className="font-semibold mb-2">Network Stats</div>
        <div className="space-y-1">
          <div className="flex justify-between gap-4">
            <span>Agents:</span>
            <span className="font-semibold">{agents.length}</span>
          </div>
          <div className="flex justify-between gap-4">
            <span>Connections:</span>
            <span className="font-semibold">{connectors.length}</span>
          </div>
          <div className="flex justify-between gap-4">
            <span>Avg Success:</span>
            <span className="font-semibold text-green-600">
              {agents.length > 0
                ? (agents.reduce((sum, a) => sum + (a.success_rate || 0), 0) / agents.length * 100).toFixed(0)
                : 0}%
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
