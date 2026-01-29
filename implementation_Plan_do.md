# Fraud Forge — Implementation Plan (derived from `doc.pdf`)

> Source: handwritten design notes in `doc.pdf` (4 pages). fileciteturn11file0

## 0) Delivery goal
Build a **hackathon-ready MVP** that demonstrates:
- Multi-team war loop state machine (R→B→Purple→Green→Black→Orange→White, Gold XAI)
- RSB/RuleSpec + Python RuleCode workflow
- APMC portable memory capsule + “Brain Surgery” 3-frame UI
- Visual patch + RBAC approvals
- LLM+RAG on fraud rules

---

## 1) Suggested MVP Tech Stack (pragmatic)
- **Backend:** FastAPI (Python)
- **UI:** Streamlit (fast) or React/Next (polish). For hackathon speed: Streamlit.
- **State/Jobs:** In-memory queue initially; optional Redis
- **Storage:** SQLite/Postgres + file-based artifact store
- **RAG:** Chroma/FAISS + local embeddings; OpenAI-compatible LLM endpoint via API key
- **Packaging:** Docker Compose for one-command run

---

## 2) Core modules to implement

### 2.1 RBAC + Identity
- Roles: SA, BA (minimum)
- Middleware:
  - session auth
  - permission checks per route/action
- Audit log table:
  - actor, action, target artifact, decision, timestamp, metadata

### 2.2 Team/Agent Registry
- Config-driven `teams.yaml` and `agents.yaml`
- Endpoints:
  - GET /teams, /agents
  - POST /runs (start), /runs/{id}/step, /runs/{id}/replay

### 2.3 War Loop Orchestrator (state machine)
Implement stages:
1. RED_SIMULATE
2. BLUE_DETECT
3. PURPLE_RULESPEC_UPDATE
4. GREEN_BUILD_PATCH
5. BLACK_STRESS_TEST
6. ORANGE_REVIEW_APPROVE (RBAC gate)
7. WHITE_COMPLIANCE_AUDIT (RBAC gate)
8. GOLD_XAI_PACK (can run in parallel or at end)
9. DONE

**Fail handling:**
- if BLACK fails: go back to PURPLE with failure reason and required fixes.

**Modes:**
- Auto-run and Manual step-run

### 2.4 Artifact Store (versioned)
Store artifacts by type:
- Scenario, Telemetry, RuleSpec(MD), RuleCode(PY), Patch, StressReport,
  ApprovalDecision, XAIReport, CompliancePack, APMC, RSB
Provide lineage links:
- artifact_id -> parent_ids -> run_id -> stage

### 2.5 RSB Manager
Implement:
- Import RSB zip
- Parse manifest (or derive from folder structure)
- Validate required files:
  - RuleSpec.md
  - RuleCode.py
  - patcher script (optional)
- Display tree + file viewer
- Merge conflicts UI (MVP: side-by-side diff)
- Output staged RSB zip

### 2.6 APMC Manager
Implement:
- Import APMC zip
- Read metadata (version, timestamp, team, summary)
- Validate schema
- Attach to run
- Provide “apply” operation that affects Purple/Green decisions

### 2.7 Brain Surgery UI (3-frame)
UI layout:
- Left: baseline model/rules snapshot
- Middle: APMC-loaded snapshot
- Right: merged snapshot
Show:
- differences in rules, thresholds, features
- “merge/apply” button (RBAC gated)
- rollback button

### 2.8 Visual Patcher
- Diff viewer (RuleSpec md + RuleCode py)
- Apply patch controls:
  - accept/reject hunks (MVP: accept all + selective reject later)
- Run tests:
  - unit tests for RuleCode
  - integration test stub
- Build new staged RSB

### 2.9 LLM + RAG
**RAG ingestion pipeline**
- Index RuleSpecs + taxonomy files into vector DB
- Chunking + metadata tags (team, rule_id, fraud_family)

**RAG usage**
- Purple: propose RuleSpec improvements
- Green: propose patch snippets
- Gold: generate explanation pack with citations to retrieved chunks

**Security**
- API key stored as env var for hackathon; vault later

---

## 3) UI pages (MVP)
1. Login
2. Command Center (Run status + quick demo run)
3. War Room (timeline + stage outputs + step controls)
4. RSB Manager (import/inspect/validate/stage)
5. APMC Manager (import/inspect/apply)
6. Brain Surgery (3-frame comparison)
7. Visual Patcher (diff + apply + tests)
8. Approvals (Orange + White queues)
9. XAI Viewer (Gold report + citations)
10. Audit Log Viewer

---

## 4) Demo flow (what you show judges)
1. Start “Demo Run” (R→B)
2. Show detection gap → Purple proposes RuleSpec update (RAG citations)
3. Green generates patch → Visual Patcher shows diff
4. Black stress test fails once → automatic return to Purple (show loop)
5. Stress test passes → Orange approves → White audits
6. Gold generates XAI pack → export Story Report

---

## 5) Hackathon-grade improvements (high impact)
- Deterministic seed + replay button (never fail live)
- “SAFE_TO_PROCEED” indicator when approvals done
- Live scoreboard: time-to-immunity, success rate, regressions
- Export bundle (Evidence Pack): zipped run + artifacts + XAI + audit log
- Synthetic-only watermark + “no real fraud” guardrails banner

---

## 6) Build plan (7 steps)
1. Create schemas + artifact store layout
2. Implement RBAC + audit logging
3. Implement orchestrator + run APIs
4. Implement RSB/APMC importers + validators
5. Implement War Room UI + stepper + evidence panels
6. Implement Brain Surgery + Visual Patcher UI
7. Implement LLM+RAG + Story Report export

---

## 7) Definition of Done
- `docker compose up` launches the app
- Demo run completes with at least one fail→purple loop and final success
- Brain Surgery 3-frame view works on an imported APMC
- RSB import→validate→stage works
- Visual patch applies a change and tests run
- Approvals are RBAC gated and logged
- XAI pack is generated and exportable
