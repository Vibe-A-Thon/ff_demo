"""RAG utility functions for embeddings and retrieval scoring."""

import asyncio
import hashlib
import json
from typing import Any, Dict, List, Tuple
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


def build_graph_snippets(graph_context: List[Dict[str, Any]], max_items: int = 6) -> List[str]:
    """Build graph context snippets.

    Args:
        graph_context: Graph retrieval payloads.
        max_items: Max items to include.

    Returns:
        List[str]: Graph snippets.

    Raises:
        None: No explicit exceptions are raised.
    """
    snippets: List[str] = []
    for hit in graph_context[: max(max_items, 1)]:
        node = hit.get("node", {})
        name = node.get("name", "node")
        neighbors = hit.get("neighbors", [])
        neighbor_names = ", ".join(n.get("name", "") for n in neighbors[:4])
        if neighbor_names:
            snippets.append(f"[graph] {name} connected to {neighbor_names}")
        else:
            snippets.append(f"[graph] {name}")
    return snippets


async def verify_answer_with_context(
    answer: str,
    context_snippets: List[str],
    llm_client: LLMClient | None,
) -> Tuple[float, str]:
    """Verify answer grounding against context.

    Args:
        answer: Generated answer.
        context_snippets: Context snippets used for generation.
        llm_client: Optional LLM client.

    Returns:
        Tuple[float, str]: Score (0-1) and feedback string.

    Raises:
        None: No explicit exceptions are raised.
    """
    if not answer or not context_snippets:
        return 0.0, "no_context"
    context_text = "\n".join(context_snippets)
    if llm_client:
        try:
            prompt = (
                "You are a verifier. Score grounding from 0 to 1 based on whether the answer is supported by the context. "
                "Respond as JSON: {\"score\": <float>, \"feedback\": <short_reason>}\n\n"
                f"Context:\n{context_text}\n\nAnswer:\n{answer}"
            )
            response = await llm_client.chat_completions_create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
            )
            payload = json.loads(response)
            score = float(payload.get("score", 0.0))
            feedback = str(payload.get("feedback", "unverified"))
            return max(0.0, min(score, 1.0)), feedback
        except Exception as exc:
            logger.exception("Verification fallback", extra={"payload": {"error": str(exc)}})

    answer_tokens = tokenize(answer)
    context_tokens = tokenize(context_text)
    overlap = len(set(answer_tokens) & set(context_tokens))
    score = overlap / max(len(set(answer_tokens)), 1)
    feedback = "heuristic_overlap"
    return max(0.0, min(score, 1.0)), feedback


async def refine_query_with_feedback(
    query: str,
    feedback: str,
    llm_client: LLMClient | None,
) -> str:
    """Refine a query using verification feedback.

    Args:
        query: Original query.
        feedback: Verification feedback.
        llm_client: Optional LLM client.

    Returns:
        str: Refined query.

    Raises:
        None: No explicit exceptions are raised.
    """
    if llm_client:
        try:
            prompt = (
                "Rewrite the query to improve retrieval based on feedback. Keep it short and synthetic-only. "
                "Return the rewritten query only.\n\n"
                f"Query: {query}\nFeedback: {feedback}"
            )
            response = await llm_client.chat_completions_create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=80,
            )
            refined = response.strip()
            return refined or query
        except Exception as exc:
            logger.exception("Query refine fallback", extra={"payload": {"error": str(exc)}})
    return query


async def rewrite_query(query: str, llm_client: LLMClient | None) -> str:
    """Rewrite a query for better retrieval.

    Args:
        query: Original query.
        llm_client: Optional LLM client.

    Returns:
        str: Rewritten query.
    """
    if llm_client:
        try:
            prompt = (
                "Rewrite the query to improve retrieval. Keep it short, include key entities, and remain synthetic-only. "
                "Return only the rewritten query.\n\n"
                f"Query: {query}"
            )
            response = await llm_client.chat_completions_create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=80,
            )
            rewritten = response.strip()
            return rewritten or query
        except Exception as exc:
            logger.exception("Query rewrite fallback", extra={"payload": {"error": str(exc)}})
    return query


async def expand_query(query: str, llm_client: LLMClient | None) -> str:
    """Expand a query with related keywords.

    Args:
        query: Original query.
        llm_client: Optional LLM client.

    Returns:
        str: Expanded query.
    """
    if llm_client:
        try:
            prompt = (
                "Expand the query with 3-5 related keywords for fraud defense retrieval. "
                "Return a single line query string.\n\n"
                f"Query: {query}"
            )
            response = await llm_client.chat_completions_create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=80,
            )
            expanded = response.strip()
            return expanded or query
        except Exception as exc:
            logger.exception("Query expansion fallback", extra={"payload": {"error": str(exc)}})
    return query


def rerank_hits(query: str, hits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Rerank hits using keyword overlap with the query.

    Args:
        query: Query text.
        hits: Retrieved hits.

    Returns:
        List[Dict[str, Any]]: Reranked hits.
    """
    query_tokens = tokenize(query)
    rescored = []
    for hit in hits:
        content = hit.get("content", "")
        score = keyword_score(query_tokens, tokenize(content))
        combined = (hit.get("score", 0) * 0.7) + (score * 0.3)
        rescored.append({**hit, "score": combined})
    rescored.sort(key=lambda item: item.get("score", 0), reverse=True)
    return rescored


def deduplicate_hits(hits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Deduplicate hits by content hash.

    Args:
        hits: Retrieved hits.

    Returns:
        List[Dict[str, Any]]: Deduplicated hits.
    """
    seen = set()
    deduped = []
    for hit in hits:
        content = hit.get("content", "")
        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
        if digest in seen:
            continue
        seen.add(digest)
        deduped.append(hit)
    return deduped


def detect_contradictions(hits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Detect simple contradictions across hits.

    Args:
        hits: Retrieved hits.

    Returns:
        List[Dict[str, Any]]: Contradiction flags.
    """
    flags: List[Dict[str, Any]] = []
    statements = [hit.get("content", "").lower() for hit in hits]
    for idx, stmt in enumerate(statements):
        if " not " in stmt and any(word in stmt for word in ["allowed", "required", "enable"]):
            flags.append({"index": idx, "reason": "negation_detected"})
    return flags


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


def classify_query_intent(query: str) -> str:
    """Classify a query intent for retrieval routing.

    Args:
        query: Query text.

    Returns:
        str: intent label (lookup, relationship, semantic).

    Raises:
        None: No explicit exceptions are raised.
    """
    lowered = query.lower()
    if any(token in lowered for token in ["ring", "network", "graph", "connected", "relationship", "shared"]):
        return "relationship"
    if any(token in lowered for token in ["rule", "rsb", "policy", "id", "code", "spec", "manifest"]):
        return "lookup"
    if any(char.isdigit() for char in lowered):
        return "lookup"
    return "semantic"


def select_rag_mode(query: str, requested_mode: str | None) -> str:
    """Select the retrieval mode based on request and query intent.

    Args:
        query: Query text.
        requested_mode: Requested rag mode.

    Returns:
        str: Selected rag mode.

    Raises:
        None: No explicit exceptions are raised.
    """
    if requested_mode and requested_mode.lower() not in {"auto", ""}:
        return requested_mode.lower()
    intent = classify_query_intent(query)
    if intent == "relationship":
        return "graph"
    if intent == "lookup":
        return "hybrid"
    return "hybrid"


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


async def compute_groundedness_metrics(
    question: str,
    answer: str,
    contexts: List[str],
    llm_client: LLMClient | None,
) -> Dict[str, Any]:
    """Compute groundedness/faithfulness metrics using RAGAS or heuristics.

    Args:
        question: Question text.
        answer: Generated answer.
        contexts: Context snippets used.
        llm_client: Optional LLM client.

    Returns:
        Dict[str, Any]: Metrics payload.
    """
    try:
        from ragas import evaluate
        from ragas.metrics import faithfulness, answer_relevancy
        from datasets import Dataset

        dataset = Dataset.from_dict({
            "question": [question],
            "answer": [answer],
            "contexts": [contexts],
        })

        result = await asyncio.to_thread(
            evaluate,
            dataset,
            metrics=[faithfulness, answer_relevancy],
        )
        return {
            "faithfulness": float(result["faithfulness"][0]),
            "answer_relevancy": float(result["answer_relevancy"][0]),
            "method": "ragas",
        }
    except Exception as exc:
        logger.warning("ragas_metrics_fallback", extra={"payload": {"error": str(exc)}})

    context_text = " ".join(contexts).lower()
    answer_tokens = tokenize(answer)
    context_tokens = tokenize(context_text)
    overlap = len(set(answer_tokens) & set(context_tokens))
    faithfulness = overlap / max(len(set(answer_tokens)), 1)
    answer_relevancy = overlap / max(len(set(context_tokens)), 1)
    return {
        "faithfulness": round(faithfulness, 4),
        "answer_relevancy": round(answer_relevancy, 4),
        "method": "heuristic",
    }
