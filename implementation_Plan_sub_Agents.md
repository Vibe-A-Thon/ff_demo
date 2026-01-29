# Fraud Forge — Sub‑Agent Implementation Plan (from FF_Team_Agents.xlsx)

**Scope:** Implementation plan to build the **sub‑agents layer** (56 agents across 8 teams) in a way that is:
- Copilot-friendly (clear interfaces, schemas, build order)
- Hackathon-safe (synthetic-only, deterministic replay, strong demo flow)
- Extensible (swap mock logic → real engines later)

---

## 0. Build strategy (pragmatic)

### Phase A — Hackathon MVP (works end-to-end)
- Implement the **agent runtime**, registry, orchestrators, state machine, artifact store, and a deterministic “demo run”.
- Each sub-agent returns **structured mock outputs** that match schemas and look realistic.
- UI consumes events + artifacts to show a “living organization”.

### Phase B — Depth upgrade (after MVP is stable)
- Replace mock logic with real modules:
  - rules engine, graph analysis, device scoring
  - ML scoring hooks
  - richer policy & compliance checks

---

## 1. Repo structure (recommended)

```
fraud_forge/
  backend/
    app.py                     # FastAPI entry
    core/
      config.py                # load YAML/JSON configs
      models.py                # Pydantic schemas (Task/Run/Artifact/etc.)
      artifacts/
        store.py               # artifact persistence + lineage
        schemas/               # JSON Schema files per artifact type
      events/
        bus.py                 # pub/sub for live UI updates (in-memory or Redis)
      runtime/
        base_agent.py          # BaseAgent + AgentResult + ValidationResult
        registry.py            # load agents from config and instantiate
        orchestrator.py        # TeamOrchestrator base
        warloop.py             # Red→Blue→...→White state machine
        guardrails.py          # synthetic-only checks, PII checks
        replay.py              # deterministic replay helpers
    teams/
      red/ agents.py
      blue/ agents.py
      purple/ agents.py
      green/ agents.py
      black/ agents.py
      orange/ agents.py
      gold/ agents.py
      white/ agents.py
    tools/
      rules_engine.py          # deterministic rule hits (MVP stub)
      graph_engine.py          # graph/link analysis (MVP stub)
      device_risk.py           # device/session scoring (MVP stub)
      ml_scoring.py            # optional model scoring stub
      chaos.py                 # chaos injection harness for Black team
      perf.py                  # load/burst simulator
    tests/
      test_warloop_e2e.py
      test_replay_determinism.py
      test_guardrails.py
  ui/
    # your chosen UI stack components
  configs/
    teams.json
    agents.json
    routing.yaml
    demo_scenarios/
      flagship_seed_001.json
```

---

## 2. Core schemas (Pydantic + JSON Schema)

### 2.1 Task
- `task_id`, `run_id`, `team_id`, `target_agent_id?`, `type`
- `inputs[]` (artifact refs), `params`, `constraints`, `acceptance_criteria[]`
- `priority`, `created_by`, `status`, `created_at`, `updated_at`
- `seed` (for deterministic replay)

### 2.2 Artifact
- `artifact_id`, `type`, `version`, `schema_version`
- `payload` (JSON), `files[]` (optional)
- `lineage`:
  - `inputs[]` (artifact_ids)
  - `inputs_hash`
  - `created_by` (agent_id)
  - `created_at`
  - `seed`
  - `safety_flags`

### 2.3 AgentResult
- `status` (success/warn/fail)
- `outputs[]` (artifacts)
- `metrics` (latency, quality flags)
- `decision_trace` (short steps list)
- `logs_ref` (pointer to JSONL logs)

### 2.4 ApprovalDecision (for Orange/White)
- `approval_id`, `run_id`, `stage`, `decision` (approve/reject)
- `approver_role`, `rationale`, `timestamp`
- `evidence_refs[]`

---

## 3. BaseAgent + TeamOrchestrator

### 3.1 BaseAgent (must implement)
- `validate(task)` → hard fails if schema/guardrails violated
- `run(task)` → produces deterministic outputs if seeded
- `emit_event(type, payload)` → progress + logs
- `make_artifact(type, payload, inputs, seed)` → standard lineage

### 3.2 TeamOrchestrator (pattern)
Each orchestrator is a subclass that:
- accepts a high-level objective (e.g., “simulate mule network attack”)
- decomposes into sub tasks
- dispatches tasks to sub agents
- aggregates artifacts into a stage bundle

**Required orchestrators (8):**
- Red Orchestrator (Campaign Manager)
- Blue Orchestrator (Defense Manager)
- Purple Orchestrator (Strategy Manager)
- Green Orchestrator (Build Manager)
- Black Orchestrator (Test Manager)
- Orange Orchestrator (Release Manager)
- Gold Orchestrator (Explanation Manager)
- White Orchestrator (Governance Manager)

---

## 4. Agent registry + configuration loading

### 4.1 Generate config from Excel (one-time utility)
Create a script:
- reads `FF_Team_Agents.xlsx`
- outputs `configs/agents.json` with:
  - agent_id, name, team_id, role
  - capabilities tags
  - default tool permissions
  - input/output artifact types

### 4.2 Runtime registry
- `AgentRegistry.load(configs)` builds a mapping `agent_id → instance`
- `TeamRegistry` groups by `team_id`

---

## 5. War Loop state machine (execution engine)

### 5.1 Stages (strict order)
1. `RED_SIMULATE_ATTACK`
2. `BLUE_DETECT_RESPOND`
3. `PURPLE_DIAGNOSE_AND_SPEC`
4. `GREEN_BUILD_PATCH`
5. `BLACK_STRESS_TEST`
6. `ORANGE_RELEASE_GATE`
7. `GOLD_EXPLAIN`
8. `WHITE_GOVERNANCE_GATE`
9. `DONE`

### 5.2 Stage contracts
Each stage must:
- consume prior stage artifacts
- run the team orchestrator
- produce stage artifacts bundle
- write status events
- optionally block at approval gates

### 5.3 Replay
- store run seed + input hashes
- replay must produce identical artifact payload hashes

---

## 6. Sub-agent implementation notes (MVP “good enough”)

### 6.1 Use deterministic generators, not random
- All synthetic entities derive from `seed`
- Example: `customer_id = sha256(seed + "customer" + idx)[:12]`

### 6.2 Provide “realistic” outputs as JSON
- For every agent, implement a payload that looks real:
  - transaction streams, link graphs, rule hit lists, test reports, review checklists
- Avoid deep ML; focus on believable structures + clean UI hooks.

### 6.3 Tool adapters (stub-first)
Implement tool modules that are stable and testable:
- `rules_engine.evaluate(stream, rules)` → rule hits + reason codes
- `graph_engine.build_links(stream)` → nodes/edges + clusters
- `device_risk.score(session)` → proxy/vpn/impossible-travel signals
- `chaos.inject(...)` → simulated failures for Black team
- `perf.run_load(...)` → latency/throughput summary

---

## 7. Approval gates (Orange + White)

### 7.1 Gate implementation
- A stage can enter `WAITING_APPROVAL`
- UI shows:
  - checklist
  - evidence pack
  - approve/reject buttons
- On approval:
  - proceed
- On reject:
  - send remediation tasks back to Purple/Green/Black

---

## 8. Live UI events (to feel “alive”)

Emit events from backend:
- `agent.status.changed`
- `agent.progress`
- `artifact.created`
- `stage.changed`
- `approval.requested`
- `approval.decision`

UI subscribes via:
- WebSocket (preferred) or polling

---

## 9. Test plan (must pass before demo)

### 9.1 E2E tests
- Start run → reaches DONE with approvals auto-approved (demo policy)
- Verify all stages emitted artifacts

### 9.2 Determinism tests
- Run twice with same seed → identical artifact hashes

### 9.3 Guardrail tests
- Attempt to ingest PII → blocked/redacted
- Attempt non-synthetic export in demo mode → blocked

---

## 10. Hackathon-winning additions (implementation)

### 10.1 One-click demo run
- `POST /runs/demo` returns a run_id and streams events

### 10.2 Scoreboard deltas
Compute and store:
- attack success rate (Red)
- detection rate / FPR (Blue)
- time-to-immunity improvement (Purple→Green→Black)
- release readiness score (Orange/White)
- explanation quality score (Gold)

### 10.3 Story-mode report builder
- Build a markdown or HTML report:
  - timeline
  - key artifacts snapshots
  - before/after metrics
  - executive summary + regulator summary
- Export PDF optional.

---

## 11. Copilot build order (do this exactly)

1. Implement schemas (`Task`, `Artifact`, `AgentResult`, `ApprovalDecision`)
2. Implement `BaseAgent`, `AgentRegistry`, artifact store, event bus
3. Implement 8 orchestrators + warloop stage runner
4. Implement sub agents as deterministic “generators” (thin logic)
5. Implement approvals workflow
6. Implement replay + determinism tests
7. Wire UI to events + artifacts
8. Add demo mode + story report + scoreboard

---

## 12. Mapping the Excel agents into code (required)
Create 8 files, one per team, and implement each listed agent as a class that inherits BaseAgent.

**Naming convention:**
- `class RedOrchestrator(BaseOrchestrator): ...`
- `class FraudScenarioGenerator(BaseAgent): ...`
- etc.

**Acceptance:** All 56 agents are instantiable and appear in `/agents` API, and the orchestrators can run the full loop.



---

## Appendix A — Agent class scaffolds (generate these classes)

### Red Team

| Agent ID | Class name | Agent name |
|---|---|---|
| `red.agent.01` | `RedOrchestrator` | Red Orchestrator (Campaign Manager) |
| `red.agent.02` | `FraudScenarioGenerator` | Fraud Scenario Generator |
| `red.agent.03` | `TransactionFraudExecutor` | Transaction Fraud Executor |
| `red.agent.04` | `LoanDepositAbuseAgent` | Loan/Deposit Abuse Agent |
| `red.agent.05` | `IdentitySpoofKycEvasionAgent` | Identity Spoof & KYC Evasion Agent |
| `red.agent.06` | `BotSwarmCoordinationAgent` | Bot Swarm & Coordination Agent |
| `red.agent.07` | `ReconWeakSignalFinder` | Recon & Weak-Signal Finder |
| `red.agent.08` | `AdaptiveLearningAgent` | Adaptive Learning Agent |

### Blue Team

| Agent ID | Class name | Agent name |
|---|---|---|
| `blue.agent.01` | `BlueOrchestrator` | Blue Orchestrator (Defense Manager) |
| `blue.agent.02` | `RuleEvaluationAgent` | Rule Evaluation Agent |
| `blue.agent.03` | `BehavioralBaselineAgent` | Behavioral Baseline Agent |
| `blue.agent.04` | `GraphLinkAnalysisAgent` | Graph & Link Analysis Agent |
| `blue.agent.05` | `DeviceSessionRiskAgent` | Device & Session Risk Agent |
| `blue.agent.06` | `ModelScoringAgent` | Model Scoring Agent |
| `blue.agent.07` | `DecisionActionAgent` | Decision & Action Agent |
| `blue.agent.08` | `IncidentPackagingAgent` | Incident Packaging (Escalation) Agent |
| `blue.agent.09` | `PostDecisionMonitorAgent` | Post-Decision Monitor Agent |

### Purple Team

| Agent ID | Class name | Agent name |
|---|---|---|
| `purple.agent.01` | `PurpleOrchestrator` | Purple Orchestrator (Strategy Manager) |
| `purple.agent.02` | `RootCauseAnalyst` | Root Cause Analyst |
| `purple.agent.03` | `RuleAuthoringAgent` | Rule Authoring Agent |
| `purple.agent.04` | `ThreatForecastingAgent` | Threat Forecasting Agent |
| `purple.agent.05` | `PolicyConstraintAgent` | Policy & Constraint Agent |
| `purple.agent.06` | `KnowledgeGraphCurator` | Knowledge Graph Curator |
| `purple.agent.07` | `RequirementsPackager` | Requirements Packager |

### Green Team

| Agent ID | Class name | Agent name |
|---|---|---|
| `green.agent.01` | `GreenOrchestrator` | Green Orchestrator (Build Manager) |
| `green.agent.02` | `RuleToCodeTranslator` | Rule-to-Code Translator |
| `green.agent.03` | `PipelineIntegrationAgent` | Pipeline & Integration Agent |
| `green.agent.04` | `FeatureEngineeringSignalAgent` | Feature Engineering / Signal Agent |
| `green.agent.05` | `ObservabilityAuditHooksAgent` | Observability & Audit Hooks Agent |
| `green.agent.06` | `PerformanceOptimizationAgent` | Performance & Optimization Agent |
| `green.agent.07` | `ConfigPolicyWiringAgent` | Config & Policy Wiring Agent |

### Black Team

| Agent ID | Class name | Agent name |
|---|---|---|
| `black.agent.01` | `BlackOrchestrator` | Black Orchestrator (Test Manager) |
| `black.agent.02` | `AdversarialReplayAgent` | Adversarial Replay Agent |
| `black.agent.03` | `EdgeCaseGenerator` | Edge-Case Generator |
| `black.agent.04` | `ChaosInjectionAgent` | Chaos Injection Agent |
| `black.agent.05` | `LoadBurstSimulationAgent` | Load / Burst Simulation Agent |
| `black.agent.06` | `RegressionCoverageAuditor` | Regression & Coverage Auditor |
| `black.agent.07` | `DefectTriageReportingAgent` | Defect Triage & Reporting Agent |

### Orange Team

| Agent ID | Class name | Agent name |
|---|---|---|
| `orange.agent.01` | `OrangeOrchestrator` | Orange Orchestrator (Release Manager) |
| `orange.agent.02` | `CodeQualityReviewer` | Code Quality Reviewer |
| `orange.agent.03` | `SecurityReviewAgent` | Security Review Agent |
| `orange.agent.04` | `TestEvidenceVerifier` | Test Evidence Verifier |
| `orange.agent.05` | `ReleaseRiskAssessor` | Release Risk Assessor |
| `orange.agent.06` | `RollbackKillSwitchVerifier` | Rollback & Kill-Switch Verifier |

### Gold Team

| Agent ID | Class name | Agent name |
|---|---|---|
| `gold.agent.01` | `GoldOrchestrator` | Gold Orchestrator (Explanation Manager) |
| `gold.agent.02` | `DecisionExplanationAgent` | Decision Explanation Agent |
| `gold.agent.03` | `EvidenceTraceAgent` | Evidence Trace Agent |
| `gold.agent.04` | `AudienceAdapterAgent` | Audience Adapter Agent |
| `gold.agent.05` | `ExplanationQaAgent` | Explanation QA Agent |
| `gold.agent.06` | `CaseNarrativeAgent` | Case Narrative Agent |

### White Team

| Agent ID | Class name | Agent name |
|---|---|---|
| `white.agent.01` | `WhiteOrchestrator` | White Orchestrator (Governance Manager) |
| `white.agent.02` | `RegulatoryMappingAgent` | Regulatory Mapping Agent |
| `white.agent.03` | `ComplianceValidationAgent` | Compliance Validation Agent |
| `white.agent.04` | `FairnessBiasMonitor` | Fairness & Bias Monitor |
| `white.agent.05` | `AuditTrailIntegrityAgent` | Audit Trail Integrity Agent |
| `white.agent.06` | `ApprovalAuthorityAgent` | Approval Authority Agent |

