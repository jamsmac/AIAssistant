'use client';

import React, { memo, useRef } from 'react';
import { Send, Paperclip, X, FileText, Image as ImageIcon, File, Mic, Loader2 } from 'lucide-react';

interface FileAttachment {
  name: string;
  type: string;
  content: string;
  size: number;
}

interface ChatInputProps {
  input: string;
  loading: boolean;
  selectedFile: FileAttachment | null;
  fileProcessing: boolean;
  fileError: string | null;
  isListening: boolean;
  voiceSupported: boolean;
  voiceError: string | null;
  onInputChange: (value: string) => void;
  onSendMessage: () => void;
  onFileSelect: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onRemoveFile: () => void;
  onStartListening: () => void;
  onStopListening: () => void;
}

const ChatInput = memo(function ChatInput({
  input,
  loading,
  selectedFile,
  fileProcessing,
  fileError,
  isListening,
  voiceSupported,
  voiceError,
  onInputChange,
  onSendMessage,
  onFileSelect,
  onRemoveFile,
  onStartListening,
  onStopListening
}: ChatInputProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSendMessage();
    }
  };

  const handleVoiceToggle = () => {
    if (isListening) {
      onStopListening();
    } else {
      onStartListening();
    }
  };

  const renderFilePreview = () => {
    if (!selectedFile) return null;

    const isImage = selectedFile.type.startsWith('image/');
    const isPdf = selectedFile.type === 'application/pdf';

    return (
      <div className="mb-3 p-3 bg-gray-800 rounded-lg border border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {isImage ? (
              <ImageIcon className="w-5 h-5 text-blue-400" />
            ) : isPdf ? (
              <FileText className="w-5 h-5 text-red-400" />
            ) : (
              <File className="w-5 h-5 text-gray-400" />
            )}
            <div>
              <div className="text-sm text-white">{selectedFile.name}</div>
              <div className="text-xs text-gray-400">
                {Math.round(selectedFile.size / 1024)} KB
              </div>
            </div>
          </div>
          <button
            onClick={onRemoveFile}
            className="p-1 hover:bg-gray-700 rounded transition"
            title="Remove file"
          >
            <X className="w-4 h-4 text-gray-400" />
          </button>
        </div>
        {isImage && (
          <img
            src={selectedFile.content}
            alt={selectedFile.name}
            className="mt-3 max-h-32 rounded"
          />
        )}
      </div>
    );
  };

  return (
    <div className="bg-white/5 backdrop-blur-md rounded-2xl border border-white/10 p-6">
      {/* File Error */}
      {fileError && (
        <div className="mb-3 p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
          <div className="text-sm text-red-400">{fileError}</div>
        </div>
      )}

      {/* Voice Error */}
      {voiceError && (
        <div className="mb-3 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
          <div className="text-sm text-yellow-400">{voiceError}</div>
        </div>
      )}

      {/* File Preview */}
      {renderFilePreview()}

      {/* Input Area */}
      <div className="flex gap-2">
        <input
          type="file"
          ref={fileInputRef}
          onChange={onFileSelect}
          accept=".pdf,.jpg,.jpeg,.png,.txt"
          className="hidden"
        />

        {/* File Upload Button */}
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={loading || fileProcessing}
          className={`w-12 h-12 flex items-center justify-center rounded-lg transition ${
            fileProcessing
              ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
              : 'bg-white/10 hover:bg-white/20 text-white'
          }`}
          title="Attach file"
        >
          {fileProcessing ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <Paperclip className="w-5 h-5" />
          )}
        </button>

        {/* Voice Input Button */}
        {voiceSupported && (
          <button
            onClick={handleVoiceToggle}
            disabled={loading}
            className={`w-12 h-12 flex items-center justify-center rounded-lg transition ${
              isListening
                ? 'bg-red-500 hover:bg-red-600 text-white animate-pulse'
                : 'bg-white/10 hover:bg-white/20 text-white'
            }`}
            title={isListening ? 'Stop recording' : 'Start voice input (Ctrl+Shift+V)'}
          >
            <Mic className="w-5 h-5" />
          </button>
        )}

        {/* Text Input */}
        <textarea
          value={input}
          onChange={(e) => onInputChange(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder={isListening ? 'Listening...' : 'Type your message or use voice input...'}
          className="flex-1 bg-white/10 border border-white/20 rounded-lg px-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
          rows={1}
          disabled={loading}
          style={{ minHeight: '48px', maxHeight: '200px' }}
        />

        {/* Send Button */}
        <button
          onClick={onSendMessage}
          disabled={loading || (!input.trim() && !selectedFile)}
          className={`w-12 h-12 rounded-lg flex items-center justify-center transition ${
            loading || (!input.trim() && !selectedFile)
              ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
              : 'bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white'
          }`}
        >
          {loading ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <Send className="w-5 h-5" />
          )}
        </button>
      </div>

      {/* Voice Recording Indicator */}
      {isListening && (
        <div className="mt-3 flex items-center gap-2 text-sm text-red-400">
          <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
          Recording... Speak clearly
        </div>
      )}
    </div>
  );
});

export default ChatInput;