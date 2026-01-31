from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING
from app.config import MONGO_URL, DB_NAME

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

async def init_database() -> None:
    await db.command("ping")
    await db.users.create_index([("email", ASCENDING)], unique=True)
    await db.rules.create_index([("id", ASCENDING)], unique=True)
    await db.runs.create_index([("id", ASCENDING)], unique=True)
    await db.battles.create_index([("id", ASCENDING)], unique=True)
    await db.rsb_packages.create_index([("id", ASCENDING)], unique=True)
    await db.evidence_packs.create_index([("id", ASCENDING)], unique=True)
    await db.knowledge_nodes.create_index([("id", ASCENDING)], unique=True)
    await db.rag_documents.create_index([("id", ASCENDING)], unique=True)
    await db.rag_documents.create_index([("collection", ASCENDING), ("created_at", ASCENDING)])
    await db.teams.create_index([("team_id", ASCENDING)], unique=True)
    await db.agents.create_index([("agent_id", ASCENDING)], unique=True)
    await db.agent_tasks.create_index([("task_id", ASCENDING)], unique=True)
    await db.agent_tasks.create_index([("run_id", ASCENDING), ("created_at", ASCENDING)])
    await db.agent_requests.create_index([("request_id", ASCENDING)], unique=True)
    await db.run_events.create_index([("run_id", ASCENDING), ("created_at", ASCENDING)])
    await db.audit_logs.create_index([("target_id", ASCENDING), ("created_at", ASCENDING)])
    await db.quality_checks.create_index([("run_id", ASCENDING), ("created_at", ASCENDING)])
    await db.evaluations.create_index([("run_id", ASCENDING), ("created_at", ASCENDING)])
    await db.approvals.create_index([("status", ASCENDING)])
    await db.approvals.create_index([("resource_type", ASCENDING), ("resource_id", ASCENDING)])

async def close_database() -> None:
    client.close()
