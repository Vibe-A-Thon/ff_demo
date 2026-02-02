# Fraud Forge — LLM‑Agnostic Capability Requirements
**Goal:** Make Fraud Forge’s agents and AI backend able to switch between different LLM providers/models (cloud or on‑prem) **without code changes**, using configuration + adapters, while preserving tool calls, structured outputs, governance, and replay determinism.  
**Generated:** 2026-02-01 22:08:08

> **Why this matters in Fraud Forge:** Fraud Forge is a multi‑agent, tool‑using system with RAG/KAG/CAG + XAI and strong auditability needs. Vendor‑locking (one LLM) makes the demo fragile (quota, outage, policy changes) and blocks bank adoption. LLM‑agnostic design reduces demo risk and increases enterprise credibility.

---

## 1) Must‑Have Product Outcomes
1. **Provider switch by config**: Change `model_registry.yaml` / env var and restart → agents run with a new LLM.
2. **Per‑team/per‑agent routing**: Red/Blue/Gold/Purple/Green/… can use different models for speed/cost/reliability.
3. **Automatic fallback**: If primary model fails (timeout/rate limit/schema invalid), router falls back to secondary without breaking the run.
4. **Tool calling compatibility**: Tool calls behave identically across vendors (normalized internal format).
5. **Structured output stability**: Agent outputs remain valid JSON schemas even after switching providers.
6. **Replay stability**: Same seed + same model version pins → same run can be replayed and audited.
7. **Evidence/audit continuity**: Model switch events, failures, and repairs are logged in audit trail and shown in evidence pack.

---

## 2) High‑Level Architecture Requirements
### 2.1 Provider Abstraction Layer (PAL)
Implement a single internal interface the agents use:
- `generate(messages, tools, response_schema, constraints) -> LLMResult`
- `stream_generate(...) -> iterator[LLMChunk]`
- `embed(texts) -> vectors` (separate service/interface)
- `moderate(text) -> flags` (optional; depends on bank policy)

**Rule:** *No agent or tool calls vendor SDKs directly.* Agents only use PAL.

### 2.2 Adapters (LLM drivers)
Provide adapters implementing PAL for:
- **OpenAI** (and OpenAI‑compatible)
- **Azure OpenAI**
- **Anthropic**
- **Local** (vLLM/Ollama or bank‑hosted endpoint)

Each adapter must support:
- timeouts, retries, rate‑limit handling
- token accounting and request IDs
- streaming normalization
- tool call normalization (see §4)

### 2.3 Model Registry + Capability Matrix
A YAML/JSON registry describing available models and their capabilities:
- `provider`, `model_name`, `version_pin`
- `context_window`, `supports_tools`, `supports_json_mode`, `supports_streaming`
- `latency_class`, `cost_class`
- **Reliability score** (from internal eval suite)
- **Safety level** (bank policy classification)
- per‑model constraints: max tool calls, max output tokens, etc.

### 2.4 Router / Policy Engine
A deterministic router that selects model per request based on:
- team/agent role (Red vs Blue vs Gold)
- intent type (retrieval planning, narrative, code gen, verification)
- required capabilities (tools/JSON/long context)
- runtime health (errors, p95 latency, quota)
- budget policy (cost caps)

Router outputs: `SelectedModel + FallbackChain + Constraints`.

---

## 3) Requirements for Agent Runtime Integration (Fraud Forge specific)
### 3.1 Team‑specific default models (configurable)
- **Red Team**: creative scenario generation model + strict safety guard
- **Blue Team**: tool‑heavy reasoning model (retrieval + detection)
- **Gold Team (XAI)**: high‑faithfulness summarizer + JSON stability
- **Purple/Green**: code/spec generation model; can be local for IP safety
- **Black**: adversarial test/edge‑case model; may use cheaper fast model
- **Orange/White**: strict compliance/security validator model (or rule‑based)

### 3.2 Deterministic run settings
For each run, persist:
- `model_provider`, `model_name`, `model_version_pin`
- prompt template versions
- retrieval index versions (vector + BM25 + graph)
- tool registry versions

### 3.3 Safety boundaries (non‑negotiable)
- Red team outputs must be filtered to **simulation‑safe patterns only**
- tool allowlists enforced server‑side
- output redaction rules applied before persistence/export
- “kill switch” stops all LLM calls and blocks deploy actions

---

## 4) Tool Calling Normalization Requirements
### 4.1 Internal Tool Call Format (canonical)
All tool calls must be represented internally as:
```json
{
  "tool_name": "retrieve_context",
  "arguments": { "query": "…", "top_k": 8 },
  "trace_id": "…",
  "requested_by": "agent_id"
}
```

Adapters must translate:
- vendor tool call formats → canonical
- canonical → vendor tool schemas (if needed)

### 4.2 Tool Registry Enforcement
- central registry with JSON schema per tool
- runtime validation of tool call arguments
- audit log per tool call (inputs redacted; outputs hashed)
- per‑team allowlists and rate limits

---

## 5) Structured Output / Schema Enforcement Requirements
### 5.1 Mandatory response schemas
For all agent outputs, enforce Pydantic/JSON schema:
- `Plan`, `ToolCallList`, `Finding`, `Decision`, `RuleSpecProposal`
- `ExplanationBundle`, `EvidenceGraphDelta`
- `ApprovalRequest`, `DeploymentRequest`, `TestReport`

### 5.2 Validation + Repair Pipeline
- validate model output against schema
- if invalid:
  1. **repair pass** (same model, strict JSON instructions)
  2. if still invalid: fallback model
  3. if still invalid: safe failure artifact (`LLMFailure`) and stop that step gracefully

### 5.3 Content constraints
- maximum response tokens
- forbid markdown when JSON required
- enforce deterministic formatting (sorted keys; stable serialization)

---

## 6) RAG/Embeddings Independence Requirements
### 6.1 Separate Embedding Provider layer
- embedding models are independent of generator models
- store `embedding_model_id`, `dim`, `corpus_version`
- support dual indices during migration

### 6.2 Retrieval Router transparency
- persist “why this retrieval strategy was selected”
- citations and hashes for evidence pack

---

## 7) Observability, Governance, and Auditability Requirements
### 7.1 Telemetry
- per model: success rate, schema‑valid rate, p95 latency, retries
- per agent: tool call count, fallback frequency, repair frequency
- export to dashboard (or log)

### 7.2 Audit events (append‑only)
- `MODEL_SELECTED`, `FALLBACK_USED`, `SCHEMA_REPAIR`, `MODEL_ERROR`
- include `run_id`, `turn_id`, `agent_id`, provider/model pins, error type

### 7.3 Evidence Pack additions
Evidence pack must include:
- model used per step (pinned)
- fallback and repair events
- any policy violations blocked

---

## 8) Evaluation Harness Requirements
Create a deterministic eval suite:
- tool‑call accuracy tests
- schema validity rate tests
- retrieval quality sanity checks
- hallucination checks for known‑facts (from synthetic corpora)
- latency and cost budget checks
- regression thresholds (block rollout if dropped)

Outputs:
- `eval_report.json`
- `eval_report.md` (judge‑friendly)

---

## 9) Configuration Files Required
- `model_registry.yaml` — model definitions + pins + capabilities
- `routing_policy.yaml` — per team/agent defaults, fallback chains, budgets
- `prompt_manifest.yaml` — prompt template versions and IDs
- `tool_registry.yaml` — canonical tool schemas + allowlists
- `eval_suite.yaml` — test prompts, expected schema types, thresholds

---

## 10) Hackathon‑Impact Notes (realistic)
**Does this help you win?** Yes, **if** you demo it visibly:
- It makes the demo resilient (quota/outage → auto‑fallback)
- It signals enterprise readiness (bank portability)
- It complements your “AI vs AI battle + learning loop” story

**But** it’s not a trophy by itself. Judges reward **visible outcomes**:
- show “Switch model → same run still works”
- show “fallback happened → demo continued”
- show “schema repair rate and reliability dashboard”

---

## 11) Deliverables Checklist (for Copilot)
- `app/llm/providers/base.py` (PAL interface)
- `app/llm/providers/openai.py`, `anthropic.py`, `azure_openai.py`, `local.py`
- `app/llm/router.py` + `routing_policy.yaml`
- `app/llm/model_registry.py` + `model_registry.yaml`
- `app/llm/normalizers/tool_calls.py`
- `app/llm/validators/schema_guard.py` (validate + repair + fallback)
- `app/eval/` harness + `eval_suite.yaml`
- audit events + dashboards + evidence pack integration
