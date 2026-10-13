"""
Chat service — coordinates conversation management, AI orchestration, and persistence.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, AsyncIterator, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.orchestrator import AIOrchestrator, OrchestratorResult
from app.core.config import get_settings
from app.core.security import detect_prompt_injection, sanitize_input, validate_message_length
from app.db.repositories import (
    ConversationRepository,
    ConversationSummaryRepository,
    MessageRepository,
)
from app.schemas.schemas import (
    ChatRequest,
    ChatResponseData,
    EmotionResult,
    EntityResult,
    SentimentResult,
    SourceResult,
)

logger = logging.getLogger(__name__)


class ChatService:
    """Handles the full chat lifecycle."""

    def __init__(self, db: AsyncSession, orchestrator: AIOrchestrator):
        self.db = db
        self.orchestrator = orchestrator
        self.conv_repo = ConversationRepository(db)
        self.msg_repo = MessageRepository(db)
        self.summary_repo = ConversationSummaryRepository(db)
        self.settings = get_settings()

    async def handle_message(self, request: ChatRequest) -> ChatResponseData:
        """Process a user chat message through the full pipeline."""
        # 1. Validate input
        message = sanitize_input(request.message)
        if not validate_message_length(message):
            raise ValueError("Message is empty or exceeds maximum length")

        if detect_prompt_injection(message):
            logger.warning("Prompt injection attempt detected")
            # Don't block — just note it; the system prompt defences handle the rest

        # 2. Get or create conversation
        conv_id = None
        if request.conversation_id:
            try:
                conv_id = uuid.UUID(request.conversation_id)
            except ValueError:
                pass

        if conv_id:
            conversation = await self.conv_repo.get_by_id(conv_id)
            if not conversation:
                conversation = await self.conv_repo.create(
                    session_id=request.session_id, language=request.language
                )
        else:
            conversation = await self.conv_repo.create(
                session_id=request.session_id, language=request.language
            )

        # 3. Store user message with image/audio attachments in metadata
        user_meta = {}
        if request.image_data:
            user_meta["image_url"] = request.image_data
        if request.audio_data:
            user_meta["audio_url"] = request.audio_data
        if request.file_name:
            user_meta["file_name"] = request.file_name

        user_msg = await self.msg_repo.create(
            conversation_id=conversation.id,
            role="user",
            content=message,
            metadata_=user_meta,
        )

        # 4. Load conversation history
        recent_messages = await self.msg_repo.get_recent(
            conversation.id, limit=self.settings.max_context_messages
        )
        history = [
            {"role": m.role, "content": m.content}
            for m in recent_messages
            if m.id != user_msg.id  # Don't include the just-added user message
        ]

        # 5. Load conversation summary if exists
        summary_text = ""
        summary_record = await self.summary_repo.get_or_none(conversation.id)
        if summary_record:
            summary_text = summary_record.summary

        # 6. Run the orchestrator
        temperature = request.temperature or self.settings.default_temperature
        max_tokens = request.max_tokens or self.settings.max_response_tokens
        result = await self.orchestrator.process_message(
            user_message=message,
            conversation_history=history,
            conversation_summary=summary_text,
            language=request.language,
            temperature=temperature,
            max_tokens=max_tokens,
            image_data=request.image_data,
        )

        # 7. Store assistant message with metadata
        assistant_msg = await self.msg_repo.create(
            conversation_id=conversation.id,
            role="assistant",
            content=result.reply,
            intent=result.intent,
            intent_confidence=result.intent_confidence,
            sentiment=result.sentiment,
            sentiment_score=result.sentiment_score,
            emotion=result.emotion,
            emotion_score=result.emotion_score,
            entities=result.entities,
            response_time_ms=result.response_time_ms,
            token_count=result.token_count,
            model_used=result.model_used,
            tools_used=result.tools_used,
            sources=[s if isinstance(s, dict) else {} for s in result.sources],
            is_fallback=result.is_fallback,
            is_error=result.is_error,
            error_code=result.error_code,
        )

        # Update the user message with NLP metadata too
        user_msg.intent = result.intent
        user_msg.intent_confidence = result.intent_confidence
        user_msg.sentiment = result.sentiment
        user_msg.sentiment_score = result.sentiment_score
        user_msg.emotion = result.emotion
        user_msg.emotion_score = result.emotion_score
        user_msg.entities = result.entities

        # 8. Generate title after first message
        all_msgs = await self.msg_repo.get_by_conversation(conversation.id, limit=5)
        if len(all_msgs) <= 2 and conversation.title == "New Conversation":
            try:
                title = await self.orchestrator.generate_title(message)
                await self.conv_repo.update_title(conversation.id, title)
            except Exception as e:
                logger.warning("Title generation failed: %s", e)

        # 9. Generate summary if conversation is getting long
        all_count = len(await self.msg_repo.get_by_conversation(conversation.id, limit=200))
        should_summarize = all_count > 10 and (
            not summary_record or (all_count - (summary_record.message_count_at_summary or 0)) > 8
        )
        if should_summarize and not self.orchestrator.is_demo:
            try:
                conv_text = "\n".join(
                    [f"{m.role}: {m.content[:200]}" for m in recent_messages[-15:]]
                )
                new_summary = await self.orchestrator.generate_summary(conv_text)
                if new_summary:
                    await self.summary_repo.upsert(conversation.id, new_summary, all_count)
            except Exception as e:
                logger.warning("Summary generation failed: %s", e)

        # 10. Build response
        return ChatResponseData(
            conversation_id=str(conversation.id),
            message_id=str(assistant_msg.id),
            reply=result.reply,
            intent=result.intent,
            intent_confidence=result.intent_confidence,
            sentiment=SentimentResult(
                label=result.sentiment or "neutral",
                score=result.sentiment_score or 0.5,
            ),
            emotion=EmotionResult(
                label=result.emotion or "neutral",
                score=result.emotion_score or 0.5,
            ),
            entities=[
                EntityResult(text=e.get("text", ""), label=e.get("label", ""))
                for e in result.entities
            ],
            sources=[
                SourceResult(
                    title=s.get("title", ""),
                    section=s.get("section", ""),
                    score=s.get("score"),
                )
                for s in result.sources
            ],
            suggestions=result.suggestions,
            response_time_ms=result.response_time_ms,
            is_demo=result.is_demo,
            is_rag=result.is_rag,
            is_faq=result.is_faq,
            image_url=request.image_data,
        )

    async def stream_message(
        self, request: ChatRequest
    ) -> AsyncIterator[str]:
        """Stream response tokens via SSE."""
        message = sanitize_input(request.message)

        # Get or create conversation
        conv_id = None
        if request.conversation_id:
            try:
                conv_id = uuid.UUID(request.conversation_id)
            except ValueError:
                pass

        if conv_id:
            conversation = await self.conv_repo.get_by_id(conv_id)
            if not conversation:
                conversation = await self.conv_repo.create(
                    session_id=request.session_id, language=request.language
                )
        else:
            conversation = await self.conv_repo.create(
                session_id=request.session_id, language=request.language
            )

        # Store user message
        await self.msg_repo.create(
            conversation_id=conversation.id,
            role="user",
            content=message,
        )

        # Load history
        recent = await self.msg_repo.get_recent(conversation.id, limit=self.settings.max_context_messages)
        history = [{"role": m.role, "content": m.content} for m in recent[:-1]]

        # Load summary
        summary_text = ""
        summary_record = await self.summary_repo.get_or_none(conversation.id)
        if summary_record:
            summary_text = summary_record.summary

        # Stream
        full_response = ""
        async for chunk in self.orchestrator.process_message_stream(
            user_message=message,
            conversation_history=history,
            conversation_summary=summary_text,
            language=request.language,
        ):
            full_response += chunk
            yield chunk

        # Store the complete response
        await self.msg_repo.create(
            conversation_id=conversation.id,
            role="assistant",
            content=full_response,
        )
