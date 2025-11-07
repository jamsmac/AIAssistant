'use client';

import { useState, useEffect } from 'react';
import { useEstimateCost } from '@/hooks/useCredits';
import { Calculator, Loader2, Sparkles, AlertCircle, CheckCircle } from 'lucide-react';

interface CostEstimatorProps {
  prompt: string;
  onEstimateChange?: (cost: number, sufficient: boolean) => void;
}

export default function CostEstimator({ prompt, onEstimateChange }: CostEstimatorProps) {
  const { estimate, loading } = useEstimateCost();
  const [estimation, setEstimation] = useState<any>(null);
  const [show, setShow] = useState(false);

  useEffect(() => {
    // Debounce estimation
    if (!prompt || prompt.length < 10) {
      setEstimation(null);
      setShow(false);
      return;
    }

    const timer = setTimeout(async () => {
      const result = await estimate(prompt);
      if (result) {
        setEstimation(result);
        setShow(true);
        onEstimateChange?.(result.estimated_cost_credits, result.sufficient_credits);
      }
    }, 1000); // Wait 1 second after user stops typing

    return () => clearTimeout(timer);
  }, [prompt]);

  if (!show || !estimation) {
    return null;
  }

  const taskTypeIcons: Record<string, string> = {
    coding: '💻',
    writing: '✍️',
    analysis: '📊',
    translation: '🌐',
    math: '🔢',
    general: '💬',
  };

  const complexityColors: Record<string, string> = {
    simple: 'text-green-400',
    medium: 'text-yellow-400',
    complex: 'text-red-400',
  };

  return (
    <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-4 mb-4 backdrop-blur-sm">
      <div className="flex items-start gap-3">
        <div className="p-2 bg-blue-900/30 rounded-lg">
          <Calculator className="w-5 h-5 text-blue-400" />
        </div>

        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <h3 className="font-semibold text-white">Cost Estimate</h3>
            {loading && <Loader2 className="w-4 h-4 animate-spin text-gray-400" />}
          </div>

          <div className="grid grid-cols-2 gap-4 mb-3">
            {/* Cost */}
            <div>
              <div className="text-xs text-gray-400 mb-1">Estimated Cost</div>
              <div className="flex items-baseline gap-1">
                <span className="text-2xl font-bold text-yellow-400">
                  {estimation.estimated_cost_credits}
                </span>
                <span className="text-sm text-gray-400">credits</span>
              </div>
            </div>

            {/* Balance */}
            <div>
              <div className="text-xs text-gray-400 mb-1">Your Balance</div>
              <div className="flex items-center gap-2">
                <span className="text-lg font-semibold text-gray-300">
                  {estimation.user_balance.toLocaleString()}
                </span>
                {estimation.sufficient_credits ? (
                  <CheckCircle className="w-4 h-4 text-green-400" />
                ) : (
                  <AlertCircle className="w-4 h-4 text-red-400" />
                )}
              </div>
            </div>
          </div>

          {/* Task Info */}
          <div className="flex items-center gap-4 mb-3 text-sm">
            <div className="flex items-center gap-1">
              <span>{taskTypeIcons[estimation.task_analysis.task_type] || '💬'}</span>
              <span className="text-gray-300 capitalize">{estimation.task_analysis.task_type}</span>
            </div>
            <div className="flex items-center gap-1">
              <span className={complexityColors[estimation.task_analysis.complexity]}>●</span>
              <span className="text-gray-300 capitalize">{estimation.task_analysis.complexity}</span>
            </div>
          </div>

          {/* Model Selection */}
          <div className="bg-gray-900/50 rounded-lg p-3 mb-3">
            <div className="flex items-center gap-2 mb-2">
              <Sparkles className="w-4 h-4 text-purple-400" />
              <span className="text-sm font-semibold text-white">Selected Model</span>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-gray-300">
                  {estimation.provider}/{estimation.selected_model}
                </div>
                <div className="text-xs text-gray-400">
                  Quality: {(estimation.quality_score * 100).toFixed(0)}% •{' '}
                  {estimation.credits_per_1k_tokens} credits/1K tokens
                </div>
              </div>
              <div className={`px-2 py-1 rounded text-xs font-semibold ${
                estimation.cost_tier === 'cheap' ? 'bg-green-900/30 text-green-400' :
                estimation.cost_tier === 'expensive' ? 'bg-red-900/30 text-red-400' :
                'bg-yellow-900/30 text-yellow-400'
              }`}>
                {estimation.cost_tier}
              </div>
            </div>
          </div>

          {/* Warning */}
          {!estimation.sufficient_credits && (
            <div className="flex items-center gap-2 bg-red-900/20 border border-red-800 rounded-lg px-3 py-2">
              <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
              <span className="text-sm text-red-300">
                Insufficient credits. Please purchase more credits to continue.
              </span>
            </div>
          )}

          {/* Reasoning */}
          {estimation.reasoning && (
            <div className="text-xs text-gray-500 mt-2 italic">
              {estimation.reasoning}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
