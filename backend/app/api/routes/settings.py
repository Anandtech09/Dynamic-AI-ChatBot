"""
Settings and feedback API routes.
"""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.repositories import FeedbackRepository, MessageRepository, UserPreferencesRepository
from app.nlp.self_learning import get_self_learning_service
from app.schemas.schemas import (
    FeedbackRequest,
    FeedbackResponse,
    SettingsRequest,
    SettingsResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Settings"])


@router.get("/settings", response_model=SettingsResponse)
async def get_settings(
    session_id: str = Query(default="default"),
    db: AsyncSession = Depends(get_db),
):
    """Get user preferences."""
    repo = UserPreferencesRepository(db)
    prefs = await repo.get_or_create(session_id)
    return SettingsResponse(
        success=True,
        data={
            "theme": prefs.theme,
            "language": prefs.language,
            "temperature": prefs.temperature,
            "max_tokens": prefs.max_tokens,
            "timestamps_enabled": prefs.timestamps_enabled,
            "sentiment_enabled": prefs.sentiment_enabled,
            "compact_mode": prefs.compact_mode,
            "auto_scroll": prefs.auto_scroll,
            "suggestions_enabled": prefs.suggestions_enabled,
        },
    )


@router.put("/settings", response_model=SettingsResponse)
async def update_settings(
    request: SettingsRequest,
    session_id: str = Query(default="default"),
    db: AsyncSession = Depends(get_db),
):
    """Update user preferences."""
    repo = UserPreferencesRepository(db)
    data = request.model_dump(exclude_none=True)
    prefs = await repo.update(session_id, data)
    return SettingsResponse(
        success=True,
        data={
            "theme": prefs.theme,
            "language": prefs.language,
            "temperature": prefs.temperature,
            "max_tokens": prefs.max_tokens,
            "timestamps_enabled": prefs.timestamps_enabled,
            "sentiment_enabled": prefs.sentiment_enabled,
            "compact_mode": prefs.compact_mode,
            "auto_scroll": prefs.auto_scroll,
            "suggestions_enabled": prefs.suggestions_enabled,
        },
    )


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    request: FeedbackRequest,
    db: AsyncSession = Depends(get_db),
):
    """Submit feedback for a message and update RLHF self-learning policy."""
    try:
        msg_id = uuid.UUID(request.message_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid message ID")

    repo = FeedbackRepository(db)
    msg_repo = MessageRepository(db)
    try:
        await repo.create(message_id=msg_id, rating=request.rating, comment=request.comment)
        
        # RLHF feedback reward tracking
        msg = await msg_repo.get_by_id(msg_id)
        intent = msg.intent if msg else None
        learning_service = get_self_learning_service()
        reward = learning_service.record_feedback(request.rating, intent=intent, comment=request.comment)
        logger.info("RLHF policy updated with reward: %+.2f for intent: %s", reward, intent)
    except Exception as e:
        logger.error("Feedback error: %s", e)
        raise HTTPException(status_code=400, detail="Could not save feedback")

    return FeedbackResponse(success=True, message="Feedback recorded — thank you for training the AI!")


@router.get("/learning-stats")
async def get_learning_stats():
    """Retrieve current RLHF self-learning policy stats and reward weights."""
    service = get_self_learning_service()
    return service.get_stats()
