"""Additional pytest hooks and patches for the test suite."""

from __future__ import annotations

import asyncio
import inspect
import logging
from datetime import datetime, timezone
from typing import Generator

import pytest
from starlette.testclient import TestClient as _TestClient

from app import audit, db as db_module, run_helpers, security, workflow_service
from app.routes import rag as rag_routes
from app import rsb_utils
from app.core import logging_config


@pytest.fixture(autouse=True)
def _patch_db(in_memory_db) -> Generator[None, None, None]:
    """Ensure all modules use the in-memory DB during tests."""
    db_module.db = in_memory_db
    security.db = in_memory_db
    audit.db = in_memory_db
    workflow_service.db = in_memory_db
    run_helpers.db = in_memory_db
    yield


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers and patch TestClient defaults."""
    config.addinivalue_line("markers", "asyncio: mark async tests")

    original_init = _TestClient.__init__

    def _init(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        kwargs.setdefault("raise_server_exceptions", False)
        return original_init(self, *args, **kwargs)

    _TestClient.__init__ = _init  # type: ignore[assignment]

    class _MergingAdapter(logging.LoggerAdapter):
        def process(self, msg, kwargs):  # type: ignore[no-untyped-def]
            extra = kwargs.get("extra", {})
            merged = {**self.extra, **extra}
            kwargs["extra"] = merged
            return msg, kwargs

    def _patched_get_logger(name: str, service_name: str = "fraud-forge"):
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging_config.RedactingJsonFormatter()
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return _MergingAdapter(logger, {"service_name": service_name})

    logging_config.get_logger = _patched_get_logger


@pytest.fixture(autouse=True)
def _patch_rsb_timestamp(monkeypatch: pytest.MonkeyPatch) -> None:
    """Freeze timestamps in RSB utils for deterministic tests."""

    class _FixedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):  # type: ignore[override]
            return datetime(2024, 1, 1, 0, 0, 0, tzinfo=tz or timezone.utc)

    monkeypatch.setattr(rsb_utils, "datetime", _FixedDatetime)


@pytest.fixture(autouse=True)
def _wrap_rag_embedding_signature(request: pytest.FixtureRequest) -> None:
    """Ensure mock embeddings accept the newer llm_client kwarg."""
    if "mock_embedding" not in request.fixturenames:
        return
    request.getfixturevalue("mock_embedding")

    original = rag_routes.get_embedding

    async def _wrapper(text: str, **kwargs):  # type: ignore[no-untyped-def]
        return await original(text)

    rag_routes.get_embedding = _wrapper


def pytest_pyfunc_call(pyfuncitem: pytest.Function) -> bool | None:
    """Run async tests without requiring pytest-asyncio."""
    test_func = pyfuncitem.obj
    if inspect.iscoroutinefunction(test_func):
        signature = inspect.signature(test_func)
        kwargs = {
            name: value
            for name, value in pyfuncitem.funcargs.items()
            if name in signature.parameters
        }
        asyncio.run(test_func(**kwargs))
        return True
    return None
