"""Add knowledge_documents and knowledge_chunks for pgvector RAG

Revision ID: 002_pgvector_rag
Revises: 001_initial
Create Date: 2026-10-12
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

try:
    from pgvector.sqlalchemy import Vector
    PGVECTOR_TYPE = Vector(384)
except Exception:
    from sqlalchemy.dialects.postgresql import JSONB
    PGVECTOR_TYPE = JSONB

revision: str = "002_pgvector_rag"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ensure pgvector extension is enabled
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # Knowledge Documents
    op.create_table(
        "knowledge_documents",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(256), nullable=False, unique=True, index=True),
        sa.Column("source", sa.String(256), default=""),
        sa.Column("category", sa.String(64), default="general"),
        sa.Column("chunk_count", sa.Integer, default=0),
        sa.Column("character_count", sa.Integer, default=0),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Knowledge Chunks with 384-dimensional pgvector embedding
    op.create_table(
        "knowledge_chunks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("document_id", UUID(as_uuid=True), sa.ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("section", sa.String(256), default=""),
        sa.Column("embedding", PGVECTOR_TYPE),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("knowledge_chunks")
    op.drop_table("knowledge_documents")
