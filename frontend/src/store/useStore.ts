import { create } from 'zustand';
import type { ChatMessage, Conversation, UserSettings } from '../types';

interface AppState {
  theme: 'light' | 'dark' | 'system';
  setTheme: (theme: 'light' | 'dark' | 'system') => void;

  sidebarOpen: boolean;
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;

  conversations: Conversation[];
  setConversations: (convs: Conversation[]) => void;
  activeConversationId: string | null;
  setActiveConversationId: (id: string | null) => void;

  messages: ChatMessage[];
  setMessages: (msgs: ChatMessage[]) => void;
  addMessage: (msg: ChatMessage) => void;
  updateLastMessage: (content: string) => void;

  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
  isStreaming: boolean;
  setIsStreaming: (streaming: boolean) => void;

  settings: UserSettings;
  setSettings: (settings: Partial<UserSettings>) => void;

  currentPage: 'chat' | 'analytics' | 'settings' | 'about';
  setCurrentPage: (page: 'chat' | 'analytics' | 'settings' | 'about') => void;

  isDemoMode: boolean;
  setIsDemoMode: (demo: boolean) => void;
}

const getInitialTheme = (): 'light' | 'dark' | 'system' => {
  const stored = localStorage.getItem('theme');
  if (stored === 'light' || stored === 'dark' || stored === 'system') return stored;
  return 'system';
};

export const useStore = create<AppState>((set) => ({
  theme: getInitialTheme(),
  setTheme: (theme) => {
    localStorage.setItem('theme', theme);
    set({ theme });
  },

  sidebarOpen: true,
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  setSidebarOpen: (open) => set({ sidebarOpen: open }),

  conversations: [],
  setConversations: (conversations) => set({ conversations }),
  activeConversationId: null,
  setActiveConversationId: (id) => set({ activeConversationId: id }),

  messages: [],
  setMessages: (messages) => set({ messages }),
  addMessage: (msg) => set((s) => ({ messages: [...s.messages, msg] })),
  updateLastMessage: (content) =>
    set((s) => {
      const msgs = [...s.messages];
      if (msgs.length > 0) {
        msgs[msgs.length - 1] = { ...msgs[msgs.length - 1], content };
      }
      return { messages: msgs };
    }),

  isLoading: false,
  setIsLoading: (isLoading) => set({ isLoading }),
  isStreaming: false,
  setIsStreaming: (isStreaming) => set({ isStreaming }),

  settings: {
    theme: 'system',
    language: 'en',
    temperature: 0.7,
    max_tokens: 2048,
    timestamps_enabled: true,
    sentiment_enabled: true,
    compact_mode: false,
    auto_scroll: true,
    suggestions_enabled: true,
  },
  setSettings: (partial) =>
    set((s) => ({ settings: { ...s.settings, ...partial } })),

  currentPage: 'chat',
  setCurrentPage: (currentPage) => set({ currentPage }),

  isDemoMode: false,
  setIsDemoMode: (isDemoMode) => set({ isDemoMode }),
}));
