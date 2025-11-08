"use client";

import { useState, useEffect } from 'react';
import Link from 'next/link';

interface Agent {
  id: string;
  name: string;
  agent_type: string;
  skills: string[];
  total_tasks_processed: number;
  successful_tasks: number;
  avg_confidence_score: number;
  trust_level: number;
  is_active: boolean;
}

interface SystemStatus {
  organization_id: string;
  agents: {
    total: number;
    by_type: Array<{
      type: string;
      count: number;
      avg_success_rate: number;
    }>;
  };
  connectors: {
    total: number;
  };
  collective_memory: {
    total_entries: number;
    success_rate: number;
  };
  status: string;
}

export default function FractalAgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);

      // Fetch agents
      const agentsRes = await fetch('/api/fractal/agents');
      if (agentsRes.ok) {
        const agentsData = await agentsRes.json();
        setAgents(agentsData.agents || []);
      }

      // Fetch system status
      const statusRes = await fetch('/api/fractal/system-status');
      if (statusRes.ok) {
        const statusData = await statusRes.json();
        setSystemStatus(statusData);
      }
    } catch (err) {
      setError('Failed to load agents data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getSuccessRate = (agent: Agent) => {
    if (agent.total_tasks_processed === 0) return 0;
    return ((agent.successful_tasks / agent.total_tasks_processed) * 100).toFixed(1);
  };

  const getAgentTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      root: 'bg-purple-100 text-purple-800 border-purple-300',
      specialist: 'bg-blue-100 text-blue-800 border-blue-300',
      coordinator: 'bg-green-100 text-green-800 border-green-300',
      worker: 'bg-gray-100 text-gray-800 border-gray-300',
    };
    return colors[type] || colors.worker;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-1/4 mb-8"></div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              {[1, 2, 3].map(i => (
                <div key={i} className="h-32 bg-gray-200 rounded"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            FractalAgents System
          </h1>
          <p className="text-gray-600">
            Self-organizing AI agent network with collective intelligence
          </p>
        </div>

        {/* System Status */}
        {systemStatus && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Total Agents</p>
                  <p className="text-3xl font-bold text-gray-900">
                    {systemStatus.agents.total}
                  </p>
                </div>
                <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                  <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Connectors</p>
                  <p className="text-3xl font-bold text-gray-900">
                    {systemStatus.connectors.total}
                  </p>
                </div>
                <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                  <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Memory Entries</p>
                  <p className="text-3xl font-bold text-gray-900">
                    {systemStatus.collective_memory.total_entries}
                  </p>
                </div>
                <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center">
                  <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Success Rate</p>
                  <p className="text-3xl font-bold text-gray-900">
                    {systemStatus.collective_memory.success_rate}%
                  </p>
                </div>
                <div className="w-12 h-12 bg-yellow-100 rounded-full flex items-center justify-center">
                  <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-8">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {/* Agents Grid */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-2xl font-bold text-gray-900">Active Agents</h2>
            <Link
              href="/admin/agents/new"
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              + Create Agent
            </Link>
          </div>

          {agents.length === 0 ? (
            <div className="bg-white rounded-lg shadow-sm p-12 text-center border border-gray-200">
              <p className="text-gray-500 mb-4">No agents found</p>
              <Link
                href="/admin/agents/new"
                className="text-blue-600 hover:text-blue-700 font-medium"
              >
                Create your first agent →
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {agents.map((agent) => (
                <Link
                  key={agent.id}
                  href={`/fractal-agents/${agent.id}`}
                  className="bg-white rounded-lg shadow-sm p-6 border border-gray-200 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-1">
                        {agent.name}
                      </h3>
                      <span className={`inline-block px-2 py-1 text-xs font-medium rounded-full border ${getAgentTypeColor(agent.agent_type)}`}>
                        {agent.agent_type}
                      </span>
                    </div>
                    <div className={`w-3 h-3 rounded-full ${agent.is_active ? 'bg-green-500' : 'bg-gray-300'}`}></div>
                  </div>

                  <div className="space-y-3">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Success Rate:</span>
                      <span className="font-medium text-gray-900">
                        {getSuccessRate(agent)}%
                      </span>
                    </div>

                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Tasks Processed:</span>
                      <span className="font-medium text-gray-900">
                        {agent.total_tasks_processed}
                      </span>
                    </div>

                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Confidence:</span>
                      <span className="font-medium text-gray-900">
                        {(agent.avg_confidence_score * 100).toFixed(0)}%
                      </span>
                    </div>

                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Trust Level:</span>
                      <span className="font-medium text-gray-900">
                        {(agent.trust_level * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>

                  <div className="mt-4 pt-4 border-t border-gray-100">
                    <p className="text-xs text-gray-500 mb-2">Skills:</p>
                    <div className="flex flex-wrap gap-1">
                      {agent.skills.slice(0, 3).map((skill, idx) => (
                        <span
                          key={idx}
                          className="inline-block px-2 py-0.5 bg-gray-100 text-gray-700 text-xs rounded"
                        >
                          {skill}
                        </span>
                      ))}
                      {agent.skills.length > 3 && (
                        <span className="inline-block px-2 py-0.5 bg-gray-100 text-gray-700 text-xs rounded">
                          +{agent.skills.length - 3}
                        </span>
                      )}
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>

        {/* Agent Types Breakdown */}
        {systemStatus && systemStatus.agents.by_type.length > 0 && (
          <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Agent Types Distribution</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {systemStatus.agents.by_type.map((typeInfo) => (
                <div key={typeInfo.type} className="text-center p-4 bg-gray-50 rounded-lg">
                  <p className="text-2xl font-bold text-gray-900">{typeInfo.count}</p>
                  <p className="text-sm text-gray-600 capitalize">{typeInfo.type}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    {(typeInfo.avg_success_rate * 100).toFixed(0)}% success
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
