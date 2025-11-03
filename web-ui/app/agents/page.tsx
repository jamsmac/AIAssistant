'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { ArrowLeft, CheckCircle, XCircle, DollarSign, Zap, Activity } from 'lucide-react';
import { API_URL } from '@/lib/config';

export const dynamic = 'force-dynamic';

interface ModelsInfo {
  [key: string]: {
    name: string;
    available: boolean;
    use_cases: string[];
    cost: string;
  };
}

interface HealthResponse {
  status: string;
  services: Record<string, boolean>;
  router_stats: { total_calls: number; total_cost: number };
}

export default function AgentsPage() {
  const [models, setModels] = useState<ModelsInfo | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const [modelsRes, healthRes] = await Promise.all([
        fetch(`${API_URL}/api/models`),
        fetch(`${API_URL}/api/health`)
      ]);
      
      const modelsData = await modelsRes.json();
      const healthData = await healthRes.json();
      
      setModels(modelsData);
      setHealth(healthData);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching data:', error);
      setLoading(false);
    }
  };

  useEffect(() => {
    const starter = setTimeout(() => { void fetchData(); }, 0);
    return () => clearTimeout(starter);
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900">
      {/* Header */}
      <header className="bg-black/30 backdrop-blur-md border-b border-white/10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center gap-4">
            <Link href="/">
              <button className="w-10 h-10 bg-white/10 hover:bg-white/20 rounded-lg flex items-center justify-center text-white transition">
                <ArrowLeft className="w-5 h-5" />
              </button>
            </Link>
            <div>
              <h1 className="text-2xl font-bold text-white">Manage AI Agents</h1>
              <p className="text-sm text-gray-400">Управление и мониторинг AI моделей</p>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8 pb-20 md:pb-8">
        {/* System Health */}
        {health && (
          <div className="bg-white/5 backdrop-blur-md rounded-2xl border border-white/10 p-6 mb-8">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-white">System Health</h2>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                <span className="text-sm text-green-300">{health.status}</span>
              </div>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div className="bg-white/5 rounded-lg p-4">
                <div className="text-gray-400 text-sm mb-1">Total API Calls</div>
                <div className="text-2xl font-bold text-white">{health.router_stats.total_calls}</div>
              </div>
              <div className="bg-white/5 rounded-lg p-4">
                <div className="text-gray-400 text-sm mb-1">Total Cost</div>
                <div className="text-2xl font-bold text-white">${health.router_stats.total_cost.toFixed(4)}</div>
              </div>
              <div className="bg-white/5 rounded-lg p-4">
                <div className="text-gray-400 text-sm mb-1">Active Services</div>
                <div className="text-2xl font-bold text-white">
                  {Object.values(health.services).filter(Boolean).length}/5
                </div>
              </div>
            </div>
          </div>
        )}

        {/* AI Models */}
        <div className="mb-4">
          <h2 className="text-2xl font-bold text-white mb-6">Available AI Models</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {models && Object.entries(models).map(([key, model]) => (
            <ModelCard key={key} modelKey={key} model={model} />
          ))}
        </div>

        {/* Legend */}
        <div className="mt-8 bg-white/5 backdrop-blur-md rounded-2xl border border-white/10 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Cost Legend</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
              <span className="text-sm text-gray-300">FREE - $0</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
              <span className="text-sm text-gray-300">$ - До $0.001</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-orange-500 rounded-full"></div>
              <span className="text-sm text-gray-300">$$ - До $0.01</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-red-500 rounded-full"></div>
              <span className="text-sm text-gray-300">$$$ - Более $0.01</span>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

type ModelInfo = { name: string; available: boolean; use_cases: string[]; cost: string };
function ModelCard({ modelKey, model }: { modelKey: string; model: ModelInfo }) {
  const costColors: Record<string, string> = {
    'FREE': 'from-green-500/20 to-green-600/20 border-green-500/30',
    '$': 'from-yellow-500/20 to-yellow-600/20 border-yellow-500/30',
    '$$': 'from-orange-500/20 to-orange-600/20 border-orange-500/30',
    '$$$': 'from-red-500/20 to-red-600/20 border-red-500/30'
  };

  const costMatch = model.cost.match(/^(FREE|\$+)/);
  const costLevel = costMatch ? costMatch[1] : '$';
  const colorClass = costColors[costLevel] || costColors['$'];

  return (
    <div className={`bg-gradient-to-br ${colorClass} backdrop-blur-md rounded-2xl border p-6 hover:scale-105 transition`}>
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-white mb-1 capitalize">{modelKey}</h3>
          <p className="text-sm text-gray-300">{model.name}</p>
        </div>
        {model.available ? (
          <CheckCircle className="w-6 h-6 text-green-400 flex-shrink-0" />
        ) : (
          <XCircle className="w-6 h-6 text-red-400 flex-shrink-0" />
        )}
      </div>

      {/* Status Badge */}
      <div className="mb-4">
        <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium ${
          model.available 
            ? 'bg-green-500/20 text-green-300 border border-green-500/30' 
            : 'bg-red-500/20 text-red-300 border border-red-500/30'
        }`}>
          <div className={`w-1.5 h-1.5 rounded-full ${model.available ? 'bg-green-400' : 'bg-red-400'}`}></div>
          {model.available ? 'Available' : 'Offline'}
        </span>
      </div>

      {/* Cost */}
      <div className="mb-4 flex items-center gap-2">
        <DollarSign className="w-4 h-4 text-gray-400" />
        <span className="text-white font-medium">{model.cost}</span>
      </div>

      {/* Use Cases */}
      <div className="mb-4">
        <div className="text-xs text-gray-400 mb-2">Best for:</div>
        <div className="flex flex-wrap gap-1">
          {model.use_cases.map((useCase: string) => (
            <span 
              key={useCase}
              className="px-2 py-1 bg-white/10 rounded text-xs text-gray-200"
            >
              {useCase.replace('_', ' ')}
            </span>
          ))}
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-2 pt-4 border-t border-white/10">
        <div className="flex items-center gap-2">
          <Zap className="w-4 h-4 text-blue-400" />
          <span className="text-xs text-gray-300">
            {model.available ? 'Ready' : 'Unavailable'}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-purple-400" />
          <span className="text-xs text-gray-300">Auto-Select</span>
        </div>
      </div>
    </div>
  );
}