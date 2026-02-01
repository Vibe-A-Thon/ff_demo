from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.core.exception_handlers import register_exception_handlers
from app.core.exceptions import AppError, RuleValidationError, RSBParseError, AgentExecutionError
from app.core.request_context import set_correlation_id


def test_app_error_handler_returns_payload():
    app = FastAPI()

    @app.middleware("http")
    async def add_correlation_id(request, call_next):
        set_correlation_id("corr-app-error")
        return await call_next(request)

    register_exception_handlers(app)

    @app.get("/fail")
    def fail():
        raise AppError("bad", code="bad", status_code=400)

    client = TestClient(app)
    response = client.get("/fail")
    assert response.status_code == 400
    assert response.json()["error"] == "bad"
    assert response.json()["correlation_id"] == "corr-app-error"


def test_custom_app_error_mappings():
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/rule-error")
    def rule_error():
        raise RuleValidationError(detail="invalid rule")

    @app.get("/rsb-error")
    def rsb_error():
        raise RSBParseError(detail="invalid rsb")

    @app.get("/agent-error")
    def agent_error():
        raise AgentExecutionError(detail="agent failed")

    client = TestClient(app)
    response = client.get("/rule-error")
    assert response.status_code == 400
    assert response.json()["error"] == "rule_validation_error"

    response = client.get("/rsb-error")
    assert response.status_code == 400
    assert response.json()["error"] == "rsb_parse_error"

    response = client.get("/agent-error")
    assert response.status_code == 500
    assert response.json()["error"] == "agent_execution_error"


def test_http_exception_handler():
    app = FastAPI()

    @app.middleware("http")
    async def add_correlation_id(request, call_next):
        set_correlation_id("corr-http")
        return await call_next(request)

    register_exception_handlers(app)

    @app.get("/missing")
    def missing():
        raise HTTPException(status_code=404, detail="missing")

    client = TestClient(app)
    response = client.get("/missing")
    assert response.status_code == 404
    assert response.json()["error"] == "http_error"
    assert response.json()["correlation_id"] == "corr-http"


def test_unhandled_exception_handler():
    app = FastAPI()

    @app.middleware("http")
    async def add_correlation_id(request, call_next):
        set_correlation_id("corr-500")
        return await call_next(request)

    register_exception_handlers(app)

    @app.get("/boom")
    def boom():
        raise ValueError("boom")

    client = TestClient(app)
    response = client.get("/boom")
    assert response.status_code == 500
    assert response.json()["error"] == "internal_server_error"
    assert response.json()["correlation_id"] == "corr-500"
