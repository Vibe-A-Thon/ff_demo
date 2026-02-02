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


@router.post("/seed-comprehensive")
async def seed_comprehensive_data(
    current_user: dict = Depends(require_permission("seed:write")),
    db: DatabaseClient = Depends(get_db),
):
    """Seed comprehensive demo data for hackathon demo.
    
    Populates all collections with realistic data including:
    - Teams (3)
    - Agents (5)
    - Rules (5)
    - Battles (15)
    - Run Events (100+)
    - RSB Packages (2)
    - Knowledge Nodes (7)
    - RAG Documents (4)
    - Agent Artifacts (10)
    
    Returns:
        dict: Detailed seeding summary with counts per collection
    """
    from app.seed_data.demo_data_generator import generate_demo_data
    
    logger.info("Starting comprehensive data seed")
    
    # Generate all demo data
    data = generate_demo_data()
    
    # Clear existing data
    collections_to_clear = [
        "teams", "agents", "rules", "battles", "run_events",
        "rsb_packages", "knowledge_nodes", "rag_documents", "agent_artifacts"
    ]
    
    for coll_name in collections_to_clear:
        coll = getattr(db, coll_name, None)
        if coll:
            result = await coll.delete_many({})
            logger.info(f"Cleared {coll_name}: {result.deleted_count} documents")
    
    # Insert new data
    counts = {}
    
    # Teams
    if data["teams"]:
        await db.teams.insert_many(data["teams"])
        counts["teams"] = len(data["teams"])
    
    # Agents
    if data["agents"]:
        await db.agents.insert_many(data["agents"])
        counts["agents"] = len(data["agents"])
    
    # Rules
    if data["rules"]:
        await db.rules.insert_many(data["rules"])
        counts["rules"] = len(data["rules"])
    
    # Battles (Runs)
    if data["battles"]:
        await db.runs.insert_many(data["battles"])
        counts["battles"] = len(data["battles"])
    
    # Run Events
    if data["run_events"]:
        await db.run_events.insert_many(data["run_events"])
        counts["run_events"] = len(data["run_events"])
    
    # RSB Packages
    if data["rsb_packages"]:
        await db.rsb_packages.insert_many(data["rsb_packages"])
        counts["rsb_packages"] = len(data["rsb_packages"])
    
    # Knowledge Nodes
    if data["knowledge_nodes"]:
        await db.knowledge_nodes.insert_many(data["knowledge_nodes"])
        counts["knowledge_nodes"] = len(data["knowledge_nodes"])
    
    # RAG Documents
    if data["rag_documents"]:
        await db.rag_documents.insert_many(data["rag_documents"])
        counts["rag_documents"] = len(data["rag_documents"])
    
    # Agent Artifacts
    if data["agent_artifacts"]:
        await db.agent_artifacts.insert_many(data["agent_artifacts"])
        counts["agent_artifacts"] = len(data["agent_artifacts"])
    
    logger.info("Comprehensive seed completed", extra={"payload": counts})
    
    await record_audit(
        current_user.get("id", "unknown"),
        "seed.comprehensive_completed",
        "seed",
        "comprehensive",
        metadata=counts
    )
    
    return {
        "message": "Comprehensive demo data seeded successfully",
        "status": "success",
        "collections_seeded": counts,
        "total_documents": sum(counts.values())
    }


@router.delete("/clear-all-data")
async def clear_all_data(
    current_user: dict = Depends(require_permission("seed:write")),
    db: DatabaseClient = Depends(get_db),
):
    """Clear all data from database (use with caution!)."""
    
    collections = [
        "teams", "agents", "rules", "battles", "runs", "run_events",
        "rsb_packages", "knowledge_nodes", "rag_documents", "agent_artifacts"
    ]
    
    deleted_counts = {}
    for coll_name in collections:
        coll = getattr(db, coll_name, None)
        if coll:
            result = await coll.delete_many({})
            deleted_counts[coll_name] = result.deleted_count
    
    await record_audit(
        current_user.get("id", "unknown"),
        "seed.clear_all",
        "seed",
        "clear",
        metadata=deleted_counts
    )
    
    return {
        "message": "All data cleared",
        "deleted": deleted_counts,
        "total_deleted": sum(deleted_counts.values())
    }
