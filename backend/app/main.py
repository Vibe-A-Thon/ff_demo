"""FastAPI application entry point."""

import asyncio
from fastapi import FastAPI, Request, Depends
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import uuid
from app.config import APP_NAME, APP_VERSION, DEBUG_MODE, API_PREFIX, CORS_ORIGINS, get_integration_setting
from app.db import init_database, close_database
from app.core.logging_config import setup_logging, get_logger
from app.model_cache import configure_model_cache_env
from app.core.request_context import set_correlation_id, set_request_id
from app.core.exception_handlers import register_exception_handlers
from app.security import get_current_user
from app.graph_sync_neo4j import run_sync_loop
from app.rag_reranker import warmup_models
from app.db import db as db_client
from app.routes import (
    auth,
    me,
    runs,
    workflow,
    xai,
    graph,
    tools,
    battles,
    rules,
    rsb,
    amc,
    pep,
    brc,
    evidence,
    teams,
    agents,
    rag,
    knowledge,
    approvals,
    governance,
    metrics,
    ai,
    seed,
    root,
    evaluation,
    settings,
    llm,
    websocket,
    brain_surgery,
    lessons,
)

setup_logging(APP_NAME)
logger = get_logger(__name__)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        request.state.request_id = request_id
        set_correlation_id(correlation_id)
        set_request_id(request_id)
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Request-ID"] = request_id
        return response


app = FastAPI(title=APP_NAME, version=APP_VERSION, debug=DEBUG_MODE)

app.get("/")(root.root)

public_routers = [auth.router, root.router]
protected_routers = [
    me.router,
    runs.router,
    workflow.router,
    xai.router,
    graph.router,
    tools.router,
    battles.router,
    rules.router,
    rsb.router,
    amc.router,
    pep.router,
    brc.router,
    evidence.router,
    teams.router,
    agents.router,
    rag.router,
    knowledge.router,
    approvals.router,
    governance.router,
    metrics.router,
    ai.router,
    seed.router,
    evaluation.router,
    settings.router,
    llm.router,
    brain_surgery.router,
    lessons.router,
]

for router in public_routers:
    app.include_router(router, prefix=API_PREFIX)

for router in protected_routers:
    app.include_router(router, prefix=API_PREFIX, dependencies=[Depends(get_current_user)])

app.include_router(websocket.router)

app.add_middleware(CorrelationIdMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

@app.on_event("startup")
async def startup_db_client():
    await init_database()
    logger.info("Database initialized")
    configure_model_cache_env()
    enabled_raw = get_integration_setting("graph_sync", "enabled", "false")
    if str(enabled_raw).lower() in {"1", "true", "yes"}:
        async def fetch_nodes():
            return await db_client.knowledge_nodes.find({}, {"_id": 0}).to_list(1000)

        async def on_result(result):
            await db_client.graph_sync_status.insert_one(result)

        app.state.graph_sync_task = asyncio.create_task(run_sync_loop(fetch_nodes, on_result))
        logger.info("Neo4j graph sync loop started")

    warmup_enabled = get_integration_setting("rag_reranker", "warmup_enabled", "false")
    if str(warmup_enabled).lower() in {"1", "true", "yes"}:
        warmup_result = await asyncio.to_thread(warmup_models)
        logger.info("Reranker warmup completed", extra={"payload": warmup_result})

@app.on_event("shutdown")
async def shutdown_db_client():
    task = getattr(app.state, "graph_sync_task", None)
    if task:
        task.cancel()
    await close_database()
    logger.info("Database connection closed")
