# RSB_DEV_plan.md — Phase-by-Phase Development Plan (Fraud Forge: Rule Suite Box)

This plan is written to be **copy-paste implementable by GitHub Copilot** for building the complete **RSB (Rule Suite Box)** capability inside Fraud Forge — including creation, validation, visualization, merge, deploy/rollback, and governance.

RSB is a `.rsb` **ZIP artifact** that packages a **single fraud detection rule** with:
- metadata (manifest)
- structured rule definitions (JSON)
- executable rule code (Python)
- tests + test data + results
- compliance + explainability documents
- patch scripts for deployment

> Note: Even though each RSB contains **one rule**, Fraud Forge forms a **rule network** by aggregating many RSBs.

---

## 1) Definition of Done (what “complete” means)

### 1.1 Hackathon demo outcome (must hit)
In under 5 minutes, a judge should see:
1) Upload or generate an `.rsb`
2) **RSB Validation**: ✅ structure + ✅ schema + ✅ hash + ✅ tests + ✅ compliance
3) **Rule Connected Map** (network view): node appears with color-coded attack type
4) Click node → open Rule Panel:
   - action, confidence, version
   - python code viewer (highlighted)
   - test status + edge-case cases
   - XAI narrative + business/dev explanation tabs
5) **Merge Preview**: import an updated `.rsb` with same rule_id
   - see diff and conflict flags
6) **Stage → Deploy** (sandbox):
   - run unit tests, integration tests
   - apply patch scripts into sandbox registry/suite
7) Show **Rollback** in one click to previous version

If the system makes these steps effortless, Fraud Forge looks enterprise-grade and “production-ready”, which wins hackathons.

### 1.2 Production outcome (future-proof)
- deterministic artifact structure + schema validation
- policy scan (no bank-specific artifacts)
- idempotent patching & safe rollout
- RBAC + audit trail
- rule lifecycle: proposed → staged → deployed → deprecated → archived
- compatibility support for “Portable Evolution Pack” (PEP) exports

---

## 2) RSB capability surface area

### 2.1 Core capabilities
- **RSB Parse / Inspect**
- **RSB Validate**
  - structure + schema + hash integrity + policy scan + optional static checks
- **RSB Catalog**
  - store RSBs with searchable metadata
- **RSB Visualize**
  - rule detail panels
  - multi-RSB network graph (connected map)
- **RSB Merge / Diff**
  - compare versions
  - detect conflicts (action change, breaking changes)
- **RSB Stage / Deploy / Rollback**
  - sandbox execution + tests
  - controlled patching into registry + suite
- **RSB Export / Download**
  - from UI or API, deterministic naming and hashes

### 2.2 Enterprise/hackathon “wow” add-ons
- one-click “Generate RSB” from an incident/battle summary
- rule quality scorecard (coverage, confidence, perf risk)
- autop-run tests + produce judge report (markdown)
- compliance badge panel (XAI + docs completeness)
- network map overlays (where this rule contributed in battles)

---

## 3) Recommended repo layout (Copilot-friendly)

### 3.1 Backend
```
backend/app/services/capsules/
  rsb/
    rsb_packager.py
    rsb_parser.py
    rsb_validator.py
    rsb_importer.py
    rsb_merger.py
    rsb_differ.py
    rsb_catalog.py
    rsb_deployer.py
    rsb_rollback.py
    schemas/
      rsb_manifest_schema.json
      rsb_rule_schema.json
      rsb_spec_schema.json
      rsb_xai_schema.json
      rsb_test_results_schema.json
    policies/
      rsb_prohibited_content.yaml
    utils/
      hashing.py
      zip_safe_extract.py
      json_schema_validate.py
      policy_scan.py
      python_static_checks.py
      semver.py
      sandbox_exec.py
```

### 3.2 UI
```
ui/src/pages/
  RsbExplorer.tsx
  RsbCatalog.tsx
  RsbImportWizard.tsx
  RsbDiff.tsx
  RulesConnectedMap.tsx
  RsbDeployments.tsx
ui/src/components/
  ArtifactTree.tsx
  JsonViewer.tsx
  MarkdownViewer.tsx
  CodeViewer.tsx
  ValidationBadge.tsx
  RuleScorecard.tsx
  ConflictResolutionPanel.tsx
```

---

## 4) Phase-by-Phase Development Plan

### Phase 0 — Freeze RSB contract: schemas, naming, policies
**Goal:** make RSB deterministic and validate-first.

**Deliverables**
- JSON Schemas for:
  - `manifest.json`
  - `rule/specification.json`
  - `rule/rule.json`
  - `compliance/*_xai.json`
  - `tests/test_results.json`
- `rsb_prohibited_content.yaml`
  - bank identifiers/URLs
  - employee/ticket/case id patterns
  - raw account numbers/PII patterns
- Naming conventions constants:
  - `RS_<ATTACKTYPE>_<RULEID>.rsb`
  - `<UID>` patterns for file names
- Define “required file set” and “optional file set”

**Acceptance**
- A sample RSB passes schema validation.
- RSB with missing manifest or rule.json fails fast.
- Policy scan flags obvious bank-specific strings.

**Hackathon boost**
- Prepare a “Demo RSB pack” generator to produce 2–3 RSBs quickly for demo and map visualization.

---

### Phase 1 — RSB Parser + Internal Data Model
**Goal:** parse `.rsb` into a single canonical in-memory representation.

**Deliverables**
- `rsb_parser.py`
  - safe unzip to temp
  - discover file paths by glob
  - load JSON + MD + PY files
  - compute basic metadata (size, checksum, file count)
- Pydantic models:
  - `RSBManifest`
  - `RuleSpec`
  - `RuleDefinition`
  - `CompliancePack`
  - `TestPack`
- A single `RSBObject` domain model.

**Acceptance**
- Parser returns a complete `RSBObject` for a valid `.rsb`.
- Parser errors are actionable (missing file, invalid JSON, etc.).

---

### Phase 2 — Integrity & Validation Engine
**Goal:** make RSB “trustable” before staging/deploy.

**Deliverables**
- `rsb_validator.py` with layered checks:
  1) ZIP safety:
     - size limit
     - path traversal protection
     - nested-zip bomb limits
  2) Required structure:
     - manifest.json present
     - rule/ folder exists
     - code/ folder exists
     - tests/ & compliance/ presence (required for “enterprise-grade”)
  3) Schema validation of JSON files
  4) Hash integrity (recommended):
     - create optional `pack_hashes.json`
     - verify per-file sha256
  5) Prohibited content scan (policy)
  6) Semver + rule_id consistency checks
  7) Optional python static checks:
     - disallow dangerous imports (os.system, subprocess) unless sandboxed
     - enforce detect function signature

**Validation report structure**
- `status: pass|fail`
- `checks[]`: list of checks with `name`, `result`, `message`, `severity`
- `summary`: counts and remediation hints

**Acceptance**
- Invalid RSB blocks import/staging and produces an explainable report.
- Validation report renders cleanly in UI.

**Hackathon boost**
- Show “Compliance Grade: A/B/C” derived from validation completeness (docs + tests + xai present).

---

### Phase 3 — RSB Catalog (repository + search)
**Goal:** organize RSBs like releases.

**Deliverables**
- Storage paths:
  - `artifact_store/rsb/<rule_id>/<version>/<filename>.rsb`
- Metadata index DB (SQLite/Postgres):
  - rule_id, version, attack_type, action, confidence
  - created_at, checksum
  - status: available/staged/deployed/archived
- APIs:
  - `GET /rsb/catalog`
  - `GET /rsb/{id}/download`
  - `POST /rsb/upload`
  - `POST /rsb/validate`

**Acceptance**
- Upload → validate → store → list works end-to-end.
- Search by attack_type, rule_id, version, status works.

**Hackathon boost**
- Add “Recommended next rules” based on missing coverage in the rule network (simple heuristic).

---

### Phase 4 — RSB Diff & Merge Decision Engine
**Goal:** import upgraded RSB versions safely, detect conflicts.

**Deliverables**
- `rsb_differ.py` produces:
  - manifest diff
  - rule.json field diffs
  - action/confidence/conditions changes
  - code diff summary (hash-based + optional textual diff)
  - compliance diff presence
  - tests delta
- `rsb_merger.py` merge logic rules:
  - **Upgrade** if same rule_id and semver is higher and no breaking changes
  - **Conflict** if action changes (review→block) or major version bump
  - **Add** if new rule_id
- UI conflict resolution model:
  - keep existing
  - accept new
  - stage both (if allowed by registry rules)
  - custom action/threshold (optional)

**Acceptance**
- Merge preview shows exact changes and conflict flags.
- System refuses silent breaking changes.

**Hackathon boost**
- Show “Risk impact estimator”:
  - action change implies higher customer impact
  - confidence increase implies fewer reviews but risk of false negatives (simple messaging)

---

### Phase 5 — Rule Network Graph + Rules Connected Map (multi-RSB aggregation)
**Goal:** create the “wow” visualization that demonstrates enterprise scale.

**Deliverables**
- Graph builder service:
  - nodes = rules (rule_id)
  - edges = dependencies / execution flows
    - initial version: simple heuristics or config-based edges
    - future: learned edges from BRC traces
- UI Map:
  - color by attack_type
  - size by confidence
  - shape by action
  - badges: test pass/fail, deployed/staged
- Click node opens:
  - manifest + rule spec
  - code viewer
  - test results
  - compliance tabs
- Filters:
  - attack_type
  - status (deployed/staged/available)
  - action type
  - confidence range

**Acceptance**
- Upload 5–10 RSBs and map renders fast and usable.
- Clicking nodes reliably loads RSB detail panel.

**Hackathon boost**
- “Battle overlay”: highlight rules that triggered in last battle and show contribution score (even if synthetic).

---

### Phase 6 — Staging & Sandbox Execution (tests + safe run)
**Goal:** no production deploy without sandbox proof.

**Deliverables**
- Sandbox test runner:
  - run unit tests (`pytest tests/ruleUT_*.py`)
  - run integration tests (if configured)
  - collect results → write/refresh `tests/test_results.json`
- Controlled Python execution environment:
  - dockerized runner or restricted subprocess
  - resource limits (time/mem)
- Stage status transitions:
  - uploaded → validated → staged → deployed → archived

**Acceptance**
- Clicking “Run Tests” in UI executes tests and updates status.
- Test failures block deployment.

**Hackathon boost**
- “Test coverage badge”: count edge cases, show pass rate gauge.

---

### Phase 7 — Deploy & Patch Automation (registry + suite integration)
**Goal:** deploy is predictable, idempotent, reversible.

**Deliverables**
- `rsb_deployer.py`:
  1) validate RSB again
  2) run tests in sandbox (optional forced)
  3) patch rule registry (`rule/rule_Patch.py`)
  4) patch python suite imports (`code/ruleCP_*.py`)
  5) copy rule code into rules directory
  6) mark deployed + audit log entry
- `rsb_rollback.py`:
  - restore previous version from catalog
  - reverse/replace registry entry
  - restore previous code file
- Deployment receipts:
  - `deploy_receipt.json` includes:
    - rule_id, versions, timestamps
    - who deployed
    - before/after hashes
    - test status at deploy

**Acceptance**
- Deploy to sandbox registry works and is idempotent.
- Rollback restores the previous state cleanly.

**Hackathon boost**
- One-click “Deploy to Sandbox” and “Rollback” are huge credibility signals.

---

### Phase 8 — Compliance & Explainability Surfacing (XAI first-class)
**Goal:** make every rule explainable and reviewable.

**Deliverables**
- Render `*_xai.json` with:
  - narrative
  - key factors
  - disclaimers
- Render business/dev markdown tabs
- Export “Rule Compliance Report” as Markdown (optionally PDF in future)
- UI “Explainability Panel” in Rule detail drawer

**Acceptance**
- A deployed rule always shows its XAI narrative and compliance docs.
- Missing docs trigger validation downgrade (warn/fail depending on policy).

**Hackathon boost**
- “Explainability Auto-Generator” button:
  - if XAI docs missing, generate templates using an internal agent (even if stubbed for hackathon).

---

### Phase 9 — PEP integration (portable evolved agents)
**Goal:** RSB becomes part of portability, not a standalone artifact.

**Deliverables**
- RSB export participates in `FF_PORTABLE_EVOLUTION_PACK.pep` structure:
  - `/capsules/*.rsb`
  - `/contracts/schemas/rsb_schema.json`
  - `/contracts/tool_registry.yaml` + `/contracts/prompt_manifest.yaml`
  - `/governance/TRANSFER_MANIFEST.json`
- Import preview shows RSB changes separately from AMC/BRC changes.
- Staged-by-default policy for imported RSBs.

**Acceptance**
- Bank B import can stage RSBs without auto-deploy.
- Version mismatch blocks import fast.

---

### Phase 10 — Hardening (post-hackathon roadmap)
**Goal:** enterprise readiness without scope blow-up during hackathon.

**Deliverables**
- Signing / verification (optional)
- Advanced policy scan (NER-based PII detection)
- Performance benchmarking suite
- A/B deploy mode with shadow scoring
- Rule effectiveness analytics dashboard (TP/FP estimates)

---

## 5) APIs (minimum set)

- `POST /rsb/upload` (file upload)
- `POST /rsb/validate` (file upload → validation report)
- `GET /rsb/catalog` (list/search)
- `GET /rsb/{rsb_id}` (details)
- `GET /rsb/{rsb_id}/download`
- `POST /rsb/diff` (two rsb files or ids)
- `POST /rsb/stage` (put into staged store)
- `POST /rsb/run-tests` (sandbox run)
- `POST /rsb/deploy` (sandbox/prod with RBAC)
- `POST /rsb/rollback`

---

## 6) CLI (optional but hackathon-powerful)

- `ff rsb validate RS_*.rsb`
- `ff rsb inspect RS_*.rsb`
- `ff rsb diff old.rsb new.rsb`
- `ff rsb deploy RS_*.rsb --sandbox`
- `ff rsb rollback --rule-id R-... --to-version 1.0.0`

CLI demos impress judges because it looks “real product”.

---

## 7) Testing Strategy

### Unit tests
- schema validation tests for each JSON file
- parser path detection tests
- prohibited content scan tests
- semver comparison and conflict detection tests

### Integration tests
- upload → validate → catalog → stage → run-tests → deploy → rollback
- merge upgrade vs conflict

### Security tests
- path traversal entries blocked
- oversized zip blocked
- dangerous python import patterns flagged (or sandboxed)

---

## 8) Hackathon-winning suggestions (high ROI)

1) **Rules Connected Map** with smooth interactions and drill-down
2) **Deploy-to-Sandbox + Rollback** in one click
3) **Conflict-aware merge wizard** (review→block highlights)
4) **Rule Scorecard** (tests + docs + confidence + action impact)
5) **Explainability Panel** front-and-center (XAI narrative)
6) **Judge Report Export** (Markdown) containing:
   - what the rule does
   - why it triggers
   - tests passed
   - compliance notes
7) **Battle overlay** (synthetic acceptable): “rules that saved the bank” storyline

---

## 9) Final acceptance checklist
- RSB parsing works for all required files
- validation blocks unsafe/incomplete artifacts
- catalog stores and indexes RSBs
- network map aggregates multiple rules
- diff/merge preview detects conflicts
- sandbox tests run and gate deploy
- deploy and rollback are deterministic and auditable
- compliance/XAI docs render cleanly

---

## 10) Next step to tighten this plan
If you share 1–2 real `.rsb` samples from your generator, we can:
- lock exact schema fields and optional folders
- implement the most accurate diff logic for your rule generator outputs
- add battle-derived dependency edges (from BRC traces)
