# Fraud Forge — Sub‑Agent Requirements (from FF_Team_Agents.xlsx)

**Scope:** This document defines the *features / functionalities / requirements* needed to implement **sub‑agents** (the 56 agents listed in `FF_Team_Agents.xlsx`) inside the Fraud Forge application.

**Goal:** Enable a multi‑team, orchestrated “living organization” where each team has a coordinator (orchestrator) and multiple specialized sub‑agents that produce traceable artifacts, can be replayed, and can run in **Auto** or **Human‑In‑The‑Loop** modes.

**Source of truth:** `FF_Team_Agents.xlsx` (Sheet2) — teams, agent names, capabilities, and detailed goals.

---

## 0. Definitions

- **Team Orchestrator:** The manager agent per team (e.g., *Red Orchestrator*) that decomposes objectives into tasks, assigns them to sub‑agents, and aggregates outputs.
- **Sub‑Agent:** A specialized agent that performs a focused job and produces a typed artifact.
- **Task:** A unit of work assigned to a sub‑agent with inputs, constraints, and acceptance criteria.
- **Artifact:** Versioned output object produced by agents (JSON + optional files) with lineage metadata for evidence.

---

## 1. Global functional requirements (apply to every sub‑agent)

### 1.1 Sub‑Agent contract (must implement)
Each sub‑agent must implement the following interface/contract:

- `agent_id` (stable, unique), `agent_name`, `team_id`, `role`
- `capabilities[]` (searchable tags)
- `allowed_tools[]` (tool permissions)
- `inputs[]` (artifact types accepted)
- `outputs[]` (artifact types produced)
- `guardrails[]` (e.g., synthetic-only, no PII)
- `run(task: Task) -> AgentResult` (deterministic if seeded)
- `validate(task) -> ValidationResult` (hard fail vs warn)
- `explain(result) -> ExplanationSnippet` (short “why/how” for Gold team)

### 1.2 Execution modes
- **AUTO:** agent executes without approvals, but still respects guardrails and produces evidence.
- **HITL:** agent requires explicit “Approve” at configurable points (start, output publish, merge).
- **REPLAY:** agent replays a previous run using stored inputs + a fixed seed to reproduce outputs.

### 1.3 Evidence & lineage (non-negotiable)
For every `run()`:
- generate a `run_id`, `task_id`, timestamps
- attach **lineage links** to upstream artifacts
- store:
  - structured logs (JSONL)
  - metrics (latency, tokens, quality flags)
  - “decision trace” (what steps it took)
- output artifacts must include:
  - `schema_version`
  - `created_by` (agent_id)
  - `inputs_hash` (checksum of inputs)
  - `seed` (for deterministic replay)
  - `safety_flags` (PII=false, synthetic=true)

### 1.4 Safety requirements (for hackathon + ethics)
- Default mode = **Synthetic-only** datasets and synthetic entities.
- Block any content that attempts to generate **actionable fraud instructions against real targets**.
- Disallow real customer identifiers; enforce redaction at ingestion + export.
- Export watermark: “Synthetic simulation for testing/training”.

### 1.5 Observability requirements
- Each agent must emit:
  - `status` updates: idle → running → waiting/blocked → done/failed
  - progress events (0–100%)
  - error events with recoverable retry hints
- Orchestrators must show:
  - which sub‑agent ran, with what inputs, and what output it produced

---

## 2. System-level sub‑agent requirements

### 2.1 Agent registry & configuration
- Agents are configured via **YAML/JSON** (not hard-coded):
  - enabled/disabled
  - default parameters (thresholds, windows)
  - tool permissions
  - prompt templates (if LLM-backed)
  - routing rules (which tasks go to which agent)

### 2.2 Task routing & collaboration
- Support **team-level** and **agent-level** routing:
  - “send task to team” → orchestrator delegates
  - “send task to specific agent”
- Support “request/response” between teams:
  - Red → Blue (new pattern)
  - Blue → Purple (miss analysis request)
  - Purple → Green (requirements pack)
  - Green → Black (test request)
  - Black → Orange (evidence)
  - Orange → White/Gold (governance + explainability)
- All cross-team requests must be auditable.

### 2.3 State machine alignment (War Loop)
The sub‑agents must collectively support this loop:
**Red → Blue → Purple → Green → Black → Orange → Gold → White**

System must:
- track stage status
- enforce gates (Orange/White)
- allow replay of full pipeline

### 2.4 UI integration requirements
The UI must be able to:
- show per-agent thinking stream and progress
- open artifacts in an “Evidence Drawer”
- show which agent produced which output
- replay with the same outputs (seeded)

---

## 3. Canonical artifact types (minimum set)

> These are required so that sub‑agents can interoperate cleanly.

### 3.1 Red artifacts
- `AttackCampaign`, `AttackPlaybook`, `SyntheticIdentityBundle`, `SyntheticTransactionStream`, `ReconFindings`, `AttackVariantReport`

### 3.2 Blue artifacts
- `RuleHits`, `BaselineDeviations`, `GraphFindings`, `DeviceSessionRisk`, `ModelScores`, `DecisionPackage`, `EscalationPack`, `OutcomeLabels`

### 3.3 Purple artifacts
- `FailureDiagnosis`, `RuleSpec`, `ThreatForecast`, `PolicyConstraints`, `OntologyUpdate`, `RequirementsPack`

### 3.4 Green artifacts
- `CodePatch`, `PipelineChange`, `FeatureSignalSpec`, `ObservabilityHooks`, `PerformanceReport`, `ConfigBundle`

### 3.5 Black artifacts
- `TestPlan`, `ReplayReport`, `EdgeCaseSet`, `ChaosReport`, `LoadTestReport`, `CoverageReport`, `DefectReport`

### 3.6 Orange artifacts
- `CodeReviewReport`, `SecurityScanReport`, `EvidenceVerification`, `ReleaseRiskReport`, `RollbackVerification`, `ReleaseDecision`

### 3.7 Gold artifacts
- `ExplanationPack`, `EvidenceTrace`, `AudienceVariantSet`, `ExplanationQAReport`, `CaseNarrative`

### 3.8 White artifacts
- `RegulatoryMapping`, `ComplianceValidationReport`, `FairnessReport`, `AuditIntegrityReport`, `GovernanceApproval`

---

## 4. Team-by-team sub‑agent inventory (as specified in the Excel)

## Red Team — The Challengers

**Team mission:** Simulates real-world fraudsters, generates and executes evolving fraud attacks (external threat model)

| Agent ID | Agent Name | Agentic capabilities | Core responsibilities (from source) |
|---|---|---|---|
| `red.agent.01` | **Red Orchestrator (Campaign Manager)** | Explicit planning, hierarchical delegation, persistent memory | Builds multi-step attack plans (campaigns), assigns tasks to sub-agents, tracks success/fail, evolves strategy over time. |
| `red.agent.02` | **Fraud Scenario Generator** | Creativity + planning + mutation | Generates new fraud storylines (payments/loans/cards/identity), mutates existing patterns to avoid detection, outputs “attack playbooks”. |
| `red.agent.03` | **Transaction Fraud Executor** | Tool use, iterative execution loops | Produces realistic fraudulent transaction streams: splitting, velocity bursts, mule routing, round-tripping, settlement timing tricks. |
| `red.agent.04` | **Loan/Deposit Abuse Agent** | Goal-driven simulation | Simulates account opening → deposit behavior → credit building → loan drawdown → default patterns. |
| `red.agent.05` | **Identity Spoof & KYC Evasion Agent** | Persona memory, context engineering | Creates synthetic identities, document inconsistencies, device/behavior masks; tests KYC/AML bypass vectors. |
| `red.agent.06` | **Bot Swarm & Coordination Agent** | Multi-agent coordination | Runs distributed attacks across many accounts/devices/IPs; simulates collusion and coordinated timing. |
| `red.agent.07` | **Recon & Weak-Signal Finder** | Research + memory | Finds weak spots (thresholds, exemptions, geo gaps), identifies “low-friction” paths attackers prefer. |
| `red.agent.08` | **Adaptive Learning Agent** | Feedback learning, episodic memory | Learns which attacks got blocked and why; tunes future attacks to specifically exploit blind spots. |


## Blue Team — The Defenders

**Team mission:** Real-time fraud detection, prevention, and response across all banking channels

| Agent ID | Agent Name | Agentic capabilities | Core responsibilities (from source) |
|---|---|---|---|
| `blue.agent.01` | **Blue Orchestrator (Defense Manager)** | Planning, delegation, state mgmt | For each event/transaction, assembles the “decision crew”, ensures required checks run, merges outputs into final action. |
| `blue.agent.02` | **Rule Evaluation Agent** | Deterministic reasoning | Applies bank rules (thresholds, watchlists, velocity rules, product constraints). Produces rule hits + reason codes. |
| `blue.agent.03` | **Behavioral Baseline Agent** | Persistent memory, anomaly detection | Maintains per-customer baseline (time, amount, device, merchant, geo). Flags deviations with explainable deltas. |
| `blue.agent.04` | **Graph & Link Analysis Agent** | Relational reasoning, memory | Builds fraud rings: shared devices/IPs/beneficiaries/merchants. Detects mule networks and collusion. |
| `blue.agent.05` | **Device & Session Risk Agent** | Context engineering, tool use | Scores device fingerprint, emulator signals, session hijack indicators, impossible travel, proxy/VPN patterns. |
| `blue.agent.06` | **Model Scoring Agent** | Tool use, evaluation | Runs ML scoring (if used), calibrates confidence, detects drift signals to report upstream. |
| `blue.agent.07` | **Decision & Action Agent** | Policy-aware decisioning | Converts risk + rules into actions: allow/block/step-up/hold/manual review, with justification package. |
| `blue.agent.08` | **Incident Packaging (Escalation) Agent** | Extreme context packaging | When a miss occurs: compiles full evidence bundle (signals, timelines, gaps, proposed hypotheses) → Purple Team. |
| `blue.agent.09` | **Post-Decision Monitor Agent** | Memory, feedback loop | Watches outcomes (chargebacks, disputes, confirmations). Feeds correctness labels back into learning + rules. |


## Purple Team — The Strategists

**Team mission:** Designs fraud rules, threat models, policies, and future-proof detection strategies

| Agent ID | Agent Name | Agentic capabilities | Core responsibilities (from source) |
|---|---|---|---|
| `purple.agent.01` | **Purple Orchestrator (Strategy Manager)** | Planning, delegation, memory | Manages backlog of fraud gaps, prioritizes fixes, assigns analysis to sub-agents, maintains rule roadmap. |
| `purple.agent.02` | **Root Cause Analyst** | Causal reasoning, evidence synthesis | Explains why Blue missed: missing feature, threshold wrong, data delay, new pattern. Outputs “failure diagnosis”. |
| `purple.agent.03` | **Rule Authoring Agent** | Context engineering, structured writing | Produces rules in a standard spec format: triggers, thresholds, exceptions, required signals, reason codes, test cases. |
| `purple.agent.04` | **Threat Forecasting Agent** | Long-horizon planning | Predicts next likely fraud variants based on Red + global patterns; writes proactive rules. |
| `purple.agent.05` | **Policy & Constraint Agent** | Governance-aware reasoning | Adds constraints (fairness, legality, minimization). Prevents rules that violate compliance or cause harm. |
| `purple.agent.06` | **Knowledge Graph Curator** | Persistent memory | Maintains “fraud ontology”: pattern → signals → controls → known bypasses. Ensures knowledge is searchable. |
| `purple.agent.07` | **Requirements Packager** | Extreme context engineering | Converts strategy into Green-ready requirement packs: acceptance criteria, logging requirements, test expectations. |


## Green Team — The Builders

**Team mission:** Converts fraud rules and strategies into production-grade Python code

| Agent ID | Agent Name | Agentic capabilities | Core responsibilities (from source) |
|---|---|---|---|
| `green.agent.01` | **Green Orchestrator (Build Manager)** | Planning, delegation, state tracking | Breaks Purple requirement pack into engineering tasks; assigns to coder/test/logging sub-agents; manages merge-ready deliverables. |
| `green.agent.02` | **Rule-to-Code Translator** | Code synthesis, context strictness | Implements rules as Python modules/services; ensures reason codes + configuration-driven thresholds. |
| `green.agent.03` | **Pipeline & Integration Agent** | Tool use, system composition | Builds streaming/batch pipelines, API endpoints, message schemas, connectors to bank systems. |
| `green.agent.04` | **Feature Engineering / Signal Agent** | Tool use, iterative loops | Implements required features (velocity windows, device signals, graph edges). Validates correctness on sample data. |
| `green.agent.05` | **Observability & Audit Hooks Agent** | Context engineering, memory | Adds structured logs, metrics, tracing, audit fields, replay capability (critical for regulators + Gold/White). |
| `green.agent.06` | **Performance & Optimization Agent** | Self-check, profiling | Reduces latency, improves throughput, prevents memory leaks; ensures real-time SLA is met. |
| `green.agent.07` | **Config & Policy Wiring Agent** | Deterministic reasoning | Converts rules to config files, feature flags, tenant-specific overrides (multi-bank support without code forks). |


## Black Team — The Stressors 

**Team mission:** Intentionally breaks systems, stress-tests defenses, validates robustness and failure handling

| Agent ID | Agent Name | Agentic capabilities | Core responsibilities (from source) |
|---|---|---|---|
| `black.agent.01` | **Black Orchestrator (Test Manager)** | Planning, delegation, memory | Creates test plan per release, assigns test execution, tracks defects, enforces “no gaps” policy. |
| `black.agent.02` | **Adversarial Replay Agent** | Persistent memory replay | Replays known Red attacks + historical fraud cases; ensures “never fail twice” guarantee. |
| `black.agent.03` | **Edge-Case Generator** | Creativity + context control | Generates rare/ugly cases: timezone issues, retries, partial failures, duplicate events, idempotency breaks. |
| `black.agent.04` | **Chaos Injection Agent** | Tool use, fault injection loops | Injects latency, drops messages, corrupts payloads, kills dependencies, simulates outage scenarios. |
| `black.agent.05` | **Load / Burst Simulation Agent** | Planning, evaluation | Simulates peak traffic and fraud bursts; validates throughput, backpressure behavior, queue safety. |
| `black.agent.06` | **Regression & Coverage Auditor** | Deterministic verification | Checks test coverage vs requirements: which rules/features are untested, missing cases, weak assertions. |
| `black.agent.07` | **Defect Triage & Reporting Agent** | Extreme context packaging | Creates structured defect reports: reproduction, logs, root cause hypothesis, severity, fix suggestion → Purple/Green. |


## Orange Team — The Gatekeepers

**Team mission:** Performs code review, security validation, and final release approval

| Agent ID | Agent Name | Agentic capabilities | Core responsibilities (from source) |
|---|---|---|---|
| `orange.agent.01` | **Orange Orchestrator (Release Manager)** | Planning, delegation, policy enforcement | Runs release checklist, assigns reviews, aggregates evidence, issues Go/No-Go. |
| `orange.agent.02` | **Code Quality Reviewer** | Static reasoning, context control | Reviews architecture consistency, maintainability, readability, modularity, error handling, coding standards. |
| `orange.agent.03` | **Security Review Agent** | Threat modeling, tool use | Scans for secrets, injection risk, authz issues, dependency risks, unsafe logging of PII. |
| `orange.agent.04` | **Test Evidence Verifier** | Evidence-based validation | Verifies Black Team results are complete, repeatable, and mapped to acceptance criteria (no “trust me” releases). |
| `orange.agent.05` | **Release Risk Assessor** | Multi-objective reasoning | Evaluates risk vs impact, decides canary vs phased rollout, requires rollback plan. |
| `orange.agent.06` | **Rollback & Kill-Switch Verifier** | Contingency planning | Confirms rollback works, flags are in place, emergency stop procedures are tested. |


## Gold Team — The Narrators

**Team mission:** Ensures all AI decisions are interpretable, auditable, and human-understandable

| Agent ID | Agent Name | Agentic capabilities | Core responsibilities (from source) |
|---|---|---|---|
| `gold.agent.01` | **Gold Orchestrator (Explanation Manager)** | Planning, delegation, memory | Coordinates explanation generation for decisions, incidents, and audit requests; standardizes templates. |
| `gold.agent.02` | **Decision Explanation Agent** | Natural language synthesis, context templates | Produces “why blocked/allowed” in clear language with reason codes + top signals. |
| `gold.agent.03` | **Evidence Trace Agent** | Persistent memory, provenance | Pulls the exact evidence chain: rule hits, model score, graph links, device signals; ensures traceability. |
| `gold.agent.04` | **Audience Adapter Agent** | Context engineering | Generates different views: fraud ops view, customer support view, regulator view, executive view. |
| `gold.agent.05` | **Explanation QA Agent** | Self-check, completeness validation | Checks for missing reasons, contradictions, sensitive info leakage, non-compliant language. |
| `gold.agent.06` | **Case Narrative Agent** | Long-context summarization | Builds investigation-ready narratives for complex incidents (timeline, actors, actions, recommended next steps). |


## White Team — The Council

**Team mission:** Ensures legality, regulatory compliance, fairness, ethics, and audit readiness

| Agent ID | Agent Name | Agentic capabilities | Core responsibilities (from source) |
|---|---|---|---|
| `white.agent.01` | **White Orchestrator (Governance Manager)** | Planning, delegation, policy enforcement | Oversees compliance backlog, audits, approvals; coordinates with Gold/Orange/Purple for governance closure. |
| `white.agent.02` | **Regulatory Mapping Agent** | Retrieval + knowledge memory | Maps controls and decisions to jurisdiction-specific regs (RBI/FCA/OCC/ECB/MAS etc.) using a compliance knowledge base. |
| `white.agent.03` | **Compliance Validation Agent** | Deterministic checking | Validates rules & code behaviors: data retention, consent, PII handling, audit completeness. |
| `white.agent.04` | **Fairness & Bias Monitor** | Statistical reasoning, memory | Measures disparate impact, false positive burden, fairness drift; raises constraints back to Purple. |
| `white.agent.05` | **Audit Trail Integrity Agent** | Persistent memory, integrity checks | Ensures logs are tamper-evident, complete, and reproducible (who/what/when/why). |
| `white.agent.06` | **Approval Authority Agent** | Governance decisioning | Final sign-off gate: validates evidence, issues compliance approval, blocks release if governance unmet. |


---

## 5. Per-team derived requirements (what Copilot must implement beyond listing agents)


### 5.1 Red Team requirements (Challengers)
- Must support **campaign planning**: orchestrator builds multi-step campaigns and delegates sub-tasks.
- Must support **variant mutation**: scenario generator mutates patterns to bypass current defenses.
- Must generate **realistic synthetic streams**: split payments, velocity bursts, mule routing, timing tricks.
- Must generate **synthetic identities & KYC evasion artifacts** (strictly synthetic; redaction enforced).
- Must simulate **multi-actor coordination**: bot swarms and collusion timing.
- Must include **recon findings**: identify weak thresholds/exemptions/geographic gaps.
- Must include **adaptive learning loop**: learn why blocked and re-target blind spots (stored as AttackVariantReport).

### 5.2 Blue Team requirements (Defenders)
- Must implement a **decision crew** pattern: orchestrator invokes rule checks, baseline, graph, device risk, model score.
- Must produce **reason-coded rule hits** (deterministic) and a single merged **DecisionPackage**.
- Must maintain **behavioral baselines** (synthetic users) and flag explainable deviations.
- Must build **link/graph analysis** for mule networks & collusion (node/edge evidence).
- Must score **device/session risk** (proxy/VPN, impossible travel, emulator signals).
- Must support **post-decision monitoring**: outcomes/labels feed back to Purple/Red for learning.
- Must generate **EscalationPack** when a miss occurs (full evidence bundle to Purple).

### 5.3 Purple Team requirements (Strategists)
- Must maintain **gap backlog + rule roadmap** with prioritization.
- Must generate **FailureDiagnosis** (“why we missed”) with evidence references.
- Must author **RuleSpec** in a structured, validated schema (triggers, thresholds, exceptions, required signals, reason codes, test cases).
- Must forecast **next variants** (ThreatForecast) using Red outcomes + knowledge base.
- Must enforce **policy constraints**: fairness, legality, minimization, “do no harm”.
- Must maintain a searchable **fraud ontology / knowledge graph**.
- Must output **RequirementsPack** to Green with acceptance criteria + logging + test expectations.

### 5.4 Green Team requirements (Builders)
- Must convert RequirementsPack + RuleSpec into **production-grade Python** modules (config-driven thresholds).
- Must implement **pipeline/integration** stubs: streaming/batch schemas, API endpoints, connectors (mock for hackathon).
- Must implement **features/signals** required by Purple (velocity windows, graph edges, device signals).
- Must add **observability hooks**: structured logs, metrics, tracing, audit fields, replay.
- Must include **performance optimization** guardrails (latency budget, throughput budget).
- Must provide **config/policy wiring** for tenant overrides without code forks.

### 5.5 Black Team requirements (Stressors)
- Must generate a **test plan per release** and enforce “no gaps” policy.
- Must replay known attacks (“never fail twice”) via **Adversarial Replay**.
- Must generate **edge cases** (idempotency, retries, duplicates, partial failures).
- Must inject **chaos faults** (latency, drops, dependency failures).
- Must simulate **burst loads** and validate backpressure safety.
- Must audit **coverage vs requirements** and highlight missing tests.
- Must produce structured **DefectReports** with reproduction steps + logs + severity.

### 5.6 Orange Team requirements (Gatekeepers)
- Must implement a **release checklist** and go/no-go gate.
- Must review **code quality** (standards, modularity, error handling).
- Must run **security review** (secrets scan, authz, dependency risk, PII logging).
- Must verify **test evidence** is complete and mapped to acceptance criteria.
- Must assess **release risk** and require rollback plan.
- Must verify **rollback & kill-switch** pathways are tested and usable.

### 5.7 Gold Team requirements (Narrators)
- Must generate **decision explanations** (“why allowed/blocked”) with reason codes + top signals.
- Must generate **evidence trace** (exact chain: rule hits, scores, links, device signals).
- Must produce **audience-adapted** narratives (ops/support/regulator/executive).
- Must QA explanations for completeness, contradictions, sensitive leakage.
- Must produce investigation-ready **case narratives** with timelines and next steps.

### 5.8 White Team requirements (Council)
- Must map controls and decisions to **jurisdiction-specific regulations** (knowledge base driven).
- Must validate **compliance behaviors**: retention, consent, PII handling, audit completeness.
- Must monitor **fairness/bias**: disparate impact, FP burden, drift.
- Must ensure **audit trail integrity**: tamper-evident, complete, reproducible.
- Must provide final **governance approval** gate with block capability.


## 6. Hackathon-winning enhancements (requirements)

### 6.1 One-click “Full War Loop Demo”
- Preload a flagship scenario and seed.
- Run Red→Blue→Purple→Green→Black→Orange→Gold→White automatically.
- Produce:
  - Scoreboard deltas (before/after)
  - Evidence pack export
  - Story-mode report (timeline + key decisions)

### 6.2 Deterministic demo mode (no surprises)
- Every agent supports `seed` to reproduce outputs.
- Provide “Replay last successful run” button.
- Bundle demo datasets and precomputed artifacts (optional) as fallback.

### 6.3 Living-organization UX hooks
- Per-agent live status + progress events.
- Animated “handoff” between teams at stage boundaries.
- Click any stage → open evidence drawer with produced artifacts.

### 6.4 Safety posture built-in
- Synthetic-only data guardrails on by default.
- Export watermark + provenance metadata.
- Role-based export restrictions (at least: admin vs viewer).

---

## 7. Acceptance criteria checklist (for Copilot)
- [ ] 56 agents exist in registry (IDs stable) with team mapping.
- [ ] Each orchestrator delegates tasks to sub-agents.
- [ ] Each stage produces a typed artifact with lineage metadata.
- [ ] Full War Loop can run end-to-end and replay deterministically.
- [ ] Evidence pack includes: artifacts, logs, metrics, approvals, explanations.
- [ ] Approval gates (Orange + White) block progression until approved.
