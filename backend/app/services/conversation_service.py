"""
Conversation service — CRUD operations for conversations.
"""

from __future__ import annotations

import re
import uuid
import json
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories import ConversationRepository, MessageRepository
from app.schemas.schemas import (
    ConversationDetail,
    ConversationOut,
    MessageOut,
    SentimentResult,
    EmotionResult,
    EntityResult,
    SourceResult,
)

logger = logging.getLogger(__name__)


class ConversationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.conv_repo = ConversationRepository(db)
        self.msg_repo = MessageRepository(db)

    async def list_conversations(self, session_id: str) -> List[ConversationOut]:
        conversations = await self.conv_repo.list_by_session(session_id)
        results = []
        for conv in conversations:
            all_msgs = await self.msg_repo.get_by_conversation(conv.id, limit=20)
            msg_count = len(all_msgs)

            # Clean any legacy unparsed title payloads
            title = conv.title or "New Conversation"
            if title.strip().startswith("{"):
                try:
                    payload = json.loads(title)
                    title = payload.get("title") or payload.get("reply", "Conversation")
                    if len(title) > 50:
                        title = title[:47] + "..."
                    await self.conv_repo.update_title(conv.id, title)
                except Exception:
                    title = "Conversation"

            # Detect conversation category / what it is for (ONLY check user queries)
            category = "General AI"
            for m in all_msgs:
                if m.role != "user":
                    continue
                meta = m.metadata_ or {}
                content_lower = m.content.lower()
                if meta.get("audio_url"):
                    category = "Voice Query"
                    break
                elif meta.get("image_url"):
                    category = "Vision Analysis"
                    break
                elif "#rag" in content_lower or m.intent in ("rag_search", "document_query"):
                    category = "RAG Docs"
                    break
                elif m.intent == "faq":
                    category = "FAQ Help"
                    break
                elif any(kw in content_lower for kw in ("python", "code", "bug", "function", "docker", "class", "react", "sql", "api")):
                    category = "Code & Tech"
                    break

            results.append(ConversationOut(
                id=str(conv.id),
                title=title,
                language=conv.language or "en",
                created_at=conv.created_at.isoformat() if conv.created_at else None,
                updated_at=conv.updated_at.isoformat() if conv.updated_at else None,
                message_count=msg_count,
                category=category,
            ))
        return results

    async def get_conversation(self, conv_id: str) -> Optional[ConversationDetail]:
        try:
            cid = uuid.UUID(conv_id)
        except ValueError:
            return None

        conv = await self.conv_repo.get_by_id(cid)
        if not conv:
            return None

        messages = await self.msg_repo.get_by_conversation(cid)
        msg_list = []
        category = "General AI"

        for m in messages:
            if m.role == "user":
                meta = m.metadata_ or {}
                content_lower = m.content.lower()
                if meta.get("audio_url"):
                    category = "Voice Query"
                elif meta.get("image_url"):
                    category = "Vision Analysis"
                elif "#rag" in content_lower or m.intent in ("rag_search", "document_query"):
                    category = "RAG Docs"
                elif m.intent == "faq" and category == "General AI":
                    category = "FAQ Help"
                elif any(kw in content_lower for kw in ("python", "code", "bug", "function", "docker", "class")):
                    if category == "General AI":
                        category = "Code & Tech"

            sentiment = None
            if m.sentiment:
                sentiment = SentimentResult(label=m.sentiment, score=m.sentiment_score or 0.5)
            emotion = None
            if m.emotion:
                emotion = EmotionResult(label=m.emotion, score=m.emotion_score or 0.5)

            entities = []
            if m.entities:
                for e in m.entities:
                    if isinstance(e, dict):
                        entities.append(EntityResult(text=e.get("text", ""), label=e.get("label", "")))

            sources = []
            if m.sources:
                for s in m.sources:
                    if isinstance(s, dict):
                        sources.append(SourceResult(title=s.get("title", ""), section=s.get("section", "")))

            has_fb = False
            fb_rating = None
            try:
                if "feedback" in m.__dict__ and m.feedback is not None:
                    has_fb = True
                    fb_rating = getattr(m.feedback, "rating", None)
            except Exception:
                has_fb = False

            meta = m.metadata_ or {}
            msg_list.append(MessageOut(
                id=str(m.id),
                role=m.role,
                content=m.content,
                created_at=m.created_at.isoformat() if m.created_at else None,
                intent=m.intent,
                intent_confidence=m.intent_confidence,
                sentiment=sentiment,
                emotion=emotion,
                entities=entities,
                sources=sources,
                response_time_ms=m.response_time_ms,
                is_fallback=m.is_fallback or False,
                is_error=m.is_error or False,
                tools_used=m.tools_used or [],
                has_feedback=has_fb,
                feedback_rating=fb_rating,
                image_url=meta.get("image_url"),
                audio_url=meta.get("audio_url"),
                file_name=meta.get("file_name"),
            ))

        # Sanitize title if needed
        title = conv.title or "New Conversation"
        if title.strip().startswith("{") or '"intent"' in title:
            user_msg = next((m for m in messages if m.role == "user"), None)
            if user_msg and user_msg.content:
                clean = re.sub(r'#\w+\s*', '', user_msg.content).strip()
                clean = re.sub(r'["\'{}]', '', clean).strip()
                words = clean.split()
                title = (" ".join(words[:5]) + ("..." if len(words) > 5 else "")).capitalize() if words else "Conversation"
            else:
                title = "Conversation"

        return ConversationDetail(
            conversation=ConversationOut(
                id=str(conv.id),
                title=title,
                language=conv.language or "en",
                created_at=conv.created_at.isoformat() if conv.created_at else None,
                updated_at=conv.updated_at.isoformat() if conv.updated_at else None,
                message_count=len(msg_list),
                category=category,
            ),
            messages=msg_list,
        )

    async def delete_conversation(self, conv_id: str) -> bool:
        try:
            cid = uuid.UUID(conv_id)
        except ValueError:
            return False
        return await self.conv_repo.delete_conversation(cid)

    async def export_conversation(self, conv_id: str, format: str = "json") -> Optional[str]:
        detail = await self.get_conversation(conv_id)
        if not detail:
            return None

        if format == "json":
            return json.dumps(detail.model_dump(), indent=2, default=str)
        elif format == "txt":
            lines = [f"Conversation: {detail.conversation.title}\n"]
            for msg in detail.messages:
                role = "You" if msg.role == "user" else "AI"
                ts = msg.created_at or ""
                lines.append(f"[{ts}] {role}: {msg.content}\n")
            return "\n".join(lines)
        elif format == "md":
            lines = [f"# {detail.conversation.title}\n"]
            for msg in detail.messages:
                role = "**You**" if msg.role == "user" else "**AI**"
                lines.append(f"{role}: {msg.content}\n")
            return "\n".join(lines)
        return None
