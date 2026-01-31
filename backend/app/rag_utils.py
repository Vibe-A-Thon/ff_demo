import hashlib
import json
import logging
from typing import Any, Dict, List
import openai
from app.config import OPENAI_API_KEY, OPENAI_EMBEDDING_MODEL

logger = logging.getLogger(__name__)
openai_client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


def tokenize(text: str) -> List[str]:
    return [t for t in "".join([c.lower() if c.isalnum() else " " for c in text]).split() if t]


def keyword_score(query_tokens: List[str], doc_tokens: List[str]) -> float:
    if not query_tokens or not doc_tokens:
        return 0.0
    overlap = len(set(query_tokens) & set(doc_tokens))
    return overlap / max(len(set(query_tokens)), 1)


def simple_embed(text: str, dim: int = 128) -> List[float]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    vector = [0.0] * dim
    for i, b in enumerate(digest):
        vector[i % dim] += (b / 255.0) - 0.5
    norm = sum(v * v for v in vector) ** 0.5
    return [v / norm for v in vector] if norm else vector


async def get_embedding(text: str) -> List[float]:
    if openai_client:
        try:
            response = await openai_client.embeddings.create(
                model=OPENAI_EMBEDDING_MODEL,
                input=text,
            )
            return response.data[0].embedding
        except Exception as exc:
            logger.warning(f"Embedding fallback: {exc}")
    return simple_embed(text)


def cosine_similarity(a: List[float], b: List[float]) -> float:
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
    return len(text.split())


def build_context_snippets(hits: List[Dict[str, Any]], max_tokens: int) -> List[str]:
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
    digits = [c for c in text if c.isdigit()]
    if len(digits) >= 9:
        return True
    lowered = text.lower()
    flags = ["ssn", "social security", "account number", "routing number", "credit card"]
    return any(flag in lowered for flag in flags)


def build_snippet(doc: Dict[str, Any]) -> str:
    return doc.get("content", "")[:180]


def format_context_prompt(snippets: List[str], query: str) -> str:
    return "\n".join(snippets) + f"\n\nUser question: {query}"


def safe_json_dumps(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, default=str)
