'use client';

import React, { memo } from 'react';
import { Zap } from 'lucide-react';
import ChatMessage from './ChatMessage';

interface FileAttachment {
  name: string;
  type: string;
  content: string;
  size: number;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  model?: string;
  cost?: number;
  tokens?: number;
  cached?: boolean;
  file?: FileAttachment;
}

interface ChatMessagesProps {
  messages: Message[];
  isStreaming?: boolean;
  streamingMessageIndex?: number;
}

const ChatMessages = memo(function ChatMessages({
  messages,
  isStreaming = false,
  streamingMessageIndex
}: ChatMessagesProps) {
  if (messages.length === 0) {
    return (
      <div className="bg-white/5 backdrop-blur-md rounded-2xl border border-white/10 p-6 mb-6 h-[500px] flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center mb-4 mx-auto">
            <Zap className="w-8 h-8 text-white" />
          </div>
          <h2 className="text-xl font-semibold text-white mb-2">
            Start chatting with AI
          </h2>
          <p className="text-gray-400 max-w-md">
            Задай любой вопрос или попроси сгенерировать код. Система автоматически выберет лучшую модель.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white/5 backdrop-blur-md rounded-2xl border border-white/10 p-6 mb-6 h-[500px] overflow-y-auto">
      <div className="space-y-4">
        {messages.map((message, index) => (
          <ChatMessage
            key={index}
            message={message}
            isStreaming={isStreaming && index === streamingMessageIndex}
          />
        ))}
      </div>
    </div>
  );
});

export default ChatMessages;