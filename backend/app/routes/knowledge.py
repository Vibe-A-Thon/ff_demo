from fastapi import APIRouter, HTTPException
from app.db import db
from app.models import KnowledgeNode, KnowledgeNodeCreate
from app.core.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.get("/knowledge-nodes")
async def get_knowledge_nodes():
    nodes = await db.knowledge_nodes.find({}, {"_id": 0}).to_list(500)
    return nodes

@router.post("/knowledge-nodes")
async def create_knowledge_node(node_data: KnowledgeNodeCreate):
    node = KnowledgeNode(**node_data.model_dump())
    await db.knowledge_nodes.insert_one(node.model_dump())
    logger.info(
        "knowledge.node.created",
        extra={"payload": {"node_id": node.id, "node_type": node.node_type, "name": node.name}},
    )
    return node

@router.put("/knowledge-nodes/{node_id}/connect/{target_id}")
async def connect_nodes(node_id: str, target_id: str):
    result = await db.knowledge_nodes.update_one(
        {"id": node_id},
        {"$addToSet": {"connections": target_id}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Node not found")
    logger.info(
        "knowledge.node.connected",
        extra={"payload": {"node_id": node_id, "target_id": target_id}},
    )
    return {"message": "Nodes connected"}

@router.delete("/knowledge-nodes/{node_id}")
async def delete_knowledge_node(node_id: str):
    result = await db.knowledge_nodes.delete_one({"id": node_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Node not found")
    await db.knowledge_nodes.update_many({}, {"$pull": {"connections": node_id}})
    logger.info("knowledge.node.deleted", extra={"payload": {"node_id": node_id}})
    return {"message": "Node deleted"}
