# BRC_DEV_plan.md — Phase-by-Phase Development Plan (Fraud Forge: Battle Run Capsule + Full App Build)

> **Purpose:** This plan is written so GitHub Copilot (and engineers) can implement **the full Fraud Forge application** with a strong, hackathon-winning centerpiece: **Battle Run Capsule (.brc)** + **War Room** + **Battle Replay**.  
> The `.brc` format and contracts are defined in `BRC_format_understanding.md` and must be treated as the source of truth.  

---

## 1) Outcomes (what “done” looks like)

### 1.1 Hackathon demo outcome (must hit)
A judge must be able to watch you do this live in < 5 minutes:

1) Configure teams/agents (preloaded defaults OK)  
2) Launch a battle (Red simulates, Blue detects/mitigates, XAI explains)  
3) Watch the **stage timeline** in **War Room** with outputs per stage  
4) See **scoreboard** (winner + metrics) + **graphs** (mule map / rules map)  
5) Click **Download BRC (.brc)**  
6) Go to **Battle Replay** → **Import BRC** → passes validation  
7) **Re-evaluate** (or **Re-run defense**) → show score delta & explain why  
8) Show **postmortem** + **rule patch proposals** (RSB candidates)  

If this flow is crisp, you will look like you built “enterprise-grade fraud engineering” in a hackathon.

### 1.2 Enterprise outcome (future-proof)
- BRC/AMC/RSB share one **ArtifactStore + Schema/Validator** stack
- “Portable evolution” is possible across banks (sanitized)
- LLM-agnostic agent runtime (swap models without rewrites)
- Audit logs + RBAC + compliance-ready export/import controls

---

## 2) Guiding principles (how to win)

1) **Everything is stage artifacts**: the orchestrator emits canonical JSON per stage; UI renders from it.
2) **Zip-first portability**: if it can’t be exported/imported, it doesn’t count as a “battle.”
3) **Schema-driven**: never ship “whatever JSON”; all files validate against schemas.
4) **Judge-first UX**: timeline, scoreboard, graphs, replay—optics matter.
5) **Safe by design**: no raw bank payload in BRC (hashed/redacted evidence only).
6) **Determinism where possible**: seed + manifests enable reproducible demos.

---

## 3) System architecture (minimum viable but scalable)

### 3.1 Core backend services/modules
- **Auth/RBAC**: admin vs bank associate roles
- **Team/Agent Registry**: teams, agents, capabilities, tool access
- **Battle Orchestrator**: stage runner + stage state machine
- **Agent Runtime**: tool calling, memory, prompts, LLM abstraction layer
- **Artifact Store**: write/read artifacts by battle_id, stage, team, agent
- **Capsule Services**:
  - **BRC** export/import/validate/replay
  - **AMC** export/import/validate (team memory capsule)
  - **RSB** export/import/validate (rule suite box)
- **Scoring & Evaluator**: scorecards, metrics, win conditions
- **XAI Service**: stage-wise + battle-wise explanations
- **Graph/Visualization Builder**: mule graphs, rules connected map
- **Audit/Observability**: structured logs, events, traces

### 3.2 Core UI modules
- **Login**
- **Admin Console**
  - configure teams/agents
  - tool permissions
  - feature flags
  - capsule export/import governance (optional in hackathon)
- **Battle Launcher**
  - pick battle type + scenario template + seed
- **War Room**
  - stage timeline + per-stage outputs
  - graphs + scoreboard
  - download BRC
- **Battle Replay**
  - import/validate BRC
  - read-only playback
  - re-evaluate / rerun-defense (sandbox)
  - compare two BRCs (optional wow)

---

## 4) Repo layout (Copilot-friendly)

Recommended monorepo:

```
fraud_forge/
  backend/
    app/
      main.py
      api/
        routes_auth.py
        routes_battle.py
        routes_artifacts.py
        routes_brc.py
        routes_amc.py
        routes_rsb.py
        routes_admin.py
      core/
        config.py
        logging.py
        errors.py
        security.py
      domain/
        models.py              # Pydantic models
        enums.py
      services/
        auth_service.py
        rbac_service.py
        agent_registry.py
        agent_runtime/
          llm_provider.py      # LLM-agnostic interface
          tool_router.py
          memory_manager.py
          prompt_manager.py
        battle_orchestrator/
          orchestrator.py
          stages.py
          emitters.py
        artifacts/
          artifact_store.py
          artifact_index.py
        capsules/
          brc/
            brc_packager.py
            brc_validator.py
            brc_importer.py
            replay_engine.py
            schemas/
          amc/
          rsb/
        scoring/
          evaluator.py
          scorecard.py
        xai/
          xai_service.py
        graphs/
          mule_graph.py
          rules_map.py
      schemas/                 # shared schemas
      policies/                # prohibited content rules
      tests/
  ui/
    ... (React or HTML/JS)
  docs/
    BRC_format_understanding.md
```

**Key rule:** UI never “guesses”; it reads orchestrator + artifact outputs by path from the backend.

---

## 5) Phase plan (deliverables, steps, acceptance)

### Phase 0 — Project bootstrap (Day 0–0.5)
**Goal:** running skeleton, CI, linting, local demo.

Deliverables:
- FastAPI server starts; UI loads; health checks
- `/health` endpoint
- Basic config + structured logging

Tasks:
- Create repo + baseline architecture layout
- Add `.env` config + feature flags
- Add logging (JSON logs) + request IDs

Acceptance:
- `curl /health` returns OK
- UI served locally

Hackathon boost:
- Add a “Demo Mode” toggle that seeds sample battles and preloads artifacts.

---

### Phase 1 — Domain models + ArtifactStore foundation (Day 0.5–1)
**Goal:** everything becomes an artifact; battle runs produce files.

Deliverables:
- Domain models:
  - BattleRun, Stage, Team, Agent, ArtifactRef, Scorecard
- ArtifactStore:
  - write/read by `(battle_run_id, stage, team, agent, filename)`
  - content-class tagging: sanitized/hashed/aggregated
- Artifact index:
  - list artifacts by battle, stage

Tasks:
- Implement `ArtifactStore` using local filesystem for hackathon:
  - `data/artifacts/<battle_run_id>/...`
- Add `ArtifactIndex` API:
  - `GET /artifacts?battle_run_id=...`

Acceptance:
- Can write artifacts and list them reliably.

Hackathon boost:
- Add a JSON viewer endpoint `GET /artifacts/file?path=...` with safe path rules.

---

### Phase 2 — Auth + RBAC + Admin Console (Day 1–1.5)
**Goal:** “enterprise-looking” control plane.

Deliverables:
- Roles:
  - Admin
  - Bank Associate
  - Viewer (optional)
- Admin UI pages:
  - teams, agents, role assignment
  - tool permissions
  - feature flags
- Backend:
  - JWT or session auth (keep it simple for hackathon)

Tasks:
- Implement minimal RBAC decorators in FastAPI
- Agent registry stored in JSON (hackathon) or SQLite

Acceptance:
- Admin can configure teams/agents and save config
- Associate can run battles but cannot edit registry

Hackathon boost:
- Pre-configured “One-click setup” templates (Red/Blue/XAI teams pre-created).

---

### Phase 3 — LLM-agnostic Agent Runtime (Day 1.5–2.5)
**Goal:** agents run regardless of underlying LLM provider.

Deliverables:
- `LLMProvider` interface:
  - `generate()`, `embed()` (if needed), `tool_call()` support
- Providers:
  - OpenAI (optional)
  - Local stub (demo)
  - Any other API (optional)
- `PromptManager`:
  - prompt versioning + hashes
- `ToolRegistry`:
  - canonical tool schemas + validation
- `MemoryManager`:
  - volatile memory per battle
  - persistent memory export hooks (AMC later)

Tasks:
- Define tool contract:
  - tool name, args schema, output schema
- Implement strict tool input/output validation
- Record tool call summaries (no raw payload)

Acceptance:
- A demo agent can:
  - call tools
  - produce JSON output per stage
  - be swapped from Provider A to Provider B by config

Hackathon boost:
- Add a UI switch: “LLM Provider: OpenAI / Stub / Other” to show agnosticism.

---

### Phase 4 — Battle Orchestrator + Stage Machine (Day 2.5–3.5)
**Goal:** battle runs become a stage timeline with outputs.

Deliverables:
- Orchestrator stages (from BRC spec):
  - 00_prepare
  - 01_plan
  - 02_simulate
  - 03_detect
  - 04_mitigate
  - 05_patch_rules
  - 06_evaluate
  - 07_postmortem
- `orchestrator/stage_state.jsonl` timeline events
- Per stage:
  - `stages/<stage>/orchestrator_output.json`
  - team outputs saved to artifacts

Tasks:
- Implement stage runner with:
  - start/end timestamps
  - status
  - outputs list (artifact refs)
  - metrics summary
- Implement `POST /battle/run`:
  - creates battle_run_id
  - runs async (or sync for hackathon) with streaming status

Acceptance:
- Running a battle generates stage outputs and a timeline state log.

Hackathon boost:
- Make stage transitions visible in UI in real-time.

---

### Phase 5 — Scoring + Evaluator + Scorecard (Day 3.5–4)
**Goal:** objective winner metrics.

Deliverables:
- Scorecard schema (per spec)
- Evaluator computes:
  - attack success rate
  - detection recall
  - FP rate
  - mitigation time
  - XAI score
- Stored in `stages/06_evaluate/scorecard.json`

Tasks:
- Create scoring rules per battle type (config-driven)
- Generate `stages/06_evaluate/metrics.json`

Acceptance:
- Every battle ends with a scorecard.

Hackathon boost:
- Scoreboard banner: “WINNER: BLUE” with big numbers and deltas vs baseline.

---

### Phase 6 — XAI pack (Day 4–4.5)
**Goal:** explainability that makes judges trust the system.

Deliverables:
- `xai/battle_xai_summary.md`
- `xai/decision_graph.json` (why chain)
- Stage-wise XAI outputs such as:
  - `stages/03_detect/xai_summary.json`
- Explanation style:
  - signals → evidence refs → rule/rationale → action → expected impact

Tasks:
- Build XAI templates that reference **hashed evidence IDs** from evidence_catalog
- Add “XAI score” to evaluator

Acceptance:
- Every detection/mitigation has a human-readable explanation.

Hackathon boost:
- “Explain like I’m a compliance officer” toggle in UI.

---

### Phase 7 — War Room UI (Day 4.5–5.5) **(MUST WOW)**
**Goal:** stage timeline + per-stage panels + artifacts + export button.

Deliverables:
- Stage timeline rail (left)
- Stage panel:
  - orchestrator summary
  - team output tabs (Red/Blue/XAI)
  - artifact viewer
- Scoreboard bar pinned
- Graph panels:
  - mule network
  - rules connected map
- **Download BRC button** (export)

Tasks:
- Implement `/battle/status` polling or websocket
- Render JSON and Markdown in UI
- Make “battle playback slider” from stage_state.jsonl (optional but huge)

Acceptance:
- A judge can understand the whole battle from War Room without you explaining.

Hackathon boost:
- Auto-generated `orchestrator/run_summary.md` shown as “Battle Story”.

---

### Phase 8 — BRC Export Engine (Day 5.5–6.5)
**Goal:** package battle artifacts into `.brc`.

Deliverables:
- `POST /brc/export?battle_run_id=...`
- BRC packager:
  - writes `manifest.json`, `metadata.json`, `pack_hashes.json`
  - includes `inputs/red_simulation_data.json`
  - includes `stages/*/orchestrator_output.json` and team outputs
  - includes `telemetry/`, `xai/`, `artifacts/` if present
- Deterministic zip build and stable file ordering

Tasks:
- Build artifact collector:
  - list files for battle_run_id
  - map into BRC folder structure
- Compute SHA256 for each file
- Add filename format:
  - `<battle_type>_<battle_run_id>_<timestamp>.brc`

Acceptance:
- Downloaded `.brc` opens and contains the required tree.
- Hashes validate (Phase 9).

Hackathon boost:
- Provide “Export Minimal / Export Full” options.

---

### Phase 9 — BRC Validator + Importer + Replay Storage (Day 6.5–7.5)
**Goal:** import, validate, and render BRC.

Deliverables:
- `POST /brc/validate` (upload) → validation report
- `POST /brc/import` → stores artifacts for replay
- `GET /brc/catalog` list available replays
- Safe extraction rules (no path traversal)

Validator checks:
- ZIP sanity + size limits
- required files exist
- JSON schema validation
- SHA256 matches `pack_hashes.json`
- prohibited-content scan (regex + optional NER)
- compatibility checks (prompt/tool hashes if present)

Acceptance:
- Valid BRC imports and appears in replay catalog.
- Invalid BRC is blocked with clear errors.

Hackathon boost:
- Validation report UI with green checks and “enterprise compliance vibe”.

---

### Phase 10 — Battle Replay UI (Day 7.5–8.5)
**Goal:** playback + re-evaluate + rerun-defense.

Deliverables:
- Upload/import flow:
  - upload → validate → preview → import → open replay
- Playback:
  - timeline + per-stage outputs
- Modes:
  1) read-only replay
  2) re-evaluate
  3) rerun-defense (sandbox)

Tasks:
- Read-only mode renders from imported orchestrator outputs
- Re-evaluate:
  - recompute scorecard with current evaluator
  - store new scorecard under replay session
- Rerun-defense:
  - reuse `inputs/red_simulation_data.json`
  - run only Blue+XAI stages in sandbox
  - compute new scorecard and delta

Acceptance:
- A judge sees the same battle in Replay and can re-evaluate.

Hackathon boost:
- “Compare Two BRCs” view (before vs after tuning) with delta highlights.

---

### Phase 11 — RSB/AMC integration (Day 8.5–9.5) *(optional for hackathon; huge for story)*
**Goal:** “battle produces fixes and evolution”.

Deliverables:
- `stages/05_patch_rules/rsb_proposals.json`
- `stages/07_postmortem/lessons_distilled.json`
- Buttons:
  - “Export RSB from this battle”
  - “Propose AMC memory update” (distilled, not raw)

Tasks:
- Convert battle learnings into bank-neutral patterns
- Generate rule proposals with tests stubs

Acceptance:
- Postmortem produces actionable fixes and lessons.

Hackathon boost:
- Show that Fraud Forge “learns” after each battle.

---

### Phase 12 — Observability, safety, and polish (Day 9.5–10)
**Goal:** stable demo + enterprise vibes.

Deliverables:
- Audit log events:
  - battle started/finished
  - export/import
  - replay modes invoked
- Error handling and user-friendly messages
- “Demo scenarios” library (prebuilt battle types)
- Documentation pages inside UI

Tasks:
- Add request correlation IDs
- Add rate limits for export/import (simple)
- Add full demo seed pack

Acceptance:
- Demo works repeatedly without manual fixes.

Hackathon boost:
- “Executive Mode” UI theme: minimal, clean, big metrics.

---

## 6) APIs (minimum set)

### Battle
- `POST /battle/run`
- `GET /battle/status?battle_run_id=...`
- `GET /battle/result?battle_run_id=...`

### Artifacts
- `GET /artifacts/index?battle_run_id=...`
- `GET /artifacts/file?path=...`

### BRC
- `POST /brc/export`
- `POST /brc/validate`
- `POST /brc/import`
- `GET  /brc/catalog`
- `POST /brc/replay` (mode: read_only / reevaluate / rerun_defense)

### Admin
- `POST /admin/teams`
- `POST /admin/agents`
- `GET  /admin/config`

---

## 7) Data safety rules (non-negotiable even for hackathon)

- BRC must not include raw PII or bank-internal artifacts.
- Evidence is stored only as:
  - hashed identifiers
  - buckets (p95, high/medium/low)
  - redacted strings
- Add a “privacy_mode: bank_neutral” flag in metadata.

---

## 8) Testing & quality gates (what Copilot must generate)

### Unit tests
- schema validation for manifest/metadata/orchestrator outputs/scorecard
- hash generation + verification
- prohibited content scanner

### Integration tests
- run battle → artifacts created → export BRC → validate BRC → import BRC → replay renders

### Security tests (lightweight for hackathon)
- zip path traversal test
- invalid JSON injection
- oversized file upload blocked

---

## 9) Hackathon-winning upgrades (high ROI)

1) **Battle Playback Slider**: “scrub” through stages visually  
2) **Graph Visuals**: mule network + rules map (even a simple force-graph is enough)  
3) **Score Delta** after re-evaluation/rerun: proves improvement  
4) **Postmortem generator**: top 5 learnings + next 3 controls + 2 rule patches  
5) **One-click Demo Scenarios**: ATO mule network, card testing, mule ring, phishing + takeover  
6) **LLM Provider Switch**: show “LLM-agnostic” on stage  
7) **Export Everything**: BRC includes artifacts; judges love portability + reproducibility  

---

## 10) Final implementation shortcut (if time is tight)

If you have only a short hackathon window, prioritize:

1) Orchestrator stage outputs + War Room timeline  
2) Scorecard + XAI summary  
3) BRC export + import validation  
4) Battle Replay read-only  
5) Re-evaluate mode (rerun-defense can be future)

That already looks “enterprise-grade” and will beat most hackathon entries.

