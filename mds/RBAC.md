# RBAC.md — Fraud Forge Application
## HITL / HOTL Modes + Role-Based Access Control + Approval Flow (Fraud → Rule/Fix → Deploy)

> **Goal:** Enable a global, bank-grade Fraud Forge platform where AI Teams operate autonomously, but all actions pass through **human governance** via **HITL/HOTL modes**, **RBAC**, and a **UI approval + escalation workflow**.

---

## 1) Human–AI Interaction Modes (HITL / HOTL)

### MODE 1 — **HITL (Human-In-The-Loop)**
**Definition:** Human must explicitly approve **every** key decision before code reaches production.

**Hard gates requiring explicit approval:**
- RuleSpec approval (Purple → Green)
- Patch approval (Green → Review)
- Test evidence sign-off (Black results)
- Release approval (to production)
- Rollback / kill switch activation

**Default usage:**
- New bank onboarding
- High-risk products/channels (cards, cross-border, lending)
- Regulatory sensitive markets or early production phases

---

### MODE 2 — **HOTL (Human-On-The-Loop)**
**Definition:** AI executes autonomously end-to-end; humans monitor continuously and can intervene.

**Key properties:**
- Auto-run simulations and pipelines
- Auto-generate rules/specs, patches, tests
- Auto-push releases subject to policy thresholds
- Human can pause/rollback at any step

**Guardrails (still required):**
- Release is blocked if:
  - Compliance checks fail
  - Test evidence incomplete
  - Drift/fairness threshold violated
  - Risk score exceeds allowed limits
- Full audit trail and reason evidence always generated

**Default usage:**
- Mature bank instance
- Proven stability (high “never fail twice” score)
- Low-risk rule updates / parameter tuning

---

### HITL/HOTL Mode Control
- Mode is set at:
  - **Bank Instance Level** (default policy)
  - Optional overrides per:
    - Channel (Cards/Payments/Loans)
    - Release type (hotfix vs major)
    - Risk level (low/medium/high)

---

## 2) RBAC Roles (Human Users)

### Role List
| Role | Description | Scope |
|---|---|---|
| **Super Admin** | Global platform owner | Cross-tenant (all banks) |
| **Bank Admin** | Bank instance owner | Single bank tenant |
| **Bank Fraud Operator** | Runs/monitors battles, interventions | Single bank tenant |
| **Bank Fraud Architect/Manager** | Rules & strategy editor, “brain surgery” | Single bank tenant |
| **Bank Fraud Dev/Test** | Patch developer/tester | Single bank tenant |
| **Bank Fraud TechLead** | Patch reviewer/approver | Single bank tenant |
| **Bank Fraud TechManager** | Release manager: deploy/rollback/override | Single bank tenant |
| **Bank Fraud Auditor** | Audit-only: logs/compliance/evidence | Single bank tenant |

---

## 3) Core Permission Domains (What the UI Controls)

### Domain Definitions
1. **Platform Admin** — tenants, integrations, security  
2. **Agent Ops** — create/assign/enable/disable agents, quotas  
3. **Scenario Ops** — run Red-Team simulations (“battles”)  
4. **Rules & Strategy** — create/edit/approve RuleSpecs  
5. **Engineering** — generate patches, manage code merges  
6. **Testing** — run replay/chaos, view coverage & resilience  
7. **Review & Approve** — review patches, approve/deny, request changes  
8. **Audit & Compliance** — logs, evidence packs, reports  
9. **Human Override** — pause pipeline, kill switch, rollback, emergency release control  

---

## 4) Role → Domain Access Matrix (RBAC)

Legend:  
- **FULL** = create/edit/approve/delete + configure  
- **WRITE** = create/edit/execute actions  
- **READ** = view only  
- **NONE** = no access  

| Role \ Domain | Platform Admin | Agent Ops | Scenario Ops | Rules & Strategy | Engineering | Testing | Review & Approve | Audit & Compliance | Human Override |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **Super Admin** | FULL | FULL | FULL | FULL | FULL | FULL | FULL | FULL | FULL |
| **Bank Admin** | FULL (bank-only) | FULL (bank-only) | WRITE | FULL | WRITE | WRITE | WRITE | READ | WRITE (bank-only) |
| **Bank Fraud Operator** | NONE | READ | WRITE | READ | NONE | READ | NONE | READ | WRITE (pause/intervene only) |
| **Bank Fraud Architect/Manager** | NONE | READ | READ | FULL | READ | READ | WRITE (RuleSpec approval) | READ | NONE |
| **Bank Fraud Dev/Test** | NONE | READ | READ | READ | WRITE | WRITE | READ | READ | NONE |
| **Bank Fraud TechLead** | NONE | READ | READ | READ | READ | READ | FULL (Patch review/approve) | READ | NONE |
| **Bank Fraud TechManager** | NONE | READ | READ | READ | READ | READ | WRITE (Release approval) | READ | FULL (release/rollback/kill switch) |
| **Bank Fraud Auditor** | NONE | NONE | NONE | READ | READ | READ | READ | FULL | NONE |

> Notes:
- **Bank Admin** can manage the bank’s configuration and agent ops but should not be the only approval authority in mature orgs—keep separation of duties when possible.
- **Fraud Operator** can intervene operationally (pause a run, stop a battle) but cannot alter rules or code.
- **Auditor** is read-only except for generating/exporting reports.

---

## 5) Separation of Duties (SoD) Rules (Bank-Grade Controls)

To prevent conflicts and ensure governance:

### Mandatory SoD Constraints
1. **Rule Author ≠ Rule Approver**
   - If Architect edits RuleSpec, approval must be by **TechLead/Manager** (or secondary Architect role).
2. **Code Author ≠ Code Approver**
   - Dev/Test cannot approve their own patch. Approval by **TechLead**.
3. **Release Approver ≠ Patch Author**
   - Release controlled by **TechManager**.
4. **Audit is read-only**
   - Auditor cannot approve or modify.
5. **Human Override limited**
   - Only TechManager (and Bank Admin in bank-scope emergency) can execute kill switch/rollback.

---

## 6) Approval Flow — UI Workflow (Fraud → Rule/Fix → Deploy)

### Canonical Lifecycle Stages
1. **Fraud Event / Simulation Outcome**
2. **Detection Outcome**
3. **Escalation (if miss or weakness)**
4. **RuleSpec Draft**
5. **RuleSpec Review + Approval**
6. **Patch Generation**
7. **Testing + Evidence**
8. **Patch Review + Approval**
9. **Release Approval**
10. **Deploy**
11. **Post-Deploy Monitoring**
12. **Rollback (if required)**

---

### Stage-by-Stage Flow with Roles

#### Stage 1 — Fraud Event / Simulation Outcome
- Triggered by:
  - 🔴 Red Team “battle”
  - ⚫ Black Team stress test
  - 🔵 Blue Team production incident
- **UI Owner:** Bank Fraud Operator (monitor), Auditor (view)
- **Artifacts Produced:**
  - ScenarioSpec ID
  - Trace pack
  - Outcome classification (blocked / missed / uncertain)

#### Stage 2 — Detection Outcome (Blue)
- Blue Team generates:
  - decision action
  - evidence pack
  - reason codes
- **UI Owner:** Fraud Operator (monitor)

#### Stage 3 — Escalation
- If fraud not blocked or weakness found:
  - Blue/Black escalates to Purple
- **UI Owner:** Fraud Architect/Manager
- **Artifact:** Incident Dossier (full context)

#### Stage 4 — RuleSpec Draft (Purple)
- Purple generates RuleSpec + acceptance criteria
- **UI Owner:** Fraud Architect/Manager
- **Artifact:** RuleSpec vX, tests required, risk classification

#### Stage 5 — RuleSpec Approval (Gate 1)
- **HITL:** mandatory approval
- **HOTL:** auto-approve only if policy says “low-risk” and thresholds pass; else manual
- **Approver Role:** Fraud Architect/Manager (primary) + optional TechLead co-approval
- **Outcome:** Approved / Rejected / Needs changes

#### Stage 6 — Patch Generation (Green)
- Green generates code patch PR + config changes
- **UI Owner:** Fraud Dev/Test
- **Artifact:** Patch ID, PR link, build artifacts

#### Stage 7 — Testing & Evidence (Black)
- Black runs:
  - replay suite
  - chaos experiments (if required)
  - coverage and resilience scoring
- **UI Owner:** Fraud Dev/Test (execute), TechLead (view)
- **Artifact:** Test Evidence Pack + Coverage Report + Resilience Score

#### Stage 8 — Patch Review & Approval (Gate 2)
- **Approver Role:** Bank Fraud TechLead
- Reviews:
  - code quality
  - security checks
  - test evidence completeness
- **Outcome:** Approved / Rejected / Changes requested

#### Stage 9 — Release Approval (Gate 3)
- **Approver Role:** Bank Fraud TechManager
- Validates:
  - rollout plan (canary/phased)
  - rollback plan
  - policy + compliance status
- **Outcome:** Release Approved / Held / Emergency path

#### Stage 10 — Deploy
- Deployment executed (autonomous or human-triggered)
- **UI Owner:** TechManager (monitor), Operator (monitor)

#### Stage 11 — Post-Deploy Monitoring
- Blue monitors live metrics:
  - fraud capture
  - false positives
  - latency
  - drift indicators
- **UI Owner:** Fraud Operator + Architect

#### Stage 12 — Rollback / Kill Switch (Emergency)
- **Role:** TechManager (primary), Bank Admin (bank-scope backup)
- Logged with reason + evidence

---

## 7) Mode-Specific Behavior in UI (HITL vs HOTL)

### HITL UI Rules
- Every gate requires explicit human click:
  - Approve RuleSpec
  - Approve Patch
  - Approve Release
- Show “Pending Approval” queues by role
- Escalation SLA timers

### HOTL UI Rules
- AI proceeds automatically if policy thresholds are met
- UI shows “Autonomous Actions Feed”
- Humans can:
  - pause pipeline
  - request review
  - rollback
  - override decisions
- Auto-generated justification displayed for every autonomous step

---

## 8) Recommended UI Screens (RBAC-aligned)

### Super Admin
- Global Tenants Console
- Global Integrations
- Global Security Center
- Global Agent Quotas

### Bank Admin
- Bank Setup & Integrations
- Agent Pools & Quotas
- Bank Policy & Mode Settings (HITL/HOTL)

### Fraud Operator
- Battles Dashboard (run/monitor)
- Live Fraud Monitor
- Intervention Controls (pause/stop)

### Fraud Architect/Manager
- RuleSpec Studio
- Escalations Inbox
- Strategy Dashboard (taxonomy coverage, gap heatmaps)

### Fraud Dev/Test
- Patch Builder
- Test Runner (replays/chaos)
- Evidence Pack Viewer

### TechLead
- Review Console (PR + Evidence)
- Approvals Queue
- Security Findings

### TechManager
- Release Console (deploy/canary/rollback)
- Override Center (kill switch)
- Rollback History

### Auditor
- Audit Log Viewer
- Evidence Pack Archive
- Compliance Reports Export

---

## 9) Audit Trail Requirements (Always On)
Every action must log:
- who (human role / agent identity)
- what (artifact id: ScenarioSpec/RuleSpec/Patch/Release)
- when (timestamp)
- why (reason + link to evidence)
- mode (HITL/HOTL)
- decision outcome (approved/denied/auto)

---

## 10) Minimal Policy Defaults (Practical Starting Point)

### Default Bank Policy (Recommended)
- Start new banks in **HITL**
- Switch to **HOTL** only after:
  - stable test coverage > threshold
  - resilience score > threshold
  - “never fail twice” score > threshold
  - auditor sign-off on governance logs

### HOTL Auto-Approve Conditions (Example)
- Rule change classified low-risk
- No new features required
- Full replay passes
- No fairness/compliance alerts
- Canary plan exists + rollback validated

---

## 11) Implementation Notes (For Developers)
- Implement RBAC using:
  - Tenant-aware roles
  - Domain permissions
  - Artifact-level ACLs (optional)
- Implement approval objects:
  - `ApprovalRequest` with stage, artifact_id, required_role, mode, status
- Provide UI queues by role:
  - “Approvals Pending”
  - “Escalations”
  - “Autonomous Actions Feed”
- Enforce SoD programmatically:
  - prevent self-approval checks in workflow engine

---