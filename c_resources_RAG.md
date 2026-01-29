# Fraud Forge — Multi‑Type RAG/KAG/CAG Resource Pack (Resources + Links)

This file is a curated **resource index** (docs, libraries, reference repos, and internal Fraud Forge artifacts) to build **multiple retrieval-augmented generation patterns** inside Fraud Forge:
- **Naive/Standard RAG**
- **Advanced RAG**
- **Modular RAG**
- **Hybrid RAG (dense + sparse/BM25)**
- **Self‑RAG (self‑reflective)**
- **Corrective RAG (CRAG)**
- **Agentic RAG (planner + tools + iteration)**
- **Multimodal RAG (text + image + audio/video)**
- **Knowledge‑Augmented Generation (KAG / GraphRAG)**
- **Cache‑Augmented Generation (CAG)**

> Security note (hackathon-safe): Fraud Forge must generate **defensive** artifacts and **synthetic** scenarios. Avoid producing operational “how-to” fraud steps.

---

## 1) Internal Fraud Forge artifacts you already have (use as initial corpus)

Use these as “seed sources” for the first RAG demo (taxonomy, rules, UI/agents, compliance language).  
(These are **local files** in your repo/workspace.)

- `app_RAG_Implementation.md` — baseline OpenAI + Chroma RAG architecture and code skeleton
- `banking_fraud_taxonomy_catalog_120.json` — fraud scenario taxonomy dataset
- `Fraud_Groups.md` — grouping/collections mapping
- `RBAC.md` — role-based access control requirements (for retrieval authorization)
- `RSB_Format_Understanding.md` — rule pack format / structure (for rule retrieval & diff)
- `FF_TEAM_AGENTS.md`, `requirements_do.md`, `implementation_Plan_do.md` — overall application + team roles, flows, and system requirements
- `UIX_requirements.md`, `UIX_DEV_Instructions_Plan.md` — UI/UX requirements & implementation guidance

Recommended ingestion approach:
- Ingest **taxonomy + compliance/policy + rule specs** as first-class documents.
- Keep **adversarial simulation descriptions** as *abstracted tags* (not operational steps).
- Use **RBAC** metadata on every chunk.

---

## 2) Core libraries (Python-first, FastAPI-friendly)

### LLM + embeddings
- OpenAI embeddings overview / release note (use `text-embedding-3-small` or `text-embedding-3-large`):  
  https://openai.com/index/new-embedding-models-and-api-updates/
- OpenAI embedding FAQ:  
  https://help.openai.com/articles/6824809-embeddings-faq

### Vector stores
- Chroma “Collections” cookbook (PersistentClient, collections, include fields):  
  https://cookbook.chromadb.dev/core/collections/

Optional alternatives (if you want):
- Qdrant: https://qdrant.tech/documentation/
- Weaviate: https://docs.weaviate.io/
- Milvus: https://milvus.io/docs

### Agentic orchestration
- LangGraph “Workflows and agents” (agent patterns, persistence, debugging):  
  https://docs.langchain.com/oss/javascript/langgraph/workflows-agents

(Alternative)
- LangChain docs: https://docs.langchain.com/
- LlamaIndex docs: https://docs.llamaindex.ai/

### Evaluation (must-have for “winning demo” credibility)
- RAGAS `evaluate()` reference (core evaluation entrypoint):  
  https://docs.ragas.io/en/latest/references/evaluate/

Optional evaluation tooling:
- TruLens: https://www.trulens.org/
- Promptfoo: https://www.promptfoo.dev/

---

## 3) Hybrid retrieval (dense + sparse/BM25)

### Python BM25 library
- rank_bm25 / haystack-bm25 repo (install `rank_bm25`):  
  https://github.com/deepset-ai/haystack-bm25

### Hybrid retrieval reference (BM25 + vector score fusion)
- Weaviate hybrid search overview (BM25F + vector fusion):  
  https://weaviate.io/developers/weaviate/search/hybrid  
  https://docs.weaviate.io/weaviate/concepts/search/hybrid-search

Even if you don’t use Weaviate, this gives a clean conceptual model for **score fusion**.

---

## 4) Knowledge Graph RAG (KAG / GraphRAG)

Neo4j references (practical GraphRAG patterns and tooling):
- “Enhance RAG with Knowledge Graphs” (hybrid + graph retrieval concept):  
  https://neo4j.com/blog/developer/enhance-rag-knowledge-graph/
- “LLM Knowledge Graph Builder” (end-to-end doc-to-graph → GraphRAG):  
  https://neo4j.com/blog/developer/llm-knowledge-graph-builder/
- “Unstructured KG with Neo4j & LangChain” (GraphCypherQAChain, vector index):  
  https://neo4j.com/blog/developer/unstructured-knowledge-graph-neo4j-langchain/

---

## 5) Multimodal RAG (image + audio/video + text)

### Image embeddings
- OpenAI CLIP reference repo:  
  https://github.com/openai/CLIP
- OpenCLIP (actively used open-source CLIP implementation):  
  https://github.com/mlfoundations/open_clip

### Audio/video → text
- OpenAI Audio API quickstart (speech-to-text `audio/transcriptions`):  
  https://platform.openai.com/docs/guides/audio/quickstart
- OpenAI Speech-to-text guide (models, file limits, diarization options):  
  https://platform.openai.com/docs/guides/speech-to-text

For video: extract audio → transcribe → chunk transcripts → embed and index.

---

## 6) Caching / CAG resources

CAG in practice usually means:
1) **Static context packs** (pre-built “knowledge bundles” that are loaded into the prompt)
2) **Retrieval-result caching** (query → retrieved docs cache)
3) **Answer caching** (for deterministic queries)
4) **KV/prompt caching** (provider-level caching where supported)

Implementation primitives:
- Redis cache: https://redis.io/docs/
- Disk cache for Python: https://pypi.org/project/diskcache/
- HTTP caching (ETag/Cache-Control): https://developer.mozilla.org/en-US/docs/Web/HTTP/Caching

---

## 7) “Winning demo” add-ons (high leverage)

- **RAG Transparency Panel** (show query rewrite, retrieval hits, rerank reasons, answer citations)
- **Evidence Pack Export** (PDF/JSON bundle with sources + confidence + approvals)
- **Safety rails** (blocklist/allowlist, “no operational fraud instructions”, synthetic-only data)
- **RBAC-aware retrieval** (no leakage of privileged collections)
- **Offline demo mode** (local seed dataset + deterministic outputs)

---

## 8) Minimal “stack choice” recommendation (fastest hackathon path)

- API: FastAPI
- RAG store: Chroma (local)
- Hybrid: `rank_bm25` + Chroma score fusion
- Agents: LangGraph (or simple custom planner loop)
- KG: Neo4j (optional for demo, but “wow factor” if you can show it)
- Eval: RAGAS (show metrics in dashboard)

---

## 9) Deliverables checklist (what you should have by demo day)

- ✅ Seed corpus ingested (taxonomy + rule specs + compliance + XAI templates)
- ✅ Query endpoint supports **collection routing** and **hybrid retrieval**
- ✅ UI shows **citations** and **retrieval trace**
- ✅ Evaluation report (RAGAS) + regression thresholds
- ✅ Evidence pack export + audit trail
- ✅ “Guardrails” proof: synthetic-only, policy-safe outputs

