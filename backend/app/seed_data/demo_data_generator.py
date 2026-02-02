"""
Comprehensive MongoDB Seed Script for Fraud Forge Demo
Populates all collections with realistic demo data for hackathon presentation
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any
import random
import uuid

def generate_demo_data() -> Dict[str, List[Dict[str, Any]]]:
    """Generate comprehensive demo data for all collections."""
    
    # Teams
    teams = [
        {
            "team_id": "purple_defenders",
            "internal_name": "Purple Team - Defenders",
            "display_name": "Purple Defenders",
            "description": "Elite defense team specializing in fraud prevention",
            "operating_mode": "HITL",
            "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "metrics": {"total_battles": 45, "win_rate": 0.87, "avg_response_time": 2.3}
        },
        {
            "team_id": "gold_advisors",
            "internal_name": "Gold Team - XAI Advisors",
            "display_name": "Gold Advisors",
            "description": "Explainable AI specialists providing transparency",
            "operating_mode": "HOTL",
            "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "metrics": {"total_explanations": 1250, "clarity_score": 0.92}
        },
        {
            "team_id": "red_attackers",
            "internal_name": "Red Team - Attackers",
            "display_name": "Red Attackers",
            "description": "Adversarial testing team simulating sophisticated attacks",
            "operating_mode": "HOTL",
            "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "metrics": {"total_attacks": 567, "success_rate": 0.13}
        }
    ]
    
    # Agents
    agents = [
        # Purple Team
        {"agent_id": "blue-sentinel-01", "agent_name": "Blue Sentinel", "team_id": "purple_defenders", "role": "blue", "status": "active", "operating_mode": "HITL", "last_run": "2026-02-01T14:30:00Z", "total_runs": 45, "success_rate": 0.89},
        {"agent_id": "guardian-shield-02", "agent_name": "Guardian Shield", "team_id": "purple_defenders", "role": "blue", "status": "active", "operating_mode": "HITL", "last_run": "2026-02-01T16:45:00Z", "total_runs": 38, "success_rate": 0.84},
        
        # Gold Team
        {"agent_id": "xai-oracle-01", "agent_name": "XAI Oracle", "team_id": "gold_advisors", "role": "gold", "status": "active", "operating_mode": "HOTL", "last_run": "2026-02-02T10:15:00Z", "total_runs": 120, "explanations_generated": 1250},
        
        # Red Team
        {"agent_id": "red-phantom-01", "agent_name": "Red Phantom", "team_id": "red_attackers", "role": "red", "status": "active", "operating_mode": "HOTL", "last_run": "2026-02-02T11:00:00Z", "total_runs": 67, "attack_success_rate": 0.12},
        {"agent_id": "crimson-viper-02", "agent_name": "Crimson Viper", "team_id": "red_attackers", "role": "red", "status": "active", "operating_mode": "HOTL", "last_run": "2026-02-02T09:30:00Z", "total_runs": 55, "attack_success_rate": 0.15}
    ]
    
    # Rules
    rules = [
        {
            "id": str(uuid.uuid4()),
            "name": "VEL-001",
            "description": "Velocity check for rapid transactions",
            "rule_type": "velocity",
            "conditions": [{"field": "tx_count", "operator": ">", "value": 5, "timeframe": "10m"}],
            "actions": [{"type": "flag", "severity": "high"}],
            "priority": 1,
            "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "team_id": "purple_defenders",
            "agent_id": "blue-sentinel-01"
        },
        {
            "id": str(uuid.uuid4()),
            "name": "STR-042",
            "description": "Suspicious transaction pattern - Round dollar amounts",
            "rule_type": "pattern",
            "conditions": [{"field": "amount", "operator": "matches", "value": "\\d+00.00$"}],
            "actions": [{"type": "block", "severity": "critical"}],
            "priority": 2,
            "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "team_id": "purple_defenders",
            "agent_id": "blue-sentinel-01"
        },
        {
            "id": str(uuid.uuid4()),
            "name": "DEV-015",
            "description": "Device fingerprint mismatch detection",
            "rule_type": "device",
            "conditions": [{"field": "device_id", "operator": "!=", "value": "known"}],
            "actions": [{"type": "challenge", "severity": "medium"}],
            "priority": 3,
            "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "team_id": "purple_defenders",
            "agent_id": "guardian-shield-02"
        },
        {
            "id": str(uuid.uuid4()),
            "name": "GEO-008",
            "description": "Geolocation anomaly - Impossible travel",
            "rule_type": "geo",
            "conditions": [{"field": "distance_km", "operator": ">", "value": 500}, {"field": "time_diff_hours", "operator": "<", "value": 4}],
            "actions": [{"type": "flag", "severity": "high"}],
            "priority": 4,
            "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "team_id": "purple_defenders",
            "agent_id": "guardian-shield-02"
        },
        {
            "id": str(uuid.uuid4()),
            "name": "ATO-099",
            "description": "Account takeover indicators",
            "rule_type": "behavioral",
            "conditions": [
                {"field": "new_payee_added", "operator": "==", "value": True},
                {"field": "high_risk_beneficiary", "operator": "==", "value": True}
            ],
            "actions": [{"type": "block", "severity": "critical"}, {"type": "alert_user"}],
            "priority": 1,
            "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "team_id": "purple_defenders",
            "agent_id": "blue-sentinel-01"
        }
    ]
    
    # Battles (Run Events)
    battles = []
    run_events = []
    current_time = datetime.now(timezone.utc)
    
    for i in range(15):
        battle_time = current_time - timedelta(days=i, hours=random.randint(0, 23))
        battle_id = f"battle-{uuid.uuid4().hex[:12]}"
        
        status = "completed" if i < 12 else "running" if i == 12 else "pending"
        success_rate = random.uniform(0.75, 0.95) if status == "completed" else 0.0
        
        battle = {
            "id": battle_id,
            "run_id": battle_id,
            "scenario_name": f"Battle {15-i}: {random.choice(['Account Takeover', 'Velocity Fraud', 'Money Mule', 'Card Fraud', 'Identity Theft'])}",
            "status": status,
            "started_at": battle_time.isoformat(),
            "completed_at": (battle_time + timedelta(minutes=random.randint(5, 45))).isoformat() if status == "completed" else None,
            "parameters": {
                "difficulty": random.choice(["easy", "medium", "hard"]),
                "max_turns": 20,
                "transaction_count": random.randint(50, 200)
            },
            "metrics": {
                "success_rate": success_rate,
                "money_at_risk": random.randint(10000, 500000),
                "money_saved": int(random.randint(10000, 500000) * success_rate),
                "time_to_immunity": random.randint(3, 15) if status == "completed" else 0,
                "patterns_learned": random.randint(2, 8) if status == "completed" else 0,
                "transactions_analyzed": random.randint(50, 200),
                "threats_detected": random.randint(5, 25),
                "false_positives": random.randint(1, 5),
                "avg_response_time_ms": random.randint(100, 500)
            },
            "teams": {
                "purple": "purple_defenders",
                "gold": "gold_advisors",
                "red": "red_attackers"
            },
            "agents": {
                "blue": ["blue-sentinel-01", "guardian-shield-02"],
                "gold": ["xai-oracle-01"],
                "red": ["red-phantom-01", "crimson-viper-02"]
            }
        }
        battles.append(battle)
        
        # Generate run events for completed battles
        if status == "completed":
            num_events = random.randint(10, 30)
            for j in range(num_events):
                event_time = battle_time + timedelta(minutes=j * 2)
                event = {
                    "run_id": battle_id,
                    "team_id": random.choice(["purple_defenders", "gold_advisors", "red_attackers"]),
                    "agent_id": random.choice([a["agent_id"] for a in agents]),
                    "event_type": random.choice(["action", "decision", "alert", "block", "flag"]),
                    "timestamp": event_time.isoformat(),
                    "data": {
                        "action": random.choice(["block", "allow", "flag", "challenge"]),
                        "transaction_id": f"TX-{uuid.uuid4().hex[:8]}",
                        "amount": random.randint(100, 50000),
                        "confidence": random.uniform(0.6, 0.99),
                        "rule_triggered": random.choice([r["name"] for r in rules])
                    },
                    "metrics": {
                        "processing_time_ms": random.randint(50, 300),
                        "confidence_score": random.uniform(0.6, 0.99)
                    }
                }
                run_events.append(event)
    
    # RSB Packages
    rsb_packages = [
        {
            "id": str(uuid.uuid4()),
            "name": "Fraud Detection Core v2.1",
            "version": "2.1.0",
            "description": "Core fraud detection rules and patterns for financial institutions",
            "manifest": {
                "rules": len(rules),
                "patterns": 8,
                "compliance": ["PCI-DSS", "SOX", "GDPR"]
            },
            "rules": [r["id"] for r in rules[:3]],
            "status": "published",
            "compliance_badges": ["PCI-DSS", "SOX", "GDPR"],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "downloads": 847,
            "rating": 4.8
        },
        {
            "id": str(uuid.uuid4()),
            "name": "ATO Defense Pack v1.5",
            "version": "1.5.2",
            "description": "Account takeover prevention rules and behavioral patterns",
            "manifest": {
                "rules": 12,
                "patterns": 5,
                "compliance": ["FFIEC", "GLBA"]
            },
            "rules": [rules[4]["id"]],
            "status": "published",
            "compliance_badges": ["FFIEC", "GLBA"],
            "created_at": (datetime.now(timezone.utc) - timedelta(days=30)).isoformat(),
            "downloads": 1203,
            "rating": 4.9
        }
    ]
    
    # Knowledge Nodes
    knowledge_nodes = [
        {"id": str(uuid.uuid4()), "node_type": "root", "name": "Blue Sentinel Core", "data": {"description": "Central defense system"}, "connections": []},
        {"id": str(uuid.uuid4()), "node_type": "rule", "name": f"Rule: {rules[0]['name']}", "data": {"rule_id": rules[0]["id"], "effectiveness": 0.92}},
        {"id": str(uuid.uuid4()), "node_type": "rule", "name": f"Rule: {rules[1]['name']}", "data": {"rule_id": rules[1]["id"], "effectiveness": 0.88}},
        {"id": str(uuid.uuid4()), "node_type": "pattern", "name": "Pattern: ATO-99", "data": {"pattern_type": "account_takeover", "confidence": 0.91}},
        {"id": str(uuid.uuid4()), "node_type": "compliance", "name": "Compliance: PCI-DSS", "data": {"standard": "PCI-DSS 4.0", "status": "compliant"}},
        {"id": str(uuid.uuid4()), "node_type": "evidence", "name": "Evidence: Transaction Burst", "data": {"evidence_type": "velocity", "severity": "high"}},
        {"id": str(uuid.uuid4()), "node_type": "evidence", "name": "Evidence: Device Change", "data": {"evidence_type": "behavioral", "severity": "medium"}},
    ]
    
    # RAG Documents
    rag_documents = [
        {
            "id": str(uuid.uuid4()),
            "collection": "taxonomy",
            "title": "Account Takeover (ATO)",
            "content": "ATO attacks involve unauthorized access to legitimate user accounts. Common indicators include: device fingerprint changes, new payee additions, high-risk beneficiary transfers, unusual login locations, and password reset requests.",
            "metadata": {"category": "ATO", "priority": "high"},
            "embedding": [random.random() for _ in range(384)]  # Mock embedding
        },
        {
            "id": str(uuid.uuid4()),
            "collection": "patterns",
            "title": "Velocity Fraud Patterns",
            "content": "Velocity fraud is characterized by rapid transaction bursts over short time windows, often indicating automated fraud scripts or bot activity. Monitor for 5+ transactions within 10 minutes, especially with round dollar amounts.",
            "metadata": {"category": "velocity", "priority": "high"},
            "embedding": [random.random() for _ in range(384)]
        },
        {
            "id": str(uuid.uuid4()),
            "collection": "rules",
            "title": "VEL-001 Implementation",
            "content": "Rule VEL-001 flags accounts with more than 5 transfers within 10 minutes. This rule has proven 92% effective in catching automated fraud attempts while maintaining a false positive rate below 2%.",
            "metadata": {"team": "purple_defenders", "rule_id": rules[0]["id"]},
            "embedding": [random.random() for _ in range(384)]
        },
        {
            "id": str(uuid.uuid4()),
            "collection": "explanations",
            "title": "XAI Decision Rationale Template",
            "content": "All fraud decisions must include: (1) Top 3 triggering signals with confidence scores, (2) Rules triggered and their severity levels, (3) Overall confidence statement with recommended action, (4) Alternative interpretations if confidence < 0.8.",
            "metadata": {"team": "gold_advisors", "template": "decision_explanation"},
            "embedding": [random.random() for _ in range(384)]
        }
    ]
    
    # Agent Artifacts (memories)
    agent_artifacts = []
    for battle in battles[:10]:  # Add artifacts for completed battles
        if battle["status"] == "completed":
            artifact = {
                "run_id": battle["id"],
                "team_id": "purple_defenders",
                "agent_id": "blue-sentinel-01",
                "artifact_type": "lesson",
                "content": {
                    "lesson": f"Learned pattern from {battle['scenario_name']}",
                    "effectiveness": random.uniform(0.75, 0.95),
                    "patterns_identified": random.randint(2, 5)
                },
                "created_at": battle["completed_at"],
                "metadata": {
                    "battle_id": battle["id"],
                    "success_rate": battle["metrics"]["success_rate"]
                }
            }
            agent_artifacts.append(artifact)
    
    return {
        "teams": teams,
        "agents": agents,
        "rules": rules,
        "battles": battles,
        "run_events": run_events,
        "rsb_packages": rsb_packages,
        "knowledge_nodes": knowledge_nodes,
        "rag_documents": rag_documents,
        "agent_artifacts": agent_artifacts
    }


# Collection schemas for reference
COLLECTION_SCHEMAS = {
    "teams": "team_id, internal_name, display_name, description, operating_mode, status, created_at, metrics",
    "agents": "agent_id, agent_name, team_id, role, status, operating_mode, last_run, total_runs",
    "rules": "id, name, description, rule_type, conditions, actions, priority, status, created_at, team_id",
    "battles": "id, run_id, scenario_name, status, started_at, completed_at, parameters, metrics, teams, agents",
    "run_events": "run_id, team_id, agent_id, event_type, timestamp, data, metrics",
    "rsb_packages": "id, name, version, description, manifest, rules, status, compliance_badges, created_at",
    "knowledge_nodes": "id, node_type, name, data, connections",
    "rag_documents": "id, collection, title, content, metadata, embedding",
    "agent_artifacts": "run_id, team_id, agent_id, artifact_type, content, created_at, metadata"
}


if __name__ == "__main__":
    # Generate and print sample data
    data = generate_demo_data()
    print(f"Generated demo data:")
    for collection, items in data.items():
        print(f"  - {collection}: {len(items)} items")
