from fastapi.testclient import TestClient


def test_create_and_retrieve_rag_doc(client: TestClient, auth_headers):
    create = client.post(
        "/api/rag/documents",
        json={
            "collection": "tests",
            "title": "Doc",
            "content": "Synthetic velocity signals",
            "metadata": {"team": "blue"},
            "synthetic_only": True,
        },
        headers=auth_headers,
    )
    assert create.status_code == 200

    retrieve = client.post(
        "/api/rag/retrieve",
        json={
            "query": "velocity",
            "collections": ["tests"],
            "top_k": 3,
            "use_hybrid": True,
            "retrieval_threshold": 0.1,
            "max_context_tokens": 200,
            "synthetic_only": True,
        },
        headers=auth_headers,
    )
    assert retrieve.status_code == 200
    assert len(retrieve.json()) >= 1
