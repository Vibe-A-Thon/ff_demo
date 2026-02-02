# amc_Format_understanding.md

# AMC (Agent Memory Capsule) — Format Understanding & Build Spec (Fraud Forge)

## Executive Summary

An **AMC (Agent Memory Capsule)** is a **Team-level portable archive** used by Fraud Forge to package an AI team’s “evolved state” for:

* **Backup / Restore**
* **Promotion across environments** (dev → test → prod)
* **Portability across banks** (Bank A → Bank B) without leaking bank-specific data
* **Versioned evolution** (agent learning over battles, outcomes, improvements)

Like an RSB (`.rsb`) is a ZIP archive packaging a *single rule suite* with metadata, code, tests, and compliance, an AMC (`.amc`) is a ZIP archive packaging a *team’s agent memory + state + learnings + logs (sanitized) + optional model artifacts* with strict metadata, schemas, and validators. 

This document defines:

1. **AMC purpose + lifecycle**
2. **Recommended AMC internal structure** (folders, files, naming)
3. **Core schemas** (manifest, agent profile, memory layers, logs, model refs)
4. **Validation rules** (import/export safety & compatibility)
5. **UI/UX features** to make AMC usage “judge-wow” (hackathon winner)
6. **Implementation hooks** (APIs/CLI + importer/merger)

---

## 1. What is an AMC File?

### 1.1 Definition

**AMC (Agent Memory Capsule)** = a **ZIP archive** (Deflate) renamed to `.amc` containing:

* Team metadata (team name, version, hash, dependencies)
* Per-agent “evolved state” (memory layers, skills, policies, preferences)
* Optional model bundle (LoRA adapters, calibration params, thresholds)
* Battle-learnings summaries (bank-neutral)
* Logs (only sanitized / aggregated / hashed evidence)
* Explainability pack (XAI artifacts) for “why the agent learned this”

### 1.2 Key characteristics

* **File type:** ZIP (`.amc`)
* **Scope:** **One AMC per Team** (Blue Team, Red Team, etc.)
* **Contents:** Multiple per-agent files (generated “on demand” based on export scope)
* **Strict versioning:** SemVer for capsule + schema version pinning
* **Portability-ready:** Must support import into same Fraud Forge version/runtime (or block import)

---

## 2. AMC File Naming Convention

**Recommended pattern**

```
<AMC_TEAM>_v<semver>_<YYYYMMDD>_<HHMMSS>_<env>.amc
```

Examples:

* `BlueTeam_v1.0.0_20260129_151908_prod.amc`
* `RedTeam_v1.2.3_20260202_091501_sandbox.amc`

**Optional**

* include `build_hash` short: `_b3f2a9d`
* include `policy_id` short: `_P001`

---

## 3. AMC Directory Structure (Recommended)

Your RSB structure is highly organized (manifest + rule + code + tests + compliance). AMC should mirror that discipline. 

### 3.1 Standard structure (build spec)

```
TEAM_BLUE.amc  (ZIP archive)
│
├── manifest.json
├── team/
│   ├── team_profile.json
│   ├── team_roles.json
│   ├── operating_policy.yaml
│   ├── capability_matrix.json
│   └── xai/
│       ├── team_xai_summary.md
│       └── team_xai_factors.json
│
├── agents/
│   ├── A-<agent_id_1>/
│   │   ├── agent_profile.json
│   │   ├── memory/
│   │   │   ├── semantic_memory.jsonl
│   │   │   ├── episodic_memory.jsonl
│   │   │   ├── procedural_memory.json
│   │   │   ├── distilled_lessons.md
│   │   │   └── memory_index.json
│   │   ├── skills/
│   │   │   ├── skill_graph.json
│   │   │   ├── skill_scores.json
│   │   │   └── tool_usage_stats.json
│   │   ├── reasoning/
│   │   │   ├── decision_patterns.json
│   │   │   ├── heuristics.json
│   │   │   └── guardrails.json
│   │   ├── logs/
│   │   │   ├── activity_log.jsonl
│   │   │   ├── error_log.jsonl
│   │   │   └── telemetry_summary.json
│   │   ├── xai/
│   │   │   ├── agent_xai_summary.md
│   │   │   └── agent_xai_evidence.json
│   │   └── checksums.json
│   │
│   └── A-<agent_id_2>/
│       └── ...
│
├── battles/
│   ├── battle_refs.json
│   ├── learnings_summary.md
│   └── evidence_catalog.json
│
├── models/                         # optional (if agent evolution includes training/calibration)
│   ├── model_reference.json
│   ├── calibration.json
│   ├── thresholds.json
│   └── adapters/                   # optional
│       └── lora_adapter.bin
│
├── contracts/                      # strongly recommended for portability
│   ├── prompt_manifest.yaml
│   ├── tool_registry.yaml
│   └── schemas/
│       ├── amc_schema.json
│       ├── agent_profile_schema.json
│       └── memory_schema.json
│
├── governance/                     # optional in hackathon, mandatory in enterprise
│   ├── sanitization_policy.yaml
│   ├── sanitization_report.json
│   └── export_policy_id.txt
│
└── pack_hashes.json
```

### 3.2 “Minimum viable AMC” (hackathon-friendly)

If time is tight, AMC can ship only:

* `manifest.json`
* `team/team_profile.json`
* `agents/*/agent_profile.json`
* `agents/*/memory/*` (distilled first)
* `contracts/` (prompt/tool manifests)
* `pack_hashes.json`

This is enough for a strong portability demo.

---

## 4. Core AMC Metadata (manifest.json)

### 4.1 Purpose

`manifest.json` is the **single source of truth** for:

* capsule identity
* schema version
* compatibility constraints
* included agents and what was exported
* hashes for integrity checks

This is the AMC equivalent of `manifest.json` in RSB. 

### 4.2 Recommended schema

```json
{
  "format": "AMC",
  "amc_version": "1.0",
  "team_id": "TEAM-BLUE",
  "team_name": "Blue Team",
  "team_version": "1.0.0",
  "created_at": "2026-01-29T15:19:08Z",
  "export_scope": {
    "include_memory_layers": ["semantic", "episodic", "procedural", "distilled"],
    "include_logs": "sanitized_only",
    "include_models": false,
    "include_battle_refs": true,
    "time_window_days": 180
  },
  "compatibility": {
    "fraud_forge_app_version": "x.y.z",
    "runtime_version": "a.b.c",
    "schema_versions": {
      "amc_schema": "1.0",
      "agent_profile": "1.0",
      "memory": "1.0"
    },
    "prompt_manifest_hash": "sha256:...",
    "tool_registry_hash": "sha256:..."
  },
  "agents": [
    {
      "agent_id": "A-001",
      "role": "Detection Analyst",
      "agent_version": "1.0.0",
      "path": "agents/A-001/"
    }
  ],
  "hashes": {
    "pack_hash": "sha256:...",
    "manifest_hash": "sha256:..."
  }
}
```

### 4.3 Mandatory fields

* `format`, `amc_version`
* `team_id`, `team_version`, `created_at`
* `compatibility.*`
* `agents[]` list
* `hashes.pack_hash`

---

## 5. Per-Agent Files

### 5.1 agent_profile.json

Describes identity, role, specialization, and evolution state.

**Recommended**

```json
{
  "agent_id": "A-001",
  "name": "Blue-Detect-01",
  "role": "Fraud Detection Agent",
  "team_id": "TEAM-BLUE",
  "capabilities": [
    "pattern_detection",
    "graph_reasoning",
    "case_summarization",
    "signal_ranking"
  ],
  "memory_stats": {
    "semantic_items": 1200,
    "episodic_items": 340,
    "procedural_rules": 55,
    "last_distilled_at": "2026-01-28T10:00:00Z"
  },
  "evolution": {
    "evolution_level": 7,
    "battles_participated": 42,
    "win_rate": 0.76,
    "last_upgrade": "2026-01-25"
  }
}
```

### 5.2 Memory layers

AMC should distinguish memory into layers (critical for portability & safety):

#### a) semantic_memory.jsonl

* “facts/knowledge” learned (bank-neutral)
* each line = one JSON object

```json
{"id":"SM-001","topic":"mule_network","lesson":"Mule rings show fan-in/fan-out patterns over 24-72h with bursty device reuse","tags":["graph","mule"],"confidence":0.82}
```

#### b) episodic_memory.jsonl

* “experiences” (must be distilled/sanitized)

```json
{"id":"EM-101","event_type":"battle_outcome","summary":"Attack chain used onboarding + mule ring + cashout; defense improved by adding velocity+device correlation","signals":["velocity_spike","device_reuse"],"result":"mitigated"}
```

#### c) procedural_memory.json

* stable procedures, playbooks, workflows

```json
{
  "playbooks": [
    {"name":"ATO Investigation","steps":["collect signals","check device graph","score risk","route to manual review"]}
  ],
  "policies": {"max_false_positive_rate": 0.02}
}
```

#### d) distilled_lessons.md

* human-readable “why this agent is better”
* perfect for hackathon judges

### 5.3 Logs

**Rule:** logs inside AMC must be **sanitized** and **bank-neutral**.

* `activity_log.jsonl` → contains only abstract events, not raw payloads
* `telemetry_summary.json` → aggregates

---

## 6. Integrity, Validation & Security (Non-Negotiable)

### 6.1 pack_hashes.json

Stores file-level hashes for integrity and quick diffing.

```json
{
  "hash_algo": "sha256",
  "files": {
    "manifest.json": "sha256:...",
    "agents/A-001/agent_profile.json": "sha256:..."
  }
}
```

### 6.2 Prohibited content rules (portable across banks)

AMC must not contain:

* PII (names/emails/phones/account numbers)
* internal URLs/domains/IPs
* employee IDs/ticket IDs/case IDs
* vendor/client names
* raw transaction payloads

### 6.3 Distillation requirement

If your AMC is “team memory” (not explicitly bank-neutral), add a distillation pipeline before export:

* raw → abstracted lessons
* identifiers → canonical categories (`core_banking`, `cards_switch`, `digital_channel`)
* exact numbers → buckets/ranges
* examples → hashes

This aligns with your “portable evolved agents” program. 

---

## 7. Import / Merge Semantics (Brain Surgery UI)

AMC import should behave like a “controlled merge” (similar to RSB version merges). 

### 7.1 Import modes

* **Replace**: overwrite agent memory state
* **Merge (Append+Dedup)**: add new memory items, deduplicate by `id`/hash
* **Merge + Bank-B Calibration Layer**: keep imported learnings, but rebuild bank-specific calibration

### 7.2 Conflict types

* Same `agent_id` but different `agent_version`
* Tool/prompt mismatch (agent expects tool args that don’t exist)
* Schema mismatch (amc schema version mismatch)

### 7.3 Mandatory pre-import checks

* schema validation
* compatibility checks (runtime/prompt/tool hashes)
* prohibited-content scan
* integrity hash verification

---

## 8. Tooling & APIs (Build-Ready)

### 8.1 CLI (minimum)

* `ff amc validate <file.amc>`
* `ff amc inspect <file.amc>` (prints manifest + agent list + memory stats)
* `ff amc diff <old.amc> <new.amc>`
* `ff amc import <file.amc> --mode merge`

### 8.2 Backend endpoints

* `POST /amc/validate`
* `POST /amc/preview`
* `POST /amc/import`
* `POST /amc/diff`
* `GET  /amc/catalog` (local repository of imported AMCs)

---

## 9. UI/UX Features That Make AMC “Hackathon Winner”

These are the “judge-wow” differentiators (simple to demo, high perceived enterprise value):

### 9.1 AMC Explorer (File Viewer)

* drag-drop `.amc`
* show directory tree
* render JSON + Markdown
* show “Team Evolution Summary” card:

  * battles count, win rate, top learned patterns
  * memory growth over time
  * top tools used

### 9.2 “Memory Diff & Timeline”

* compare `AMC v1.0.0` vs `AMC v1.1.0`
* highlight:

  * added lessons
  * modified playbooks
  * new heuristics
* “What changed & why” auto-summary (XAI)

### 9.3 “Safety Scan” Badge

* one-click scan
* show: `0 PII found`, `0 bank identifiers`, `hash verified`
* even if sanitization report is “future scope”, the badge demo is gold

### 9.4 Import Preview + Sandbox Mode

* show exactly what will change before import
* activate imported agents **only in sandbox**
* run a synthetic scenario to prove improvement

### 9.5 “Evolved Agent Showcase”

* per-agent profile page:

  * strengths
  * known weaknesses
  * recommended role assignment
  * “top 5 lessons learned” in plain English

---

## 10. Recommendations (Best Practices)

1. **Make AMC strictly schema-driven** (no ad-hoc files)
2. **Pin prompts/tools via hashes** to prevent silent breakage
3. **Always generate a short judge-friendly summary** (Markdown)
4. **Keep logs aggregated**; keep “experience” distilled
5. **Provide deterministic validation** (same input ⇒ same result)

---

## 11. Acceptance Criteria

An AMC is “valid” if:

* It opens as ZIP
* `manifest.json` exists and validates
* `agents/` contains ≥1 agent with `agent_profile.json`
* memory files follow schema and contain no prohibited content
* `pack_hashes.json` matches the archive contents
* tool/prompt contract hashes match runtime

---

## 12. Next Step (When you can list actual zip contents)

Update §3 structure with the **exact filenames found in your real AMC zip**, and adjust:

* whether `manifest.json` name differs
* whether per-agent folders are named by UUID
* whether memory is stored as `.jsonl` or `.md` or `.pkl`

This doc is designed so you only need to replace the tree + file names, not rewrite the logic.

---

## Appendix A — Quick Reference: AMC vs RSB

* **RSB**: One fraud rule package (code/tests/compliance) 
* **AMC**: Team agent evolution package (memory/state/logs/models/contracts)

---

If you want, paste the **actual zip file listing** (top-level entries) and I’ll revise this into a **100% “based-on-real-zip”** document with the **exact** file tree + exact observed schemas—without changing the overall spec structure.
