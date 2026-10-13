# Complete Deployment Guide — Dynamic AI Chatbot

This single, comprehensive guide covers all deployment paths for the **Dynamic AI Chatbot**, from **100% free cloud hosting ($0/month)** to **Docker Compose on a VPS** and **manual local development**.

---

## 🧭 Choose Your Deployment Method

| Method | Target Environment | Monthly Cost | Setup Time | Best For |
|---|---|---|---|---|
| **Option 1 (Recommended)** | **Cloud Free Tier** (Neon + Render + Vercel) | **$0** (No credit card) | ~5 mins | Demos, portfolios, personal testing |
| **Option 2** | **Docker Compose** (Local or Cloud VPS) | $0 local / ~$5–10 VPS | ~2 mins | Full local stack or dedicated server |
| **Option 3** | **Manual Bare-Metal** (Python + Node.js) | $0 local | ~5 mins | Direct code debugging & active development |

---

## ☁️ Option 1: 100% Free Cloud Deployment ($0 / Month)

Deploy the entire full-stack project live on the internet with **zero cost** and **no credit card required**.

### Architecture Overview

```
   [End Users / Browsers]
              │
              ▼
   ┌───────────────────────┐
   │    Vercel / Netlify   │  ◄── Frontend (React/Vite SPA on Global CDN)
   │     (100% FREE)       │      • Instant load, 0s cold start, free SSL
   └──────────┬────────────┘
              │ HTTPS API calls
              ▼
   ┌───────────────────────┐
   │       Render.com      │  ◄── Backend (FastAPI Web Service)
   │     (100% FREE)       │      • Auto-deploys from GitHub
   └──────────┬────────────┘      • Python 3 runtime, Swagger docs at /docs
              │ Async connection
              ▼
   ┌───────────────────────┐
   │       Neon.tech       │  ◄── Database (Serverless PostgreSQL)
   │     (100% FREE)       │      • 0.5 GB storage, built-in Web SQL Table Editor
   └───────────────────────┘      • Replaces pgAdmin in the cloud!
```

### Step 1: Create Free PostgreSQL Database on Neon (60 seconds)
1. Go to **[https://neon.tech](https://neon.tech)** and sign up for free (using GitHub or Google).
2. Click **Create Project** (e.g. `chatbot-db`).
3. Under **Connection Details**, copy your connection string:
   ```text
   postgresql://user:password@ep-xyz.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```
   > [!NOTE]
   > The backend automatically handles dialect normalization and SSL params via `async_database_url`. You do not need to edit or reformat the connection string. Neon also provides an interactive SQL Console and Table Viewer in the browser, replacing the need for a separate pgAdmin container in the cloud.

### Step 2: Deploy Backend on Render.com
1. Push your repository to **GitHub**.
2. Go to **[https://dashboard.render.com](https://dashboard.render.com)** and sign in.
3. Click **New +** -> **Web Service** and select your GitHub repository.
4. Configure the service settings:
   - **Name**: `dynamic-chatbot-backend`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: **Free**
5. Under **Environment Variables**, add:
   - `DATABASE_URL`: *(Paste your Neon connection string from Step 1)*
   - `GEMINI_API_KEY`: *(Paste your Google AI Studio API key, or leave empty for Demo Mode)*
   - `GEMINI_MODEL`: `gemini-2.5-flash`
   - `APP_ENV`: `production`
   - `APP_DEBUG`: `false`
   - `SECRET_KEY`: *(Enter any random secret string, e.g. generate via `openssl rand -hex 32`)*
   - `CORS_ORIGINS`: `*`
   - REDIS_URL: *(Optional: paste your free Upstash Redis URL, or leave empty)*
6. Click **Create Web Service**. Once deployed, copy your backend URL:
   `https://dynamic-chatbot-backend.onrender.com`
   *(Verify it by opening `/docs` in your browser)*

### Step 3: Deploy Frontend on Vercel (Fast & Zero Cold Start)
1. Go to **[https://vercel.com](https://vercel.com)** and sign in with GitHub.
2. Click **Add New…** -> **Project** and select your GitHub repository.
3. In the project setup:
   - **Root Directory**: Click `Edit` and select `frontend`
   - **Framework Preset**: `Vite` (auto-detected)
   - Expand **Environment Variables**:
     - `VITE_API_URL`: `https://dynamic-chatbot-backend.onrender.com` *(your Render backend URL)*
4. Click **Deploy**. In under 45 seconds, your frontend will be live at `https://your-chatbot.vercel.app` with automatic SSL.

### ⚡ Alternative: 1-Click Blueprint on Render
If you prefer deploying both frontend and backend together on Render without Vercel:
1. In the Render Dashboard, click **New +** -> **Blueprint**.
2. Connect this repository. Render reads [`render.yaml`](file:///d:/Telegram/AI_Personalized_Chatbot/dynamic-ai-chatbot/render.yaml) from root.
3. Input your `DATABASE_URL` (from Neon) and `GEMINI_API_KEY`.
4. Click **Apply**. Render will provision both services automatically on the free tier.

### 💡 Preventing Render Backend Cold Starts
Render free web services sleep after 15 minutes of inactivity (~30s delay on first request).
* **Fix**: Use a free monitoring service like **[cron-job.org](https://cron-job.org)** or **[UptimeRobot](https://uptimerobot.com)** to send an HTTP GET request to `https://your-backend.onrender.com/api/health` every 10 minutes. This keeps your free backend warm and active 24/7!

---

## 🐳 Option 2: Docker Compose Deployment (Local or VPS)

Docker Compose runs the complete stack locally or on a virtual private server (VPS).

### Running Services

| Container | Port | Description & Access |
|---|---|---|
| **`chatbot-frontend`** | `http://localhost:3000` | React + Vite UI served via Nginx with real-time SSE streaming proxy |
| **`chatbot-backend`** | `http://localhost:8000` | FastAPI REST API & Swagger docs at `/docs` |
| **`chatbot-pgadmin`** | `http://localhost:5050` | pgAdmin 4 Web UI (Login: `admin@chatbot.local` / `admin`, pre-connected) |
| **`chatbot-postgres`** | `localhost:5432` | PostgreSQL 16 database (`chatbot` / `chatbot_pass`) |
| **`chatbot-redis`** | `localhost:6379` | Redis 7 in-memory cache |

### Commands

```bash
# 1. Start all containers in the background
docker compose up --build -d

# 2. Check running container status and health
docker compose ps

# 3. Follow logs across all containers
docker compose logs -f

# 4. Stop all containers gracefully
docker compose down

# 5. Full data reset (removes volumes)
docker compose down -v
```

---

## 💻 Option 3: Manual Local Development

If developing locally without Docker:

### 1. Backend Setup
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate # Linux/macOS

pip install -r requirements.txt
# Environment loaded automatically from backend/.env
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
# Open http://localhost:5173
```

### 3. Run Automated Tests
```bash
cd backend
python -m pytest tests/ -v
# 25/25 unit tests covering security, guardrails, tools, and endpoints
```

---

## 🔒 Security & Environment Variables Checklist

All sensitive variables are isolated into `.env` files and never hardcoded into Dockerfiles or application code:

1. **Backend Environment** ([backend/.env](file:///d:/Telegram/AI_Personalized_Chatbot/dynamic-ai-chatbot/backend/.env)):
   - `GEMINI_API_KEY`: Google AI Studio key (or empty for Demo Mode).
   - `DATABASE_URL`: PostgreSQL connection string (Docker network host: `postgres`, local: `localhost`, cloud: Neon URL).
   - `SECRET_KEY`: Set to a strong random string in production (`openssl rand -hex 32`).
   - `APP_HOST` and `APP_PORT`: Server binding (Dockerfile dynamically uses `APP_HOST` and `PORT`).
2. **Frontend Environment** ([frontend/.env](file:///d:/Telegram/AI_Personalized_Chatbot/dynamic-ai-chatbot/frontend/.env)):
   - `VITE_API_URL`: `/api` when behind Nginx reverse proxy, or the full HTTPS backend URL (`https://your-backend.onrender.com`) when frontend is hosted separately on Vercel.
3. **Never commit `.env` files**: `.gitignore` is configured to prevent committing environment secrets.
