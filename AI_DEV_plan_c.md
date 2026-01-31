# 🛠️ FRAUD FORGE — AI Development Implementation Plan
## Phase-by-Phase Development Guide for All AI Functionalities
### Version 3.0 | Hackathon Winning Implementation | 100% Victory Target

---

# 📋 TABLE OF CONTENTS

1. [Executive Summary](#1-executive-summary)
2. [Development Timeline](#2-development-timeline)
3. [Phase 0: Foundation Setup](#3-phase-0-foundation-setup)
4. [Phase 1: LLM Integration](#4-phase-1-llm-integration)
5. [Phase 2: RAG System Core](#5-phase-2-rag-system-core)
6. [Phase 3-5: Multi-Agent Framework](#6-phase-3-5-multi-agent-framework)
7. [Phase 6-8: Advanced RAG, KAG, XAI](#7-phase-6-8-advanced-rag-kag-xai)
8. [Phase 9: Agentic RAG & Self-RAG](#8-phase-9-agentic-rag--self-rag)
9. [Phase 10: War Loop Integration](#9-phase-10-war-loop-integration)
10. [Phase 11-12: Testing & Demo](#10-phase-11-12-testing--demo)
11. [Quick Start Commands](#11-quick-start-commands)
12. [API Endpoints Reference](#12-api-endpoints-reference)

---

# 1. EXECUTIVE SUMMARY

## 1.1 Development Strategy

This plan implements the complete AI functionality for Fraud Forge in **12 phases**, designed to:
- Connect to LLM via API key from `.env` file
- Build progressively from foundation to advanced features
- Ensure each phase produces working, testable components
- Prioritize hackathon-winning demo capabilities

## 1.2 Phase Overview

| Phase | Name | Duration | Deliverable |
|-------|------|----------|-------------|
| 0 | Foundation Setup | Day 1 | Project structure, dependencies |
| 1 | LLM Integration | Day 1-2 | OpenAI service working |
| 2 | RAG System Core | Day 2-3 | ChromaDB + basic RAG |
| 3 | Multi-Agent Framework | Day 3-4 | BaseAgent + registry |
| 4 | Team Orchestrators | Day 4-5 | 8 orchestrators |
| 5 | Sub-Agent Implementation | Day 5-7 | 54 agents (stubs) |
| 6 | Advanced RAG Patterns | Day 7-8 | Hybrid + reranking |
| 7 | Knowledge Graph | Day 8-9 | Neo4j integration |
| 8 | XAI Pipeline | Day 9-10 | Gold Team XAI |
| 9 | Agentic RAG & Self-RAG | Day 10-11 | LangGraph workflows |
| 10 | War Loop Integration | Day 11-12 | Full state machine |
| 11 | Evaluation & Testing | Day 12-13 | RAGAS + quality gates |
| 12 | Demo Preparation | Day 13-14 | Demo mode + replay |

---

# 2. DEVELOPMENT TIMELINE

```
Week 1: Foundation & Core AI
├── Day 1: Phase 0 (Foundation) + Phase 1 (LLM)
├── Day 2: Phase 1 (LLM) + Phase 2 (RAG Core)
├── Day 3: Phase 2 (RAG) + Phase 3 (Multi-Agent Framework)
├── Day 4: Phase 3 (Framework) + Phase 4 (Orchestrators)
├── Day 5: Phase 4 (Orchestrators) + Phase 5 (Sub-Agents)
├── Day 6: Phase 5 (Sub-Agents continued)
└── Day 7: Phase 5 (Complete) + Phase 6 (Advanced RAG)

Week 2: Advanced Features & Integration
├── Day 8: Phase 6 (Advanced RAG) + Phase 7 (KAG)
├── Day 9: Phase 7 (KAG) + Phase 8 (XAI)
├── Day 10: Phase 8 (XAI) + Phase 9 (Agentic RAG)
├── Day 11: Phase 9 (Self-RAG) + Phase 10 (War Loop)
├── Day 12: Phase 10 (Integration) + Phase 11 (Testing)
├── Day 13: Phase 11 (Quality) + Phase 12 (Demo)
└── Day 14: Phase 12 (Demo Polish) + Final Testing
```

---

# 3. PHASE 0: FOUNDATION SETUP

## 3.1 Directory Structure

```
fraud-forge/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── openai_service.py
│   │   │   ├── rag/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── vector_store.py
│   │   │   │   ├── hybrid.py
│   │   │   │   ├── agentic.py
│   │   │   │   └── graph_rag.py
│   │   │   └── agents/
│   │   │       ├── __init__.py
│   │   │       ├── base_agent.py
│   │   │       ├── registry.py
│   │   │       ├── factory.py
│   │   │       └── teams/
│   │   ├── xai/
│   │   │   └── explainer.py
│   │   ├── api/routes/
│   │   └── schemas/
│   ├── scripts/
│   │   ├── seed_rag.py
│   │   ├── test_llm.py
│   │   └── demo_run.py
│   ├── requirements.txt
│   └── .env
├── data/
│   └── banking_fraud_taxonomy_catalog_120.json
└── docker-compose.yml
```

## 3.2 Requirements.txt

```txt
# Core Framework
fastapi==0.109.0
uvicorn==0.27.0
pydantic==2.5.3
pydantic-settings==2.1.0
python-dotenv==1.0.0

# OpenAI
openai==1.12.0
tiktoken==0.5.2

# LangChain & LangGraph
langchain==0.1.0
langchain-openai==0.0.5
langgraph==0.0.20

# Vector Store
chromadb==0.4.22

# Graph Database
neo4j==5.15.0
networkx==3.2.1

# Search & Retrieval
rank-bm25==0.2.2

# Evaluation
ragas==0.1.0

# Caching
redis==5.0.1

# Async
httpx==0.26.0
aiofiles==23.2.1
tenacity==8.2.3

# Testing
pytest==7.4.4
pytest-asyncio==0.23.3
```

## 3.3 Environment Configuration (.env)

```bash
# OpenAI Configuration (REQUIRED)
OPENAI_API_KEY=sk-your-api-key-here

# Model Configuration
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Vector Store
CHROMA_PERSIST_DIRECTORY=./chroma_data

# Graph Database (Optional)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# Cache (Optional)
REDIS_URL=redis://localhost:6379

# Application
DEBUG=true
LOG_LEVEL=INFO
```

## 3.4 Config Module

```python
# backend/app/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    """Application settings loaded from .env file."""
    
    # OpenAI (REQUIRED)
    openai_api_key: str
    openai_model: str = "gpt-4-turbo-preview"
    openai_embedding_model: str = "text-embedding-3-small"
    
    # Vector Store
    chroma_persist_directory: str = "./chroma_data"
    
    # Graph Database (Optional)
    neo4j_uri: Optional[str] = None
    neo4j_user: Optional[str] = None
    neo4j_password: Optional[str] = None
    
    # Cache (Optional)
    redis_url: Optional[str] = None
    
    # Application
    debug: bool = False
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
```

## 3.5 Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - CHROMA_PERSIST_DIRECTORY=/data/chroma
    volumes:
      - ./backend:/app
      - chroma_data:/data/chroma
    depends_on:
      - chromadb

  chromadb:
    image: chromadb/chroma:latest
    ports:
      - "8001:8000"
    volumes:
      - chroma_data:/chroma/chroma

  neo4j:
    image: neo4j:5.15-community
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      - NEO4J_AUTH=neo4j/password
    volumes:
      - neo4j_data:/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  chroma_data:
  neo4j_data:
```

---

# 4. PHASE 1: LLM INTEGRATION

## 4.1 OpenAI Service

```python
# backend/app/services/openai_service.py
"""
OpenAI service for LLM completions and embeddings.
Connects to OpenAI API using key from .env file.
"""

from typing import List, Optional, AsyncGenerator, Dict, Any
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
from app.config import settings
import logging
import json

logger = logging.getLogger(__name__)

class OpenAIService:
    """OpenAI service with all required AI capabilities."""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.embedding_model = settings.openai_embedding_model
        self._usage_stats = {"total_tokens": 0, "total_cost": 0.0}
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        json_mode: bool = False
    ) -> str:
        """Generate completion using OpenAI GPT-4."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response_format = {"type": "json_object"} if json_mode else {"type": "text"}
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format
            )
            
            if response.usage:
                self._usage_stats["total_tokens"] += response.usage.total_tokens
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI generation error: {e}")
            raise
    
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7
    ) -> AsyncGenerator[str, None]:
        """Stream completion for real-time display."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            stream=True
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector using OpenAI."""
        response = await self.client.embeddings.create(
            model=self.embedding_model,
            input=text
        )
        return response.data[0].embedding
    
    async def generate_embeddings_batch(
        self, 
        texts: List[str],
        batch_size: int = 100
    ) -> List[List[float]]:
        """Generate embeddings for multiple texts in batches."""
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            response = await self.client.embeddings.create(
                model=self.embedding_model,
                input=batch
            )
            all_embeddings.extend([d.embedding for d in response.data])
        
        return all_embeddings
    
    async def function_call(
        self,
        prompt: str,
        tools: List[Dict],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3
    ) -> Dict[str, Any]:
        """Execute function calling with tools."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=temperature
        )
        
        message = response.choices[0].message
        
        if message.tool_calls:
            tool_call = message.tool_calls[0]
            return {
                "tool_name": tool_call.function.name,
                "tool_args": json.loads(tool_call.function.arguments),
                "content": message.content
            }
        
        return {"content": message.content}
    
    def get_usage_stats(self) -> Dict[str, Any]:
        return self._usage_stats.copy()

# Singleton instance
openai_service = OpenAIService()
```

## 4.2 Test LLM Script

```python
# backend/scripts/test_llm.py
"""Test LLM integration."""

import asyncio
from app.services.openai_service import openai_service

async def main():
    print("=" * 50)
    print("TESTING LLM INTEGRATION")
    print("=" * 50)
    
    # Test generation
    print("\n1. Testing generation...")
    response = await openai_service.generate(
        prompt="What are the top 3 types of banking fraud?",
        system_prompt="You are a fraud detection expert. Be concise.",
        max_tokens=300
    )
    print(f"   ✓ Response: {response[:100]}...")
    
    # Test embeddings
    print("\n2. Testing embeddings...")
    embedding = await openai_service.generate_embedding(
        "Structuring fraud involves splitting large transactions"
    )
    print(f"   ✓ Embedding dimension: {len(embedding)}")
    
    # Test JSON mode
    print("\n3. Testing JSON mode...")
    json_response = await openai_service.generate(
        prompt="List 2 fraud types as JSON with 'name' and 'description'",
        json_mode=True
    )
    print(f"   ✓ JSON: {json_response[:100]}...")
    
    print("\n" + "=" * 50)
    print("✅ ALL TESTS PASSED!")
    print(f"Total tokens: {openai_service.get_usage_stats()['total_tokens']}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

# 5. PHASE 2: RAG SYSTEM CORE

## 5.1 Vector Store Service

```python
# backend/app/services/rag/vector_store.py
"""ChromaDB vector store for RAG system."""

import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any, Optional
from app.config import settings
from app.services.openai_service import openai_service
import logging

logger = logging.getLogger(__name__)

class VectorStoreService:
    """ChromaDB vector store for RAG."""
    
    # Collection names
    ATTACKS = "attacks"
    PATTERNS = "patterns"
    TAXONOMY = "taxonomy"
    RULES = "rules"
    EXPLANATIONS = "explanations"
    COMPLIANCE = "compliance"
    INCIDENTS = "incidents"
    
    def __init__(self):
        self.client = None
        self.collections: Dict[str, chromadb.Collection] = {}
    
    async def initialize(self):
        """Initialize ChromaDB and collections."""
        logger.info("Initializing ChromaDB...")
        
        self.client = chromadb.PersistentClient(
            path=settings.chroma_persist_directory,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        
        collection_names = [
            self.ATTACKS, self.PATTERNS, self.TAXONOMY,
            self.RULES, self.EXPLANATIONS, self.COMPLIANCE,
            self.INCIDENTS
        ]
        
        for name in collection_names:
            self.collections[name] = self.client.get_or_create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"Collection '{name}' ready")
    
    async def add_documents_batch(
        self,
        collection_name: str,
        documents: List[Dict[str, Any]]
    ) -> int:
        """Add multiple documents to collection."""
        collection = self.collections.get(collection_name)
        if not collection:
            return 0
        
        ids = [d["id"] for d in documents]
        texts = [d["text"] for d in documents]
        metadatas = [d.get("metadata", {}) for d in documents]
        
        embeddings = await openai_service.generate_embeddings_batch(texts)
        
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )
        
        return len(documents)
    
    async def search(
        self,
        collection_name: str,
        query: str,
        limit: int = 5,
        filters: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """Search collection for similar documents."""
        collection = self.collections.get(collection_name)
        if not collection:
            return []
        
        query_embedding = await openai_service.generate_embedding(query)
        
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            where=filters
        )
        
        formatted = []
        for i in range(len(results["ids"][0])):
            formatted.append({
                "id": results["ids"][0][i],
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                "similarity": 1 - results["distances"][0][i] if results["distances"] else 0
            })
        
        return formatted
    
    async def get_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all collections."""
        return {name: {"count": col.count()} for name, col in self.collections.items()}

vector_store = VectorStoreService()
```

## 5.2 RAG Service

```python
# backend/app/services/rag/__init__.py
"""Core RAG service for Fraud Forge."""

from typing import List, Dict, Any, Optional
from app.services.rag.vector_store import vector_store, VectorStoreService
import logging

logger = logging.getLogger(__name__)

class RAGService:
    """Main RAG service for fraud knowledge retrieval."""
    
    def __init__(self):
        self.vs = vector_store
    
    async def initialize(self):
        await self.vs.initialize()
        logger.info("RAG Service initialized")
    
    async def find_scenarios(self, query: str, limit: int = 5) -> List[Dict]:
        """Find fraud taxonomy scenarios."""
        return await self.vs.search(VectorStoreService.TAXONOMY, query, limit)
    
    async def find_rules(self, query: str, limit: int = 5) -> List[Dict]:
        """Find detection rules."""
        return await self.vs.search(VectorStoreService.RULES, query, limit)
    
    async def find_explanations(self, query: str, limit: int = 5) -> List[Dict]:
        """Find past explanations."""
        return await self.vs.search(VectorStoreService.EXPLANATIONS, query, limit)
    
    async def build_red_team_context(self, query: str, limit: int = 5) -> str:
        """Build context for Red Team agents."""
        scenarios = await self.find_scenarios(query, limit)
        attacks = await self.vs.search(VectorStoreService.ATTACKS, query, limit)
        
        parts = ["### FRAUD SCENARIOS"]
        for s in scenarios:
            parts.append(f"- {s['text'][:300]}")
        parts.append("\n### PAST ATTACKS")
        for a in attacks:
            parts.append(f"- {a['text'][:300]}")
        
        return "\n".join(parts)
    
    async def build_blue_team_context(self, query: str, limit: int = 5) -> str:
        """Build context for Blue Team agents."""
        patterns = await self.vs.search(VectorStoreService.PATTERNS, query, limit)
        rules = await self.find_rules(query, limit)
        
        parts = ["### DETECTION PATTERNS"]
        for p in patterns:
            parts.append(f"- {p['text'][:300]}")
        parts.append("\n### DETECTION RULES")
        for r in rules:
            parts.append(f"- {r['text'][:300]}")
        
        return "\n".join(parts)
    
    async def build_gold_team_context(self, query: str, limit: int = 5) -> str:
        """Build context for Gold Team (XAI) agents."""
        explanations = await self.find_explanations(query, limit)
        scenarios = await self.find_scenarios(query, limit)
        
        parts = ["### PAST EXPLANATIONS"]
        for e in explanations:
            parts.append(f"- {e['text'][:300]}")
        parts.append("\n### RELATED SCENARIOS")
        for s in scenarios:
            parts.append(f"- {s['text'][:300]}")
        
        return "\n".join(parts)
    
    async def get_stats(self) -> Dict[str, Dict[str, Any]]:
        return await self.vs.get_stats()

rag_service = RAGService()
```

## 5.3 Seed RAG Script

```python
# backend/scripts/seed_rag.py
"""Seed RAG system with fraud taxonomy data."""

import asyncio
import json
from pathlib import Path
from app.services.rag import rag_service
from app.services.rag.vector_store import vector_store, VectorStoreService

async def seed_taxonomy():
    """Seed fraud scenarios."""
    print("Seeding taxonomy...")
    
    # Sample scenarios (use full taxonomy JSON in production)
    scenarios = [
        {"scenario_id": "S001", "family_id": "F01", "name": "Synthetic Identity", 
         "description": "Fake identity using mixed real/fake data", "risk_level": "High"},
        {"scenario_id": "S002", "family_id": "F02", "name": "Account Takeover",
         "description": "Unauthorized access via credential theft", "risk_level": "High"},
        {"scenario_id": "S003", "family_id": "F05", "name": "Structuring",
         "description": "Splitting transactions to avoid reporting", "risk_level": "High"},
    ]
    
    documents = []
    for s in scenarios:
        documents.append({
            "id": s["scenario_id"],
            "text": f"Fraud Type: {s['name']}. {s['description']}. Risk: {s['risk_level']}",
            "metadata": {"family_id": s["family_id"], "risk_level": s["risk_level"]}
        })
    
    count = await vector_store.add_documents_batch(VectorStoreService.TAXONOMY, documents)
    print(f"✓ Seeded {count} scenarios")

async def seed_rules():
    """Seed detection rules."""
    print("Seeding rules...")
    
    rules = [
        {"id": "RULE_001", "text": "Structuring Detection: Flag deposits $9000-$9999 within 24h", 
         "metadata": {"action": "review", "confidence": "0.85"}},
        {"id": "RULE_002", "text": "Velocity Check: Flag >10 transactions in 1 hour",
         "metadata": {"action": "review", "confidence": "0.80"}},
        {"id": "RULE_003", "text": "Impossible Travel: Flag transactions >500 miles apart in <2h",
         "metadata": {"action": "block", "confidence": "0.95"}},
    ]
    
    count = await vector_store.add_documents_batch(VectorStoreService.RULES, rules)
    print(f"✓ Seeded {count} rules")

async def main():
    print("=" * 50)
    print("SEEDING FRAUD FORGE RAG")
    print("=" * 50)
    
    await rag_service.initialize()
    await seed_taxonomy()
    await seed_rules()
    
    stats = await rag_service.get_stats()
    print("\nStats:", {k: v["count"] for k, v in stats.items()})
    print("\n✓ Seeding complete!")

if __name__ == "__main__":
    asyncio.run(main())
```

---

# 6. PHASE 3-5: MULTI-AGENT FRAMEWORK

## 6.1 Base Agent

```python
# backend/app/services/agents/base_agent.py
"""Base agent class implementing Agent 2.0 principles."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from enum import Enum
from datetime import datetime
import uuid

class AgentStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class Task(BaseModel):
    task_id: str
    run_id: str
    team_id: str
    task_type: str
    params: Dict[str, Any] = {}
    seed: Optional[str] = None

class Artifact(BaseModel):
    artifact_id: str
    artifact_type: str
    payload: Dict[str, Any] = {}
    created_by: str = ""
    created_at: datetime = datetime.utcnow()

class AgentResult(BaseModel):
    agent_id: str
    task_id: str
    status: str
    outputs: List[Artifact] = []
    decision_trace: List[str] = []
    error: Optional[str] = None

class BaseAgent(ABC):
    """Abstract base for all Fraud Forge agents."""
    
    def __init__(self, agent_id: str, agent_name: str, team_id: str, role: str):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.team_id = team_id
        self.role = role
        self.status = AgentStatus.IDLE
        self.capabilities: List[str] = []
    
    @abstractmethod
    async def run(self, task: Task) -> AgentResult:
        """Execute the agent's task."""
        pass
    
    def make_artifact_id(self) -> str:
        return f"art_{self.team_id}_{uuid.uuid4().hex[:8]}"
```

## 6.2 Agent Factory (All 54 Agents)

```python
# backend/app/services/agents/factory.py
"""Agent factory for all 54 agents."""

from app.services.agents.base_agent import BaseAgent, Task, AgentResult, Artifact, AgentStatus
from typing import List, Dict

AGENT_DEFINITIONS = {
    "red": [
        ("red.agent.01", "Red Orchestrator", "orchestrator"),
        ("red.agent.02", "Fraud Scenario Generator", "scenario_generator"),
        ("red.agent.03", "Transaction Executor", "executor"),
        ("red.agent.04", "Loan Abuse Agent", "abuse_simulator"),
        ("red.agent.05", "Identity Spoof Agent", "identity_spoof"),
        ("red.agent.06", "Bot Swarm Agent", "swarm"),
        ("red.agent.07", "Recon Agent", "recon"),
        ("red.agent.08", "Adaptive Learner", "learner"),
    ],
    "blue": [
        ("blue.agent.01", "Blue Orchestrator", "orchestrator"),
        ("blue.agent.02", "Rule Evaluator", "rule_evaluator"),
        ("blue.agent.03", "Baseline Detector", "baseline"),
        ("blue.agent.04", "Graph Analyzer", "graph"),
        ("blue.agent.05", "Device Risk Agent", "device_risk"),
        ("blue.agent.06", "Model Scorer", "model_scorer"),
        ("blue.agent.07", "Decision Agent", "decision"),
        ("blue.agent.08", "Escalation Agent", "escalator"),
        ("blue.agent.09", "Monitor Agent", "monitor"),
    ],
    "purple": [
        ("purple.agent.01", "Purple Orchestrator", "orchestrator"),
        ("purple.agent.02", "Root Cause Analyst", "root_cause"),
        ("purple.agent.03", "Rule Author", "rule_author"),
        ("purple.agent.04", "Threat Forecaster", "forecaster"),
        ("purple.agent.05", "Policy Agent", "policy"),
        ("purple.agent.06", "KG Curator", "kg_curator"),
        ("purple.agent.07", "Requirements Packager", "requirements"),
    ],
    "green": [
        ("green.agent.01", "Green Orchestrator", "orchestrator"),
        ("green.agent.02", "Code Translator", "code_gen"),
        ("green.agent.03", "Pipeline Builder", "pipeline"),
        ("green.agent.04", "Feature Engineer", "feature"),
        ("green.agent.05", "Observability Agent", "observability"),
        ("green.agent.06", "Performance Agent", "performance"),
        ("green.agent.07", "Config Agent", "config"),
    ],
    "black": [
        ("black.agent.01", "Black Orchestrator", "orchestrator"),
        ("black.agent.02", "Replay Agent", "replay"),
        ("black.agent.03", "Edge Case Generator", "edge_case"),
        ("black.agent.04", "Chaos Agent", "chaos"),
        ("black.agent.05", "Load Tester", "load"),
        ("black.agent.06", "Coverage Auditor", "coverage"),
        ("black.agent.07", "Defect Reporter", "defect"),
    ],
    "orange": [
        ("orange.agent.01", "Orange Orchestrator", "orchestrator"),
        ("orange.agent.02", "Code Reviewer", "code_review"),
        ("orange.agent.03", "Security Reviewer", "security"),
        ("orange.agent.04", "Evidence Verifier", "evidence"),
        ("orange.agent.05", "Risk Assessor", "risk"),
        ("orange.agent.06", "Rollback Verifier", "rollback"),
    ],
    "gold": [
        ("gold.agent.01", "Gold Orchestrator", "orchestrator"),
        ("gold.agent.02", "Explainer", "explainer"),
        ("gold.agent.03", "Evidence Tracer", "evidence"),
        ("gold.agent.04", "Audience Adapter", "audience"),
        ("gold.agent.05", "Explanation QA", "qa"),
        ("gold.agent.06", "Narrator", "narrator"),
    ],
    "white": [
        ("white.agent.01", "White Orchestrator", "orchestrator"),
        ("white.agent.02", "Regulatory Mapper", "regulatory"),
        ("white.agent.03", "Compliance Validator", "compliance"),
        ("white.agent.04", "Fairness Monitor", "fairness"),
        ("white.agent.05", "Audit Trail Agent", "audit"),
        ("white.agent.06", "Approver", "approver"),
    ]
}

class GenericAgent(BaseAgent):
    """Generic agent for hackathon prototype."""
    
    async def run(self, task: Task) -> AgentResult:
        self.status = AgentStatus.RUNNING
        artifact = Artifact(
            artifact_id=self.make_artifact_id(),
            artifact_type=f"{self.team_id}_output",
            payload={"agent": self.agent_id, "task": task.task_type},
            created_by=self.agent_id
        )
        self.status = AgentStatus.COMPLETED
        return AgentResult(
            agent_id=self.agent_id,
            task_id=task.task_id,
            status="success",
            outputs=[artifact],
            decision_trace=[f"executed:{task.task_type}"]
        )

class AgentRegistry:
    """Central registry for all agents."""
    
    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}
        self._teams: Dict[str, List[str]] = {}
    
    def register(self, agent: BaseAgent):
        self._agents[agent.agent_id] = agent
        if agent.team_id not in self._teams:
            self._teams[agent.team_id] = []
        self._teams[agent.team_id].append(agent.agent_id)
    
    def get_agent(self, agent_id: str) -> BaseAgent:
        return self._agents.get(agent_id)
    
    def get_team_agents(self, team_id: str) -> List[BaseAgent]:
        return [self._agents[aid] for aid in self._teams.get(team_id, [])]
    
    def get_teams(self) -> List[str]:
        return list(self._teams.keys())
    
    def count(self) -> int:
        return len(self._agents)

agent_registry = AgentRegistry()

def register_all_agents() -> int:
    """Register all 54 agents."""
    for team_id, agents in AGENT_DEFINITIONS.items():
        for agent_id, agent_name, role in agents:
            agent = GenericAgent(agent_id, agent_name, team_id, role)
            agent_registry.register(agent)
    return agent_registry.count()
```

---

# 7. PHASE 6-8: ADVANCED RAG, KAG, XAI

## 7.1 Hybrid RAG

```python
# backend/app/services/rag/hybrid.py
"""Hybrid RAG with dense + BM25."""

from rank_bm25 import BM25Okapi
from typing import List, Dict
from app.services.rag.vector_store import vector_store

class HybridRAGService:
    """Combines vector and BM25 search."""
    
    def __init__(self):
        self._bm25_indices = {}
        self._corpus = {}
    
    def build_bm25_index(self, collection: str, docs: List[Dict]):
        texts = [d["text"] for d in docs]
        tokenized = [t.lower().split() for t in texts]
        self._bm25_indices[collection] = BM25Okapi(tokenized)
        self._corpus[collection] = docs
    
    async def hybrid_search(
        self, query: str, collection: str, limit: int = 10, alpha: float = 0.5
    ) -> List[Dict]:
        """Search with RRF fusion."""
        # Dense search
        dense = await vector_store.search(collection, query, limit * 2)
        
        # BM25 search
        sparse = self._bm25_search(query, collection, limit * 2)
        
        # RRF fusion
        return self._rrf_fusion(dense, sparse, alpha, limit)
    
    def _bm25_search(self, query: str, collection: str, limit: int) -> List[Dict]:
        if collection not in self._bm25_indices:
            return []
        
        bm25 = self._bm25_indices[collection]
        scores = bm25.get_scores(query.lower().split())
        top_idx = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:limit]
        
        return [{"id": str(i), "score": scores[i], **self._corpus[collection][i]} 
                for i in top_idx if scores[i] > 0]
    
    def _rrf_fusion(self, dense: List, sparse: List, alpha: float, limit: int) -> List:
        scores = {}
        for rank, doc in enumerate(dense):
            scores[doc["id"]] = scores.get(doc["id"], 0) + alpha / (60 + rank)
        for rank, doc in enumerate(sparse):
            scores[doc["id"]] = scores.get(doc["id"], 0) + (1-alpha) / (60 + rank)
        
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        return [{"id": id, "rrf_score": scores[id]} for id in sorted_ids[:limit]]

hybrid_rag = HybridRAGService()
```

## 7.2 XAI Service

```python
# backend/app/xai/explainer.py
"""Gold Team XAI generation."""

from pydantic import BaseModel
from typing import List, Dict
from app.services.openai_service import openai_service
from app.services.rag import rag_service
import json

class ExplanationBundle(BaseModel):
    decision_id: str
    decision_label: str
    risk_score: float
    plain_summary: str
    triggered_rules: List[Dict]
    counterfactuals: List[Dict]
    compliance_tags: List[str]

class XAIService:
    """Explainable AI service."""
    
    async def generate_explanation(self, decision: Dict) -> ExplanationBundle:
        context = await rag_service.build_gold_team_context(
            str(decision.get("rules", "fraud")), 5
        )
        
        prompt = f"""
Explain this fraud detection decision:
Decision: {decision.get('label', 'review')}
Risk: {decision.get('risk_score', 0.5)}
Rules: {decision.get('rules', [])}

Context: {context[:1000]}

Output JSON with: summary, reasons[], counterfactuals[]
"""
        
        response = await openai_service.generate(prompt, json_mode=True)
        data = json.loads(response)
        
        return ExplanationBundle(
            decision_id=decision.get("id", "unknown"),
            decision_label=decision.get("label", "review"),
            risk_score=decision.get("risk_score", 0.5),
            plain_summary=data.get("summary", "Decision based on risk factors."),
            triggered_rules=decision.get("rules", []),
            counterfactuals=data.get("counterfactuals", []),
            compliance_tags=["Data Minimization"]
        )

xai_service = XAIService()
```

---

# 8. PHASE 9: AGENTIC RAG & SELF-RAG

```python
# backend/app/services/rag/agentic.py
"""LangGraph-based Agentic RAG."""

from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Dict
from app.services.rag import rag_service
from app.services.openai_service import openai_service

class AgentState(TypedDict):
    query: str
    docs: List[Dict]
    verified: bool
    answer: str
    trace: List[Dict]

class AgenticRAGService:
    """Agentic RAG with verification."""
    
    def __init__(self):
        self.graph = self._build_graph()
    
    def _build_graph(self):
        graph = StateGraph(AgentState)
        
        graph.add_node("retrieve", self._retrieve)
        graph.add_node("verify", self._verify)
        graph.add_node("generate", self._generate)
        
        graph.set_entry_point("retrieve")
        graph.add_edge("retrieve", "verify")
        graph.add_conditional_edges(
            "verify",
            lambda s: "generate" if s["verified"] else "retrieve",
            {"generate": "generate", "retrieve": "retrieve"}
        )
        graph.add_edge("generate", END)
        
        return graph.compile()
    
    async def _retrieve(self, state: AgentState) -> AgentState:
        docs = await rag_service.find_scenarios(state["query"], 5)
        state["docs"] = docs
        state["trace"].append({"step": "retrieve", "count": len(docs)})
        return state
    
    async def _verify(self, state: AgentState) -> AgentState:
        state["verified"] = len(state["docs"]) >= 2
        state["trace"].append({"step": "verify", "passed": state["verified"]})
        return state
    
    async def _generate(self, state: AgentState) -> AgentState:
        context = "\n".join([d["text"][:200] for d in state["docs"]])
        answer = await openai_service.generate(
            f"Query: {state['query']}\nContext: {context}\nAnswer:",
            system_prompt="Answer based on context only."
        )
        state["answer"] = answer
        state["trace"].append({"step": "generate"})
        return state
    
    async def run(self, query: str) -> Dict:
        result = await self.graph.ainvoke({
            "query": query, "docs": [], "verified": False, "answer": "", "trace": []
        })
        return {"answer": result["answer"], "trace": result["trace"]}

agentic_rag = AgenticRAGService()
```

---

# 9. PHASE 10: WAR LOOP INTEGRATION

```python
# backend/app/services/warloop.py
"""War Loop State Machine."""

from enum import Enum
from typing import Dict, Optional
from app.services.agents.factory import agent_registry
from app.services.agents.base_agent import Task
import uuid

class WarLoopState(Enum):
    RED_SIMULATE = "red_simulate"
    BLUE_DETECT = "blue_detect"
    PURPLE_DIAGNOSE = "purple_diagnose"
    GREEN_BUILD = "green_build"
    BLACK_TEST = "black_test"
    ORANGE_REVIEW = "orange_review"
    WHITE_GOVERNANCE = "white_governance"
    GOLD_EXPLAIN = "gold_explain"
    DONE = "done"

TRANSITIONS = {
    WarLoopState.RED_SIMULATE: WarLoopState.BLUE_DETECT,
    WarLoopState.BLUE_DETECT: WarLoopState.PURPLE_DIAGNOSE,
    WarLoopState.PURPLE_DIAGNOSE: WarLoopState.GREEN_BUILD,
    WarLoopState.GREEN_BUILD: WarLoopState.BLACK_TEST,
    WarLoopState.BLACK_TEST: WarLoopState.ORANGE_REVIEW,
    WarLoopState.ORANGE_REVIEW: WarLoopState.WHITE_GOVERNANCE,
    WarLoopState.WHITE_GOVERNANCE: WarLoopState.GOLD_EXPLAIN,
    WarLoopState.GOLD_EXPLAIN: WarLoopState.DONE,
}

class WarLoopEngine:
    """Execute the War Loop."""
    
    def __init__(self):
        self.state = WarLoopState.RED_SIMULATE
        self.run_id: Optional[str] = None
        self.artifacts = {}
    
    async def start(self, scenario_id: str, seed: str) -> str:
        self.run_id = f"run_{uuid.uuid4().hex[:8]}"
        self.state = WarLoopState.RED_SIMULATE
        self.artifacts = {}
        return self.run_id
    
    async def step(self) -> Dict:
        team_id = self.state.value.split("_")[0]
        orchestrator = agent_registry.get_agent(f"{team_id}.agent.01")
        
        if orchestrator:
            task = Task(
                task_id=f"task_{self.run_id}_{self.state.value}",
                run_id=self.run_id,
                team_id=team_id,
                task_type=self.state.value
            )
            result = await orchestrator.run(task)
            self.artifacts[self.state.value] = result.outputs
        
        prev = self.state
        self.state = TRANSITIONS.get(self.state, WarLoopState.DONE)
        
        return {
            "run_id": self.run_id,
            "previous": prev.value,
            "current": self.state.value,
            "done": self.state == WarLoopState.DONE
        }
    
    async def run_full(self) -> Dict:
        steps = []
        while self.state != WarLoopState.DONE:
            steps.append(await self.step())
        return {"run_id": self.run_id, "steps": steps}

war_loop = WarLoopEngine()
```

---

# 10. PHASE 11-12: TESTING & DEMO

## 10.1 Demo Runner

```python
# backend/scripts/demo_run.py
"""One-click demo runner."""

import asyncio
from app.services.rag import rag_service
from app.services.agents.factory import register_all_agents, agent_registry
from app.services.warloop import war_loop

async def run_demo():
    print("=" * 60)
    print("🎯 FRAUD FORGE DEMO RUN")
    print("=" * 60)
    
    print("\n1. Initializing RAG...")
    await rag_service.initialize()
    
    print("\n2. Registering agents...")
    count = register_all_agents()
    print(f"   ✓ {count} agents registered")
    print(f"   Teams: {agent_registry.get_teams()}")
    
    print("\n3. Starting War Loop...")
    run_id = await war_loop.start("demo", "seed001")
    print(f"   Run ID: {run_id}")
    
    print("\n4. Executing stages...")
    result = await war_loop.run_full()
    
    for step in result["steps"]:
        print(f"   ✓ {step['previous']} → {step['current']}")
    
    print("\n" + "=" * 60)
    print("✅ DEMO COMPLETE!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_demo())
```

---

# 11. QUICK START COMMANDS

```bash
# 1. Setup
cd fraud-forge/backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env: add OPENAI_API_KEY

# 2. Start services
docker-compose up -d chromadb

# 3. Test LLM
python scripts/test_llm.py

# 4. Seed RAG
python scripts/seed_rag.py

# 5. Register agents
python -c "from app.services.agents.factory import register_all_agents; print(f'{register_all_agents()} agents')"

# 6. Run demo
python scripts/demo_run.py

# 7. Start API
uvicorn app.main:app --reload --port 8000
```

---

# 12. API ENDPOINTS REFERENCE

```python
# backend/app/api/routes/rag.py
from fastapi import APIRouter

router = APIRouter(prefix="/api/rag", tags=["RAG"])

@router.get("/stats")
async def get_stats():
    from app.services.rag import rag_service
    return await rag_service.get_stats()

@router.post("/search")
async def search(collection: str, query: str, limit: int = 5):
    from app.services.rag import rag_service
    return await rag_service.find_scenarios(query, limit)

@router.post("/context/{team}")
async def build_context(team: str, query: str):
    from app.services.rag import rag_service
    if team == "red":
        return await rag_service.build_red_team_context(query, 5)
    elif team == "blue":
        return await rag_service.build_blue_team_context(query, 5)
    return await rag_service.build_gold_team_context(query, 5)
```

```python
# backend/app/api/routes/agents.py
from fastapi import APIRouter

router = APIRouter(prefix="/api/agents", tags=["Agents"])

@router.get("/")
async def list_agents():
    from app.services.agents.factory import agent_registry
    return {"count": agent_registry.count(), "teams": agent_registry.get_teams()}

@router.get("/team/{team_id}")
async def get_team(team_id: str):
    from app.services.agents.factory import agent_registry
    agents = agent_registry.get_team_agents(team_id)
    return [{"id": a.agent_id, "name": a.agent_name, "role": a.role} for a in agents]
```

```python
# backend/app/api/routes/warloop.py
from fastapi import APIRouter

router = APIRouter(prefix="/api/warloop", tags=["War Loop"])

@router.post("/start")
async def start_run(scenario_id: str = "demo", seed: str = "001"):
    from app.services.warloop import war_loop
    run_id = await war_loop.start(scenario_id, seed)
    return {"run_id": run_id}

@router.post("/step")
async def step_run():
    from app.services.warloop import war_loop
    return await war_loop.step()

@router.post("/run")
async def full_run():
    from app.services.warloop import war_loop
    return await war_loop.run_full()
```

---

# 📋 IMPLEMENTATION CHECKLIST

- [ ] Phase 0: Project structure + dependencies
- [ ] Phase 1: OpenAI service (generation, streaming, embeddings)
- [ ] Phase 2: ChromaDB + 7 collections + seeding
- [ ] Phase 3: BaseAgent + AgentRegistry
- [ ] Phase 4: 8 Team Orchestrators
- [ ] Phase 5: 54 Agents registered
- [ ] Phase 6: Hybrid RAG (vector + BM25)
- [ ] Phase 7: GraphRAG with Neo4j
- [ ] Phase 8: XAI Pipeline
- [ ] Phase 9: Agentic RAG + Self-RAG
- [ ] Phase 10: War Loop state machine
- [ ] Phase 11: Evaluation metrics
- [ ] Phase 12: Demo mode + replay

---

**Document Version:** 3.0  
**Status:** READY FOR IMPLEMENTATION  
**Target:** 100% Hackathon Victory

# 🚀 BUILD THE AI THAT NEVER LETS FRAUD WIN TWICE!
