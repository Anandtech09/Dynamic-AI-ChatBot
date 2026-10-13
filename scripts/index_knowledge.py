#!/usr/bin/env python3
"""
Knowledge Base Indexing Script

Indexes all documents in data/knowledge/ into the PostgreSQL pgvector store.

Usage:
    python scripts/index_knowledge.py
"""

import asyncio
import os
import sys

# Ensure UTF-8 stdout encoding on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add directories to path so app modules can be imported in both container and host
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from backend.app.services.rag_service import RAGService  # noqa: E402
from backend.app.core.config import get_settings  # noqa: E402
from backend.app.db.database import init_db  # noqa: E402


async def main():
    settings = get_settings()
    await init_db()
    
    # Determine knowledge directory
    knowledge_dir = os.path.join(
        os.path.dirname(__file__), "..", "data", "knowledge"
    )
    knowledge_dir = os.path.abspath(knowledge_dir)
    
    print(f"📚 Knowledge Base Indexing (PostgreSQL pgvector)")
    print(f"   Directory: {knowledge_dir}")
    print(f"   Vector Engine: pgvector (vector(384) cosine distance)")
    print()
    
    if not os.path.exists(knowledge_dir):
        print(f"❌ Knowledge directory not found: {knowledge_dir}")
        sys.exit(1)
    
    # List files
    files = [f for f in os.listdir(knowledge_dir) if f.endswith(('.md', '.txt'))]
    if not files:
        print("⚠ No .md or .txt files found in knowledge directory")
        sys.exit(0)
    
    print(f"   Found {len(files)} document(s):")
    for f in files:
        print(f"   • {f}")
    print()
    
    # Index
    rag = RAGService()
    total = await rag.index_directory(knowledge_dir)
    
    print(f"\n✅ Indexing complete!")
    print(f"   Total chunks indexed: {total}")
    
    # Verify
    docs = await rag.get_document_list()
    print(f"   Documents in store: {len(docs)}")
    for doc in docs:
        print(f"   • {doc['title']} ({doc['chunk_count']} chunks)")


if __name__ == "__main__":
    asyncio.run(main())
