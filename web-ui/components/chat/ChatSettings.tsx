'use client';

import React, { memo } from 'react';

interface ChatSettingsProps {
  taskType: string;
  budget: string;
  complexity: number;
  streamEnabled: boolean;
  contextEnabled: boolean;
  sessionId: string;
  messageCount: number;
  onTaskTypeChange: (value: string) => void;
  onBudgetChange: (value: string) => void;
  onComplexityChange: (value: number) => void;
  onStreamToggle: () => void;
  onContextToggle: () => void;
  onNewChat: () => void;
}

const ChatSettings = memo(function ChatSettings({
  taskType,
  budget,
  complexity,
  streamEnabled,
  contextEnabled,
  sessionId,
  messageCount,
  onTaskTypeChange,
  onBudgetChange,
  onComplexityChange,
  onStreamToggle,
  onContextToggle,
  onNewChat
}: ChatSettingsProps) {
  return (
    <div className="bg-white/5 backdrop-blur-md rounded-2xl border border-white/10 p-6 mb-6">
      <div className="grid grid-cols-1 md:grid-cols-6 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Task Type
          </label>
          <select
            value={taskType}
            onChange={(e) => onTaskTypeChange(e.target.value)}
            className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="code">Code Generation</option>
            <option value="architecture">Architecture</option>
            <option value="review">Code Review</option>
            <option value="test">Testing</option>
            <option value="devops">DevOps</option>
            <option value="research">Research</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Budget
          </label>
          <select
            value={budget}
            onChange={(e) => onBudgetChange(e.target.value)}
            className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="free">Free (Gemini/Ollama)</option>
            <option value="cheap">Cheap (DeepSeek)</option>
            <option value="medium">Medium (GPT-4)</option>
            <option value="premium">Premium (Claude)</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Complexity: {complexity}
          </label>
          <input
            type="range"
            min="1"
            max="10"
            value={complexity}
            onChange={(e) => onComplexityChange(Number(e.target.value))}
            className="w-full h-2 bg-white/10 rounded-lg appearance-none cursor-pointer"
          />
        </div>

        {/* Streaming Toggle */}
        <div>
          <label className="block text-sm text-gray-400 mb-2">Streaming</label>
          <button
            onClick={onStreamToggle}
            className={`w-full px-4 py-2 rounded-lg font-medium transition ${
              streamEnabled ? 'bg-green-500 text-white' : 'bg-gray-700 text-gray-300'
            }`}
          >
            {streamEnabled ? '✓ Enabled' : '✗ Disabled'}
          </button>
        </div>

        {/* Context Toggle */}
        <div>
          <label className="block text-sm text-gray-400 mb-2">Context Memory</label>
          <button
            onClick={onContextToggle}
            className={`w-full px-4 py-2 rounded-lg font-medium transition ${
              contextEnabled ? 'bg-purple-500 text-white' : 'bg-gray-700 text-gray-300'
            }`}
          >
            {contextEnabled ? '✓ Enabled' : '✗ Disabled'}
          </button>
        </div>

        {/* New Chat Button */}
        <div>
          <label className="block text-sm text-gray-400 mb-2">&nbsp;</label>
          <button
            onClick={onNewChat}
            className="w-full px-4 py-2 bg-gradient-to-r from-pink-500 to-red-500 hover:from-pink-600 hover:to-red-600 rounded-lg text-white font-medium transition"
          >
            🔄 New Chat
          </button>
        </div>
      </div>

      {/* Context Info */}
      {contextEnabled && sessionId && (
        <div className="mt-4 col-span-2 bg-purple-500/10 border border-purple-500/30 rounded-xl p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm font-medium text-white mb-1">Context Memory Active</div>
              <div className="text-xs text-gray-400">
                Session: {sessionId.slice(0, 8)}... • {messageCount} messages
              </div>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-purple-400">{messageCount * 50}</div>
              <div className="text-xs text-gray-400">~tokens</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
});

export default ChatSettings;