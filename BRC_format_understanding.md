# BRC_format_understanding.md — BRC (Battle Run Capsule) Format Spec (Fraud Forge)

## 0) Executive summary

A **BRC (Battle Run Capsule)** is a **battle-level portable archive** used by Fraud Forge to package **everything produced during a Red vs Blue (and other team) battle run** so it can be:

- **Replayed** (read-only playback) in *Battle Replay* UI
- **Re-evaluated** (recompute scorecards with current scoring rules)
- **Re-run** (sandbox re-run defense, optionally full rerun if deterministic)
- **Audited** (what happened, when, why, using which stage artifacts)
- **Shared** (portable across environments/banks without leaking bank-specific data)

**Design goal:** A `.brc` is a **ZIP archive** renamed to `.brc` containing:
- **inputs** (red team simulation data as JSON)
- **orchestrator outputs per stage**
- **team/agent outputs**
- **telemetry + scorecards**
- **XAI artifacts**
- **integrity hashes** (and optional signatures later)

This aligns with your capsule ecosystem:
- **RSB** = canonical rule suite box for fixes/controls/tests
- **AMC** = team/agent memory capsule (evolved state)
- **BRC** = **one battle run** trace + artifacts (the “War Room export”)

---

## 1) File type, naming, and scope

### 1.1 File type
- `.brc` is a **ZIP** (Deflate) file, extension changed to `.brc`

### 1.2 One BRC per battle run
- Exactly **one BRC** represents exactly **one battle run** (`battle_run_id`)

### 1.3 BRC filename (required)
Pattern:
```

<battle_type>*<battle_run_id>*<YYYYMMDD>_<HHMMSS>.brc

```

Examples:
- `ato_mule_network_000042_20260202_031500.brc`
- `card_testing_000043_20260202_033005.brc`

Notes:
- Timestamp should be **UTC** (recommended) or store timezone in manifest.

---

## 2) Required files in a BRC

A valid BRC must contain **at least**:

- `manifest.json` (mandatory)
- `metadata.json` (mandatory)
- `pack_hashes.json` (mandatory)
- `inputs/red_simulation_data.json` (mandatory)
- `stages/<...>/orchestrator_output.json` per stage (mandatory)
- `stages/06_evaluate/scorecard.json` (mandatory for demo + objective scoring)

---

## 3) Recommended internal folder structure

### 3.1 Full structure (enterprise-grade, future proof)

```

<battle_type>*<battle_run_id>*<timestamp>.brc
│
├── manifest.json
├── metadata.json
├── pack_hashes.json
│
├── inputs/
│   ├── red_simulation_data.json          # required (sanitized)
│   ├── scenario_config.json              # optional (seed, knobs, flags)
│   ├── synthetic_dataset.jsonl           # optional (bank-neutral synthetic)
│   └── mapping_hints.json                # optional (canonical mapping hints)
│
├── orchestrator/
│   ├── stage_plan.json                   # canonical stage definitions
│   ├── stage_state.jsonl                 # timeline transitions
│   ├── tool_calls_summary.jsonl          # aggregated only, no raw payload
│   └── run_summary.md                    # judge-friendly summary
│
├── stages/
│   ├── 00_prepare/
│   │   ├── orchestrator_output.json
│   │   └── system_health.json
│   ├── 01_plan/
│   │   ├── orchestrator_output.json
│   │   ├── red_team_<id>*<ts>.json
│   │   └── blue_team*<id>*<ts>.json
│   ├── 02_simulate/
│   │   ├── orchestrator_output.json
│   │   ├── red_team*<id>*<ts>.json
│   │   └── red_team/
│   │       ├── <agent_id>*<id>*<ts>.json
│   │       └── ...
│   ├── 03_detect/
│   │   ├── orchestrator_output.json
│   │   ├── blue_team*<id>*<ts>.json
│   │   └── xai_summary.json
│   ├── 04_mitigate/
│   │   ├── orchestrator_output.json
│   │   ├── blue_team*<id>_<ts>.json
│   │   └── mitigation_actions.json
│   ├── 05_patch_rules/
│   │   ├── orchestrator_output.json
│   │   ├── rsb_proposals.json            # fix proposals generated during battle
│   │   └── generated_rsb_refs.json       # references to exported .rsb (optional)
│   ├── 06_evaluate/
│   │   ├── orchestrator_output.json
│   │   ├── scorecard.json
│   │   └── metrics.json
│   └── 07_postmortem/
│       ├── orchestrator_output.json
│       ├── postmortem.md
│       └── lessons_distilled.json
│
├── telemetry/
│   ├── metrics.json
│   ├── metrics_timeseries.jsonl
│   ├── alerts.jsonl
│   └── evidence_catalog.json             # hashed/bucketed evidence
│
├── xai/
│   ├── battle_xai_summary.md
│   ├── decision_graph.json               # “why chain” across stages
│   ├── key_factors.json
│   └── disclaimers.json
│
├── artifacts/
│   ├── mule_network_graph.json           # for UI visualization
│   ├── rules_connected_map.json          # for UI visualization
│   └── screenshots/                      # optional (sanitized only)
│
├── contracts/                            # strongly recommended for portability
│   ├── prompt_manifest.yaml
│   ├── tool_registry.yaml
│   └── schemas/
│       ├── brc_schema.json
│       ├── orchestrator_output_schema.json
│       └── stage_output_schema.json
│
└── governance/                           # optional for hackathon; required for enterprise
├── sanitization_policy.yaml
├── sanitization_report.json
└── transfer_manifest.json

```

### 3.2 Minimum viable BRC (hackathon-friendly)
If you want to ship the “wow” with minimal engineering, include:

- `manifest.json`, `metadata.json`, `pack_hashes.json`
- `inputs/red_simulation_data.json`
- `orchestrator/run_summary.md`
- `stages/*/orchestrator_output.json` + one team output per stage
- `stages/06_evaluate/scorecard.json`
- `xai/battle_xai_summary.md`

---

## 4) Naming conventions inside stages

Requirement: “outputs per stage named as `teamname_battlerunid_timestamp`”.

Recommended:

- Team level:
```

stages/<stage>/red_team_<battle_run_id>*<timestamp>.json
stages/<stage>/blue_team*<battle_run_id>*<timestamp>.json
stages/<stage>/xai_team*<battle_run_id>_<timestamp>.json

```
- Agent level (optional):
```

stages/<stage>/<team_name>/<agent_id>*<battle_run_id>*<timestamp>.json

````

---

## 5) `manifest.json` — identity + compatibility + index

Purpose:
- Proves what this BRC is, which versions created it, what it contains, and how to validate it.

Recommended schema (minimum):

```json
{
"format": "BRC",
"brc_version": "1.0",
"battle_run_id": "000042",
"battle_type": "ato_mule_network",
"created_at": "2026-02-02T03:15:00Z",
"seed": 123456,
"participants": {
  "teams": ["TEAM-RED", "TEAM-BLUE", "TEAM-XAI"],
  "agents_count": 12
},
"compatibility": {
  "fraud_forge_app_version": "x.y.z",
  "runtime_version": "a.b.c",
  "schema_versions": {
    "brc_schema": "1.0",
    "orchestrator_output": "1.0",
    "stage_output": "1.0"
  },
  "prompt_manifest_hash": "sha256:...",
  "tool_registry_hash": "sha256:..."
},
"artifact_index": [
  {
    "path": "inputs/red_simulation_data.json",
    "type": "input",
    "content_class": "sanitized",
    "sha256": "..."
  },
  {
    "path": "stages/06_evaluate/scorecard.json",
    "type": "scorecard",
    "content_class": "aggregated",
    "sha256": "..."
  }
],
"hashes": {
  "pack_hash": "sha256:..."
}
}
````

Mandatory fields:

* `format`, `brc_version`
* `battle_run_id`, `battle_type`, `created_at`
* `compatibility.*`
* `hashes.pack_hash`
* `artifact_index` must include at least: `manifest.json`, `metadata.json`, `pack_hashes.json`, `scorecard.json`

---

## 6) `metadata.json` — battle context + stage plan + flags

Purpose:

* UI + replay engine reads the stage plan and feature flags from here.

Recommended:

```json
{
  "battle_goal": "Test defenses against mule-network cashout chain",
  "stage_plan": [
    {"id": 0, "name": "prepare", "description": "Init + health checks"},
    {"id": 1, "name": "plan", "description": "Threat plan + defense plan"},
    {"id": 2, "name": "simulate", "description": "Red creates scenarios and evidence"},
    {"id": 3, "name": "detect", "description": "Blue detects and explains"},
    {"id": 4, "name": "mitigate", "description": "Blue recommends/executes mitigations"},
    {"id": 5, "name": "patch_rules", "description": "Generate RSB proposals"},
    {"id": 6, "name": "evaluate", "description": "Score + metrics"},
    {"id": 7, "name": "postmortem", "description": "Lessons + next actions"}
  ],
  "feature_flags": {
    "agentic_rag_enabled": true,
    "graph_reasoning_enabled": true,
    "xai_journal_enabled": true
  },
  "privacy_mode": "bank_neutral",
  "export_policy_id": "P001"
}
```

---

## 7) Orchestrator output per stage (War Room contract)

### 7.1 `stages/*/orchestrator_output.json`

This is the **canonical stage record** that War Room must surface “per stage”.

Recommended:

```json
{
  "battle_run_id": "000042",
  "stage": {"id": 3, "name": "detect"},
  "started_at": "2026-02-02T03:16:20Z",
  "ended_at": "2026-02-02T03:16:55Z",
  "status": "completed",
  "inputs": [{"ref": "inputs/red_simulation_data.json"}],
  "participants": ["TEAM-BLUE", "TEAM-XAI"],
  "outputs": [
    {"ref": "stages/03_detect/blue_team_000042_20260202_031621.json", "type": "team_output"},
    {"ref": "stages/03_detect/xai_summary.json", "type": "xai"}
  ],
  "metrics": {
    "detections": 12,
    "false_positives_est": 0.02,
    "latency_ms_p95": 180
  },
  "notes": "Blue flagged mule cashout chain via velocity + device reuse + graph fan-out"
}
```

Hard constraints:

* No raw payloads. Anything sensitive becomes evidence refs (hashed/bucketed).
* `outputs[]` must list every artifact required by UI.

---

## 8) Inputs — red team simulation data (mandatory)

### 8.1 `inputs/red_simulation_data.json`

This should include:

* battle scenario description
* synthetic entities (actors, devices, merchants, mule accounts) — **no real bank data**
* event timeline / tx chain
* expected outcomes (optional)
* seed / randomization knobs (optional)

Suggested structure:

```json
{
  "scenario_id": "SCN-ATO-MULE-01",
  "scenario_name": "ATO mule-network cashout chain",
  "entities": {
    "customers": [{"id":"C1","bucket":"new"}, {"id":"C2","bucket":"tenured"}],
    "devices": [{"id":"D1","bucket":"reused"}],
    "merchants": [{"id":"M1","mcc":"6011"}]
  },
  "events": [
    {"t":"2026-02-02T03:15:05Z","type":"login","actor":"C1","device":"D1"},
    {"t":"2026-02-02T03:15:10Z","type":"transfer","from":"C1","to":"C2","amount_bucket":"p95"}
  ],
  "attack_intent": "cashout",
  "ground_truth": {"fraud": true}
}
```

---

## 9) Telemetry + evidence

### 9.1 `telemetry/evidence_catalog.json`

Only hashed/bucketed/redacted evidence:

```json
{
  "evidence": [
    {"evidence_id": "EVID-1", "type": "device_reuse", "hash": "sha256:...", "bucket": "high"},
    {"evidence_id": "EVID-3", "type": "velocity_spike", "hash": "sha256:...", "bucket": "p95"}
  ]
}
```

---

## 10) Scorecard (mandatory for judge clarity)

### 10.1 `stages/06_evaluate/scorecard.json`

```json
{
  "battle_run_id": "000042",
  "battle_type": "ato_mule_network",
  "winner": "TEAM-BLUE",
  "score": {
    "attack_success_rate": 0.12,
    "detection_recall": 0.91,
    "false_positive_rate": 0.02,
    "mitigation_time_s": 45,
    "explainability_score": 0.88
  },
  "highlights": [
    "Blue caught 91% of attacks within p95 180ms",
    "XAI explanations were consistent across detections",
    "Rule patches proposed: 2"
  ]
}
```

---

## 11) BRC export/import requirements (UI + backend)

### 11.1 War Room UI

* Must show **Orchestrator outputs per stage** (read `stages/*/orchestrator_output.json`)
* Must show **Team outputs per stage** (tabs)
* Must show **Artifacts explorer** (tree + preview)
* Must show **Scoreboard bar** (winner + key KPIs)

**Download button**

* “Download artifacts as BRC” button
* Calls backend export endpoint and downloads:

  * `<battle_type>_<battle_run_id>_<timestamp>.brc`

### 11.2 Battle Replay UI

* “Import BRC” button
* Runs validation first (structure + schema + hash + prohibited content)
* Supports replay modes:

  1. **Read-only replay**
  2. **Re-evaluate**
  3. **Re-run defense (sandbox)**
  4. Full rerun (optional future)

---

## 12) Validation + integrity

### 12.1 `pack_hashes.json` (mandatory)

```json
{
  "hash_algo": "sha256",
  "files": {
    "manifest.json": "sha256:...",
    "metadata.json": "sha256:...",
    "stages/06_evaluate/scorecard.json": "sha256:..."
  }
}
```

### 12.2 Prohibited content policy (must-not-contain)

BRC must not contain:

* PII (names/emails/phones/account numbers)
* internal URLs/domains/IPs
* employee/case/ticket IDs
* vendor/client names
* raw transaction payloads / screenshots with identifiers

Only hashed/redacted evidence + aggregated metrics allowed.

---

## 13) Hackathon-winning “wow” features (recommended)

* Animated battle timeline playback (scrub through `orchestrator/stage_state.jsonl`)
* Mule network graph visualization (`artifacts/mule_network_graph.json`)
* Rules connected map visualization (`artifacts/rules_connected_map.json`)
* Auto-generated `postmortem.md` with:

  * Top 5 detected patterns
  * Top 3 recommended controls
  * Top 2 rule patch proposals
* BRC diff view: compare scorecards between two BRCs (before/after tuning)

````

---

```md
# BRC_DEV_plan.md — Phase-by-Phase Development Plan (Fraud Forge BRC)

## Goal

Implement **Battle Run Capsule (.brc)** end-to-end:
- War Room can **export** a `.brc` containing:
  - inputs (red simulation JSON)
  - orchestrator outputs per stage
  - team/agent outputs
  - telemetry + scorecard
  - XAI artifacts
  - integrity hashes
- Battle Replay can **import** a `.brc`, render it, and optionally **re-evaluate / re-run defense** in sandbox
- This becomes a core “wow” differentiator: **traceability + portability + replayability**

---

## Core components

### Backend
1. **Battle Orchestrator**
   - Runs stages and emits canonical orchestrator outputs
2. **Artifact Store**
   - Stores stage outputs with tags (sanitized/hashed/aggregated)
3. **BRC Packager**
   - Builds `.brc` from artifact store + inputs + metadata
4. **BRC Validator**
   - Structure + schema + hashes + prohibited-content scan
5. **BRC Importer**
   - Imports `.brc` back into replay storage
6. **Replay Engine**
   - Read-only replay + re-evaluate + rerun-defense modes
7. **XAI Service**
   - Produces stage-wise and battle-wise explanations
8. **Scoring Service**
   - Produces scorecards and metrics

### UI
1. **War Room**
   - Stage timeline + orchestrator outputs per stage + export button
2. **Battle Replay**
   - Import + validate + render + compare + rerun buttons

---

## Phase 0 — Lock format & schemas (foundation)

### Deliverables
- `schemas/brc_schema.json`
- `schemas/orchestrator_output_schema.json`
- `schemas/stage_output_schema.json`
- `schemas/scorecard_schema.json`
- `policies/brc_prohibited_content.yaml`
- Naming utilities for stage artifacts and final `.brc` filename

### Tasks
- Finalize stage list: prepare/plan/simulate/detect/mitigate/patch_rules/evaluate/postmortem
- Define minimum viable artifacts per stage for UI
- Decide content-class tags:
  - `raw` (disallowed)
  - `sanitized`
  - `hashed`
  - `aggregated`

### Exit criteria
- A mocked BRC validates against schemas and structure rules.
- Prohibited-content scan blocks obvious PII patterns.

---

## Phase 1 — Orchestrator emits stable outputs per stage

### Deliverables
- `stages/<stage>/orchestrator_output.json` (per stage)
- `orchestrator/stage_state.jsonl` timeline stream
- Team outputs produced per stage stored into artifact store

### Tasks
- Add `StageOutputEmitter` in orchestrator:
  - stage start/end events
  - outputs list (paths)
  - stage-level metrics summary
- Ensure stable paths and deterministic naming

### Exit criteria
- Each stage produces orchestrator output + at least one team output where applicable.

---

## Phase 2 — BRC packaging engine (export)

### Deliverables
- `POST /brc/export`
- Packaging module:
  - writes `manifest.json`, `metadata.json`, `pack_hashes.json`
  - copies inputs (red simulation JSON)
  - pulls stage artifacts from artifact store
  - produces `.brc` stream

### Tasks
- Support export options:
  - include agent-level outputs (yes/no)
  - include full telemetry (yes/no)
  - include graphs/maps (yes/no)
- Prevent zip path traversal
- Deterministic file order for reproducible hashes

### Exit criteria
- War Room can export `.brc` and validator passes.

---

## Phase 3 — War Room UI: orchestrator outputs per stage + export button

### Deliverables
- Stage timeline reads `stage_state.jsonl` and stage outputs
- Stage details panel shows:
  - orchestrator output summary
  - team outputs tabs
  - artifact viewer (JSON/MD)
- “Download BRC” button triggers `/brc/export`

### “Judge-wow” add-ons
- Scoreboard bar: winner + recall + FP + mitigation time + XAI score
- Playback slider for timeline

### Exit criteria
- A judge can watch a battle and export the full run in one click.

---

## Phase 4 — Import + validation pipeline (Battle Replay UI)

### Deliverables
- `POST /brc/validate` (upload returns validation report)
- `POST /brc/import` (imports into replay storage)
- Replay UI:
  - upload → validate → preview → import → render

### Validator checks
- ZIP sanity checks + size limits
- required files present
- schema validation
- `pack_hashes.json` hash verification
- prohibited-content scan
- compatibility checks (runtime/tool/prompt versions if present)

### Exit criteria
- Imported BRC renders the full stage timeline + artifacts.

---

## Phase 5 — Replay modes (where value multiplies)

### Deliverables
1) **Read-only replay**
2) **Re-evaluate**
   - recompute scorecard with current scoring rules
3) **Re-run defense (sandbox)**
   - reuse stored red inputs; rerun blue detection/mitigation
4) Full rerun (optional future)

### Tasks
- Build replay engine with safe sandbox isolation
- Add deterministic hooks:
  - seed in manifest
  - record tool/prompt hashes for safe rerun gating
- Add comparison view:
  - old scorecard vs new scorecard (delta + explanation)

### Exit criteria
- Import a BRC and show score delta after re-evaluation.

---

## Phase 6 — Feedback loop to AMC/RSB (winner feature)

### Deliverables
- From BRC generate:
  - `stages/07_postmortem/postmortem.md`
  - `stages/07_postmortem/lessons_distilled.json`
  - `stages/05_patch_rules/rsb_proposals.json`
- Optional: “Export RSB from battle” and “Append lessons to AMC” actions

### Exit criteria
- One battle run generates:
  - BRC + postmortem + rule proposals
  - (optional) AMC patch candidate

---

## Phase 7 — Hardening (post-hackathon)

- Signing + verification (optional)
- Stronger PII detection (regex + NER)
- RBAC gates for export/import/rerun
- Full audit logging

---

## Hackathon demo script (use exactly this)

1) Run battle in War Room; show stage-by-stage timeline.
2) Open a stage and show orchestrator output + team outputs + XAI summary.
3) Show scorecard.
4) Click **Download BRC**.
5) Open Battle Replay → import BRC → validation passes.
6) Click **Re-evaluate** (or **Re-run defense**) → show improvement delta.
7) Show auto-generated postmortem + fix proposals.

This makes judges remember: **replayable battles + portable evidence + explainable decisions**.

---