"""
Conversation management API routes.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.schemas import ConversationListResponse, ConversationDetail, ExportRequest
from app.services.conversation_service import ConversationService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/conversations", tags=["Conversations"])


@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    session_id: str = Query(default="default"),
    db: AsyncSession = Depends(get_db),
):
    """List all conversations for a session."""
    service = ConversationService(db)
    conversations = await service.list_conversations(session_id)
    return ConversationListResponse(success=True, data=conversations)


@router.get("/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a conversation with all its messages (accelerated with Redis cache)."""
    from app.services.cache_service import get_cache_service
    cache = get_cache_service()
    cache_key = f"conv:{conversation_id}:detail"
    cached = await cache.get(cache_key)
    if cached is not None:
        return {"success": True, "data": cached, "cached": True}

    service = ConversationService(db)
    detail = await service.get_conversation(conversation_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Conversation not found")

    dumped = detail.model_dump()
    await cache.set(cache_key, dumped, ttl=1800)
    return {"success": True, "data": dumped, "cached": False}


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a conversation and all its messages."""
    service = ConversationService(db)
    deleted = await service.delete_conversation(conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")

    from app.services.cache_service import get_cache_service
    cache = get_cache_service()
    await cache.delete(f"conv:{conversation_id}:detail")
    await cache.delete_pattern("conv:list:*")
    return {"success": True, "message": "Conversation deleted"}


@router.post("/{conversation_id}/export")
async def export_conversation(
    conversation_id: str,
    request: ExportRequest,
    db: AsyncSession = Depends(get_db),
):
    """Export a conversation in the specified format."""
    service = ConversationService(db)
    content = await service.export_conversation(conversation_id, request.format)
    if not content:
        raise HTTPException(status_code=404, detail="Conversation not found")

    media_type = {
        "json": "application/json",
        "txt": "text/plain",
        "md": "text/markdown",
    }.get(request.format, "text/plain")

    return PlainTextResponse(content=content, media_type=media_type)
