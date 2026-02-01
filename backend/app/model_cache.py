"""Shared model artifact caching helpers."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from app.config import get_integration_setting
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def _ensure_dir(path: str) -> str:
    Path(path).mkdir(parents=True, exist_ok=True)
    return path


def get_model_cache_dir() -> Optional[str]:
    """Resolve shared model cache directory.

    Priority:
    1) integrations_config.json -> model_cache.shared_dir
    2) integrations_config.json -> multimodal.model_cache_dir
    3) MODEL_CACHE_DIR env
    4) HF_HOME env
    """
    cache_dir = (
        get_integration_setting("model_cache", "shared_dir")
        or get_integration_setting("multimodal", "model_cache_dir")
        or os.environ.get("MODEL_CACHE_DIR")
        or os.environ.get("HF_HOME")
    )
    if not cache_dir:
        return None
    return _ensure_dir(cache_dir)


def configure_model_cache_env(cache_dir: Optional[str] = None) -> Optional[str]:
    """Configure shared cache environment variables.

    Returns:
        Optional[str]: The resolved cache directory.
    """
    resolved = cache_dir or get_model_cache_dir()
    if not resolved:
        return None

    hub_cache = _ensure_dir(os.path.join(resolved, "hub"))
    transformers_cache = _ensure_dir(os.path.join(resolved, "transformers"))
    sentence_cache = _ensure_dir(os.path.join(resolved, "sentence-transformers"))
    torch_cache = _ensure_dir(os.path.join(resolved, "torch"))

    os.environ.setdefault("HF_HOME", resolved)
    os.environ.setdefault("HUGGINGFACE_HUB_CACHE", hub_cache)
    os.environ.setdefault("TRANSFORMERS_CACHE", transformers_cache)
    os.environ.setdefault("SENTENCE_TRANSFORMERS_HOME", sentence_cache)
    os.environ.setdefault("TORCH_HOME", torch_cache)

    logger.info("model_cache.configured", extra={"payload": {"cache_dir": resolved}})
    return resolved
