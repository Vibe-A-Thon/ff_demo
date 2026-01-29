# Fraud Forge — Requirements (v2)
**Scope:** Bank-grade, multi-tenant, agentic fraud defense platform  
**Architecture:** **Hybrid** multi-agent system + **Lifecycle Workflow Engine (state machine)** + **KPI/Risk Governance** + **Automated Artifact Validators**  
**Autonomy modes:** HITL / HOTL (policy-conditioned autonomy)  
**Core thesis:** **Failure → Learning → Immunity** (provable in UI + auditable in artifacts)

---

## 0) Executive Summary

### 0.1 Product Overview
Fraud Forge is an **Eight-Team AI Defense System** that continuously:
1) Simulates fraud in controlled environments,  
2) Detects/defends in real time (or flags misses),  
3) Converts misses into **RuleSpecs**,  
4) Generates **patches**, runs **tests/chaos/replays**,  
5) Pushes changes through **approvals**, and  
6) Deploys safely with monitoring and rollback.

### 0.2 Core Value Proposition
- **Share Wisdom, Not Data:** Transfer learned defenses without sharing customer data.
- **Eight-Team Architecture:** Red/Blue/Black/Purple/Green/Orange/Gold/White cover the full lifecycle.
- **Provable Self-Healing:** “Brain Surgery” shows knowledge/patch merges and hot-swaps (sandbox).
- **Enterprise Governance:** RBAC + SoD + Validators + KPI/Risk gating for HOTL.

---

## 1) Teams (Internal + Market Names)

| Internal Team | Color | Color Code | Market / Bank-Facing Name | What It Means (Plain English) |
|---|---:|---:|---|---|
| **Red Team** | 🔴 | `#FF0000` | **The Challengers** | Simulates how real fraudsters attack banks (sandbox only) |
| **Blue Team** | 🔵 | `#0000FF` | **The Defenders** | Detects and stops fraud in real time |
| **Black Team** | ⚫ | `#000000` | **The Breakers** | Intentionally breaks things to expose weak spots (QA + chaos) |
| **Green Team** | 🟢 | `#00FF00` | **The Patchers** | Builds and updates prevention logic (Python code + configs) |
| **Gold Team** | 🟡 | `#FFD700` | **The Narrators** | Explains why actions were allowed/blocked (XAI) |
| **White Team** | ⚪ | `#FFFFFF` | **The Council** | Ensures legality, fairness, compliance, blast-radius governance |
| **Purple Team** | 🟣 | `#800080` | **The Strategists** | Writes RuleSpecs + future-proof scenarios for Green |
| **Orange Team** | 🟠 | `#FF6600` | **The Gatekeepers** | Reviews, approves, and blocks unsafe releases |

**Shared specialist agents (cross-team membership by function):**
- **Scenario Designer Agent** — Red + Black + Purple  
- **Data Forge Agent** — Red + Black + White  
- **Behavior Sequence Agent** — Red + Blue + Black  

> Red is “external mindset” but runs **inside a bank-controlled sandbox**—never against real systems.

---

## 2) Architecture Requirements (Hybrid + Deep Agents)

### 2.1 Orchestration model (Hybrid)
- **Top-level Orchestrator per team (Manager)**: creates plans, delegates work, reconciles results, publishes artifacts.
- **Sub-managers**: per stage (scenario design, detection, rules, patching, testing, approvals, deploy).
- **Specialists**: run in parallel (data forge, trace generation, regression, XAI, compliance).

### 2.2 Deep Agent pillars (must be implemented)
1) **Explicit Planning** (plans, retries, failure handling)  
2) **Hierarchical Delegation** (manager → sub-agents)  
3) **Persistent Memory** (external source of truth)  
4) **Extreme Context Engineering** (protocols, formats, templates)

### 2.3 Agentic system components (must exist)
- Memory (short/long), Knowledge Base, Tool/API integration
- Planning & Decomposition Engine + Execution Loop
- Reasoning & Decision policies (bounded by guardrails)
- Evaluation & Testing frameworks (replays, chaos, coverage)
- Logging & Feedback loops (metrics + audit)
- Goal/KPI tracking (drives HOTL)
- Guardrails & Safety filters (validators beyond RBAC)

---

## 3) Lifecycle Workflow Engine (State Machine) — Required

### 3.1 Purpose
A tenant-aware **workflow engine** coordinates the full fraud lifecycle:
- enforces RBAC + SoD + validator gating,
- routes escalation between teams,
- supports HITL/HOTL,
- emits immutable audit events and evidence.

### 3.2 Minimum states
`INCIDENT_CREATED → TRIAGED → RULESPEC_DRAFTED → RULESPEC_PENDING_APPROVAL → RULESPEC_APPROVED  
→ PATCH_IN_PROGRESS → PATCH_READY → TESTING_IN_PROGRESS → EVIDENCE_READY  
→ PATCH_PENDING_APPROVAL → PATCH_APPROVED → RELEASE_PLANNED → RELEASE_PENDING_APPROVAL  
→ RELEASE_APPROVED → DEPLOYING → DEPLOYED → MONITORING → CLOSED_SUCCESS / ROLLED_BACK`  
Plus `FROZEN` (governance freeze).

### 3.3 Gates (approval points)
- **Gate A: RuleSpec Approval** (Architect/Manager)  
- **Gate B: Patch Approval** (TechLead)  
- **Gate C: Release Approval** (TechManager)  
- **Emergency Override:** TechManager + mandatory justification + audit trail

---

## 4) Autonomy Modes — HITL / HOTL

### 4.1 HITL (Human-in-the-loop)
Human approves **every** fraud fix decision before production.

### 4.2 HOTL (Human-on-the-loop)
AI executes autonomously; human monitors and can intervene.

**HOTL must be policy-conditioned:**
- Governance returns **SAFE_TO_PROCEED**, and
- Automated validators **PASS**, and
- No freeze, and
- Actions are explainable + revertible (rollback ready)

---

## 5) KPI / Risk Governance Service (Goal tracking drives HOTL)

### 5.1 Purpose
A governance service evaluates risk posture and outputs:
- `SAFE_TO_PROCEED`
- `PROCEED_WITH_REVIEW` (forces HITL at next gate)
- `FREEZE_RELEASES`
- `EMERGENCY_HALT`

### 5.2 Minimum KPIs
- Fraud detection quality (TPR), false positives (FPR)
- Detection latency p95/p99
- Money at risk / money saved
- Replay coverage score
- Chaos resilience score
- Security scan status (SAST/DAST/secrets)
- Drift/health (if ML)
- Approval latency + rollback rate

---

## 6) Automated Artifact Validators (Guardrails beyond RBAC)

### 6.1 Required validator categories
- ScenarioSpec Safety Validator (sandbox-only, provenance, no real identifiers)
- RuleSpec Schema & Policy Validator (measurable conditions, reason codes, tests required)
- Patch Validator (links to RuleSpec, quality checks, secrets scan, observability hooks)
- Evidence Validator (replay + chaos + coverage thresholds met)
- Release Readiness Validator (rollback plan, governance SAFE_TO_PROCEED)

### 6.2 Enforcement
- HOTL: **strict PASS**
- HITL: may allow PASS_WITH_WARNINGS if policy allows
- FAIL blocks the transition and creates remediation tasks

---

## 7) RBAC + Approval Flow (UI + API)

### 7.1 Roles
| Human Role | Primary Mode | Summary |
|---|---|---|
| Super Admin | God mode | All tenants/platform; creates Bank Admin |
| Bank Admin | God mode (tenant) | Full control within one bank instance |
| Bank Fraud Operator | HITL/HOTL | Runs/monitors battles; intervenes |
| Bank Fraud Architect/Manager | HITL/HOTL | Edits RuleSpecs; high-impact changes |
| Bank Fraud Dev/Test | HITL/HOTL | Patch dev/testing; runs replays/chaos |
| Bank Fraud TechLead | HITL/HOTL | Reviews/approves patches |
| Bank Fraud TechManager | HITL/HOTL | Release/rollback/kill switch |
| Bank Fraud Auditor | View-only | Logs, evidence packs, compliance |

### 7.2 Separation of Duties (SoD) — Mandatory
- Artifact author cannot approve their own artifacts.
- Severity-based multi-approver policies (tenant configurable).

---

## 8) “War Loop” Orchestration (Simulation-to-Immunity)

**Canonical flow:**
`RED_ATTACK → BLUE_DETECT → {BLOCKED | BLUE_ANALYZE}  
BLUE_ANALYZE → PURPLE_RULESPEC → GREEN_PATCH → BLACK_TEST → ORANGE_APPROVE → GOLD_EXPLAIN → WHITE_GOVERN  
WHITE_GOVERN → {DEPLOY | SHADOW_DEPLOY | REJECT | ESCALATE}`

- If Blue fails to defend: auto-escalate to Purple with the full IncidentDossier.
- If validators fail: block + return remediation tasks to the responsible team.
- If governance FREEZE: block release; open a governance incident.

---

# 9) Signature UI Stations (High-impact “proof” screens)

## 9.1 The War Room (Simulation Engine)
**Purpose:** Visually prove **Failure → Learning → Immunity**.

**Requirements**
- **Orchestration:** LangGraph-orchestrated Red/Blue turn-based simulations.
- **Auto-Play:** agents take turns without manual clicking.
- **Live Metrics:** Fraud Velocity, Money at Risk / Money Saved, Detection Latency, **Time-to-Immunity (Global)**.
- **Chat Stream:** side-by-side agent reasoning stream (red vs blue) for explainability.
- **PAMP Stream:** “matrix-style” raw message stream (JSON/gRPC envelopes) with redaction.
- **Voice Command:** push-to-talk (Whisper) triggers Observer Agent (e.g., “why did we lose?”).

**Acceptance criteria**
- A full battle run is replayable from saved state with identical metrics.
- Every decision links to an artifact + explanation + evidence.

## 9.2 Brain Surgery Station (Live Agent Mutation)
**Purpose:** Demonstrate real **self-healing**, not just prompts.

**Requirements**
- **Tech:** `pyvis` or `streamlit-agraph`.
- **Visual:** force-directed knowledge graph.
  - Blue nodes = current knowledge
  - Green nodes = incoming patch
  - Gold nodes = trusted swarm knowledge
- **Action:** drag-and-drop new skill node to merge.
- **Validation:** hot-swap logic into a running agent via **sandboxed** execution.

**Safety requirement**
- Hot-swaps must run in a sandbox with strict policies (no filesystem/network access unless explicitly allowed by tenant policy).

## 9.3 Difference Visualizer (Proof of Mutation)
**Purpose:** Prove **real code** changed.

**Requirements**
- Split-pane (Before vs After) with syntax highlighting.
- Theme highlights: additions/ removals (tenant-themeable).
- Links from diff to RuleSpec + EvidencePack + approvals.

## 9.4 PAMP & APMC/AMC Manager (Portable Intelligence)
**Purpose:** “PDF of Agentic AI” — portable, auditable intelligence transfer.

**Requirements**
- PAMP schema, encryption (AES-256-GCM), trust handshake, lineage.
- Capsule contents:
  - `manifest.json` (id/version)
  - `memory.vec` (embeddings)
  - `logic.py` (rules/reflex)
  - `lineage.log` (provenance + XAI)
- Export/import agents between tenants/clouds **without** customer data.

## 9.5 Agent Time Machine
**Purpose:** Enterprise-grade recoverability.

**Requirements**
- Versioned snapshots; timeline view; one-click rollback.
- Auto-snapshot triggers: pre-merge, pre-deploy, pre-rollback.

---

## 10) Core Functional Requirements (By Team)

### 10.1 Red Team (The Challengers) 🔴 — P0
- Generate fraud simulations from templates (min 100 types across taxonomy)
- Mutate scenarios based on defender outcomes (learning loop)
- Produce ScenarioSpec + SessionTraces + PAMP message logs (redacted)

### 10.2 Blue Team (The Defenders) 🔵 — P0
- Detect/stop fraud in real time (rules + model + memory retrieval)
- Produce DetectionResult with evidence + confidence + reason codes
- When failing: produce IncidentDossier and escalate to Purple automatically

### 10.3 Black Team (The Breakers) ⚫ — P0
- Edge case discovery; stress testing; false-positive analysis
- Chaos testing and replay harness; produces EvidencePack

### 10.4 Purple Team (The Strategists) 🟣 — P0
- Convert IncidentDossier into RuleSpec (schema + acceptance criteria + tests)
- Maintain taxonomy coverage and future-proof scenario catalog

### 10.5 Green Team (The Patchers) 🟢 — P0
- Generate Python patches from RuleSpec (code + configs)
- Run local sandbox validation; create PatchManifest

### 10.6 Orange Team (The Gatekeepers) 🟠 — P0
- Review patches, enforce quality/security gates, approve/reject
- Ensure SoD and EvidencePack completeness before approval

### 10.7 Gold Team (The Narrators) 🟡 — P0
- XAI narratives; lineage; decision explanation; compliance phrasing
- Every decision must be explainable and linkable to evidence

### 10.8 White Team (The Council) ⚪ — P0
- Governance decisions: approve/conditional/reject/escalate
- Blast radius assessment; deployment scope (local/tenant/global)
- Enforces policy and freeze states

---

## 11) Non-Functional Requirements (NFRs)
### Security & privacy
- Tenant isolation; encryption at rest/in transit; secrets management
- No real PII in synthetic artifacts; validators enforce redaction
- Immutable audit trail; tamper-evident evidence packs

### Reliability
- Workflow transitions are idempotent; retries/timeouts; resumable battles
- HITL fallback if governance/validators unavailable

### Observability
- Tracing across lifecycle transitions; Time-to-Immunity metric
- Audit exports per incident (evidence packs + approvals + diffs)

---

## 12) Definition of Done (DoD) — Minimum demo bar
- Full “War Loop” run: attack → miss → RuleSpec → patch → test → approvals → deploy → re-attack blocked
- War Room shows Time-to-Immunity decreasing across runs
- EvidencePack + approvals + governance decisions are exportable and verifiable
