# Fraud Forge — LLM‑Agnostic Implementation Plan
**Goal:** Implement LLM‑agnostic capability for Fraud Forge agents with minimal churn: provider adapters, routing, schema guards, tool normalization, eval harness, and audit/evidence integration.  
**Generated:** 2026-02-01 22:08:08

---

## Phase 0 — Freeze contracts (do this first)
### 0.1 Canonical message format + output schemas
- Standardize internal message objects and tool message representation.
- Define Pydantic schemas: `Plan`, `ToolCallList`, `Finding`, `Decision`, `ExplanationBundle`, `RuleSpecProposal`, `LLMFailure`.

**Exit criteria:** Agents can import schemas without any provider SDK installed.

### 0.2 Canonical tool call spec + registry
- Create canonical tool call JSON format.
- Create `tool_registry.yaml` with JSON schema per tool.
- Add runtime validator for tool arguments.

**Exit criteria:** A tool call fails fast with a readable validation error.

---

## Phase 1 — Provider Abstraction Layer (PAL) + 2 adapters
### 1.1 Implement PAL
Create internal interface:
- `generate()` + `stream_generate()`
- unified `LLMResult` and error taxonomy
- token usage accounting

### 1.2 Implement adapters
For hackathon speed implement **two**:
- Primary cloud provider (OpenAI/OpenAI‑compatible)
- Secondary fallback (Local vLLM/Ollama or Anthropic)

Include:
- timeouts and cancellation
- retries with exponential backoff
- rate‑limit detection and cooldown

**Exit criteria:** Switch provider via config; the response object shape stays the same.

---

## Phase 2 — Model Registry + Router + Fallback Chains
### 2.1 Implement model registry
- Create `model_registry.yaml` loader and validator.
- Support per‑model capability flags and version pins.

### 2.2 Implement routing policy
- Create `routing_policy.yaml` mapping:
  - team/agent → default model
  - intent → required capabilities
  - fallback chains

### 2.3 Implement router
- Select model + attach fallback list.
- Enforce constraints (context window, tool support, JSON mode).

**Exit criteria:** Red/Blue/Gold teams can run on different models in one run.

---

## Phase 3 — Tool Call Normalization
### 3.1 Normalize inbound tool calls
- Parse provider tool call outputs → canonical tool calls.
- Validate tool args using the registry.

### 3.2 Normalize outbound tool schemas
- Convert canonical schemas to provider tool definitions.
- Keep tool naming stable across providers.

**Exit criteria:** Same tool set works identically on both providers.

---

## Phase 4 — Schema Guard + Repair + Safe Failure
### 4.1 Schema validation middleware
- Validate every model output against expected schema.
- Reject non‑JSON when JSON is required.

### 4.2 Repair and fallback strategy
1) repair with strict JSON instructions (same model)  
2) repair using fallback model  
3) emit `LLMFailure` artifact and stop that step gracefully (no crash)

### 4.3 Integrate into agent runtime
All LLM calls must go through:
`router → provider → schema_guard → tool_normalizer`.

**Exit criteria:** Demo flows show high schema validity; failures don’t break the run.

---

## Phase 5 — Audit + Observability + Evidence Pack
### 5.1 Telemetry
Track per model/team:
- schema‑valid rate
- fallback count
- repair count
- latency p95

### 5.2 Audit events
Append‑only events:
- `MODEL_SELECTED`, `FALLBACK_USED`, `SCHEMA_REPAIR`, `MODEL_ERROR`

### 5.3 Evidence pack
Include:
- model pins per step
- fallback/repair events
- tool call trace IDs and redacted payload hashes

**Exit criteria:** Evidence pack shows a readable “Model Reliability Timeline”.

---

## Phase 6 — Eval Harness (safe switching)
### 6.1 Build eval suite
- tool call accuracy tests
- schema validity tests
- retrieval + citation sanity checks
- known‑facts hallucination checks (synthetic corpora)

### 6.2 Regression gates
- threshold checks; fail pipeline if regression exceeds limits

### 6.3 Judge‑friendly report
Generate:
- `eval_report.md` comparing 2 models

**Exit criteria:** One command produces a compare report and pass/fail status.

---

## Phase 7 — Hackathon demo packaging (make it visible)
### 7.1 UI: “LLM Provider” toggle (demo mode)
- Run setup screen: choose provider/model for each team.
- Show model badges in the battle arena timeline.

### 7.2 Demo: forced failure → fallback
- Simulate 429/timeout on primary → fallback continues run.
- Show timeline event: “Fallback activated”.

### 7.3 Reliability card
- Display schema validity %, fallback count, avg latency per team.

**Exit criteria:** Judges can see the feature without reading code.

---

## Minimal scope for hackathon (recommended)
- Support **2 providers** for the demo (primary + fallback).
- Implement schema guard + fallback (most visible reliability gain).
- Add UI toggle + timeline badges (makes it “wow”).

---

## Will this make Fraud Forge a “100% winner”?
It **materially increases win probability** because it:
- reduces demo failure risk
- signals enterprise readiness (bank portability + vendor independence)
- adds a strong architecture differentiator

But no feature guarantees 100% victory—wins depend on judging rubric and execution quality.  
**Best strategy:** implement LLM‑agnostic + show it live in the war room (toggle + fallback + reliability stats).
