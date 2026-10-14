import type {
  ActivityData,
  AnalyticsOverview,
  ApiResponse,
  ChatResponseData,
  Conversation,
  ConversationDetail,
  HealthStatus,
  UserSettings,
} from '../types';

const envApiUrl = (import.meta.env.VITE_API_URL as string | undefined)?.trim();
const API_BASE = !envApiUrl || envApiUrl === '/' || envApiUrl === '/api'
  ? '/api'
  : envApiUrl.startsWith('http')
    ? (envApiUrl.endsWith('/api') ? envApiUrl : `${envApiUrl.replace(/\/$/, '')}/api`)
    : envApiUrl;

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body?.error?.message || body?.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function sendMessage(
  message: string,
  conversationId?: string,
  sessionId = 'default',
  language = 'en',
  temperature?: number,
  imageData?: string,
  audioData?: string,
  fileName?: string,
  ragDocumentTitle?: string,
): Promise<ApiResponse<ChatResponseData>> {
  return request<ApiResponse<ChatResponseData>>('/chat', {
    method: 'POST',
    body: JSON.stringify({
      message,
      conversation_id: conversationId,
      session_id: sessionId,
      language,
      temperature,
      image_data: imageData,
      audio_data: audioData,
      file_name: fileName,
      rag_document_title: ragDocumentTitle,
    }),
  });
}

export async function getConversations(
  sessionId = 'default',
): Promise<{ success: boolean; data: Conversation[] }> {
  return request(`/conversations?session_id=${sessionId}`);
}

export async function getConversation(
  id: string,
): Promise<{ success: boolean; data: ConversationDetail }> {
  return request(`/conversations/${id}`);
}

export async function deleteConversation(id: string): Promise<{ success: boolean }> {
  return request(`/conversations/${id}`, { method: 'DELETE' });
}

export async function exportConversation(
  id: string,
  format: 'json' | 'txt' | 'md' = 'json',
): Promise<string> {
  const res = await fetch(`${API_BASE}/conversations/${id}/export`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ conversation_id: id, format }),
  });
  return res.text();
}

export async function getAnalyticsOverview(): Promise<ApiResponse<AnalyticsOverview>> {
  return request('/analytics/overview');
}

export async function getSentimentData(): Promise<ApiResponse<any>> {
  return request('/analytics/sentiment');
}

export async function getIntentData(): Promise<ApiResponse<any>> {
  return request('/analytics/intents');
}

export async function getActivityData(
  days = 30,
): Promise<ApiResponse<ActivityData>> {
  return request(`/analytics/activity?days=${days}`);
}

export async function getLearningData(): Promise<ApiResponse<any>> {
  return request('/analytics/learning');
}

export async function getSettings(
  sessionId = 'default',
): Promise<{ success: boolean; data: UserSettings }> {
  return request(`/settings?session_id=${sessionId}`);
}

export async function updateSettings(
  settings: Partial<UserSettings>,
  sessionId = 'default',
): Promise<{ success: boolean; data: UserSettings }> {
  return request(`/settings?session_id=${sessionId}`, {
    method: 'PUT',
    body: JSON.stringify(settings),
  });
}

export async function submitFeedback(
  messageId: string,
  rating: number,
  comment = '',
): Promise<{ success: boolean }> {
  return request('/feedback', {
    method: 'POST',
    body: JSON.stringify({ message_id: messageId, rating, comment }),
  });
}

export async function getHealth(): Promise<HealthStatus> {
  return request('/health');
}

export async function indexKnowledge(): Promise<{ success: boolean; chunks: number }> {
  return request('/knowledge/index', { method: 'POST' });
}

export async function uploadDocument(
  file: File,
  category = 'user_upload',
): Promise<ApiResponse<any>> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('category', category);

  const res = await fetch(`${API_BASE}/rag/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body?.detail || body?.error?.message || `Upload failed with HTTP ${res.status}`);
  }
  return res.json();
}

export async function getDocuments(): Promise<ApiResponse<any[]>> {
  return request('/rag/documents');
}

export async function deleteDocument(title: string): Promise<ApiResponse<any>> {
  return request(`/rag/documents/${encodeURIComponent(title)}`, {
    method: 'DELETE',
  });
}

export async function searchRag(query: string, topK = 3): Promise<ApiResponse<any[]>> {
  return request('/rag/search', {
    method: 'POST',
    body: JSON.stringify({ query, top_k: topK }),
  });
}

export async function getLearningStats(): Promise<any> {
  return request('/learning-stats');
}
