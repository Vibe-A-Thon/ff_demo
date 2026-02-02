# Implementation Plan: Multi-Type RAG for Fraud Forge

## Phase 1: Foundation - Hybrid Retrieval Engine (Weeks 1-2)
**Goal:** Build the unified retrieval layer that supports both semantic (behavioral) and keyword (identifier) search.

### Step 1.1: Vector Store Setup (ChromaDB)
* **Action:** Deploy ChromaDB in Docker.
* **Data Structure:** Create collections for `transactions`, `patterns`, and `rules`.
* **Embedding Model:** Use `text-embedding-3-small` (OpenAI) or `bge-m3` (Open Source) for high-performance embeddings.
* **Code:** Implement a `VectorStoreService` class that handles document chunking and ingestion.

### Step 1.2: Keyword Search Setup (BM25)
* **Action:** Integrate `rank_bm25` or ElasticSearch.
* **Why:** To allow agents to search by exact `transaction_id`, `account_number`, or `error_code`.
* **Integration:** Build a `HybridRetriever` class that queries both Vector and BM25 indices and fuses results using Reciprocal Rank Fusion (RRF).

## Phase 2: Knowledge Graph Integration - GraphRAG (Weeks 3-4)
**Goal:** Enable the detection of complex fraud rings and relationships.

### Step 2.1: Graph Database Deployment
* **Action:** Deploy Neo4j Community Edition via Docker.
* **Schema Design:** Define nodes (`Customer`, `Account`, `Transaction`, `Device`, `IP`) and relationships (`TRANSFERRED_TO`, `USED_DEVICE`, `SHARED_IP`).

### Step 2.2: Knowledge Graph Construction
* **Pipeline:** Build an ingestion script that converts raw transaction logs into graph nodes/edges.
* **GraphRAG Implementation:**
    * Use LangChain's `GraphCypherQAChain` to allow LLMs to write Cypher queries.
    * Implement "Community Detection" algorithms (Louvain) to pre-calculate fraud rings and store them as context for the RAG system.

## Phase 3: Agentic Intelligence - The "Brain" (Weeks 5-6)
**Goal:** Transform static retrieval into active planning agents.

### Step 3.1: LangGraph Orchestration
* **Action:** Initialize a `StateGraph` for Red and Blue agents.
* **State Schema:** Define the agent state (e.g., `messages`, `retrieved_docs`, `plan`, `critique`).

### Step 3.2: Tool Integration
* **Tools:** Register the `HybridRetriever` and `GraphRetriever` as tools the agent can call.
* **Logic:** Implement a "Plan-and-Execute" flow where the agent first outlines a search strategy (e.g., "Check IP history, then check linked accounts") before executing tools.

## Phase 4: Self-Correction & Robustness (Weeks 7-8)
**Goal:** Ensure high reliability for code generation and compliance reports.

### Step 4.1: Self-RAG Implementation
* **Critic Model:** Fine-tune or prompt a small model (e.g., GPT-4o-mini) to act as a "Critic."
* **Workflow:**
    1.  **Retrieve:** Fetch documents.
    2.  **Grade:** Critic evaluates relevance (Score 0-1).
    3.  **Generate:** Generator creates an answer.
    4.  **Reflect:** Critic evaluates if the answer is supported by the documents.
    5.  **Loop:** If scores are low, rewrite the query and retry.

### Step 4.2: Corrective RAG (CRAG) Logic
* **Trigger:** If the "Relevance Score" from the retrieval step is below a threshold (e.g., 0.7), trigger a corrective action.
* **Action:** For Fraud Forge, the corrective action is to "widen the search" (e.g., expand the time window of transaction logs) or "switch strategies" (e.g., move from Graph search to Vector search).

## Phase 5: Production & Optimization (Week 9)
* **Caching:** Implement Cache-Augmented Generation (CAG) using Redis for frequently accessed static rules (e.g., KYC guidelines).
* **Evaluation:** Use Ragas or TruLens to benchmark the RAG pipeline's faithfulness and answer relevance.