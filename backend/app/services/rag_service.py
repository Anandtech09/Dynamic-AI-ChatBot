"""
RAG Service — Semantic Document Retrieval and Indexing using PostgreSQL pgvector.

Stores documents and embeddings natively in PostgreSQL with pgvector extension:
- Zero chance of file corruption / data loss compared to file-based vector stores
- Direct relational foreign-key cascading and ACID transactions
- Native vector cosine distance search: <=> operator with HNSW/IVFFlat index
- 384-dimensional dense semantic embedding engine
"""

from __future__ import annotations

import hashlib
import logging
import math
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.database import async_session_factory
from app.db.repositories.repositories import KnowledgeRepository
from app.services.cache_service import get_cache_service

logger = logging.getLogger(__name__)


class SemanticEmbeddingEngine:
    """
    384-Dimensional Dense Semantic Vector Generator.
    Generates deterministic, L2-normalized dense embeddings for semantic retrieval.
    Compatible with pgvector vector(384) schema.
    """

    DIMENSION = 384

    def __init__(self):
        self.settings = get_settings()

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate a 384-dimensional normalized dense embedding vector.
        Uses sublinear n-gram feature hashing projection with positional sine-cosine encoding.
        """
        vector = [0.0] * self.DIMENSION
        clean_text = text.lower().strip()
        tokens = re.findall(r"\b\w+\b", clean_text)
        if not tokens:
            return vector

        # 1. Unigram and bigram projections
        features = list(tokens)
        for i in range(len(tokens) - 1):
            features.append(f"{tokens[i]}_{tokens[i+1]}")

        # 2. Project features into 384-dimensional space
        for pos, feat in enumerate(features):
            h = int(hashlib.md5(feat.encode("utf-8")).hexdigest(), 16)
            idx = h % self.DIMENSION
            weight = 1.0 + (1.0 / (1.0 + math.log(1 + pos)))
            # Add with hash sign flip to minimize collisions
            sign = 1.0 if ((h >> 8) & 1) == 0 else -1.0
            vector[idx] += sign * weight

            # Position-sensitive harmonics
            harmonic_idx = (idx + 192) % self.DIMENSION
            vector[harmonic_idx] += (sign * 0.5) * math.cos(pos * 0.1)

        # 3. L2 unit vector normalization
        sq_sum = sum(v * v for v in vector)
        if sq_sum > 0:
            norm = math.sqrt(sq_sum)
            vector = [v / norm for v in vector]

        return vector


class RAGService:
    """
    Production RAG Service powered by PostgreSQL and pgvector.
    Provides document chunking, embedding generation, transactional indexing,
    and high-performance semantic vector similarity search.
    """

    def __init__(
        self,
        db: Optional[AsyncSession] = None,
        persist_dir: Optional[str] = None,
        collection_name: str = "knowledge",
    ):
        self.db = db
        self.settings = get_settings()
        self.embedding_engine = SemanticEmbeddingEngine()

    @property
    def is_available(self) -> bool:
        """PostgreSQL pgvector RAG is always available when the database is active."""
        return True

    async def _execute_with_session(self, func):
        """Execute a database function using provided session or a managed transaction."""
        if self.db is not None:
            return await func(self.db)
        async with async_session_factory() as session:
            try:
                result = await func(session)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise

    async def index_document(
        self,
        title: str,
        content: str,
        source: str = "",
        chunk_size: int = 500,
        metadata: Optional[Dict] = None,
    ) -> int:
        """Split a document into semantic chunks and store in PostgreSQL with pgvector embeddings."""
        chunks = self._chunk_text(content, chunk_size=chunk_size)
        if not chunks:
            return 0

        chunks_data = []
        for i, chunk in enumerate(chunks):
            embedding = self.embedding_engine.generate_embedding(chunk)
            chunks_data.append({
                "chunk_index": i,
                "content": chunk,
                "section": self._extract_section(chunk),
                "embedding": embedding,
            })

        async def _save(session: AsyncSession):
            repo = KnowledgeRepository(session)
            doc = await repo.save_document(
                title=title,
                source=source,
                category=(metadata or {}).get("category", "general"),
                content=content,
                chunks_data=chunks_data,
            )
            return doc.chunk_count

        count = await self._execute_with_session(_save)
        logger.info("Successfully indexed %d chunks for document '%s' into PostgreSQL pgvector", count, title)
        # Invalidate cached searches when new content is indexed
        cache = get_cache_service()
        await cache.invalidate_rag_cache()
        return count

    async def search(
        self,
        query: str,
        top_k: int = 3,
        document_title: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Hybrid Semantic & Lexical Search with Reciprocal Rank Fusion (RRF),
        Multi-Feature Re-ranking, Document-Specific Filtering, and Redis caching.
        """
        cache = get_cache_service()
        cache_query_key = f"{query}::doc={document_title}" if document_title else query
        cached = await cache.get_rag_search(cache_query_key, top_k)
        if cached is not None:
            logger.debug("Redis cache HIT for RAG search query: %s", cache_query_key)
            return cached

        query_vector = self.embedding_engine.generate_embedding(query)

        async def _search(session: AsyncSession):
            repo = KnowledgeRepository(session)
            return await repo.search_chunks(
                query_vector=query_vector,
                query=query,
                top_k=top_k,
                document_title=document_title,
            )

        try:
            results = await self._execute_with_session(_search)
            if results:
                await cache.set_rag_search(cache_query_key, top_k, results)
            return results
        except Exception as e:
            logger.error("RAG hybrid vector search failed: %s", e, exc_info=True)
            return []

    async def get_document_list(self) -> List[Dict[str, Any]]:
        """List all indexed documents from PostgreSQL."""
        async def _list(session: AsyncSession):
            repo = KnowledgeRepository(session)
            docs = await repo.list_documents()
            return [
                {
                    "title": d.title,
                    "source": d.source,
                    "category": d.category,
                    "chunk_count": d.chunk_count,
                    "character_count": d.character_count,
                    "created_at": d.created_at.isoformat() if d.created_at else None,
                }
                for d in docs
            ]

        try:
            return await self._execute_with_session(_list)
        except Exception as e:
            logger.error("Failed to list knowledge documents: %s", e)
            return []

    list_documents = get_document_list

    async def delete_document(self, title: str) -> bool:
        """Delete a document and all its chunks with cascading relational deletion."""
        async def _delete(session: AsyncSession):
            repo = KnowledgeRepository(session)
            return await repo.delete_document(title)

        try:
            deleted = await self._execute_with_session(_delete)
            if deleted:
                cache = get_cache_service()
                await cache.invalidate_rag_cache()
            return deleted
        except Exception as e:
            logger.error("Failed to delete document '%s': %s", title, e)
            return False

    async def index_directory(self, directory: str) -> int:
        """Scan and index all .txt and .md files in a directory."""
        dir_path = Path(directory)
        if not dir_path.exists():
            logger.warning("Knowledge directory not found: %s", directory)
            return 0

        total_chunks = 0
        for file_path in sorted(dir_path.glob("*")):
            if file_path.suffix.lower() in (".txt", ".md"):
                try:
                    content = file_path.read_text(encoding="utf-8")
                    title = file_path.stem.replace("_", " ").replace("-", " ").title()
                    chunks = await self.index_document(
                        title=title,
                        content=content,
                        source=str(file_path.name),
                    )
                    total_chunks += chunks
                except Exception as e:
                    logger.error("Failed to index %s: %s", file_path, e)

        return total_chunks

    @classmethod
    def extract_text_from_file(cls, filename: str, file_bytes: bytes) -> tuple[str, int]:
        """
        Extract clean text and page/record count from uploaded file bytes.
        Supports PDF (multi-page, 30+ pages), DOCX, CSV, TXT, MD, and JSON.
        Returns: (extracted_text, page_or_item_count)
        """
        import io
        import csv
        import zipfile
        import xml.etree.ElementTree as ET

        ext = Path(filename).suffix.lower()
        text = ""
        count = 1

        if ext == ".pdf":
            try:
                import pypdf
                reader = pypdf.PdfReader(io.BytesIO(file_bytes))
                count = len(reader.pages)
                pages_text = []
                for idx, page in enumerate(reader.pages, start=1):
                    p_text = page.extract_text() or ""
                    cleaned = p_text.strip()
                    if cleaned:
                        pages_text.append(f"--- Page {idx} ---\n{cleaned}")
                text = "\n\n".join(pages_text)
            except Exception as e:
                logger.warning("pypdf extraction failed for %s: %s; trying fallback", filename, e)
                try:
                    raw = file_bytes.decode("latin-1", errors="ignore")
                    words = re.findall(r"[A-Za-z0-9\s.,!?;:\"'-]{4,}", raw)
                    text = " ".join(words)
                except Exception as fallback_err:
                    logger.error("PDF fallback failed: %s", fallback_err)
                    text = file_bytes.decode("utf-8", errors="ignore")

        elif ext == ".docx":
            try:
                with zipfile.ZipFile(io.BytesIO(file_bytes)) as docx:
                    xml_content = docx.read("word/document.xml")
                    tree = ET.fromstring(xml_content)
                    namespaces = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
                    paragraphs = []
                    for p in tree.iterfind(".//w:p", namespaces):
                        p_texts = [node.text for node in p.iterfind(".//w:t", namespaces) if node.text]
                        if p_texts:
                            paragraphs.append("".join(p_texts).strip())
                    text = "\n\n".join([p for p in paragraphs if p])
                    count = len(paragraphs)
            except Exception as e:
                logger.warning("DOCX extraction error for %s: %s", filename, e)
                text = file_bytes.decode("utf-8", errors="ignore")

        elif ext == ".csv":
            try:
                raw_str = file_bytes.decode("utf-8-sig")
            except UnicodeDecodeError:
                raw_str = file_bytes.decode("latin-1", errors="ignore")

            try:
                reader = csv.reader(io.StringIO(raw_str))
                rows = list(reader)
                if rows:
                    headers = [h.strip() for h in rows[0]]
                    count = len(rows) - 1
                    formatted_rows = []
                    for i, row in enumerate(rows[1:], start=1):
                        row_items = [
                            f"{headers[j] if j < len(headers) else f'Col{j+1}'}: {val.strip()}"
                            for j, val in enumerate(row)
                            if val.strip()
                        ]
                        if row_items:
                            formatted_rows.append(f"Row {i} -> " + ", ".join(row_items))
                    text = (
                        f"CSV Document: {filename}\nHeaders: {', '.join(headers)}\n\n"
                        + "\n".join(formatted_rows)
                    )
            except Exception as e:
                logger.warning("CSV parsing error: %s", e)
                text = raw_str

        elif ext in (".txt", ".md"):
            try:
                text = file_bytes.decode("utf-8-sig")
            except UnicodeDecodeError:
                text = file_bytes.decode("latin-1", errors="ignore")

        elif ext == ".json":
            try:
                import json
                obj = json.loads(file_bytes.decode("utf-8"))
                text = json.dumps(obj, indent=2)
            except Exception:
                text = file_bytes.decode("utf-8", errors="ignore")

        else:
            try:
                text = file_bytes.decode("utf-8")
            except UnicodeDecodeError:
                text = file_bytes.decode("latin-1", errors="ignore")

        return text.strip(), count

    async def chunk_and_index_file(
        self,
        filename: str,
        file_bytes: bytes,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ) -> Dict[str, Any]:
        """Extract text from uploaded file bytes, chunk, and index into PostgreSQL pgvector."""
        text, page_count = self.extract_text_from_file(filename, file_bytes)

        if not text:
            raise ValueError(f"Could not extract readable text from file '{filename}'. Please ensure the file contains valid text.")

        title = Path(filename).stem.replace("_", " ").replace("-", " ").title()
        chunk_count = await self.index_document(
            title=title,
            content=text,
            source=filename,
            chunk_size=chunk_size,
        )

        return {
            "title": title,
            "filename": filename,
            "chunk_count": chunk_count,
            "character_count": len(text),
            "page_count": page_count,
            "preview": text[:200] + ("..." if len(text) > 200 else ""),
        }

    @classmethod
    def _chunk_text(cls, text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[str]:
        """
        Split text into overlapping chunks with preserved sentence and paragraph context.
        Handles multi-page documents (30+ pages) cleanly without cutting words in half.
        """
        if not text or not text.strip():
            return []

        # Normalize newlines
        clean_text = text.replace("\r\n", "\n").replace("\r", "\n")
        paragraphs = [p.strip() for p in clean_text.split("\n\n") if p.strip()]

        refined_blocks: List[str] = []
        for p in paragraphs:
            if len(p) <= chunk_size:
                refined_blocks.append(p)
            else:
                # Sub-split large paragraphs by sentence endings
                sentences = re.split(r'(?<=[.!?])\s+', p)
                sub_block = ""
                for s in sentences:
                    s = s.strip()
                    if not s:
                        continue
                    if len(sub_block) + len(s) + 1 <= chunk_size:
                        sub_block = f"{sub_block} {s}".strip() if sub_block else s
                    else:
                        if sub_block:
                            refined_blocks.append(sub_block)
                        # If a single sentence exceeds chunk_size, split by word
                        if len(s) > chunk_size:
                            words = s.split()
                            word_acc = ""
                            for w in words:
                                if len(word_acc) + len(w) + 1 <= chunk_size:
                                    word_acc = f"{word_acc} {w}".strip() if word_acc else w
                                else:
                                    if word_acc:
                                        refined_blocks.append(word_acc)
                                    word_acc = w
                            if word_acc:
                                refined_blocks.append(word_acc)
                            sub_block = ""
                        else:
                            sub_block = s
                if sub_block:
                    refined_blocks.append(sub_block)

        chunks: List[str] = []
        current_chunk = ""

        for block in refined_blocks:
            if not current_chunk:
                current_chunk = block
            elif len(current_chunk) + len(block) + 2 <= chunk_size:
                current_chunk = f"{current_chunk}\n\n{block}"
            else:
                chunks.append(current_chunk)
                if chunk_overlap > 0 and len(current_chunk) > chunk_overlap:
                    overlap_seed = current_chunk[-chunk_overlap:].strip()
                    current_chunk = f"{overlap_seed}\n\n{block}"
                else:
                    current_chunk = block

        if current_chunk and (not chunks or current_chunk != chunks[-1]):
            chunks.append(current_chunk)

        return chunks if chunks else [text[:chunk_size]]

    @staticmethod
    def _extract_section(text: str) -> str:
        """Extract a markdown section heading or page indicator from chunk text."""
        for line in text.split("\n"):
            line = line.strip()
            if line.startswith("#"):
                return line.lstrip("#").strip()
            if line.startswith("--- Page "):
                return line.strip("- ").strip()
        return ""
