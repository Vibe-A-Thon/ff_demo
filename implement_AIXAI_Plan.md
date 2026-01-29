# Fraud Forge — AI / XAI / Agentic AI Implementation Plan (implement_AIXAI_Plan.md)

## 0) Outcome target
Deliver a demo-ready Fraud Forge build where judges can:
- run a synthetic fraud battle (Red vs Blue)
- see real-time KPIs and timeline
- inspect **XAI evidence** (plain + technical + audit)
- approve a rule update and re-run to show improvement
- export an “Evidence Pack” artifact

---

## 1) Repository structure (recommended)
```
fraud-forge/
  backend/
    app/
      main.py
      api/                # FastAPI routes
      core/               # config, logging, telemetry
      agents/
        supervisor/
        red_team/
        blue_team/
        gold_team/
        green_team/
        white_team/
        orange_team/
        black_team/
        purple_team/
      tools/              # tool registry + tool implementations
      memory/             # vector store + episodic store + KG adapters
      xai/                # explainability pipeline + schemas
      simulator/          # synthetic transaction + channel simulator
      governance/         # approvals, RBAC, audit logs
      evaluation/         # quality checks, test harness
      schemas/            # pydantic models for messages/artifacts
  frontend/
    ... (War Room / dashboards / evidence graph)
  data/
    seed_scenarios/
    taxonomies/
  docs/
    architecture.md
    demo_script.md
```

---

## 2) Phase plan (build in this order)

### Phase 1 — Foundations (Day 0–1)
**Goal:** run session + messaging + persistence skeleton.

1. Create **RunSession** object
   - `run_id`, seed, start/end timestamps
   - scenario_id, version pins (ruleset, model, taxonomy)

2. Implement **Event Bus**
   - simple: in-memory queue (hackathon)
   - scalable: Redis pub/sub (optional)

3. Define message schemas (Pydantic)
   - `AgentTask`, `AgentResult`, `EvidenceItem`, `Decision`, `ExplanationBundle`
   - include `trace_id`, `span_id`, `parent_span_id`

4. Implement **trace logging**
   - every agent step logs inputs/outputs
   - store as `run_artifacts/<run_id>/trace.jsonl`

Deliverable: CLI endpoint `POST /runs/start` triggers a “hello world” turn loop.

---

### Phase 2 — Tool Registry + Simulator (Day 1–2)
**Goal:** agents can call deterministic tools.

1. Tool registry
   - `tool_name`, `input_schema`, `output_schema`, `safety_level`
   - allowlists per team (policy gating)

2. Implement simulator tools
   - `simulate_transactions(scenario, seed) -> events`
   - `apply_attack(events, attack_plan) -> attacked_events`
   - `score_risk(events, ruleset, model) -> scores`
   - `respond(actions, events) -> updated_state`

3. Deterministic replay
   - all tools take `seed` and return deterministic results
   - persist raw tool I/O

Deliverable: supervisor runs a basic Red/Blue loop for N turns.

---

### Phase 3 — Agents v1 (Day 2–3)
**Goal:** minimal but end-to-end multi-team behavior.

Implement as classes with a common interface:

- `plan(task, state) -> plan_steps`
- `act(step, tools) -> result`
- `reflect(result, state) -> adjustments`
- `emit(result) -> structured output`

#### 3.1 Supervisor / Orchestrator
- turn scheduler: `Red → Blue → Gold → (optional) others`
- stops on success conditions (fraud stopped / threshold reached)

#### 3.2 Red Team v1
- generates synthetic “attack plan” from taxonomy (no real-world exploit detail)
- mutates attacks slightly each turn (novelty)
- outputs `AttackArtifact`

#### 3.3 Blue Team v1
- evaluates events and returns `Decision` + `ResponseActions`
- adds “LearningNote” for potential new rules

#### 3.4 Gold Team v1 (XAI)
- takes Blue decision + evidence
- builds ExplanationBundle with:
  - rule triggers
  - top feature importance (mocked first; real SHAP later)
  - counterfactual stub
  - evidence links

Deliverable: API `GET /runs/{run_id}` shows turn list + decisions + explanations.

---

### Phase 4 — XAI pipeline (Day 3–4)
**Goal:** high-quality, judge-friendly explainability.

1. Define ExplanationBundle schema (final)
2. Implement evidence collection
   - convert tool outputs to EvidenceItems
   - attach provenance: `source_tool`, `source_run`, `source_step`

3. Implement “Reason extraction”
   - Rule-based: exact rules fired, thresholds, matched fields
   - Model-based: SHAP/feature importance (or proxy if model is simple)

4. Counterfactual generator
   - For rules: show which condition change flips outcome
   - For model: minimal feature changes (bounded, synthetic)

5. Similar-case retrieval (optional)
   - vector embedding of case summary
   - return top-k similar synthetic cases with outcomes

Deliverable: gold explanations look credible and consistent in plain+technical modes.

---

### Phase 5 — Knowledge graph & diffs (Day 4–5)
**Goal:** the “wow” evidence graph + before/after comparisons.

1. Build graph model
   - nodes: Case, Decision, Rule, Feature, Evidence, PolicyTag
   - edges: `TRIGGERED_BY`, `SUPPORTED_BY`, `MAPS_TO`, `SIMILAR_TO`

2. Implement graph storage
   - hackathon: NetworkX persisted as JSON
   - optional: Neo4j for visualization scale

3. Diff engine
   - compare two runs:
     - KPI deltas
     - which rules changed
     - which evidence/rationale changed

Deliverable: “Compare Run A vs Run B” endpoint + graph export.

---

### Phase 6 — Governance + approvals (Day 5–6)
**Goal:** show enterprise-grade readiness.

1. RBAC gates
   - associate vs admin vs auditor
2. Approvals workflow
   - new rule proposal → reviewer → approver → staged → deployed
3. Audit log (append-only)
   - signed entries (hash chain optional)
4. “SAFE_TO_PROCEED” indicator
   - only if tests pass + compliance checks green

Deliverable: demo shows “propose rule → run tests → approve → deploy”.

---

### Phase 7 — Evaluation & quality gates (Day 6–7)
**Goal:** reduce hallucinations and make outputs defensible.

1. Automated checks
   - explanation completeness (no missing evidence)
   - contradiction check (reason must match triggered rule)
   - regression check (no KPI collapse beyond threshold)

2. Scenario-based test suites
   - baseline scenarios per fraud family
   - stress tests from Black Team

3. Observability
   - per-agent latency + tool usage
   - run summary report

Deliverable: “Metrics dashboard” + exportable run report.

---

## 3) Concrete API checklist (FastAPI)
- `POST /runs/start` (scenario_id, seed, mode)
- `POST /runs/{run_id}/pause|resume|stop`
- `GET /runs/{run_id}` (timeline, KPIs, decisions)
- `GET /runs/{run_id}/evidence/{case_id}`
- `GET /runs/{run_id}/graph` (nodes+edges)
- `GET /runs/compare?run_a=&run_b=`
- `POST /rules/propose`
- `POST /rules/test`
- `POST /rules/approve`
- `GET /audit/logs`

---

## 4) Agent prompt / config patterns (Copilot-friendly)
Store prompts/configs as versioned YAML:
- `agents/<team>/prompts/*.yaml`
- include:
  - role, goals, allowed tools
  - output JSON schema
  - safety constraints
  - reflection checklist

---

## 5) Safety rules (must implement)
1. Red Team outputs must stay in **simulation language**
   - describe synthetic patterns and signals, not procedural exploitation
2. No real data ingestion
3. Export artifacts must redact sensitive-like fields by default
4. Human approval required for:
   - promoting rules to “deployed”
   - exporting audit packs in “external share” mode

---

## 6) Demo script (to win)
1. Choose a scenario: “Account Takeover + Mule Network”
2. Start auto-run (10 turns)
3. Show: one successful bypass → Blue catches on
4. Open explanation:
   - “Why flagged?” (rules + features + evidence)
5. Propose a rule improvement (Green)
6. Run tests (Black)
7. Approve (Orange/White)
8. Re-run: KPI improves, false positives stable
9. Export evidence pack + show graph

---

## 7) Build notes for hackathon timebox
- If full SHAP is heavy, start with:
  - rules-first explanations
  - simple model (logistic regression) for feature weights
- Use deterministic seeds to keep demos reliable.
- Keep UI fast: precompute run summaries and lazy-load evidence nodes.
