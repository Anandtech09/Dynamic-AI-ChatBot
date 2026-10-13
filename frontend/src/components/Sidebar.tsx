import React from 'react';
import {
  MessageSquarePlus,
  BarChart3,
  Settings,
  Info,
  MessageCircle,
  Trash2,
  X,
  Bot,
  Mic,
  Image as ImageIcon,
  BookOpen,
  Code,
  FileText,
} from 'lucide-react';
import { useStore } from '../store/useStore';
import type { Conversation } from '../types';

interface SidebarProps {
  onNewChat: () => void;
  onSelectConversation: (id: string) => void;
  onDeleteConversation: (id: string) => void;
}

function getCleanTitle(raw: string, category?: string): string {
  if (!raw || raw === 'New Conversation') {
    if (category === 'Voice Query') return '🎙️ Voice Note';
    if (category === 'Vision Analysis') return '📷 Photo Analysis';
    if (category === 'RAG Docs') return '📄 Document Query';
    if (category === 'Code & Tech') return '💻 Code Assistant';
    return 'New Conversation';
  }
  const trimmed = raw.trim();
  if (trimmed.startsWith('{') || trimmed.includes('"intent"') || trimmed.includes('"sentiment"')) {
    try {
      const parsed = JSON.parse(trimmed);
      if (parsed.title) return String(parsed.title);
    } catch {}
    if (category === 'Voice Query') return '🎙️ Voice Note';
    if (category === 'Vision Analysis') return '📷 Photo Analysis';
    if (category === 'RAG Docs') return '📄 Document Query';
    return 'Conversation';
  }
  return raw;
}

function getCategoryBadgeClass(cat: string): string {
  switch (cat) {
    case 'RAG Docs':
      return 'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300';
    case 'Code & Tech':
      return 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300';
    case 'Voice Query':
      return 'bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-300';
    case 'Vision Analysis':
      return 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300';
    case 'FAQ Help':
      return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300';
    default:
      return 'bg-surface-200 text-surface-600 dark:bg-surface-800 dark:text-surface-400';
  }
}

export function Sidebar({ onNewChat, onSelectConversation, onDeleteConversation }: SidebarProps) {
  const {
    sidebarOpen,
    setSidebarOpen,
    conversations,
    activeConversationId,
    currentPage,
    setCurrentPage,
    isDemoMode,
  } = useStore();

  const handleNav = (page: 'chat' | 'analytics' | 'settings' | 'about') => {
    setCurrentPage(page);
    // Only auto-close on mobile screens (< 1024px)
    if (typeof window !== 'undefined' && window.innerWidth < 1024) {
      setSidebarOpen(false);
    }
  };

  const handleNewChatClick = () => {
    onNewChat();
    setCurrentPage('chat');
    if (typeof window !== 'undefined' && window.innerWidth < 1024) {
      setSidebarOpen(false);
    }
  };

  const handleSelectConv = (id: string) => {
    onSelectConversation(id);
    setCurrentPage('chat');
    if (typeof window !== 'undefined' && window.innerWidth < 1024) {
      setSidebarOpen(false);
    }
  };

  return (
    <>
      {/* Mobile backdrop overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/40 backdrop-blur-xs z-40 lg:hidden transition-opacity duration-300"
          onClick={() => setSidebarOpen(false)}
          aria-label="Close sidebar overlay"
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-50 h-full flex flex-col w-72 max-w-[85vw]
          bg-white dark:bg-surface-900 border-r border-surface-200 dark:border-surface-800
          transition-transform duration-300 ease-in-out shrink-0
          lg:static lg:z-auto lg:max-w-none lg:translate-x-0
          ${sidebarOpen ? 'translate-x-0 shadow-2xl lg:shadow-none' : '-translate-x-full lg:translate-x-0'}`}
      >
        <div className="flex flex-col h-full w-full">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-surface-200 dark:border-surface-800">
            <div
              className="flex items-center gap-2.5 cursor-pointer hover:opacity-85 transition-opacity"
              onClick={() => handleNav('chat')}
              title="Go to Chat"
            >
              <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center shadow-sm">
                <Bot size={18} className="text-white" />
              </div>
              <div>
                <h1 className="font-semibold text-sm">Dynamic AI</h1>
                {isDemoMode && (
                  <span className="text-[10px] text-amber-600 dark:text-amber-400 font-medium">DEMO MODE</span>
                )}
              </div>
            </div>
            {/* Close button for mobile only */}
            <button
              onClick={() => setSidebarOpen(false)}
              className="btn-ghost p-1.5 lg:hidden text-surface-500 hover:text-surface-900 dark:hover:text-surface-100"
              aria-label="Close sidebar"
            >
              <X size={18} />
            </button>
          </div>

          {/* New Chat Button */}
          <div className="p-3">
            <button onClick={handleNewChatClick} className="btn-primary w-full" id="new-chat-btn">
              <MessageSquarePlus size={16} />
              New Chat
            </button>
          </div>

          {/* Conversations List */}
          <div className="flex-1 overflow-y-auto px-2 pb-2">
            <p className="text-xs font-medium text-surface-400 dark:text-surface-500 px-2 py-2 uppercase tracking-wider">
              Recent Conversations
            </p>
            {conversations.length === 0 ? (
              <p className="text-xs text-surface-400 dark:text-surface-500 px-2 py-4 text-center">
                No conversations yet
              </p>
            ) : (
              <div className="space-y-1">
                {conversations.map((conv) => (
                  <ConversationItem
                    key={conv.id}
                    conversation={conv}
                    isActive={conv.id === activeConversationId && currentPage === 'chat'}
                    onSelect={() => handleSelectConv(conv.id)}
                    onDelete={() => onDeleteConversation(conv.id)}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Navigation */}
          <div className="border-t border-surface-200 dark:border-surface-800 p-2 space-y-0.5">
            <NavButton
              icon={<BarChart3 size={16} />}
              label="Analytics"
              active={currentPage === 'analytics'}
              onClick={() => handleNav('analytics')}
            />
            <NavButton
              icon={<Settings size={16} />}
              label="Settings"
              active={currentPage === 'settings'}
              onClick={() => handleNav('settings')}
            />
            <NavButton
              icon={<Info size={16} />}
              label="About"
              active={currentPage === 'about'}
              onClick={() => handleNav('about')}
            />
          </div>
        </div>
      </aside>
    </>
  );
}

function ConversationItem({
  conversation,
  isActive,
  onSelect,
  onDelete,
}: {
  conversation: Conversation;
  isActive: boolean;
  onSelect: () => void;
  onDelete: () => void;
}) {
  const category = conversation.category || 'General AI';
  const displayTitle = getCleanTitle(conversation.title, category);

  let CategoryIcon = MessageCircle;
  let iconColor = 'opacity-60 text-primary-600 dark:text-primary-400';

  if (category === 'Voice Query') {
    CategoryIcon = Mic;
    iconColor = 'text-rose-500 dark:text-rose-400';
  } else if (category === 'Vision Analysis') {
    CategoryIcon = ImageIcon;
    iconColor = 'text-amber-500 dark:text-amber-400';
  } else if (category === 'RAG Docs') {
    CategoryIcon = BookOpen;
    iconColor = 'text-purple-500 dark:text-purple-400';
  } else if (category === 'Code & Tech') {
    CategoryIcon = Code;
    iconColor = 'text-blue-500 dark:text-blue-400';
  }

  return (
    <div
      className={`group flex flex-col gap-1 px-3 py-2.5 rounded-xl cursor-pointer transition-all duration-150
        ${isActive
          ? 'bg-primary-50 dark:bg-primary-900/20 text-primary-900 dark:text-primary-100 font-medium ring-1 ring-primary-500/30'
          : 'hover:bg-surface-100 dark:hover:bg-surface-800/80 text-surface-700 dark:text-surface-300'
        }`}
      onClick={onSelect}
    >
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0 flex-1">
          <CategoryIcon size={14} className={`shrink-0 ${iconColor}`} />
          <span className="text-sm font-medium truncate">{displayTitle}</span>
        </div>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onDelete();
          }}
          className="opacity-0 group-hover:opacity-100 p-1 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/30 text-red-500 transition-all shrink-0"
          aria-label="Delete conversation"
          title="Delete conversation"
        >
          <Trash2 size={13} />
        </button>
      </div>

      {/* Purpose / Category Subtitle */}
      <div className="flex items-center gap-1.5 pl-5 text-[11px]">
        <span className={`px-1.5 py-0.5 rounded-md font-medium text-[10px] ${getCategoryBadgeClass(category)}`}>
          {category}
        </span>
        {conversation.message_count > 0 && (
          <span className="text-surface-400 dark:text-surface-500 text-[10px]">
            • {conversation.message_count} {conversation.message_count === 1 ? 'msg' : 'msgs'}
          </span>
        )}
      </div>
    </div>
  );
}

function NavButton({
  icon,
  label,
  active,
  onClick,
}: {
  icon: React.ReactNode;
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-sm font-medium transition-all
        ${active
          ? 'bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-300 shadow-xs'
          : 'text-surface-600 dark:text-surface-400 hover:bg-surface-100 dark:hover:bg-surface-800'
        }`}
    >
      {icon}
      {label}
    </button>
  );
}
