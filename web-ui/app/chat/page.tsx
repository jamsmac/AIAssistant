'use client';

import { useState, useEffect, useRef, lazy, Suspense } from 'react';
import Link from 'next/link';
import { ArrowLeft, ChevronRight, Loader2 } from 'lucide-react';
import { API_URL } from '@/lib/config';

// Lazy load components for better performance
const ChatSidebar = lazy(() => import('@/components/chat/ChatSidebar'));
const ChatSettings = lazy(() => import('@/components/chat/ChatSettings'));
const ChatMessages = lazy(() => import('@/components/chat/ChatMessages'));
const ChatInput = lazy(() => import('@/components/chat/ChatInput'));

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

interface ChatSession {
  id: string;
  user_id: number;
  created_at: string;
  updated_at: string;
  message_count: number;
  first_message?: string;
}

// Type for SpeechRecognition API
interface SpeechRecognitionEvent {
  resultIndex: number;
  results: {
    length: number;
    [index: number]: {
      isFinal: boolean;
      [index: number]: {
        transcript: string;
      };
    };
  };
}

interface SpeechRecognitionErrorEvent {
  error: string;
}

interface SpeechRecognitionInstance {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start: () => void;
  stop: () => void;
  onstart: (() => void) | null;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  onerror: ((event: SpeechRecognitionErrorEvent) => void) | null;
  onend: (() => void) | null;
}

// Loading component for Suspense fallback
const LoadingSpinner = () => (
  <div className="flex items-center justify-center p-4">
    <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
  </div>
);

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [taskType, setTaskType] = useState<string>('code');
  const [budget, setBudget] = useState<string>('cheap');
  const [complexity, setComplexity] = useState<number>(5);
  const [streamEnabled, setStreamEnabled] = useState(true);
  const [sessionId, setSessionId] = useState<string>('');
  const [contextEnabled, setContextEnabled] = useState(true);
  const [selectedFile, setSelectedFile] = useState<FileAttachment | null>(null);
  const [fileProcessing, setFileProcessing] = useState(false);
  const [fileError, setFileError] = useState<string | null>(null);

  // Voice input state
  const [isListening, setIsListening] = useState(false);
  const [voiceSupported, setVoiceSupported] = useState(false);
  const [voiceError, setVoiceError] = useState<string | null>(null);
  const recognitionRef = useRef<SpeechRecognitionInstance | null>(null);

  // Sidebar state
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [sessionsLoading, setSessionsLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);
  const searchTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Streaming state
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingMessageIndex, setStreamingMessageIndex] = useState<number | undefined>();

  useEffect(() => {
    // Create or restore session
    const savedSessionId = typeof window !== 'undefined' ? localStorage.getItem('currentSessionId') : null;
    if (savedSessionId) {
      setSessionId(savedSessionId);
    } else {
      createNewSession();
    }
    // Load sessions list
    fetchSessions();

    // Auto-close sidebar on mobile
    const handleResize = () => {
      if (window.innerWidth < 768) {
        setSidebarOpen(false);
      }
    };
    handleResize();
    window.addEventListener('resize', handleResize);

    // Check voice recognition support
    const SpeechRecognition = (window as unknown as { SpeechRecognition?: new () => SpeechRecognitionInstance; webkitSpeechRecognition?: new () => SpeechRecognitionInstance }).SpeechRecognition ||
                              (window as unknown as { SpeechRecognition?: new () => SpeechRecognitionInstance; webkitSpeechRecognition?: new () => SpeechRecognitionInstance }).webkitSpeechRecognition;
    setVoiceSupported(!!SpeechRecognition);

    // Keyboard shortcut for voice input (Ctrl+Shift+V)
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.shiftKey && e.key === 'V') {
        e.preventDefault();
        if (voiceSupported) {
          if (isListening) {
            stopListening();
          } else {
            startListening();
          }
        }
      }
    };
    window.addEventListener('keydown', handleKeyDown);

    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

  const createNewSession = async () => {
    try {
      const response = await fetch(`${API_URL}/api/sessions/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      const data = await response.json();
      setSessionId(data.session_id);
      if (typeof window !== 'undefined') localStorage.setItem('currentSessionId', data.session_id);
      setMessages([]);
      fetchSessions(); // Refresh session list
    } catch (error) {
      console.error('Error creating session:', error);
    }
  };

  const fetchSessions = async () => {
    setSessionsLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/sessions`);
      const data = await response.json();
      setSessions(data.sessions || []);
    } catch (error) {
      console.error('Error fetching sessions:', error);
    } finally {
      setSessionsLoading(false);
    }
  };

  const loadSession = async (session_id: string) => {
    try {
      const response = await fetch(`${API_URL}/api/sessions/${session_id}/messages`);
      const data = await response.json();
      setMessages(data.messages || []);
      setSessionId(session_id);
      if (typeof window !== 'undefined') localStorage.setItem('currentSessionId', session_id);
      // Close sidebar on mobile after loading
      if (window.innerWidth < 768) {
        setSidebarOpen(false);
      }
    } catch (error) {
      console.error('Error loading session:', error);
    }
  };

  const deleteSession = async (session_id: string) => {
    try {
      await fetch(`${API_URL}/api/sessions/${session_id}`, {
        method: 'DELETE'
      });
      // If deleting current session, create new one
      if (session_id === sessionId) {
        await createNewSession();
      }
      fetchSessions(); // Refresh list
      setDeleteConfirm(null);
    } catch (error) {
      console.error('Error deleting session:', error);
    }
  };

  const handleSearch = (query: string) => {
    setSearchQuery(query);
    // Debounce search
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }
    searchTimeoutRef.current = setTimeout(() => {
      fetchSessions();
    }, 300);
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setFileError(null);

    // Validate file size (10MB max)
    if (file.size > 10 * 1024 * 1024) {
      setFileError('File size exceeds 10MB limit');
      return;
    }

    // Validate file type
    const allowedTypes = [
      'application/pdf',
      'image/jpeg',
      'image/jpg',
      'image/png',
      'text/plain'
    ];

    if (!allowedTypes.includes(file.type)) {
      setFileError('Unsupported file type. Please use PDF, JPG, PNG, or TXT files.');
      return;
    }

    setFileProcessing(true);

    try {
      let content = '';

      if (file.type === 'text/plain') {
        // Read text file directly
        content = await file.text();
      } else if (file.type.startsWith('image/')) {
        // Convert image to base64
        const reader = new FileReader();
        content = await new Promise<string>((resolve, reject) => {
          reader.onload = () => resolve(reader.result as string);
          reader.onerror = reject;
          reader.readAsDataURL(file);
        });
      } else if (file.type === 'application/pdf') {
        // For PDF, we'll send base64 and let backend handle extraction
        const reader = new FileReader();
        content = await new Promise<string>((resolve, reject) => {
          reader.onload = () => resolve(reader.result as string);
          reader.onerror = reject;
          reader.readAsDataURL(file);
        });
      }

      setSelectedFile({
        name: file.name,
        type: file.type,
        content: content,
        size: file.size
      });
    } catch (error) {
      console.error('Error processing file:', error);
      setFileError('Failed to process file');
    } finally {
      setFileProcessing(false);
    }
  };

  const removeFile = () => {
    setSelectedFile(null);
    setFileError(null);
  };

  // Voice recognition functions
  const startListening = () => {
    if (!voiceSupported) {
      setVoiceError('Voice recognition is not supported in your browser');
      return;
    }

    setVoiceError(null);
    const SpeechRecognition = (window as unknown as { SpeechRecognition?: new () => SpeechRecognitionInstance; webkitSpeechRecognition?: new () => SpeechRecognitionInstance }).SpeechRecognition ||
                              (window as unknown as { SpeechRecognition?: new () => SpeechRecognitionInstance; webkitSpeechRecognition?: new () => SpeechRecognitionInstance }).webkitSpeechRecognition;

    if (!SpeechRecognition) return;

    const recognition = new SpeechRecognition();

    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = navigator.language || 'en-US';

    recognition.onstart = () => {
      setIsListening(true);
    };

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let finalTranscript = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscript += transcript + ' ';
        }
      }

      // Update input with final transcript
      if (finalTranscript) {
        setInput(prev => prev + finalTranscript);
      }
    };

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      console.error('Speech recognition error:', event.error);
      let errorMessage = 'Voice recognition error';

      switch (event.error) {
        case 'no-speech':
          errorMessage = 'No speech detected. Please try again.';
          break;
        case 'audio-capture':
          errorMessage = 'Microphone not found or not accessible';
          break;
        case 'not-allowed':
          errorMessage = 'Microphone access denied. Please grant permission.';
          break;
        case 'network':
          errorMessage = 'Network error during voice recognition';
          break;
        default:
          errorMessage = `Voice recognition error: ${event.error}`;
      }

      setVoiceError(errorMessage);
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognitionRef.current = recognition;
    recognition.start();
  };

  const stopListening = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      recognitionRef.current = null;
    }
    setIsListening(false);
  };

  const sendMessage = async () => {
    if (!input.trim() && !selectedFile) return;
    if (loading) return;

    const userMessage: Message = {
      role: 'user',
      content: input,
      file: selectedFile || undefined
    };
    setMessages(prev => [...prev, userMessage]);
    const currentInput = input;
    const currentFile = selectedFile;
    setInput('');
    setSelectedFile(null);
    setLoading(true);

    if (streamEnabled) {
      try {
        // Create empty assistant message
        const assistantMessageIndex = messages.length + 1;
        setMessages(prev => [...prev, { role: 'assistant', content: '', model: '' }]);
        setIsStreaming(true);
        setStreamingMessageIndex(assistantMessageIndex);

        const response = await fetch(`${API_URL}/api/chat/stream`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            prompt: currentInput,
            task_type: taskType,
            complexity: complexity,
            budget: budget,
            session_id: contextEnabled ? sessionId : null,
            file: currentFile ? {
              name: currentFile.name,
              type: currentFile.type,
              content: currentFile.content
            } : undefined
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
                    // Update message in real-time
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
                    // Handle completion
                    if (data.tokens) {
                      setMessages(prev => {
                        const newMessages = [...prev];
                        newMessages[assistantMessageIndex] = {
                          ...newMessages[assistantMessageIndex],
                          tokens: data.tokens,
                          cost: data.cost
                        };
                        return newMessages;
                      });
                    }
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
        setIsStreaming(false);
        setStreamingMessageIndex(undefined);
      }
    } else {
      // Non-streaming mode
      try {
        const response = await fetch(`${API_URL}/api/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            prompt: currentInput,
            task_type: taskType,
            complexity: complexity,
            budget: budget,
            session_id: contextEnabled ? sessionId : null,
            file: currentFile ? {
              name: currentFile.name,
              type: currentFile.type,
              content: currentFile.content
            } : undefined
          })
        });

        const data = await response.json();

        if (data.error) {
          throw new Error(data.error);
        }

        setMessages(prev => [...prev, {
          role: 'assistant',
          content: data.response || 'No response received',
          model: data.model,
          cost: data.cost,
          tokens: data.tokens,
          cached: data.cached
        }]);
      } catch (error) {
        console.error('Chat error:', error);
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-900 flex">
      {/* Sidebar */}
      <Suspense fallback={<LoadingSpinner />}>
        <ChatSidebar
          sessions={sessions}
          currentSessionId={sessionId}
          sidebarOpen={sidebarOpen}
          searchQuery={searchQuery}
          deleteConfirm={deleteConfirm}
          sessionsLoading={sessionsLoading}
          onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
          onNewSession={createNewSession}
          onLoadSession={loadSession}
          onDeleteSession={deleteSession}
          onSearchChange={handleSearch}
          onSetDeleteConfirm={setDeleteConfirm}
        />
      </Suspense>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="bg-black/30 backdrop-blur-md border-b border-white/10">
          <div className="max-w-5xl mx-auto px-6 py-4">
            <div className="flex items-center gap-4">
              {/* Sidebar Toggle */}
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="w-10 h-10 bg-white/10 hover:bg-white/20 rounded-lg flex items-center justify-center text-white transition"
              >
                <ChevronRight className={`w-5 h-5 transform ${sidebarOpen ? 'rotate-180' : ''} transition-transform`} />
              </button>
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

        <div className="max-w-5xl mx-auto px-6 py-6 pb-20 md:pb-6 w-full">
          {/* Settings Panel */}
          <Suspense fallback={<LoadingSpinner />}>
            <ChatSettings
              taskType={taskType}
              budget={budget}
              complexity={complexity}
              streamEnabled={streamEnabled}
              contextEnabled={contextEnabled}
              sessionId={sessionId}
              messageCount={messages.length}
              onTaskTypeChange={setTaskType}
              onBudgetChange={setBudget}
              onComplexityChange={setComplexity}
              onStreamToggle={() => setStreamEnabled(!streamEnabled)}
              onContextToggle={() => setContextEnabled(!contextEnabled)}
              onNewChat={createNewSession}
            />
          </Suspense>

          {/* Chat Messages */}
          <Suspense fallback={<LoadingSpinner />}>
            <ChatMessages
              messages={messages}
              isStreaming={isStreaming}
              streamingMessageIndex={streamingMessageIndex}
            />
          </Suspense>

          {/* Loading Indicator - shown when AI is thinking */}
          {loading && !isStreaming && (
            <div className="flex items-center justify-center gap-3 py-4 animate-fadeIn">
              <div className="flex items-center gap-2 px-4 py-2 bg-gray-700/50 rounded-lg border border-gray-600">
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                </div>
                <span className="text-sm text-gray-300">AI is thinking...</span>
              </div>
            </div>
          )}

          {/* Input Area */}
          <Suspense fallback={<LoadingSpinner />}>
            <ChatInput
              input={input}
              loading={loading}
              selectedFile={selectedFile}
              fileProcessing={fileProcessing}
              fileError={fileError}
              isListening={isListening}
              voiceSupported={voiceSupported}
              voiceError={voiceError}
              onInputChange={setInput}
              onSendMessage={sendMessage}
              onFileSelect={handleFileSelect}
              onRemoveFile={removeFile}
              onStartListening={startListening}
              onStopListening={stopListening}
            />
          </Suspense>
        </div>
      </div>
    </div>
  );
}