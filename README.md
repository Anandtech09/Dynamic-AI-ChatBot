# Dynamic AI Chatbot

A modern AI-powered conversational assistant built with **Google Gemini**, **FastAPI**, **React**, and **PostgreSQL**. Features NLP analysis, contextual memory, RAG knowledge retrieval, tool calling, and an analytics dashboard.

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![React](https://img.shields.io/badge/React-18-61dafb?logo=react)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)
![Gemini](https://img.shields.io/badge/Google-Gemini-4285F4?logo=google)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| **AI Conversations** | Context-aware chat powered by Google Gemini (with graceful Demo mode) |
| **Multimodal Vision & Voice** | Audio recording (up to 3 min) with waveform player + image attachments |
| **Intent Recognition** | 12 functional intent classes via local rule + ML classification |
| **Entity Extraction** | Detects dates, emails, URLs, tech stacks, organizations, currencies |
| **Sentiment & Emotion** | Real-time polarity score (-1.0 to +1.0) and 7 emotion classifications |
| **Self-Learning (RLHF)** | Policy weights adapted based on human feedback rewards |
| **Contextual Memory** | Short-term + long-term conversation memory with automatic summarisation |
| **RAG Knowledge Base** | Ingestion of .pdf, .docx, .md, .txt into PostgreSQL pgvector embeddings |
| **Tool Calling** | Calculator, DateTime, and semantic knowledge retrieval |
| **Analytics Dashboard** | Live KPIs, sentiment trends, intent frequency, latency metrics |
| **Multilingual** | English, Hindi, Hinglish support |
| **Export** | JSON, TXT, Markdown conversation export |
| **Dark/Light Theme** | System-aware theme with manual override |
| **Demo Mode** | 100% functional without an API key for immediate zero-cost evaluation |

---

## 🏗️ Architecture

```
User → React Frontend → FastAPI REST API → AI Orchestrator
                                              ├── Intent Recognition (Statistical TF-IDF + Centroid ML)
                                              ├── Entity Extraction
                                              ├── Sentiment Analysis (VADER Mathematical Valence Modeling)
                                              ├── Emotion Detection
                                              ├── Knowledge Retrieval (Native PostgreSQL pgvector)
                                              ├── Tool Execution
                                              ├── Context Management
                                              ├── Response Generation (Gemini)
                                              └── Guardrails
                                           → PostgreSQL + pgvector (persistence & vector store)
                                           → Redis (caching)
```

See [docs/architecture.md](docs/architecture.md) for detailed diagrams.

---

## 🛠️ Technology Stack

### Backend
- **Python 3.11+**, FastAPI, Uvicorn, Pydantic v2
- **SQLAlchemy** (async) + **Alembic** migrations
- **PostgreSQL 16 + pgvector** for persistence and native vector search
- **Redis** for caching

### AI/LLM
- **Google Gemini** (via `google-generativeai` SDK)
- LLM provider abstraction (swappable)
- Structured JSON extraction for NLP tasks

### Frontend
- **React 18** + **TypeScript** + **Vite**
- **TailwindCSS** for styling
- **Recharts** for analytics charts
- **Zustand** for state management
- **react-markdown** + **react-syntax-highlighter**

### Infrastructure
- **Docker** + **Docker Compose**
- Health checks, CORS, rate limiting

---

## 📁 Project Structure

```
dynamic-ai-chatbot/
├── backend/
│   ├── app/
│   │   ├── ai/              # LLM providers, prompts, orchestrator, guardrails
│   │   ├── api/routes/       # FastAPI endpoints
│   │   ├── core/             # Config, logging, security
│   │   ├── db/               # Models, repositories, database
│   │   ├── nlp/              # Intent classification, NER, sentiment, FAQ, RLHF
│   │   ├── schemas/          # Pydantic request/response models
│   │   ├── services/         # Business logic layer (RAG, Chat, Conversations)
│   │   ├── tools/            # Calculator, DateTime, KnowledgeSearch
│   │   └── main.py           # FastAPI app factory
│   ├── tests/
│   ├── alembic/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/       # Sidebar, ChatArea, Analytics, Settings, About
│   │   ├── services/         # API client
│   │   ├── store/            # Zustand state
│   │   └── types/            # TypeScript interfaces
│   ├── package.json
│   └── Dockerfile
├── data/knowledge/           # RAG knowledge base documents
├── scripts/                  # Utility scripts
├── docs/                     # Documentation
├── docker-compose.yml
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Redis 7+
- Google Gemini API key (from [Google AI Studio](https://aistudio.google.com/))

### 1. Clone and Setup Backend

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### 3. Setup Database

```bash
# Create PostgreSQL database
createdb chatbot_db

# Run migrations (or let FastAPI auto-create tables)
alembic upgrade head
```

### 4. Index Knowledge Base

```bash
cd ..
python scripts/index_knowledge.py
```

### 5. Start Backend

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### 6. Setup and Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit **http://localhost:5173**

---

## 🐳 Docker Setup

The easiest way to run the entire stack with a single command:

```bash
# Configure your Gemini API key in backend/.env (or leave empty for Demo Mode)
# Start all containers in detached mode
docker compose up --build -d

# Check running services
docker compose ps
```

### Running Services:
- **Frontend Web UI**: [http://localhost:3000](http://localhost:3000)
- **Backend API**: [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **pgAdmin 4 Database Studio**: [http://localhost:5050](http://localhost:5050) (Login: `admin@chatbot.local` / `admin`)
- **PostgreSQL 16**: `localhost:5432` (User: `chatbot`, DB: `chatbot_db`)
- **Redis 7**: `localhost:6379`

---

## ☁️ 100% Free Cloud Deployment (Zero Cost)

Deploy online for **$0 / month** with no credit card required:
- **Database**: [Neon.tech](https://neon.tech) (Free Serverless PostgreSQL)
- **Backend**: [Render.com](https://render.com) (Free Python Web Service)
- **Frontend**: [Vercel](https://vercel.com) (Free Global Edge Hosting)

Detailed step-by-step instructions: **[docs/deployment.md](docs/deployment.md)**
Or use the 1-click **[render.yaml](render.yaml)** Blueprint on Render.


---

## 🔧 Environment Variables

All variables are loaded automatically from `.env` (or environment variables). Never commit secrets to version control.

| Variable | Source | Description |
|----------|--------|-------------|
| `GEMINI_API_KEY` | `.env` | Google Gemini API key (optional for Demo mode) |
| `GEMINI_MODEL` | `.env` | Gemini model name (default: `gemini-2.5-flash`) |
| `DATABASE_URL` | `.env` | PostgreSQL async connection string |
| `REDIS_URL` | `.env` | Redis connection string |
| `SECRET_KEY` | `.env` | Application secret key for tokens and encryption |
| `CORS_ORIGINS` | `.env` | Whitelisted frontend origins |
| `APP_ENV` | `.env` | Environment (`development` / `production`) |
| `RATE_LIMIT_PER_MINUTE` | `.env` | API rate limit per client session |
| `MAX_MESSAGE_LENGTH` | `.env` | Maximum incoming user message characters |
| `ENABLE_RAG` | `.env` | Enable/disable PostgreSQL pgvector knowledge retrieval |
| `ENABLE_TOOLS` | `.env` | Enable/disable deterministic tool execution |

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/chat` | Send chat message (text, voice, image) |
| `POST` | `/api/chat/stream` | Stream chat response (SSE) |
| `GET` | `/api/conversations` | List conversations |
| `GET` | `/api/conversations/{id}` | Get conversation detail |
| `DELETE` | `/api/conversations/{id}` | Delete conversation |
| `POST` | `/api/conversations/{id}/export` | Export conversation |
| `GET` | `/api/analytics/overview` | Dashboard KPIs |
| `GET` | `/api/analytics/sentiment` | Sentiment data |
| `GET` | `/api/analytics/intents` | Intent distribution |
| `GET` | `/api/analytics/activity` | Activity time series |
| `GET` | `/api/settings` | Get preferences |
| `PUT` | `/api/settings` | Update preferences |
| `POST` | `/api/feedback` | Submit feedback (updates RLHF policy) |
| `GET` | `/api/learning-stats` | Retrieve RLHF adaptation stats |
| `POST` | `/api/rag/upload` | Upload & chunk document into pgvector |
| `GET` | `/api/rag/documents` | List indexed knowledge documents |
| `DELETE` | `/api/rag/documents/{title}` | Remove document and vector chunks |
| `POST` | `/api/rag/search` | Semantic search over knowledge base |

Full Swagger docs at `/docs` when backend is running.

---

## 🧠 AI Pipeline

Every message flows through:

```
Input Validation → Load Context → Detect Intent → Extract Entities
→ Analyse Sentiment/Emotion → Check Knowledge Base (RAG)
→ Execute Tools → Build Context → Generate Response (Gemini)
→ Apply Guardrails → Store Interaction → Update Analytics → Return
```

---

## 🧪 Testing

```bash
# Backend tests (no API key required)
cd backend
pytest tests/ -v

# Frontend build check
cd frontend
npm run build
```

Tests mock external Gemini requests — no live API key needed.

---

## 🔒 Security

- API keys loaded from environment variables only
- No secrets in source code or browser storage
- CORS whitelist configuration
- Input validation and size limits
- Prompt injection detection
- Response guardrails (blocks leaked secrets)
- Sanitised markdown rendering

---

## 🌍 Language Support

| Language | Code | Example |
|----------|------|---------|
| English | `en` | "Explain machine learning" |
| Hindi | `hi` | "मशीन लर्निंग क्या है?" |
| Hinglish | `hinglish` | "Mujhe FastAPI samjhao" |

Extensible — add more languages in `prompt_templates.py`.

---

## 📊 Analytics

The dashboard shows real metrics from stored conversations:
- Total conversations and messages
- Average response time
- Sentiment distribution (pie chart)
- Intent distribution (bar chart)
- Messages and latency over time
- Recent activity table
- Success/failure rates

---

## 🔮 Future Enhancements

- Production model fine-tuning with custom LoRA adapters
- Third-party chat connectors (WhatsApp, Telegram, Slack bots)
- Multi-user authentication & OAuth2 integration
- Team workspaces and role-based access control (RBAC)
- Multi-turn conversational evaluation benchmarks (RAGAS)
- Hybrid dense + sparse (BM25) vector search in PostgreSQL

---

## 📝 Note on AI Approach

This system integrates **pretrained NLP components** and a **generative AI model** (Google Gemini) rather than training a large language model from scratch. The value is in the **orchestration architecture**: context management, structured extraction, knowledge retrieval, tool calling, and analytics. Custom model fine-tuning and reinforcement learning are documented as future enhancements.

---

## 📄 License

MIT License — see [LICENSE](LICENSE).
