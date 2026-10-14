"""
RAG API routes — document upload, chunking, indexing, and management.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from pydantic import BaseModel

from app.core.config import get_settings
from app.services.rag_service import RAGService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/rag", tags=["RAG & Knowledge Base"])


def _get_rag() -> RAGService:
    settings = get_settings()
    return RAGService()


class SearchRequest(BaseModel):
    query: str
    top_k: int = 3
    document_title: Optional[str] = None


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    chunk_size: int = Query(500, ge=100, le=2000),
):
    """
    Upload a document (.txt, .md, .pdf, .docx, .csv, .json), chunk it,
    and index the embeddings into PostgreSQL with pgvector.
    """
    rag = _get_rag()
    if not rag.is_available:
        raise HTTPException(status_code=503, detail="PostgreSQL vector store is unavailable")

    try:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

        result = await rag.chunk_and_index_file(
            filename=file.filename or "uploaded_doc.txt",
            file_bytes=content,
            chunk_size=chunk_size,
        )

        pages_info = f" from {result['page_count']} pages" if result.get("page_count", 1) > 1 else ""
        return {
            "success": True,
            "message": f"Successfully indexed {result['chunk_count']} chunks{pages_info} into PostgreSQL pgvector",
            "data": result,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("RAG upload failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")


@router.get("/documents")
async def list_documents():
    """List all currently indexed documents in PostgreSQL pgvector."""
    rag = _get_rag()
    docs = await rag.get_document_list()
    total_chunks = sum(d.get("chunk_count", 0) for d in docs)
    return {
        "success": True,
        "total_documents": len(docs),
        "total_chunks": total_chunks,
        "documents": docs,
        "data": docs,
    }


@router.delete("/documents/{title}")
async def delete_document(title: str):
    """Remove a document and all its chunks from the PostgreSQL pgvector store."""
    rag = _get_rag()
    deleted = await rag.delete_document(title)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Document '{title}' not found")
    return {
        "success": True,
        "message": f"Deleted document '{title}' from knowledge base",
    }


@router.post("/search")
async def search_knowledge(request: SearchRequest):
    """Test hybrid semantic & lexical search with RRF over indexed documents."""
    rag = _get_rag()
    results = await rag.search(
        request.query,
        top_k=request.top_k,
        document_title=request.document_title,
    )
    return {
        "success": True,
        "query": request.query,
        "document_title": request.document_title,
        "count": len(results),
        "results": results,
    }
