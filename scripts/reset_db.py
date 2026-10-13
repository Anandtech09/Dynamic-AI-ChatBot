#!/usr/bin/env python3
"""
Database Reset & Clean Script

Wipes all data across all tables in PostgreSQL (or Neon DB) for a clean slate.

Usage:
    python scripts/reset_db.py
    python scripts/reset_db.py --drop    # Drop and recreate all tables
"""

from __future__ import annotations

import asyncio
import os
import sys

# Ensure UTF-8 stdout encoding on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add paths so app modules can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from sqlalchemy import text  # noqa: E402
from app.core.config import get_settings  # noqa: E402
from app.db.database import Base, engine, init_db  # noqa: E402


async def reset_database(drop_tables: bool = False) -> None:
    settings = get_settings()
    db_url = settings.async_database_url

    print("=" * 60)
    print("Database Reset Utility")
    print(f"Target URL: {db_url.split('@')[-1] if '@' in db_url else db_url}")
    print("=" * 60)

    tables = [
        "messages",
        "feedback",
        "conversation_summaries",
        "user_preferences",
        "conversations",
        "knowledge_chunks",
        "knowledge_documents",
    ]

    async with engine.begin() as conn:
        if drop_tables:
            print("\nDropping all existing tables...")
            await conn.run_sync(Base.metadata.drop_all)
            print("Recreating fresh tables and pgvector extension...")
            await init_db()
            print("All tables recreated cleanly.")
        else:
            print("\nTruncating all tables (wiping all rows)...")
            for tbl in tables:
                try:
                    await conn.execute(text(f"TRUNCATE TABLE {tbl} CASCADE;"))
                    print(f"  [CLEARED] {tbl}")
                except Exception as e:
                    print(f"  [SKIPPED/EMPTY] {tbl} ({e})")

    print("\nDatabase reset complete. All data cleared successfully.")
    print("=" * 60)


def main() -> None:
    drop_flag = "--drop" in sys.argv
    asyncio.run(reset_database(drop_tables=drop_flag))


if __name__ == "__main__":
    main()
