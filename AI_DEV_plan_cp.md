# Fraud Forge — AI_DEV_plan.md
**Scope:** Phase-by-phase plan to build all AI + backend capabilities for Fraud Forge (Agents, Multi‑RAG/KAG/CAG, XAI, governance, metrics).  
**Source set:** `ff_md.zip` extracted docs consolidated into an execution plan for GitHub Copilot.  
**Generated:** 2026-01-31 19:00:50

> **Non‑negotiable safety:** all scenarios are synthetic and sandboxed; no real PII; no operational wrongdoing guidance.

---

## 0) Target demo outcome (definition of “done”)
A build is demo‑ready when you can:
1. Start a run with a fixed seed (deterministic)
2. Stream Red vs Blue turns + KPIs in real-time
3. Click any case → see XAI explanation + evidence graph
4. Auto-trigger learning loop → propose/build/test/approve/deploy a patch
5. Re-run and show **Time‑to‑Immunity** + KPI improvements
6. Export **Evidence Pack**

---

## 1) Phase 0 — Repo, infra, and core contracts (Day 0–1)
### 1.1 Monorepo layout (backend focus)
```
backend/app/
  api/                 # REST + WS
  agents/              # supervisor + teams + sub-agents
  tools/               # tool registry + tool impls
  simulator/           # synthetic scenarios + ground truth
  retrieval/           # Multi-RAG router + indices
  xai/                 # explanation + evidence graph
  governance/          # RBAC/SoD/approvals/audit
  rsb/                 # RSB parsing + validation + staging
  metrics/             # KPIs + time-to-immunity
  schemas/             # typed artifacts & messages
  storage/             # postgres + files + vector + graph adapters
```
### 1.2 Implement the “typed artifact” layer first (critical)
Create Pydantic models for:
- `RunSession`, `TurnEvent`, `KPIUpdate`
- `AgentMessage (PAMP)`, `AgentTask`, `AgentResult`
- `Decision`, `ExplanationBundle`, `EvidenceGraph`
- `RuleSpec`, `RSBManifest`, `TestReport`
- `ApprovalRequest`, `AuditLogEntry`
**Acceptance criteria:** every agent/tool output validates against schemas.

---

## 2) Phase 1 — Deterministic synthetic simulator + run session loop (Day 1–3)
### 2.1 Simulator
- Implement scenario templates aligned to taxonomy ids
- Produce synthetic event streams with ground truth labels
- Support channels: cards, payments, account takeover, mule network (synthetic)
- Seeded randomness for replay stability
### 2.2 Run session service
- start/pause/resume/stop/replay
- turn engine (timeboxed per turn)
- persist turns + artifacts + KPIs
### 2.3 WebSocket streaming
- broadcast per-run events: reasoning chunks, KPIs, approvals, artifacts
**Acceptance criteria:** UI can render a live timeline from streamed events.

---

## 3) Phase 2 — Agent runtime (Supervisor + 8 teams) (Day 3–6)
### 3.1 Supervisor
- Maintains state machine:
  - battle loop: Red ↔ Blue ↔ Gold
  - improvement loop: Purple → Green → Black → Orange → White
- Tool allowlists per team
- Budgeting: timeouts, max sub-agents, max tool calls per turn
### 3.2 Implement team orchestrators first
- RedOrchestrator: plans synthetic campaign; delegates to scenario generator/executor
- BlueOrchestrator: runs detection and response; delegates to rule/model evaluators
- GoldOrchestrator: produces ExplanationBundle and evidence graph
- Purple/Green/Black/Orange/White orchestrators: patch pipeline
### 3.3 Add sub-agents incrementally
Implement sub-agent set from `FF_Team_Agents.xlsx` (56 agents total):
- Start with 2–3 per team (P0)
- Expand to full roster if time permits
**Acceptance criteria:** each team emits at least one typed artifact per turn.

---

## 4) Phase 3 — Multi‑RAG foundation (Hybrid retrieval) (Day 6–8)
### 4.1 Ingestion pipelines (P0)
- Index corpora:
  - taxonomy + fraud groups
  - rules/specs + RSB docs
  - prior runs summaries + evidence pack summaries
- Vector store: Chroma collections
- Keyword index: BM25
### 4.2 RetrievalRouter (P0)
- Implement intent classifier (lightweight rules) to choose:
  - BM25, vector, hybrid (RRF)
- Return `RetrievalBundle` with citations + hashes
**Acceptance criteria:** retrieval is visible and deterministic for demo queries.

---

## 5) Phase 4 — Advanced/Agentic RAG + Self‑RAG/CRAG (Day 8–10)
### 5.1 Advanced RAG modules
- Query rewrite/expansion (safe; no PII)
- Reranking (heuristic or cross‑encoder)
- Dedup + contradiction detection
### 5.2 Self‑RAG quality gate
- score retrieved context; if weak, re‑query and/or switch strategy
### 5.3 Agentic RAG
- Planner breaks complex question into sub‑queries:
  - “what rule blocked it”
  - “which similar case exists”
  - “what patch should be proposed”
- Uses toolchain iteratively; logs reasoning steps
**Acceptance criteria:** show a “retrieval decision trace” in the UI/debug.

---

## 6) Phase 5 — KAG / GraphRAG for rings & mule networks (Day 10–12)
### 6.1 Graph model
- Nodes: Customer/Account/Transaction/Device/IP/Rule/Policy
- Edges: TRANSFERRED_TO, SHARED_DEVICE, SHARED_IP, TRIGGERED_RULE, MAPS_TO_POLICY
### 6.2 Graph construction (synthetic)
- Convert simulator outputs + detection outputs into graph updates
### 6.3 Graph retrieval + multi-hop reasoning
- Provide `/retrieval/graph-query`
- Integrate into Blue detection and Gold XAI as evidence
**Acceptance criteria:** evidence graph shows ring/mule pattern and linked rules.

---

## 7) Phase 6 — CAG (Cache‑augmented generation) (Day 12)
### 7.1 What to cache
- policy summaries, rule summaries, taxonomy summaries
- “best practices playbooks” (defensive)
### 7.2 Cache mechanisms
- precomputed summaries + KV store
- cache invalidation on ruleset update
**Acceptance criteria:** common queries answer instantly and cite cache hits.

---

## 8) Phase 7 — XAI pipeline + Evidence Packs (Day 12–13)
### 8.1 ExplanationBundle builder (P0)
- Rules-first reasoning (triggered rules, thresholds)
- Top signals/features
- Counterfactuals (bounded, synthetic)
- Similar-case retrieval results
### 8.2 Evidence graph builder (P0)
- Build graph JSON with provenance hashes
### 8.3 Evidence pack exporter (P0)
- Bundle: timeline + KPIs + approvals + diffs + explanations
- Output: JSON + markdown summary (pdf-ready)
**Acceptance criteria:** one-click export used in judge demo.

---

## 9) Phase 8 — Governance + approvals + audit (Day 13)
### 9.1 RBAC & SoD (P0)
- enforce permissions on every endpoint
- enforce SoD: proposer != approver, etc.
### 9.2 SAFE_TO_PROCEED indicator
- compile test results + compliance checks + risk flags
### 9.3 Append-only audit log
- hash chain on events (lightweight)
**Acceptance criteria:** demonstrate approvals timeline in UI and export.

---

## 10) Phase 9 — RSB lifecycle integration (Day 13–14)
### 10.1 RSB parser/validator
- validate structure + manifest + required docs/tests/compliance
### 10.2 Test runner sandbox
- execute UT/IT with timeouts; capture outputs
### 10.3 Stage/deploy/rollback
- create new pinned ruleset version
- rollback to previous version
**Acceptance criteria:** demo importing an RSB and deploying a patched rule.

---

## 11) Phase 10 — Hackathon polish (parallel)
### 11.1 Demo mode stability
- fixed seeds + prerecorded traces fallback
- graceful degradation if LLM or retrieval fails
### 11.2 “WOW” narrative
- start with a successful Red attack → show miss
- run patch pipeline → re-run shows immunity and KPI delta
### 11.3 Judge artifacts
- Evidence Pack + “before/after” KPI compare snapshots
- explainability completeness badge
- time-to-immunity improvement chart

---

## 12) Copilot task list (copy/paste backlog)
```text
1) Create Pydantic schemas for RunSession/TurnEvent/KPIUpdate + store in Postgres.
2) Implement deterministic synthetic simulator with scenario templates mapped to taxonomy ids.
3) Build Supervisor orchestrator with turn engine, team allowlists, budgets, and WS event streaming.
4) Implement Red/Blue/Gold orchestrators and minimum sub-agents per team; persist PAMP messages.
5) Implement RetrievalRouter with BM25 + Chroma + hybrid RRF; return RetrievalBundle with citations/hashes.
6) Implement Self-RAG quality gate and CRAG fallback strategy; log retrieval decisions.
7) Implement graph builder (NetworkX) and graph retrieval; integrate into evidence graph output.
8) Implement ExplanationBundle builder + counterfactuals + similar-case retrieval.
9) Implement Evidence Pack exporter (JSON + markdown) including approvals and rule diffs.
10) Implement RBAC + SoD checks + SAFE_TO_PROCEED computation and append-only audit hash chain.
11) Implement RSB zip parser/validator + sandboxed test runner + stage/deploy/rollback to ruleset registry.
12) Add demo mode: fixed seeds, precomputed traces fallback, and a single-click “WOW Replay” endpoint.
```

---

## 13) Risk controls (keep the demo safe & stable)
- Disable any non-synthetic connectors by default.
- Red team “attacks” are pattern generators only; block any actionable instructions.
- Timebox all LLM calls; cache frequent prompts in demo mode.
- Provide fallback responses and precomputed run data for offline resilience.
