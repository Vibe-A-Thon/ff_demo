"""Dependency injection interfaces for external services."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol


class LLMClient(Protocol):
    """Boundary for LLM providers."""

    async def embeddings_create(self, model: str, input: str) -> List[float]:
        ...

    async def chat_completions_create(
        self,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: int,
    ) -> str:
        ...


class OpenAIClientAdapter:
    """Adapter to standardize OpenAI client usage for DI."""

    def __init__(self, client: Any) -> None:
        self._client = client

    async def embeddings_create(self, model: str, input: str) -> List[float]:
        response = await self._client.embeddings.create(model=model, input=input)
        return response.data[0].embedding

    async def chat_completions_create(
        self,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: int,
    ) -> str:
        response = await self._client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content


class DatabaseClient(Protocol):
    """Boundary for database clients with dynamic collection access."""

    def __getattr__(self, name: str) -> Any:
        ...


@dataclass(slots=True)
class VectorDocument:
    id: str
    vector: List[float]
    metadata: Optional[Dict[str, Any]] = None


@dataclass(slots=True)
class VectorMatch:
    id: str
    score: float
    metadata: Optional[Dict[str, Any]] = None


class VectorStore(Protocol):
    """Boundary for vector stores."""

    async def upsert(self, namespace: str, items: List[VectorDocument]) -> None:
        ...

    async def query(self, namespace: str, vector: List[float], top_k: int = 5) -> List[VectorMatch]:
        ...


class InMemoryVectorStore:
    """Simple in-memory vector store for tests and local use."""

    def __init__(self) -> None:
        self._store: Dict[str, List[VectorDocument]] = {}

    async def upsert(self, namespace: str, items: List[VectorDocument]) -> None:
        bucket = self._store.setdefault(namespace, [])
        existing = {item.id: item for item in bucket}
        for item in items:
            existing[item.id] = item
        self._store[namespace] = list(existing.values())

    async def query(self, namespace: str, vector: List[float], top_k: int = 5) -> List[VectorMatch]:
        items = self._store.get(namespace, [])
        scored = [
            VectorMatch(id=item.id, score=_cosine_similarity(vector, item.vector), metadata=item.metadata)
            for item in items
        ]
        scored.sort(key=lambda match: match.score, reverse=True)
        return scored[: max(top_k, 1)]


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    if not a or not b:
        return 0.0
    length = min(len(a), len(b))
    dot = sum(a[i] * b[i] for i in range(length))
    norm_a = sum(a[i] * a[i] for i in range(length)) ** 0.5
    norm_b = sum(b[i] * b[i] for i in range(length)) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)