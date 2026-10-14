"""
Analytics API routes — dashboard data.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.schemas import AnalyticsResponse
from app.services.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/overview", response_model=AnalyticsResponse)
async def analytics_overview(db: AsyncSession = Depends(get_db)):
    """Get high-level KPI metrics."""
    service = AnalyticsService(db)
    overview = await service.get_overview()
    return AnalyticsResponse(success=True, data=overview.model_dump())


@router.get("/sentiment", response_model=AnalyticsResponse)
async def analytics_sentiment(db: AsyncSession = Depends(get_db)):
    """Get sentiment distribution and trend data."""
    service = AnalyticsService(db)
    data = await service.get_sentiment_data()
    return AnalyticsResponse(success=True, data=data)


@router.get("/intents", response_model=AnalyticsResponse)
async def analytics_intents(db: AsyncSession = Depends(get_db)):
    """Get intent distribution data."""
    service = AnalyticsService(db)
    data = await service.get_intent_data()
    return AnalyticsResponse(success=True, data=data)


@router.get("/activity", response_model=AnalyticsResponse)
async def analytics_activity(
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Get time-series activity data for charts."""
    service = AnalyticsService(db)
    data = await service.get_activity_data(days=days)
    return AnalyticsResponse(success=True, data=data)


@router.get("/learning", response_model=AnalyticsResponse)
async def analytics_learning():
    """
    Get dynamic self-learning and reinforcement metrics from learning_state.json.
    Reports adaptation score, human feedback stats, cumulative rewards,
    and intent policy weights.
    """
    from app.nlp.self_learning import get_self_learning_service
    service = get_self_learning_service()
    data = service.get_stats()
    data["interactions"] = service.state.get("interactions", 0)
    data["cumulative_reward"] = round(float(service.state.get("cumulative_reward", 0.0)), 3)
    data["rewards_history"] = list(reversed(service.state.get("rewards", [])[-15:]))
    return AnalyticsResponse(success=True, data=data)
