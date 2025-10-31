'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { ArrowLeft, RefreshCw, TrendingUp, CheckCircle, ExternalLink } from 'lucide-react';

interface RankingModel {
  id: number;
  model_name: string;
  rank: number;
  score: number;
  notes: string;
  update_date: string;
  source_name: string;
  source_url: string;
  category?: string;
}

interface CategoryRankings {
  [key: string]: RankingModel[];
}

type Category = { key: string; label: string; icon: string; description: string; color: string };
const CATEGORIES: Category[] = [
  { 
    key: 'reasoning', 
    label: 'Reasoning & Logic',
    icon: '🧠',
    description: 'MMLU, ARC, complex problem solving',
    color: 'from-purple-500 to-purple-600'
  },
  { 
    key: 'coding', 
    label: 'Coding & Development',
    icon: '💻',
    description: 'HumanEval, MBPP, code generation',
    color: 'from-blue-500 to-blue-600'
  },
  { 
    key: 'vision', 
    label: 'Vision & Multimodal',
    icon: '👁️',
    description: 'MMMU, image understanding',
    color: 'from-green-500 to-green-600'
  },
  { 
    key: 'chat', 
    label: 'Chat & General AI',
    icon: '💬',
    description: 'Chatbot Arena, human preferences',
    color: 'from-orange-500 to-orange-600'
  },
  { 
    key: 'agents', 
    label: 'Agents & Tool Use',
    icon: '🤖',
    description: 'AgentBench, function calling',
    color: 'from-pink-500 to-pink-600'
  },
  { 
    key: 'translation', 
    label: 'Translation & Language',
    icon: '🌍',
    description: 'FLORES, multilingual tasks',
    color: 'from-cyan-500 to-cyan-600'
  },
  { 
    key: 'local', 
    label: 'Local & Open Source',
    icon: '🏠',
    description: 'Ollama, HuggingFace models',
    color: 'from-teal-500 to-teal-600'
  }
];

export default function ModelsRankingPage() {
  const [rankings, setRankings] = useState<CategoryRankings>({});
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<string>('');
  const [selectedModel, setSelectedModel] = useState<RankingModel | null>(null);
  const [showDetails, setShowDetails] = useState(false);

  useEffect(() => {
    loadRankings();
  }, []);

  const loadRankings = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/rankings');
      const data = await response.json();
      setRankings(data);
      
      // Получаем дату последнего обновления
      const dates = Object.values(data).flat().map((m: RankingModel) => m.update_date);
      if (dates.length > 0) {
        const latest = dates.sort().reverse()[0];
        setLastUpdate(latest);
      }
    } catch (error) {
      console.error('Error loading rankings:', error);
    } finally {
      setLoading(false);
    }
  };

  const getBestUseCases = (category: string): string[] => {
    const useCases: Record<string, string[]> = {
      'reasoning': ['Complex problem solving', 'Mathematical reasoning', 'Logic puzzles', 'Academic research'],
      'coding': ['Code generation', 'Bug fixing', 'Code review', 'API development'],
      'vision': ['Image analysis', 'OCR', 'Visual Q&A', 'Scene understanding'],
      'chat': ['General conversation', 'Customer support', 'Creative writing', 'Brainstorming'],
      'agents': ['Tool use', 'Function calling', 'Multi-step tasks', 'Automation'],
      'translation': ['Multilingual tasks', 'Document translation', 'Localization'],
      'local': ['Privacy-focused', 'Offline usage', 'Self-hosted', 'Custom fine-tuning']
    };
    return useCases[category] || [];
  };

  const updateRankings = async () => {
    setUpdating(true);
    try {
      const response = await fetch('http://localhost:8000/api/rankings/update', {
        method: 'POST'
      });
      const data = await response.json();
      
      if (data.success) {
        await loadRankings();
        alert(`✅ Updated ${data.total_updated} models!`);
      }
    } catch (error) {
      console.error('Error updating rankings:', error);
      alert('❌ Error updating rankings');
    } finally {
      setUpdating(false);
    }
  };

  const formatDate = (dateString: string) => {
    if (!dateString) return 'Unknown';
    return new Date(dateString).toLocaleDateString('ru-RU', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900">
      {/* Header */}
      <header className="bg-black/30 backdrop-blur-md border-b border-white/10 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link href="/">
                <button className="w-10 h-10 bg-white/10 hover:bg-white/20 rounded-lg flex items-center justify-center text-white transition">
                  <ArrowLeft className="w-5 h-5" />
                </button>
              </Link>
              <div>
                <h1 className="text-2xl font-bold text-white">AI Models Ranking</h1>
                <p className="text-sm text-gray-400">
                  Топ-3 AI модели по направлениям
                  {lastUpdate && ` • Обновлено: ${formatDate(lastUpdate)}`}
                </p>
              </div>
            </div>

            <button
              onClick={updateRankings}
              disabled={updating}
              className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 disabled:opacity-50 rounded-lg text-white font-medium transition"
            >
              <RefreshCw className={`w-4 h-4 ${updating ? 'animate-spin' : ''}`} />
              {updating ? 'Обновление...' : 'Обновить данные'}
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {loading ? (
          <div className="text-center py-12">
            <RefreshCw className="w-12 h-12 text-blue-400 animate-spin mx-auto mb-4" />
            <p className="text-gray-400">Загрузка рейтингов...</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {CATEGORIES.map((category) => (
              <CategoryCard
                key={category.key}
                category={category}
                models={rankings[category.key] || []}
                formatDate={formatDate}
                onModelClick={(model) => { setSelectedModel(model); setShowDetails(true); }}
              />
            ))}
          </div>
        )}

        {/* Info */}
        <div className="mt-8 bg-blue-500/10 border border-blue-500/30 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-2 flex items-center gap-2">
            <TrendingUp className="w-5 h-5" />
            О рейтингах
          </h3>
          <p className="text-gray-300 text-sm">
            Данные собираются из проверенных источников: HuggingFace Leaderboards, 
            Artificial Analysis, Chatbot Arena (LMSYS), Papers with Code. 
            Рейтинги обновляются еженедельно или по запросу.
          </p>
        </div>
      </main>
      {/* Model Details Modal */}
      {showDetails && selectedModel && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-6" onClick={() => setShowDetails(false)}>
          <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl border border-white/20 max-w-2xl w-full p-8" onClick={(e) => e.stopPropagation()}>
            {/* Header */}
            <div className="flex items-start justify-between mb-6">
              <div>
                <div className="flex items-center gap-3 mb-2">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-lg ${
                    selectedModel.rank === 1 ? 'bg-yellow-500 text-black' :
                    selectedModel.rank === 2 ? 'bg-gray-400 text-black' :
                    'bg-orange-600 text-white'
                  }`}>
                    #{selectedModel.rank}
                  </div>
                  <div>
                    <h2 className="text-2xl font-bold text-white">{selectedModel.model_name}</h2>
                    <p className="text-gray-400 text-sm">{selectedModel.category}</p>
                  </div>
                </div>
              </div>
              <button onClick={() => setShowDetails(false)} className="w-10 h-10 bg-white/10 hover:bg-white/20 rounded-lg flex items-center justify-center text-white transition">✕</button>
            </div>

            {/* Score */}
            <div className="grid grid-cols-2 gap-4 mb-6">
              <div className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-4">
                <div className="text-sm text-gray-400 mb-1">Score</div>
                <div className="text-3xl font-bold text-white">{selectedModel.score}</div>
              </div>
              <div className="bg-green-500/10 border border-green-500/30 rounded-xl p-4">
                <div className="text-sm text-gray-400 mb-1">Rank</div>
                <div className="text-3xl font-bold text-white">#{selectedModel.rank}</div>
              </div>
            </div>

            {/* Details */}
            <div className="space-y-4">
              <div>
                <h3 className="text-white font-semibold mb-2">Performance Notes</h3>
                <p className="text-gray-300 text-sm">{selectedModel.notes}</p>
              </div>
              <div>
                <h3 className="text-white font-semibold mb-2">Source</h3>
                <div className="flex items-center gap-2 text-sm">
                  <span className="text-gray-300">{selectedModel.source_name}</span>
                  {selectedModel.source_url && (
                    <>
                      <span className="text-gray-500">•</span>
                      <a href={selectedModel.source_url} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:text-blue-300 flex items-center gap-1">
                        View Source
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    </>
                  )}
                </div>
              </div>
              <div>
                <h3 className="text-white font-semibold mb-2">Last Updated</h3>
                <p className="text-gray-300 text-sm">{formatDate(selectedModel.update_date)}</p>
              </div>
              {/* Best Use Cases */}
              <div>
                <h3 className="text-white font-semibold mb-2">Best For</h3>
                <div className="flex flex-wrap gap-2">
                  {getBestUseCases(selectedModel.category || '').map((useCase, idx) => (
                    <span key={idx} className="px-3 py-1 bg-purple-500/20 border border-purple-500/30 rounded-lg text-purple-300 text-sm">
                      {useCase}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="mt-6 flex gap-3">
              <button onClick={() => setShowDetails(false)} className="flex-1 px-4 py-2 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 rounded-lg text-white font-medium transition">
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function CategoryCard({ category, models, formatDate, onModelClick }: { category: Category; models: RankingModel[]; formatDate: (s: string) => string; onModelClick: (m: RankingModel) => void }) {
  return (
    <div className="bg-white/5 backdrop-blur-md rounded-2xl border border-white/10 p-6 hover:bg-white/10 transition">
      {/* Category Header */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className={`w-12 h-12 bg-gradient-to-br ${category.color} rounded-xl flex items-center justify-center text-2xl`}>
              {category.icon}
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">{category.label}</h2>
              <p className="text-sm text-gray-400">{category.description}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Models List */}
      <div className="space-y-3">
        {models.length === 0 ? (
          <p className="text-gray-500 text-center py-4">No data</p>
        ) : (
          models.map((model: RankingModel) => (
            <div
              key={model.id}
              onClick={() => onModelClick(model)}
              className="bg-black/30 rounded-lg p-4 hover:bg-black/40 transition cursor-pointer"
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-3">
                  {/* Rank Badge */}
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${
                    model.rank === 1 ? 'bg-yellow-500 text-black' :
                    model.rank === 2 ? 'bg-gray-400 text-black' :
                    'bg-orange-600 text-white'
                  }`}>
                    {model.rank}
                  </div>
                  
                  <div>
                    <h3 className="text-white font-semibold">{model.model_name}</h3>
                    <p className="text-sm text-gray-400">{model.notes}</p>
                  </div>
                </div>

                {/* Score */}
                <div className="text-right">
                  <div className="text-2xl font-bold text-white">{model.score}</div>
                  <div className="text-xs text-gray-400">score</div>
                </div>
              </div>

              {/* Source */}
              {model.source_name && (
                <div className="flex items-center gap-2 mt-2 text-xs text-gray-400">
                  <CheckCircle className="w-3 h-3" />
                  <span>Source: {model.source_name}</span>
                  <span>•</span>
                  <span>{formatDate(model.update_date)}</span>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}