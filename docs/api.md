# API Documentation — Dynamic AI Chatbot

Base URL: `http://localhost:8000`

Interactive docs: `/docs` (Swagger) or `/redoc`

---

## Chat

### POST /api/chat

Process a chat message through the full AI pipeline.

**Request Body:**
```json
{
  "message": "Explain machine learning",
  "conversation_id": "uuid-string (optional, omit for new conversation)",
  "session_id": "default",
  "language": "en",
  "temperature": 0.7,
  "max_tokens": 2048
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "conversation_id": "uuid",
    "message_id": "uuid",
    "reply": "Machine learning is...",
    "intent": "explanation",
    "intent_confidence": 0.94,
    "sentiment": {"label": "neutral", "score": 0.88},
    "emotion": {"label": "curiosity", "score": 0.75},
    "entities": [{"text": "machine learning", "label": "technology"}],
    "sources": [],
    "suggestions": ["Give me an example", "What are its types?"],
    "response_time_ms": 1200,
    "is_demo": false
  }
}
```

### POST /api/chat/stream

Stream response via Server-Sent Events.

---

## Conversations

### GET /api/conversations?session_id=default

List all conversations for a session.

### GET /api/conversations/{id}

Get conversation with all messages.

### DELETE /api/conversations/{id}

Delete a conversation.

### POST /api/conversations/{id}/export

Export conversation. Body: `{"conversation_id": "...", "format": "json|txt|md"}`

---

## Analytics

### GET /api/analytics/overview

Returns KPI metrics.

### GET /api/analytics/sentiment

Sentiment distribution and trends.

### GET /api/analytics/intents

Intent distribution data.

### GET /api/analytics/activity?days=30

Time-series activity data.

---

## Settings

### GET /api/settings?session_id=default

Get user preferences.

### PUT /api/settings?session_id=default

Update preferences. Body includes any subset of: `theme`, `language`, `temperature`, `max_tokens`, `timestamps_enabled`, `sentiment_enabled`, `compact_mode`, `auto_scroll`, `suggestions_enabled`.

---

## Feedback

### POST /api/feedback

```json
{"message_id": "uuid", "rating": 5, "comment": "Great answer!"}
```

---

## Knowledge & RAG (PostgreSQL pgvector)

### POST /api/rag/upload

Upload and chunk a document (.txt, .md, .pdf, .docx, .csv, .json) and index into pgvector.
- Multipart Form: `file` (UploadFile), `chunk_size` (int, default: 500)

### GET /api/rag/documents

List indexed documents with title, character count, chunk count, and categories.

### DELETE /api/rag/documents/{title}

Delete a document and all its embedded chunks from the vector store.

### POST /api/rag/search

Direct semantic vector search across chunks.
```json
{"query": "machine learning architecture", "top_k": 3}
```

---

## Self-Learning & RLHF

### POST /api/feedback

Submit thumbs up/down user feedback.
```json
{"message_id": "uuid", "rating": 5, "comment": "Great answer!"}
```

### GET /api/learning-stats

Retrieve current RLHF policy adaptation weights and feedback telemetry.

---

## Health

### GET /api/health

```json
{
  "status": "ok",
  "version": "1.0.0",
  "demo_mode": false,
  "services": {
    "database": "healthy",
    "llm": "configured",
    "knowledge_base": "available"
  }
}
```

---

## Error Responses

All errors follow:
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message"
  }
}
```

Error codes: `VALIDATION_ERROR`, `LLM_ERROR`, `LLM_TIMEOUT`, `INTERNAL_ERROR`, `NOT_FOUND`
