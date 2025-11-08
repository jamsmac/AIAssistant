"use client";

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
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
  created_at: string;
}

export default function AgentDetailPage() {
  const params = useParams();
  const agentId = params.id as string;
  const [agent, setAgent] = useState<Agent | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (agentId) {
      fetch(`/api/fractal/agents/${agentId}`)
        .then(res => res.json())
        .then(data => { setAgent(data); setLoading(false); })
        .catch(err => { console.error(err); setLoading(false); });
    }
  }, [agentId]);

  const getSuccessRate = () => {
    if (!agent || agent.total_tasks_processed === 0) return 0;
    return ((agent.successful_tasks / agent.total_tasks_processed) * 100).toFixed(1);
  };

  if (loading) {
    return <div className="min-h-screen bg-gray-50 p-8"><div className="max-w-7xl mx-auto">Loading...</div></div>;
  }

  if (!agent) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-8">
        <div className="text-center">
          <h1 className="text-4xl font-bold mb-4">Agent not found</h1>
          <Link href="/fractal-agents" className="text-blue-600 hover:text-blue-700">Back to agents</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <Link href="/fractal-agents" className="inline-flex items-center text-sm text-gray-600 hover:text-gray-900 mb-6">
          Back to agents
        </Link>

        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">{agent.name}</h1>
          <p className="text-gray-600">Type: {agent.agent_type} | ID: {agent.id}</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-sm p-6 border">
            <p className="text-sm text-gray-600 mb-1">Success Rate</p>
            <p className="text-3xl font-bold text-gray-900">{getSuccessRate()}%</p>
          </div>
          <div className="bg-white rounded-lg shadow-sm p-6 border">
            <p className="text-sm text-gray-600 mb-1">Confidence</p>
            <p className="text-3xl font-bold text-gray-900">{(agent.avg_confidence_score * 100).toFixed(0)}%</p>
          </div>
          <div className="bg-white rounded-lg shadow-sm p-6 border">
            <p className="text-sm text-gray-600 mb-1">Trust Level</p>
            <p className="text-3xl font-bold text-gray-900">{(agent.trust_level * 100).toFixed(0)}%</p>
          </div>
          <div className="bg-white rounded-lg shadow-sm p-6 border">
            <p className="text-sm text-gray-600 mb-1">Skills</p>
            <p className="text-3xl font-bold text-gray-900">{agent.skills.length}</p>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6 border">
          <h2 className="text-xl font-bold mb-4">Skills</h2>
          <div className="flex flex-wrap gap-2">
            {agent.skills.map((skill, idx) => (
              <span key={idx} className="px-3 py-1 bg-blue-50 text-blue-700 text-sm rounded-full">
                {skill}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
