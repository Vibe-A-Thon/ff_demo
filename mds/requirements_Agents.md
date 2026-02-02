# Fraud Forge — Agent Teams Requirements (from Team Model image)

## 1. Purpose
Fraud Forge operates like a **living organization** of AI agent teams. Each team has a distinct mission and a **bank-facing name** for product storytelling.

This document defines the **requirements** for representing, managing, and orchestrating these teams and their agents in the application.

---

## 2. Team model (canonical mapping)

| Internal Team | Colour | Market / Bank‑Facing Name | Meaning (plain English) |
|---|---|---|---|
| Red Team | 🔴 | **The Challengers** | Simulates real‑world fraudsters; generates and executes evolving fraud attacks (external threat model). |
| Blue Team | 🔵 | **The Defenders** | Real‑time fraud detection, prevention, and response across all banking channels. |
| Black Team | ⚫ | **The Stressors** | Intentionally breaks systems; stress‑tests defenses; validates robustness and failure handling. |
| Green Team | 🟢 | **The Builders** | Converts fraud rules and strategies into production‑grade Python code. |
| Gold Team | 🟡 | **The Narrators** | Ensures AI decisions are interpretable, auditable, and human‑understandable. |
| White Team | ⚪ | **The Council** | Ensures legality, regulatory compliance, fairness, ethics, and audit readiness. |
| Purple Team | 🟣 | **The Strategists** | Designs fraud rules, threat models, policies, and future‑proof detection strategies. |
| Orange Team | 🟠 | **The Gatekeepers** | Performs code review, security validation, and final release approval. |

---

## 3. Organizational “War Loop” (required behavior)
The system must support the following **organizational operating loop**:

1. **Challengers (Red)** simulate attacks & try to break the bank.
2. **Defenders (Blue)** stop them (detect/prevent/respond).
3. **Strategists (Purple)** learn from outcomes & improve strategy/rules.
4. **Builders (Green)** implement rules/strategies into production-grade code.
5. **Stressors (Black)** stress-test robustness, degradation, and failure handling.
6. **Gatekeepers (Orange)** review and approve releases & changes.
7. **Narrators (Gold)** explain decisions, evidence, and rationale.
8. **Council (White)** ensures trust, ethics, compliance, and audit readiness.

**Requirement:** The UI and orchestration layer must make this loop visible, trackable, and replayable.

---

## 4. Core entities & metadata requirements

### 4.1 Team entity
Each Team must have:
- `team_id` (e.g., `red`, `blue`, `black`, `green`, `gold`, `white`, `purple`, `orange`)
- `internal_name` (e.g., “Red Team”)
- `bank_facing_name` (e.g., “The Challengers”)
- `colour_token` (UI token, not hard-coded hex)
- `mission_statement`
- `capability_tags` (search/filter)
- `default_agent_roles` (what agents exist by default)

### 4.2 Agent entity
Each Agent must have:
- `agent_id`, `agent_name`, `team_id`
- `role` (e.g., Attack Planner, Detector Tuner, Policy Reviewer)
- `capabilities` (list)
- `inputs` and `outputs` (artifact types)
- `operating_mode` (manual / semi-auto / auto)
- `guardrails` (constraints, safety rules)
- `status` (idle/running/waiting/blocked/failed)
- `metrics` (success rate, time-to-complete, quality score)

### 4.3 Artifacts (minimum set)
System must represent and trace:
- `Scenario` / `AttackPlan` (Red)
- `Telemetry` / `Alerts` / `Observations` (Blue)
- `Strategy` / `RuleSpec` / `ThreatModel` (Purple)
- `Patch` / `CodeChange` / `Package` (Green)
- `StressTestReport` / `ChaosRun` results (Black)
- `ApprovalDecision` / `ReleaseNote` (Orange)
- `ExplanationPack` (Gold)
- `CompliancePack` / `AuditPack` (White)

All artifacts must be:
- versioned,
- linked to a run/session,
- traceable end-to-end (lineage graph).

---

## 5. UI/UX requirements for agent teams

### 5.1 Team Directory (P0)
- Grid/list of teams showing: colour, internal name, bank-facing name, mission
- Click → Team Detail page with:
  - agent roster
  - current workload
  - recent outcomes
  - top artifacts produced
  - “start task” shortcuts

### 5.2 Agent Roster & Status (P0)
- Real-time status badges for each agent
- “What it does” panel (inputs/outputs, constraints)
- Quick actions: assign task, pause, resume, retry, view logs

### 5.3 War Loop Timeline (P0)
- Visual timeline of loop stages (Red→Blue→Purple→Green→Black→Orange→Gold→White)
- Stage completion indicators and blockers
- “Jump to evidence” links for each stage output

### 5.4 Evidence & Explainability Everywhere (P0)
- Every stage output must link to:
  - evidence used
  - decisions made
  - explanation (Gold)
  - approvals (Orange)
  - compliance notes (White)

### 5.5 Governance Visibility (P0)
- Approval gates clearly shown (Gatekeepers + Council)
- Who approved/blocked and why
- Safe-to-proceed indicator

---

## 6. Orchestration requirements

### 6.1 Task routing
- Tasks must route to **teams** and optionally **specific agents**.
- Default routing rules:
  - Attack simulation → Red
  - Detection response → Blue
  - Strategy/rules → Purple
  - Code patch → Green
  - Stress test → Black
  - Release review → Orange
  - Explanation → Gold
  - Compliance audit → White

### 6.2 Collaboration protocol
- Teams can request artifacts from others via a structured request:
  - `request_id`, `from_team`, `to_team`, `artifact_type`, `priority`, `due_by`
- Requests and responses must be logged and visible.

### 6.3 Safety guardrails (non-negotiable)
- “Synthetic-only / sandbox-only” operation mode default
- Disallow real customer identifiers
- Export controls (watermarks + provenance metadata)

---

## 7. Non-functional requirements
- **Auditability:** every action → immutable log entry
- **Repeatability:** runs can be replayed
- **Explainability:** explanations generated for key decisions
- **Latency:** UI updates in near real-time for demos
- **Resilience:** failed agent actions are recoverable (retry/rollback)
- **Extensibility:** new teams/agents/capabilities can be added via config

---

## 8. Hackathon demo requirements (to “win”)
- One-click “Demo Run” of the full War Loop (preloaded scenario)
- Live scoreboard: attack success vs defense improvements
- Story-mode report: timeline + key deltas + explainability pack export
- Visual “living organization” feel: agents animate, statuses update, evidence links pop

