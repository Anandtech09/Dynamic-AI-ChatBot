"""
Pydantic request / response schemas for the API.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ── Chat ─────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    conversation_id: Optional[str] = None
    session_id: str = Field(default="default")
    language: str = Field(default="en")
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    image_data: Optional[str] = None  # Base64 data URL or remote image URL
    audio_data: Optional[str] = None  # Base64 audio or audio transcript
    file_name: Optional[str] = None  # Uploaded file / document name
    rag_document_title: Optional[str] = None  # Filter RAG to specific document (None = all)


class SentimentResult(BaseModel):
    label: str
    score: float


class EmotionResult(BaseModel):
    label: str
    score: float


class EntityResult(BaseModel):
    text: str
    label: str
    start: Optional[int] = None
    end: Optional[int] = None


class SourceResult(BaseModel):
    title: str
    section: Optional[str] = None
    score: Optional[float] = None
    rrf_score: Optional[float] = None
    recall_at_k: Optional[float] = None


class ChatResponse(BaseModel):
    success: bool = True
    data: Optional[ChatResponseData] = None
    error: Optional[ErrorDetail] = None


class ChatResponseData(BaseModel):
    conversation_id: str
    message_id: str
    reply: str
    intent: Optional[str] = None
    intent_confidence: Optional[float] = None
    sentiment: Optional[SentimentResult] = None
    emotion: Optional[EmotionResult] = None
    entities: List[EntityResult] = []
    sources: List[SourceResult] = []
    suggestions: List[str] = []
    response_time_ms: int = 0
    is_demo: bool = False
    is_rag: bool = False
    is_faq: bool = False
    image_url: Optional[str] = None


class ErrorDetail(BaseModel):
    code: str
    message: str


# Fix forward references
ChatResponse.model_rebuild()


# ── Conversations ────────────────────────────────────────────────────────────

class ConversationOut(BaseModel):
    id: str
    title: str
    language: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    message_count: int = 0
    category: Optional[str] = "General AI"

    model_config = ConfigDict(from_attributes=True)


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    created_at: Optional[str] = None
    intent: Optional[str] = None
    intent_confidence: Optional[float] = None
    sentiment: Optional[SentimentResult] = None
    emotion: Optional[EmotionResult] = None
    entities: List[EntityResult] = []
    sources: List[SourceResult] = []
    response_time_ms: Optional[int] = None
    is_fallback: bool = False
    is_error: bool = False
    tools_used: List[str] = []
    has_feedback: bool = False
    feedback_rating: Optional[int] = None
    image_url: Optional[str] = None
    audio_url: Optional[str] = None
    file_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ConversationDetail(BaseModel):
    conversation: ConversationOut
    messages: List[MessageOut]


class ConversationListResponse(BaseModel):
    success: bool = True
    data: List[ConversationOut] = []


# ── Feedback ─────────────────────────────────────────────────────────────────

class FeedbackRequest(BaseModel):
    message_id: str
    rating: int = Field(..., ge=1, le=5)
    comment: str = ""


class FeedbackResponse(BaseModel):
    success: bool = True
    message: str = "Feedback recorded"


# ── Settings ─────────────────────────────────────────────────────────────────

class SettingsRequest(BaseModel):
    theme: Optional[str] = None
    language: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0, le=2)
    max_tokens: Optional[int] = Field(None, ge=100, le=8192)
    timestamps_enabled: Optional[bool] = None
    sentiment_enabled: Optional[bool] = None
    compact_mode: Optional[bool] = None
    auto_scroll: Optional[bool] = None
    suggestions_enabled: Optional[bool] = None


class SettingsResponse(BaseModel):
    success: bool = True
    data: Dict[str, Any] = {}


# ── Analytics ────────────────────────────────────────────────────────────────

class AnalyticsOverview(BaseModel):
    total_conversations: int = 0
    total_messages: int = 0
    avg_response_time_ms: float = 0
    success_count: int = 0
    failure_count: int = 0
    positive_pct: float = 0
    negative_pct: float = 0
    neutral_pct: float = 0
    avg_feedback_rating: float = 0


class AnalyticsResponse(BaseModel):
    success: bool = True
    data: Any = None


# ── Knowledge ────────────────────────────────────────────────────────────────

class KnowledgeDocument(BaseModel):
    title: str
    content: str
    source: str = ""
    chunk_count: int = 0


class KnowledgeListResponse(BaseModel):
    success: bool = True
    documents: List[KnowledgeDocument] = []
    total: int = 0


# ── Health ───────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
    demo_mode: bool = False
    services: Dict[str, str] = {}


# ── Export ───────────────────────────────────────────────────────────────────

class ExportRequest(BaseModel):
    conversation_id: str
    format: str = Field(default="json", pattern="^(json|txt|md)$")
