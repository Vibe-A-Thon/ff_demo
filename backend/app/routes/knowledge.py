from fastapi import APIRouter, HTTPException
from app.db import db
from app.models import KnowledgeNode, KnowledgeNodeCreate

router = APIRouter()

@router.get("/knowledge-nodes")
async def get_knowledge_nodes():
    nodes = await db.knowledge_nodes.find({}, {"_id": 0}).to_list(500)
    return nodes

@router.post("/knowledge-nodes")
async def create_knowledge_node(node_data: KnowledgeNodeCreate):
    node = KnowledgeNode(**node_data.model_dump())
    await db.knowledge_nodes.insert_one(node.model_dump())
    return node

@router.put("/knowledge-nodes/{node_id}/connect/{target_id}")
async def connect_nodes(node_id: str, target_id: str):
    result = await db.knowledge_nodes.update_one(
        {"id": node_id},
        {"$addToSet": {"connections": target_id}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Node not found")
    return {"message": "Nodes connected"}

@router.delete("/knowledge-nodes/{node_id}")
async def delete_knowledge_node(node_id: str):
    result = await db.knowledge_nodes.delete_one({"id": node_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Node not found")
    await db.knowledge_nodes.update_many({}, {"$pull": {"connections": node_id}})
    return {"message": "Node deleted"}
