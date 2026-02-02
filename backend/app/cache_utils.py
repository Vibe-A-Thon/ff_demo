"""Simple TTL cache utilities."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(slots=True)
class CacheItem:
    payload: Any
    expires_at: float


class TTLCache:
    """Small in-memory TTL cache."""

    def __init__(self, ttl_seconds: int = 300, max_items: int = 200) -> None:
        self._ttl_seconds = ttl_seconds
        self._max_items = max_items
        self._store: Dict[str, CacheItem] = {}

    def get(self, key: str) -> Optional[Any]:
        item = self._store.get(key)
        if not item:
            return None
        if item.expires_at < time.time():
            self._store.pop(key, None)
            return None
        return item.payload

    def set(self, key: str, payload: Any) -> None:
        if len(self._store) >= self._max_items:
            self._evict_expired_or_oldest()
        self._store[key] = CacheItem(payload=payload, expires_at=time.time() + self._ttl_seconds)

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
