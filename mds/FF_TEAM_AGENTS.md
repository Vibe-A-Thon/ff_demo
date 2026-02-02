# Fraud Forge — FF_TEAM_AGENTS.md
*Copilot build requirements (derived from all attached artifacts).*

## 0) Goal
Build an enterprise-grade, hackathon-demo-ready **Fraud Forge** application that simulates fraud attacks (Red Team), defends and patches detections (Blue Team + Purple/Green/Black/Orange/White workflow), and produces explainability (Gold Team) with full evidence packs.

## 1) Core product requirements (must-have)
### 1.1 Platform & security
- RBAC login module with roles: **SA (System Architect)** and **BA (Business Architect)** (plus team-based roles).
- Role-based navigation and permissions per screen (view/run/edit/approve/export).
- Audit logging for every action (import/export/run/patch/approve) with immutable checksum chain.
- API key vault UI for LLM keys (masked, rotate, revoke) + per-role access.

### 1.2 Safety boundaries (non-negotiable)
- Default to **synthetic simulation** only (no real customer PII).
- All exports must include: provenance metadata + watermark + “for simulation/training” banner.
- Disable any “actionable fraud instruction” outputs; Red Team outputs are *simulated event streams and playbooks for detection testing only*.

### 1.3 Battle lifecycle + state machine
- Implement the lifecycle flow:
  - **Red → Blue → (End)**
  - Improvement loop: **Purple → Green → Black → Orange → White**
  - Failure loop routes back for iteration.
  - **Gold** overlays everything with XAI narrative generation.
- State machine must require **human intervention via RBAC** for “brain surgery” and “visual patch”.

### 1.4 Artifact systems
- **RSB (Rule Suite Box)** import/inspect/validate/test/merge/export.
- **APMC/AMC capsule** import/inspect/validate/merge/export + 3-frame brain surgery view.
- **Evidence Pack** generation + viewer (XAI + tests + logs + approvals + checksums).


## UI / UX Screens (Hackathon MVP “must show” set)

> Source: your UI screen table screenshot + notes in doc.pdf.

### 1) Battle Arena / War Room
- **Purpose:** Manual + auto-run of Red vs Blue battles; run/inspect/replay individual battles; live orchestrator view.
- **Must-have UI:** Battle timeline; side-by-side Red vs Blue reasoning streams; live KPIs; auto/manual play controls (play/pause/step/replay); turn list; session trace viewer; evidence links; scenario builder; parameter sliders; quick presets; run summary.
- **Primary interactions:** Start/stop auto-play; step-through turns; jump-to evidence; select scenario; tune parameters; run simulation; replay.

### 2) Thinking Visualizer (inside Battle Arena)
- **Purpose:** Demo-grade “reasoning stream” presentation that judges can understand in 30 seconds.
- **Must-have UI:** Stage cards (Recon → Ideation → Evasion → etc); streaming text with chunked reveal; stage progress bar; “why” highlights; confidence indicator.
- **Primary interactions:** Expand/collapse stages; pin key steps; export explanation snippet.

### 3) Brain Surgery Station
- **Purpose:** Visualize & merge knowledge / patches into the live defense brain.
- **Must-have UI:** Force-directed graph (rules/patterns/compliance/evidence); drag-drop patch nodes; sandbox hot-swap control with safety badge; knowledge graph panel; sandbox test runner.
- **Primary interactions:** Drag patch node to target; run validation; view before/after deltas; stage merge.

### 4) Difference Visualizer
- **Purpose:** Show code + RuleSpec diffs (what changed, why it’s safe).
- **Must-have UI:** Split-pane before/after diff viewer; syntax highlighting; inline comments; approve/reject controls; conflict view.
- **Primary interactions:** Accept/reject patch hunks; annotate; resolve conflicts; “stage for deploy”.

### 5) RSB Manager (Rule Suite Box Manager)
- **Purpose:** Import / inspect / merge / validate / stage RSB packages.
- **Must-have UI:** RSB list; file tree; manifest panel; RuleSpec viewer; code viewer; test results; compliance docs; merge/conflict UI.
- **Primary interactions:** Upload RSB; run preflight validation; run tests; merge to staging; export updated package.

### 6) Rule Editor + Test Runner
- **Purpose:** Author and validate RuleSpecs and rule code.
- **Must-have UI:** Structured RuleSpec form; code editor; unit/integration test runner; test results panel; coverage summary.
- **Primary interactions:** Edit spec/code; run UT/IT; save as draft; submit for approval.

### 7) Approvals & Governance
- **Purpose:** Gate approvals and enforce SoD (segregation of duties).
- **Must-have UI:** Approval queue; multi-approver workflow; validator status; SAFE_TO_PROCEED indicator; policy checklist.
- **Primary interactions:** Approve/reject with comments; request changes; escalate; view full evidence chain.

### 8) Evidence Pack Viewer
- **Purpose:** Audit + export all artifacts for a run/patch.
- **Must-have UI:** XAI narrative; test results; logs; approvals; checksum + lineage metadata; export controls.
- **Primary interactions:** Filter by scenario/family; compare runs; export snapshot (PDF/ZIP/JSON).

### 9) Metrics Dashboard
- **Purpose:** Learning KPIs and trends over time.
- **Must-have UI:** Success rate; novelty; time-to-immunity; patterns learned; before/after comparison charts; “regressions” list.
- **Primary interactions:** Toggle time range; drill-down to run; compare baselines.

### 10) Explainability Panel (embedded everywhere)
- **Purpose:** Human-readable XAI for alerts/attacks.
- **Must-have UI:** “Gold” explanation; triggered rule breakdown; similar cases; counterfactual hints.
- **Primary interactions:** Toggle plain/technical view; copy/share explanation; open evidence pack.



## Key Concepts from doc.pdf (must become requirements)

### RBAC + roles
- **Login module with RBAC**.
- Roles explicitly mentioned: **SA (System Architect)** and **BA (Business Architect)**.
- Team-based access: Red, Blue, Purple, Green, Black, Orange, Gold, White.

### Team workflow / state machine
- A **state machine process** governs “visual patch” and “brain surgery” and **requires human intervention via RBAC**.
- Flow sketched: **Red → Blue → (end)** with an improvement loop: **Purple → Green → Black → Orange → White** and a failure loop that routes back for iteration.
- **Gold** sits as the “XAI full details about project” layer (always-on explanation).

### APMC / AMC (Agent Portable Memory Capsule)
- Definition: a portable capsule containing **agent model updates/learnings post-baseline**, plus **experience** and **memory**.

### RSB (Rule Suite Box)
- Contains:
  - **RuleSpec** (MD/JSON with rule details & characteristics)
  - **Rule code** (Python with the rule/fix code)
  - **Patcher** (patches RuleSpec + rule code into target repo/registry)

### Brain Surgery (3-frame UI)
- UI must display:
  1) Frame: existing model/rules
  2) Frame: loaded APMC in model
  3) Frame: merged model (APMC + existing)

### LLM + RAG
- Need to connect to an LLM using an **open API key** and build a **RAG over fraud rules** (RuleSpecs + past evidence).



## RSB Package Support (based on RSB_MULE_NETWORK.zip)

### Supported RSB folder structure
- `manifest.json` (rule_id, rule_version, attack_type, created_at, format=RSB)
- `rule/`
  - `description.md`
  - `specification.json` (RuleSpec)
  - `rule.json` (publishable rule definition)
  - `rule_Patch.py` (patch helper)
- `code/` (rule implementation(s))
- `tests/` + `testcases/` (UT/IT + edge cases + results JSON)
- `compliance/` (business/dev explanations + XAI explanation JSON)

### RSB Manager functional requirements
- Import RSB zip, show **tree view** and **manifest**.
- Validate: schema, rule_id/version consistency, required files, checksums.
- Run tests (UT/IT/edge cases) inside sandbox; show results.
- Preview compliance + XAI docs in UI.
- Merge rules into local “rules registry” (staging → approved → deployed).
- Export merged RSB (new version) and generate **diff report**.



## APMC / AMC Capsule Support (based on blue_apmc_v1.0.0_20251229_110908.zip)

### Supported capsule structure
- `manifest.json` + `metadata.json` (agent_id, team, agent_name, version, capsule_id, created_at, format=AMC)
- `cognitive/fingerprint.json` (sha256 + summary counts)
- `experience/` + `experience.json` (battle_completed events, run payloads)
- `rules/` + `rules.json` (implemented rules, code strings, specs)
- `memory/` + `memory.json` (vector memory metadata + records)
- `snapshots.json` (captured state snapshots per battle/run)
- `lineage/history.json` (future-proof for ancestry)

### APMC Viewer requirements
- Import capsule zip; validate fingerprint/hash; show summary (rules count, snapshots count, events count).
- Browse timeline of experience events and open “battle snapshots”.
- View implemented rules (code + spec) and compare with current rules registry.
- “Propose merge” flow into staging (goes through Purple/Green/Black/Orange/White gates).
- Export updated capsule after merge (lineage updated).

### Brain Surgery Station requirements
- Provide the **3-frame view** (existing vs APMC vs merged).
- Show merge plan as a graph: Root → rule nodes → evidence nodes → compliance nodes (like your Rules_connected_Map example).
- Support “hot-swap in sandbox” then “stage for deploy”.


## 2) Team agent requirements (from FF_Team_Agents.xlsx)

> Build the app so each “team” is a logical agent group with its own UI surfaces, tasks, and artifacts.

## Team 1: Red Team — The Challengers

**Mission:** Simulates real-world fraudsters, generates and executes evolving fraud attacks (external threat model)

### Agents

- **1. Red Orchestrator (Campaign Manager)**
  - *Agentic capabilities:* Explicit planning, hierarchical delegation, persistent memory
  - *Work/goal:* Builds multi-step attack plans (campaigns), assigns tasks to sub-agents, tracks success/fail, evolves strategy over time.

- **2. Fraud Scenario Generator**
  - *Agentic capabilities:* Creativity + planning + mutation
  - *Work/goal:* Generates new fraud storylines (payments/loans/cards/identity), mutates existing patterns to avoid detection, outputs “attack playbooks”.

- **3. Transaction Fraud Executor**
  - *Agentic capabilities:* Tool use, iterative execution loops
  - *Work/goal:* Produces realistic fraudulent transaction streams: splitting, velocity bursts, mule routing, round-tripping, settlement timing tricks.

- **4. Loan/Deposit Abuse Agent**
  - *Agentic capabilities:* Goal-driven simulation
  - *Work/goal:* Simulates account opening → deposit behavior → credit building → loan drawdown → default patterns.

- **5. Identity Spoof & KYC Evasion Agent**
  - *Agentic capabilities:* Persona memory, context engineering
  - *Work/goal:* Creates synthetic identities, document inconsistencies, device/behavior masks; tests KYC/AML bypass vectors.

- **6. Bot Swarm & Coordination Agent**
  - *Agentic capabilities:* Multi-agent coordination
  - *Work/goal:* Runs distributed attacks across many accounts/devices/IPs; simulates collusion and coordinated timing.

- **7. Recon & Weak-Signal Finder**
  - *Agentic capabilities:* Research + memory
  - *Work/goal:* Finds weak spots (thresholds, exemptions, geo gaps), identifies “low-friction” paths attackers prefer.

- **8. Adaptive Learning Agent**
  - *Agentic capabilities:* Feedback learning, episodic memory
  - *Work/goal:* Learns which attacks got blocked and why; tunes future attacks to specifically exploit blind spots.



## Team 2: Blue Team — The Defenders

**Mission:** Real-time fraud detection, prevention, and response across all banking channels

### Agents

- **1. Blue Orchestrator (Defense Manager)**
  - *Agentic capabilities:* Planning, delegation, state mgmt
  - *Work/goal:* For each event/transaction, assembles the “decision crew”, ensures required checks run, merges outputs into final action.

- **2. Rule Evaluation Agent**
  - *Agentic capabilities:* Deterministic reasoning
  - *Work/goal:* Applies bank rules (thresholds, watchlists, velocity rules, product constraints). Produces rule hits + reason codes.

- **3. Behavioral Baseline Agent**
  - *Agentic capabilities:* Persistent memory, anomaly detection
  - *Work/goal:* Maintains per-customer baseline (time, amount, device, merchant, geo). Flags deviations with explainable deltas.

- **4. Graph & Link Analysis Agent**
  - *Agentic capabilities:* Relational reasoning, memory
  - *Work/goal:* Builds fraud rings: shared devices/IPs/beneficiaries/merchants. Detects mule networks and collusion.

- **5. Device & Session Risk Agent**
  - *Agentic capabilities:* Context engineering, tool use
  - *Work/goal:* Scores device fingerprint, emulator signals, session hijack indicators, impossible travel, proxy/VPN patterns.

- **6. Model Scoring Agent**
  - *Agentic capabilities:* Tool use, evaluation
  - *Work/goal:* Runs ML scoring (if used), calibrates confidence, detects drift signals to report upstream.

- **7. Decision & Action Agent**
  - *Agentic capabilities:* Policy-aware decisioning
  - *Work/goal:* Converts risk + rules into actions: allow/block/step-up/hold/manual review, with justification package.

- **8. Incident Packaging (Escalation) Agent**
  - *Agentic capabilities:* Extreme context packaging
  - *Work/goal:* When a miss occurs: compiles full evidence bundle (signals, timelines, gaps, proposed hypotheses) → Purple Team.

- **9. Post-Decision Monitor Agent**
  - *Agentic capabilities:* Memory, feedback loop
  - *Work/goal:* Watches outcomes (chargebacks, disputes, confirmations). Feeds correctness labels back into learning + rules.



## Team 3: Purple Team — The Strategists

**Mission:** Designs fraud rules, threat models, policies, and future-proof detection strategies

### Agents

- **1. Purple Orchestrator (Strategy Manager)**
  - *Agentic capabilities:* Planning, delegation, memory
  - *Work/goal:* Manages backlog of fraud gaps, prioritizes fixes, assigns analysis to sub-agents, maintains rule roadmap.

- **2. Root Cause Analyst**
  - *Agentic capabilities:* Causal reasoning, evidence synthesis
  - *Work/goal:* Explains why Blue missed: missing feature, threshold wrong, data delay, new pattern. Outputs “failure diagnosis”.

- **3. Rule Authoring Agent**
  - *Agentic capabilities:* Context engineering, structured writing
  - *Work/goal:* Produces rules in a standard spec format: triggers, thresholds, exceptions, required signals, reason codes, test cases.

- **4. Threat Forecasting Agent**
  - *Agentic capabilities:* Long-horizon planning
  - *Work/goal:* Predicts next likely fraud variants based on Red + global patterns; writes proactive rules.

- **5. Policy & Constraint Agent**
  - *Agentic capabilities:* Governance-aware reasoning
  - *Work/goal:* Adds constraints (fairness, legality, minimization). Prevents rules that violate compliance or cause harm.

- **6. Knowledge Graph Curator**
  - *Agentic capabilities:* Persistent memory
  - *Work/goal:* Maintains “fraud ontology”: pattern → signals → controls → known bypasses. Ensures knowledge is searchable.

- **7. Requirements Packager**
  - *Agentic capabilities:* Extreme context engineering
  - *Work/goal:* Converts strategy into Green-ready requirement packs: acceptance criteria, logging requirements, test expectations.



## Team 4: Green Team — The Builders

**Mission:** Converts fraud rules and strategies into production-grade Python code

### Agents

- **1. Green Orchestrator (Build Manager)**
  - *Agentic capabilities:* Planning, delegation, state tracking
  - *Work/goal:* Breaks Purple requirement pack into engineering tasks; assigns to coder/test/logging sub-agents; manages merge-ready deliverables.

- **2. Rule-to-Code Translator**
  - *Agentic capabilities:* Code synthesis, context strictness
  - *Work/goal:* Implements rules as Python modules/services; ensures reason codes + configuration-driven thresholds.

- **3. Pipeline & Integration Agent**
  - *Agentic capabilities:* Tool use, system composition
  - *Work/goal:* Builds streaming/batch pipelines, API endpoints, message schemas, connectors to bank systems.

- **4. Feature Engineering / Signal Agent**
  - *Agentic capabilities:* Tool use, iterative loops
  - *Work/goal:* Implements required features (velocity windows, device signals, graph edges). Validates correctness on sample data.

- **5. Observability & Audit Hooks Agent**
  - *Agentic capabilities:* Context engineering, memory
  - *Work/goal:* Adds structured logs, metrics, tracing, audit fields, replay capability (critical for regulators + Gold/White).

- **6. Performance & Optimization Agent**
  - *Agentic capabilities:* Self-check, profiling
  - *Work/goal:* Reduces latency, improves throughput, prevents memory leaks; ensures real-time SLA is met.

- **7. Config & Policy Wiring Agent**
  - *Agentic capabilities:* Deterministic reasoning
  - *Work/goal:* Converts rules to config files, feature flags, tenant-specific overrides (multi-bank support without code forks).



## Team 5: Black Team — The Stressors 

**Mission:** Intentionally breaks systems, stress-tests defenses, validates robustness and failure handling

### Agents

- **1. Black Orchestrator (Test Manager)**
  - *Agentic capabilities:* Planning, delegation, memory
  - *Work/goal:* Creates test plan per release, assigns test execution, tracks defects, enforces “no gaps” policy.

- **2. Adversarial Replay Agent**
  - *Agentic capabilities:* Persistent memory replay
  - *Work/goal:* Replays known Red attacks + historical fraud cases; ensures “never fail twice” guarantee.

- **3. Edge-Case Generator**
  - *Agentic capabilities:* Creativity + context control
  - *Work/goal:* Generates rare/ugly cases: timezone issues, retries, partial failures, duplicate events, idempotency breaks.

- **4. Chaos Injection Agent**
  - *Agentic capabilities:* Tool use, fault injection loops
  - *Work/goal:* Injects latency, drops messages, corrupts payloads, kills dependencies, simulates outage scenarios.

- **5. Load / Burst Simulation Agent**
  - *Agentic capabilities:* Planning, evaluation
  - *Work/goal:* Simulates peak traffic and fraud bursts; validates throughput, backpressure behavior, queue safety.

- **6. Regression & Coverage Auditor**
  - *Agentic capabilities:* Deterministic verification
  - *Work/goal:* Checks test coverage vs requirements: which rules/features are untested, missing cases, weak assertions.

- **7. Defect Triage & Reporting Agent**
  - *Agentic capabilities:* Extreme context packaging
  - *Work/goal:* Creates structured defect reports: reproduction, logs, root cause hypothesis, severity, fix suggestion → Purple/Green.



## Team 6: Orange Team — The Gatekeepers

**Mission:** Performs code review, security validation, and final release approval

### Agents

- **1. Orange Orchestrator (Release Manager)**
  - *Agentic capabilities:* Planning, delegation, policy enforcement
  - *Work/goal:* Runs release checklist, assigns reviews, aggregates evidence, issues Go/No-Go.

- **2. Code Quality Reviewer**
  - *Agentic capabilities:* Static reasoning, context control
  - *Work/goal:* Reviews architecture consistency, maintainability, readability, modularity, error handling, coding standards.

- **3. Security Review Agent**
  - *Agentic capabilities:* Threat modeling, tool use
  - *Work/goal:* Scans for secrets, injection risk, authz issues, dependency risks, unsafe logging of PII.

- **4. Test Evidence Verifier**
  - *Agentic capabilities:* Evidence-based validation
  - *Work/goal:* Verifies Black Team results are complete, repeatable, and mapped to acceptance criteria (no “trust me” releases).

- **5. Release Risk Assessor**
  - *Agentic capabilities:* Multi-objective reasoning
  - *Work/goal:* Evaluates risk vs impact, decides canary vs phased rollout, requires rollback plan.

- **6. Rollback & Kill-Switch Verifier**
  - *Agentic capabilities:* Contingency planning
  - *Work/goal:* Confirms rollback works, flags are in place, emergency stop procedures are tested.



## Team 7: Gold Team — The Narrators

**Mission:** Ensures all AI decisions are interpretable, auditable, and human-understandable

### Agents

- **1. Gold Orchestrator (Explanation Manager)**
  - *Agentic capabilities:* Planning, delegation, memory
  - *Work/goal:* Coordinates explanation generation for decisions, incidents, and audit requests; standardizes templates.

- **2. Decision Explanation Agent**
  - *Agentic capabilities:* Natural language synthesis, context templates
  - *Work/goal:* Produces “why blocked/allowed” in clear language with reason codes + top signals.

- **3. Evidence Trace Agent**
  - *Agentic capabilities:* Persistent memory, provenance
  - *Work/goal:* Pulls the exact evidence chain: rule hits, model score, graph links, device signals; ensures traceability.

- **4. Audience Adapter Agent**
  - *Agentic capabilities:* Context engineering
  - *Work/goal:* Generates different views: fraud ops view, customer support view, regulator view, executive view.

- **5. Explanation QA Agent**
  - *Agentic capabilities:* Self-check, completeness validation
  - *Work/goal:* Checks for missing reasons, contradictions, sensitive info leakage, non-compliant language.

- **6. Case Narrative Agent**
  - *Agentic capabilities:* Long-context summarization
  - *Work/goal:* Builds investigation-ready narratives for complex incidents (timeline, actors, actions, recommended next steps).



## Team 8: White Team — The Council

**Mission:** Ensures legality, regulatory compliance, fairness, ethics, and audit readiness

### Agents

- **1. White Orchestrator (Governance Manager)**
  - *Agentic capabilities:* Planning, delegation, policy enforcement
  - *Work/goal:* Oversees compliance backlog, audits, approvals; coordinates with Gold/Orange/Purple for governance closure.

- **2. Regulatory Mapping Agent**
  - *Agentic capabilities:* Retrieval + knowledge memory
  - *Work/goal:* Maps controls and decisions to jurisdiction-specific regs (RBI/FCA/OCC/ECB/MAS etc.) using a compliance knowledge base.

- **3. Compliance Validation Agent**
  - *Agentic capabilities:* Deterministic checking
  - *Work/goal:* Validates rules & code behaviors: data retention, consent, PII handling, audit completeness.

- **4. Fairness & Bias Monitor**
  - *Agentic capabilities:* Statistical reasoning, memory
  - *Work/goal:* Measures disparate impact, false positive burden, fairness drift; raises constraints back to Purple.

- **5. Audit Trail Integrity Agent**
  - *Agentic capabilities:* Persistent memory, integrity checks
  - *Work/goal:* Ensures logs are tamper-evident, complete, and reproducible (who/what/when/why).

- **6. Approval Authority Agent**
  - *Agentic capabilities:* Governance decisioning
  - *Work/goal:* Final sign-off gate: validates evidence, issues compliance approval, blocks release if governance unmet.




## 3) Data model & schemas (Copilot MUST implement)
### 3.1 Core entities
- **Scenario**: id, name, fraud_family, channel, description, parameters, steps, variants, seed, created_by, version, status.
- **Battle/Run**: id, scenario_id, timestamp, mode (auto/manual), timeline(turns), metrics, result, artifacts pointers.
- **Agent**: team, agent_id, name, capabilities, status, memory pointers.
- **RuleSpec**: rule_id, name, description, conditions, action, confidence, version, owner, tags, compliance_mappings.
- **RuleCode**: rule_id, language, code, tests, dependencies.
- **PatchSet**: patch_id, diffs, affected_rules, approvals_required, status, risk_score.
- **RSBManifest** + **APMCManifest**: as in your packages.
- **EvidencePack**: narrative, triggered rules, tests, logs, approvals, checksum, lineage.

### 3.2 JSON schema validation
- Validate every import (RSB/APMC) and every export (Evidence Pack).
- Provide `schemas/` folder with versioned JSON schema files.


## 4) Backend API requirements (Copilot MUST implement)
- `POST /auth/login`, `GET /auth/me`
- `GET /teams`, `GET /agents`
- `CRUD /scenarios`
- `POST /battles/run` (auto/manual), `GET /battles/{{id}}`, `POST /battles/{{id}}/replay`
- `POST /rsb/import`, `GET /rsb/{{id}}`, `POST /rsb/{{id}}/validate`, `POST /rsb/{{id}}/test`, `POST /rsb/{{id}}/merge`, `GET /rsb/{{id}}/export`
- `POST /apmc/import`, `GET /apmc/{{id}}`, `POST /apmc/{{id}}/validate`, `POST /apmc/{{id}}/propose-merge`, `GET /apmc/{{id}}/export`
- `POST /patches/{{id}}/approve|reject`
- `GET /evidence/{{battle_id}}`, `GET /evidence/{{battle_id}}/export`
- `POST /llm/test-connection`, `POST /rag/index-rules`, `POST /rag/query`


## 5) UI build requirements (Copilot MUST implement)
- React SPA (or equivalent) with route guards from RBAC.
- Reusable components:
  - Timeline player (play/step/replay)
  - Graph view (force-directed) with node types (Root/Rule/Pattern/Compliance/Evidence)
  - Diff viewer (split view, syntax highlight)
  - Evidence pack viewer (export controls)
  - Approval queue + SAFE_TO_PROCEED badge

## 6) Hackathon readiness (must ship)
- Demo mode with 2–3 preloaded scenarios + 1 preloaded RSB + 1 preloaded APMC.
- “Replay last run” offline fallback.
- One-click Story Mode report generation (screenshots + deltas + narrative).


## Improvements to make this “100% hackathon-winning”

### 1) One-click “Demo Run” + Story Mode
- Button: **Run Battle → Evaluate → Explain → Generate Evidence Pack**
- Auto-narrated timeline with 5–7 key moments and metric deltas.

### 2) Red vs Blue Scoreboard (Battle Arena overlay)
- Live score: detection rate ↑, false positives ↓, time-to-detect ↓, robustness ↑.
- “Patch impact” badges (“+18% ring detection”, “-9% FPR”).

### 3) Safety-first guardrails (critical for judges)
- “Synthetic Only” mode ON by default (no real PII, no real accounts).
- Export watermark + provenance tags everywhere.
- Hard blocks on “real-world execution” outputs; only generate **simulation artifacts**.

### 4) Trust layer that looks enterprise
- Tamper-evident audit log (hash chain).
- Evidence pack checksum + lineage.
- RBAC + SoD approvals shown visually (SAFE_TO_PROCEED).

### 5) UX polish that wins demos
- Persistent right-side “Explainability Panel”.
- Keyboard shortcuts for play/step/replay.
- “Replay last successful run” (offline fallback).
- Dark mode + clean neon graph visuals (matches your example).

### 6) Copilot-friendly build scaffolding
- Provide strict JSON schemas (Scenario, Battle, RuleSpec, RSB manifest, APMC manifest, EvidencePack).
- Provide an OpenAPI spec for backend endpoints.
- Provide sample data + golden demo scenarios + golden evidence packs.

