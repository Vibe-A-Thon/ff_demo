"""Dependency providers for external services."""

from __future__ import annotations

from typing import Optional

from app import db as db_module
from app.core.external_services import (
    DatabaseClient,
    InMemoryVectorStore,
    LLMClient,
    VectorStore,
)
from app.llm import LLMGateway, LLMService

_llm_client: Optional[LLMClient] = None
_llm_service: Optional[LLMService] = None
_vector_store: Optional[VectorStore] = None


def get_db() -> DatabaseClient:
    """Return the current database client.

    Args:
        None: This function takes no parameters.

    Returns:
        DatabaseClient: Database client instance.

    Raises:
        None: No explicit exceptions are raised.
    """
    return db_module.db


def get_llm_client() -> Optional[LLMClient]:
    """Return the configured LLM client if available.

    Args:
        None: This function takes no parameters.

    Returns:
        Optional[LLMClient]: LLM client instance.

    Raises:
        None: No explicit exceptions are raised.
    """
    global _llm_client
    if _llm_client is not None:
        return _llm_client
    _llm_client = LLMGateway(get_llm_service())
    return _llm_client


def get_llm_service() -> LLMService:
    """Return the configured LLM service.

    Args:
        None: This function takes no parameters.

    Returns:
        LLMService: LLM service instance.

    Raises:
        None: No explicit exceptions are raised.
    """
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service


def get_vector_store() -> VectorStore:
    """Return the vector store instance.

    Args:
        None: This function takes no parameters.

    Returns:
        VectorStore: Vector store instance.

    Raises:
        None: No explicit exceptions are raised.
    """
    global _vector_store
    if _vector_store is None:
        _vector_store = InMemoryVectorStore()
    return _vector_store