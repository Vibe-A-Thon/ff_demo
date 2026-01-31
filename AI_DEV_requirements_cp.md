# Fraud Forge — AI_DEV_requirements.md
**Scope:** AI + backend requirements only (Agents, Agentic AI, Multi‑RAG/KAG/CAG, XAI, orchestration, evaluation, governance).  
**Source set:** Extracted from `ff_md.zip` (all included `.md/.json/.xlsx`) and consolidated into a single Copilot‑ready spec.  
**Generated:** 2026-01-31 19:00:50

> **Safety boundary (non‑negotiable):** Fraud Forge is a **defensive simulation and training** platform. All “attacks” are **synthetic, sandboxed, non‑operational**. No real customer PII. No actionable wrongdoing instructions. Exported artifacts must be watermarked **“Simulation/Training Only.”**

---

## 1) What judges must see (AI + backend angle)
1. **AI vs AI battle**: Red generates a synthetic fraud campaign → Blue detects/responds → Gold explains → Metrics update live.
2. **Learning loop**: A miss becomes a **patch** (Purple→Green→Black→Orange→White) → re‑run shows **Time‑to‑Immunity** improving.
3. **Auditability**: Every agent action has **trace_id**, evidence links, and approval trail.
4. **Evidence Pack**: One‑click export: timeline, decisions, XAI, rule diffs, approvals, KPI deltas.

---

## 2) AI/back‑end architecture requirements (services & boundaries)
### 2.1 Core services (minimum viable for hackathon)
- **API Gateway (FastAPI)**: REST + WebSocket streaming.
- **Run Session Service**: run lifecycle (start/pause/resume/stop/replay), deterministic seeding.
- **Agent Runtime / Orchestrator**: supervises 8 teams, turn engine, tool routing, budgets/timeouts.
- **Synthetic Fraud Simulator**: produces events/transactions with ground truth labels.
- **Detection Service**: rule engine + simple model scoring (baseline) + hybrid retrieval.
- **XAI/Evidence Service**: ExplanationBundle + evidence graph + counterfactuals + similarity.
- **Governance Service**: RBAC, SoD, approvals workflow, SAFE_TO_PROCEED gates.
- **RSB/Rule Lifecycle Service**: RuleSpec → code/tests → package → stage/deploy → rollback.
- **Metrics & Observability Service**: KPIs + traces + export snapshots.

### 2.2 Data stores (hackathon‑friendly defaults)
- **PostgreSQL**: users/roles, runs/turns, approvals, audit log metadata, rule registry metadata.
- **File store (local)**: artifacts (`/data/artifacts`) — RSB zips, evidence packs, diff snapshots.
- **Vector store (Chroma)**: embeddings for cases/rules/policies/playbooks/similar runs.
- **BM25 index**: keyword search for IDs, rule names, taxonomy labels.
- **Graph store**:
  - **P0**: in‑memory NetworkX + JSON export
  - **P1**: Neo4j (GraphRAG/KAG)

### 2.3 Event streaming (required)
- WebSocket channel per run: `ws/runs/{run_id}`
- Stream types:
  - `turn_started`, `turn_completed`
  - `reasoning_chunk` (team/agent)
  - `kpi_update`
  - `approval_status`
  - `artifact_ready` (evidence pack, diff, report)

---

## 3) Multi‑Agent System requirements (8 teams + sub‑agents)
### 3.1 Team structure (source: FF_Team_Agents.xlsx)
### Black Team — *The Stressors *
- Purpose: Intentionally breaks systems, stress-tests defenses, validates robustness and failure handling
- Agents (7): 1. Black Orchestrator (Test Manager), 2. Adversarial Replay Agent, 3. Edge-Case Generator, 4. Chaos Injection Agent, 5. Load / Burst Simulation Agent, 6. Regression & Coverage Auditor …
### Blue Team — *The Defenders*
- Purpose: Real-time fraud detection, prevention, and response across all banking channels
- Agents (9): 1. Blue Orchestrator (Defense Manager), 2. Rule Evaluation Agent, 3. Behavioral Baseline Agent, 4. Graph & Link Analysis Agent, 5. Device & Session Risk Agent, 6. Model Scoring Agent …
### Gold Team — *The Narrators*
- Purpose: Ensures all AI decisions are interpretable, auditable, and human-understandable
- Agents (6): 1. Gold Orchestrator (Explanation Manager), 2. Decision Explanation Agent, 3. Evidence Trace Agent, 4. Audience Adapter Agent, 5. Explanation QA Agent, 6. Case Narrative Agent
### Green Team — *The Builders*
- Purpose: Converts fraud rules and strategies into production-grade Python code
- Agents (7): 1. Green Orchestrator (Build Manager), 2. Rule-to-Code Translator, 3. Pipeline & Integration Agent, 4. Feature Engineering / Signal Agent, 5. Observability & Audit Hooks Agent, 6. Performance & Optimization Agent …
### Orange Team — *The Gatekeepers*
- Purpose: Performs code review, security validation, and final release approval
- Agents (6): 1. Orange Orchestrator (Release Manager), 2. Code Quality Reviewer, 3. Security Review Agent, 4. Test Evidence Verifier, 5. Release Risk Assessor, 6. Rollback & Kill-Switch Verifier
### Purple Team — *The Strategists*
- Purpose: Designs fraud rules, threat models, policies, and future-proof detection strategies
- Agents (7): 1. Purple Orchestrator (Strategy Manager), 2. Root Cause Analyst, 3. Rule Authoring Agent, 4. Threat Forecasting Agent, 5. Policy & Constraint Agent, 6. Knowledge Graph Curator …
### Red Team — *The Challengers*
- Purpose: Simulates real-world fraudsters, generates and executes evolving fraud attacks (external threat model)
- Agents (8): 1. Red Orchestrator (Campaign Manager), 2. Fraud Scenario Generator, 3. Transaction Fraud Executor, 4. Loan/Deposit Abuse Agent, 5. Identity Spoof & KYC Evasion Agent, 6. Bot Swarm & Coordination Agent …
### White Team — *The Council*
- Purpose: Ensures legality, regulatory compliance, fairness, ethics, and audit readiness
- Agents (6): 1. White Orchestrator (Governance Manager), 2. Regulatory Mapping Agent, 3. Compliance Validation Agent, 4. Fairness & Bias Monitor, 5. Audit Trail Integrity Agent, 6. Approval Authority Agent


> **Total agent roster:** 56 agents across 8 teams (including orchestrators and specialists).

### 3.2 Mandatory agent contract (all agents)
Every agent (and sub‑agent) must implement:
- **Identity**: `agent_id`, `agent_name`, `team_id`, `role`, `version`
- **Loop**: `plan → act → reflect` (all steps logged)
- **Tool usage**: only via **Tool Registry** (typed schemas, allowlists)
- **Safety**: output filtering, tool allowlists, redaction rules
- **Budgets**: token/step/time budgets per turn; hard timeout in demo mode
- **Determinism**: replay‑safe (seeded randomness + version pins)
- **Artifacts**: outputs must be typed and persisted (JSON + optional files)
- **Observability**: attach `trace_id`, `span_id`, `run_id`, `turn_id`

### 3.3 Agent communication protocol (PAMP)
Implement **PAMP (Protocol for Agent Message Passing)**:
- Envelope fields: `msg_id`, `run_id`, `turn_id`, `from_agent`, `to_agent`, `intent`, `payload_schema`, `payload`, `confidence`, `requires_approval`
- Message types:
  - `TASK_ASSIGN`, `FINDING`, `PROPOSAL`, `COUNTERARG`, `APPROVAL_REQUEST`, `DECISION`, `EVIDENCE_LINK`
- Persistence: every message stored with provenance for replay/audit.

### 3.4 Sub‑agent spawning (must support)
- Parent agents can spawn **sub‑agents** with:
  - scoped goal + acceptance criteria
  - strict tool allowlist
  - deadline + timeout
  - output schema requirement
- Enforce quotas (hackathon stability):
  - max sub‑agents per turn
  - max wall‑clock time per agent
  - backpressure when system load is high

### 3.5 Tool registry (must support)
- Central registry with:
  - tool name, description, schema, safety level, owners, rate limits
  - audit logging of every tool call (inputs redacted, outputs hashed)
- Required tools (minimum):
  - `simulate_transactions`
  - `mutate_scenario` (synthetic)
  - `score_risk_rules`
  - `score_risk_model`
  - `retrieve_context` (Multi‑RAG router)
  - `build_evidence_graph`
  - `generate_explanations`
  - `run_tests`
  - `package_rsb`
  - `request_approval`
  - `export_evidence_pack`

---

## 4) AI Knowledge layer: Multi‑RAG + KAG + CAG requirements
### 4.1 Supported augmentation types (must implement interface)
- **Naive RAG**: retrieve‑and‑read from vector store.
- **Advanced RAG**: query rewrite/expansion, rerank, filtering.
- **Modular RAG**: plug‑replace modules: chunker, retriever, reranker, summarizer.
- **Agentic RAG**: planner agent decomposes query and uses multiple tools iteratively.
- **Self‑RAG**: self‑evaluate retrieved context & answer; revise if weak.
- **Corrective RAG (CRAG)**: retrieval quality gate; fallback to alternate retrieval if poor.
- **Hybrid RAG**: BM25 + vectors fused (RRF or weighted scoring).
- **Multimodal RAG**: images/pdfs/screenshots/diagrams (optional for P1).
- **KAG**: knowledge graph query + multi‑hop reasoning (GraphRAG).
- **CAG**: cache‑augmented generation (preloaded KV or precomputed summaries).

### 4.2 Retrieval targets (Fraud Forge‑specific)
The retrieval layer must index and retrieve across:
- Fraud taxonomy (0 types) + Fraud_Groups
- Rules (RuleSpec + code docs) + RSB compliance docs
- Prior runs: decisions, outcomes, “what worked” patches
- Playbooks: response actions and escalation guidelines (defensive)
- Policies/controls: compliance mappings & SoD rules
- Evidence packs & investigation notes (synthetic)

### 4.3 Unified Multi‑RAG router (required)
Implement a `RetrievalRouter` that selects strategy based on query intent:
- **lookup** (IDs, rule names) → BM25
- **semantic** (behavior, patterns) → vector
- **relationship** (rings/mule nets) → graph/KAG
- **static** (manuals/policies) → CAG cache
- **multimodal** → OCR/vision embedding (optional)

Router outputs **RetrievalBundle**:
- `context_chunks[]` (source, score, hash, citations)
- `graph_facts[]` (nodes/edges, provenance)
- `cache_hits[]`
- `quality_metrics` (coverage, redundancy, contradiction flags)

### 4.4 Indexing & ingestion (required)
- Chunking policies per corpus:
  - rules/specs: section‑aware chunking
  - evidence packs: event‑anchored chunking
  - taxonomy: node‑per‑type chunking
- Embedding pipeline with versioning:
  - `embedding_model_id`, `embedding_dim`, `created_at`, `corpus_version`
- Reranking (P1):
  - cross‑encoder or LLM‑based rerank (bounded) OR simple heuristic rerank

### 4.5 Retrieval quality gates (Self‑RAG/CRAG)
- Score retrieved context quality:
  - top‑k similarity, novelty, source diversity, contradiction
- If quality < threshold:
  - expand query, switch retriever, add BM25, or graph fallback
- Persist decisions for later analysis (“why retrieval changed”).

---

## 5) Explainability (XAI) requirements — Gold Team as a first‑class system
### 5.1 ExplanationBundle schema (required for every detection)
- `decision`: label(s), risk score, confidence
- `why`: triggered rules + thresholds; key signals/features
- `evidence`: links to events, rule IDs, retrieval citations, hashes
- `counterfactuals`: minimal changes that flip the decision (safe/synthetic)
- `similar_cases`: retrieved cases with relevance
- `governance`: version pins (ruleset/model/taxonomy/RSB), approvals involved
- `compliance_tags`: policy/control mapping, SoD flags, data minimization flags

### 5.2 Evidence graph requirements
- Node types: Case, Event, Rule, Feature, Pattern, Policy, Approval, AgentAction
- Edge types: TRIGGERED_BY, SUPPORTED_BY, MAPS_TO, DERIVED_FROM, APPROVED_BY, SIMILAR_TO
- Provenance rules:
  - every node/edge must include source + hash + created_by agent

### 5.3 XAI agents (required)
Minimum Gold team sub‑agents:
- **Plain‑English Narrator**: business explanation & next steps
- **Technical Explainer**: rules/features/thresholds
- **Audit Explainer**: controls mapping + version pins + SoD notes
- **Counterfactual Generator**: bounded rule‑based counterfactuals
- **Evidence Pack Curator**: assembles judge‑ready artifacts

---

## 6) Learning loop & “Time‑to‑Immunity” (hackathon differentiator)
### 6.1 Immunization engine (required)
When a Red scenario succeeds or Blue misses:
1. Capture failure signature (features + context + evidence)
2. Purple proposes mitigation (RuleSpecProposal + expected KPI impact)
3. Green builds patch (code/tests/RSB)
4. Black stress‑tests & generates counterexamples
5. Orange reviews (secure, style, performance)
6. White validates compliance & fairness constraints
7. Deploy new ruleset version; re‑run same seed; show KPI delta

### 6.2 Metrics (must compute per run + global)
- **Time‑to‑Immunity**: turns or minutes from first success → stable block rate
- Defense success rate; detection latency p95/p99
- Money at risk vs saved (synthetic)
- Attack novelty score vs defense robustness score
- Explainability completeness score (bundle coverage, missing evidence)

---

## 7) Governance & security requirements (AI‑specific)
- RBAC/SoD enforced server‑side for:
  - tool usage (high‑risk tools locked)
  - deployments/rollbacks
  - evidence export
- Append‑only audit log:
  - `who/what/when/why` + hashes
- HITL and HOTL modes:
  - HOTL must still emit approval requests for gates; can auto‑approve only under policy
- “Kill switch”:
  - stop run; lock deploy; rollback ruleset pointer

---

## 8) AI‑backend APIs (minimum set)
- Run control: `/runs/start|pause|resume|stop|replay`
- Streams: `/ws/runs/{run_id}`
- Agent ops:
  - `/agents/registry`, `/agents/{id}/status`, `/agents/{id}/messages`
- Retrieval:
  - `/retrieval/query` (returns RetrievalBundle)
  - `/retrieval/ingest` (admin)
- XAI:
  - `/xai/explain?case_id=`
  - `/xai/evidence-graph?case_id=`
  - `/xai/export-evidence-pack?run_id=`
- Rules lifecycle:
  - `/rulespec/validate|propose|build|test|approve|deploy|rollback`
  - `/rsb/upload|validate|run-tests|stage|deploy`

---

## 9) Hackathon‑winning AI extras (high ROI)
1. **Demo‑mode deterministic runs** with precomputed traces fallback (offline safe).
2. **One‑click “WOW Replay”**: best run loads instantly; shows learning delta.
3. **Persona toggles** for narration tone: Associate vs Engineer vs Auditor.
4. **Retrieval transparency**: show which RAG mode was used and why (Self‑RAG score).
5. **Explainability completeness score**: green/yellow/red badge per case.
6. **Attack vs Defense leaderboard**: novelty vs robustness (synthetic).
7. **Cross‑bank “Share Wisdom, Not Data”** demo: export/import sanitized defense patterns only.

---

## 10) Implementation resources (copy/paste links)
```text
Backend + Orchestration
- FastAPI: https://fastapi.tiangolo.com/
- Pydantic: https://docs.pydantic.dev/
- OpenTelemetry: https://opentelemetry.io/
- LangGraph: https://github.com/langchain-ai/langgraph
- AutoGen: https://github.com/microsoft/autogen
- CrewAI: https://github.com/crewAIInc/crewAI

Retrieval (RAG)
- Chroma: https://github.com/chroma-core/chroma
- FAISS: https://github.com/facebookresearch/faiss
- rank_bm25: https://github.com/dorianbrown/rank_bm25
- Neo4j: https://neo4j.com/developer/
- NetworkX: https://networkx.org/

Explainability
- SHAP: https://github.com/shap/shap
- Alibi: https://github.com/SeldonIO/alibi
- LIME: https://github.com/marcotcr/lime

Eval/Tracing (optional)
- Langfuse: https://github.com/langfuse/langfuse
- Phoenix: https://github.com/Arize-ai/phoenix
```
---

## Appendix A — Complete agent roster (from FF_Team_Agents.xlsx)
| Team | Market Name | No | Agent | Agentic Capabilities (short) |
| --- | --- | --- | --- | --- |
| Black Team | The Stressors | 1 | Black Orchestrator (Test Manager) | Planning, delegation, memory |
| Black Team | The Stressors | 2 | Adversarial Replay Agent | Persistent memory replay |
| Black Team | The Stressors | 3 | Edge-Case Generator | Creativity + context control |
| Black Team | The Stressors | 4 | Chaos Injection Agent | Tool use, fault injection loops |
| Black Team | The Stressors | 5 | Load / Burst Simulation Agent | Planning, evaluation |
| Black Team | The Stressors | 6 | Regression & Coverage Auditor | Deterministic verification |
| Black Team | The Stressors | 7 | Defect Triage & Reporting Agent | Extreme context packaging |
| Blue Team | The Defenders | 1 | Blue Orchestrator (Defense Manager) | Planning, delegation, state mgmt |
| Blue Team | The Defenders | 2 | Rule Evaluation Agent | Deterministic reasoning |
| Blue Team | The Defenders | 3 | Behavioral Baseline Agent | Persistent memory, anomaly detection |
| Blue Team | The Defenders | 4 | Graph & Link Analysis Agent | Relational reasoning, memory |
| Blue Team | The Defenders | 5 | Device & Session Risk Agent | Context engineering, tool use |
| Blue Team | The Defenders | 6 | Model Scoring Agent | Tool use, evaluation |
| Blue Team | The Defenders | 7 | Decision & Action Agent | Policy-aware decisioning |
| Blue Team | The Defenders | 8 | Incident Packaging (Escalation) Agent | Extreme context packaging |
| Blue Team | The Defenders | 9 | Post-Decision Monitor Agent | Memory, feedback loop |
| Gold Team | The Narrators | 1 | Gold Orchestrator (Explanation Manager) | Planning, delegation, memory |
| Gold Team | The Narrators | 2 | Decision Explanation Agent | Natural language synthesis, context templates |
| Gold Team | The Narrators | 3 | Evidence Trace Agent | Persistent memory, provenance |
| Gold Team | The Narrators | 4 | Audience Adapter Agent | Context engineering |
| Gold Team | The Narrators | 5 | Explanation QA Agent | Self-check, completeness validation |
| Gold Team | The Narrators | 6 | Case Narrative Agent | Long-context summarization |
| Green Team | The Builders | 1 | Green Orchestrator (Build Manager) | Planning, delegation, state tracking |
| Green Team | The Builders | 2 | Rule-to-Code Translator | Code synthesis, context strictness |
| Green Team | The Builders | 3 | Pipeline & Integration Agent | Tool use, system composition |
| Green Team | The Builders | 4 | Feature Engineering / Signal Agent | Tool use, iterative loops |
| Green Team | The Builders | 5 | Observability & Audit Hooks Agent | Context engineering, memory |
| Green Team | The Builders | 6 | Performance & Optimization Agent | Self-check, profiling |
| Green Team | The Builders | 7 | Config & Policy Wiring Agent | Deterministic reasoning |
| Orange Team | The Gatekeepers | 1 | Orange Orchestrator (Release Manager) | Planning, delegation, policy enforcement |
| Orange Team | The Gatekeepers | 2 | Code Quality Reviewer | Static reasoning, context control |
| Orange Team | The Gatekeepers | 3 | Security Review Agent | Threat modeling, tool use |
| Orange Team | The Gatekeepers | 4 | Test Evidence Verifier | Evidence-based validation |
| Orange Team | The Gatekeepers | 5 | Release Risk Assessor | Multi-objective reasoning |
| Orange Team | The Gatekeepers | 6 | Rollback & Kill-Switch Verifier | Contingency planning |
| Purple Team | The Strategists | 1 | Purple Orchestrator (Strategy Manager) | Planning, delegation, memory |
| Purple Team | The Strategists | 2 | Root Cause Analyst | Causal reasoning, evidence synthesis |
| Purple Team | The Strategists | 3 | Rule Authoring Agent | Context engineering, structured writing |
| Purple Team | The Strategists | 4 | Threat Forecasting Agent | Long-horizon planning |
| Purple Team | The Strategists | 5 | Policy & Constraint Agent | Governance-aware reasoning |
| Purple Team | The Strategists | 6 | Knowledge Graph Curator | Persistent memory |
| Purple Team | The Strategists | 7 | Requirements Packager | Extreme context engineering |
| Red Team | The Challengers | 1 | Red Orchestrator (Campaign Manager) | Explicit planning, hierarchical delegation, persistent memory |
| Red Team | The Challengers | 2 | Fraud Scenario Generator | Creativity + planning + mutation |
| Red Team | The Challengers | 3 | Transaction Fraud Executor | Tool use, iterative execution loops |
| Red Team | The Challengers | 4 | Loan/Deposit Abuse Agent | Goal-driven simulation |
| Red Team | The Challengers | 5 | Identity Spoof & KYC Evasion Agent | Persona memory, context engineering |
| Red Team | The Challengers | 6 | Bot Swarm & Coordination Agent | Multi-agent coordination |
| Red Team | The Challengers | 7 | Recon & Weak-Signal Finder | Research + memory |
| Red Team | The Challengers | 8 | Adaptive Learning Agent | Feedback learning, episodic memory |
| White Team | The Council | 1 | White Orchestrator (Governance Manager) | Planning, delegation, policy enforcement |
| White Team | The Council | 2 | Regulatory Mapping Agent | Retrieval + knowledge memory |
| White Team | The Council | 3 | Compliance Validation Agent | Deterministic checking |
| White Team | The Council | 4 | Fairness & Bias Monitor | Statistical reasoning, memory |
| White Team | The Council | 5 | Audit Trail Integrity Agent | Persistent memory, integrity checks |
| White Team | The Council | 6 | Approval Authority Agent | Governance decisioning |
