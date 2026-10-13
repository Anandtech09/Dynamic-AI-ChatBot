FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create required directories
RUN mkdir -p /app/data

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import os, httpx; p = os.getenv('PORT') or os.getenv('APP_PORT') or '8000'; h = '127.0.0.1' if os.getenv('APP_HOST') in ('0.0.0.0', None) else os.getenv('APP_HOST'); r = httpx.get(f'http://{h}:{p}/api/health', timeout=5.0); exit(0 if r.status_code == 200 else 1)"

CMD ["sh", "-c", "uvicorn app.main:app --host ${APP_HOST:-0.0.0.0} --port ${PORT:-${APP_PORT:-8000}}"]
