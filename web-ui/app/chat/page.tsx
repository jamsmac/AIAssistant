'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { ArrowLeft, Send, Zap, Loader2 } from 'lucide-react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  model?: string;
  cost?: number;
  tokens?: number;
  cached?: boolean;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [taskType, setTaskType] = useState<string>('code');
  const [budget, setBudget] = useState<string>('cheap');
  const [complexity, setComplexity] = useState<number>(5);
  const [streamEnabled, setStreamEnabled] = useState(true); // По умолчанию включен
  const [sessionId, setSessionId] = useState<string>('');
  const [contextEnabled, setContextEnabled] = useState(true);

  useEffect(() => {
    // Создаем или восстанавливаем сессию
    const savedSessionId = typeof window !== 'undefined' ? localStorage.getItem('currentSessionId') : null;
    if (savedSessionId) {
      setSessionId(savedSessionId);
    } else {
      createNewSession();
    }
  }, []);

  const createNewSession = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/sessions/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      const data = await response.json();
      setSessionId(data.session_id);
      if (typeof window !== 'undefined') localStorage.setItem('currentSessionId', data.session_id);
      setMessages([]);
    } catch (error) {
      console.error('Error creating session:', error);
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage: Message = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    const currentInput = input;
    setInput('');
    setLoading(true);

    if (streamEnabled) {
      try {
        // Создаем пустое сообщение ассистента
        const assistantMessageIndex = messages.length + 1;
        setMessages(prev => [...prev, { role: 'assistant', content: '', model: '' }]);

        const response = await fetch('http://localhost:8000/api/chat/stream', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            prompt: userMessage.content,
            task_type: taskType,
            complexity: complexity,
            budget: budget,
            session_id: contextEnabled ? sessionId : null
          })
        });

        const reader = response.body?.getReader();
        const decoder = new TextDecoder();

        if (reader) {
          let accumulatedText = '';
          let currentModel = '';

          while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');

            for (const line of lines) {
              if (line.startsWith('data: ')) {
                try {
                  const data = JSON.parse(line.slice(6));

                  if (data.type === 'metadata') {
                    currentModel = data.model;
                  } else if (data.type === 'content') {
                    accumulatedText += data.chunk;
                    // Обновляем сообщение в реальном времени
                    setMessages(prev => {
                      const newMessages = [...prev];
                      newMessages[assistantMessageIndex] = {
                        role: 'assistant',
                        content: accumulatedText,
                        model: currentModel
                      };
                      return newMessages;
                    });
                  } else if (data.type === 'done') {
                    // можно обработать завершение
                    // tokens: data.tokens
                  }
                } catch (e) {
                  console.error('Parse error:', e);
                }
              }
            }
          }
        }
      } catch (error) {
        console.error('Streaming error:', error);
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `Error: ${error instanceof Error ? error.message : String(error)}`,
          model: 'error'
        }]);
      } finally {
        setLoading(false);
      }
    } else {
      // Обычный режим (без streaming)
      try {
        const response = await fetch('http://localhost:8000/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            prompt: currentInput,
            task_type: taskType,
            complexity: complexity,
            budget: budget,
            session_id: contextEnabled ? sessionId : null
          })
        });

        const data = await response.json();

        setMessages(prev => [...prev, {
          role: 'assistant',
          content: data.response,
          model: data.model,
          cost: data.cost,
          tokens: data.tokens
        }]);
      } catch (error) {
        console.error('Error:', error);
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `Error: ${error instanceof Error ? error.message : String(error)}`,
          model: 'error'
        }]);
      } finally {
        setLoading(false);
      }
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
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
              <h1 className="text-2xl font-bold text-white">AI Chat</h1>
              <p className="text-sm text-gray-400">Общайся с AI моделями</p>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-5xl mx-auto px-6 py-6 pb-20 md:pb-6">
        {/* Settings Panel */}
        <div className="bg-white/5 backdrop-blur-md rounded-2xl border border-white/10 p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-6 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Task Type
              </label>
              <select
                value={taskType}
                onChange={(e) => setTaskType(e.target.value)}
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
                onChange={(e) => setBudget(e.target.value)}
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
                onChange={(e) => setComplexity(Number(e.target.value))}
                className="w-full h-2 bg-white/10 rounded-lg appearance-none cursor-pointer"
              />
            </div>

            {/* Streaming Toggle */}
            <div>
              <label className="block text-sm text-gray-400 mb-2">Streaming</label>
              <button
                onClick={() => setStreamEnabled(!streamEnabled)}
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
                onClick={() => setContextEnabled(!contextEnabled)}
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
                onClick={createNewSession}
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
                    Session: {sessionId.slice(0, 8)}... • {messages.length} messages
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-purple-400">{messages.length * 50}</div>
                  <div className="text-xs text-gray-400">~tokens</div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Chat Messages */}
        <div className="bg-white/5 backdrop-blur-md rounded-2xl border border-white/10 p-6 mb-6 h-[500px] overflow-y-auto">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center">
              <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center mb-4">
                <Zap className="w-8 h-8 text-white" />
              </div>
              <h2 className="text-xl font-semibold text-white mb-2">
                Start chatting with AI
              </h2>
              <p className="text-gray-400 max-w-md">
                Задай любой вопрос или попроси сгенерировать код. Система автоматически выберет лучшую модель.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {messages.map((message, index) => (
                <div
                  key={index}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] rounded-2xl p-4 ${
                      message.role === 'user'
                        ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white'
                        : 'bg-white/10 text-gray-100'
                    }`}
                  >
                    <div className="whitespace-pre-wrap">{message.content}</div>
                    {message.model && (
                      <div className="mt-3 pt-3 border-t border-white/20">
                        <div className="flex items-center gap-3 text-xs">
                          <div className="flex items-center gap-1 text-gray-400">
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            {message.model}
                          </div>
                          {message.tokens !== undefined && (
                            <div className="flex items-center gap-1 text-gray-400">
                              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" />
                              </svg>
                              {message.tokens} tokens
                            </div>
                          )}
                          {message.cached && (
                            <div className="flex items-center gap-1 text-green-400">
                              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                              </svg>
                              Cached
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
              {/* Advanced Typing indicator */}
              {loading && streamEnabled && (
                <div className="flex gap-3 justify-start">
                  <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-blue-500 rounded-lg flex items-center justify-center flex-shrink-0">
                    <svg className="w-4 h-4 text-white animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                  </div>
                  <div className="bg-white/10 rounded-2xl px-4 py-3 min-w-[200px]">
                    <div className="flex items-center gap-3">
                      <div className="flex gap-1">
                        <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                        <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                        <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                      </div>
                      <span className="text-xs text-gray-400">AI is thinking...</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Input */}
        <div className="bg-white/5 backdrop-blur-md rounded-2xl border border-white/10 p-4">
          <div className="flex gap-4">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Напиши свой вопрос... (Enter для отправки)"
              className="flex-1 bg-white/10 border border-white/20 rounded-lg px-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              rows={3}
              disabled={loading}
            />
            <button
              onClick={sendMessage}
              disabled={loading || !input.trim()}
              className="px-6 bg-gradient-to-br from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-white font-medium transition flex items-center gap-2"
            >
              {loading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}