'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { API_URL } from '@/lib/config';
import {
  ArrowLeft,
  Search,
  Filter,
  Download, 
  
  DollarSign,
  MessageSquare,
  Database,
  TrendingUp,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';

interface HistoryItem {
  id: number;
  timestamp: string;
  prompt: string;
  response: string;
  model: string;
  task_type: string;
  complexity: number;
  budget: string;
  tokens: number;
  cost: number;
  error: number;
  created_at: string;
}

interface HistoryStats {
  general: {
    total_requests: number;
    total_tokens: number;
    total_cost: number;
    avg_cost: number;
    first_request: string;
    last_request: string;
  };
  by_model: Array<{
    model: string;
    count: number;
    tokens: number;
    cost: number;
  }>;
  by_task: Array<{
    task_type: string;
    count: number;
    avg_cost: number;
  }>;
  by_date: Array<{
    date: string;
    count: number;
    cost: number;
  }>;
}

export default function HistoryPage() {
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [stats, setStats] = useState<HistoryStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedItem, setSelectedItem] = useState<HistoryItem | null>(null);
  
  // Фильтры
  const [searchQuery, setSearchQuery] = useState('');
  const [modelFilter, setModelFilter] = useState('');
  const [taskFilter, setTaskFilter] = useState('');
  const [page, setPage] = useState(1);
  const [limit] = useState(20);

  // Загрузка данных
  const loadHistory = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        limit: limit.toString(),
        offset: ((page - 1) * limit).toString(),
        ...(modelFilter && { model: modelFilter }),
        ...(taskFilter && { task_type: taskFilter }),
        ...(searchQuery && { search: searchQuery })
      });

      const response = await fetch(`${API_URL}/api/history?${params}`);
      const data = await response.json();
      setHistory(data.items || []);
    } catch (error) {
      console.error('Error loading history:', error);
    } finally {
      setLoading(false);
    }
  }, [limit, page, modelFilter, taskFilter, searchQuery]);

  const loadStats = async () => {
    try {
      const response = await fetch(`${API_URL}/api/stats`);
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Error loading stats:', error);
    }
  };

  useEffect(() => {
    loadHistory();
    loadStats();
  }, [loadHistory]);

  const exportData = async (format: 'json' | 'csv') => {
    try {
      const params = new URLSearchParams({ format });
      const response = await fetch(`${API_URL}/api/history/export?${params}`);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `history_${new Date().toISOString().split('T')[0]}.${format}`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting:', error);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('ru-RU', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const uniqueModels = Array.from(new Set(history.map(h => h.model)));
  const uniqueTasks = Array.from(new Set(history.map(h => h.task_type).filter(Boolean)));

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900">
      {/* Header */}
      <header className="bg-black/30 backdrop-blur-md border-b border-white/10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link href="/">
                <button className="w-10 h-10 bg-white/10 hover:bg-white/20 rounded-lg flex items-center justify-center text-white transition">
                  <ArrowLeft className="w-5 h-5" />
                </button>
              </Link>
              <div>
                <h1 className="text-2xl font-bold text-white">Request History</h1>
                <p className="text-sm text-gray-400">История всех запросов к AI</p>
              </div>
            </div>

            {/* Export buttons */}
            <div className="flex gap-2">
              <button
                onClick={() => exportData('json')}
                className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-white transition flex items-center gap-2"
              >
                <Download className="w-4 h-4" />
                JSON
              </button>
              <button
                onClick={() => exportData('csv')}
                className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-white transition flex items-center gap-2"
              >
                <Download className="w-4 h-4" />
                CSV
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8 pb-20 md:pb-8">
        {/* Stats Cards */}
        {stats && stats.general && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <StatCard
              icon={MessageSquare}
              label="Total Requests"
              value={stats.general.total_requests}
              color="blue"
            />
            <StatCard
              icon={Database}
              label="Total Tokens"
              value={stats.general.total_tokens.toLocaleString()}
              color="purple"
            />
            <StatCard
              icon={DollarSign}
              label="Total Cost"
              value={`$${stats.general.total_cost.toFixed(4)}`}
              color="green"
            />
            <StatCard
              icon={TrendingUp}
              label="Avg Cost"
              value={`$${stats.general.avg_cost.toFixed(6)}`}
              color="orange"
            />
          </div>
        )}

        {/* Filters */}
        <div className="bg-white/5 backdrop-blur-md rounded-2xl border border-white/10 p-6 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <Filter className="w-5 h-5 text-gray-400" />
            <h2 className="text-lg font-semibold text-white">Filters</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Search */}
            <div>
              <label className="block text-sm text-gray-400 mb-2">Search</label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search in prompts..."
                  className="w-full bg-white/10 border border-white/20 rounded-lg pl-10 pr-4 py-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            {/* Model filter */}
            <div>
              <label className="block text-sm text-gray-400 mb-2">Model</label>
              <select
                value={modelFilter}
                onChange={(e) => setModelFilter(e.target.value)}
                className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All models</option>
                {uniqueModels.map(model => (
                  <option key={model} value={model}>{model}</option>
                ))}
              </select>
            </div>

            {/* Task type filter */}
            <div>
              <label className="block text-sm text-gray-400 mb-2">Task Type</label>
              <select
                value={taskFilter}
                onChange={(e) => setTaskFilter(e.target.value)}
                className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All tasks</option>
                {uniqueTasks.map(task => (
                  <option key={task} value={task}>{task}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Clear filters */}
          {(searchQuery || modelFilter || taskFilter) && (
            <button
              onClick={() => {
                setSearchQuery('');
                setModelFilter('');
                setTaskFilter('');
              }}
              className="mt-4 text-sm text-blue-400 hover:text-blue-300 transition"
            >
              Clear all filters
            </button>
          )}
        </div>

        {/* History list */}
        <div className="space-y-4">
          {loading ? (
            <div className="text-center py-12 text-gray-400">Loading...</div>
          ) : history.length === 0 ? (
            <div className="text-center py-12">
              <Database className="w-16 h-16 text-gray-600 mx-auto mb-4" />
              <p className="text-gray-400">No requests found</p>
            </div>
          ) : (
            history.map((item) => (
              <HistoryCard
                key={item.id}
                item={item}
                onClick={() => setSelectedItem(item)}
                formatDate={formatDate}
              />
            ))
          )}
        </div>

        {/* Pagination */}
        {history.length > 0 && (
          <div className="flex items-center justify-center gap-4 mt-8">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-4 py-2 bg-white/10 hover:bg-white/20 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-white transition flex items-center gap-2"
            >
              <ChevronLeft className="w-4 h-4" />
              Previous
            </button>
            <span className="text-white">Page {page}</span>
            <button
              onClick={() => setPage(p => p + 1)}
              disabled={history.length < limit}
              className="px-4 py-2 bg-white/10 hover:bg-white/20 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-white transition flex items-center gap-2"
            >
              Next
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        )}
      </main>

      {/* Detail Modal */}
      {selectedItem && (
        <DetailModal
          item={selectedItem}
          onClose={() => setSelectedItem(null)}
          formatDate={formatDate}
        />
      )}
    </div>
  );
}

interface StatCardProps {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string | number;
  color: 'blue' | 'purple' | 'green' | 'orange';
}

function StatCard({ icon: Icon, label, value, color }: StatCardProps) {
  const colors = {
    blue: 'from-blue-500 to-blue-600',
    purple: 'from-purple-500 to-purple-600',
    green: 'from-green-500 to-green-600',
    orange: 'from-orange-500 to-orange-600'
  };

  return (
    <div className="bg-white/5 backdrop-blur-md rounded-xl border border-white/10 p-4">
      <div className="flex items-center gap-3">
        <div className={`w-10 h-10 bg-gradient-to-br ${colors[color]} rounded-lg flex items-center justify-center`}>
          <Icon className="w-5 h-5 text-white" />
        </div>
        <div>
          <div className="text-sm text-gray-400">{label}</div>
          <div className="text-xl font-bold text-white">{value}</div>
        </div>
      </div>
    </div>
  );
}

function HistoryCard({ item, onClick, formatDate }: { item: HistoryItem; onClick: () => void; formatDate: (s: string) => string }) {
  return (
    <div
      onClick={onClick}
      className="bg-white/5 backdrop-blur-md rounded-xl border border-white/10 p-6 hover:bg-white/10 cursor-pointer transition"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="w-2 h-2 bg-green-400 rounded-full" />
          <span className="text-sm font-medium text-blue-300">{item.model}</span>
          {item.task_type && (
            <span className="px-2 py-0.5 bg-purple-500/20 text-purple-300 rounded text-xs">
              {item.task_type}
            </span>
          )}
        </div>
        <div className="text-right">
          <div className="text-sm text-gray-400">{formatDate(item.timestamp)}</div>
          <div className="text-sm font-medium text-green-300">${item.cost.toFixed(6)}</div>
        </div>
      </div>

      <div className="text-white font-medium mb-2 line-clamp-1">{item.prompt}</div>
      <div className="text-gray-400 text-sm line-clamp-2">{item.response}</div>

      <div className="flex items-center gap-4 mt-3 text-xs text-gray-400">
        <span>{item.tokens} tokens</span>
        {item.complexity && <span>Complexity: {item.complexity}</span>}
        {item.budget && <span>Budget: {item.budget}</span>}
      </div>
    </div>
  );
}

function DetailModal({ item, onClose, formatDate }: { item: HistoryItem; onClose: () => void; formatDate: (s: string) => string }) {
  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 z-50" onClick={onClose}>
      <div className="bg-gray-900 rounded-2xl border border-white/20 max-w-4xl w-full max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
        <div className="p-6 border-b border-white/10">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-xl font-bold text-white">Request Details</h2>
            <button onClick={onClose} className="text-gray-400 hover:text-white">✕</button>
          </div>
          <div className="flex items-center gap-3 text-sm">
            <span className="text-blue-300 font-medium">{item.model}</span>
            <span className="text-gray-400">•</span>
            <span className="text-gray-400">{formatDate(item.timestamp)}</span>
            <span className="text-gray-400">•</span>
            <span className="text-green-300 font-medium">${item.cost.toFixed(6)}</span>
          </div>
        </div>

        <div className="p-6 space-y-6">
          <div>
            <div className="text-sm text-gray-400 mb-2">Prompt</div>
            <div className="bg-black/30 rounded-lg p-4 text-white whitespace-pre-wrap">{item.prompt}</div>
          </div>

          <div>
            <div className="text-sm text-gray-400 mb-2">Response</div>
            <div className="bg-black/30 rounded-lg p-4 text-white whitespace-pre-wrap">{item.response}</div>
          </div>

          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <div className="text-gray-400">Tokens</div>
              <div className="text-white font-medium">{item.tokens}</div>
            </div>
            {item.task_type && (
              <div>
                <div className="text-gray-400">Task Type</div>
                <div className="text-white font-medium">{item.task_type}</div>
              </div>
            )}
            {item.complexity && (
              <div>
                <div className="text-gray-400">Complexity</div>
                <div className="text-white font-medium">{item.complexity}</div>
              </div>
            )}
            {item.budget && (
              <div>
                <div className="text-gray-400">Budget</div>
                <div className="text-white font-medium">{item.budget}</div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
