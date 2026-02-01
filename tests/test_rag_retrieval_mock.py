import pytest
from fastapi.testclient import TestClient

from app.routes import rag as rag_routes


@pytest.fixture()
def mock_embedding(monkeypatch):
    async def _fake_embedding(text: str):
        return [1.0, 0.0] if "alpha" in text or "velocity" in text else [0.0, 1.0]

    monkeypatch.setattr(rag_routes, "get_embedding", _fake_embedding)
    return _fake_embedding


def test_rag_retrieve_uses_vector_mock(client: TestClient, auth_headers, in_memory_db, mock_embedding):
    in_memory_db.rag_documents._items.extend(
        [
            {
                "id": "doc-1",
                "collection": "tests",
                "title": "Alpha",
                "content": "alpha signal",
                "embedding": [1.0, 0.0],
                "metadata": {},
                "synthetic_only": True,
            },
            {
                "id": "doc-2",
                "collection": "tests",
                "title": "Beta",
                "content": "beta signal",
                "embedding": [0.0, 1.0],
                "metadata": {},
                "synthetic_only": True,
            },
        ]
    )

    response = client.post(
        "/api/rag/retrieve",
        json={
            "query": "alpha",
            "collections": ["tests"],
            "top_k": 1,
            "use_hybrid": False,
            "retrieval_threshold": 0.1,
            "max_context_tokens": 200,
            "synthetic_only": True,
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    hits = response.json()
    assert hits[0]["doc_id"] == "doc-1"


def test_rag_query_fallback_to_all_collections(client: TestClient, auth_headers, in_memory_db, mock_embedding):
    in_memory_db.rag_documents._items.extend(
        [
            {
                "id": "doc-3",
                "collection": "primary",
                "title": "Primary",
                "content": "beta signal",
                "embedding": [0.0, 1.0],
                "metadata": {},
                "synthetic_only": True,
            },
            {
                "id": "doc-4",
                "collection": "fallback",
                "title": "Fallback",
                "content": "alpha signal",
                "embedding": [1.0, 0.0],
                "metadata": {},
                "synthetic_only": True,
            },
        ]
    )

    response = client.post(
        "/api/rag/query",
        json={
            "query": "alpha",
            "collections": ["primary"],
            "top_k": 2,
            "use_hybrid": False,
            "retrieval_threshold": 0.9,
            "max_context_tokens": 200,
            "synthetic_only": True,
            "include_graph_context": False,
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["used_fallback"] is True
    assert payload["hits"][0]["collection"] == "fallback"


def test_rag_query_includes_graph_context(client: TestClient, auth_headers, in_memory_db, mock_embedding):
    in_memory_db.rag_documents._items.append(
        {
            "id": "doc-5",
            "collection": "tests",
            "title": "Velocity",
            "content": "velocity signal",
            "embedding": [1.0, 0.0],
            "metadata": {},
            "synthetic_only": True,
        }
    )
    in_memory_db.knowledge_nodes._items.append(
        {
            "id": "node-1",
            "node_type": "taxonomy",
            "name": "velocity anomaly",
            "data": {"score": 1},
            "connections": [],
        }
    )

    response = client.post(
        "/api/rag/query",
        json={
            "query": "velocity",
            "collections": ["tests"],
            "top_k": 1,
            "use_hybrid": False,
            "retrieval_threshold": 0.1,
            "max_context_tokens": 200,
            "synthetic_only": True,
            "include_graph_context": True,
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["graph_context"][0]["name"] == "velocity anomaly"
