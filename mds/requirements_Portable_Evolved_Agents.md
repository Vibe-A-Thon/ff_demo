# Fraud Forge — Portable Evolved Agents (Bank A ➜ Bank B) Requirements
**Purpose:** Enable Bank B to receive **evolved Fraud Forge agents** (experience, memory, model refs/artifacts, rules/fixes, and battle learnings) from Bank A **without transferring any Bank A data**, and import them into the same Fraud Forge runtime running in Bank B.  
**Generated:** 2026-02-01 23:32:58

---

## 0) Context & Goal
Fraud Forge is already mature in **Bank A** with evolved AI agents and strong fraud defenses. A new **Bank B** wants Fraud Forge as a software service and wants to start with **evolved agents**, not “newbie agents.”

### Transfer artifacts (existing concepts)
- **AMC (Agent Memory Capsule)**: `.amc` (zip-like) generated **one per Team**, containing multiple files per agent (memory, logs, state, etc.) on demand.
- **RSB (Rule Suite Box)**: `.rsb` (zip-like) generated **per lost fraud detection** containing rules + fixes.
- **BRC (Battle Run Capsule)**: `.brc` (zip-like) generated per battle, containing run trace details.

### Target experience
Bank B imports these artifacts and immediately gets **battle-proven, evolved agents** while ensuring:
- no Bank A identifiers/PII,
- same Fraud Forge version compatibility,
- deterministic replay + auditable lineage,
- safe and controlled activation.

---

## 1) High-Level Feature Set
### 1.1 Portable Evolved Agents Program
1. **Export Evolved Agents** (Bank A)
2. **Package Portable Evolution Pack** (Admin UI)
3. **Validate Pack** (pre-import validation + signature)
4. **Import into Bank B** (Brain Surgery UI)
5. **Activate & Calibrate** (safe enablement, bank-specific mapping)
6. **Prove Readiness** (synthetic eval suite + report)

---

## 2) Core Portability Assumptions (Given / Confirmed)
These are treated as *true* for this capability:
- AMC contains **no raw Bank A artifacts** (PII, acct numbers, URLs, employee/case IDs, vendor refs).
- RSB rules are **canonical** (no Bank A-specific field names, channel IDs, proprietary score names).
- BRC traces contain **no raw payloads**, only hashed/redacted evidence and aggregated telemetry.
- Bank A and Bank B run the **exact same Fraud Forge version** (runtime/tool/prompt/schema versions).

> Note: Even if raw Bank A artifacts are removed, team memories may still have “soft identifiers” unless intentionally distilled (see §6).

---

## 3) New Required Artifacts (Minimum Additions)
AMC/RSB/BRC are necessary but need “glue” to make portability reliable.

### 3.1 Transfer Manifest (mandatory)
Create `TRANSFER_MANIFEST.json` (or `.yaml`) included in the exported pack:
- Fraud Forge app version + build hash
- Agent runtime version
- AMC/RSB/BRC schema versions
- Prompt template versions (hashes)
- Tool registry version (hash)
- Model references (ID, provider, version pin)
- Embedding model ID + vector dimension (if RAG/KAG exists)
- Feature flags used during learning/battles
- Export timestamp, export policy ID
- Pack ID + lineage info (source bank ID hashed / anonymized), signing metadata

**Why:** Bank B must reliably validate compatibility prior to import.

### 3.2 Schemas + Validators (mandatory)
Provide and enforce:
- `schemas/amc_schema.json`
- `schemas/rsb_schema.json`
- `schemas/brc_schema.json`
- `validators/` or at least a CLI: `ff validate-capsule <file>` and `ff validate-pack <pep>`

Validation must check:
- schema compliance
- version compatibility
- no prohibited fields (Bank A artifacts)
- tool/prompt contract compatibility (see §3.3)
- signature integrity (if enabled)

### 3.3 Prompt & Tool Contract Pack (mandatory)
Include in pack:
- `prompt_manifest.yaml` (prompt template IDs + hashes + versions)
- `tool_registry.yaml` (canonical tool schema definitions + versions)

**Why:** Agent memory/behavior assumes tool names, argument shapes, prompt structure. Prevent Tool X vs Tool X_v2 mismatches.

### 3.4 Sanitization Report (future scope; include design now)
For hackathon, can be shown as “planned / optional,” but requirements should include:
- `SANITIZATION_POLICY.yaml` (rules)
- `SANITIZATION_REPORT.md/json` (proof + summary stats)

---

## 4) Optional Portability Extensions (Architecture-Dependent)
### 4.1 Model Artifacts / Model Bundle (recommended when training exists)
If Bank A evolved via fine-tuning/LoRA/reward models/calibration:
- Exportable via **Brain Surgery UI**
- Packaged as part of **AMC** for the corresponding team (or separate `model_bundle/` in the pack)
- Include `model_card.md` + `model_reference.json`

**Security note:** weights can leak training info; include future “privacy gate” (distillation or approval).

### 4.2 Retrieval Assets (if RAG/KAG exists)
Do **not** ship Bank A indexes. Ship only bank-neutral retrieval configs:
- retrieval router config
- ranker/reranker config
- KG schema + query templates
- playbooks/pattern libraries

### 4.3 Evaluation / Benchmark Pack (highly recommended)
Include synthetic evaluation to prove “evolved agents”:
- `synthetic_eval_suite/cases.jsonl`
- `synthetic_eval_suite/expected_metrics.yaml`
- `synthetic_eval_suite/runner.py`
- Generated report in Bank B after import: `eval_report.md`

---

## 5) Portable Evolution Pack (PEP) — Packaging Requirement
Add an Admin UI page to generate a single portable bundle:
`FF_PORTABLE_EVOLUTION_PACK.pep`

### 5.1 Pack structure (required)
```
FF_PORTABLE_EVOLUTION_PACK.pep
  /capsules
    team_red.amc
    team_blue.amc
    ...
    fraud_fix_001.rsb
    fraud_fix_002.rsb
    battle_YYYY_MM_DD.brc
  /contracts
    tool_registry.yaml
    prompt_manifest.yaml
    schemas/
      amc_schema.json
      rsb_schema.json
      brc_schema.json
  /governance
    TRANSFER_MANIFEST.json
    (future) SANITIZATION_POLICY.yaml
    (future) SANITIZATION_REPORT.md
  /validation
    validate_pack.py (or CLI instructions)
    synthetic_eval_suite/
      cases.jsonl
      expected_metrics.yaml
```
Optional:
```
  /model_bundle
    lora_adapters/
    model_card.md
```

---

## 6) Memory Transfer Safety Requirements (Distillation Layer)
Your AMC is “Team memory” (not explicitly bank-neutral). To safely port without Bank A references, add a distillation pipeline.

### 6.1 Distillation function (required)
Before export, process AMC contents:
- Convert raw narratives/log lines → abstracted “lessons learned”
- Replace internal system references with canonical categories
- Replace concrete indicators with generalized forms (hashing/binning/ranges)
- Remove or generalize any free-text that can embed Bank A identifiers

### 6.2 Policy for prohibited content (required)
Define “must-not-contain” rules applied during distillation + validation:
- PII patterns (names, emails, phone, account numbers, addresses)
- internal URLs/domains/IPs
- employee/case/ticket IDs
- vendor/client names
- exact transaction IDs, exact timestamps tied to real events (use bucketing)

### 6.3 Evidence preservation (required)
Preserve usefulness by keeping:
- pattern IDs, tactic IDs, telemetry categories
- hashed exemplars
- aggregated statistics and weights

---

## 7) Import & Activation Workflow (Bank B)
### 7.1 Brain Surgery UI — Import experience (enhanced)
- Import `.pep` OR individual `.amc/.rsb/.brc`
- Pre-import checks:
  - schema + compatibility + tool/prompt contract checks
  - policy checks (prohibited content scan)
  - signature check (if enabled)
- Import preview:
  - list teams/agents affected
  - show what will be updated/merged/replaced
  - show conflicts + resolution options

### 7.2 Merge policies (required)
- **AMC**: Replace / Merge (append+dedup) / Merge + Bank-B calibration layer
- **RSB**: Proposed / Sandbox-only / Approved
- **BRC**: Store as evidence + replayable runs

### 7.3 Activation gates (required)
- Imported agents start in **Sandbox/Simulation** mode
- Require Admin approval to enable production mode
- Optionally require synthetic eval pass threshold

---

## 8) UI Requirements
### 8.1 Admin UI — Portable Evolution Pack page (new)
- Select export scope:
  - Teams
  - RSB fixes (taxonomy/date/severity)
  - BRC battles (date/tags)
  - Include model bundle (toggle)
  - Include eval suite (toggle)
- Export action:
  - Generate `.pep`
  - Show pack ID, size, hash, versions
  - Download

### 8.2 Brain Surgery UI — Import page (enhanced)
- Upload `.pep` or `.amc/.rsb/.brc`
- Validate
- Preview changes
- Import
- Activate (sandbox first)
- Run eval suite + show report (optional)

---

## 9) Backend/API Requirements
### 9.1 Core services
- `packaging_service`: build/verify `.pep`
- `manifest_service`: create/validate transfer manifest
- `schema_service`: load schemas and validate
- `distillation_service`: sanitize and distill AMC memory
- `import_service`: import & merge capsules
- `eval_service`: run synthetic suite and produce report

### 9.2 APIs (examples)
- `POST /export/pep`
- `POST /import/pep/validate`
- `POST /import/pep/preview`
- `POST /import/pep/commit`
- `POST /import/activate`
- `POST /eval/run`

---

## 10) Non-Functional Requirements (NFR)
1. **Compatibility-first**: strict version pinning via manifest; block import on mismatch.
2. **Safety**: prohibited-content scan on import/export; default sandbox activation.
3. **Performance**: validate/import within hackathon-acceptable time.
4. **Observability**: audit log every export/import/merge/activation action.
5. **Reproducibility**: store hashes for packs and capsule entries.
6. **Extensibility**: new capsule types in future without breaking older packs.

---

## 11) Acceptance Criteria
- Bank A can export `.pep` containing selected AMC/RSB/BRC plus contracts + manifest.
- Bank B can validate and import with a clear preview and no runtime errors.
- Imported agents appear as “Evolved vX” and can run in sandbox.
- Synthetic eval suite runs in Bank B and generates `eval_report.md`.
- Import is blocked on version mismatch.
- Prohibited-content scan reports 0 Bank A artifacts (or blocks import).

---

## 12) Deliverables (for GitHub Copilot)
- Schema files + validators
- Transfer manifest generator + validator
- Admin UI export page + Brain Surgery import page
- Packaging engine for `.pep`
- Distillation pipeline for AMC
- Synthetic eval harness + reporting
