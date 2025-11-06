'use client';

import React, { memo } from 'react';
import { FileText, ImageIcon, File, AlertTriangle, XCircle } from 'lucide-react';

interface FileAttachment {
  name: string;
  type: string;
  content: string;
  size: number;
}

interface Message {
  role: 'user' | 'assistant' | 'error';
  content: string;
  model?: string;
  cost?: number;
  tokens?: number;
  cached?: boolean;
  file?: FileAttachment;
  error?: boolean;
  errorType?: 'timeout' | 'rate_limit' | 'validation' | 'server' | 'network';
}

interface ChatMessageProps {
  message: Message;
  isStreaming?: boolean;
}

const ChatMessage = memo(function ChatMessage({ message, isStreaming = false }: ChatMessageProps) {
  const renderFilePreview = (file: FileAttachment) => {
    const isImage = file.type.startsWith('image/');
    const isPdf = file.type === 'application/pdf';

    return (
      <div className="mb-2 p-2 bg-gray-700/50 rounded-lg inline-block">
        <div className="flex items-center gap-2">
          {isImage ? (
            <ImageIcon className="w-4 h-4 text-blue-400" />
          ) : isPdf ? (
            <FileText className="w-4 h-4 text-red-400" />
          ) : (
            <File className="w-4 h-4 text-gray-400" />
          )}
          <span className="text-sm text-gray-300">{file.name}</span>
          <span className="text-xs text-gray-500">
            ({Math.round(file.size / 1024)}KB)
          </span>
        </div>
        {isImage && (
          <img
            src={file.content}
            alt={file.name}
            className="mt-2 max-w-xs rounded"
          />
        )}
      </div>
    );
  };

  // Determine styling based on message type
  const isError = message.error || message.role === 'error';
  const isUser = message.role === 'user';

  const getErrorIcon = () => {
    switch (message.errorType) {
      case 'timeout':
        return <AlertTriangle className="w-5 h-5 text-yellow-400" />;
      case 'rate_limit':
        return <AlertTriangle className="w-5 h-5 text-orange-400" />;
      case 'network':
        return <XCircle className="w-5 h-5 text-red-400" />;
      default:
        return <XCircle className="w-5 h-5 text-red-400" />;
    }
  };

  const getErrorStyles = () => {
    if (!isError) return '';
    switch (message.errorType) {
      case 'timeout':
      case 'rate_limit':
        return 'bg-yellow-900/20 border-yellow-600 text-yellow-100';
      case 'validation':
        return 'bg-orange-900/20 border-orange-600 text-orange-100';
      case 'network':
        return 'bg-red-900/20 border-red-600 text-red-100';
      default:
        return 'bg-red-900/20 border-red-600 text-red-100';
    }
  };

  return (
    <div
      className={`flex ${
        isUser ? 'justify-end' : 'justify-start'
      } mb-4 animate-fadeIn`}
    >
      <div
        className={`max-w-[70%] rounded-lg px-4 py-3 ${
          isError
            ? `${getErrorStyles()} border`
            : isUser
            ? 'bg-blue-600 text-white'
            : 'bg-gray-700 text-gray-100 border border-gray-600'
        }`}
      >
        {/* Error icon for error messages */}
        {isError && (
          <div className="flex items-center gap-2 mb-2">
            {getErrorIcon()}
            <span className="font-semibold text-sm">
              {message.errorType === 'timeout' && 'Request Timeout'}
              {message.errorType === 'rate_limit' && 'Rate Limit Exceeded'}
              {message.errorType === 'validation' && 'Validation Error'}
              {message.errorType === 'network' && 'Network Error'}
              {!message.errorType && 'Error'}
            </span>
          </div>
        )}

        {message.file && renderFilePreview(message.file)}

        <div className="whitespace-pre-wrap break-words">
          {message.content}
          {isStreaming && (
            <span className="inline-block w-1 h-4 ml-1 bg-current animate-pulse" />
          )}
        </div>

        {/* Show retry hint for certain errors */}
        {isError && (message.errorType === 'timeout' || message.errorType === 'rate_limit') && (
          <div className="mt-2 text-xs opacity-75">
            💡 Tip: Try again in a moment or simplify your request
          </div>
        )}

        {message.role === 'assistant' && !isError && (message.model || message.cost !== undefined) && (
          <div className="flex items-center gap-4 mt-2 pt-2 border-t border-gray-600">
            {message.model && (
              <span className="text-xs text-gray-400">
                {message.model}
              </span>
            )}
            {message.tokens && (
              <span className="text-xs text-gray-400">
                {message.tokens} tokens
              </span>
            )}
            {message.cost !== undefined && (
              <span className="text-xs text-gray-400">
                ${message.cost.toFixed(6)}
              </span>
            )}
            {message.cached && (
              <span className="text-xs text-green-400">
                ⚡ Cached
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
});

export default ChatMessage;