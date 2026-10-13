# Setup Guide — Dynamic AI Chatbot

## Prerequisites

- **Docker Desktop** (recommended for 1-command startup) OR:
  - Python 3.10+
  - Node.js 18+
  - PostgreSQL 14+
  - Redis 7+
- Optional: Google Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey) (app falls back gracefully to built-in Demo Mode if omitted).

---

## 1. Automated Docker Compose Setup (Recommended)

1. Make sure Docker Desktop is running.
2. Ensure environment files are configured:
   - [backend/.env](file:///d:/Telegram/AI_Personalized_Chatbot/dynamic-ai-chatbot/backend/.env) (set your `GEMINI_API_KEY` or leave blank for demo mode)
   - [frontend/.env](file:///d:/Telegram/AI_Personalized_Chatbot/dynamic-ai-chatbot/frontend/.env) (`VITE_API_URL=/api`)
3. Launch the full environment:
   ```bash
   docker compose up --build -d
   ```
4. Access the applications:
   - **Chatbot Web UI**: [http://localhost:3000](http://localhost:3000)
   - **FastAPI Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
   - **pgAdmin 4 Database Studio**: [http://localhost:5050](http://localhost:5050) (Login: `admin@chatbot.local` / `admin`)

---

## 2. Local Development Setup (Manual)

### Backend

```bash
cd backend

# Create and activate virtual environment (optional)
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate # Linux/macOS

# Install dependencies
pip install -r requirements.txt

# Environment is loaded from backend/.env
# Run the FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend

# Install packages
npm install

# Build verification
npm run build

# Start Vite dev server with proxy
npm run dev
# Accessible at http://localhost:5173
```

---

## 3. Running Test Suites

```bash
cd backend
python -m pytest tests/ -v
```
All 25 automated unit tests verify:
- Security input sanitization & prompt injection prevention
- Secret and API key leak detection in guardrails
- Math Calculator & DateTime tool execution
- LLM provider fallback & demo mode responses
- Orchestration and title generation
- API health and root endpoints

---

## 4. Troubleshooting

| Issue | Solution |
|-------|----------|
| `Docker Desktop Service error` | Open Docker Desktop from your Windows Start Menu to initialize the engine service |
| `Demo Mode shown in UI` | Set `GEMINI_API_KEY` in `backend/.env` with your API key from Google AI Studio |
| `PostgreSQL connection issue` | When using Docker, host is `postgres`. When running manually outside Docker, change `DATABASE_URL` host to `localhost` |
| `pgAdmin server connection` | Pre-configured in `scripts/pgadmin/servers.json`; password is `chatbot_pass` |
