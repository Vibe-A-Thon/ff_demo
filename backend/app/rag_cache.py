"""Cache for cache-augmented generation (CAG)."""

from __future__ import annotations

import time
import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional

from app.core.external_services import DatabaseClient


@dataclass(slots=True)
class CAGCacheItem:
    payload: Dict[str, Any]
    expires_at: float


class CAGCache:
    """In-memory cache for static knowledge retrieval results."""

    def __init__(self, ttl_seconds: int = 600, max_items: int = 200) -> None:
        self._ttl_seconds = ttl_seconds
        self._max_items = max_items
        self._store: Dict[str, CAGCacheItem] = {}

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        item = self._store.get(key)
        if not item:
            return None
        if item.expires_at < time.time():
            self._store.pop(key, None)
            return None
        return item.payload

    def set(self, key: str, payload: Dict[str, Any]) -> None:
        if len(self._store) >= self._max_items:
            self._evict_expired_or_oldest()
        self._store[key] = CAGCacheItem(payload=payload, expires_at=time.time() + self._ttl_seconds)

    def _evict_expired_or_oldest(self) -> None:
        now = time.time()
        expired_keys = [key for key, item in self._store.items() if item.expires_at < now]
        for key in expired_keys:
            self._store.pop(key, None)
        if len(self._store) < self._max_items:
            return
        oldest_key = min(self._store.items(), key=lambda pair: pair[1].expires_at)[0]
        self._store.pop(oldest_key, None)

    def stats(self) -> Dict[str, Any]:
        return {
            "size": len(self._store),
            "max_items": self._max_items,
            "ttl_seconds": self._ttl_seconds,
        }


cag_cache = CAGCache()


def hash_cache_key(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


async def get_persisted_cache(db: DatabaseClient, key: str) -> Optional[Dict[str, Any]]:
    """Get cached payload from persistent store.

    Args:
        db: Database client.
        key: Cache key.

    Returns:
        Optional[Dict[str, Any]]: Cached payload if valid.
    """
    record = await db.rag_cag_cache.find_one({"key": key}, {"_id": 0})
    if not record:
        return None
    expires_at = record.get("expires_at")
    if expires_at and datetime.fromisoformat(expires_at) < datetime.now(timezone.utc):
        await db.rag_cag_cache.delete_one({"key": key})
        return None
    return record.get("payload")


async def set_persisted_cache(db: DatabaseClient, key: str, payload: Dict[str, Any], ttl_seconds: int = 600) -> None:
    """Persist cached payload.

    Args:
        db: Database client.
        key: Cache key.
        payload: Payload to cache.
        ttl_seconds: Time-to-live in seconds.
    """
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
    await db.rag_cag_cache.update_one(
        {"key": key},
        {
            "$set": {
                "key": key,
                "payload": payload,
                "expires_at": expires_at.isoformat(),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        },
        upsert=True,
    )
