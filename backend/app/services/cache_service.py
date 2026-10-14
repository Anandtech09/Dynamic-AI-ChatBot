"""
Cache Service — High-Performance In-Memory Caching via Redis.

Accelerates conversational AI workflows:
- Semantic RAG vector query caching (sub-millisecond repeat queries)
- Active session message history caching
- Analytics overview aggregation caching
- Graceful fail-open fallback if Redis is unavailable
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class CacheService:
    """Async Redis caching client with automatic JSON serialization and fail-open resilience."""

    _instance: Optional[CacheService] = None

    def __init__(self):
        self.settings = get_settings()
        self._redis = None
        self._enabled = bool(self.settings.redis_url)

    async def _get_client(self):
        """Lazily initialize the async Redis connection."""
        if not self._enabled:
            return None
        if self._redis is None:
            try:
                import redis.asyncio as aioredis
                url = self.settings.redis_url
                # Auto-upgrade to SSL rediss:// for cloud endpoints (e.g., Upstash) that require TLS
                if "upstash.io" in url and url.startswith("redis://"):
                    url = url.replace("redis://", "rediss://", 1)

                self._redis = aioredis.from_url(
                    url,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=3.0,
                    socket_timeout=3.0,
                )
            except Exception as e:
                logger.warning("Could not connect to Redis at %s: %s", self.settings.redis_url, e)
                self._redis = None
        return self._redis

    async def is_healthy(self) -> bool:
        """Check if Redis cache is reachable and responding to PING."""
        try:
            client = await self._get_client()
            if client:
                return await client.ping()
        except Exception:
            pass
        return False

    async def get(self, key: str) -> Optional[Any]:
        """Retrieve and deserialize a JSON object from cache. Returns None on cache miss."""
        try:
            client = await self._get_client()
            if not client:
                return None
            data = await client.get(key)
            if data is not None:
                return json.loads(data)
        except Exception as e:
            logger.debug("Redis cache get failed for key '%s': %s", key, e)
        return None

    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Serialize and store an object in cache with a TTL (seconds)."""
        try:
            client = await self._get_client()
            if not client:
                return False
            payload = json.dumps(value)
            await client.set(key, payload, ex=ttl)
            return True
        except Exception as e:
            logger.debug("Redis cache set failed for key '%s': %s", key, e)
            return False

    async def delete(self, key: str) -> bool:
        """Remove a specific key from cache."""
        try:
            client = await self._get_client()
            if client:
                await client.delete(key)
                return True
        except Exception as e:
            logger.debug("Redis cache delete failed for key '%s': %s", key, e)
        return False

    async def delete_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching a glob pattern (e.g., 'rag:*')."""
        count = 0
        try:
            client = await self._get_client()
            if not client:
                return 0
            keys = await client.keys(pattern)
            if keys:
                count = await client.delete(*keys)
        except Exception as e:
            logger.debug("Redis delete_pattern failed for '%s': %s", pattern, e)
        return count

    # ── Specialized Caching Helpers ──────────────────────────────────────────

    async def get_rag_search(self, query: str, top_k: int) -> Optional[List[Dict[str, Any]]]:
        """Fetch cached semantic search results for an identical query."""
        key = f"rag:query:{top_k}:{query.strip().lower()}"
        return await self.get(key)

    async def set_rag_search(self, query: str, top_k: int, results: List[Dict[str, Any]], ttl: int = 1800) -> bool:
        """Store semantic search results in cache (default TTL: 30 minutes)."""
        key = f"rag:query:{top_k}:{query.strip().lower()}"
        return await self.set(key, results, ttl=ttl)

    async def invalidate_rag_cache(self) -> int:
        """Invalidate all cached RAG queries when knowledge documents are modified."""
        return await self.delete_pattern("rag:query:*")

    async def get_analytics_overview(self) -> Optional[Dict[str, Any]]:
        """Fetch cached dashboard KPIs."""
        return await self.get("analytics:overview")

    async def set_analytics_overview(self, data: Dict[str, Any], ttl: int = 60) -> bool:
        """Cache dashboard KPIs for 60 seconds."""
        return await self.set("analytics:overview", data, ttl=ttl)


_cache_instance: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """Return the cached singleton CacheService instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = CacheService()
    return _cache_instance
