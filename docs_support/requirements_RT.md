# requirements_RT.md — Fraud Forge External Red Team (Agentic) Requirements

> **Purpose**: Define a banking-grade, *safe*, *authorized*, **external** AI Red Team system that can (a) execute simulations for the existing fraud taxonomy catalog and (b) **generate novel adversarial scenario variants** via constrained creativity, *without enabling real-world wrongdoing*.  
> **Audience**: Engineering team using GitHub Copilot (GHCP), product/security, bank stakeholders (Fraud/AML/InfoSec/Compliance).

---

## 0) Guiding Principles (Hard Rules)

1. **Authorized-only**: Simulations run **only** under a signed Rules of Engagement (RoE) and **only** in bank-approved environments (UAT/pre-prod/digital twin).
2. **No real harm**:
   - No use of real customer PII in simulations.
   - No real money movement.
   - No contacting real counterparties.
   - No instructions that operationalize fraud. Output is **event/telemetry specifications** and **defense testing** artifacts.
3. **Defense-first**: Every run must produce measurable defensive learnings:
   - telemetry → detection → response → control gaps → remediation recommendations.
4. **Auditable and repeatable**: Deterministic replays, immutable logs, traceable lineage for generated scenarios.

---

## 1) Product Scope

### 1.1 In-Scope
- Import and execute **seed scenarios** (e.g., 120+ catalog) across **consumer + commercial banking**.
- Generate **novel adversarial scenarios** via:
  - mutation/permutation operators,
  - adversarial search (coverage-gap targeted),
  - safe compositional chaining across rails/channels/workflows.
- Orchestrate simulations across:
  - **USA-heavy rails**: ACH (incl. return codes), wires (domestic + SWIFT), checks/RDC, RTP/FedNow, P2P.
  - cards (auth streams, disputes),
  - onboarding/KYC/KYB,
  - commercial treasury workflows (entitlements, approvals, templates, batches).
- Provide reporting:
  - coverage matrix, gap analysis, control recommendations,
  - red-team findings and blue-team verification tests.

### 1.2 Out-of-Scope (Explicitly Prohibited)
- Generation of step-by-step instructions for committing fraud in the real world.
- Tools that attempt exploitation of bank systems beyond safe simulation channels.
- Any feature that can run against production endpoints without explicit bank authorization.
- Any feature that uses or stores real customer PII for simulation.

---

## 2) Personas & Roles

### 2.1 User Roles
- **Bank Admin (Blue-side Owner)**: configures integrations, approves RoE, sets test windows/limits.
- **Red Team Operator (Vendor)**: selects campaigns, runs simulations, reviews findings.
- **Blue Team Operator (Bank Fraud Ops)**: monitors alerts/cases, measures response SLAs, tunes controls.
- **Auditor/Compliance Reviewer**: reviews audit trails, scenario lineage, evidence packages.

### 2.2 Role-Based Access Control (RBAC)
- Roles: `BANK_ADMIN`, `BANK_ANALYST`, `VENDOR_OPERATOR`, `AUDITOR`, `READONLY`.
- Fine-grained permissions for:
  - scenario authoring,
  - campaign execution,
  - connector configuration,
  - export of findings (with data minimization).

---

## 3) Deployment & Boundary Model (External Red Team)

### 3.1 Preferred Deployment (Recommended)
**Bank-hosted deployment** (containers in bank UAT/pre-prod or isolated VPC):
- Vendor provides signed container images.
- Bank controls network, secrets, and outbound access.
- Vendor receives **aggregated/non-sensitive** results via controlled export.

### 3.2 Alternative Deployment (If allowed by bank)
**Vendor-hosted control plane** + bank-hosted execution agents:
- Control plane handles orchestration metadata only.
- Execution happens inside bank boundary.
- Only sanitized metrics and reports leave the bank network.

### 3.3 Mandatory Controls
- Kill switch (global + per-campaign).
- Rate limits and volume caps.
- Allowlists for target systems (UAT/pre-prod only).
- Immutable audit logging for all actions.

---

## 4) High-Level Architecture

### 4.1 Core Components
1. **Scenario Catalog Service**
   - imports seed catalog JSON
   - stores canonical scenario specs (versioned)
2. **Novel Scenario Generator (NASG)**
   - constrained creativity: mutation + adversarial search
   - produces scenario variants as “Simulation Packs”
3. **Simulation Orchestrator**
   - schedules campaigns
   - enforces RoE, limits, kill-switch
4. **Digital Twin / Event Simulator**
   - emits bank-observable events & telemetry (safe)
   - supports channel/rail simulators
5. **Connector Layer**
   - integrates with bank fraud stack (read/write where allowed)
   - SIEM/SOAR/case mgmt/data lake
6. **Evaluation Engine**
   - collects outcomes, calculates coverage metrics
   - generates evidence, gap hypotheses, remediation items
7. **Reporting & Dashboards**
   - coverage heatmaps, scenario lineage, SLA metrics
8. **Policy & Safety Gate**
   - blocks unsafe/operationally harmful scenario specs
   - validates feasibility, telemetry completeness, and compliance constraints

### 4.2 Data Flow (Conceptual)
Seed Catalog → Scenario Compiler → NASG variants → Safety Gate → Orchestrator → Simulators → Bank Systems → Outcome Collector → Evaluation → Reports/Exports

---

## 5) Scenario Model (Simulation Pack)

### 5.1 Requirements
Each scenario (seed or generated) MUST include:
- **Identity**: IDs, family mapping, tags (rail/channel/segment)
- **Entry vector** (high-level)
- **Prerequisites** (environment state, entitlements, limits)
- **Event flow** as **phases** (not operational instructions)
- **Telemetry contract**: required observable signals/events
- **Expected controls**: step-up/holds/case/blocks/limits
- **Test cases**:
  - Red-team objective assertions (what should stress defenses)
  - Blue-team detection/response assertions (what should trigger)
- **Segment applicability**: consumer/commercial/both
- **Lineage** for generated scenarios:
  - seed(s), mutation operators, novelty rationale

### 5.2 Minimal JSON Schema (guidance)
```json
{
  "scenario_id": "F07-GEN-2026-000123",
  "family_id": "F07",
  "scenario_name": "Novel variant: first-time recipient + device posture shift + off-hours",
  "entry_vector": "Customer-authorized payment via instant rail",
  "prerequisites": ["P2P enabled", "Account age < 7 days", "New device not in trusted set"],
  "step_flow_phases": ["access/contact", "profile/channel manipulation", "payment setup", "execute", "post-event cashout/layering (simulated)"],
  "telemetry_contract": {
    "required_events": ["login_attempt", "device_posture_change", "payee_add", "payment_initiate", "risk_score_emit", "alert_or_hold_decision"],
    "required_features": ["device_id", "geo", "velocity_metrics", "payee_age", "account_age", "approval_chain"]
  },
  "expected_controls": ["step_up_auth", "new_payee_hold", "velocity_cap", "case_create"],
  "test_cases": {
    "red_team": ["Attempt 3 payments with escalating amounts within 10 minutes (simulated)"],
    "blue_team": ["Alert on new payee + off-hours + device change; hold first payment; create case within 2 minutes"]
  },
  "segment_applicability": {"consumer": true, "commercial": false},
  "mutation_lineage": {
    "seed_ids": ["F07-S01"],
    "operators": ["TIMING_OFF_HOURS", "DEVICE_POSTURE_SHIFT", "AMOUNT_ESCALATION"],
    "novelty_rationale": "Tests correlation across device + timing + new payee hold policy."
  }
}
```

---

## 6) Novel Scenario Generation (NASG)

### 6.1 Goals
- Generate **new, bank-specific** adversarial scenarios that:
  - are feasible in sandbox/digital twin,
  - are telemetry-complete (measurable),
  - stress specific control surfaces,
  - provide remediation-focused outputs.

### 6.2 Inputs
- Seed scenario catalog (versioned).
- Bank configuration snapshot:
  - enabled products/rails/channels,
  - limits and hold policies,
  - fraud engine features availability,
  - workflow settings (commercial approvals/SoD),
  - known blind spots (optional).
- Constraints:
  - RoE limits (max volumes, allowed rails, allowed windows).

### 6.3 Mutation Operators (Library)
**Must implement a modular operator framework**.

Required operator categories:
1. **Channel operators**: `WEB↔MOBILE↔CALL_CENTER↔BRANCH_ASSISTED`
2. **Rail operators**: `ACH↔WIRE↔INSTANT↔CARD↔CHECK/RDC`
3. **Timing operators**: `BURST`, `SLOW_BURN`, `OFF_HOURS`, `END_OF_MONTH`
4. **Actor operators**: `CONSUMER`, `SMB`, `TREASURY_MAKER`, `TREASURY_CHECKER`, `VENDOR_ADMIN`, `INSIDER_SIM`
5. **Workflow operators (Commercial)**: `ENTITLEMENT_CHANGE`, `APPROVAL_CHAIN_DEVIATION`, `TEMPLATE_EDIT`, `BATCH_SPLIT`
6. **Telemetry operators**: `DEVICE_POSTURE_SHIFT`, `GEO_VELOCITY`, `PAYEE_AGE`, `ACCOUNT_AGE`, `RETURN_CODE_SEQUENCE`
7. **Noise operators**: inject benign traffic to avoid “toy tests”
8. **Stress operators**: near-threshold tests (without disclosing thresholds)

### 6.4 Adversarial Search / Coverage-Gap Targeting
- Treat the bank’s detection/controls as a **black box** (from outcomes):
  - propose variant → run → observe detection/hold/case outcomes → score → iterate.
- Objective functions:
  - maximize uncovered areas (misses),
  - minimize false positive impact (via benign background),
  - maximize telemetry diversity and novelty.

### 6.5 Safety Gate for NASG (Mandatory)
- Reject any generation that:
  - includes real-world targeting instructions,
  - suggests bypass steps that are operational,
  - requires real PII or production access,
  - violates RoE constraints.
- Output must remain at **event-telemetry** level.

---

## 7) Simulation Execution

### 7.1 Simulators (Required)
- **Digital Banking Event Simulator**
  - login attempts, device enrollment, profile changes, payee add, transfer initiation
- **Card Stream Simulator**
  - authorization patterns, declines, merchant categories, disputes/chargebacks
- **ACH Simulator (USA-heavy)**
  - credits/debits, originator IDs, return codes, settlement windows (simulated)
- **Wire Simulator**
  - beneficiary lifecycle, corridor/routing metadata (simulated), recall events (simulated)
- **Instant Payments Simulator**
  - RTP/FedNow-style events, request-for-payment patterns, P2P alias binding
- **Check/RDC Simulator**
  - deposit events, duplicate presentment flags, image metadata anomalies (synthetic)
- **Commercial Treasury Workflow Simulator**
  - entitlements, maker-checker approvals, templates, batch creation/release

### 7.2 Orchestrator Requirements
- Campaign scheduling: single, batch, recurring regression runs.
- Deterministic replay with seeded randomness.
- Safety controls: max TPS, max value, max number of actions, automatic stop on anomalies.
- Kill switch with immediate termination.

### 7.3 Outcome Collection
- Collect:
  - fraud engine decisions (scores, rules fired, features used if available),
  - alerts and cases created,
  - step-up/hold/block events,
  - investigator actions and SLA timestamps,
  - SIEM/SOAR playbook triggers.

---

## 8) Integrations (Connector Layer)

### 8.1 Required Integrations (pluggable)
- **Fraud Engine Connector**: submit simulated events and fetch outcomes.
- **Case Management Connector**: create/read cases, add evidence, measure workflows.
- **SIEM/SOAR Connector**: ingest alerts, record playbook actions.
- **Data Lake Connector**: store run logs, metrics, and reports (sanitized).

### 8.2 Connector Standards
- Support REST + message bus patterns.
- Configured via secure secrets manager.
- Allowlist-based endpoint access.
- Full request/response logging (sanitized) for audit.

---

## 9) Reporting & Analytics

### 9.1 Core Reports
- **Coverage Matrix**
  - scenario family × rail × channel × segment × control mapping
  - % covered, missed, partial
- **Gap Analysis**
  - missing telemetry, weak rules, workflow bypasses, threshold brittleness
- **Remediation Backlog**
  - actionable items: new rule, new feature, workflow fix, policy change
- **Blue Team Readiness**
  - alert quality, case routing correctness, SLA adherence, false positive estimates
- **Scenario Lineage**
  - for generated scenarios: seeds + operators + novelty rationale + results

### 9.2 KPIs
- Time-to-detect, time-to-contain, time-to-case
- Coverage improvement over time
- False positive impact (via benign traffic runs)
- Repeatability score (replay consistency)
- Control effectiveness score per control category

---

## 10) Security, Privacy, and Compliance Requirements

### 10.1 Security
- SSO/OIDC (if bank supports) + MFA for admin roles
- RBAC with least privilege
- Secrets in vault (no plaintext)
- Signed container images, SBOM, vulnerability scanning (CI gate)
- Immutable audit logs, tamper-evident storage

### 10.2 Privacy/Data Minimization
- Synthetic data generation only
- Redaction layer for any logs/exports
- Export only aggregated metrics by default
- Configurable retention policies (bank-defined)

### 10.3 Auditability
- Every action logged: who/what/when/where
- Scenario versioning + lineage
- Evidence packages per campaign (sanitized)

---

## 11) Non-Functional Requirements (NFRs)

- **Reliability**: 99.5% availability in test environment (where applicable)
- **Performance**:
  - support burst simulations (configurable TPS) within RoE limits
  - outcome correlation within minutes (near-real-time)
- **Scalability**:
  - parallel campaigns by bank tenant (multi-tenant or isolated deployments)
- **Observability**:
  - metrics, tracing, structured logs
- **Maintainability**:
  - plugin framework for new simulators/operators/connectors
- **Portability**:
  - containerized deployment (Docker/Kubernetes)

---

## 12) Test Plan & Acceptance Criteria

### 12.1 Platform Tests
- RBAC enforcement tests
- RoE enforcement (windows/limits/kill switch)
- Audit log integrity tests
- Deterministic replay tests

### 12.2 Simulator Tests
- Event fidelity: produces expected telemetry fields
- Cross-rail correlation: events linkable by scenario run IDs
- Benign traffic generation validated (no excessive alerts)

### 12.3 NASG Tests
- Mutation operator unit tests
- Safety gate tests: blocks unsafe outputs
- Novelty scoring tests
- Black-box search converges on new variants without violating constraints

### 12.4 Acceptance Criteria (MVP)
- Import seed catalog and run ≥ 50 scenarios end-to-end in sandbox.
- Generate ≥ 200 novel variants (safe), execute ≥ 50, produce:
  - coverage matrix,
  - at least 10 validated control gaps,
  - remediation backlog items with traceability.
- Full audit trail and exportable evidence package for each campaign.

---

## 13) Suggested Tech Stack (Bank-friendly)

- Backend: Python + FastAPI (services), Celery/RQ (jobs) or event-driven with Kafka/NATS (if available)
- Storage: Postgres (metadata), object store (artifacts), Redis (queues/cache)
- Observability: OpenTelemetry + Prometheus/Grafana (optional)
- UI: React + TypeScript (optional MVP UI), or Streamlit for fast internal UI
- Packaging: Docker + Helm charts
- Security: Vault/Secrets Manager integration, OIDC, signed images

---

## 14) Suggested Repository Structure

```
fraud-forge-redteam/
  docs/
    requirements_RT.md
    roe_template.md
    safety_policy.md
  services/
    catalog_service/
    nasg_service/
    orchestrator/
    simulators/
      digital_banking/
      ach/
      wire/
      instant/
      cards/
      checks_rdc/
      commercial_treasury/
    connectors/
      fraud_engine/
      case_mgmt/
      siem_soar/
      data_lake/
    evaluation/
    reporting/
    policy_safety_gate/
  ui/
    dashboard/
  infra/
    docker/
    helm/
  tests/
    unit/
    integration/
    e2e/
  samples/
    seed_catalog_example.json
    simulation_pack_examples/
```

---

## 15) Deliverables

1. Working Red Team platform (MVP → v1) with:
   - catalog import,
   - NASG generation,
   - orchestrated runs,
   - integrations (at least fraud engine + case mgmt),
   - reports and evidence packages.
2. RoE templates + safety policy docs.
3. Operator UI or CLI for campaigns.
4. Automated test suite (unit + integration + e2e).
5. Deployment artifacts (Docker + Helm) and runbooks.

---

## 16) Notes for GH Copilot Usage

- Treat this as an SRS. Implement iteratively:
  1) schema + storage + audit logging
  2) orchestrator + one simulator (digital banking) + one rail (ACH)
  3) safety gate + NASG with 10 operators
  4) reporting + coverage matrix
  5) add remaining simulators/connectors

- Always maintain the “Hard Rules” section; do not implement prohibited features.
