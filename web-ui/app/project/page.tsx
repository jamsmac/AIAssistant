'use client';

import { useState } from 'react';
import Link from 'next/link';
import { ArrowLeft, Rocket, Loader2, CheckCircle, Download } from 'lucide-react';
import { API_URL } from '@/lib/config';

type ModelResult = { model: string; response: string; cost: number; tokens: number };
interface ProjectResult {
  project_id: string;
  architecture: ModelResult;
  code: ModelResult;
  review: ModelResult;
  total_cost: number;
  status: string;
}

export default function CreateProjectPage() {
  const [idea, setIdea] = useState('');
  const [budget, setBudget] = useState<string>('medium');
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState('');
  const [result, setResult] = useState<ProjectResult | null>(null);
  const [error, setError] = useState('');

  const createProject = async () => {
    if (!idea.trim() || idea.length < 10) {
      setError('Описание проекта должно быть минимум 10 символов');
      return;
    }

    setLoading(true);
    setError('');
    setResult(null);
    setProgress(0);

    // Симуляция прогресса
    const progressInterval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 90) {
          clearInterval(progressInterval);
          return 90;
        }
        return prev + 10;
      });
    }, 3000);

    try {
      // Этап 1: Архитектура
      setCurrentStep('Создание архитектуры...');
      
      const response = await fetch(`${API_URL}/api/project`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ idea, budget })
      });

      clearInterval(progressInterval);

      if (!response.ok) {
        throw new Error('Ошибка при создании проекта');
      }

      const data = await response.json();
      setResult(data);
      setProgress(100);
      setCurrentStep('Готово!');
      
    } catch (err) {
      clearInterval(progressInterval);
      setError(err instanceof Error ? err.message : 'Произошла ошибка');
      setProgress(0);
    } finally {
      setLoading(false);
    }
  };

  const downloadResult = (content: string, filename: string) => {
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900">
      {/* Header */}
      <header className="bg-black/30 backdrop-blur-md border-b border-white/10">
        <div className="max-w-5xl mx-auto px-6 py-4">
          <div className="flex items-center gap-4">
            <Link href="/">
              <button className="w-10 h-10 bg-white/10 hover:bg-white/20 rounded-lg flex items-center justify-center text-white transition">
                <ArrowLeft className="w-5 h-5" />
              </button>
            </Link>
            <div>
              <h1 className="text-2xl font-bold text-white">Create Project</h1>
              <p className="text-sm text-gray-400">Создай полный проект из идеи</p>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-8 pb-20 md:pb-8">
        {/* Form */}
        {!result && (
          <div className="bg-white/5 backdrop-blur-md rounded-2xl border border-white/10 p-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl flex items-center justify-center">
                <Rocket className="w-6 h-6 text-white" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-white">Опиши свою идею</h2>
                <p className="text-sm text-gray-400">AI создаст архитектуру, код и ревью</p>
              </div>
            </div>

            <div className="space-y-6">
              {/* Project Idea */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Идея проекта *
                </label>
                <textarea
                  value={idea}
                  onChange={(e) => setIdea(e.target.value)}
                  placeholder="Например: CRM система для управления вендинговыми автоматами с панелью аналитики и мобильным приложением"
                  className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none"
                  rows={5}
                  disabled={loading}
                />
                <div className="text-xs text-gray-400 mt-1">
                  Минимум 10 символов. Чем детальнее описание, тем лучше результат.
                </div>
              </div>

              {/* Budget */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Бюджет
                </label>
                <select
                  value={budget}
                  onChange={(e) => setBudget(e.target.value)}
                  className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                  disabled={loading}
                >
                  <option value="free">Free - Gemini/Ollama (бесплатно, медленнее)</option>
                  <option value="cheap">Cheap - DeepSeek (~$0.001)</option>
                  <option value="medium">Medium - GPT-4 (~$0.02) ⭐ Рекомендуется</option>
                  <option value="premium">Premium - Claude ($0.05+, лучшее качество)</option>
                </select>
              </div>

              {/* Error */}
              {error && (
                <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
                  <p className="text-red-300 text-sm">{error}</p>
                </div>
              )}

              {/* Create Button */}
              <button
                onClick={createProject}
                disabled={loading || !idea.trim()}
                className="w-full bg-gradient-to-br from-purple-500 to-purple-600 hover:from-purple-600 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg px-6 py-4 text-white font-medium transition flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Создаю проект...
                  </>
                ) : (
                  <>
                    <Rocket className="w-5 h-5" />
                    Создать проект
                  </>
                )}
              </button>
            </div>

            {/* Progress */}
            {loading && (
              <div className="mt-8">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-300">{currentStep}</span>
                  <span className="text-sm text-gray-300">{progress}%</span>
                </div>
                <div className="w-full bg-white/10 rounded-full h-2 overflow-hidden">
                  <div
                    className="bg-gradient-to-r from-purple-500 to-blue-500 h-full transition-all duration-500"
                    style={{ width: `${progress}%` }}
                  />
                </div>
                <p className="text-xs text-gray-400 mt-2">
                  Это займет 30-60 секунд. AI создает архитектуру, генерирует код и делает ревью.
                </p>
              </div>
            )}
          </div>
        )}

        {/* Results */}
        {result && (
          <div className="space-y-6">
            {/* Success Header */}
            <div className="bg-gradient-to-br from-green-500/20 to-green-600/20 backdrop-blur-md rounded-2xl border border-green-500/30 p-6">
              <div className="flex items-center gap-3 mb-4">
                <CheckCircle className="w-8 h-8 text-green-400" />
                <div>
                  <h2 className="text-2xl font-bold text-white">Проект создан!</h2>
                  <p className="text-gray-300">ID: {result.project_id}</p>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-sm text-gray-400">Статус</div>
                  <div className="text-lg font-semibold text-green-300 capitalize">{result.status}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-400">Общая стоимость</div>
                  <div className="text-lg font-semibold text-white">${result.total_cost.toFixed(6)}</div>
                </div>
              </div>
            </div>

            {/* Architecture */}
            <ResultCard
              title="📐 Architecture"
              model={result.architecture.model}
              cost={result.architecture.cost}
              tokens={result.architecture.tokens}
              content={result.architecture.response}
              onDownload={() => downloadResult(result.architecture.response, 'architecture.md')}
            />

            {/* Code */}
            <ResultCard
              title="💻 Generated Code"
              model={result.code.model}
              cost={result.code.cost}
              tokens={result.code.tokens}
              content={result.code.response}
              onDownload={() => downloadResult(result.code.response, 'code.txt')}
            />

            {/* Review */}
            <ResultCard
              title="🔍 Code Review"
              model={result.review.model}
              cost={result.review.cost}
              tokens={result.review.tokens}
              content={result.review.response}
              onDownload={() => downloadResult(result.review.response, 'review.md')}
            />

            {/* Create Another */}
            <button
              onClick={() => {
                setResult(null);
                setIdea('');
                setProgress(0);
              }}
              className="w-full bg-white/10 hover:bg-white/20 rounded-lg px-6 py-3 text-white font-medium transition"
            >
              Создать еще один проект
            </button>
          </div>
        )}
      </main>
    </div>
  );
}

function ResultCard({ title, model, cost, tokens, content, onDownload }: { title: string; model: string; cost: number; tokens: number; content: string; onDownload: () => void }) {
  const [expanded, setExpanded] = useState(false);
  const preview = content.substring(0, 300);

  return (
    <div className="bg-white/5 backdrop-blur-md rounded-2xl border border-white/10 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">{title}</h3>
        <button
          onClick={onDownload}
          className="flex items-center gap-2 px-3 py-1.5 bg-white/10 hover:bg-white/20 rounded-lg text-sm text-white transition"
        >
          <Download className="w-4 h-4" />
          Download
        </button>
      </div>

      <div className="flex items-center gap-4 mb-4 text-sm text-gray-400">
        <span>Model: {model}</span>
        <span>•</span>
        <span>${cost.toFixed(6)}</span>
        <span>•</span>
        <span>{tokens} tokens</span>
      </div>

      <div className="bg-black/30 rounded-lg p-4 font-mono text-sm text-gray-300 whitespace-pre-wrap">
        {expanded ? content : preview}
        {content.length > 300 && !expanded && '...'}
      </div>

      {content.length > 300 && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="mt-3 text-sm text-blue-400 hover:text-blue-300 transition"
        >
          {expanded ? 'Свернуть' : 'Показать полностью'}
        </button>
      )}
    </div>
  );
}