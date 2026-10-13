"""
Analytics service — compute dashboard metrics from stored data.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories import ConversationRepository, FeedbackRepository, MessageRepository
from app.schemas.schemas import AnalyticsOverview

logger = logging.getLogger(__name__)


class AnalyticsService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.conv_repo = ConversationRepository(db)
        self.msg_repo = MessageRepository(db)
        self.fb_repo = FeedbackRepository(db)

    async def get_overview(self) -> AnalyticsOverview:
        total_convs = await self.conv_repo.count_all()
        total_msgs = await self.msg_repo.count_all()
        avg_response = await self.msg_repo.avg_response_time()
        sf = await self.msg_repo.success_failure_counts()
        sentiment_dist = await self.msg_repo.sentiment_distribution()
        avg_rating = await self.fb_repo.avg_rating()

        # Calculate sentiment percentages
        total_sentiment = sum(s["count"] for s in sentiment_dist)
        positive_pct = 0.0
        negative_pct = 0.0
        neutral_pct = 0.0
        if total_sentiment > 0:
            for s in sentiment_dist:
                pct = round((s["count"] / total_sentiment) * 100, 1)
                if s["label"] == "positive":
                    positive_pct = pct
                elif s["label"] == "negative":
                    negative_pct = pct
                elif s["label"] == "neutral":
                    neutral_pct = pct

        return AnalyticsOverview(
            total_conversations=total_convs,
            total_messages=total_msgs,
            avg_response_time_ms=avg_response,
            success_count=sf["success"],
            failure_count=sf["failure"],
            positive_pct=positive_pct,
            negative_pct=negative_pct,
            neutral_pct=neutral_pct,
            avg_feedback_rating=avg_rating,
        )

    async def get_sentiment_data(self) -> Dict[str, Any]:
        dist = await self.msg_repo.sentiment_distribution()
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=30)
        trend = await self.msg_repo.sentiment_trend(start, now)
        return {"distribution": dist, "trend": trend}

    async def get_intent_data(self) -> Dict[str, Any]:
        dist = await self.msg_repo.intent_distribution()
        return {"intents": dist}

    async def get_activity_data(self, days: int = 30) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=days)

        conversations_over_time = await self.conv_repo.count_by_date_range(start, now)
        messages_over_time = await self.msg_repo.count_by_date_range(start, now)
        response_latency = await self.msg_repo.response_time_series(start, now)
        recent = await self.msg_repo.recent_activity(limit=20)
        emotions = await self.msg_repo.emotion_distribution()

        return {
            "conversations_over_time": conversations_over_time,
            "messages_over_time": messages_over_time,
            "response_latency": response_latency,
            "recent_activity": recent,
            "emotion_distribution": emotions,
        }
