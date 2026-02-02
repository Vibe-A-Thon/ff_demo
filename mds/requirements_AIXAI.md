# Fraud Forge — AI / XAI / Agentic AI Requirements (requirements_AIXAI.md)

## 0) Scope and intent
Fraud Forge is a **defensive security & fraud-resilience** simulation platform that:
- **Generates synthetic fraud scenarios** (Red Team) to stress-test controls.
- **Detects / responds / learns** (Blue Team) using rules + models.
- **Explains decisions** (Gold Team XAI) in human-readable, auditable form.
- **Governs releases** (White/Orange) with approvals and compliance readiness.

**Hard constraint (hackathon-safe):**
- No “how-to commit fraud” guidance, no real account data; only **synthetic, sandbox** scenarios and defensive learning.

---

## 1) High-level AI/XAI architecture requirements
### 1.1 Core runtime layers
1. **Agent Runtime & Orchestration**
   - Session orchestration: run → pause → resume → replay
   - Turn-based execution and deterministic replays (seeded)
   - Multi-agent messaging (pub/sub) + traceability

2. **Tooling Layer**
   - Transaction simulator (synthetic)
   - Scenario builder
   - Policy/rule retrieval (RAG/KG/CAG optional)
   - Model inference (risk scoring)
   - Validation harness (tests, counterexamples, stress tests)
   - Export tools (evidence packs, reports)

3. **Memory & Knowledge**
   - Per-run episodic memory (turns, decisions, evidence)
   - Long-term “learned artifacts” memory (patterns, rules, playbooks)
   - Knowledge graph: nodes = rules/patterns/evidence/compliance links

4. **XAI & Audit**
   - Structured explanation objects per decision
   - Evidence lineage graph + reproducible provenance
   - Audit log for approvals, deployments, diffs

5. **Observability & Evaluation**
   - Run traces, token/tool usage, latency
   - Automated quality checks: hallucination checks, consistency, regression

---

## 2) Agent system requirements
### 2.1 Agent model: “Teams → Agents → Sub-agents”
Fraud Forge must support:
- **Top-level Teams** (Red/Blue/Black/Green/Gold/White/Purple/Orange)
- Each team has **Primary Agents** and can spawn **Sub-agents** for tasks.
- A **Supervisor / Orchestrator** coordinates all teams, enforces policies, and manages session state.

### 2.2 Mandatory agentic capabilities (applies to all agents)
1. **Goal → Plan → Execute loop**
   - Explicit goal statement
   - Plan decomposition into steps
   - Tool calls for each step with logged inputs/outputs

2. **Tool use**
   - Standard tool registry + typed IO contracts
   - Sandboxed execution for any code/tooling
   - Tool retries, timeouts, and safe fallbacks

3. **Reflection + self-check**
   - “Self-RAG / self-reflection” step before finalizing an action/decision
   - Detect missing evidence, contradictions, low confidence

4. **Memory**
   - Short-term context buffer
   - Per-agent memory store (notes, hypotheses, learned heuristics)
   - Run-to-run learning (optional for hackathon; must be toggleable)

5. **Collaboration**
   - Message passing with structured payloads (task, evidence, recommendation)
   - Consensus / arbitration mode:
     - majority vote, weighted vote, or “council override”
   - Conflict detection and resolution

6. **Safety guardrails**
   - Safety policies per team (e.g., Red Team cannot export “actionable fraud instructions”)
   - “Safe Mode” that redacts sensitive operational details in UI exports
   - Human-in-the-loop approval for risky actions (deployments, rule promotions)

### 2.3 Required agent roles (minimum set)
#### Supervisor / Orchestrator (central)
- Creates run sessions, seeds, and scenario context
- Launches team agents, controls turn order, handles retries/rollbacks
- Emits the battle timeline + trace graph
- Enforces RBAC + policy checks

#### Red Team (Challengers)
- Fraud Scenario Synthesizer (generates synthetic fraud patterns + sequences)
- Attack Planner (chooses channel/MCC/device/profile behaviors)
- Payload Executor (runs against simulator only)
- Adversarial Mutator (evolves attacks to bypass current rules/models)

#### Blue Team (Defenders)
- Detection Analyst (rules + model scoring)
- Response Orchestrator (holds/step-up-auth/alerts)
- Feature/Signal Builder (engineers features from events)
- Post-Incident Learner (turns incidents into new rules/patterns)

#### Gold Team (Narrators / XAI)
- Explanation Composer (plain + technical)
- Evidence Graph Builder (why/what triggered, lineage)
- Counterfactual Generator (“what would change the outcome?”)
- Similar-Case Retriever (finds prior similar synthetic cases)

#### Green Team (Builders)
- RuleSpec Compiler (RuleSpec → executable rules)
- Test Generator (unit tests + scenario tests)
- Packaging Agent (builds “RSB” packages / versioned artifacts)

#### White Team (Council / Compliance)
- Policy Checker (PCI-like mapping, data minimization)
- Fairness/Reasonableness Checker (bias & consistency)
- Audit Pack Reviewer (completeness checks)

#### Orange Team (Gatekeepers)
- Code Reviewer (static checks)
- Release Approver (sign-off workflow)
- Runtime SRE/QA (health, performance, regression)

#### Black Team (Stressors)
- Chaos Tester (latency/outage injection)
- Robustness Validator (false positive/negative tradeoffs, edge cases)

#### Purple Team (Strategists)
- Threat Modeler (taxonomy alignment)
- Strategy Planner (roadmap of defenses, prioritization)

---

## 3) XAI requirements (must be product-grade)
### 3.1 Explanation object schema (mandatory)
Every decision (alert/block/step-up) must generate an **Explanation Bundle**:
- Decision: label, risk score, confidence, action taken
- Top reasons:
  - triggered rules (ids + thresholds)
  - top features (weights/importance)
  - anomaly factors (distance, rarity)
- Evidence links:
  - events, transactions, device signals, customer profile facts (synthetic)
- Counterfactuals:
  - minimal changes that flip the decision
- Model card / rule card references:
  - version, training data summary (synthetic), constraints
- Compliance tags:
  - e.g., “Data Minimization”, “KYC step-up”
- Human readable summary:
  - 2–4 sentence explanation in plain English
- Technical trace:
  - tool calls + intermediate reasoning artifacts (for auditors)

### 3.2 Evidence graph requirements
- Build a graph connecting: **Case → Decision → Rule/Model → Evidence nodes → Policy nodes**
- Must support:
  - Expand/collapse evidence
  - “Why this rule fired” drill-down
  - Compare two runs (before/after rule changes)
  - Export as “Evidence Pack” (json + pdf-ready markdown)

### 3.3 XAI UI modes
- **Plain mode** (bank associate)
- **Technical mode** (engineers)
- **Audit mode** (compliance + approvals)
- Toggle must be available from any case detail screen.

---

## 4) Knowledge augmentation requirements (for agent + XAI)
Even if full RAG/KG/CAG is implemented separately, AI/XAI must integrate with a knowledge layer for:
- Fraud taxonomy lookup (type, sub-type, signals)
- Playbooks (recommended responses)
- Rule library + version history
- Prior cases (synthetic) for similarity and explanations
- Policy mapping (compliance tags and requirements)

---

## 5) Data & simulation requirements (hackathon-safe)
- Synthetic customer profiles, devices, and transactions
- Multi-channel simulation: card-present, card-not-present, UPI/wallet, netbanking (as needed)
- Deterministic seeding for repeatable demos
- “Attack families” and “defense baselines” loadable as bundles

---

## 6) Non-functional requirements (NFR)
- **Latency**: interactive demo < 1–2s per turn for UI rendering; background tasks async
- **Reproducibility**: every run has a seed + artifact versions
- **Security**: RBAC (associate/admin), audit logs immutable (append-only)
- **Explainability quality**: minimum completeness checks (no missing evidence)
- **Observability**: trace IDs across agents/tools; exportable telemetry

---

## 7) “Hackathon-winning” differentiators (high ROI)
1. **One-click demo modes**
   - “Bank Associate: Stop the Fraud”
   - “Architect: Improve Detection”
   - “Auditor: Verify Compliance”
2. **Battle timeline + replay**
   - step-through turns; jump-to-evidence; compare runs
3. **Before/After diff**
   - rule/model change → immediate KPI delta + explanation delta
4. **Evidence Pack export**
   - shareable artifact for judges (single click)
5. **Agent “thinking visualizer”**
   - stage cards: recon → ideate → execute → reflect
6. **Auto-tuning assistant**
   - suggests threshold changes with impact estimate (safe, synthetic)
7. **Leaderboard**
   - defense score vs attack novelty (synthetic scoreboard)

---

## 8) Recommended libraries / resources (links)
> URLs are provided in a code block for copy/paste.

```text
Agent orchestration:
- LangGraph: https://github.com/langchain-ai/langgraph
- AutoGen: https://github.com/microsoft/autogen
- CrewAI: https://github.com/crewAIInc/crewAI

RAG / indexing:
- LlamaIndex: https://github.com/run-llama/llama_index
- LangChain: https://github.com/langchain-ai/langchain
- FAISS: https://github.com/facebookresearch/faiss
- Chroma: https://github.com/chroma-core/chroma
- Qdrant: https://github.com/qdrant/qdrant

Knowledge graph:
- Neo4j: https://neo4j.com/developer/
- NetworkX: https://networkx.org/

Explainability:
- SHAP: https://github.com/shap/shap
- Alibi Explain: https://github.com/SeldonIO/alibi
- LIME: https://github.com/marcotcr/lime

Observability / eval:
- OpenTelemetry: https://opentelemetry.io/
- Langfuse: https://github.com/langfuse/langfuse
- Arize Phoenix: https://github.com/Arize-ai/phoenix
```
