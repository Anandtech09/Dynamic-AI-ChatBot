import React, { useState, useRef, useEffect } from 'react';
import {
  Copy,
  Check,
  ThumbsUp,
  ThumbsDown,
  RefreshCw,
  Bot,
  User,
  Clock,
  Sparkles,
  BookOpen,
  Wrench,
  Volume2,
  VolumeX,
  Zap,
  Tag,
  ChevronDown,
  ChevronUp,
  Play,
  Pause,
  Mic,
  FileText,
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import type { ChatMessage } from '../types';
import { useStore } from '../store/useStore';
import { submitFeedback } from '../services/api';

interface MessageBubbleProps {
  message: ChatMessage;
  onRegenerate?: () => void;
  onSelectSuggestion?: (text: string) => void;
}

export function MessageBubble({ message, onRegenerate, onSelectSuggestion }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const { settings } = useStore();
  const [copied, setCopied] = useState(false);
  const [feedbackGiven, setFeedbackGiven] = useState<number | null>(message.feedback_rating || null);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [showSources, setShowSources] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleFeedback = async (rating: number) => {
    try {
      await submitFeedback(message.id, rating);
      setFeedbackGiven(rating);
    } catch {}
  };

  const toggleSpeak = () => {
    if (!('speechSynthesis' in window)) {
      alert('Speech synthesis is not supported in this browser.');
      return;
    }

    if (isSpeaking) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
      return;
    }

    window.speechSynthesis.cancel(); // Stop any ongoing speech
    const cleanText = message.content
      .replace(/[#*`_~[\]()]/g, ' ')
      .replace(/https?:\/\/\S+/g, '')
      .trim();

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = settings.language === 'es' ? 'es-ES' : settings.language === 'fr' ? 'fr-FR' : 'en-US';
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);

    setIsSpeaking(true);
    window.speechSynthesis.speak(utterance);
  };

  const sentimentBadge = message.sentiment && settings.sentiment_enabled && !isUser ? (
    <span
      className={`badge ${
        message.sentiment.label === 'positive'
          ? 'badge-positive'
          : message.sentiment.label === 'negative'
          ? 'badge-negative'
          : 'badge-neutral'
      }`}
    >
      {message.sentiment.label} ({Math.round(message.sentiment.score * 100)}%)
    </span>
  ) : null;

  return (
    <div
      className={`flex gap-3 animate-fade-in ${isUser ? 'flex-row-reverse' : ''} ${
        settings.compact_mode ? 'py-1' : 'py-2'
      }`}
    >
      <div
        className={`shrink-0 w-8 h-8 rounded-xl flex items-center justify-center shadow-sm ${
          isUser
            ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400'
            : message.is_rag
            ? 'bg-gradient-to-br from-purple-500 to-indigo-600 text-white shadow-purple-500/20'
            : 'bg-gradient-to-br from-emerald-400 to-teal-500 text-white'
        }`}
      >
        {isUser ? <User size={16} /> : message.is_rag ? <BookOpen size={16} /> : <Bot size={16} />}
      </div>

      <div className={`flex flex-col max-w-[85%] lg:max-w-[75%] ${isUser ? 'items-end' : 'items-start'}`}>
        {message.image_url && (
          <div className="mb-2">
            <img
              src={message.image_url}
              alt="User attachment"
              className="max-h-60 max-w-full rounded-2xl border border-surface-200 dark:border-surface-700 shadow-sm object-cover"
            />
          </div>
        )}

        {message.audio_url && (
          <VoiceMessagePlayer audioUrl={message.audio_url} isUser={isUser} />
        )}

        {message.file_name && (
          <div className="mb-2 flex items-center gap-2 px-3.5 py-2 rounded-2xl bg-purple-50 dark:bg-purple-950/40 border border-purple-200 dark:border-purple-800/60 text-xs text-purple-900 dark:text-purple-200 font-medium shadow-xs">
            <FileText size={16} className="text-purple-600 dark:text-purple-400 shrink-0" />
            <span className="truncate max-w-[220px]">{message.file_name}</span>
          </div>
        )}

        <div
          className={`rounded-2xl px-4 py-3 shadow-sm ${
            isUser
              ? 'bg-primary-600 text-white rounded-tr-md'
              : message.is_rag
              ? 'bg-purple-50/60 dark:bg-purple-950/20 border border-purple-200/80 dark:border-purple-800/40 rounded-tl-md text-surface-900 dark:text-surface-100'
              : 'bg-surface-100 dark:bg-surface-800 rounded-tl-md text-surface-900 dark:text-surface-100'
          }`}
        >
          {isUser ? (
            <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="markdown-content text-sm space-y-2">
              <ReactMarkdown
                components={{
                  code({ className, children, ...props }) {
                    const match = /language-(\w+)/.exec(className || '');
                    const codeString = String(children).replace(/\n$/, '');
                    if (match) {
                      return (
                        <div className="relative group my-2">
                          <div className="flex items-center justify-between px-4 py-1.5 bg-surface-800 dark:bg-surface-950 rounded-t-xl">
                            <span className="text-xs text-surface-400 font-mono">{match[1]}</span>
                            <button
                              onClick={() => navigator.clipboard.writeText(codeString)}
                              className="text-xs text-surface-400 hover:text-white transition-colors flex items-center gap-1"
                            >
                              <Copy size={12} /> Copy
                            </button>
                          </div>
                          <SyntaxHighlighter
                            style={oneDark}
                            language={match[1]}
                            PreTag="div"
                            customStyle={{
                              margin: 0,
                              borderTopLeftRadius: 0,
                              borderTopRightRadius: 0,
                              borderBottomLeftRadius: '0.75rem',
                              borderBottomRightRadius: '0.75rem',
                              fontSize: '0.8125rem',
                            }}
                          >
                            {codeString}
                          </SyntaxHighlighter>
                        </div>
                      );
                    }
                    return (
                      <code className={className} {...props}>
                        {children}
                      </code>
                    );
                  },
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>
          )}
        </div>

        <div className={`flex items-center gap-1.5 mt-1.5 flex-wrap ${isUser ? 'flex-row-reverse' : ''}`}>
          {settings.timestamps_enabled && message.created_at && (
            <span className="text-[11px] text-surface-400 flex items-center gap-1">
              <Clock size={10} />
              {new Date(message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </span>
          )}

          {!isUser && message.response_time_ms && (
            <span className="text-[11px] text-surface-400">{message.response_time_ms}ms</span>
          )}

          {/* RAG Retrieved Pill */}
          {!isUser && message.is_rag && (
            <span className="badge bg-purple-100 dark:bg-purple-900/40 text-purple-700 dark:text-purple-300 text-[10px] flex items-center gap-1 font-semibold">
              <BookOpen size={10} /> RAG Vector Search
            </span>
          )}

          {/* Pre-trained FAQ Pill */}
          {!isUser && message.is_faq && (
            <span className="badge bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-300 text-[10px] flex items-center gap-1 font-semibold">
              <Zap size={10} /> Pre-trained FAQ
            </span>
          )}

          {/* Intent Tag */}
          {!isUser && message.intent && message.intent !== 'unknown' && (
            <span className="badge bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300 text-[10px] flex items-center gap-1">
              🎯 {message.intent}
              {message.intent_confidence ? ` (${Math.round(message.intent_confidence * 100)}%)` : ''}
            </span>
          )}

          {/* Emotion Tag */}
          {!isUser && message.emotion && message.emotion.label !== 'neutral' && (
            <span className="badge bg-pink-50 dark:bg-pink-950/40 text-pink-700 dark:text-pink-300 text-[10px] flex items-center gap-1">
              🎭 {message.emotion.label}
            </span>
          )}

          {sentimentBadge}

          {/* RAG Sources Accordion Toggle */}
          {!isUser && message.sources && message.sources.length > 0 && (
            <button
              onClick={() => setShowSources(!showSources)}
              className="badge bg-indigo-50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300 text-[10px] flex items-center gap-1 hover:bg-indigo-100 transition-colors"
            >
              <BookOpen size={10} /> {message.sources.length} source{message.sources.length > 1 ? 's' : ''}
              {showSources ? <ChevronUp size={10} /> : <ChevronDown size={10} />}
            </button>
          )}

          {!isUser && message.tools_used && message.tools_used.length > 0 && (
            <span className="badge badge-neutral text-[10px] flex items-center gap-1">
              <Wrench size={10} /> {message.tools_used.join(', ')}
            </span>
          )}
        </div>

        {/* Expandable RAG Sources List */}
        {!isUser && showSources && message.sources && message.sources.length > 0 && (
          <div className="w-full mt-2 p-3 rounded-xl bg-purple-50/50 dark:bg-purple-950/20 border border-purple-200 dark:border-purple-800/40 text-xs space-y-1.5 animate-fade-in">
            <span className="font-semibold text-purple-800 dark:text-purple-300 block">
              Retrieved RAG Sources (PostgreSQL pgvector):
            </span>
            {message.sources.map((src, i) => (
              <div key={i} className="flex items-center justify-between py-1 border-b border-purple-100 dark:border-purple-900/30 last:border-0 flex-wrap gap-1">
                <span className="text-surface-700 dark:text-surface-300 font-medium truncate max-w-[240px]">
                  📄 {src.title} {src.section ? `— ${src.section}` : ''}
                </span>
                <div className="flex items-center gap-1.5 ml-auto shrink-0">
                  {src.score !== undefined && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-purple-100 dark:bg-purple-900/40 text-purple-700 dark:text-purple-300">
                      Score: {Math.round(src.score * 100)}%
                    </span>
                  )}
                  {src.recall_at_k !== undefined && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-100 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-300 font-mono" title="Recall@K (retrieved relevant chunks over candidate pool)">
                      Recall@K: {Math.round(src.recall_at_k * 100)}%
                    </span>
                  )}
                  {src.rrf_score !== undefined && (
                    <span className="text-[9px] px-1 py-0.5 rounded bg-surface-200/60 dark:bg-surface-800 text-surface-500 font-mono" title="Reciprocal Rank Fusion score">
                      RRF: {src.rrf_score}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Named Entities (NER) Pills */}
        {!isUser && message.entities && message.entities.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-1.5">
            {message.entities.slice(0, 4).map((ent, idx) => (
              <span
                key={idx}
                className="text-[10px] px-2 py-0.5 rounded-md bg-surface-200/80 dark:bg-surface-700/60 text-surface-600 dark:text-surface-300 flex items-center gap-1 font-mono"
              >
                <Tag size={8} />
                <span className="font-bold text-surface-500">{ent.label}:</span>
                {ent.text}
              </span>
            ))}
          </div>
        )}

        {/* Assistant Actions Bar */}
        {!isUser && (
          <div className="flex items-center gap-1 mt-1 text-surface-400">
            {/* Voice playback / Text to speech */}
            <button
              onClick={toggleSpeak}
              className={`btn-ghost p-1.5 transition-colors ${
                isSpeaking ? 'text-purple-600 bg-purple-50 dark:bg-purple-900/30' : 'hover:text-surface-700 dark:hover:text-surface-200'
              }`}
              title={isSpeaking ? 'Stop reading' : 'Read aloud (Text-to-Speech)'}
              aria-label="Text to speech"
            >
              {isSpeaking ? <VolumeX size={14} /> : <Volume2 size={14} />}
            </button>

            {/* Copy button */}
            <button
              onClick={handleCopy}
              className="btn-ghost p-1.5 hover:text-surface-700 dark:hover:text-surface-200"
              aria-label="Copy response"
            >
              {copied ? <Check size={14} className="text-emerald-500" /> : <Copy size={14} />}
            </button>

            {/* Thumbs Up (RLHF Feedback) */}
            <button
              onClick={() => handleFeedback(5)}
              className={`btn-ghost p-1.5 transition-colors ${
                feedbackGiven === 5 ? 'text-emerald-500 bg-emerald-50 dark:bg-emerald-950/40' : 'hover:text-surface-700'
              }`}
              title="Helpful (Train RLHF model)"
              aria-label="Thumbs up"
            >
              <ThumbsUp size={14} />
            </button>

            {/* Thumbs Down (RLHF Feedback) */}
            <button
              onClick={() => handleFeedback(1)}
              className={`btn-ghost p-1.5 transition-colors ${
                feedbackGiven === 1 ? 'text-red-500 bg-red-50 dark:bg-red-950/40' : 'hover:text-surface-700'
              }`}
              title="Not helpful (Train RLHF model)"
              aria-label="Thumbs down"
            >
              <ThumbsDown size={14} />
            </button>

            {onRegenerate && (
              <button
                onClick={onRegenerate}
                className="btn-ghost p-1.5 hover:text-surface-700 dark:hover:text-surface-200"
                aria-label="Regenerate"
              >
                <RefreshCw size={14} />
              </button>
            )}
          </div>
        )}

        {/* Dynamic Predictive Suggestions */}
        {!isUser && message.suggestions && message.suggestions.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-2.5">
            {message.suggestions.map((s, i) => (
              <button
                key={i}
                onClick={() => onSelectSuggestion?.(s)}
                className="text-xs px-3 py-1.5 rounded-full
                  bg-purple-50 dark:bg-purple-900/20
                  text-purple-700 dark:text-purple-300
                  hover:bg-purple-100 dark:hover:bg-purple-900/40
                  border border-purple-200 dark:border-purple-800
                  transition-all flex items-center gap-1 shadow-sm hover:scale-[1.02]"
              >
                <Sparkles size={11} className="text-purple-500" />
                {s}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export function TypingIndicator() {
  return (
    <div className="flex gap-3 py-2 animate-fade-in">
      <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-emerald-400 to-teal-500 flex items-center justify-center shadow-sm">
        <Bot size={16} className="text-white" />
      </div>
      <div className="bg-surface-100 dark:bg-surface-800 rounded-2xl rounded-tl-md px-4 py-3 flex items-center gap-1.5">
        <div className="typing-dot" />
        <div className="typing-dot" />
        <div className="typing-dot" />
      </div>
    </div>
  );
}

function VoiceMessagePlayer({ audioUrl, isUser }: { audioUrl: string; isUser: boolean }) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const audioRef = useRef<HTMLAudioElement>(null);

  // Accurate duration decoding (bypasses Chromium WebM Infinity duration bug)
  useEffect(() => {
    let isMounted = true;
    if (audioUrl) {
      try {
        const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
        if (AudioCtx) {
          const ctx = new AudioCtx();
          fetch(audioUrl)
            .then((res) => res.arrayBuffer())
            .then((buf) => ctx.decodeAudioData(buf))
            .then((decoded) => {
              if (isMounted && decoded && decoded.duration > 0 && isFinite(decoded.duration)) {
                setDuration(decoded.duration);
              }
            })
            .catch(() => {});
        }
      } catch {}
    }
    return () => {
      isMounted = false;
    };
  }, [audioUrl]);

  const togglePlay = () => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      audioRef.current.play();
      setIsPlaying(true);
    }
  };

  const handleSeek = (time: number) => {
    if (!audioRef.current) return;
    audioRef.current.currentTime = time;
    setCurrentTime(time);
  };

  const formatSec = (sec: number) => {
    if (isNaN(sec) || !isFinite(sec) || sec <= 0) return '0:00';
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  };

  const validDuration = isFinite(duration) && duration > 0 ? duration : (currentTime > 0 ? currentTime : 0);
  const percent = validDuration > 0 ? Math.min(100, Math.max(0, (currentTime / validDuration) * 100)) : 0;

  return (
    <div
      className={`flex items-center gap-3 p-3 rounded-2xl mb-2 w-full max-w-sm ${
        isUser
          ? 'bg-primary-700/90 border border-primary-400/30 text-white shadow-sm'
          : 'bg-surface-200/90 dark:bg-surface-800 border border-surface-300 dark:border-surface-700 text-surface-900 dark:text-surface-100 shadow-sm'
      }`}
    >
      <button
        type="button"
        onClick={togglePlay}
        className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 transition-transform active:scale-95 cursor-pointer shadow-sm ${
          isUser
            ? 'bg-white text-primary-700 hover:bg-primary-50'
            : 'bg-primary-600 hover:bg-primary-700 text-white'
        }`}
        aria-label={isPlaying ? 'Pause voice note' : 'Play voice note'}
      >
        {isPlaying ? <Pause size={18} /> : <Play size={18} className="ml-0.5" />}
      </button>

      <div className="flex-1 min-w-[150px]">
        <div className="flex items-center justify-between text-[11px] mb-1.5 font-medium">
          <span className="flex items-center gap-1 opacity-90">
            <Mic size={11} /> Voice Note
          </span>
          <span className="font-mono text-[11px] opacity-80">
            {formatSec(currentTime)} / {formatSec(validDuration)}
          </span>
        </div>

        <div className="relative flex items-center h-5 w-full cursor-pointer group">
          <div className="absolute inset-x-0 h-2 rounded-full overflow-hidden bg-black/25 dark:bg-white/20">
            <div
              className={`h-full rounded-full transition-[width] duration-75 ${
                isUser ? 'bg-white' : 'bg-primary-600 dark:bg-primary-500'
              }`}
              style={{ width: `${percent}%` }}
            />
          </div>

          <input
            type="range"
            min={0}
            max={validDuration > 0 ? validDuration : 100}
            step={0.1}
            value={currentTime}
            onChange={(e) => handleSeek(parseFloat(e.target.value))}
            aria-label="Seek voice note position"
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
          />

          <div
            className={`absolute top-1/2 -translate-y-1/2 w-3.5 h-3.5 rounded-full shadow-md pointer-events-none transition-transform group-hover:scale-125 ${
              isUser
                ? 'bg-white border-2 border-primary-800'
                : 'bg-primary-600 border-2 border-white dark:border-surface-800'
            }`}
            style={{
              left: `calc(${percent}% - 7px)`,
            }}
          />
        </div>
      </div>

      <audio
        ref={audioRef}
        src={audioUrl}
        onTimeUpdate={(e) => {
          const ct = e.currentTarget.currentTime;
          setCurrentTime(ct);
          if (ct > duration && isFinite(ct)) {
            setDuration(ct);
          }
        }}
        onLoadedMetadata={(e) => {
          const d = e.currentTarget.duration;
          if (isFinite(d) && d > 0) {
            setDuration(d);
          }
        }}
        onEnded={() => {
          setIsPlaying(false);
          setCurrentTime(0);
        }}
        className="hidden"
      />
    </div>
  );
}
