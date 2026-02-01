from fastapi.testclient import TestClient


def test_http_exception_includes_correlation_id(client: TestClient, auth_headers):
    response = client.get(
        "/api/rules/does-not-exist",
        headers={**auth_headers, "X-Correlation-ID": "cid-123"},
    )
    assert response.status_code == 404
    payload = response.json()
    assert payload["correlation_id"] == "cid-123"
