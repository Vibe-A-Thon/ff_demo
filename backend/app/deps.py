"""Dependency providers for external services."""

from __future__ import annotations

from typing import Optional

from app import db as db_module
from app.config import OPENAI_API_KEY
from app.core.external_services import (
    DatabaseClient,
    InMemoryVectorStore,
    LLMClient,
    OpenAIClientAdapter,
    VectorStore,
)

_llm_client: Optional[LLMClient] = None
_vector_store: Optional[VectorStore] = None


def get_db() -> DatabaseClient:
    return db_module.db


def get_llm_client() -> Optional[LLMClient]:
    global _llm_client
    if _llm_client is not None:
        return _llm_client
    if not OPENAI_API_KEY:
        return None
    from openai import AsyncOpenAI

    _llm_client = OpenAIClientAdapter(AsyncOpenAI(api_key=OPENAI_API_KEY))
    return _llm_client


def get_vector_store() -> VectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = InMemoryVectorStore()
    return _vector_store