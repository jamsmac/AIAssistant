'use client'

import { useState } from 'react'
import { Plus, Play, Save, GitBranch, Zap, Settings } from 'lucide-react'

interface WorkflowNode {
  id: string
  type: 'agent' | 'condition' | 'action'
  name: string
  config: any
  position: { x: number; y: number }
}

interface WorkflowConnection {
  from: string
  to: string
  label?: string
}

export default function WorkflowBuilderPage() {
  const [nodes, setNodes] = useState<WorkflowNode[]>([])
  const [connections, setConnections] = useState<WorkflowConnection[]>([])
  const [workflowName, setWorkflowName] = useState('New Workflow')
  const [selectedNode, setSelectedNode] = useState<string | null>(null)

  const availableAgents = [
    { id: 'backend-architect', name: 'Backend Architect', type: 'agent' },
    { id: 'frontend-developer', name: 'Frontend Developer', type: 'agent' },
    { id: 'qa-engineer', name: 'QA Engineer', type: 'agent' },
    { id: 'devops-engineer', name: 'DevOps Engineer', type: 'agent' },
  ]

  const addNode = (agentType: string) => {
    const newNode: WorkflowNode = {
      id: `node-${Date.now()}`,
      type: 'agent',
      name: agentType,
      config: {},
      position: { x: 100 + nodes.length * 50, y: 100 + nodes.length * 50 }
    }
    setNodes([...nodes, newNode])
  }

  const saveWorkflow = () => {
    const workflow = {
      name: workflowName,
      nodes,
      connections
    }
    console.log('Saving workflow:', workflow)
    // TODO: Implement actual API call
    alert('Workflow saved! (API integration pending)')
  }

  const executeWorkflow = () => {
    console.log('Executing workflow:', { nodes, connections })
    // TODO: Implement actual API call
    alert('Workflow execution started! (API integration pending)')
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              Workflow Builder
            </h1>
            <p className="text-gray-600 mt-2">
              Create multi-agent workflows with LangGraph
            </p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={saveWorkflow}
              className="px-4 py-2 bg-white text-gray-700 rounded-lg font-semibold hover:shadow-md transition-all flex items-center gap-2 border border-gray-300"
            >
              <Save size={20} />
              Save
            </button>
            <button
              onClick={executeWorkflow}
              className="px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-semibold hover:shadow-lg transition-all flex items-center gap-2"
            >
              <Play size={20} />
              Execute
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Left Sidebar - Agent Palette */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-xl shadow-md p-6">
              <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
                <Zap size={20} />
                Agent Palette
              </h3>
              <div className="space-y-2">
                {availableAgents.map((agent) => (
                  <button
                    key={agent.id}
                    onClick={() => addNode(agent.name)}
                    className="w-full px-4 py-3 bg-gradient-to-r from-blue-50 to-purple-50 hover:from-blue-100 hover:to-purple-100 rounded-lg text-left transition-all border border-blue-200 hover:border-blue-300"
                  >
                    <div className="flex items-center gap-2">
                      <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg flex items-center justify-center text-white font-bold text-sm">
                        {agent.name.charAt(0)}
                      </div>
                      <span className="font-semibold text-gray-800 text-sm">{agent.name}</span>
                    </div>
                  </button>
                ))}
              </div>

              <div className="mt-6 pt-6 border-t border-gray-200">
                <h4 className="text-sm font-semibold text-gray-700 mb-3">Control Nodes</h4>
                <button className="w-full px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-left transition-all text-sm">
                  <GitBranch className="inline mr-2" size={16} />
                  Condition
                </button>
              </div>
            </div>
          </div>

          {/* Main Canvas */}
          <div className="lg:col-span-3">
            <div className="bg-white rounded-xl shadow-md p-6 min-h-[600px]">
              <div className="mb-4 flex items-center justify-between">
                <input
                  type="text"
                  value={workflowName}
                  onChange={(e) => setWorkflowName(e.target.value)}
                  className="text-xl font-bold text-gray-800 bg-transparent border-b-2 border-transparent hover:border-gray-300 focus:border-blue-500 focus:outline-none px-2 py-1"
                />
                <div className="text-sm text-gray-600">
                  {nodes.length} nodes, {connections.length} connections
                </div>
              </div>

              {/* Canvas Area */}
              <div className="relative bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg border-2 border-dashed border-gray-300 min-h-[500px] p-4">
                {nodes.length === 0 ? (
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="text-center">
                      <Plus className="mx-auto text-gray-400 mb-4" size={48} />
                      <h3 className="text-lg font-semibold text-gray-700 mb-2">
                        Start Building Your Workflow
                      </h3>
                      <p className="text-gray-600">
                        Drag agents from the palette to create your workflow
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {nodes.map((node, index) => (
                      <div
                        key={node.id}
                        className={`bg-white rounded-lg shadow-md p-4 border-2 transition-all cursor-pointer ${
                          selectedNode === node.id
                            ? 'border-blue-500 shadow-lg'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                        onClick={() => setSelectedNode(node.id)}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg flex items-center justify-center text-white font-bold">
                              {index + 1}
                            </div>
                            <div>
                              <h4 className="font-semibold text-gray-800">{node.name}</h4>
                              <p className="text-xs text-gray-600">Agent Node</p>
                            </div>
                          </div>
                          <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                            <Settings size={18} className="text-gray-600" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Workflow Info */}
            <div className="mt-6 bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl shadow-lg p-6 text-white">
              <h3 className="text-xl font-bold mb-4">LangGraph Integration</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4">
                  <h4 className="font-semibold mb-1">Stateful Workflows</h4>
                  <p className="text-sm text-blue-100">Maintain state across agent executions</p>
                </div>
                <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4">
                  <h4 className="font-semibold mb-1">Multi-Agent Collaboration</h4>
                  <p className="text-sm text-blue-100">Agents work together on complex tasks</p>
                </div>
                <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4">
                  <h4 className="font-semibold mb-1">Conditional Branching</h4>
                  <p className="text-sm text-blue-100">Dynamic workflow paths based on results</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
