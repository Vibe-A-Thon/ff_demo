"""RAG utility functions for embeddings and retrieval scoring."""

import hashlib
import json
from typing import Any, Dict, List
import openai
from app.config import OPENAI_API_KEY, OPENAI_EMBEDDING_MODEL
from app.core.external_services import LLMClient
from app.core.logging_config import get_logger

logger = get_logger(__name__)
openai_client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


def tokenize(text: str) -> List[str]:
    """Tokenize a string into normalized tokens.

    Args:
        text: Input text.

    Returns:
        List[str]: Token list.

    Raises:
        None: No explicit exceptions are raised.
    """
    return [t for t in "".join([c.lower() if c.isalnum() else " " for c in text]).split() if t]


def keyword_score(query_tokens: List[str], doc_tokens: List[str]) -> float:
    """Compute keyword overlap score.

    Args:
        query_tokens: Query tokens.
        doc_tokens: Document tokens.

    Returns:
        float: Overlap score.

    Raises:
        None: No explicit exceptions are raised.
    """
    if not query_tokens or not doc_tokens:
        return 0.0
    overlap = len(set(query_tokens) & set(doc_tokens))
    return overlap / max(len(set(query_tokens)), 1)


def simple_embed(text: str, dim: int = 128) -> List[float]:
    """Generate a deterministic embedding for text.

    Args:
        text: Input text.
        dim: Embedding dimension.

    Returns:
        List[float]: Embedding vector.

    Raises:
        None: No explicit exceptions are raised.
    """
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    vector = [0.0] * dim
    for i, b in enumerate(digest):
        vector[i % dim] += (b / 255.0) - 0.5
    norm = sum(v * v for v in vector) ** 0.5
    return [v / norm for v in vector] if norm else vector


async def get_embedding(text: str, llm_client: LLMClient | None = None) -> List[float]:
    """Retrieve an embedding using LLM or fallback.

    Args:
        text: Input text.
        llm_client: Optional LLM client.

    Returns:
        List[float]: Embedding vector.

    Raises:
        None: Exceptions are handled with fallback.
    """
    if llm_client:
        try:
            return await llm_client.embeddings_create(model=OPENAI_EMBEDDING_MODEL, input=text)
        except Exception as exc:
            logger.exception("Embedding fallback", extra={"payload": {"error": str(exc)}})
    if openai_client:
        try:
            response = await openai_client.embeddings.create(
                model=OPENAI_EMBEDDING_MODEL,
                input=text,
            )
            return response.data[0].embedding
        except Exception as exc:
            logger.exception("Embedding fallback", extra={"payload": {"error": str(exc)}})
    return simple_embed(text)


def cosine_similarity(a: List[float], b: List[float]) -> float:
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


def approx_tokens(text: str) -> int:
    """Approximate token count for text.

    Args:
        text: Input text.

    Returns:
        int: Token count approximation.

    Raises:
        None: No explicit exceptions are raised.
    """
    return len(text.split())


def build_context_snippets(hits: List[Dict[str, Any]], max_tokens: int) -> List[str]:
    """Build context snippets within token budget.

    Args:
        hits: Retrieved hits.
        max_tokens: Token budget.

    Returns:
        List[str]: Context snippets.

    Raises:
        None: No explicit exceptions are raised.
    """
    snippets: List[str] = []
    running = 0
    for hit in hits:
        content = hit.get("content", "")
        chunk = f"[{hit.get('collection')}:{hit.get('id')}] {content}"
        chunk_tokens = approx_tokens(chunk)
        if running + chunk_tokens > max_tokens:
            break
        snippets.append(chunk)
        running += chunk_tokens
    return snippets


def contains_sensitive_identifiers(text: str) -> bool:
    """Detect sensitive identifiers in text.

    Args:
        text: Input text.

    Returns:
        bool: True if sensitive content is detected.

    Raises:
        None: No explicit exceptions are raised.
    """
    digits = [c for c in text if c.isdigit()]
    if len(digits) >= 9:
        return True
    lowered = text.lower()
    flags = ["ssn", "social security", "account number", "routing number", "credit card"]
    return any(flag in lowered for flag in flags)


def build_snippet(doc: Dict[str, Any]) -> str:
    """Build a short snippet from a document.

    Args:
        doc: Document payload.

    Returns:
        str: Snippet text.

    Raises:
        None: No explicit exceptions are raised.
    """
    return doc.get("content", "")[:180]


def format_context_prompt(snippets: List[str], query: str) -> str:
    """Format context and query into a prompt.

    Args:
        snippets: Context snippets.
        query: User query.

    Returns:
        str: Prompt text.

    Raises:
        None: No explicit exceptions are raised.
    """
    return "\n".join(snippets) + f"\n\nUser question: {query}"


def safe_json_dumps(payload: Dict[str, Any]) -> str:
    """Serialize payload to JSON safely.

    Args:
        payload: Payload data.

    Returns:
        str: JSON string.

    Raises:
        None: No explicit exceptions are raised.
    """
    return json.dumps(payload, ensure_ascii=False, default=str)
