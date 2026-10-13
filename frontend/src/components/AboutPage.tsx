import React from 'react';
import {
  Bot,
  Brain,
  Database,
  Shield,
  Sparkles,
  MessageSquare,
  BarChart3,
  Globe,
  Code,
  BookOpen,
  Wrench,
  ArrowLeft,
  Menu,
  Github,
  ExternalLink,
} from 'lucide-react';
import { useStore } from '../store/useStore';

export function AboutPage() {
  const { setCurrentPage, toggleSidebar } = useStore();

  return (
    <div className="h-full overflow-y-auto">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-white/80 dark:bg-surface-900/80 backdrop-blur-sm border-b border-surface-200 dark:border-surface-800 px-4 sm:px-6 py-3.5 sm:py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5 sm:gap-3">
            {/* Mobile menu toggle */}
            <button
              onClick={toggleSidebar}
              className="btn-ghost p-1.5 lg:hidden text-surface-600 dark:text-surface-300"
              aria-label="Open navigation menu"
            >
              <Menu size={20} />
            </button>

            <div>
              <h1 className="text-base sm:text-xl font-semibold leading-tight">About</h1>
              <p className="text-xs sm:text-sm text-surface-500 hidden sm:block">Dynamic AI Chatbot v1.0.0</p>
            </div>
          </div>
        </div>
      </div>

      <div className="p-6 max-w-3xl mx-auto space-y-8">
        <div className="card p-8 text-center">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-500 to-emerald-500 flex items-center justify-center mx-auto mb-4 shadow-lg shadow-primary-500/20">
            <Bot size={32} className="text-white" />
          </div>
          <h2 className="text-2xl font-bold mb-2">Dynamic AI Chatbot</h2>
          <p className="text-surface-500 dark:text-surface-400 max-w-lg mx-auto leading-relaxed">
            A modern AI-powered conversational assistant built with Google Gemini,
            featuring NLP analysis, contextual memory, RAG knowledge retrieval,
            tool calling, and an analytics dashboard.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <FeatureCard icon={<Brain />} title="AI-Powered" desc="Powered by Google Gemini for intelligent, context-aware conversations" />
          <FeatureCard icon={<MessageSquare />} title="Contextual Memory" desc="Remembers conversation context and user preferences across sessions" />
          <FeatureCard icon={<Sparkles />} title="NLP Analysis" desc="Intent recognition, entity extraction, sentiment & emotion analysis" />
          <FeatureCard icon={<BookOpen />} title="Knowledge Base (RAG)" desc="Retrieves relevant information from indexed documents" />
          <FeatureCard icon={<Wrench />} title="Tool Calling" desc="Built-in calculator, date/time, and knowledge search tools" />
          <FeatureCard icon={<BarChart3 />} title="Analytics Dashboard" desc="Real-time insights into conversations, sentiment, and performance" />
          <FeatureCard icon={<Globe />} title="Multilingual" desc="Supports English, Hindi, and Hinglish with extensible language system" />
          <FeatureCard icon={<Shield />} title="Secure by Design" desc="API key protection, input validation, guardrails, and prompt-injection defence" />
        </div>

        <div className="card p-6">
          <h3 className="font-semibold mb-4 flex items-center gap-2"><Code size={18} className="text-primary-600" /> Technology Stack</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
            {[
              'FastAPI', 'React + TypeScript', 'Google Gemini',
              'PostgreSQL (pgvector)', 'Redis', 'TF-IDF / Centroid ML',
              'TailwindCSS', 'Recharts', 'SQLAlchemy',
              'Pydantic v2', 'Docker', 'Alembic',
            ].map((tech) => (
              <div key={tech} className="flex items-center gap-2 px-3 py-2 rounded-xl bg-surface-50 dark:bg-surface-800">
                <div className="w-1.5 h-1.5 rounded-full bg-primary-500" />
                {tech}
              </div>
            ))}
          </div>
        </div>

        <div className="card p-6">
          <h3 className="font-semibold mb-3 flex items-center gap-2"><Database size={18} className="text-primary-600" /> Architecture</h3>
          <p className="text-sm text-surface-600 dark:text-surface-400 leading-relaxed">
            The system uses a layered architecture: <strong>React frontend</strong> communicates with a <strong>FastAPI backend</strong> through REST APIs.
            The backend orchestrates an AI pipeline that includes intent recognition (statistical TF-IDF & centroid cosine similarity), entity extraction, sentiment analysis (VADER valence modeling),
            knowledge retrieval (RAG via native PostgreSQL pgvector), tool execution, and response generation using Google Gemini.
            Conversations are persisted in <strong>PostgreSQL</strong>, with <strong>Redis</strong> for caching.
            The LLM provider is abstracted behind an interface, making it replaceable.
          </p>
        </div>

        <div className="card p-5 border-amber-200 dark:border-amber-800 bg-amber-50/50 dark:bg-amber-900/10">
          <p className="text-sm text-amber-800 dark:text-amber-300 leading-relaxed">
            <strong>Note:</strong> This system integrates pretrained NLP components and a generative AI model (Google Gemini)
            rather than training a large language model from scratch. The AI pipeline adds value through orchestration,
            context management, structured extraction, and knowledge retrieval. Custom model fine-tuning and
            reinforcement learning are documented as future enhancements.
          </p>
        </div>
      </div>
    </div>
  );
}

function FeatureCard({ icon, title, desc }: { icon: React.ReactNode; title: string; desc: string }) {
  return (
    <div className="card p-4 flex gap-3">
      <div className="p-2 rounded-xl bg-primary-50 dark:bg-primary-900/20 text-primary-600 dark:text-primary-400 h-fit">
        {React.cloneElement(icon as React.ReactElement, { size: 18 })}
      </div>
      <div>
        <h4 className="font-medium text-sm mb-0.5">{title}</h4>
        <p className="text-xs text-surface-500 dark:text-surface-400 leading-relaxed">{desc}</p>
      </div>
    </div>
  );
}
