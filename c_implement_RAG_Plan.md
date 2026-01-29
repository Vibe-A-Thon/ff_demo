# Fraud Forge — Multi‑Type RAG/KAG/CAG Implementation Plan (Step‑by‑Step)

This is a **practical implementation plan** to extend the existing Fraud Forge RAG baseline (OpenAI + Chroma) into a **multi‑pattern retrieval and knowledge system**:
- Naive RAG → Advanced RAG → Modular RAG
- Hybrid RAG (dense+BM25) + reranking
- Self‑RAG + Corrective RAG (CRAG)
- Agentic RAG (planner + tools)
- KAG / GraphRAG (Neo4j)
- CAG (cache/context packs)
- Multimodal RAG (image + audio/video)

> Safety: keep adversarial content **abstract & defensive**; generate **synthetic** examples only.

---

## 0) Start from your baseline (already defined)

Your existing baseline doc already includes:
- OpenAI embeddings (`text-embedding-3-small`)
- ChromaDB vector store
- Multiple collections (attacks/taxonomy/rules/compliance/xai/etc.)
- A core `RAGService`
- FastAPI endpoints
- Data seeding scripts
- Frontend hooks

Use that as **Phase 0** foundation and then evolve via plug-in modules.

---

## 1) Architecture upgrade — make RAG “pluggable”

### 1.1 Define a standard Retrieval Interface (contracts)
Create an internal interface layer so you can swap retrieval strategies without rewriting agents.

**Core contracts (Python interfaces / protocols):**
- `Chunker`: `chunk(doc) -> List[Chunk]`
- `Embedder`: `embed(texts) -> List[Vector]`
- `Retriever`: `retrieve(query, *, filters, top_k) -> List[Hit]`
- `Reranker`: `rerank(query, hits) -> List[Hit]`
- `ContextBuilder`: `build(hits, budget_tokens) -> ContextPack`
- `AnswerGenerator`: `generate(query, context_pack, system_policies) -> Answer`
- `Verifier`: `verify(answer, context_pack) -> VerificationResult`
- `Cache`: `get/set` for (query → retrieval hits, query → answer)
- `KGStore` (optional): graph upsert + graph query

### 1.2 Central Orchestrator: `RAGOrchestrator`
Single entrypoint called by:
- API endpoints
- Team agents (Red/Blue/Gold/White/Purple, etc.)
- UI tools (Evidence Pack builder)

`RAGOrchestrator.run(query, mode, persona, collection_scope, rbac_ctx, multimodal_inputs)`

Where:
- `mode`: naive | advanced | modular | hybrid | agentic | self_rag | crag | kag | cag | multimodal
- `persona`: red/blue/gold/white/purple/orange/green/black (controls prompting + routing + constraints)
- `collection_scope`: which collections to search
- `rbac_ctx`: user role + tenancy + sensitivity labels
- `multimodal_inputs`: optional image/audio/video

---

## 2) Data model & metadata — enforce “retrieval governance”

### 2.1 Mandatory metadata fields on every chunk
- `source_type`: taxonomy | rulespec | compliance | xai_template | incident | run_log
- `collection`: e.g., `taxonomies`, `rules`, `compliance`, `xai`
- `family_id`, `scenario_id`, `rule_id` (when applicable)
- `channel`: card | upi | netbanking | branch | merchant | atm
- `jurisdiction`: IN | EU | US (if needed)
- `sensitivity`: public | internal | restricted
- `rbac_roles_allowed`: list of roles
- `created_at`, `version`, `hash`

### 2.2 Content safety constraints (important)
- Store only **defensive** artifacts or **abstract** adversarial patterns.
- If you must represent “adversarial behavior”, use **non-operational tags**:
  - e.g., `pattern_tag: "velocity_anomaly"`, `pattern_tag: "identity_mismatch"`
- No “how-to commit fraud” content in the corpus.

---

## 3) Implement the RAG modes (incremental phases)

### Phase A — Naive / Standard RAG (baseline)
**Goal:** retrieve chunks → stuff into prompt → answer with citations.

Steps:
1. Query → embed
2. Vector retrieval from chosen collection(s)
3. Context pack build (token-budget)
4. Answer generation
5. Return: answer + citations + retrieved hits (for UI transparency)

Acceptance criteria:
- Deterministic response structure (`Answer` schema)
- Each answer contains at least N citations

---

### Phase B — Advanced RAG (query rewriting + filtering + reranking)
**Goal:** improve relevance & reduce noise.

Add modules:
1) **Query rewrite**:
   - Expand acronyms (MCC, KYC, AML)
   - Create sub-queries (e.g., “signals”, “controls”, “playbook”)
2) **Pre-filters**:
   - collection filters (taxonomy vs rules)
   - channel filters (UPI vs cards)
   - RBAC filters (role-based)
3) **Reranking**:
   - Cross-encoder reranker OR LLM reranker (small budget)

Outputs for UI:
- Show original query + rewritten query
- Show filters applied
- Show before/after rerank ordering

Acceptance criteria:
- Improved retrieval precision on a small test set
- Less than X% empty results

---

### Phase C — Modular RAG (plug-and-play)
**Goal:** allow the UI to select modules at runtime.

Implement:
- `RAGPipelineConfig` (JSON/YAML):
  - chunking policy
  - embeddings model
  - retrieval type
  - reranker type
  - context budget
  - verifier type
  - caching policy
- “Pipeline Builder” that instantiates modules based on config.

UI:
- “RAG Mode Switcher” dropdown
- “Context Budget” slider
- “Collections” multi-select

---

### Phase D — Hybrid RAG (dense + BM25)
**Goal:** best of semantic + exact match.

Implementation:
1. Dense retrieval from Chroma (vector)
2. Sparse retrieval using BM25 (in-memory or separate store)
3. Score fusion:
   - normalized similarity + normalized BM25 score
   - alpha weight (UI slider)
4. Rerank fused list (optional)

Acceptance criteria:
- Keyword-heavy queries show better results (IDs, rule codes, policy refs)

---

### Phase E — Self‑RAG (self-check)
**Goal:** reduce hallucinations by verifying relevance & grounding.

Add:
- `Verifier` module:
  - checks if answer claims are supported by retrieved chunks
  - checks “coverage”: are the retrieved chunks sufficient?
- If failed:
  - request more retrieval
  - broaden search scope
  - reduce constraints

UI:
- “Grounding Score”
- “Unsupported Claims” list
- “Retry with broader scope” button

---

### Phase F — Corrective RAG (CRAG)
**Goal:** detect low-quality retrieval and correct before generation.

Add:
- Retrieval quality gates:
  - min similarity threshold
  - diversity threshold (avoid duplicates)
  - source-type coverage (rules + compliance + taxonomy)
- Correction strategies:
  - alternate query rewrite
  - fallback to BM25
  - expand to adjacent collections
  - ask clarifying question **in UI** (not blocking API)

UI:
- “Retrieval Quality Gate” indicator (PASS/WARN/FAIL)
- Correction log (what the system changed)

---

### Phase G — Agentic RAG (planner + tools + iteration)
**Goal:** for complex questions (multi-hop, long playbooks), the system plans and iterates.

Agent loop:
1. **Planner**: decomposes question into steps (e.g., “Find scenario”, “Find controls”, “Generate response template”)
2. **Tool use**:
   - `retrieve_taxonomy`
   - `retrieve_rules`
   - `retrieve_compliance`
   - `search_runs` (evidence logs)
   - `build_evidence_pack`
3. **Iterate** until success criteria met:
   - min grounding score
   - min citations
4. Return final answer + full trace.

Implementation options:
- LangGraph (recommended): graph of nodes (plan → retrieve → verify → finalize)
- Or custom finite-state loop.

UI:
- Step timeline (like a “thinking visualizer”)
- Tool calls list
- “Stop / pause / replay” (super demo-friendly)

---

### Phase H — Knowledge‑Augmented Generation (KAG / GraphRAG)
**Goal:** multi-hop reasoning and entity relationships (accounts, devices, merchants, policies, controls).

Graph build steps:
1. Extract entities & relations from:
   - taxonomy scenarios
   - rules (rule_id → indicator → control)
   - compliance obligations (policy → requirement → control)
2. Store in Neo4j:
   - `Entity`, `Document`, `Chunk`, `Control`, `Rule`, `Scenario`
3. Retrieval:
   - entity-centric subgraph fetch
   - hybrid retrieval (vector+keyword+graph)
4. Generation:
   - produce answer grounded in subgraph facts and retrieved chunks

UI:
- “Knowledge Graph Explorer”
- Click node → show supporting sources

Hackathon path:
- Start with a **small KG** (scenario→indicators→controls→rules) and show the visualization.

---

### Phase I — Cache‑Augmented Generation (CAG)
**Goal:** speed + stability for repeated questions and static corpora.

Implement 3 caches:
1. **Context Pack Cache**:
   - key: `(mode, collections, query_hash, filters)`
   - value: `ContextPack`
2. **Retrieval Cache**:
   - key: `(embedding_model, collection, query_hash, filters)`
   - value: `HitList`
3. **Answer Cache** (optional):
   - key: `(system_prompt_hash, query_hash, context_hash)`
   - value: final answer

Static “Knowledge Bundles” (CAG packs):
- Build once at startup:
  - “Policy Pack” (compliance)
  - “Taxonomy Pack”
  - “XAI Pack”
- Use these packs as **always-available** context for certain personas (e.g., Gold/White).

UI:
- Cache hit/miss indicator
- Warm-up button (for demo)

---

### Phase J — Multimodal RAG (text + images + audio/video)
**Goal:** retrieve and explain evidence across media.

Pipelines:
1) **Image**:
   - embed via CLIP/OpenCLIP
   - store vectors + metadata
   - retrieve similar images + captions
2) **Audio/Video**:
   - transcribe (speech-to-text)
   - chunk transcripts
   - embed + index
3) Combine:
   - multimodal hit merge
   - single context pack with multimodal citations

UI:
- Evidence viewer (image thumbnails, transcript segments)
- “Jump to timestamp” for audio/video

---

## 4) API design (FastAPI endpoints)

Suggested endpoints:
- `POST /rag/query` → main orchestrator entrypoint
- `POST /rag/seed` → seed or refresh collections
- `GET /rag/collections` → list collections + stats
- `POST /rag/evaluate` → run RAGAS evaluation and store report
- `GET /rag/traces/{run_id}` → agentic trace timeline
- `POST /rag/evidence-pack` → export evidence pack (JSON/PDF)

Return shapes must include:
- `answer`
- `citations[]` (source_id, chunk_id, offsets)
- `retrieval_debug` (optional, gated by role)
- `trace` (for agentic)

---

## 5) UI integration (make it “wow” in demo)

Must-have UI widgets:
- **RAG Mode switcher** (naive/advanced/hybrid/agentic/kag/cag/multimodal)
- **Evidence sidebar** with citations
- **Retrieval trace** (before/after rerank)
- **Grounding score + warnings**
- **Replay** (timeline of steps)
- **Export evidence pack**

Demo story:
- Show the same query across 3 modes:
  - naive vs hybrid vs agentic
- Show KG exploration for one scenario
- Show evaluation dashboard with RAGAS score

---

## 6) Evaluation & QA (hackathon credibility)

### 6.1 Build a small gold dataset (20–50 questions)
- For each question, define:
  - expected source types (taxonomy + compliance + rules)
  - expected key facts (bulleted)
  - “must cite” documents

### 6.2 Automate evaluation (RAGAS + regression)
- Run `evaluate()` nightly or on-demand
- Gate merges if metrics drop below threshold
- Track:
  - faithfulness
  - answer relevance
  - context precision/recall

---

## 7) Security / governance (must not leak data)

- RBAC-aware retrieval (filter at query time, not after)
- Per-tenant namespaces/collections (hackathon: simulate tenancy with metadata)
- Audit log all retrieval + answer events
- Safety policy:
  - refuse operational wrongdoing instructions
  - return defensive guidance and reporting templates

---

## 8) “Fastest hackathon build” sequence (what to do first)

1) Implement **Modular RAG interface** + `RAGOrchestrator`
2) Add **Advanced RAG** (rewrite + rerank)
3) Add **Hybrid retrieval** (dense + BM25) + alpha slider in UI
4) Add **Self-RAG verifier** + grounding score widget
5) Add **Agentic RAG** replay timeline
6) If time: add **KAG mini-graph** visualization + one GraphRAG query

---

## 9) Definition of Done (DoD)

Your RAG layer is “demo-ready” when:
- ✅ Every answer shows citations + evidence panel
- ✅ You can switch RAG modes live
- ✅ Agentic mode shows a step timeline
- ✅ Evaluation dashboard shows RAGAS results
- ✅ RBAC filters prevent restricted retrieval
- ✅ Exportable evidence pack exists
