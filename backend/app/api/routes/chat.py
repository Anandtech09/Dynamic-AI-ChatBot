"""
Chat API routes — message processing and streaming.
"""

from __future__ import annotations

import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.database import get_db
from app.schemas.schemas import ChatRequest, ChatResponse, ChatResponseData, ErrorDetail
from app.services.chat_service import ChatService
from app.ai.orchestrator import AIOrchestrator
from app.services.rag_service import RAGService
from app.tools import create_tool_registry

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Chat"])


def _get_orchestrator() -> AIOrchestrator:
    settings = get_settings()
    rag = None
    if settings.enable_rag:
        rag = RAGService()
    tool_registry = create_tool_registry(rag)
    return AIOrchestrator(rag_service=rag, tool_registry=tool_registry)


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """Process a chat message through the full AI pipeline."""
    try:
        orchestrator = _get_orchestrator()
        service = ChatService(db, orchestrator)
        data = await service.handle_message(request)
        return ChatResponse(success=True, data=data)
    except ValueError as e:
        return ChatResponse(
            success=False,
            error=ErrorDetail(code="VALIDATION_ERROR", message=str(e)),
        )
    except RuntimeError as e:
        logger.error("Runtime error in chat: %s", e)
        return ChatResponse(
            success=False,
            error=ErrorDetail(code="LLM_ERROR", message="AI service is temporarily unavailable."),
        )
    except Exception as e:
        logger.error("Chat error: %s", e, exc_info=True)
        return ChatResponse(
            success=False,
            error=ErrorDetail(code="INTERNAL_ERROR", message="An unexpected error occurred."),
        )


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """Stream a chat response via Server-Sent Events."""
    orchestrator = _get_orchestrator()
    service = ChatService(db, orchestrator)

    async def event_generator():
        try:
            # Send conversation_id first
            conv_id = request.conversation_id or "new"
            yield f"data: {json.dumps({'type': 'start', 'conversation_id': conv_id})}\n\n"

            async for chunk in service.stream_message(request):
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"

            yield f"data: {json.dumps({'type': 'end'})}\n\n"
        except Exception as e:
            logger.error("Streaming error: %s", e)
            yield f"data: {json.dumps({'type': 'error', 'message': 'Streaming failed'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
