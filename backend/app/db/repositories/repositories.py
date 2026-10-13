"""
Database repository layer — all raw SQL / ORM queries live here.
"""

from __future__ import annotations

import math
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Sequence

from sqlalchemy import delete, desc, func, select, update, and_, cast, Date
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    Conversation,
    ConversationSummary,
    Feedback,
    KnowledgeChunk,
    KnowledgeDocument,
    Message,
    UserPreferences,
)


# ── Conversation Repository ─────────────────────────────────────────────────

class ConversationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, session_id: str, title: str = "New Conversation", language: str = "en") -> Conversation:
        conv = Conversation(session_id=session_id, title=title, language=language)
        self.db.add(conv)
        await self.db.flush()
        return conv

    async def get_by_id(self, conv_id: uuid.UUID) -> Optional[Conversation]:
        result = await self.db.execute(
            select(Conversation).where(Conversation.id == conv_id)
        )
        return result.scalar_one_or_none()

    async def list_by_session(self, session_id: str, limit: int = 50) -> Sequence[Conversation]:
        result = await self.db.execute(
            select(Conversation)
            .where(Conversation.session_id == session_id, Conversation.is_archived == False)
            .order_by(desc(Conversation.updated_at))
            .limit(limit)
        )
        return result.scalars().all()

    async def update_title(self, conv_id: uuid.UUID, title: str) -> None:
        await self.db.execute(
            update(Conversation).where(Conversation.id == conv_id).values(title=title)
        )

    async def delete_conversation(self, conv_id: uuid.UUID) -> bool:
        result = await self.db.execute(
            delete(Conversation).where(Conversation.id == conv_id)
        )
        return result.rowcount > 0

    async def count_all(self) -> int:
        result = await self.db.execute(select(func.count(Conversation.id)))
        return result.scalar() or 0

    async def count_by_date_range(self, start: datetime, end: datetime) -> List[Dict]:
        result = await self.db.execute(
            select(
                cast(Conversation.created_at, Date).label("date"),
                func.count(Conversation.id).label("count"),
            )
            .where(Conversation.created_at.between(start, end))
            .group_by(cast(Conversation.created_at, Date))
            .order_by(cast(Conversation.created_at, Date))
        )
        return [{"date": str(row.date), "count": row.count} for row in result.all()]


# ── Message Repository ───────────────────────────────────────────────────────

class MessageRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, **kwargs) -> Message:
        msg = Message(**kwargs)
        self.db.add(msg)
        await self.db.flush()
        return msg

    async def get_by_id(self, message_id: uuid.UUID) -> Optional[Message]:
        result = await self.db.execute(select(Message).where(Message.id == message_id))
        return result.scalar_one_or_none()

    async def get_by_conversation(
        self, conv_id: uuid.UUID, limit: int = 100
    ) -> Sequence[Message]:
        result = await self.db.execute(
            select(Message)
            .options(selectinload(Message.feedback))
            .where(Message.conversation_id == conv_id)
            .order_by(Message.created_at)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_recent(
        self, conv_id: uuid.UUID, limit: int = 20
    ) -> Sequence[Message]:
        result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conv_id)
            .order_by(desc(Message.created_at))
            .limit(limit)
        )
        return list(reversed(result.scalars().all()))

    async def count_all(self) -> int:
        result = await self.db.execute(select(func.count(Message.id)))
        return result.scalar() or 0

    async def count_by_date_range(self, start: datetime, end: datetime) -> List[Dict]:
        result = await self.db.execute(
            select(
                cast(Message.created_at, Date).label("date"),
                func.count(Message.id).label("count"),
            )
            .where(Message.created_at.between(start, end))
            .group_by(cast(Message.created_at, Date))
            .order_by(cast(Message.created_at, Date))
        )
        return [{"date": str(row.date), "count": row.count} for row in result.all()]

    async def avg_response_time(self) -> float:
        result = await self.db.execute(
            select(func.avg(Message.response_time_ms)).where(
                Message.role == "assistant", Message.response_time_ms.isnot(None)
            )
        )
        return round(result.scalar() or 0, 1)

    async def sentiment_distribution(self) -> List[Dict]:
        result = await self.db.execute(
            select(
                Message.sentiment,
                func.count(Message.id).label("count"),
            )
            .where(Message.sentiment.isnot(None))
            .group_by(Message.sentiment)
        )
        return [{"label": row.sentiment, "count": row.count} for row in result.all()]

    async def intent_distribution(self) -> List[Dict]:
        result = await self.db.execute(
            select(
                Message.intent,
                func.count(Message.id).label("count"),
            )
            .where(Message.intent.isnot(None))
            .group_by(Message.intent)
            .order_by(desc(func.count(Message.id)))
            .limit(15)
        )
        return [{"intent": row.intent, "count": row.count} for row in result.all()]

    async def emotion_distribution(self) -> List[Dict]:
        result = await self.db.execute(
            select(
                Message.emotion,
                func.count(Message.id).label("count"),
            )
            .where(Message.emotion.isnot(None))
            .group_by(Message.emotion)
        )
        return [{"emotion": row.emotion, "count": row.count} for row in result.all()]

    async def response_time_series(self, start: datetime, end: datetime) -> List[Dict]:
        result = await self.db.execute(
            select(
                cast(Message.created_at, Date).label("date"),
                func.avg(Message.response_time_ms).label("avg_ms"),
            )
            .where(
                Message.role == "assistant",
                Message.response_time_ms.isnot(None),
                Message.created_at.between(start, end),
            )
            .group_by(cast(Message.created_at, Date))
            .order_by(cast(Message.created_at, Date))
        )
        return [{"date": str(row.date), "avg_ms": round(row.avg_ms, 1)} for row in result.all()]

    async def recent_activity(self, limit: int = 20) -> List[Dict]:
        result = await self.db.execute(
            select(Message)
            .where(Message.role == "user")
            .order_by(desc(Message.created_at))
            .limit(limit)
        )
        messages = result.scalars().all()
        return [
            {
                "timestamp": msg.created_at.isoformat() if msg.created_at else None,
                "conversation_id": str(msg.conversation_id),
                "message_preview": msg.content[:80] if msg.content else "",
                "intent": msg.intent,
                "sentiment": msg.sentiment,
                "response_time_ms": msg.response_time_ms,
                "is_error": msg.is_error,
            }
            for msg in messages
        ]

    async def success_failure_counts(self) -> Dict[str, int]:
        total = await self.db.execute(
            select(func.count(Message.id)).where(Message.role == "assistant")
        )
        errors = await self.db.execute(
            select(func.count(Message.id)).where(
                Message.role == "assistant", Message.is_error == True
            )
        )
        total_count = total.scalar() or 0
        error_count = errors.scalar() or 0
        return {"success": total_count - error_count, "failure": error_count}

    async def sentiment_trend(self, start: datetime, end: datetime) -> List[Dict]:
        result = await self.db.execute(
            select(
                cast(Message.created_at, Date).label("date"),
                Message.sentiment,
                func.count(Message.id).label("count"),
            )
            .where(
                Message.sentiment.isnot(None),
                Message.created_at.between(start, end),
            )
            .group_by(cast(Message.created_at, Date), Message.sentiment)
            .order_by(cast(Message.created_at, Date))
        )
        return [
            {"date": str(row.date), "sentiment": row.sentiment, "count": row.count}
            for row in result.all()
        ]


# ── Feedback Repository ──────────────────────────────────────────────────────

class FeedbackRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, message_id: uuid.UUID, rating: int, comment: str = "") -> Feedback:
        fb = Feedback(message_id=message_id, rating=rating, comment=comment)
        self.db.add(fb)
        await self.db.flush()
        return fb

    async def avg_rating(self) -> float:
        result = await self.db.execute(select(func.avg(Feedback.rating)))
        return round(result.scalar() or 0, 2)


# ── UserPreferences Repository ───────────────────────────────────────────────

class UserPreferencesRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create(self, session_id: str) -> UserPreferences:
        result = await self.db.execute(
            select(UserPreferences).where(UserPreferences.session_id == session_id)
        )
        prefs = result.scalar_one_or_none()
        if not prefs:
            prefs = UserPreferences(session_id=session_id)
            self.db.add(prefs)
            await self.db.flush()
        return prefs

    async def update(self, session_id: str, data: Dict[str, Any]) -> UserPreferences:
        prefs = await self.get_or_create(session_id)
        for key, value in data.items():
            if hasattr(prefs, key) and key not in ("id", "session_id", "created_at"):
                setattr(prefs, key, value)
        await self.db.flush()
        return prefs


# ── ConversationSummary Repository ───────────────────────────────────────────

class ConversationSummaryRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_none(self, conv_id: uuid.UUID) -> Optional[ConversationSummary]:
        result = await self.db.execute(
            select(ConversationSummary).where(
                ConversationSummary.conversation_id == conv_id
            )
        )
        return result.scalar_one_or_none()

    async def upsert(self, conv_id: uuid.UUID, summary: str, msg_count: int) -> ConversationSummary:
        existing = await self.get_or_none(conv_id)
        if existing:
            existing.summary = summary
            existing.message_count_at_summary = msg_count
            await self.db.flush()
            return existing
        cs = ConversationSummary(
            conversation_id=conv_id,
            summary=summary,
            message_count_at_summary=msg_count,
        )
        self.db.add(cs)
        await self.db.flush()
        return cs


# ── Knowledge Repository (pgvector) ─────────────────────────────────────────

class KnowledgeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_document_by_title(self, title: str) -> Optional[KnowledgeDocument]:
        result = await self.db.execute(
            select(KnowledgeDocument).where(KnowledgeDocument.title == title)
        )
        return result.scalar_one_or_none()

    async def list_documents(self) -> Sequence[KnowledgeDocument]:
        result = await self.db.execute(
            select(KnowledgeDocument).order_by(desc(KnowledgeDocument.created_at))
        )
        return result.scalars().all()

    async def delete_document(self, title: str) -> bool:
        doc = await self.get_document_by_title(title)
        if not doc:
            return False
        await self.db.delete(doc)
        await self.db.flush()
        return True

    async def save_document(
        self,
        title: str,
        source: str,
        category: str,
        content: str,
        chunks_data: List[Dict[str, Any]],
    ) -> KnowledgeDocument:
        existing = await self.get_document_by_title(title)
        if existing:
            await self.db.delete(existing)
            await self.db.flush()

        doc = KnowledgeDocument(
            title=title,
            source=source,
            category=category,
            chunk_count=len(chunks_data),
            character_count=len(content),
        )
        self.db.add(doc)
        await self.db.flush()

        for c in chunks_data:
            chunk = KnowledgeChunk(
                document_id=doc.id,
                chunk_index=c["chunk_index"],
                content=c["content"],
                section=c.get("section", ""),
                embedding=c.get("embedding"),
            )
            self.db.add(chunk)

        await self.db.flush()
        return doc

    async def search_chunks(self, query_vector: List[float], top_k: int = 3) -> List[Dict[str, Any]]:
        # 1. Try pgvector native cosine distance operator <=>
        try:
            stmt = (
                select(
                    KnowledgeChunk.content,
                    KnowledgeChunk.section,
                    KnowledgeDocument.title,
                    KnowledgeDocument.source,
                    KnowledgeChunk.embedding.cosine_distance(query_vector).label("distance"),
                )
                .join(KnowledgeDocument, KnowledgeChunk.document_id == KnowledgeDocument.id)
                .order_by("distance")
                .limit(top_k)
            )
            result = await self.db.execute(stmt)
            rows = result.all()
            output = []
            for row in rows:
                dist = row.distance if row.distance is not None else 1.0
                score = max(0.0, 1.0 - float(dist))
                if score >= 0.25:
                    output.append({
                        "content": row.content,
                        "section": row.section or "",
                        "title": row.title,
                        "source": row.source or "",
                        "score": round(score, 3),
                    })
            return output
        except Exception:
            # 2. Resilient Python cosine fallback for non-pgvector / SQLite test environments
            stmt = (
                select(KnowledgeChunk, KnowledgeDocument.title, KnowledgeDocument.source)
                .join(KnowledgeDocument, KnowledgeChunk.document_id == KnowledgeDocument.id)
            )
            result = await self.db.execute(stmt)
            all_chunks = result.all()
            scored = []
            for chunk_obj, title, source in all_chunks:
                emb = chunk_obj.embedding
                if isinstance(emb, (list, tuple)) and len(emb) == len(query_vector):
                    dot = sum(a * b for a, b in zip(query_vector, emb))
                    norm_q = math.sqrt(sum(a * a for a in query_vector)) or 1.0
                    norm_e = math.sqrt(sum(b * b for b in emb)) or 1.0
                    sim = dot / (norm_q * norm_e)
                    scored.append((sim, chunk_obj, title, source))

            scored.sort(key=lambda x: x[0], reverse=True)
            output = []
            for sim, chunk_obj, title, source in scored[:top_k]:
                if sim >= 0.25:
                    output.append({
                        "content": chunk_obj.content,
                        "section": chunk_obj.section or "",
                        "title": title,
                        "source": source or "",
                        "score": round(float(sim), 3),
                    })
            return output
