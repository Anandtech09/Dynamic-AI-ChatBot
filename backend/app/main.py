"""
Dynamic AI Chatbot — FastAPI Application Entry Point.

Configures middleware, registers routes, and manages startup/shutdown lifecycle.
"""

from __future__ import annotations

import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes.analytics import router as analytics_router
from app.api.routes.chat import router as chat_router
from app.api.routes.conversations import router as conv_router
from app.api.routes.health import router as health_router
from app.api.routes.rag import router as rag_router
from app.api.routes.settings import router as settings_router
from app.core.config import get_settings
from app.core.logging_config import generate_request_id, request_id_var, setup_logging
from app.db.database import init_db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    settings = get_settings()
    setup_logging(
        level=settings.log_level,
        log_file=settings.log_file if settings.enable_file_logging else None,
    )
    logger.info("Starting %s (env=%s)", settings.app_name, settings.app_env)

    if settings.is_demo_mode:
        logger.warning("⚠ Running in DEMO MODE — set GEMINI_API_KEY for full functionality")

    # Create database tables
    try:
        await init_db()
        logger.info("Database tables created/verified")
    except Exception as e:
        logger.error("Database initialisation failed: %s", e)
        logger.warning("App will start but database features may not work")

    yield

    logger.info("Shutting down %s", settings.app_name)


def create_app() -> FastAPI:
    """Application factory."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description=(
            "A modern AI-powered conversational assistant with NLP analysis, "
            "contextual memory, RAG knowledge retrieval, tool calling, "
            "and analytics dashboard."
        ),
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ── CORS ─────────────────────────────────────────────────────────────────
    origins = settings.cors_origins_list
    allow_all = "*" in origins or not origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if allow_all else origins,
        allow_credentials=not allow_all,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Request-ID Middleware ────────────────────────────────────────────────
    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        rid = generate_request_id()
        request_id_var.set(rid)
        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        return response

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error("Unhandled error: %s", exc, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred. Please try again.",
                },
            },
        )

    app.include_router(chat_router)
    app.include_router(conv_router)
    app.include_router(analytics_router)
    app.include_router(settings_router)
    app.include_router(health_router)
    app.include_router(rag_router)

    @app.get("/", tags=["Root"])
    async def root():
        return {
            "name": settings.app_name,
            "version": "1.0.0",
            "status": "running",
            "demo_mode": settings.is_demo_mode,
            "docs": "/docs",
        }

    return app


app = create_app()
