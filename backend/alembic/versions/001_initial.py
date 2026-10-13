"""Initial schema

Revision ID: 001_initial
Revises:
Create Date: 2026-10-07
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Conversations
    op.create_table(
        "conversations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("session_id", sa.String(64), nullable=False, index=True),
        sa.Column("title", sa.String(256), default="New Conversation"),
        sa.Column("language", sa.String(20), default="en"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("is_archived", sa.Boolean, default=False),
    )

    # Messages
    op.create_table(
        "messages",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("conversation_id", UUID(as_uuid=True), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("intent", sa.String(64)),
        sa.Column("intent_confidence", sa.Float),
        sa.Column("sentiment", sa.String(20)),
        sa.Column("sentiment_score", sa.Float),
        sa.Column("emotion", sa.String(20)),
        sa.Column("emotion_score", sa.Float),
        sa.Column("entities", JSONB, default=list),
        sa.Column("response_time_ms", sa.Integer),
        sa.Column("token_count", sa.Integer),
        sa.Column("model_used", sa.String(64)),
        sa.Column("tools_used", JSONB, default=list),
        sa.Column("sources", JSONB, default=list),
        sa.Column("is_fallback", sa.Boolean, default=False),
        sa.Column("is_error", sa.Boolean, default=False),
        sa.Column("error_code", sa.String(32)),
        sa.Column("metadata", JSONB, default=dict),
    )

    # Feedback
    op.create_table(
        "feedback",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("message_id", UUID(as_uuid=True), sa.ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("rating", sa.Integer, nullable=False),
        sa.Column("comment", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # User Preferences
    op.create_table(
        "user_preferences",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("session_id", sa.String(64), nullable=False, unique=True, index=True),
        sa.Column("theme", sa.String(20), default="system"),
        sa.Column("language", sa.String(20), default="en"),
        sa.Column("temperature", sa.Float, default=0.7),
        sa.Column("max_tokens", sa.Integer, default=2048),
        sa.Column("timestamps_enabled", sa.Boolean, default=True),
        sa.Column("sentiment_enabled", sa.Boolean, default=True),
        sa.Column("compact_mode", sa.Boolean, default=False),
        sa.Column("auto_scroll", sa.Boolean, default=True),
        sa.Column("suggestions_enabled", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Conversation Summaries
    op.create_table(
        "conversation_summaries",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("conversation_id", UUID(as_uuid=True), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("summary", sa.Text, nullable=False),
        sa.Column("message_count_at_summary", sa.Integer, default=0),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("conversation_summaries")
    op.drop_table("user_preferences")
    op.drop_table("feedback")
    op.drop_table("messages")
    op.drop_table("conversations")
