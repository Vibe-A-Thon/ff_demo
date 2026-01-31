from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from app.config import APP_NAME, APP_VERSION, DEBUG_MODE, API_PREFIX, CORS_ORIGINS
from app.db import init_database, close_database
from app.routes import (
    auth,
    me,
    runs,
    xai,
    graph,
    tools,
    battles,
    rules,
    rsb,
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
    websocket,
)

app = FastAPI(title=APP_NAME, version=APP_VERSION, debug=DEBUG_MODE)

app.get("/")(root.root)

for router in [
    auth.router,
    me.router,
    runs.router,
    xai.router,
    graph.router,
    tools.router,
    battles.router,
    rules.router,
    rsb.router,
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
    root.router,
    evaluation.router,
]:
    app.include_router(router, prefix=API_PREFIX)

app.include_router(websocket.router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_db_client():
    await init_database()

@app.on_event("shutdown")
async def shutdown_db_client():
    await close_database()
