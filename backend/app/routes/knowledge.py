"""Knowledge graph node routes.

Manage knowledge nodes and their connections.
"""

from fastapi import APIRouter, HTTPException, Depends
from app.db import db
from app.models import KnowledgeNode, KnowledgeNodeCreate
from app.core.logging_config import get_logger
from app.audit import record_audit
from app.security import require_permission
from app.graph_sync_neo4j import health_check, sync_nodes

router = APIRouter()
logger = get_logger(__name__)

@router.get("/knowledge-nodes")
async def get_knowledge_nodes(current_user: dict = Depends(require_permission("knowledge:read"))):
    """List all knowledge nodes.

    Args:
        None: This endpoint takes no parameters.

    Returns:
        list[dict]: Knowledge node documents.

    Raises:
        None: No explicit exceptions are raised.
    """
    nodes = await db.knowledge_nodes.find({}, {"_id": 0}).to_list(500)
    await record_audit(
        current_user.get("id", "unknown"),
        "knowledge.nodes.list",
        "knowledge_node",
        "list",
    )
    return nodes

@router.post("/knowledge-nodes")
async def create_knowledge_node(node_data: KnowledgeNodeCreate, current_user: dict = Depends(require_permission("knowledge:write"))):
    """Create a knowledge node.

    Args:
        node_data: Payload describing the node.

    Returns:
        KnowledgeNode: Created node.

    Raises:
        None: No explicit exceptions are raised.
    """
    node = KnowledgeNode(**node_data.model_dump())
    await db.knowledge_nodes.insert_one(node.model_dump())
    await record_audit(
        current_user.get("id", "unknown"),
        "knowledge.node.created",
        "knowledge_node",
        node.id,
        metadata={"node_type": node.node_type, "name": node.name},
    )
    logger.info(
        "knowledge.node.created",
        extra={"payload": {"node_id": node.id, "node_type": node.node_type, "name": node.name}},
    )
    return node

@router.put("/knowledge-nodes/{node_id}/connect/{target_id}")
async def connect_nodes(node_id: str, target_id: str, current_user: dict = Depends(require_permission("knowledge:write"))):
    """Connect one node to another.

    Args:
        node_id: Source node identifier.
        target_id: Target node identifier.

    Returns:
        dict: Connection result.

    Raises:
        HTTPException: If the source node does not exist.
    """
    result = await db.knowledge_nodes.update_one(
        {"id": node_id},
        {"$addToSet": {"connections": target_id}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Node not found")
    await record_audit(
        current_user.get("id", "unknown"),
        "knowledge.node.connected",
        "knowledge_node",
        node_id,
        metadata={"target_id": target_id},
    )
    logger.info(
        "knowledge.node.connected",
        extra={"payload": {"node_id": node_id, "target_id": target_id}},
    )
    return {"message": "Nodes connected"}

@router.delete("/knowledge-nodes/{node_id}")
async def delete_knowledge_node(node_id: str, current_user: dict = Depends(require_permission("knowledge:write"))):
    """Delete a knowledge node.

    Args:
        node_id: Node identifier to delete.

    Returns:
        dict: Deletion result.

    Raises:
        HTTPException: If the node does not exist.
    """
    result = await db.knowledge_nodes.delete_one({"id": node_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Node not found")
    await db.knowledge_nodes.update_many({}, {"$pull": {"connections": node_id}})
    await record_audit(
        current_user.get("id", "unknown"),
        "knowledge.node.deleted",
        "knowledge_node",
        node_id,
    )
    logger.info("knowledge.node.deleted", extra={"payload": {"node_id": node_id}})
    return {"message": "Node deleted"}


@router.post("/knowledge-nodes/sync-neo4j")
async def sync_knowledge_nodes(current_user: dict = Depends(require_permission("knowledge:write"))):
    """Sync knowledge nodes to Neo4j.

    Returns:
        dict: Sync summary.
    """
    nodes = await db.knowledge_nodes.find({}, {"_id": 0}).to_list(500)
    result = sync_nodes(nodes)
    await record_audit(
        current_user.get("id", "unknown"),
        "knowledge.nodes.sync",
        "knowledge_node",
        "neo4j",
        metadata=result,
    )
    logger.info("knowledge.nodes.sync", extra={"payload": result})
    return result


@router.get("/knowledge-nodes/neo4j-health")
async def neo4j_health(current_user: dict = Depends(require_permission("knowledge:read"))):
    """Check Neo4j health."""
    result = await health_check()
    await record_audit(
        current_user.get("id", "unknown"),
        "knowledge.neo4j.health",
        "knowledge_node",
        "neo4j",
        metadata=result,
    )
    return result


@router.get("/knowledge-nodes/graph-sync-status")
async def graph_sync_status(current_user: dict = Depends(require_permission("knowledge:read"))):
    """Return recent graph sync status entries."""
    records = await db.graph_sync_status.find({}, {"_id": 0}).sort("timestamp", -1).to_list(20)
    await record_audit(
        current_user.get("id", "unknown"),
        "knowledge.nodes.sync.status",
        "knowledge_node",
        "neo4j",
        metadata={"count": len(records)},
    )
    return {"items": records}
