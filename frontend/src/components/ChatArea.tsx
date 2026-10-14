import React, { useEffect, useRef } from 'react';
import {
  Menu,
  Download,
  Sparkles,
  MessageCircle,
  Brain,
  Lightbulb,
  Code,
  HelpCircle,
} from 'lucide-react';
import { useStore } from '../store/useStore';
import { MessageBubble, TypingIndicator } from './MessageBubble';
import { ChatInput } from './ChatInput';
import { exportConversation } from '../services/api';

interface ChatAreaProps {
  onSendMessage: (
    message: string,
    imageData?: string,
    audioData?: string,
    fileName?: string,
    ragDocumentTitle?: string,
  ) => void;
}

const QUICK_PROMPTS = [
  { icon: <Brain size={16} />, text: 'Explain machine learning in simple terms' },
  { icon: <Code size={16} />, text: 'Help me understand Python decorators' },
  { icon: <Lightbulb size={16} />, text: '#rag What are the key features of this chatbot?' },
  { icon: <HelpCircle size={16} />, text: 'What NLP and AI capabilities are supported?' },
];

export function ChatArea({ onSendMessage }: ChatAreaProps) {
  const {
    messages,
    isLoading,
    activeConversationId,
    loadingConversationId,
    toggleSidebar,
    settings,
    isDemoMode,
  } = useStore();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (settings.auto_scroll && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isLoading, settings.auto_scroll]);

  const handleExport = async (format: 'json' | 'txt' | 'md') => {
    if (!activeConversationId) return;
    try {
      const content = await exportConversation(activeConversationId, format);
      const blob = new Blob([content], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `conversation.${format}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Export failed:', err);
    }
  };

  const isEmpty = messages.length === 0;

  return (
    <div className="flex flex-col h-full">
      <header className="flex items-center justify-between px-4 py-3 border-b border-surface-200 dark:border-surface-800 bg-white/80 dark:bg-surface-900/80 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <button onClick={toggleSidebar} className="btn-ghost p-1.5 lg:hidden text-surface-600 dark:text-surface-300" aria-label="Toggle sidebar">
            <Menu size={20} />
          </button>
          <div>
            <h2 className="font-semibold text-sm">Chat</h2>
            {isDemoMode && (
              <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 font-medium">
                Demo Mode — Real Local NLP, RAG, Voice & Vision Active
              </span>
            )}
          </div>
        </div>
        {activeConversationId && messages.length > 0 && (
          <div className="flex items-center gap-1">
            <button onClick={() => handleExport('json')} className="btn-ghost text-xs gap-1" aria-label="Export JSON">
              <Download size={14} /> JSON
            </button>
            <button onClick={() => handleExport('txt')} className="btn-ghost text-xs gap-1" aria-label="Export TXT">
              <Download size={14} /> TXT
            </button>
          </div>
        )}
      </header>

      <div className="flex-1 overflow-y-auto px-4">
        <div className="max-w-3xl mx-auto py-4">
          {loadingConversationId ? (
            <ConversationLoadingSkeleton />
          ) : isEmpty ? (
            <EmptyState onPromptClick={(p) => onSendMessage(p)} />
          ) : (
            <>
              {messages.map((msg) => (
                <MessageBubble
                  key={msg.id}
                  message={msg}
                  onSelectSuggestion={(s) => onSendMessage(s)}
                />
              ))}
              {isLoading && <TypingIndicator />}
            </>
          )}
          <div ref={bottomRef} />
        </div>
      </div>

      <ChatInput onSend={onSendMessage} />
    </div>
  );
}

function ConversationLoadingSkeleton() {
  return (
    <div className="flex flex-col gap-6 py-6 animate-pulse" aria-label="Loading conversation history">
      <div className="flex items-center justify-center gap-2 mb-4 p-2 rounded-xl bg-surface-100 dark:bg-surface-800/60 w-fit mx-auto border border-surface-200 dark:border-surface-700/60 shadow-xs">
        <div className="w-3.5 h-3.5 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
        <span className="text-xs font-medium text-surface-600 dark:text-surface-300">Loading conversation history...</span>
      </div>

      {/* Assistant message skeleton */}
      <div className="flex items-start gap-3">
        <div className="w-8 h-8 rounded-xl bg-surface-200 dark:bg-surface-700 shrink-0" />
        <div className="space-y-2 max-w-md w-full">
          <div className="h-4 bg-surface-200 dark:bg-surface-700 rounded-md w-3/4" />
          <div className="h-4 bg-surface-200 dark:bg-surface-700 rounded-md w-1/2" />
        </div>
      </div>

      {/* User message skeleton */}
      <div className="flex items-start gap-3 justify-end">
        <div className="space-y-2 max-w-sm w-full">
          <div className="h-4 bg-primary-200 dark:bg-primary-900/50 rounded-md w-full ml-auto" />
          <div className="h-4 bg-primary-200 dark:bg-primary-900/50 rounded-md w-2/3 ml-auto" />
        </div>
        <div className="w-8 h-8 rounded-xl bg-primary-200 dark:bg-primary-900/50 shrink-0" />
      </div>

      {/* Assistant response skeleton */}
      <div className="flex items-start gap-3">
        <div className="w-8 h-8 rounded-xl bg-surface-200 dark:bg-surface-700 shrink-0" />
        <div className="space-y-2 max-w-lg w-full">
          <div className="h-4 bg-surface-200 dark:bg-surface-700 rounded-md w-5/6" />
          <div className="h-4 bg-surface-200 dark:bg-surface-700 rounded-md w-4/6" />
          <div className="h-4 bg-surface-200 dark:bg-surface-700 rounded-md w-2/6" />
        </div>
      </div>
    </div>
  );
}

function EmptyState({ onPromptClick }: { onPromptClick: (text: string) => void }) {
  return (
    <div className="flex flex-col items-center justify-center h-full min-h-[60vh] animate-fade-in">
      <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-500 to-emerald-500 flex items-center justify-center mb-6 shadow-lg shadow-primary-500/20">
        <Sparkles size={28} className="text-white" />
      </div>
      <h2 className="text-2xl font-semibold mb-2">Welcome to Dynamic AI</h2>
      <p className="text-surface-500 dark:text-surface-400 mb-8 text-center max-w-md">
        Your intelligent conversational assistant. Ask anything, get contextual responses,
        and explore insights.
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-lg">
        {QUICK_PROMPTS.map((prompt, i) => (
          <button
            key={i}
            onClick={() => onPromptClick(prompt.text)}
            className="card p-4 text-left hover:border-primary-300 dark:hover:border-primary-700 transition-all group"
          >
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-lg bg-primary-50 dark:bg-primary-900/20 text-primary-600 dark:text-primary-400 group-hover:bg-primary-100 dark:group-hover:bg-primary-900/30 transition-colors">
                {prompt.icon}
              </div>
              <span className="text-sm text-surface-600 dark:text-surface-300 leading-relaxed">
                {prompt.text}
              </span>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
