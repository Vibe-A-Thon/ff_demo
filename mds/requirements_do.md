# Fraud Forge — Requirements (derived from `doc.pdf`)

> Source: handwritten design notes in `doc.pdf` (4 pages). fileciteturn11file0

## 0) Objective
Build **Fraud Forge** as an enterprise-grade, hackathon-ready application that behaves like a **living organization of AI/XAI agent teams** executing an iterative “war loop”:
- **Red (Challengers)** simulates evolving fraud attacks
- **Blue (Defenders)** detects/prevents/responds
- **Purple (Strategists)** improves threat model + RuleSpecs
- **Green (Builders)** produces production-grade code patches
- **Black (Stressors)** stress-tests robustness + failure handling
- **Orange (Gatekeepers)** validates/reviews and approves releases
- **White (Council/Auditors)** ensures compliance/audit readiness
- **Gold (Narrators)** provides full XAI explanation pack

(Teams/role mapping and flow are explicitly listed on pages 1–2.)

---

## 1) Personas, Roles, and RBAC (P0)
### 1.1 Login module (RBAC)
**Requirement:** App must have an RBAC-based login module. (Page 1)

### 1.2 Roles (minimum from doc)
- **SA — System Architect**
- **BA — Business Architect**
(From page 1. Expandable in future: analyst/operator/admin.)

### 1.3 RBAC enforcement rules
- Screen-level access control + action-level permissions
- Human-in-the-loop approvals enforced by RBAC for:
  - **Visual Patch**
  - **Brain Surgery**
(From page 4: “state machine process invokes human intervention via RBAC”.)

### 1.4 Audit logging (P0)
- Every RBAC-protected action must write an audit event:
  - who, what, when, artifact ids, decision (approve/reject), rationale

---

## 2) Team and Agent Organization Model (P0)
### 2.1 Teams (canonical)
From page 1 (team list):
- Red — Challengers
- Blue — Defenders
- Purple — Strategics/Strategists
- Green — Builders
- Black — Stressors
- Orange — Gatekeepers
- Gold — Narrators
- White — Council / Auditors

### 2.2 Agentic capability assumption
Each team contains multiple AI/XAI agents with agentic capabilities. (Page 1)

**Requirement:** The system must allow:
- Configuring teams and their agents (count, names, roles)
- Assigning tasks/runs to teams/agents
- Viewing agent status (idle/running/blocked/failed)
- Capturing agent outputs as artifacts (versioned)

---

## 3) War Loop State Machine (P0)
### 3.1 Primary flow
From page 2 diagram:
- **R → B → End** (fast path)
- or **R → B → Purple → Green → Black → (Success) Orange → White**
- If **Fail** at testing, loop returns back to **Purple** (for redesign) then re-run downstream stages
- **Gold** produces “XAI full details about project” (page 2 note)

### 3.2 State machine requirements
- Must track run state per scenario/run id
- Must persist stage outputs as artifacts
- Must support:
  - Auto-run (end-to-end)
  - Manual step-through (for demo)
  - Replay (deterministic seed)

### 3.3 Gate requirements
- Orange/White stages must be approval-gated via RBAC (HITL)
- If Orange/White rejects, run returns to appropriate prior stage with reason

---

## 4) APMC — Agent Portable Memory Capsule (P0)
From page 2:
- APMC is an **Agent Portable Memory Capsule** (portable model updates/learning)
- Contains:
  - baseline model updates/learning post baseline
  - **Experience**
  - **Memory**

### 4.1 APMC requirements
- Import/export APMC packages (zip)
- View APMC metadata:
  - version, author/team, timestamp, summary, change log
- Validate APMC:
  - schema validity
  - safety constraints (no real PII, synthetic only in hackathon mode)
- Apply/attach APMC to a run
- Maintain lineage: which APMC influenced which run and patch

---

## 5) RSB — Rule Suite Box (P0)
From page 3:
RSB contains:
- **Rule Spec**: Markdown file with rule details & characteristics
- **Rule Code**: Python code implementing rule/fix
- **Patcher**: mechanism to patch RuleSpec + RuleCode

### 5.1 RSB requirements
- Import/export RSB packages
- Inspect contents (manifest/tree view)
- Validate:
  - RuleSpec presence and required fields
  - RuleCode presence and unit tests presence (recommended)
  - Patcher script presence/compatibility
- Merge RSB updates with conflict resolution
- Produce “staged RSB” ready for deployment

---

## 6) Brain Surgery UI (P0/P1)
From page 3:
A UI showing **3-frame view**:
1) Existing model
2) Model with loaded APMC
3) Merged model (APMC + existing model)

### 6.1 Brain Surgery requirements
- 3-pane comparison layout (side-by-side)
- Highlight differences between:
  - baseline vs APMC-enhanced vs merged
- Provide a safe “merge/apply” action gated by RBAC
- Provide “rollback” action to revert to baseline snapshot

---

## 7) Visual Patcher (P0)
From pages 3–4:
- Must visually show **code, patches, RuleSpec**
- Must patch the existing **code repo and existing RuleSpec**
- Driven by the same state-machine + RBAC intervention

### 7.1 Visual patch requirements
- Diff viewer for RuleSpec (markdown diff)
- Diff viewer for RuleCode (python diff)
- Patch apply controls (accept/reject per hunk)
- Test runner panel (execute unit tests / integration checks)
- Commit packaging (build an updated RSB or patch bundle)

---

## 8) LLM + RAG Integration (P0/P1)
From page 4:
- “Need to connect to LLM by open API key and build a RAG with fraud rules.”

### 8.1 LLM connectivity requirements
- UI to store API key securely (or env var for hackathon)
- Provider abstraction: OpenAI-compatible base URL + model name
- Rate limit + retry + timeout handling

### 8.2 RAG requirements (fraud rules)
- Ingest RuleSpecs + taxonomy docs into vector store
- Retrieval used to:
  - propose RuleSpec improvements (Purple)
  - generate patch suggestions (Green)
  - produce explanations (Gold)
- Evidence: each generated suggestion must cite retrieved snippets

---

## 9) Commercial packaging options (P1)
From page 2 (offerings):
1) Add-on experience-based performance (SaaS)
2) Complete installation (SaaS)
3) Only software (PaaS)

**Requirement:** Document deployment options and provide config toggles:
- “SaaS demo mode” (single-tenant)
- “On-prem/PaaS mode” (local services + self-hosted)

---

## 10) Hackathon-winning product requirements (must add)
### 10.1 Demo-first controls (P0)
- **One-click “Demo Run”** that executes the war loop with deterministic seed
- “Replay last run” fallback (offline-safe demo)

### 10.2 Scoreboard + story mode (P0)
- Show before/after metrics (detection rate, false positive rate, time-to-immunity)
- Generate a **Story Report**:
  - timeline of stages
  - key diffs (RuleSpec/RuleCode)
  - XAI narrative pack
  - approvals and audit trail

### 10.3 Safety guardrails (P0)
- Synthetic-only data generation toggle ON by default
- Watermark all exports (DEMO / SYNTHETIC)
- Redact any accidental identifiers in outputs

---

## 11) Acceptance criteria (minimum)
- Login + RBAC works for SA/BA and gates Brain Surgery + Visual Patch actions
- State machine runs end-to-end (manual + auto) and supports Fail→Purple loop
- RSB import/inspect/validate + staging works
- APMC import + apply and 3-frame Brain Surgery view works
- Visual patcher shows diffs and can apply patch + run tests
- LLM+RAG can answer “why” and propose a RuleSpec improvement with citations
- Demo run + story report export works reliably

