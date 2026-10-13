# Dynamic AI Chatbot — Project Report

---

## 1. Introduction

The Dynamic AI Chatbot is a modern, full-stack conversational assistant application that leverages Google's Gemini generative AI model to provide intelligent, context-aware responses. The system goes beyond a simple question-answer interface by incorporating a complete NLP analysis pipeline, contextual memory, knowledge retrieval (RAG), tool execution, and an analytics dashboard.

This project demonstrates the practical application of AI engineering principles — integrating pretrained models through API-based services, building robust orchestration pipelines, and creating production-ready software architecture.

---

## 2. Problem Statement

Most basic chatbot implementations follow a simplistic pattern:

```
User message → LLM API call → Display response
```

This approach lacks:
- **Context awareness** — each message is treated independently
- **NLP analysis** — no understanding of intent, entities, or sentiment
- **Knowledge grounding** — responses rely entirely on the model's training data
- **Observability** — no analytics or performance tracking
- **Robustness** — no error handling, fallback, or security measures

There is a need for a chatbot architecture that wraps AI capabilities in proper software engineering practices, providing a complete, maintainable, and extensible system.

---

## 3. Objectives

1. Build a conversational AI assistant using Google Gemini as the core language model
2. Implement a structured NLP pipeline for intent recognition, entity extraction, sentiment analysis, and emotion detection
3. Maintain conversational context through short-term and long-term memory
4. Implement RAG (Retrieval-Augmented Generation) for knowledge-grounded responses
5. Provide tool-calling capabilities for deterministic operations
6. Create an analytics dashboard with real metrics from stored conversations
7. Support multiple languages (English, Hindi, Hinglish)
8. Ensure security, error handling, and production readiness
9. Document the architecture for academic and portfolio purposes

---

## 4. Existing System

The reference implementations provided include:

**Reference 1 (PersonalizedChatBot.ipynb):** A Streamlit-based chatbot using LangChain and Gemini with basic session-state history management. Simple but lacks persistence, NLP analysis, and proper architecture.

**Reference 2 (AI chatbot.zip):** A Flask web application with a chat interface, basic sentiment heuristics, and analytics concepts. Uses vanilla HTML/CSS/JavaScript frontend with simple keyword-based analysis.

**Limitations of existing systems:**
- No structured NLP pipeline
- Keyword-based sentiment (not ML-based)
- No conversation persistence across sessions
- No knowledge retrieval
- No tool execution
- Limited error handling
- Tightly coupled architecture
- Hardcoded configuration and API keys

---

## 5. Proposed System

The proposed system implements a layered architecture:

```
Frontend (React + TypeScript)
    ↓ REST API
Backend (FastAPI + Python)
    ↓
AI Orchestrator
    ├── Intent Recognition (Statistical TF-IDF + Centroid Cosine Similarity)
    ├── Entity Extraction (Multi-pattern NER & POS extraction)
    ├── Sentiment Analysis (VADER Mathematical Valence Modeling)
    ├── Emotion Detection (6-Class Affect Distribution)
    ├── Knowledge Retrieval (Native PostgreSQL pgvector search)
    ├── Tool Execution (Calculator, DateTime, Knowledge)
    ├── Context Management (history + summaries)
    ├── Response Generation (Google Gemini)
    └── Guardrails (safety filtering)
    ↓
PostgreSQL 16 + pgvector (conversation persistence & vector store)
Redis (caching)
```

---

## 6. System Architecture

The application follows a clean monorepo structure with three main tiers:

### Presentation Tier
React 18 with TypeScript, TailwindCSS, Recharts, and Zustand state management. Provides a polished chat interface, analytics dashboard, and settings page.

### Application Tier
FastAPI with Pydantic v2 for request/response validation. Implements the Repository pattern for database access, Service pattern for business logic, and a central AI Orchestrator for the intelligence pipeline.

### Data Tier
PostgreSQL with pgvector for relational data (conversations, messages, feedback, preferences) as well as native 384-dimensional vector embeddings (RAG), and Redis for caching.

The LLM provider is abstracted behind a `LLMProvider` interface, allowing future replacement of Google Gemini with other providers.

---

## 7. Technologies Used

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Backend Framework | FastAPI 0.115 | Async REST API |
| Language | Python 3.11+ | Backend logic |
| Frontend | React 18 + TypeScript | User interface |
| Build Tool | Vite | Frontend bundling |
| Styling | TailwindCSS 3 | UI design |
| Charts | Recharts | Analytics visualisation |
| State Management | Zustand | Frontend state |
| AI Model | Google Gemini | Response generation + NLP |
| Database | PostgreSQL 16 | Data persistence |
| ORM | SQLAlchemy 2.0 (async) | Database abstraction |
| Migrations | Alembic | Schema management |
| Vector Store | PostgreSQL pgvector | Native RAG embeddings |
| Caching | Redis 7 | Performance |
| Containerisation | Docker + Compose | Deployment |
| Testing | Pytest | Backend tests |

---

## 8. NLP Components

### 8.1 Approach

All NLP tasks use **structured LLM extraction** — the Gemini model is prompted to return JSON-formatted analysis rather than training custom models. This provides:
- High accuracy leveraging Gemini's language understanding
- Zero training data requirement
- Easy extensibility
- Consistent structured output via Pydantic validation

### 8.2 Component Summary

| Component | Method | Output |
|-----------|--------|--------|
| Intent Recognition | Structured LLM prompt | Primary intent + confidence + secondary intents |
| Entity Extraction | Structured LLM prompt | Entity text + type (person, location, date, etc.) |
| Sentiment Analysis | Structured LLM prompt | Label (positive/neutral/negative) + score |
| Emotion Detection | Structured LLM prompt | Label (joy/sadness/anger/etc.) + score |

The architecture is modular — custom trained classifiers can replace LLM-based extraction in the future.

---

## 9. LLM Integration

Google Gemini is integrated through the `google-generativeai` Python SDK. Key design decisions:

- **Provider abstraction**: `LLMProvider` base class with `GeminiProvider` implementation
- **Demo mode**: `DemoProvider` returns safe placeholder responses when no API key is configured
- **Configurable model**: Model name is set via `GEMINI_MODEL` environment variable
- **Streaming support**: Async generator for token-by-token streaming via SSE
- **Error isolation**: LLM failures are caught and converted to user-friendly fallback messages

---

## 10. Intent Recognition

The system classifies user messages into 15+ intent categories:

| Intent | Example |
|--------|---------|
| `greeting` | "Hello!", "Hi there" |
| `technical_question` | "How does FastAPI work?" |
| `calculation` | "What is 25 * 4?" |
| `summarization` | "Summarise this article" |
| `code_help` | "Write a Python function" |
| `complaint` | "This isn't working properly" |
| `farewell` | "Goodbye" |

Multiple intents are detected for compound requests (e.g., "How much does it cost and can I cancel?" → `pricing` + `cancellation`).

---

## 11. Named Entity Recognition

Extracted entity types include: person, organization, location, date, time, email, phone, number, product, technology, programming_language, URL, order_id, currency_amount.

Example:
```
Input:  "Book a flight from Kochi to Delhi tomorrow"
Output: [{"text": "Kochi", "label": "location"},
         {"text": "Delhi", "label": "location"},
         {"text": "tomorrow", "label": "date"}]
```

---

## 12. Sentiment Analysis

Real sentiment classification with confidence scores, not keyword matching:

```
Input:  "This is really frustrating, nothing works"
Output: {"sentiment": "negative", "score": 0.92,
         "emotion": "frustration", "emotion_score": 0.88}
```

Sentiment data feeds into analytics charts and can influence response tone through emotion-aware prompting.

---

## 13. Contextual Memory

### Short-term Memory
The most recent messages (configurable via `MAX_CONTEXT_MESSAGES`) are included in the LLM context window.

### Long-term Memory
All conversations are persisted in PostgreSQL. Previous conversations can be reopened with full history.

### Conversation Summarisation
For long conversations (>10 messages), the system generates compressed summaries to maintain context without exceeding token limits. Summaries capture key topics, user preferences, and important facts.

### Context Window Management
The system bounds the context sent to Gemini: recent messages + summary + RAG context + tool results, preventing token overflow.

---

## 14. RAG (Retrieval-Augmented Generation)

### Pipeline
1. **Indexing**: Documents in `data/knowledge/` are split into chunks and embedded into PostgreSQL with pgvector (vector(384))
2. **Retrieval**: User queries are semantically matched against stored chunks
3. **Augmentation**: Retrieved context is injected into the system prompt
4. **Generation**: Gemini generates responses grounded in retrieved information

### Source Attribution
When RAG content is used, source metadata is included in the response:
```json
{"sources": [{"title": "AI Concepts", "section": "Machine Learning", "score": 0.87}]}
```

The system never fabricates sources — if no relevant document is found, it falls back to general LLM knowledge.

---

## 15. Analytics

The analytics dashboard displays real metrics computed from stored conversation data:

- **KPI cards**: Total conversations, messages, average response time, feedback rating
- **Sentiment distribution**: Pie chart of positive/neutral/negative
- **Intent distribution**: Bar chart of top detected intents
- **Time series**: Messages over time, response latency trends
- **Recent activity**: Table with message previews, intents, sentiments, latency

All analytics come from backend database queries — no fabricated data.

---

## 16. Security

| Measure | Implementation |
|---------|---------------|
| Secrets management | Environment variables, `.env` files, never in code |
| CORS | Configurable whitelist |
| Input validation | Pydantic models, size limits |
| Rate limiting | Configurable per-minute limits |
| Prompt injection | Pattern detection + system prompt hardening |
| Output guardrails | Blocks leaked API keys, secrets in responses |
| Frontend isolation | No API keys in browser, no unsafe HTML execution |

---

## 17. Testing

The test suite covers:
- **Security functions**: Input sanitisation, prompt injection detection
- **Guardrails**: Secret blocking, response truncation
- **Tools**: Calculator operations, DateTime, registry
- **AI providers**: Demo mode responses, structured output
- **Orchestrator**: Full pipeline in demo mode
- **Schemas**: Validation of request/response models
- **API endpoints**: Root endpoint health check

All tests mock external Gemini requests — no live API key required to run the test suite.

---

## 18. Results

The implemented system successfully demonstrates:

1. **Functional AI chatbot** with intelligent, contextual responses
2. **Structured NLP pipeline** providing real intent, entity, sentiment, and emotion analysis
3. **Persistent conversations** with context maintained across messages
4. **Knowledge retrieval** grounding responses in indexed documents
5. **Tool execution** for calculations and date/time queries
6. **Analytics dashboard** with real metrics and interactive charts
7. **Multilingual support** for English, Hindi, and Hinglish
8. **Production-ready architecture** with Docker, migrations, health checks, and error handling

---

## 19. Limitations

1. NLP analysis relies on LLM API calls, adding latency per message
2. No offline mode — requires internet for Gemini API
3. No user authentication — uses session-based identification
4. RAG is limited to text documents (no PDF, image, or audio processing)
5. No voice input/output
6. Single-tenant deployment (no multi-user isolation)

---

## 20. Future Enhancements

1. **Custom Intent Classifier**: Train a dedicated classifier using collected labelled conversations
2. **Model Fine-tuning**: Use feedback data for Gemini fine-tuning when available
3. **Reinforcement Learning**: Implement RLHF using collected user feedback ratings
4. **Channel Adapters**: WhatsApp, Telegram, Slack integration
5. **Voice Interface**: Speech-to-text input, text-to-speech output
6. **Authentication**: User accounts with role-based access
7. **File Upload**: PDF/document upload for on-demand RAG
8. **Advanced Caching**: Semantic cache for frequently asked questions

---

## 21. Conclusion

The Dynamic AI Chatbot project demonstrates how pretrained AI models can be integrated into a well-architected software system to create a capable conversational assistant. Rather than training a large language model from scratch, the project adds value through:

- **Orchestration**: A structured pipeline that coordinates multiple AI capabilities
- **Context management**: Intelligent memory with summarisation for long conversations
- **Knowledge grounding**: RAG pipeline connecting the AI to curated information
- **Observability**: Real analytics derived from actual conversation data
- **Engineering quality**: Clean architecture, testing, documentation, and deployment

The modular design ensures future extensibility — custom trained models, additional channels, and advanced features can be added without rewriting the core system.
