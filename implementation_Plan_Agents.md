# Fraud Forge — Dev Implementation Plan (Agent Teams)

## 1. Goal
Implement the **Agent Teams layer** of Fraud Forge as a configurable “organization engine” with:
- Team directory + agent roster UI
- Task routing and orchestration across teams
- Evidence lineage + explainability integration
- Governance gates (approvals + compliance)

This plan is optimized for **hackathon delivery** while remaining scalable.

---

## 2. Recommended MVP scope (hackathon)
### Must deliver (P0)
- Team model (8 teams) rendered in UI from config
- Agent registry (stub agents per team) + status updates
- Run pipeline that simulates the War Loop with deterministic mock outputs
- Evidence links + explanation pack placeholder
- Approval gates (Orange + White) as UI workflows

### Nice to have (P1)
- Graph lineage visualization between artifacts
- Basic rule/patch diff viewer
- Stress test dashboard

---

## 3. Architecture (reference)
### 3.1 Services/modules
- **UI (React/Next.js or Streamlit UI layer)**
  - Teams, Agents, War Loop, Evidence
- **API (FastAPI)**
  - team/agent registry, tasks, runs, artifacts, approvals
- **Orchestrator**
  - simple state machine for the War Loop
  - pluggable agent executors
- **Storage**
  - SQLite/Postgres for hackathon
  - file store for artifacts (JSON/MD/PDF)
- **Event bus**
  - in-memory pub/sub or Redis (optional) for live UI updates

---

## 4. Data model (schemas)
Create JSON schemas (or Pydantic models) for:

### 4.1 Team
```json
{
  "team_id": "red",
  "internal_name": "Red Team",
  "bank_facing_name": "The Challengers",
  "colour_token": "red",
  "mission_statement": "...",
  "capability_tags": ["attack", "simulation"],
  "default_agent_roles": ["AttackPlanner", "EvasionDesigner"]
}
```

### 4.2 Agent
```json
{
  "agent_id": "red.attack_planner.01",
  "agent_name": "Attack Planner 01",
  "team_id": "red",
  "role": "AttackPlanner",
  "capabilities": ["scenario_generate", "variant_mutate"],
  "operating_mode": "semi_auto",
  "guardrails": ["synthetic_only"],
  "status": "idle",
  "metrics": {"success_rate": 0.78, "avg_latency_ms": 540}
}
```

### 4.3 Task / Run / Artifact / ApprovalDecision
- `Task`: who requested, target team/agent, input artifacts, priority, status
- `Run`: pipeline state, stage outcomes, timestamps, replay seed
- `Artifact`: typed payload with version + lineage links
- `ApprovalDecision`: approver role, outcome, rationale, timestamp

---

## 5. Backend APIs (FastAPI)
### 5.1 Teams & Agents
- `GET /teams`
- `GET /teams/{team_id}`
- `GET /agents?team_id=red`
- `POST /agents/{agent_id}/assign-task`
- `POST /agents/{agent_id}/pause|resume|retry`

### 5.2 Runs (War Loop)
- `POST /runs` (start demo run)
- `GET /runs/{run_id}` (status + current stage)
- `POST /runs/{run_id}/step` (manual stepping)
- `POST /runs/{run_id}/replay` (replay from seed)

### 5.3 Artifacts & Evidence
- `GET /runs/{run_id}/artifacts`
- `GET /artifacts/{artifact_id}`
- `GET /artifacts/{artifact_id}/lineage`

### 5.4 Governance
- `GET /approvals?status=pending`
- `POST /approvals/{approval_id}/decision` (approve/reject)

---

## 6. Orchestration logic (War Loop state machine)
Implement a simple state machine:

1. `RED_SIMULATE_ATTACK`
2. `BLUE_DETECT_RESPOND`
3. `PURPLE_IMPROVE_STRATEGY`
4. `GREEN_BUILD_PATCH`
5. `BLACK_STRESS_TEST`
6. `ORANGE_REVIEW_APPROVE`
7. `GOLD_GENERATE_EXPLANATION`
8. `WHITE_COMPLIANCE_AUDIT`
9. `DONE`

### Execution options
- **Auto**: run stages sequentially with timers
- **Manual**: user steps stages (ideal for demos)

Each stage must produce an artifact and attach it to lineage.

---

## 7. UI implementation (screen/components)

### 7.1 Team Directory
- Team cards with colour badge + bank-facing name + mission
- Click → Team detail (agents + workload)

### 7.2 Agent Roster
- Agent list with status chips, current task, last output
- Expand row → capability list, guardrails, metrics
- Actions: Assign task, Pause/Resume, View logs

### 7.3 War Loop Timeline
- Horizontal stage timeline with:
  - current stage highlight
  - pass/fail icons
  - “evidence” button per stage
- Player controls: Auto-play, Pause, Next stage, Replay

### 7.4 Evidence Drawer (right panel)
- Shows artifacts for current stage
- “Explanation” tab (Gold)
- “Approvals” tab (Orange/White)

---

## 8. Deterministic demo outputs (hackathon tactic)
To avoid flaky demos:
- Use a fixed `seed` per scenario
- Generate consistent mock outputs per stage:
  - Red: attack steps + “fraud velocity”
  - Blue: alerts + detection score
  - Purple: improved RuleSpec
  - Green: patch diff summary
  - Black: stress test summary
  - Orange: approval decision
  - Gold: explanation narrative
  - White: compliance checklist

---

## 9. Guardrails & compliance (minimum)
- Enforce `synthetic_only` flag in config
- Watermark exports with provenance metadata
- Disable raw export for restricted roles (RBAC later)

---

## 10. Build order (Copilot-friendly)
1. Create `teams.json` + `agents.json`
2. Implement Pydantic models + `/teams` `/agents`
3. Implement state machine + `/runs`
4. Implement artifact store + lineage links
5. Build UI: Team Directory → Team Detail → War Loop → Evidence Drawer
6. Add approvals workflow + SAFE_TO_PROCEED gating
7. Add replay + story-mode report export (optional)

---

## 11. What makes this “100% hackathon winning”
- “Living organization” UX: agents animate + statuses change live
- One-click demo run with replay fallback
- Clear before/after deltas + explanation pack
- Governance gates shown visually (trust + enterprise feel)

