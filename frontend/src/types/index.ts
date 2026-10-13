export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at?: string;
  intent?: string;
  intent_confidence?: number;
  sentiment?: { label: string; score: number };
  emotion?: { label: string; score: number };
  entities?: { text: string; label: string }[];
  sources?: { title: string; section?: string; score?: number }[];
  response_time_ms?: number;
  is_fallback?: boolean;
  is_error?: boolean;
  tools_used?: string[];
  suggestions?: string[];
  has_feedback?: boolean;
  feedback_rating?: number;
  is_rag?: boolean;
  is_faq?: boolean;
  image_url?: string;
  audio_url?: string;
  file_name?: string;
}

export interface Conversation {
  id: string;
  title: string;
  language: string;
  created_at?: string;
  updated_at?: string;
  message_count: number;
  category?: string;
}

export interface ConversationDetail {
  conversation: Conversation;
  messages: ChatMessage[];
}

export interface ChatResponseData {
  conversation_id: string;
  message_id: string;
  reply: string;
  intent?: string;
  intent_confidence?: number;
  sentiment?: { label: string; score: number };
  emotion?: { label: string; score: number };
  entities?: { text: string; label: string }[];
  sources?: { title: string; section?: string; score?: number }[];
  suggestions?: string[];
  response_time_ms: number;
  is_demo?: boolean;
  is_rag?: boolean;
  is_faq?: boolean;
  image_url?: string;
}

export interface RagDocument {
  title: string;
  chunks: number;
  source: string;
  category?: string;
}

export interface RagUploadResponse {
  success: boolean;
  title: string;
  chunks: number;
  message: string;
}

export interface LearningStats {
  total_feedback: number;
  average_reward: number;
  positive_rewards: number;
  negative_rewards: number;
  adaptation_score: number;
  top_rewarded_intents: { intent: string; avg_reward: number; count: number }[];
  policy_weights: Record<string, number>;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: { code: string; message: string };
}

export interface AnalyticsOverview {
  total_conversations: number;
  total_messages: number;
  avg_response_time_ms: number;
  success_count: number;
  failure_count: number;
  positive_pct: number;
  negative_pct: number;
  neutral_pct: number;
  avg_feedback_rating: number;
}

export interface ActivityData {
  conversations_over_time: { date: string; count: number }[];
  messages_over_time: { date: string; count: number }[];
  response_latency: { date: string; avg_ms: number }[];
  recent_activity: RecentActivity[];
  emotion_distribution: { emotion: string; count: number }[];
}

export interface RecentActivity {
  timestamp: string;
  conversation_id: string;
  message_preview: string;
  intent?: string;
  sentiment?: string;
  response_time_ms?: number;
  is_error?: boolean;
}

export interface UserSettings {
  theme: 'light' | 'dark' | 'system';
  language: string;
  temperature: number;
  max_tokens: number;
  timestamps_enabled: boolean;
  sentiment_enabled: boolean;
  compact_mode: boolean;
  auto_scroll: boolean;
  suggestions_enabled: boolean;
}

export interface HealthStatus {
  status: string;
  version: string;
  demo_mode: boolean;
  services: Record<string, string>;
}
