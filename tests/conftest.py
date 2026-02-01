"""Pytest configuration and fixtures."""

from __future__ import annotations

import os
import sys
from typing import Dict

import pytest
from fastapi.testclient import TestClient

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_PATH = os.path.join(ROOT, "backend")
if BACKEND_PATH not in sys.path:
    sys.path.insert(0, BACKEND_PATH)

from app.main import app  # noqa: E402
from app.security import create_token  # noqa: E402
from app import db as db_module  # noqa: E402
from app.routes import approvals, battles, rag, rsb, rules, runs, evidence, workflow  # noqa: E402
from tests.fixtures import InMemoryDB, seed_user  # noqa: E402


@pytest.fixture()
def in_memory_db():
    return InMemoryDB()


@pytest.fixture()
def client(in_memory_db):
    db_module.db = in_memory_db
    approvals.db = in_memory_db
    battles.db = in_memory_db
    rag.db = in_memory_db
    rsb.db = in_memory_db
    rules.db = in_memory_db
    runs.db = in_memory_db
    evidence.db = in_memory_db
    workflow.db = in_memory_db
    return TestClient(app)


@pytest.fixture()
def auth_headers(in_memory_db) -> Dict[str, str]:
    user = seed_user(in_memory_db, role="bank_admin")
    token = create_token(user["id"], user["role"])
    return {"Authorization": f"Bearer {token}"}
