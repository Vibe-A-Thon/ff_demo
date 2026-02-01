"""Seed data routes.

Populate the database with demo data.
"""

import random
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from app.core.external_services import DatabaseClient, LLMClient
from app.core.logging_config import get_logger
from app.deps import get_db, get_llm_client
from app.models import Battle, KnowledgeNode, RAGDocument, RSBPackage, Rule
from app.rag_utils import get_embedding
from app.audit import record_audit
from app.security import require_permission

router = APIRouter()
logger = get_logger(__name__)

@router.post("/seed-data")
async def seed_data(
    current_user: dict = Depends(require_permission("seed:write")),
    db: DatabaseClient = Depends(get_db),
    llm_client: LLMClient | None = Depends(get_llm_client),
):
    """Seed demo data across collections.

    Args:
        db: Database client.
        llm_client: Optional LLM client.

    Returns:
        dict: Seeding summary.

    Raises:
        None: No explicit exceptions are raised.
    """
    await db.battles.delete_many({})
    await db.rules.delete_many({})
    await db.knowledge_nodes.delete_many({})
    await db.rsb_packages.delete_many({})
    await db.rag_documents.delete_many({})

    rules_data = [
        {"name": "VEL-001", "description": "Velocity check for rapid transactions", "rule_type": "velocity", "conditions": [{"field": "tx_count", "operator": ">", "value": 5}], "actions": [{"type": "flag", "severity": "high"}], "priority": 1, "status": "active"},
        {"name": "STR-042", "description": "Suspicious transaction pattern", "rule_type": "pattern", "conditions": [{"field": "amount", "operator": ">", "value": 10000}], "actions": [{"type": "block", "severity": "critical"}], "priority": 2, "status": "active"},
        {"name": "DEV-015", "description": "Device fingerprint mismatch", "rule_type": "device", "conditions": [{"field": "device_id", "operator": "!=", "value": "known"}], "actions": [{"type": "challenge", "severity": "medium"}], "priority": 3, "status": "active"},
        {"name": "GEO-008", "description": "Geolocation anomaly detection", "rule_type": "geo", "conditions": [{"field": "distance", "operator": ">", "value": 500}], "actions": [{"type": "flag", "severity": "medium"}], "priority": 4, "status": "draft"},
    ]

    created_rules = []
    for rule_data in rules_data:
        rule = Rule(**rule_data)
        await db.rules.insert_one(rule.model_dump())
        created_rules.append(rule.id)

    nodes_data = [
        {"node_type": "root", "name": "Blue Sentinel Core", "data": {"description": "Central defense system"}},
        {"node_type": "rule", "name": "Rule: VEL-001", "data": {"rule_id": created_rules[0]}},
        {"node_type": "rule", "name": "Rule: STR-042", "data": {"rule_id": created_rules[1]}},
        {"node_type": "pattern", "name": "Pattern: ATO-99", "data": {"pattern_type": "account_takeover"}},
        {"node_type": "compliance", "name": "Compliance: PCI-DSS", "data": {"standard": "PCI-DSS 4.0"}},
    ]

    created_nodes = []
    for node_data in nodes_data:
        node = KnowledgeNode(**node_data)
        await db.knowledge_nodes.insert_one(node.model_dump())
        created_nodes.append(node.id)

    root_id = created_nodes[0]
    for node_id in created_nodes[1:]:
        await db.knowledge_nodes.update_one({"id": root_id}, {"$addToSet": {"connections": node_id}})

    for i in range(8):
        evidence_node = KnowledgeNode(node_type="evidence", name="Evidence", data={"evidence_id": f"EV-{i:03d}"})
        await db.knowledge_nodes.insert_one(evidence_node.model_dump())
        parent_idx = random.randint(1, 4)
        if parent_idx < len(created_nodes):
            await db.knowledge_nodes.update_one({"id": created_nodes[parent_idx]}, {"$addToSet": {"connections": evidence_node.id}})

    rag_entries = [
        {"collection": "taxonomy", "title": "Account Takeover", "content": "ATO patterns include device change, new payee addition, and high-risk beneficiary transfers.", "metadata": {"category": "ATO"}},
        {"collection": "patterns", "title": "Velocity Fraud", "content": "Rapid transaction bursts over short windows often indicate automated fraud scripts.", "metadata": {"category": "velocity"}},
        {"collection": "rules", "title": "VEL-001", "content": "Flag accounts with more than 5 transfers within 10 minutes.", "metadata": {"team": "purple"}},
        {"collection": "explanations", "title": "Decision Rationale", "content": "Provide top three signals, rules triggered, and confidence statement.", "metadata": {"team": "gold"}},
    ]
    for entry in rag_entries:
        embedding = await get_embedding(entry["content"], llm_client=llm_client)
        doc = RAGDocument(**entry, embedding=embedding)
        await db.rag_documents.insert_one(doc.model_dump())

    for i in range(3):
        battle = Battle(
            scenario_name=f"Demo Battle {i+1}",
            status="completed" if i < 2 else "pending",
            parameters={"difficulty": "medium", "max_turns": 10},
            metrics={
                "success_rate": random.randint(70, 95),
                "money_at_risk": random.randint(5000, 50000),
                "time_to_immunity": max(1, 10 - i * 3),
                "patterns_learned": (i + 1) * 5,
            },
        )
        if i < 2:
            battle.completed_at = datetime.now(timezone.utc).isoformat()
        await db.battles.insert_one(battle.model_dump())

    rsb = RSBPackage(
        name="Fraud Detection Core v2.1",
        version="2.1.0",
        description="Core fraud detection rules and patterns",
        manifest={"rules": len(created_rules), "patterns": 5, "compliance": ["PCI-DSS", "SOX"]},
        rules=created_rules[:2],
        compliance_badges=["PCI-DSS", "SOX", "GDPR"],
    )
    await db.rsb_packages.insert_one(rsb.model_dump())

    logger.info(
        "seed.completed",
        extra={"payload": {"rules": len(created_rules), "nodes": len(created_nodes), "battles": 3}},
    )
    await record_audit(
        current_user.get("id", "unknown"),
        "seed.completed",
        "seed",
        "demo",
        metadata={
            "rules": len(created_rules),
            "nodes": len(created_nodes),
            "battles": 3,
            "rag_docs": len(rag_entries),
        },
    )
    return {
        "message": "Demo data seeded successfully",
        "rules": len(created_rules),
        "nodes": len(created_nodes),
        "battles": 3,
        "rag_docs": len(rag_entries),
    }
