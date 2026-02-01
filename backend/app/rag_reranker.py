"""Strong reranker and contradiction classifier using cross-encoders."""

from __future__ import annotations

from typing import Any, Dict, List

from app.core.logging_config import get_logger
from app.config import get_integration_setting
from app.model_cache import configure_model_cache_env, get_model_cache_dir

logger = get_logger(__name__)

_reranker = None
_contradiction_model = None


def _load_reranker():
    global _reranker
    if _reranker is not None:
        return
    try:
        from sentence_transformers import CrossEncoder
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("sentence-transformers is required for cross-encoder reranking") from exc
    cache_dir = get_model_cache_dir()
    configure_model_cache_env(cache_dir)
    _reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2", cache_folder=cache_dir)


def _load_contradiction():
    global _contradiction_model
    if _contradiction_model is not None:
        return
    try:
        from sentence_transformers import CrossEncoder
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("sentence-transformers is required for contradiction classifier") from exc
    cache_dir = get_model_cache_dir()
    configure_model_cache_env(cache_dir)
    _contradiction_model = CrossEncoder("cross-encoder/nli-deberta-v3-base", cache_folder=cache_dir)


def _predict_in_batches(model, pairs: List[tuple], batch_size: int) -> List[float]:
    scores: List[float] = []
    batch = max(batch_size, 1)
    for idx in range(0, len(pairs), batch):
        chunk = pairs[idx : idx + batch]
        scores.extend(model.predict(chunk))
    return scores


def rerank_hits_strong(query: str, hits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Rerank hits using a cross-encoder model.

    Args:
        query: Query text.
        hits: Retrieved hits.

    Returns:
        List[Dict[str, Any]]: Reranked hits.
    """
    if not hits:
        return hits
    try:
        _load_reranker()
        pairs = [(query, hit.get("content", "")) for hit in hits]
        batch_size = int(get_integration_setting("rag_reranker", "batch_size", "8") or 8)
        scores = _predict_in_batches(_reranker, pairs, batch_size)
        rescored = []
        for hit, score in zip(hits, scores):
            rescored.append({**hit, "score": float(score)})
        rescored.sort(key=lambda item: item.get("score", 0), reverse=True)
        return rescored
    except Exception as exc:
        logger.warning("strong_rerank_fallback", extra={"payload": {"error": str(exc)}})
        return hits


def classify_contradictions(query: str, hits: List[Dict[str, Any]], threshold: float = 0.6) -> List[Dict[str, Any]]:
    """Classify contradictions using NLI cross-encoder.

    Args:
        query: Query text.
        hits: Retrieved hits.
        threshold: Contradiction score threshold.

    Returns:
        List[Dict[str, Any]]: Flags for contradictions.
    """
    if not hits:
        return []
    try:
        _load_contradiction()
        pairs = [(query, hit.get("content", "")) for hit in hits]
        batch_size = int(get_integration_setting("rag_reranker", "batch_size", "8") or 8)
        scores = _predict_in_batches(_contradiction_model, pairs, batch_size)
        flags = []
        for idx, score in enumerate(scores):
            if float(score) >= threshold:
                flags.append({"index": idx, "reason": "contradiction_model", "score": float(score)})
        return flags
    except Exception as exc:
        logger.warning("contradiction_model_fallback", extra={"payload": {"error": str(exc)}})
        return []


def warmup_models() -> Dict[str, Any]:
    """Warm up cross-encoder models to reduce first-call latency."""
    result = {"reranker": "skipped", "contradiction": "skipped"}
    try:
        _load_reranker()
        _reranker.predict([("warmup", "warmup")])
        result["reranker"] = "ok"
    except Exception as exc:
        result["reranker"] = f"error:{exc}"
    try:
        _load_contradiction()
        _contradiction_model.predict([("warmup", "warmup")])
        result["contradiction"] = "ok"
    except Exception as exc:
        result["contradiction"] = f"error:{exc}"
    return result
