"""AMC export/import/validation utilities."""

from __future__ import annotations

import io
import json
import hashlib
import zipfile
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

import yaml
from jsonschema import validate as jsonschema_validate
from jsonschema import ValidationError

from app.config import APP_VERSION, AMC_STORAGE_DIR
from app.db import db
from app.teams_data import default_team_payloads, default_agent_payloads
from app.tooling import TOOL_REGISTRY
from app.rag_utils import contains_sensitive_identifiers

SCHEMA_DIR = Path(__file__).resolve().parent / "schemas"
POLICY_FILE = Path(__file__).resolve().parent / "policies" / "amc_prohibited_content.yaml"


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _safe_members(zip_file: zipfile.ZipFile) -> List[str]:
    safe_names: List[str] = []
    for member in zip_file.namelist():
        if member.startswith("/") or ".." in member.split("/"):
            raise ValueError("Unsafe path detected in AMC archive")
        safe_names.append(member)
    return safe_names


def _load_schema(name: str) -> Dict[str, Any]:
    schema_path = SCHEMA_DIR / name
    if not schema_path.exists():
        return {}
    return json.loads(schema_path.read_text(encoding="utf-8"))


def _load_policy() -> Dict[str, Any]:
    if not POLICY_FILE.exists():
        return {"prohibited_patterns": [], "terms": []}
    return yaml.safe_load(POLICY_FILE.read_text(encoding="utf-8")) or {}


def _scan_text(text: str, policy: Dict[str, Any]) -> List[str]:
    hits: List[str] = []
    for pattern in policy.get("prohibited_patterns", []):
        try:
            if re.search(pattern, text, flags=re.IGNORECASE):
                hits.append(pattern)
        except re.error:
            continue
    lowered = text.lower()
    terms = policy.get("terms", [])
    if isinstance(terms, dict):
        terms = terms.get("include", [])
    for keyword in terms:
        if keyword.lower() in lowered:
            hits.append(keyword)
    if contains_sensitive_identifiers(text):
        hits.append("sensitive_identifiers")
    return hits


def _scan_zip_for_policy(zf: zipfile.ZipFile) -> List[Dict[str, Any]]:
    policy = _load_policy()
    findings: List[Dict[str, Any]] = []
    for name in zf.namelist():
        if name.endswith("/"):
            continue
        if not name.lower().endswith((".json", ".jsonl", ".md", ".txt", ".yaml", ".yml")):
            continue
        with zf.open(name) as handle:
            try:
                text = handle.read().decode("utf-8")
            except UnicodeDecodeError:
                continue
        hits = _scan_text(text, policy)
        if hits:
            findings.append({"file": name, "hits": hits})
    return findings


def _compute_pack_hashes(files: Dict[str, bytes]) -> Tuple[Dict[str, str], str]:
    hashes: Dict[str, str] = {}
    for path, content in files.items():
        if path == "pack_hashes.json":
            continue
        hashes[path] = f"sha256:{_sha256_bytes(content)}"
    pack_hash = _sha256_bytes(json.dumps(hashes, sort_keys=True).encode("utf-8"))
    return hashes, f"sha256:{pack_hash}"


def build_tool_registry_yaml() -> str:
    payload = {
        "version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "tools": [tool.model_dump() for tool in TOOL_REGISTRY.values()],
    }
    return yaml.safe_dump(payload, sort_keys=False)


def build_prompt_manifest_yaml(team_id: str) -> str:
    payload = {
        "version": "1.0",
        "team_id": team_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "prompts": [
            {
                "prompt_id": f"{team_id}.orchestrator",
                "hash": f"sha256:{hashlib.sha256(team_id.encode('utf-8')).hexdigest()}",
                "version": "1.0",
            }
        ],
    }
    return yaml.safe_dump(payload, sort_keys=False)


def _build_memory_index(semantic: List[Dict[str, Any]], episodic: List[Dict[str, Any]], procedural: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "semantic_items": len(semantic),
        "episodic_items": len(episodic),
        "procedural_rules": len(procedural.get("playbooks", [])),
        "last_distilled_at": datetime.now(timezone.utc).isoformat(),
    }


def _build_agent_profile(agent: Dict[str, Any], memory_index: Dict[str, Any]) -> Dict[str, Any]:
    evolution_level = min(9, max(1, memory_index.get("semantic_items", 1) // 200 + 1))
    return {
        "agent_id": agent.get("agent_id"),
        "name": agent.get("agent_name"),
        "role": agent.get("role"),
        "team_id": agent.get("team_id"),
        "capabilities": agent.get("capabilities", []),
        "memory_stats": memory_index,
        "evolution": {
            "evolution_level": evolution_level,
            "battles_participated": max(1, memory_index.get("episodic_items", 1) * 2),
            "win_rate": round(0.62 + (evolution_level * 0.02), 2),
            "last_upgrade": datetime.now(timezone.utc).date().isoformat(),
        },
    }


def _build_semantic_entries(agent: Dict[str, Any], artifacts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if artifacts:
        entries = []
        for artifact in artifacts[:5]:
            entries.append(
                {
                    "id": f"SM-{artifact.get('artifact_id', 'auto')}",
                    "topic": artifact.get("artifact_type", "pattern"),
                    "lesson": f"Derived insight from {artifact.get('artifact_type', 'artifact')} artifacts.",
                    "tags": [agent.get("team_id", "team"), "synthetic"],
                    "confidence": 0.78,
                }
            )
        return entries
    return [
        {
            "id": f"SM-{agent.get('agent_id')}-001",
            "topic": "synthetic_patterns",
            "lesson": "Detected recurring synthetic fraud signatures across simulated runs.",
            "tags": ["synthetic", "baseline"],
            "confidence": 0.74,
        }
    ]


def _build_episodic_entries(agent: Dict[str, Any], tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if tasks:
        entries = []
        for task in tasks[:5]:
            entries.append(
                {
                    "id": f"EM-{task.get('task_id', 'auto')}",
                    "event_type": task.get("task_type", "agent_task"),
                    "summary": f"Completed {task.get('task_type', 'task')} for run {task.get('run_id', 'n/a')}",
                    "signals": [agent.get("team_id", "team"), "synthetic"],
                    "result": task.get("status", "completed"),
                }
            )
        return entries
    return [
        {
            "id": f"EM-{agent.get('agent_id')}-001",
            "event_type": "battle_outcome",
            "summary": "Synthetic defense adjustments improved detection confidence.",
            "signals": ["velocity_spike", "device_reuse"],
            "result": "mitigated",
        }
    ]


def _build_procedural_memory(agent: Dict[str, Any]) -> Dict[str, Any]:
    role = agent.get("role", "Analyst")
    return {
        "playbooks": [
            {
                "name": f"{role} Playbook",
                "steps": [
                    "collect synthetic signals",
                    "score risk",
                    "record decision",
                    "route for review",
                ],
            }
        ],
        "policies": {"max_false_positive_rate": 0.02},
    }


def _build_distilled_lessons(agent: Dict[str, Any], semantic: List[Dict[str, Any]]) -> str:
    summary_lines = [
        f"# Distilled Lessons for {agent.get('agent_name', 'Agent')}",
        "",
        "- Synthetic-only lessons distilled from recent battle simulations.",
        "- Key themes:",
    ]
    for entry in semantic[:3]:
        summary_lines.append(f"  - {entry.get('lesson')}")
    summary_lines.append("")
    summary_lines.append("These lessons are portable and contain no bank identifiers.")
    return "\n".join(summary_lines)


def _build_agent_files(agent: Dict[str, Any], artifacts: List[Dict[str, Any]], tasks: List[Dict[str, Any]]) -> Dict[str, bytes]:
    semantic = _build_semantic_entries(agent, artifacts)
    episodic = _build_episodic_entries(agent, tasks)
    procedural = _build_procedural_memory(agent)
    memory_index = _build_memory_index(semantic, episodic, procedural)
    agent_profile = _build_agent_profile(agent, memory_index)

    base = f"agents/{agent.get('agent_id')}/"
    files: Dict[str, bytes] = {
        f"{base}agent_profile.json": json.dumps(agent_profile, indent=2).encode("utf-8"),
        f"{base}memory/semantic_memory.jsonl": "\n".join(json.dumps(item) for item in semantic).encode("utf-8"),
        f"{base}memory/episodic_memory.jsonl": "\n".join(json.dumps(item) for item in episodic).encode("utf-8"),
        f"{base}memory/procedural_memory.json": json.dumps(procedural, indent=2).encode("utf-8"),
        f"{base}memory/distilled_lessons.md": _build_distilled_lessons(agent, semantic).encode("utf-8"),
        f"{base}memory/memory_index.json": json.dumps(memory_index, indent=2).encode("utf-8"),
        f"{base}skills/skill_graph.json": json.dumps({"nodes": [], "edges": []}, indent=2).encode("utf-8"),
        f"{base}skills/skill_scores.json": json.dumps({"scores": agent.get("capabilities", [])}, indent=2).encode("utf-8"),
        f"{base}skills/tool_usage_stats.json": json.dumps({"tools": agent.get("allowed_tools", [])}, indent=2).encode("utf-8"),
        f"{base}reasoning/decision_patterns.json": json.dumps({"patterns": []}, indent=2).encode("utf-8"),
        f"{base}reasoning/heuristics.json": json.dumps({"heuristics": []}, indent=2).encode("utf-8"),
        f"{base}reasoning/guardrails.json": json.dumps({"guardrails": agent.get("guardrails", [])}, indent=2).encode("utf-8"),
        f"{base}logs/telemetry_summary.json": json.dumps({"metrics": agent.get("metrics", {})}, indent=2).encode("utf-8"),
        f"{base}xai/agent_xai_summary.md": f"# XAI Summary\n\nSynthetic explanation artifacts for {agent.get('agent_name', 'agent')}.".encode("utf-8"),
        f"{base}xai/agent_xai_evidence.json": json.dumps({"evidence": []}, indent=2).encode("utf-8"),
    }
    return files


def _build_team_files(team: Dict[str, Any]) -> Dict[str, bytes]:
    team_profile = {
        "team_id": team.get("team_id"),
        "internal_name": team.get("internal_name"),
        "bank_facing_name": team.get("bank_facing_name"),
        "mission_statement": team.get("mission_statement"),
        "capability_tags": team.get("capability_tags", []),
    }
    return {
        "team/team_profile.json": json.dumps(team_profile, indent=2).encode("utf-8"),
        "team/team_roles.json": json.dumps({"roles": team.get("default_agent_roles", [])}, indent=2).encode("utf-8"),
        "team/operating_policy.yaml": yaml.safe_dump({"synthetic_only": True}, sort_keys=False).encode("utf-8"),
        "team/capability_matrix.json": json.dumps({"capabilities": team.get("capability_tags", [])}, indent=2).encode("utf-8"),
        "team/xai/team_xai_summary.md": f"# Team XAI Summary\n\n{team.get('bank_facing_name', 'Team')} explanation readiness.".encode("utf-8"),
        "team/xai/team_xai_factors.json": json.dumps({"factors": []}, indent=2).encode("utf-8"),
    }


def _parse_jsonl(text: str) -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries


def _build_manifest(
    team: Dict[str, Any],
    export_scope: Dict[str, Any],
    prompt_hash: str,
    tool_hash: str,
    agent_entries: List[Dict[str, Any]],
) -> Dict[str, Any]:
    return {
        "format": "AMC",
        "amc_version": "1.0",
        "team_id": team.get("team_id"),
        "team_name": team.get("internal_name"),
        "team_version": team.get("version", "1.0.0"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "export_scope": export_scope,
        "compatibility": {
            "fraud_forge_app_version": APP_VERSION,
            "runtime_version": "1.0.0",
            "schema_versions": {
                "amc_schema": "1.0",
                "agent_profile": "1.0",
                "memory": "1.0",
            },
            "prompt_manifest_hash": prompt_hash,
            "tool_registry_hash": tool_hash,
        },
        "agents": agent_entries,
        "hashes": {},
    }


def _parse_agent_ids(file_names: List[str]) -> List[str]:
    agent_ids: List[str] = []
    for name in file_names:
        if name.startswith("agents/") and name.endswith("/agent_profile.json"):
            parts = name.split("/")
            if len(parts) > 2:
                agent_ids.append(parts[1])
    return list(sorted(set(agent_ids)))


def _extract_manifest(zf: zipfile.ZipFile) -> Dict[str, Any] | None:
    try:
        with zf.open("manifest.json") as handle:
            return json.loads(handle.read().decode("utf-8"))
    except (KeyError, json.JSONDecodeError, UnicodeDecodeError):
        return None


def _build_preview(zf: zipfile.ZipFile) -> Dict[str, Any]:
    manifest = _extract_manifest(zf) or {}
    file_names = _safe_members(zf)
    agent_ids = _parse_agent_ids(file_names)
    memory_counts = {}
    for agent_id in agent_ids:
        semantic_path = f"agents/{agent_id}/memory/semantic_memory.jsonl"
        episodic_path = f"agents/{agent_id}/memory/episodic_memory.jsonl"
        semantic_count = 0
        episodic_count = 0
        if semantic_path in file_names:
            with zf.open(semantic_path) as handle:
                semantic_count = len(_parse_jsonl(handle.read().decode("utf-8")))
        if episodic_path in file_names:
            with zf.open(episodic_path) as handle:
                episodic_count = len(_parse_jsonl(handle.read().decode("utf-8")))
        memory_counts[agent_id] = {
            "semantic": semantic_count,
            "episodic": episodic_count,
        }
    return {
        "manifest": manifest,
        "agent_count": len(agent_ids),
        "memory_counts": memory_counts,
    }


def _build_import_snapshot(zf: zipfile.ZipFile) -> Dict[str, Any]:
    preview = _build_preview(zf)
    manifest = preview.get("manifest") or {}
    memory_counts = preview.get("memory_counts", {})
    file_names = _safe_members(zf)
    agent_entries: List[Dict[str, Any]] = []
    for agent_id in _parse_agent_ids(file_names):
        profile_path = f"agents/{agent_id}/agent_profile.json"
        profile: Dict[str, Any] = {}
        if profile_path in file_names:
            try:
                with zf.open(profile_path) as handle:
                    profile = json.loads(handle.read().decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                profile = {}
        counts = memory_counts.get(agent_id, {})
        agent_entries.append(
            {
                "agent_id": agent_id,
                "name": profile.get("name") or profile.get("agent_name"),
                "role": profile.get("role"),
                "semantic": counts.get("semantic", 0),
                "episodic": counts.get("episodic", 0),
            }
        )

    total_semantic = sum(item.get("semantic", 0) for item in memory_counts.values())
    total_episodic = sum(item.get("episodic", 0) for item in memory_counts.values())
    return {
        "team_id": manifest.get("team_id"),
        "team_name": manifest.get("team_name", manifest.get("team_id")),
        "agent_count": preview.get("agent_count", len(agent_entries)),
        "memory_counts": memory_counts,
        "agents": agent_entries,
        "totals": {"semantic": total_semantic, "episodic": total_episodic},
        "manifest": manifest,
        "source": "import",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def _build_snapshot_from_agents(team: Dict[str, Any], agents: List[Dict[str, Any]], memory_counts: Dict[str, Dict[str, int]], agent_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    total_semantic = sum(item.get("semantic", 0) for item in memory_counts.values())
    total_episodic = sum(item.get("episodic", 0) for item in memory_counts.values())
    return {
        "team_id": team.get("team_id"),
        "team_name": team.get("internal_name", team.get("team_id")),
        "agent_count": len(agents),
        "memory_counts": memory_counts,
        "agents": agent_entries,
        "totals": {"semantic": total_semantic, "episodic": total_episodic},
        "source": "baseline",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def _merge_snapshots(baseline: Dict[str, Any], imported: Dict[str, Any], mode: str) -> Dict[str, Any]:
    merged_counts: Dict[str, Dict[str, int]] = {}
    baseline_counts = baseline.get("memory_counts", {})
    imported_counts = imported.get("memory_counts", {})
    agent_ids = set(baseline_counts.keys()) | set(imported_counts.keys())

    for agent_id in agent_ids:
        base = baseline_counts.get(agent_id, {})
        incoming = imported_counts.get(agent_id, {})
        if mode == "replace":
            merged_counts[agent_id] = {
                "semantic": incoming.get("semantic", 0),
                "episodic": incoming.get("episodic", 0),
            }
        else:
            merged_counts[agent_id] = {
                "semantic": base.get("semantic", 0) + incoming.get("semantic", 0),
                "episodic": base.get("episodic", 0) + incoming.get("episodic", 0),
            }

    merged_agents: List[Dict[str, Any]] = []
    for agent_id in sorted(agent_ids):
        base_agent = next((agent for agent in baseline.get("agents", []) if agent.get("agent_id") == agent_id), {})
        import_agent = next((agent for agent in imported.get("agents", []) if agent.get("agent_id") == agent_id), {})
        counts = merged_counts.get(agent_id, {})
        merged_agents.append(
            {
                "agent_id": agent_id,
                "name": import_agent.get("name") or base_agent.get("name"),
                "role": import_agent.get("role") or base_agent.get("role"),
                "semantic": counts.get("semantic", 0),
                "episodic": counts.get("episodic", 0),
            }
        )

    total_semantic = sum(item.get("semantic", 0) for item in merged_counts.values())
    total_episodic = sum(item.get("episodic", 0) for item in merged_counts.values())
    merged = {
        "team_id": imported.get("team_id") or baseline.get("team_id"),
        "team_name": imported.get("team_name") or baseline.get("team_name"),
        "agent_count": len(agent_ids),
        "memory_counts": merged_counts,
        "agents": merged_agents,
        "totals": {"semantic": total_semantic, "episodic": total_episodic},
        "merge_mode": mode,
        "source": "merged",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    if mode == "merge_calibrate":
        merged["calibration_required"] = True
    return merged


async def build_baseline_snapshot(team_id: str) -> Dict[str, Any]:
    team = await db.teams.find_one({"team_id": team_id}, {"_id": 0})
    if not team:
        team = next((t for t in default_team_payloads() if t["team_id"] == team_id), None)
    if not team:
        raise ValueError("Team not found")

    agents = await db.agents.find({"team_id": team_id}, {"_id": 0}).to_list(200)
    if not agents:
        agents = [a for a in default_agent_payloads() if a["team_id"] == team_id]

    memory_counts: Dict[str, Dict[str, int]] = {}
    agent_entries: List[Dict[str, Any]] = []
    for agent in agents:
        agent_id = agent.get("agent_id")
        if not agent_id:
            continue
        artifacts = await db.agent_artifacts.find({"agent_id": agent_id}, {"_id": 0}).to_list(10)
        tasks = await db.agent_tasks.find({"target_agent_id": agent_id}, {"_id": 0}).to_list(10)
        semantic = _build_semantic_entries(agent, artifacts)
        episodic = _build_episodic_entries(agent, tasks)
        memory_counts[agent_id] = {
            "semantic": len(semantic),
            "episodic": len(episodic),
        }
        agent_entries.append(
            {
                "agent_id": agent_id,
                "name": agent.get("agent_name"),
                "role": agent.get("role"),
                "semantic": len(semantic),
                "episodic": len(episodic),
            }
        )

    return _build_snapshot_from_agents(team, agents, memory_counts, agent_entries)


async def build_amc_merge_preview(payload: bytes, mode: str = "merge") -> Dict[str, Any]:
    with zipfile.ZipFile(io.BytesIO(payload)) as zf:
        import_snapshot = _build_import_snapshot(zf)
    team_id = import_snapshot.get("team_id") or "blue"
    baseline = await build_baseline_snapshot(team_id)
    merged = _merge_snapshots(baseline, import_snapshot, mode)
    return {
        "baseline": baseline,
        "import": import_snapshot,
        "merged": merged,
        "preview": {
            "manifest": import_snapshot.get("manifest"),
            "agent_count": import_snapshot.get("agent_count"),
            "memory_counts": import_snapshot.get("memory_counts"),
        },
    }


async def apply_amc_merge_state(
    payload: bytes,
    mode: str,
    activate: bool,
    actor_id: str,
    package_id: Optional[str] = None,
) -> Dict[str, Any]:
    preview = await build_amc_merge_preview(payload, mode=mode)
    baseline = preview.get("baseline")
    imported = preview.get("import")
    merged = preview.get("merged")
    team_id = merged.get("team_id") if merged else None

    state_update = {
        "team_id": team_id,
        "baseline_snapshot": baseline,
        "import_snapshot": imported,
        "merged_snapshot": merged,
        "last_mode": mode,
        "last_package_id": package_id,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    if activate and package_id:
        state_update.update(
            {
                "active_package_id": package_id,
                "active_snapshot": merged,
                "activated_by": actor_id,
                "activated_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    await db.amc_states.update_one({"team_id": team_id}, {"$set": state_update}, upsert=True)
    return preview


async def export_amc(team_id: str, export_scope: Dict[str, Any], env_tag: str) -> Tuple[bytes, Dict[str, Any], str]:
    team = await db.teams.find_one({"team_id": team_id}, {"_id": 0})
    if not team:
        team = next((t for t in default_team_payloads() if t["team_id"] == team_id), None)
    if not team:
        raise ValueError("Team not found")

    agents = await db.agents.find({"team_id": team_id}, {"_id": 0}).to_list(200)
    if not agents:
        agents = [a for a in default_agent_payloads() if a["team_id"] == team_id]

    prompt_manifest = build_prompt_manifest_yaml(team_id)
    tool_registry = build_tool_registry_yaml()
    prompt_hash = f"sha256:{_sha256_bytes(prompt_manifest.encode('utf-8'))}"
    tool_hash = f"sha256:{_sha256_bytes(tool_registry.encode('utf-8'))}"

    files: Dict[str, bytes] = {}
    files.update(_build_team_files(team))
    files["contracts/prompt_manifest.yaml"] = prompt_manifest.encode("utf-8")
    files["contracts/tool_registry.yaml"] = tool_registry.encode("utf-8")

    for schema_file in ["amc_schema.json", "agent_profile_schema.json", "memory_schema.json"]:
        schema_path = SCHEMA_DIR / schema_file
        if schema_path.exists():
            files[f"contracts/schemas/{schema_file}"] = schema_path.read_text(encoding="utf-8").encode("utf-8")

    policy_text = POLICY_FILE.read_text(encoding="utf-8") if POLICY_FILE.exists() else ""
    if policy_text:
        files["governance/sanitization_policy.yaml"] = policy_text.encode("utf-8")

    if export_scope.get("include_battle_refs"):
        battles = await db.battles.find({}, {"_id": 0}).to_list(50)
        battle_refs = [
            {
                "battle_id": battle.get("id"),
                "scenario": battle.get("scenario_name"),
                "status": battle.get("status"),
            }
            for battle in battles
        ]
        files["battles/battle_refs.json"] = json.dumps(battle_refs, indent=2).encode("utf-8")
        files["battles/learnings_summary.md"] = (
            "# Battle Learnings\n\nDistilled outcomes from synthetic battles for portability."
        ).encode("utf-8")

    agent_entries: List[Dict[str, Any]] = []
    for agent in agents:
        artifacts = await db.agent_artifacts.find({"agent_id": agent.get("agent_id")}, {"_id": 0}).to_list(10)
        tasks = await db.agent_tasks.find({"target_agent_id": agent.get("agent_id")}, {"_id": 0}).to_list(10)
        files.update(_build_agent_files(agent, artifacts, tasks))
        agent_entries.append(
            {
                "agent_id": agent.get("agent_id"),
                "role": agent.get("role"),
                "agent_version": agent.get("version", "1.0.0"),
                "path": f"agents/{agent.get('agent_id')}/",
            }
        )

    manifest = _build_manifest(team, export_scope, prompt_hash, tool_hash, agent_entries)
    files["manifest.json"] = json.dumps(manifest, indent=2).encode("utf-8")

    hashes, pack_hash = _compute_pack_hashes(files)
    manifest["hashes"] = {"pack_hash": pack_hash, "manifest_hash": hashes.get("manifest.json", "")}
    files["manifest.json"] = json.dumps(manifest, indent=2).encode("utf-8")
    hashes, pack_hash = _compute_pack_hashes(files)
    files["pack_hashes.json"] = json.dumps({"hash_algo": "sha256", "files": hashes}, indent=2).encode("utf-8")

    with io.BytesIO() as buffer:
        with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            for path, content in files.items():
                zf.writestr(path, content)
        buffer.seek(0)
        filename = f"{team.get('internal_name','Team').replace(' ', '')}_v{team.get('version','1.0.0')}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{env_tag}.amc"
        return buffer.read(), manifest, filename


def validate_amc_bytes(payload: bytes) -> Dict[str, Any]:
    errors: List[str] = []
    warnings: List[str] = []
    with zipfile.ZipFile(io.BytesIO(payload)) as zf:
        file_names = _safe_members(zf)
        required = ["manifest.json", "team/team_profile.json", "pack_hashes.json"]
        for name in required:
            if name not in file_names:
                errors.append(f"Missing required file: {name}")

        manifest = _extract_manifest(zf)
        if not manifest:
            errors.append("manifest.json missing or invalid")
        else:
            schema = _load_schema("amc_schema.json")
            if schema:
                try:
                    jsonschema_validate(instance=manifest, schema=schema)
                except ValidationError as exc:
                    errors.append(f"manifest.json schema error: {exc.message}")

        agent_schema = _load_schema("agent_profile_schema.json")
        memory_schema = _load_schema("memory_schema.json")
        for name in file_names:
            if name.endswith("/agent_profile.json") and agent_schema:
                try:
                    with zf.open(name) as handle:
                        payload = json.loads(handle.read().decode("utf-8"))
                    jsonschema_validate(instance=payload, schema=agent_schema)
                except (ValidationError, json.JSONDecodeError, UnicodeDecodeError) as exc:
                    errors.append(f"{name} schema error: {getattr(exc, 'message', str(exc))}")
            if name.endswith("semantic_memory.jsonl") or name.endswith("episodic_memory.jsonl"):
                if not memory_schema:
                    continue
                try:
                    with zf.open(name) as handle:
                        entries = _parse_jsonl(handle.read().decode("utf-8"))
                    for entry in entries[:50]:
                        jsonschema_validate(instance=entry, schema=memory_schema)
                except (ValidationError, UnicodeDecodeError) as exc:
                    errors.append(f"{name} memory schema error: {getattr(exc, 'message', str(exc))}")

        try:
            with zf.open("pack_hashes.json") as handle:
                pack_hashes = json.loads(handle.read().decode("utf-8"))
        except (KeyError, json.JSONDecodeError, UnicodeDecodeError):
            pack_hashes = None
            errors.append("pack_hashes.json missing or invalid")

        if pack_hashes:
            files_hashes = pack_hashes.get("files", {})
            for path, expected in files_hashes.items():
                if path not in file_names:
                    errors.append(f"Missing file listed in pack_hashes.json: {path}")
                    continue
                with zf.open(path) as handle:
                    actual = f"sha256:{_sha256_bytes(handle.read())}"
                if actual != expected:
                    errors.append(f"Hash mismatch for {path}")

            if manifest and manifest.get("hashes", {}).get("pack_hash"):
                computed_pack_hash = _sha256_bytes(json.dumps(files_hashes, sort_keys=True).encode("utf-8"))
                expected_pack_hash = manifest.get("hashes", {}).get("pack_hash")
                if expected_pack_hash != f"sha256:{computed_pack_hash}":
                    warnings.append("manifest pack_hash does not match computed pack hash")

        policy_hits = _scan_zip_for_policy(zf)
        if policy_hits:
            errors.append("Prohibited content detected")

        if manifest:
            compatibility = manifest.get("compatibility", {})
            if compatibility.get("fraud_forge_app_version") not in {APP_VERSION, "x.y.z"}:
                warnings.append("AMC created with different Fraud Forge version")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "policy_hits": policy_hits if "policy_hits" in locals() else [],
    }


def preview_amc_bytes(payload: bytes) -> Dict[str, Any]:
    with zipfile.ZipFile(io.BytesIO(payload)) as zf:
        return _build_preview(zf)


def diff_amc_bytes(old_payload: bytes, new_payload: bytes) -> Dict[str, Any]:
    with zipfile.ZipFile(io.BytesIO(old_payload)) as zf_old, zipfile.ZipFile(io.BytesIO(new_payload)) as zf_new:
        old_preview = _build_preview(zf_old)
        new_preview = _build_preview(zf_new)

    agent_ids = set(old_preview.get("memory_counts", {}).keys()) | set(new_preview.get("memory_counts", {}).keys())
    diff_summary = []
    for agent_id in sorted(agent_ids):
        old_counts = old_preview.get("memory_counts", {}).get(agent_id, {})
        new_counts = new_preview.get("memory_counts", {}).get(agent_id, {})
        diff_summary.append(
            {
                "agent_id": agent_id,
                "semantic_delta": new_counts.get("semantic", 0) - old_counts.get("semantic", 0),
                "episodic_delta": new_counts.get("episodic", 0) - old_counts.get("episodic", 0),
            }
        )

    return {
        "old": old_preview,
        "new": new_preview,
        "changes": diff_summary,
    }


async def save_amc_package(payload: bytes, manifest: Dict[str, Any], env_tag: str, source: str, created_by: str, validation: Dict[str, Any] | None = None) -> Dict[str, Any]:
    package_id = hashlib.sha256(payload).hexdigest()[:16]
    storage_path = AMC_STORAGE_DIR / f"{package_id}.amc"
    storage_path.write_bytes(payload)

    record = {
        "id": package_id,
        "team_id": manifest.get("team_id"),
        "team_name": manifest.get("team_name", manifest.get("team_id")),
        "team_version": manifest.get("team_version", "1.0.0"),
        "env_tag": env_tag,
        "status": "imported" if source == "import" else "exported",
        "manifest": manifest,
        "validation": validation or {},
        "storage_path": str(storage_path),
        "source": source,
        "created_by": created_by,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.amc_packages.insert_one(record)
    return record


async def list_catalog() -> List[Dict[str, Any]]:
    return await db.amc_packages.find({}, {"_id": 0}).to_list(200)


async def activate_package(package_id: str, actor_id: str) -> Dict[str, Any]:
    package = await db.amc_packages.find_one({"id": package_id}, {"_id": 0})
    if not package:
        raise ValueError("AMC package not found")
    team_id = package.get("team_id")
    await db.amc_states.update_one(
        {"team_id": team_id},
        {"$set": {"team_id": team_id, "active_package_id": package_id, "activated_by": actor_id, "activated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )
    await db.amc_packages.update_one({"id": package_id}, {"$set": {"status": "active"}})
    return package
