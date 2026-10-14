import React, { useEffect, useCallback } from 'react';
import { useStore } from './store/useStore';
import { Sidebar } from './components/Sidebar';
import { ChatArea } from './components/ChatArea';
import { AnalyticsDashboard } from './components/AnalyticsDashboard';
import { SettingsPage } from './components/SettingsPage';
import { AboutPage } from './components/AboutPage';
import {
  sendMessage,
  getConversations,
  getConversation,
  deleteConversation as apiDeleteConversation,
  getHealth,
} from './services/api';
import type { ChatMessage } from './types';

function App() {
  const {
    theme,
    currentPage,
    setConversations,
    activeConversationId,
    setActiveConversationId,
    messages,
    setMessages,
    addMessage,
    isLoading,
    setIsLoading,
    settings,
    setIsDemoMode,
  } = useStore();

  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
    } else if (theme === 'light') {
      root.classList.remove('dark');
    } else {
      // System preference
      const mq = window.matchMedia('(prefers-color-scheme: dark)');
      root.classList.toggle('dark', mq.matches);
      const handler = (e: MediaQueryListEvent) => root.classList.toggle('dark', e.matches);
      mq.addEventListener('change', handler);
      return () => mq.removeEventListener('change', handler);
    }
  }, [theme]);

  useEffect(() => {
    loadConversations();
    checkHealth();
  }, []);

  const checkHealth = async () => {
    try {
      const health = await getHealth();
      setIsDemoMode(health.demo_mode);
    } catch {}
  };

  const loadConversations = async () => {
    try {
      const res = await getConversations();
      if (res.data) setConversations(res.data);
    } catch {}
  };

  const handleSendMessage = useCallback(async (
    text: string,
    imageData?: string,
    audioData?: string,
    fileName?: string,
    ragDocumentTitle?: string,
  ) => {
    if (isLoading) return;

    // Add user message immediately
    const userMsg: ChatMessage = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content: text,
      created_at: new Date().toISOString(),
      image_url: imageData,
      audio_url: audioData,
      file_name: fileName,
    };
    addMessage(userMsg);
    setIsLoading(true);

    try {
      const res = await sendMessage(
        text,
        activeConversationId || undefined,
        'default',
        settings.language,
        settings.temperature,
        imageData,
        audioData,
        fileName,
        ragDocumentTitle,
      );

      if (res.success && res.data) {
        // Update conversation ID if this was a new conversation
        if (!activeConversationId) {
          setActiveConversationId(res.data.conversation_id);
        }

        const assistantMsg: ChatMessage = {
          id: res.data.message_id,
          role: 'assistant',
          content: res.data.reply,
          created_at: new Date().toISOString(),
          intent: res.data.intent,
          intent_confidence: res.data.intent_confidence,
          sentiment: res.data.sentiment,
          emotion: res.data.emotion,
          entities: res.data.entities,
          sources: res.data.sources,
          suggestions: res.data.suggestions,
          response_time_ms: res.data.response_time_ms,
          is_rag: res.data.is_rag,
          is_faq: res.data.is_faq,
        };
        addMessage(assistantMsg);
        const convId = activeConversationId || res.data.conversation_id;
        if (convId) {
          const currentMsgs = [...useStore.getState().messages, assistantMsg];
          useStore.getState().cacheConversationMessages(convId, currentMsgs);
        }

        // Refresh conversation list
        loadConversations();
      } else {
        // Error response
        const errorMsg: ChatMessage = {
          id: `error-${Date.now()}`,
          role: 'assistant',
          content: res.error?.message || 'Sorry, something went wrong. Please try again.',
          created_at: new Date().toISOString(),
          is_error: true,
        };
        addMessage(errorMsg);
      }
    } catch (e: any) {
      const errorMsg: ChatMessage = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: 'Unable to connect to the server. Please check that the backend is running.',
        created_at: new Date().toISOString(),
        is_error: true,
      };
      addMessage(errorMsg);
    } finally {
      setIsLoading(false);
    }
  }, [activeConversationId, isLoading, settings.language, settings.temperature]);

  const handleNewChat = useCallback(() => {
    setActiveConversationId(null);
    setMessages([]);
    useStore.getState().setCurrentPage('chat');
  }, []);

  const handleSelectConversation = useCallback(async (id: string) => {
    if (id === activeConversationId) return;
    setActiveConversationId(id);

    const store = useStore.getState();
    const cached = store.conversationCache[id];

    if (cached && cached.length > 0) {
      // 1. Instant Cache Hit: Instantaneous load with zero UI latency
      setMessages(cached);
      store.setLoadingConversationId(null);

      // Background revalidation (SWR pattern)
      try {
        const res = await getConversation(id);
        if (res.data?.messages) {
          store.cacheConversationMessages(id, res.data.messages);
          if (useStore.getState().activeConversationId === id) {
            setMessages(res.data.messages);
          }
        }
      } catch {}
      return;
    }

    // 2. Cache Miss: Display sleek conversation history loader
    store.setLoadingConversationId(id);
    setMessages([]);

    try {
      const res = await getConversation(id);
      if (res.data?.messages) {
        store.cacheConversationMessages(id, res.data.messages);
        if (useStore.getState().activeConversationId === id) {
          setMessages(res.data.messages);
        }
      }
    } catch {
      // Silently fail
    } finally {
      store.setLoadingConversationId(null);
    }
  }, [activeConversationId]);

  const handleDeleteConversation = useCallback(async (id: string) => {
    try {
      await apiDeleteConversation(id);
      useStore.getState().clearConversationCache(id);
      if (activeConversationId === id) {
        setActiveConversationId(null);
        setMessages([]);
      }
      loadConversations();
    } catch {
      // Silently fail
    }
  }, [activeConversationId]);

  const renderPage = () => {
    switch (currentPage) {
      case 'analytics':
        return <AnalyticsDashboard />;
      case 'settings':
        return <SettingsPage />;
      case 'about':
        return <AboutPage />;
      default:
        return <ChatArea onSendMessage={handleSendMessage} />;
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-surface-50 dark:bg-surface-950">
      <Sidebar
        onNewChat={handleNewChat}
        onSelectConversation={handleSelectConversation}
        onDeleteConversation={handleDeleteConversation}
      />
      <main className="flex-1 flex flex-col min-w-0">
        {renderPage()}
      </main>
    </div>
  );
}

export default App;
