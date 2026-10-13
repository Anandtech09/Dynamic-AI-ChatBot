"""
Health check and knowledge management routes.
"""

from __future__ import annotations

import logging
import os

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.database import get_db
from app.schemas.schemas import HealthResponse, KnowledgeListResponse
from app.services.rag_service import RAGService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Health & Knowledge"])


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    """Overall application health check."""
    settings = get_settings()
    services = {}

    # Database
    try:
        await db.execute(text("SELECT 1"))
        services["database"] = "healthy"
    except Exception:
        services["database"] = "unhealthy"

    # Gemini
    services["llm"] = "configured" if settings.gemini_api_key else "demo_mode"

    # RAG (PostgreSQL pgvector)
    rag = RAGService()
    services["knowledge_base"] = "available" if rag.is_available else "unavailable"

    status = "ok" if services.get("database") == "healthy" else "degraded"

    return HealthResponse(
        status=status,
        version="1.0.0",
        demo_mode=settings.is_demo_mode,
        services=services,
    )


@router.get("/knowledge", response_model=KnowledgeListResponse)
async def list_knowledge():
    """List indexed knowledge documents."""
    rag = RAGService()
    docs = await rag.get_document_list()
    return KnowledgeListResponse(
        success=True,
        documents=[
            {"title": d["title"], "content": "", "source": d.get("source", ""), "chunk_count": d.get("chunk_count", 0)}
            for d in docs
        ],
        total=len(docs),
    )


@router.post("/knowledge/index")
async def index_knowledge():
    """Index all documents in the knowledge directory."""
    rag = RAGService()
    candidates = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))), "data", "knowledge"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "data", "knowledge"),
        "/app/data/knowledge",
        "./data/knowledge",
        "../data/knowledge",
    ]
    knowledge_dir = next((c for c in candidates if os.path.exists(c)), candidates[0])

    if not os.path.exists(knowledge_dir):
        return {"success": False, "message": f"Knowledge directory not found: {knowledge_dir}"}

    chunks = await rag.index_directory(knowledge_dir)
    return {"success": True, "message": f"Indexed {chunks} chunks", "chunks": chunks}
