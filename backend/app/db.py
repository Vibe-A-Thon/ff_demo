"""Database connection utilities and indexes."""

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING
from app.config import MONGO_URL, DB_NAME

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

async def init_database() -> None:
    """Initialize database connections and indexes.

    Args:
        None: This function takes no parameters.

    Returns:
        None: This function returns no value.

    Raises:
        None: No explicit exceptions are raised.
    """
    await db.command("ping")
    await db.users.create_index([("email", ASCENDING)], unique=True)
    await db.rules.create_index([("id", ASCENDING)], unique=True)
    await db.runs.create_index([("id", ASCENDING)], unique=True)
    await db.battles.create_index([("id", ASCENDING)], unique=True)
    await db.rsb_packages.create_index([("id", ASCENDING)], unique=True)
    await db.amc_packages.create_index([("id", ASCENDING)], unique=True)
    await db.amc_packages.create_index([("team_id", ASCENDING), ("created_at", ASCENDING)])
    await db.amc_states.create_index([("team_id", ASCENDING)], unique=True)
    await db.pep_packs.create_index([("id", ASCENDING)], unique=True)
    await db.pep_packs.create_index([("created_at", ASCENDING)])
    await db.brc_packages.create_index([("id", ASCENDING)], unique=True)
    await db.brc_packages.create_index([("run_id", ASCENDING), ("created_at", ASCENDING)])
    await db.evidence_packs.create_index([("id", ASCENDING)], unique=True)
    await db.knowledge_nodes.create_index([("id", ASCENDING)], unique=True)
    await db.rag_documents.create_index([("id", ASCENDING)], unique=True)
    await db.rag_documents.create_index([("collection", ASCENDING), ("created_at", ASCENDING)])
    await db.rag_media_documents.create_index([("id", ASCENDING)], unique=True)
    await db.rag_media_documents.create_index([("collection", ASCENDING), ("created_at", ASCENDING)])
    await db.rag_retrieval_logs.create_index([("created_at", ASCENDING)])
    await db.rag_cag_cache.create_index([("key", ASCENDING)], unique=True)
    await db.rag_cag_cache.create_index([("expires_at", ASCENDING)])
    await db.rag_cache_telemetry.create_index([("created_at", ASCENDING)])
    await db.rag_evaluation_alerts.create_index([("created_at", ASCENDING)])
    await db.graph_sync_status.create_index([("timestamp", ASCENDING)])
    await db.teams.create_index([("team_id", ASCENDING)], unique=True)
    await db.agents.create_index([("agent_id", ASCENDING)], unique=True)
    await db.agent_tasks.create_index([("task_id", ASCENDING)], unique=True)
    await db.agent_tasks.create_index([("run_id", ASCENDING), ("created_at", ASCENDING)])
    await db.agent_requests.create_index([("request_id", ASCENDING)], unique=True)
    await db.agent_artifacts.create_index([("artifact_id", ASCENDING)], unique=True)
    await db.agent_artifacts.create_index([("run_id", ASCENDING), ("created_at", ASCENDING)])
    await db.agent_artifacts.create_index([("task_id", ASCENDING), ("created_at", ASCENDING)])
    await db.agent_artifacts.create_index([("agent_id", ASCENDING), ("created_at", ASCENDING)])
    await db.run_events.create_index([("run_id", ASCENDING), ("created_at", ASCENDING)])
    await db.audit_logs.create_index([("target_id", ASCENDING), ("created_at", ASCENDING)])
    await db.llm_telemetry_events.create_index([("created_at", ASCENDING)])
    await db.llm_telemetry_events.create_index([("model_id", ASCENDING), ("created_at", ASCENDING)])
    await db.llm_telemetry.create_index([("model_id", ASCENDING), ("team_id", ASCENDING), ("agent_id", ASCENDING)])
    await db.quality_checks.create_index([("run_id", ASCENDING), ("created_at", ASCENDING)])
    await db.evaluations.create_index([("run_id", ASCENDING), ("created_at", ASCENDING)])
    await db.rag_evaluations.create_index([("created_at", ASCENDING)])
    await db.platform_settings.create_index([("key", ASCENDING)], unique=True)
    await db.approvals.create_index([("status", ASCENDING)])
    await db.approvals.create_index([("resource_type", ASCENDING), ("resource_id", ASCENDING)])

async def close_database() -> None:
    """Close the database connection.

    Args:
        None: This function takes no parameters.

    Returns:
        None: This function returns no value.

    Raises:
        None: No explicit exceptions are raised.
    """
    client.close()
