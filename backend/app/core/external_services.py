"""Dependency injection interfaces for external services."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol


class LLMClient(Protocol):
    """Boundary for LLM providers."""

    async def embeddings_create(self, model: str, input: str) -> List[float]:
        """Create embeddings for input text.

        Args:
            model: Embedding model name.
            input: Input text.

        Returns:
            List[float]: Embedding vector.

        Raises:
            None: Implementations may raise provider-specific errors.
        """
        ...

    async def chat_completions_create(
        self,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: int,
    ) -> str:
        """Create a chat completion.

        Args:
            model: Model name.
            messages: Chat messages.
            max_tokens: Token limit.

        Returns:
            str: Completion text.

        Raises:
            None: Implementations may raise provider-specific errors.
        """
        ...


class OpenAIClientAdapter:
    """Adapter to standardize OpenAI client usage for DI."""

    def __init__(self, client: Any) -> None:
        """Initialize adapter.

        Args:
            client: OpenAI client instance.

        Returns:
            None: This initializer returns no value.

        Raises:
            None: No explicit exceptions are raised.
        """
        self._client = client

    async def embeddings_create(self, model: str, input: str) -> List[float]:
        """Create embeddings using the OpenAI client.

        Args:
            model: Model name.
            input: Input text.

        Returns:
            List[float]: Embedding vector.

        Raises:
            None: Provider errors may be raised.
        """
        response = await self._client.embeddings.create(model=model, input=input)
        return response.data[0].embedding

    async def chat_completions_create(
        self,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: int,
    ) -> str:
        """Create a chat completion using the OpenAI client.

        Args:
            model: Model name.
            messages: Chat messages.
            max_tokens: Token limit.

        Returns:
            str: Completion text.

        Raises:
            None: Provider errors may be raised.
        """
        response = await self._client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content


class DatabaseClient(Protocol):
    """Boundary for database clients with dynamic collection access."""

    def __getattr__(self, name: str) -> Any:
        """Retrieve collection attribute dynamically.

        Args:
            name: Attribute name.

        Returns:
            Any: Collection or attribute.

        Raises:
            AttributeError: When attribute is missing.
        """
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
        """Upsert vector documents.

        Args:
            namespace: Namespace key.
            items: Vector documents.

        Returns:
            None: This method returns no value.

        Raises:
            None: Implementations may raise storage errors.
        """
        ...

    async def query(self, namespace: str, vector: List[float], top_k: int = 5) -> List[VectorMatch]:
        """Query similar vectors.

        Args:
            namespace: Namespace key.
            vector: Query vector.
            top_k: Number of results.

        Returns:
            List[VectorMatch]: Ranked matches.

        Raises:
            None: Implementations may raise storage errors.
        """
        ...


class InMemoryVectorStore:
    """Simple in-memory vector store for tests and local use."""

    def __init__(self) -> None:
        """Initialize the store.

        Args:
            None: No parameters.

        Returns:
            None: This initializer returns no value.

        Raises:
            None: No explicit exceptions are raised.
        """
        self._store: Dict[str, List[VectorDocument]] = {}

    async def upsert(self, namespace: str, items: List[VectorDocument]) -> None:
        """Upsert documents into the store.

        Args:
            namespace: Namespace key.
            items: Vector documents.

        Returns:
            None: This method returns no value.

        Raises:
            None: No explicit exceptions are raised.
        """
        bucket = self._store.setdefault(namespace, [])
        existing = {item.id: item for item in bucket}
        for item in items:
            existing[item.id] = item
        self._store[namespace] = list(existing.values())

    async def query(self, namespace: str, vector: List[float], top_k: int = 5) -> List[VectorMatch]:
        """Query similar documents from the store.

        Args:
            namespace: Namespace key.
            vector: Query vector.
            top_k: Number of results.

        Returns:
            List[VectorMatch]: Ranked matches.

        Raises:
            None: No explicit exceptions are raised.
        """
        items = self._store.get(namespace, [])
        scored = [
            VectorMatch(id=item.id, score=_cosine_similarity(vector, item.vector), metadata=item.metadata)
            for item in items
        ]
        scored.sort(key=lambda match: match.score, reverse=True)
        return scored[: max(top_k, 1)]


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    """Compute cosine similarity for vectors.

    Args:
        a: First vector.
        b: Second vector.

    Returns:
        float: Cosine similarity.

    Raises:
        None: No explicit exceptions are raised.
    """
    if not a or not b:
        return 0.0
    length = min(len(a), len(b))
    dot = sum(a[i] * b[i] for i in range(length))
    norm_a = sum(a[i] * a[i] for i in range(length)) ** 0.5
    norm_b = sum(b[i] * b[i] for i in range(length)) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)