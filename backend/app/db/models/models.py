"""
SQLAlchemy ORM models for the chatbot application.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.database import Base


def gen_uuid():
    return uuid.uuid4()


class Conversation(Base):
    """A conversation session."""

    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    session_id = Column(String(64), nullable=False, index=True)
    title = Column(String(256), default="New Conversation")
    language = Column(String(20), default="en")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    is_archived = Column(Boolean, default=False)

    messages = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan",
        order_by="Message.created_at",
    )
    summary = relationship(
        "ConversationSummary", back_populates="conversation", uselist=False,
        cascade="all, delete-orphan",
    )


class Message(Base):
    """A single message in a conversation."""

    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    conversation_id = Column(
        UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role = Column(String(20), nullable=False)  # "user" | "assistant" | "system"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # NLP metadata
    intent = Column(String(64))
    intent_confidence = Column(Float)
    sentiment = Column(String(20))
    sentiment_score = Column(Float)
    emotion = Column(String(20))
    emotion_score = Column(Float)
    entities = Column(JSONB, default=list)

    # Performance
    response_time_ms = Column(Integer)
    token_count = Column(Integer)
    model_used = Column(String(64))

    # Tools / RAG
    tools_used = Column(JSONB, default=list)
    sources = Column(JSONB, default=list)

    # Status
    is_fallback = Column(Boolean, default=False)
    is_error = Column(Boolean, default=False)
    error_code = Column(String(32))

    # Extra metadata
    metadata_ = Column("metadata", JSONB, default=dict)

    conversation = relationship("Conversation", back_populates="messages")
    feedback = relationship(
        "Feedback", back_populates="message", uselist=False, cascade="all, delete-orphan"
    )


class Feedback(Base):
    """User feedback on a specific AI message."""

    __tablename__ = "feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    message_id = Column(
        UUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    rating = Column(Integer, nullable=False)  # 1 (thumbs down) or 5 (thumbs up)
    comment = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    message = relationship("Message", back_populates="feedback")


class UserPreferences(Base):
    """Per-session user preferences."""

    __tablename__ = "user_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    session_id = Column(String(64), nullable=False, unique=True, index=True)
    theme = Column(String(20), default="system")
    language = Column(String(20), default="en")
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=2048)
    timestamps_enabled = Column(Boolean, default=True)
    sentiment_enabled = Column(Boolean, default=True)
    compact_mode = Column(Boolean, default=False)
    auto_scroll = Column(Boolean, default=True)
    suggestions_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ConversationSummary(Base):
    """Compressed summary of a long conversation for context-window management."""

    __tablename__ = "conversation_summaries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    conversation_id = Column(
        UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False, unique=True,
    )
    summary = Column(Text, nullable=False)
    message_count_at_summary = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    conversation = relationship("Conversation", back_populates="summary")


try:
    from pgvector.sqlalchemy import Vector
    PGVECTOR_TYPE = Vector(384)
except Exception:
    PGVECTOR_TYPE = JSONB


class KnowledgeDocument(Base):
    """Document indexed in the RAG knowledge base."""

    __tablename__ = "knowledge_documents"
    __mapper_args__ = {"confirm_deleted_rows": False}

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    title = Column(String(256), nullable=False, unique=True, index=True)
    source = Column(String(256), default="")
    category = Column(String(64), default="general")
    chunk_count = Column(Integer, default=0)
    character_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    chunks = relationship(
        "KnowledgeChunk",
        back_populates="document",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="KnowledgeChunk.chunk_index",
    )


class KnowledgeChunk(Base):
    """Semantic text chunk with 384-dim dense vector embedding in PostgreSQL."""

    __tablename__ = "knowledge_chunks"
    __mapper_args__ = {"confirm_deleted_rows": False}

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    section = Column(String(256), default="")
    embedding = Column(PGVECTOR_TYPE)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    document = relationship("KnowledgeDocument", back_populates="chunks")
