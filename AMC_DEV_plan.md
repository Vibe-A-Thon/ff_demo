# AMC_DEV_plan.md — Phase-by-Phase Development Plan (Fraud Forge: Agent Memory Capsule)

This plan is designed so GitHub Copilot can implement **Agent Memory Capsule (AMC)** end-to-end as a first-class, enterprise-grade capability inside Fraud Forge — with “judge-wow” UX for a hackathon demo and a clean path to production readiness.

**Contract baseline:** `amc_Format_understanding.md` is the source-of-truth for AMC intent, recommended structure, and safety requirements. fileciteturn16file0

---

## 1) Outcomes (definition of done)

### 1.1 Hackathon demo outcome (must hit)
In a live demo, a judge should see this in < 3 minutes:

1) Open **AMC Explorer** → drag-drop an `.amc` file
2) See **Team Evolution Summary**:
   - battles participated, win rate, evolution level
   - top learned patterns (“distilled lessons”)
   - last distilled timestamp
3) Click **Safety Scan** → shows ✅ “No PII / No Bank Identifiers” + ✅ Hash verified
4) Click **Memory Diff** (AMC v1 vs v2) → highlights what changed & why
5) Click **Import Preview** → shows exactly what will change
6) Click **Import (Sandbox)** → activate evolved agents in sandbox
7) Run a quick synthetic scenario → show improved scorecard delta

If you do this smoothly, the audience perceives you built “portable evolved AI” with governance.

### 1.2 Production outcome (future-proof)
- AMC can be **exported/imported/validated/diffed** consistently
- AMC contents are **schema-validated**, **hashed**, and **policy-scanned**
- AMC is **portable** across banks in a bank-neutral manner (no sensitive artifacts)
- AMC is **compatible** with runtime prompt/tool contracts (hash pinned)
- AMC integrates with **BRC** (battle learnings distilled into AMC) and **RSB** (rule improvements referenced)

---

## 2) Guiding principles (how AMC wins)

1) **Layered memory, not raw logs**: store semantic/episodic/procedural/distilled layers; logs must be aggregated/sanitized.
2) **Schema + hashes by default**: every file validates and is hashed.
3) **Contracts pinned**: prompt/tool registry hashes prevent “works on my bank” breakage.
4) **Deterministic import behavior**: replace/merge/dedup is predictable.
5) **Human-readable artifacts**: every AMC includes a short Markdown summary for judges and reviewers.
6) **Same ArtifactStore** for AMC/RSB/BRC: one foundation, multiple capsule types.

---

## 3) Minimum AMC capability set

### 3.1 Functional capabilities
- Export AMC (team-level)
- Validate AMC (structure + schema + hashes + policy scan)
- Inspect AMC (manifest + agents list + memory stats)
- Import AMC with modes:
  - Replace
  - Merge (append + dedup)
  - Merge + Calibration Layer (future)
- Diff two AMCs (what changed)
- Catalog AMCs (local repository)
- Sandbox activation of imported AMC

### 3.2 Non-functional capabilities
- No sensitive content in AMC (PII and bank identifiers blocked)
- Compatibility enforced (FF version, runtime version, prompt/tool hashes)
- Integrity enforced (pack_hashes.json)
- RBAC enforced (who can export/import)
- Audit events recorded for every AMC action

---

## 4) Repo layout (Copilot-friendly)

Recommended backend layout additions (aligned with your existing structure used for BRC/RSB):

```
backend/app/services/capsules/
  amc/
    amc_packager.py
    amc_validator.py
    amc_importer.py
    amc_merger.py
    amc_differ.py
    amc_catalog.py
    schemas/
      amc_schema.json
      agent_profile_schema.json
      memory_schema.json
    policies/
      amc_prohibited_content.yaml
    utils/
      hashing.py
      zip_safe_extract.py
      json_schema_validate.py
      policy_scan.py
```

UI layout additions:

```
ui/src/pages/
  AmcExplorer.tsx
  AmcDiff.tsx
  AmcImportWizard.tsx
  AmcCatalog.tsx
ui/src/components/
  ArtifactTree.tsx
  JsonViewer.tsx
  MarkdownViewer.tsx
  SafetyScanBadge.tsx
  SummaryCards.tsx
```

---

## 5) Phase-by-phase development plan

### Phase 0 — Lock AMC contracts, schemas, and policies (foundation)
**Goal:** no “free-form” capsule content; everything is validated.

**Deliverables**
- `schemas/amc_schema.json`
- `schemas/agent_profile_schema.json`
- `schemas/memory_schema.json`
- `policies/amc_prohibited_content.yaml` (regex + keyword rules)
- File naming rules + folder structure constants
- “Export scope” definition and enum:
  - memory layers included
  - logs included (sanitized only)
  - include models (true/false)
  - include battle references (true/false)
  - time window days

**Tasks**
- Define minimal mandatory files:
  - `manifest.json`
  - `team/team_profile.json`
  - `agents/<id>/agent_profile.json`
  - `pack_hashes.json`
- Define “allowed content classes”:
  - `sanitized`, `hashed`, `aggregated` (disallow `raw`)
- Define required manifest fields:
  - compatibility, prompt/tool hashes, exported agents list

**Acceptance**
- A mocked AMC zip validates completely.
- Policy scanner flags obvious PII markers.

**Hackathon boost**
- Create a “demo AMC generator” script that produces a sample AMC with believable stats and distilled lessons.

---

### Phase 1 — ArtifactStore integration + internal AMC data model
**Goal:** AMC export is a view over stored agent/team state, not a separate system.

**Deliverables**
- `TeamProfile`, `AgentProfile`, `MemoryLayer` Pydantic models
- `MemoryIndex` structure for each agent
- Standard “distilled lessons” generator interface
- `ArtifactStore` conventions:
  - team/agent memory state stored in normalized paths

**Tasks**
- Normalize how memory exists in the running system:
  - where semantic memory is stored
  - where episodic summaries exist
  - where procedural playbooks are stored
  - how tool usage stats are recorded
- Implement `MemorySnapshotBuilder(team_id)`:
  - returns structured object graph for export

**Acceptance**
- For a team in runtime, you can build an in-memory snapshot of everything needed for AMC export.

**Hackathon boost**
- Auto-generate “Team Evolution Summary” as Markdown directly from snapshot.

---

### Phase 2 — AMC Export / Packaging engine (generate .amc)
**Goal:** export produces a deterministic, portable `.amc`.

**Deliverables**
- `POST /amc/export` endpoint
- `amc_packager.py` producing `.amc` as ZIP stream
- `pack_hashes.json` generator (SHA-256 per file)
- Optional deterministic zip order for reproducibility

**Tasks**
1) Export request contract:
   - team_id
   - export_scope
   - output env tag (sandbox/prod)
2) Build directory tree as per spec:
   - `team/`
   - `agents/<id>/...`
   - `battles/` (optional)
   - `contracts/` (prompt/tool hashes)
3) Write `manifest.json` and `team_profile.json`
4) For each agent:
   - `agent_profile.json`
   - memory layers (jsonl/json/md)
   - skills, reasoning, telemetry summary
   - xai summaries
5) Compute hashes and write `pack_hashes.json`
6) Return `.amc` filename with pattern:
   - `<TeamName>_v<semver>_<timestamp>_<env>.amc`

**Acceptance**
- Exported `.amc` opens as zip and matches required structure.
- Hash file exists and contains all included files.

**Hackathon boost**
- Add export presets: “Minimal”, “Standard”, “Full”.
- Add “Include Judge Summary” toggle (defaults ON).

---

### Phase 3 — AMC Validator (structure + schema + hashes + policy scan)
**Goal:** AMC can be trusted; it must be valid before import.

**Deliverables**
- `POST /amc/validate` endpoint
- `amc_validator.py`:
  - zip structure checks
  - schema validation
  - hash validation
  - prohibited-content scan
  - compatibility checks

**Validator checklist**
1) ZIP sanity:
   - file size limit
   - no nested zip bombs
   - no path traversal entries
2) Required files exist
3) Schema validate:
   - manifest
   - agent profiles
   - memory items format
4) Hashes:
   - every file in pack_hashes exists and matches sha256
5) Prohibited content scan:
   - PII patterns
   - bank identifiers / internal URLs / case IDs
6) Compatibility:
   - FF app version/range
   - runtime version
   - prompt_manifest_hash
   - tool_registry_hash

**Acceptance**
- A valid AMC passes with green checks.
- An invalid AMC returns a detailed validation report.

**Hackathon boost**
- Show validation report UI with:
  - ✅ structure
  - ✅ schemas
  - ✅ integrity
  - ✅ safety
  - ✅ compatibility

---

### Phase 4 — AMC Import + Merge engine (Brain Surgery semantics)
**Goal:** safely adopt evolved agents (replace/merge) without surprises.

**Deliverables**
- `POST /amc/import` endpoint with mode options
- `amc_importer.py` (safe extract + register)
- `amc_merger.py` (replace/merge/dedup)
- Import preview report generator

**Import modes**
- **Replace**
  - overwrite agent memory state for the team
- **Merge (Append + Dedup)**
  - append new memory items and deduplicate by `(id|hash)`
  - merge procedural playbooks by name/version
- **Merge + Calibration Layer** (future)
  - keep learnings, but rebuild bank-specific thresholds/weights

**Conflict handling**
- Same agent_id but incompatible versions
- Missing expected tool contracts (tool_registry hash mismatch)
- Schema version mismatch

**Acceptance**
- Import produces a deterministic preview of changes and then applies them.
- Runtime loads imported agents in sandbox.

**Hackathon boost**
- “Import Preview” UI that clearly states:
  - new lessons added
  - playbooks changed
  - risk guardrails updated
  - no sensitive data detected

---

### Phase 5 — AMC Diff & Timeline (the “wow” enterprise feature)
**Goal:** show evolution visually; judges love “before vs after”.

**Deliverables**
- `POST /amc/diff` endpoint
- `amc_differ.py`:
  - manifest deltas
  - agent profile deltas
  - memory additions/removals/changes
  - procedural playbook diffs
- UI: “AMC Diff” page

**Diff outputs**
- Summary:
  - number of memory items added
  - top topics changed
  - win rate / evolution level change
- Detailed:
  - per-agent changes
  - per-memory-layer changes
- Optional:
  - “Why it changed” auto-summary (XAI style)

**Acceptance**
- Two AMCs produce a clean diff report and UI highlights.

**Hackathon boost**
- One-click “Generate Diff Story” Markdown for judges.

---

### Phase 6 — AMC Catalog + Lifecycle + Rollback
**Goal:** treat AMC like versioned releases (enterprise signal).

**Deliverables**
- `GET /amc/catalog` list
- Local repository:
  - store imported/exported AMCs with tags
- UI catalog page:
  - filter by team, version, date, env
- Rollback:
  - “activate AMC version” in sandbox
  - (prod activation is future)

**Acceptance**
- You can browse AMCs and activate one as the running team state (sandbox).

**Hackathon boost**
- “Evolved Agent Showcase” page that loads from catalog.

---

### Phase 7 — AMC ↔ Battle (BRC) feedback loop (high leverage)
**Goal:** prove agents evolve from battles.

**Deliverables**
- “Promote learnings from BRC → AMC” pipeline:
  - from postmortem lessons_distilled.json into AMC memory layers
- “Attach battle references” (battles/battle_refs.json)

**Tasks**
- Define distillation format:
  - structured “lessons” objects
  - no raw logs or identifiers
- Build `LessonDistiller`:
  - BRC artifacts → distilled lessons → semantic/episodic entries
- Update export to include new distilled lessons in memory

**Acceptance**
- After a battle, AMC export shows newly learned distilled lessons.

**Hackathon boost**
- In demo: run a battle → export AMC v1 → apply lessons → export AMC v2 → show diff.

---

### Phase 8 — Security, compliance, and performance hardening
**Goal:** credible enterprise posture even in hackathon.

**Deliverables**
- RBAC gates:
  - only Admin can import/activate
  - Associate can inspect/validate in read-only
- Audit events:
  - export/import/diff/activate
- Improved PII detection (future):
  - regex + dictionary + optional NER

**Acceptance**
- Every AMC operation generates audit log entries with request id.

**Hackathon boost**
- “Compliance Badge” panel with:
  - export policy id
  - safety scan result
  - integrity verified
  - compatibility verified

---

## 6) APIs (minimum set)

### Export / Validate / Import
- `POST /amc/export`
  - body: `{team_id, export_scope, env_tag}`
  - returns: `.amc` file stream + filename
- `POST /amc/validate`
  - upload `.amc`
  - returns: validation report (structure/schema/hash/policy/compat)
- `POST /amc/preview`
  - upload `.amc`
  - returns: what would change if imported (no write)
- `POST /amc/import`
  - upload `.amc` + mode: `replace|merge|merge_calibrate`
- `POST /amc/diff`
  - upload two `.amc` or refer to catalog ids
  - returns: diff report
- `GET /amc/catalog`
  - list stored AMCs + metadata
- `POST /amc/activate`
  - sandbox activation (prod is future)

---

## 7) CLI (optional but powerful)

- `ff amc validate <file.amc>`
- `ff amc inspect <file.amc>`
- `ff amc diff <old.amc> <new.amc>`
- `ff amc import <file.amc> --mode merge --sandbox`

CLI is great for judges: “it works as a tool, not just a UI”.

---

## 8) Testing plan (Copilot should generate)

### Unit tests
- Schema validation for manifest/agent_profile/memory layers
- Hash generation + verification
- Prohibited content scanner (positive + negative cases)
- Merge/dedup behavior with deterministic results

### Integration tests
- Run a synthetic battle → generate lessons → export AMC → validate → import sandbox → export again → diff
- Import preview equals actual applied changes

### Security tests (lightweight)
- zip path traversal is blocked
- oversized zip is blocked
- nested zip bomb limits enforced

---

## 9) Hackathon-winning AMC UX features (highest ROI)

1) **AMC Explorer** (file tree + viewers)
2) **Team Evolution Summary** card (big metrics, readable)
3) **Safety Scan Badge** (green checks)
4) **Import Preview Wizard** (clear impact before apply)
5) **Memory Diff** (before vs after)
6) **Sandbox Activation** (prove no-risk testing)
7) **Evolved Agent Showcase** (per-agent strengths + “top 5 lessons learned”)
8) **One-click “Generate Judge Report”** Markdown/PDF-ready summary (future)

---

## 10) Delivery shortcuts (if time is tight)

If you must compress scope:

**Must ship**
- Export AMC
- Validate AMC (schema + hashes)
- AMC Explorer UI
- Import in sandbox (replace mode)
- Team summary + distilled lessons

**Nice-to-have**
- Diff
- Merge import
- Advanced safety scan
- Catalog + rollback

Even the must-ship set will score highly if the UX is clean and demo-able.

---

## 11) Final acceptance criteria (AMC complete)

AMC feature is considered complete when:

- Export produces `.amc` matching format contracts and hashes
- Validate returns deterministic report and blocks unsafe/incompatible capsules
- Import supports at least Replace + Sandbox activation
- UI exposes:
  - explorer
  - safety scan
  - import preview
  - team summary
- At least one end-to-end demo exists:
  - battle → learnings → export AMC → import sandbox → improved results

---

## 12) Next step (to make this “based on real zip”)

If you share one real `.amc` sample (exported from your system), update:
- exact internal file tree and file names
- exact schemas (field-by-field)
- import/merge strategy details for your real memory format

The plan above stays the same — only schemas and paths get tightened.
