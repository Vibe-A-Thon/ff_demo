"""Demo AMC Generator - Creates sample AMC files for hackathon demonstration.

This script generates believable AMC packages with realistic stats, 
distilled lessons, and team evolution data for demo purposes.
"""

from __future__ import annotations

import io
import json
import hashlib
import zipfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4
import random


def _sha256(content: str | bytes) -> str:
    """Compute SHA-256 hash."""
    if isinstance(content, str):
        content = content.encode()
    return f"sha256:{hashlib.sha256(content).hexdigest()}"


def _generate_semantic_memory(team_id: str, count: int = 20) -> List[Dict[str, Any]]:
    """Generate demo semantic memory entries."""
    topics = ["mule", "ato", "velocity", "graph", "device", "behavioral", "social_engineering"]
    lessons = [
        "Mule networks exhibit fan-in/fan-out patterns over 24-72h windows.",
        "ATO attacks preceded by credential validation from proxy IPs.",
        "Velocity spikes + new device = 3.5x fraud indicator.",
        "Graph analysis reveals hidden connections in money movement.",
        "Device fingerprint anomalies correlate with synthetic identities.",
        "Behavioral deviation from baseline indicates compromise.",
        "Social engineering attacks target support channels first.",
        "Multi-hop transactions obscure true beneficiary.",
        "Session anomalies indicate credential sharing or theft.",
        "Geo-velocity impossibilities signal VPN/proxy usage.",
        "New payee + high amount = elevated risk factor.",
        "Cross-border transactions with timing anomalies flag mules.",
        "Onboarding velocity spikes indicate synthetic ID farms.",
        "Device clustering reveals bot networks.",
        "Dormant account reactivation patterns signal ATO.",
    ]
    
    entries = []
    for i in range(count):
        days_ago = random.randint(1, 180)
        entry = {
            "id": f"SM-{uuid4().hex[:8].upper()}",
            "topic": random.choice(topics),
            "lesson": random.choice(lessons),
            "tags": random.sample(["graph", "velocity", "device", "geo", "behavioral"], k=random.randint(1, 3)),
            "confidence": round(random.uniform(0.65, 0.95), 2),
            "created_at": (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat(),
        }
        entries.append(entry)
    return entries


def _generate_episodic_memory(team_id: str, count: int = 10) -> List[Dict[str, Any]]:
    """Generate demo episodic memory entries."""
    event_types = ["battle_outcome", "investigation_complete", "rule_deployed", "alert_resolved"]
    results = ["mitigated", "blocked", "escalated", "compromised"]
    
    entries = []
    for i in range(count):
        days_ago = random.randint(1, 90)
        entry = {
            "id": f"EM-{uuid4().hex[:8].upper()}",
            "event_type": random.choice(event_types),
            "summary": f"Event {i+1}: Team response to coordinated attack pattern.",
            "signals": random.sample(["velocity_spike", "device_reuse", "geo_anomaly", "graph_link"], k=random.randint(1, 2)),
            "result": random.choice(results),
            "created_at": (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat(),
        }
        entries.append(entry)
    return entries


def _generate_procedural_memory(team_id: str) -> Dict[str, Any]:
    """Generate demo procedural memory."""
    return {
        "playbooks": [
            {
                "name": "ATO Investigation",
                "version": "2.1.0",
                "steps": [
                    "Collect device and session signals",
                    "Check velocity patterns",
                    "Analyze geo-location consistency",
                    "Score risk using ML model",
                    "Route high-risk to manual review"
                ]
            },
            {
                "name": "Mule Detection",
                "version": "1.5.0",
                "steps": [
                    "Identify fan-in/fan-out patterns",
                    "Check account age and activity",
                    "Analyze transaction timing",
                    "Graph link analysis",
                    "Score and alert"
                ]
            }
        ],
        "policies": {
            "max_false_positive_rate": 0.02,
            "min_detection_rate": 0.95,
            "escalation_threshold": 0.85
        }
    }


def _generate_agent_profile(agent_id: str, team_id: str, name: str, role: str) -> Dict[str, Any]:
    """Generate demo agent profile."""
    return {
        "agent_id": agent_id,
        "name": name,
        "role": role,
        "team_id": team_id,
        "capabilities": [
            "pattern_detection",
            "graph_reasoning",
            "case_summarization",
            "signal_ranking"
        ],
        "memory_stats": {
            "semantic_items": random.randint(500, 2000),
            "episodic_items": random.randint(100, 500),
            "procedural_rules": random.randint(20, 80),
            "last_distilled_at": datetime.now(timezone.utc).isoformat()
        },
        "evolution": {
            "evolution_level": random.randint(5, 15),
            "battles_participated": random.randint(20, 100),
            "win_rate": round(random.uniform(0.65, 0.90), 2),
            "last_upgrade": (datetime.now(timezone.utc) - timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d")
        }
    }


def _generate_distilled_lessons_md(team_name: str, semantic: List[Dict[str, Any]]) -> str:
    """Generate human-readable distilled lessons markdown."""
    lines = [
        f"# {team_name} — Distilled Lessons",
        "",
        f"**Last Updated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "## Top Learned Patterns",
        "",
    ]
    
    for i, entry in enumerate(semantic[:5], 1):
        lines.append(f"### {i}. {entry['topic'].replace('_', ' ').title()}")
        lines.append(f"> {entry['lesson']}")
        lines.append(f"- **Confidence:** {entry['confidence']:.0%}")
        lines.append(f"- **Tags:** {', '.join(entry['tags'])}")
        lines.append("")
    
    lines.extend([
        "---",
        "",
        "## Evolution Summary",
        "",
        "This agent has evolved through multiple battles, learning to detect:",
        "- Mule network patterns with graph analysis",
        "- ATO attacks through behavioral anomaly detection",
        "- Velocity abuse with device correlation",
        "",
        "*All content is bank-neutral and PII-free.*"
    ])
    
    return "\n".join(lines)


def _generate_team_xai_summary(team_name: str) -> str:
    """Generate team XAI summary markdown."""
    return f"""# {team_name} — Explainability Summary

## Decision Transparency

This team uses a multi-signal approach combining:
- **Graph Analysis**: Network patterns in transaction flows
- **Behavioral Modeling**: Deviation from established baselines
- **Velocity Signals**: Timing patterns in activities
- **Device Intelligence**: Fingerprint correlation and anomalies

## Key Strengths
1. High precision in mule detection (92% accuracy)
2. Fast adaptation to new attack vectors
3. Excellent coordination between agents

## Areas for Improvement
1. Reduce false positives in low-volume segments
2. Improve detection latency for real-time scenarios

---
*Generated for compliance and transparency.*
"""


def generate_demo_amc(
    team_id: str = "blue",
    team_version: str = "1.2.0",
    env_tag: str = "sandbox",
    include_models: bool = False,
    include_battle_refs: bool = True,
) -> bytes:
    """
    Generate a complete demo AMC package.
    
    Returns:
        bytes: The AMC package as a ZIP archive
    """
    team_names = {
        "blue": "Blue Team",
        "red": "Red Team",
        "purple": "Purple Team",
        "green": "Green Team",
        "black": "Black Team",
        "orange": "Orange Team",
        "gold": "Gold Team",
        "white": "White Team",
    }
    
    team_name = team_names.get(team_id.lower(), f"{team_id.title()} Team")
    team_id_upper = f"TEAM-{team_id.upper()}"
    
    # Generate agent data
    agents = [
        {"id": f"A-{team_id.upper()}-001", "name": f"{team_name} Orchestrator", "role": "Orchestrator"},
        {"id": f"A-{team_id.upper()}-002", "name": f"{team_name} Detector", "role": "Detection Analyst"},
        {"id": f"A-{team_id.upper()}-003", "name": f"{team_name} Responder", "role": "Response Coordinator"},
    ]
    
    # Build file contents
    files: Dict[str, bytes] = {}
    hashes: Dict[str, str] = {}
    
    # Team profile
    team_profile = {
        "team_id": team_id_upper,
        "team_name": team_name,
        "version": team_version,
        "agents": len(agents),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "evolution": {
            "battles_total": random.randint(50, 200),
            "win_rate": round(random.uniform(0.70, 0.88), 2),
            "evolution_level": random.randint(8, 18),
        },
    }
    team_profile_json = json.dumps(team_profile, indent=2)
    files["team/team_profile.json"] = team_profile_json.encode()
    hashes["team/team_profile.json"] = _sha256(team_profile_json)
    
    # Team XAI summary
    team_xai = _generate_team_xai_summary(team_name)
    files["team/xai/team_xai_summary.md"] = team_xai.encode()
    hashes["team/xai/team_xai_summary.md"] = _sha256(team_xai)
    
    # Agent files
    manifest_agents = []
    for agent in agents:
        agent_path = f"agents/{agent['id']}"
        
        # Agent profile
        profile = _generate_agent_profile(agent["id"], team_id_upper, agent["name"], agent["role"])
        profile_json = json.dumps(profile, indent=2)
        files[f"{agent_path}/agent_profile.json"] = profile_json.encode()
        hashes[f"{agent_path}/agent_profile.json"] = _sha256(profile_json)
        
        # Memory
        semantic = _generate_semantic_memory(team_id)
        semantic_jsonl = "\n".join(json.dumps(e) for e in semantic)
        files[f"{agent_path}/memory/semantic_memory.jsonl"] = semantic_jsonl.encode()
        hashes[f"{agent_path}/memory/semantic_memory.jsonl"] = _sha256(semantic_jsonl)
        
        episodic = _generate_episodic_memory(team_id)
        episodic_jsonl = "\n".join(json.dumps(e) for e in episodic)
        files[f"{agent_path}/memory/episodic_memory.jsonl"] = episodic_jsonl.encode()
        hashes[f"{agent_path}/memory/episodic_memory.jsonl"] = _sha256(episodic_jsonl)
        
        procedural = _generate_procedural_memory(team_id)
        procedural_json = json.dumps(procedural, indent=2)
        files[f"{agent_path}/memory/procedural_memory.json"] = procedural_json.encode()
        hashes[f"{agent_path}/memory/procedural_memory.json"] = _sha256(procedural_json)
        
        distilled_md = _generate_distilled_lessons_md(agent["name"], semantic)
        files[f"{agent_path}/memory/distilled_lessons.md"] = distilled_md.encode()
        hashes[f"{agent_path}/memory/distilled_lessons.md"] = _sha256(distilled_md)
        
        # Memory index
        memory_index = {
            "semantic_count": len(semantic),
            "episodic_count": len(episodic),
            "procedural_count": len(procedural.get("playbooks", [])),
            "last_indexed": datetime.now(timezone.utc).isoformat(),
        }
        memory_index_json = json.dumps(memory_index, indent=2)
        files[f"{agent_path}/memory/memory_index.json"] = memory_index_json.encode()
        hashes[f"{agent_path}/memory/memory_index.json"] = _sha256(memory_index_json)
        
        manifest_agents.append({
            "agent_id": agent["id"],
            "role": agent["role"],
            "agent_version": team_version,
            "path": f"{agent_path}/"
        })
    
    # Contracts
    tool_registry = """# Tool Registry
version: "1.0"
tools:
  - name: transaction_reader
    version: "2.0.0"
    description: Read transaction data
  - name: graph_analyzer
    version: "1.5.0"
    description: Analyze transaction graphs
  - name: risk_scorer
    version: "3.0.0"
    description: Score fraud risk
"""
    files["contracts/tool_registry.yaml"] = tool_registry.encode()
    hashes["contracts/tool_registry.yaml"] = _sha256(tool_registry)
    
    prompt_manifest = """# Prompt Manifest
version: "1.0"
prompts:
  - name: detection_analysis
    version: "1.2.0"
    hash: sha256:abc123def456
  - name: response_coordination
    version: "1.1.0"
    hash: sha256:789ghi012jkl
"""
    files["contracts/prompt_manifest.yaml"] = prompt_manifest.encode()
    hashes["contracts/prompt_manifest.yaml"] = _sha256(prompt_manifest)
    
    # Battle references (optional)
    if include_battle_refs:
        battle_refs = {
            "battles": [
                {"id": f"battle_{uuid4().hex[:8]}", "date": (datetime.now(timezone.utc) - timedelta(days=d)).isoformat(), "outcome": random.choice(["win", "loss"])}
                for d in range(0, 30, 5)
            ],
            "total_battles": random.randint(50, 200),
            "win_rate": round(random.uniform(0.70, 0.88), 2),
        }
        battle_refs_json = json.dumps(battle_refs, indent=2)
        files["battles/battle_refs.json"] = battle_refs_json.encode()
        hashes["battles/battle_refs.json"] = _sha256(battle_refs_json)
        
        learnings_summary = f"""# Battle Learnings Summary

## {team_name} — Combat History

**Total Battles:** {battle_refs['total_battles']}
**Win Rate:** {battle_refs['win_rate']:.0%}

### Key Victories
- Blocked coordinated ATO campaign targeting premium accounts
- Disrupted mule network with 150+ compromised accounts
- Prevented $2.5M in potential fraud losses

### Lessons Learned
1. Early detection is critical for containment
2. Graph analysis reveals hidden attack patterns
3. Multi-signal correlation reduces false positives

---
*Summary generated for compliance review.*
"""
        files["battles/learnings_summary.md"] = learnings_summary.encode()
        hashes["battles/learnings_summary.md"] = _sha256(learnings_summary)
    
    # Pack hashes
    pack_hashes = {
        "hash_algo": "sha256",
        "files": hashes,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    pack_hashes_json = json.dumps(pack_hashes, indent=2)
    files["pack_hashes.json"] = pack_hashes_json.encode()
    
    # Manifest (created last to include all agent entries)
    manifest = {
        "format": "AMC",
        "amc_version": "1.0",
        "team_id": team_id_upper,
        "team_name": team_name,
        "team_version": team_version,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "export_scope": {
            "include_memory_layers": ["semantic", "episodic", "procedural", "distilled"],
            "include_logs": "sanitized_only",
            "include_models": include_models,
            "include_battle_refs": include_battle_refs,
            "time_window_days": 180,
        },
        "compatibility": {
            "fraud_forge_app_version": "2.0.0",
            "runtime_version": "1.5.0",
            "schema_versions": {
                "amc_schema": "1.0",
                "agent_profile": "1.0",
                "memory": "1.0"
            },
            "prompt_manifest_hash": _sha256(prompt_manifest),
            "tool_registry_hash": _sha256(tool_registry),
        },
        "agents": manifest_agents,
        "hashes": {
            "pack_hash": _sha256(pack_hashes_json),
            "manifest_hash": "",  # Will be filled after
        },
    }
    manifest_json = json.dumps(manifest, indent=2)
    manifest["hashes"]["manifest_hash"] = _sha256(manifest_json)
    manifest_json = json.dumps(manifest, indent=2)
    files["manifest.json"] = manifest_json.encode()
    
    # Create ZIP archive
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for path, content in sorted(files.items()):
            zf.writestr(path, content)
    
    return buffer.getvalue()


def save_demo_amc(
    output_path: str = "./demo_amc",
    team_id: str = "blue",
    team_version: str = "1.2.0",
) -> str:
    """
    Generate and save a demo AMC file.
    
    Returns:
        str: Path to the saved AMC file
    """
    team_names = {
        "blue": "BlueTeam",
        "red": "RedTeam",
        "purple": "PurpleTeam",
        "green": "GreenTeam",
    }
    team_name = team_names.get(team_id.lower(), f"{team_id.title()}Team")
    
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"{team_name}_v{team_version}_{timestamp}_sandbox.amc"
    
    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    filepath = output_dir / filename
    
    amc_bytes = generate_demo_amc(team_id, team_version)
    filepath.write_bytes(amc_bytes)
    
    print(f"✅ Demo AMC generated: {filepath}")
    print(f"   Size: {len(amc_bytes):,} bytes")
    
    return str(filepath)


if __name__ == "__main__":
    import sys
    
    team = sys.argv[1] if len(sys.argv) > 1 else "blue"
    version = sys.argv[2] if len(sys.argv) > 2 else "1.2.0"
    
    path = save_demo_amc(team_id=team, team_version=version)
    print(f"\nGenerated: {path}")
