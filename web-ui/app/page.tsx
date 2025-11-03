'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { API_URL } from '@/lib/config';
import {
  Activity,
  Zap,
  DollarSign,
  CheckCircle,
  Code,
  MessageSquare,
  Settings,
  TrendingUp,
  Clock
} from 'lucide-react';

interface ByModelUsage { calls: number; tokens: number; cost: number }
interface Stats {
  calls: number;
  tokens: number;
  cost: number;
  avg_cost_per_call: number;
  by_model: Record<string, ByModelUsage>;
  available_models: Record<string, boolean>;
}

export default function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchStats = async () => {
    try {
      const response = await fetch(`${API_URL}/api/stats`);
      const data = await response.json();
      setStats(data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching stats:', error);
      setLoading(false);
    }
  };

  useEffect(() => {
    const interval = setInterval(fetchStats, 10000); // обновление каждые 10 сек
    // Отложенный старт, чтобы не вызывать setState синхронно в эффекте
    const starter = setTimeout(() => { void fetchStats(); }, 0);
    return () => {
      clearInterval(interval);
      clearTimeout(starter);
    };
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading...</div>
      </div>
    );
  }

  const modelsAvailable = stats?.available_models 
    ? Object.values(stats.available_models).filter(Boolean).length 
    : 0;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900">
      {/* Header */}
      <header className="bg-black/30 backdrop-blur-md border-b border-white/10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <Zap className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">AI Development System</h1>
                <p className="text-sm text-gray-400">Автоматизация разработки с AI</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
              <span className="text-sm text-gray-300">Online</span>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8 pb-20 md:pb-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <StatCard
            title="Total Requests"
            value={stats?.calls || 0}
            icon={<Activity className="w-6 h-6" />}
            color="blue"
            trend="+12%"
          />
          <StatCard
            title="Active Models"
            value={modelsAvailable}
            icon={<CheckCircle className="w-6 h-6" />}
            color="green"
          />
          <StatCard
            title="Total Cost"
            value={`$${(stats?.cost || 0).toFixed(4)}`}
            icon={<DollarSign className="w-6 h-6" />}
            color="purple"
          />
          <StatCard
            title="Avg Cost/Request"
            value={`$${(stats?.avg_cost_per_call || 0).toFixed(6)}`}
            icon={<TrendingUp className="w-6 h-6" />}
            color="orange"
          />
        </div>

        {/* Action Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-6 mb-12">
          {/* AI Chat */}
          <ActionCard
            title="AI Chat"
            description="Общайся с AI моделями"
            icon={<MessageSquare className="w-8 h-8" />}
            href="/chat"
            color="blue"
          />

          {/* Create Project */}
          <ActionCard
            title="Create Project"
            description="Создай проект из идеи"
            icon={<Code className="w-8 h-8" />}
            href="/project"
            color="purple"
          />

          {/* Manage Agents */}
          <ActionCard
            title="Manage Agents"
            description="Настройка AI агентов"
            icon={<Settings className="w-8 h-8" />}
            href="/agents"
            color="green"
          />

          {/* Request History */}
          <ActionCard
            title="Request History"
            description="История запросов к AI"
            icon={<Clock className="w-8 h-8" />}
            href="/history"
            color="yellow"
          />

          {/* Models Ranking - NEW */}
          <ActionCard
            title="Models Ranking"
            description="Рейтинги AI моделей"
            icon={<TrendingUp className="w-8 h-8" />}
            href="/models-ranking"
            color="orange"
          />
        </div>

        {/* Models Status */}
        <div className="bg-white/5 backdrop-blur-md rounded-2xl border border-white/10 p-6">
          <h2 className="text-xl font-semibold text-white mb-4">AI Models Status</h2>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            {stats?.available_models && Object.entries(stats.available_models).map(([model, available]) => (
              <ModelStatus
                key={model}
                name={model}
                available={available}
              />
            ))}
          </div>
        </div>

        {/* Usage by Model */}
        {stats?.by_model && Object.keys(stats.by_model).length > 0 && (
          <div className="mt-8 bg-white/5 backdrop-blur-md rounded-2xl border border-white/10 p-6">
            <h2 className="text-xl font-semibold text-white mb-4">Usage by Model</h2>
            <div className="space-y-3">
              {Object.entries(stats.by_model).map(([model, data]) => (
                <div key={model} className="flex items-center justify-between p-3 bg-white/5 rounded-lg">
                  <div>
                    <div className="text-white font-medium">{model}</div>
                    <div className="text-sm text-gray-400">{data.calls} calls • {data.tokens} tokens</div>
                  </div>
                  <div className="text-right">
                    <div className="text-white font-mono">${data.cost.toFixed(6)}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

interface StatCardProps { title: string; value: string | number; icon: React.ReactNode; color: 'blue'|'green'|'purple'|'orange'; trend?: string }
function StatCard({ title, value, icon, color, trend }: StatCardProps) {
  const colorClasses = {
    blue: 'from-blue-500 to-blue-600',
    green: 'from-green-500 to-green-600',
    purple: 'from-purple-500 to-purple-600',
    orange: 'from-orange-500 to-orange-600'
  };

  return (
    <div className="bg-white/5 backdrop-blur-md rounded-2xl border border-white/10 p-6 hover:bg-white/10 transition">
      <div className="flex items-center justify-between mb-4">
        <div className={`w-12 h-12 bg-gradient-to-br ${colorClasses[color]} rounded-xl flex items-center justify-center text-white`}>
          {icon}
        </div>
        {trend && (
          <span className="text-xs text-green-400 font-medium">{trend}</span>
        )}
      </div>
      <div className="text-3xl font-bold text-white mb-1">{value}</div>
      <div className="text-sm text-gray-400">{title}</div>
    </div>
  );
}

interface ActionCardProps { title: string; description: string; icon: React.ReactNode; href: string; color: 'blue'|'purple'|'green'|'yellow'|'orange' }
function ActionCard({ title, description, icon, href, color }: ActionCardProps) {
  const colorClasses = {
    blue: 'from-blue-500/20 to-blue-600/20 hover:from-blue-500/30 hover:to-blue-600/30 border-blue-500/30',
    purple: 'from-purple-500/20 to-purple-600/20 hover:from-purple-500/30 hover:to-purple-600/30 border-purple-500/30',
    green: 'from-green-500/20 to-green-600/20 hover:from-green-500/30 hover:to-green-600/30 border-green-500/30',
    yellow: 'from-yellow-500/20 to-yellow-600/20 hover:from-yellow-500/30 hover:to-yellow-600/30 border-yellow-500/30',
    orange: 'from-orange-500/20 to-orange-600/20 hover:from-orange-500/30 hover:to-orange-600/30 border-orange-500/30'
  };

  return (
    <Link href={href}>
      <div className={`bg-gradient-to-br ${colorClasses[color]} backdrop-blur-md rounded-2xl border p-6 hover:scale-105 transition cursor-pointer`}>
        <div className="mb-4 text-white">{icon}</div>
        <h3 className="text-lg font-semibold text-white mb-2">{title}</h3>
        <p className="text-sm text-gray-300">{description}</p>
      </div>
    </Link>
  );
}

function ModelStatus({ name, available }: { name: string; available: boolean }) {
  return (
    <div className={`p-4 rounded-xl border ${available ? 'bg-green-500/10 border-green-500/30' : 'bg-red-500/10 border-red-500/30'}`}>
      <div className="flex items-center gap-2 mb-2">
        <div className={`w-2 h-2 rounded-full ${available ? 'bg-green-400' : 'bg-red-400'}`}></div>
        <span className="text-white text-sm font-medium capitalize">{name}</span>
      </div>
      <span className={`text-xs ${available ? 'text-green-300' : 'text-red-300'}`}>
        {available ? 'Available' : 'Offline'}
      </span>
    </div>
  );
}