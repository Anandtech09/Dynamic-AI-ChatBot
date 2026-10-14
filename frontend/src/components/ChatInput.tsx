import React, { useState, useRef, useEffect } from 'react';
import {
  Send,
  StopCircle,
  Mic,
  Image as ImageIcon,
  FileText,
  X,
  BookOpen,
  CheckCircle2,
  AlertCircle,
  Trash2,
  Play,
  Pause,
} from 'lucide-react';
import { useStore } from '../store/useStore';
import { uploadDocument, getDocuments, deleteDocument } from '../services/api';
import type { RagDocument } from '../types';

interface ChatInputProps {
  onSend: (
    message: string,
    imageData?: string,
    audioData?: string,
    fileName?: string,
    ragDocumentTitle?: string,
  ) => void;
  onStop?: () => void;
}

const MAX_VOICE_SECONDS = 180; // 3 minutes maximum

export function ChatInput({ onSend, onStop }: ChatInputProps) {
  const [input, setInput] = useState('');
  const [imageData, setImageData] = useState<string | null>(null);
  const [attachedFileName, setAttachedFileName] = useState<string | null>(null);
  const [showRagModal, setShowRagModal] = useState(false);
  const [ragDocuments, setRagDocuments] = useState<RagDocument[]>([]);
  const [selectedRagDoc, setSelectedRagDoc] = useState<string>('');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);

  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [recordSeconds, setRecordSeconds] = useState(0);

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const docInputRef = useRef<HTMLInputElement>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<any>(null);

  const { isLoading, isStreaming } = useStore();

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 160) + 'px';
    }
  }, [input]);

  // Load indexed RAG documents on initial mount and when modal opens
  useEffect(() => {
    fetchRagDocs();
  }, []);

  useEffect(() => {
    if (showRagModal) {
      fetchRagDocs();
    }
  }, [showRagModal]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      if (mediaStreamRef.current) {
        mediaStreamRef.current.getTracks().forEach((t) => t.stop());
      }
    };
  }, []);

  const fetchRagDocs = async () => {
    try {
      const res = await getDocuments();
      const list = res.data || (res as any).documents || [];
      if (Array.isArray(list)) {
        setRagDocuments(list);
      }
    } catch (e) {
      console.warn('Could not load RAG documents:', e);
    }
  };

  const formatTime = (totalSeconds: number) => {
    if (isNaN(totalSeconds) || totalSeconds < 0) return '00:00';
    const mins = Math.floor(totalSeconds / 60);
    const secs = Math.floor(totalSeconds % 60);
    return `${mins < 10 ? '0' : ''}${mins}:${secs < 10 ? '0' : ''}${secs}`;
  };

  const startRecording = async () => {
    if (typeof window === 'undefined' || !navigator.mediaDevices?.getUserMedia) {
      alert('Microphone recording is not supported in this browser.');
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;

      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.start(250);
      setIsRecording(true);
      setIsPaused(false);
      setRecordSeconds(0);

      // Start 3-minute max timer
      if (timerRef.current) clearInterval(timerRef.current);
      timerRef.current = setInterval(() => {
        setRecordSeconds((prev) => {
          if (prev >= MAX_VOICE_SECONDS - 1) {
            // Maximum 3 minutes reached - auto send
            stopAndSendRecording();
            return MAX_VOICE_SECONDS;
          }
          return prev + 1;
        });
      }, 1000);
    } catch (err: any) {
      console.error('Microphone error:', err);
      alert('Microphone access was denied. Please allow microphone permissions in your browser.');
      cancelRecording();
    }
  };

  const pauseRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.pause();
      if (timerRef.current) clearInterval(timerRef.current);
      setIsPaused(true);
    }
  };

  const resumeRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'paused') {
      mediaRecorderRef.current.resume();
      timerRef.current = setInterval(() => {
        setRecordSeconds((prev) => {
          if (prev >= MAX_VOICE_SECONDS - 1) {
            stopAndSendRecording();
            return MAX_VOICE_SECONDS;
          }
          return prev + 1;
        });
      }, 1000);
      setIsPaused(false);
    }
  };

  const cancelRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => track.stop());
    }
    if (timerRef.current) clearInterval(timerRef.current);
    audioChunksRef.current = [];
    setIsRecording(false);
    setIsPaused(false);
    setRecordSeconds(0);
  };

  const stopAndSendRecording = () => {
    if (!mediaRecorderRef.current) return;

    if (timerRef.current) clearInterval(timerRef.current);

    mediaRecorderRef.current.onstop = () => {
      const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
      const reader = new FileReader();
      reader.onloadend = () => {
        const base64Audio = reader.result as string;
        // Direct send voice note without preview or text repetition
        onSend('🎙️ Voice Message', imageData || undefined, base64Audio);
        setImageData(null);
      };
      reader.readAsDataURL(blob);

      // Stop stream tracks
      if (mediaStreamRef.current) {
        mediaStreamRef.current.getTracks().forEach((track) => track.stop());
      }
      setIsRecording(false);
      setIsPaused(false);
      setRecordSeconds(0);
    };

    if (mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
  };

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      alert('Please select an image file (.png, .jpg, .webp)');
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      setImageData(reader.result as string);
    };
    reader.readAsDataURL(file);
    e.target.value = '';
  };

  const removeImage = () => {
    setImageData(null);
  };

  const handleDocUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setUploadStatus(null);
    try {
      const res = await uploadDocument(file);
      const chunkCount = res.data?.chunk_count || res.data?.chunks || 1;
      const pageInfo = res.data?.page_count && res.data.page_count > 1 ? ` (${res.data.page_count} pages)` : '';
      setUploadStatus(`Indexed ${chunkCount} chunks${pageInfo} from "${file.name}"!`);
      setAttachedFileName(file.name);
      setInput((prev) => (prev.includes('#rag') ? prev : `#rag Query about ${file.name.replace(/\.[^/.]+$/, '')}: `));
      await fetchRagDocs();
      setTimeout(() => setUploadStatus(null), 5000);
    } catch (err: any) {
      setUploadStatus(`Error: ${err.message || 'Upload failed'}`);
    } finally {
      setIsUploading(false);
      e.target.value = '';
    }
  };

  const handleDeleteDoc = async (title: string) => {
    try {
      await deleteDocument(title);
      await fetchRagDocs();
    } catch (err) {
      console.error('Delete doc failed:', err);
    }
  };

  const handleToggleRagTag = () => {
    if (input.toLowerCase().includes('#rag') || selectedRagDoc) {
      setInput((prev) => prev.replace(/#rag\s*/i, '').trim());
      setSelectedRagDoc('');
    } else {
      setInput((prev) => `#rag ${prev}`.trim() + ' ');
      textareaRef.current?.focus();
    }
  };

  const handleSend = () => {
    if (isRecording) {
      stopAndSendRecording();
      return;
    }

    const trimmed = input.trim();
    if ((trimmed || imageData || attachedFileName) && !isLoading) {
      onSend(
        trimmed || (imageData ? 'What is in this image?' : `Document: ${attachedFileName}`),
        imageData || undefined,
        undefined,
        attachedFileName || undefined,
        selectedRagDoc || undefined,
      );
      setInput('');
      setImageData(null);
      setAttachedFileName(null);
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const hasRagTag = input.toLowerCase().includes('#rag') || Boolean(selectedRagDoc);

  return (
    <div className="border-t border-surface-200 dark:border-surface-800 bg-white dark:bg-surface-900 p-2.5 sm:p-4 relative">
      <div className="max-w-3xl mx-auto space-y-2">
        {/* Attachment Previews Tray */}
        <div className="flex items-center gap-2 flex-wrap">
          {/* Image Preview Thumbnail */}
          {imageData && (
            <div className="relative inline-block animate-fade-in">
              <img
                src={imageData}
                alt="Attached preview"
                className="w-16 h-16 sm:w-20 sm:h-20 object-cover rounded-xl border-2 border-primary-500 shadow-md"
              />
              <button
                onClick={removeImage}
                className="absolute -top-2 -right-2 p-1 bg-red-500 text-white rounded-full hover:bg-red-600 shadow cursor-pointer"
                aria-label="Remove image"
              >
                <X size={12} />
              </button>
            </div>
          )}

          {/* Document File Chip */}
          {attachedFileName && (
            <div className="relative inline-flex items-center gap-2 px-3 py-1.5 bg-purple-50 dark:bg-purple-950/40 border border-purple-200 dark:border-purple-800 rounded-xl text-xs text-purple-900 dark:text-purple-200 font-medium animate-fade-in shadow-xs">
              <BookOpen size={14} className="text-purple-600 dark:text-purple-400 shrink-0" />
              <span className="truncate max-w-[180px] sm:max-w-[240px]">{attachedFileName}</span>
              <button
                type="button"
                onClick={() => setAttachedFileName(null)}
                className="p-0.5 bg-purple-200/50 dark:bg-purple-900/50 hover:bg-purple-300 dark:hover:bg-purple-800 rounded-full text-purple-700 dark:text-purple-300 cursor-pointer"
                aria-label="Remove document attachment"
              >
                <X size={12} />
              </button>
            </div>
          )}
        </div>

        {/* Upload Status Toast */}
        {uploadStatus && (
          <div
            className={`flex items-center gap-2 p-2.5 rounded-xl text-xs ${
              uploadStatus.startsWith('Error')
                ? 'bg-red-50 text-red-700 dark:bg-red-950/40 dark:text-red-300 border border-red-200 dark:border-red-800'
                : 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800'
            }`}
          >
            {uploadStatus.startsWith('Error') ? <AlertCircle size={14} /> : <CheckCircle2 size={14} />}
            <span>{uploadStatus}</span>
          </div>
        )}

        {/* RAG Document Selector Strip */}
        {hasRagTag && (
          <div className="flex items-center justify-between gap-2 p-2 px-3 rounded-xl bg-purple-50 dark:bg-purple-950/40 border border-purple-200 dark:border-purple-800 text-xs animate-fade-in flex-wrap shadow-xs">
            <div className="flex items-center gap-1.5 font-semibold text-purple-700 dark:text-purple-300">
              <BookOpen size={13} className="text-purple-600 dark:text-purple-400" />
              <span>RAG Target:</span>
            </div>
            <div className="flex items-center gap-1.5 flex-1 min-w-[200px]">
              <select
                id="rag-document-selector"
                value={selectedRagDoc}
                onChange={(e) => {
                  setSelectedRagDoc(e.target.value);
                  if (!input.toLowerCase().includes('#rag')) {
                    setInput((prev) => `#rag ${prev}`.trim() + ' ');
                  }
                }}
                className="w-full bg-white dark:bg-surface-800 border border-purple-300 dark:border-purple-700 text-purple-900 dark:text-purple-100 rounded-lg px-2.5 py-1 text-xs font-medium focus:outline-none focus:ring-1 focus:ring-purple-500 cursor-pointer shadow-2xs"
                title="Select specific document for RAG search"
              >
                <option value="">🌐 All Documents (Hybrid Search + RRF)</option>
                {ragDocuments.map((doc, idx) => (
                  <option key={idx} value={doc.title}>
                    📄 {doc.title} ({doc.chunk_count ?? doc.chunks ?? '?'} chunks)
                  </option>
                ))}
              </select>
            </div>
            <button
              type="button"
              onClick={() => {
                setSelectedRagDoc('');
                setInput((prev) => prev.replace(/#rag\s*/i, '').trim());
              }}
              className="p-1 rounded-md text-purple-500 hover:bg-purple-200/60 dark:hover:bg-purple-900/60 transition-colors cursor-pointer"
              title="Reset RAG search filter"
            >
              <X size={13} />
            </button>
          </div>
        )}

        {isRecording && (
          <div className="flex items-center justify-between p-3 rounded-2xl bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900/50 shadow-sm animate-fade-in gap-3 flex-wrap">
            <div className="flex items-center gap-2.5">
              <span
                className={`w-3 h-3 rounded-full ${
                  !isPaused ? 'bg-red-500 animate-pulse' : 'bg-amber-500'
                }`}
              />
              <span className="text-xs sm:text-sm font-semibold text-red-700 dark:text-red-300">
                {!isPaused ? 'Recording Voice...' : 'Recording Paused'}
              </span>
              <span className="px-2.5 py-0.5 rounded-md bg-white dark:bg-surface-800 text-xs font-mono font-medium text-surface-800 dark:text-surface-200 shadow-xs border border-surface-200 dark:border-surface-700">
                {formatTime(recordSeconds)} / {formatTime(MAX_VOICE_SECONDS)}
              </span>
            </div>

            <div className="flex items-center gap-2">
              {!isPaused ? (
                <button
                  type="button"
                  onClick={pauseRecording}
                  className="p-2 rounded-xl bg-white dark:bg-surface-800 hover:bg-surface-100 dark:hover:bg-surface-700 text-surface-700 dark:text-surface-200 border border-surface-200 dark:border-surface-700 shadow-xs transition-colors cursor-pointer"
                  title="Pause recording"
                >
                  <Pause size={16} />
                </button>
              ) : (
                <button
                  type="button"
                  onClick={resumeRecording}
                  className="p-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white shadow-xs transition-colors cursor-pointer"
                  title="Resume recording"
                >
                  <Play size={16} />
                </button>
              )}

              <button
                type="button"
                onClick={cancelRecording}
                className="p-2 rounded-xl text-red-500 hover:bg-red-100 dark:hover:bg-red-900/40 transition-colors cursor-pointer"
                title="Discard recording"
              >
                <Trash2 size={16} />
              </button>

              <button
                type="button"
                onClick={stopAndSendRecording}
                className="flex items-center gap-1.5 px-3 py-1.5 sm:px-3.5 sm:py-2 rounded-xl bg-primary-600 hover:bg-primary-700 text-white text-xs font-semibold shadow-sm transition-all active:scale-95 cursor-pointer"
                title="Send Voice Recording"
              >
                <Send size={14} />
                <span>Send Voice</span>
              </button>
            </div>
          </div>
        )}

        {/* Modern Mobile-Optimized Input Card */}
        <div className="relative flex flex-col bg-surface-100 dark:bg-surface-800/90 rounded-2xl border border-surface-200 dark:border-surface-700 focus-within:ring-2 focus-within:ring-primary-500/40 focus-within:border-primary-500 transition-all shadow-xs p-1.5 sm:p-2">
          {/* Full-width Responsive Text Area */}
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              isRecording
                ? 'Recording voice note (up to 3 min)... Click "Send Voice" when done.'
                : hasRagTag
                ? `Ask question with RAG (${selectedRagDoc ? `Doc: ${selectedRagDoc}` : 'All Docs (Hybrid RRF)'})...`
                : 'Ask anything, or use #rag to search knowledge...'
            }
            rows={1}
            className="w-full resize-none bg-transparent px-2.5 pt-2 pb-1.5 text-sm sm:text-base text-surface-900 dark:text-surface-100 placeholder:text-surface-400 dark:placeholder:text-surface-500 focus:outline-none max-h-40 min-h-[44px] leading-relaxed"
            disabled={isLoading && !isStreaming}
            aria-label="Message input"
            id="chat-input"
          />

          {/* Action Toolbar Row (Generous spacing on mobile & desktop) */}
          <div className="flex items-center justify-between pt-1 border-t border-surface-200/50 dark:border-surface-700/50 mt-1">
            {/* Left side attachment actions */}
            <div className="flex items-center gap-1">
              {/* Hidden file inputs */}
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleImageSelect}
                accept="image/*"
                className="hidden"
              />
              <input
                type="file"
                ref={docInputRef}
                onChange={handleDocUpload}
                accept=".pdf,.txt,.md,.docx,.csv"
                className="hidden"
              />

              {/* RAG Tag Toggle Button */}
              <button
                type="button"
                onClick={handleToggleRagTag}
                className={`px-2 py-1 rounded-xl text-xs font-semibold tracking-wider transition-all flex items-center gap-1 cursor-pointer ${
                  hasRagTag
                    ? 'bg-purple-600 text-white shadow-xs ring-1 ring-purple-400'
                    : 'bg-surface-200/80 dark:bg-surface-700/80 text-surface-600 dark:text-surface-300 hover:bg-purple-100 dark:hover:bg-purple-900/40 hover:text-purple-600'
                }`}
                title="Toggle #RAG search tag in query"
              >
                <BookOpen size={13} />
                <span>#RAG</span>
                {selectedRagDoc && (
                  <span className="max-w-[70px] sm:max-w-[120px] truncate text-[10px] opacity-90 border-l border-white/40 pl-1 font-normal">
                    {selectedRagDoc}
                  </span>
                )}
              </button>

              {/* Upload Image Button */}
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="p-1.5 sm:p-2 rounded-xl text-surface-500 dark:text-surface-400 hover:bg-surface-200 dark:hover:bg-surface-700 transition-colors cursor-pointer"
                title="Upload Image for Multimodal Vision Analysis"
                aria-label="Upload Image"
              >
                <ImageIcon size={18} />
              </button>

              {/* Document RAG Upload / Management Modal Opener */}
              <button
                type="button"
                onClick={() => setShowRagModal(true)}
                className="p-1.5 sm:p-2 rounded-xl text-surface-500 dark:text-surface-400 hover:bg-surface-200 dark:hover:bg-surface-700 transition-colors cursor-pointer"
                title="Manage & Upload RAG Documents (PDF, TXT, MD)"
                aria-label="RAG Documents"
              >
                <FileText size={18} />
              </button>
            </div>

            {/* Right side primary actions */}
            <div className="flex items-center gap-1.5">
              {/* Voice Input Button */}
              <button
                type="button"
                onClick={isRecording ? cancelRecording : startRecording}
                className={`p-1.5 sm:p-2 rounded-xl transition-all cursor-pointer ${
                  isRecording
                    ? 'bg-red-500 text-white animate-pulse shadow-md shadow-red-500/30'
                    : 'text-surface-500 dark:text-surface-400 hover:bg-surface-200 dark:hover:bg-surface-700'
                }`}
                title={
                  isRecording
                    ? 'Recording in progress (Click to cancel)'
                    : 'Record voice note (Click to start, max 3 min)'
                }
                aria-label="Record voice note"
              >
                <Mic size={18} />
              </button>

              {/* Send / Stop Button */}
              {isStreaming ? (
                <button
                  type="button"
                  onClick={onStop}
                  className="p-2 sm:p-2.5 rounded-xl bg-red-500 hover:bg-red-600 text-white transition-colors cursor-pointer"
                  aria-label="Stop generation"
                >
                  <StopCircle size={18} />
                </button>
              ) : (
                <button
                  type="button"
                  onClick={handleSend}
                  disabled={(!input.trim() && !imageData && !attachedFileName && !isRecording) || isLoading}
                  className="p-2 sm:p-2.5 rounded-xl bg-primary-600 hover:bg-primary-700 text-white transition-all disabled:opacity-30 disabled:cursor-not-allowed shadow-xs active:scale-95 cursor-pointer"
                  aria-label="Send message"
                  id="send-btn"
                >
                  <Send size={18} />
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Footer info & hints */}
        <div className="flex items-center justify-between text-[11px] text-surface-400 dark:text-surface-500 px-1">
          <span>
            💡 Tag{' '}
            <code className="px-1 py-0.5 rounded bg-surface-200 dark:bg-surface-800 text-purple-600 dark:text-purple-400 font-mono">
              #rag
            </code>{' '}
            for Hybrid Search + RRF
          </span>
          <span className="hidden sm:inline">🎙️ Voice messages | 🖼️ Vision supported</span>
        </div>
      </div>

      {showRagModal && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white dark:bg-surface-900 rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-surface-200 dark:border-surface-800 space-y-4 animate-scale-up">
            <div className="flex items-center justify-between border-b border-surface-100 dark:border-surface-800 pb-3">
              <div className="flex items-center gap-2">
                <div className="p-2 rounded-xl bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400">
                  <BookOpen size={20} />
                </div>
                <div>
                  <h3 className="font-semibold text-base">Knowledge Base (RAG)</h3>
                  <p className="text-xs text-surface-500">Indexed documents for semantic AI search</p>
                </div>
              </div>
              <button
                onClick={() => setShowRagModal(false)}
                className="btn-ghost p-1.5 text-surface-400 hover:text-surface-700 dark:hover:text-surface-200 cursor-pointer"
                aria-label="Close modal"
              >
                <X size={18} />
              </button>
            </div>

            {/* Document Upload Dropzone */}
            <div
              onClick={() => docInputRef.current?.click()}
              className="border-2 border-dashed border-surface-200 dark:border-surface-700 hover:border-purple-500 rounded-2xl p-6 text-center cursor-pointer transition-colors bg-surface-50/50 dark:bg-surface-800/30"
            >
              <FileText size={32} className="mx-auto mb-2 text-purple-500" />
              <p className="text-sm font-medium">Click to upload documents</p>
              <p className="text-xs text-surface-400 mt-1">Supports PDF, TXT, MD, CSV, DOCX (up to 20MB)</p>
              {isUploading && (
                <p className="text-xs text-purple-600 dark:text-purple-400 font-medium mt-2 animate-pulse">
                  Chunking and indexing document...
                </p>
              )}
            </div>

            {/* Document List */}
            <div className="space-y-2 max-h-60 overflow-y-auto">
              <p className="text-xs font-semibold uppercase tracking-wider text-surface-400">
                Indexed Documents ({ragDocuments.length})
              </p>
              {ragDocuments.length === 0 ? (
                <p className="text-xs text-surface-400 italic py-3 text-center">
                  No documents indexed yet. Upload one above to enable semantic retrieval!
                </p>
              ) : (
                ragDocuments.map((doc, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between p-2.5 rounded-xl bg-surface-50 dark:bg-surface-800 border border-surface-100 dark:border-surface-700 text-xs"
                  >
                    <div className="flex items-center gap-2 truncate">
                      <FileText size={14} className="text-purple-500 shrink-0" />
                      <span className="truncate font-medium">{doc.title}</span>
                      <span className="text-surface-400 shrink-0">• {doc.chunks} chunks</span>
                    </div>
                    <button
                      onClick={() => handleDeleteDoc(doc.title)}
                      className="p-1 rounded text-red-500 hover:bg-red-50 dark:hover:bg-red-950/40 transition-colors cursor-pointer"
                      title="Delete document index"
                      aria-label="Delete document"
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                ))
              )}
            </div>

            {/* Modal Footer */}
            <div className="pt-2 border-t border-surface-100 dark:border-surface-800 flex justify-between items-center text-xs text-surface-500">
              <span>Use <code className="text-purple-600 font-mono">#rag</code> in chat to query knowledge</span>
              <button
                onClick={() => setShowRagModal(false)}
                className="btn-primary text-xs py-1.5 px-3 cursor-pointer"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
