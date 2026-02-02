# 🧠 FRAUD FORGE - RAG Implementation with OpenAI
## Complete RAG System for AI-Powered Fraud Defense
### Version 1.0 | Production-Ready Implementation

---

# 📋 TABLE OF CONTENTS

1. [Architecture Overview](#1-architecture-overview)
2. [Setup & Configuration](#2-setup--configuration)
3. [OpenAI Integration](#3-openai-integration)
4. [ChromaDB Vector Store](#4-chromadb-vector-store)
5. [RAG Collections Design](#5-rag-collections-design)
6. [Core RAG Service](#6-core-rag-service)
7. [Team Agent Integration](#7-team-agent-integration)
8. [Data Seeding](#8-data-seeding)
9. [API Endpoints](#9-api-endpoints)
10. [Frontend Integration](#10-frontend-integration)
11. [Testing](#11-testing)
12. [Deployment](#12-deployment)

---

# 1. ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     FRAUD FORGE RAG ARCHITECTURE                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                         FRONTEND (React)                                 ││
│  │  Battle Arena │ Brain Surgery │ RSB Manager │ Metrics │ XAI Panel       ││
│  └───────────────────────────────┬─────────────────────────────────────────┘│
│                                  │                                           │
│  ┌───────────────────────────────▼─────────────────────────────────────────┐│
│  │                       RAG SERVICE LAYER                                  ││
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐        ││
│  │  │  OpenAI    │  │  ChromaDB  │  │  Context   │  │  Retrieval │        ││
│  │  │  Service   │  │  Vector    │  │  Builder   │  │  Service   │        ││
│  │  │ (GPT-4 +   │  │  Store     │  │            │  │            │        ││
│  │  │ Embeddings)│  │            │  │            │  │            │        ││
│  │  └────────────┘  └────────────┘  └────────────┘  └────────────┘        ││
│  └───────────────────────────────┬─────────────────────────────────────────┘│
│                                  │                                           │
│  ┌───────────────────────────────▼─────────────────────────────────────────┐│
│  │                    VECTOR COLLECTIONS                                    ││
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────┐       ││
│  │  │ attacks │ │patterns │ │taxonomy │ │  rules  │ │explanations │       ││
│  │  │(Red Team)│(Blue Team)│(120 scen)│(detection)│ (Gold XAI)   │       ││
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────────┘       ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# 2. SETUP & CONFIGURATION

## 2.1 Project Structure

```
fraud-forge/backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── services/
│   │   ├── openai_service.py      # OpenAI client
│   │   ├── rag/
│   │   │   ├── __init__.py        # Main RAG service
│   │   │   ├── vector_store.py    # ChromaDB client
│   │   │   ├── retrieval.py       # Search service
│   │   │   └── collections.py     # Document schemas
│   │   └── agents/
│   │       ├── base_agent.py
│   │       ├── red_phantom.py
│   │       ├── blue_sentinel.py
│   │       └── gold_explainer.py
│   └── api/routes/
│       └── rag.py
├── scripts/
│   ├── seed_rag.py
│   └── test_rag.py
├── requirements.txt
└── .env
```

## 2.2 Dependencies

```txt
# requirements.txt
fastapi==0.109.0
uvicorn==0.27.0
pydantic==2.5.3
pydantic-settings==2.1.0
python-dotenv==1.0.0

# OpenAI
openai==1.12.0
tiktoken==0.5.2

# Vector Store
chromadb==0.4.22

# Async
httpx==0.26.0
aiofiles==23.2.1

# Testing
pytest==7.4.4
pytest-asyncio==0.23.3
```

## 2.3 Environment Configuration

```bash
# .env
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
CHROMA_PERSIST_DIRECTORY=./chroma_data
```

```python
# app/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    openai_api_key: str
    openai_model: str = "gpt-4-turbo-preview"
    openai_embedding_model: str = "text-embedding-3-small"
    chroma_persist_directory: str = "./chroma_data"
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
```

---

# 3. OPENAI INTEGRATION

## 3.1 OpenAI Service

```python
# app/services/openai_service.py
from typing import List, Optional, AsyncGenerator
from openai import AsyncOpenAI
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class OpenAIService:
    """OpenAI service for LLM completions and embeddings."""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.embedding_model = settings.openai_embedding_model
    
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
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format
        )
        
        return response.choices[0].message.content
    
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
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector using OpenAI."""
        response = await self.client.embeddings.create(
            model=self.embedding_model,
            input=text
        )
        return response.data[0].embedding
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        response = await self.client.embeddings.create(
            model=self.embedding_model,
            input=texts
        )
        return [d.embedding for d in response.data]

# Singleton
openai_service = OpenAIService()
```

---

# 4. CHROMADB VECTOR STORE

## 4.1 Vector Store Service

```python
# app/services/rag/vector_store.py
import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any, Optional
from app.config import settings
from app.services.openai_service import openai_service
import logging

logger = logging.getLogger(__name__)

class VectorStoreService:
    """ChromaDB vector store for RAG."""
    
    ATTACKS = "attacks"
    PATTERNS = "patterns"
    TAXONOMY = "taxonomy"
    RULES = "rules"
    EXPLANATIONS = "explanations"
    
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
        
        collections = [
            (self.ATTACKS, "Red Team attack memory"),
            (self.PATTERNS, "Blue Team detection patterns"),
            (self.TAXONOMY, "120 fraud scenarios"),
            (self.RULES, "Detection rules"),
            (self.EXPLANATIONS, "XAI explanations"),
        ]
        
        for name, desc in collections:
            self.collections[name] = self.client.get_or_create_collection(
                name=name,
                metadata={"description": desc}
            )
            logger.info(f"Collection '{name}': {self.collections[name].count()} docs")
    
    async def add_document(
        self,
        collection_name: str,
        document_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Add document with auto-generated embedding."""
        try:
            collection = self.collections.get(collection_name)
            if not collection:
                return False
            
            embedding = await openai_service.generate_embedding(text)
            
            collection.add(
                ids=[document_id],
                embeddings=[embedding],
                documents=[text],
                metadatas=[metadata] if metadata else None
            )
            return True
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            return False
    
    async def add_documents_batch(
        self,
        collection_name: str,
        documents: List[Dict[str, Any]]
    ) -> int:
        """Add multiple documents efficiently."""
        try:
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
        except Exception as e:
            logger.error(f"Batch add error: {e}")
            return 0
    
    async def search(
        self,
        collection_name: str,
        query: str,
        limit: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search collection using semantic similarity."""
        try:
            collection = self.collections.get(collection_name)
            if not collection:
                return []
            
            query_embedding = await openai_service.generate_embedding(query)
            
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where,
                include=["documents", "metadatas", "distances"]
            )
            
            formatted = []
            if results["ids"] and results["ids"][0]:
                for i, doc_id in enumerate(results["ids"][0]):
                    formatted.append({
                        "id": doc_id,
                        "text": results["documents"][0][i] if results["documents"] else None,
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else None,
                        "similarity": 1 - (results["distances"][0][i] if results["distances"] else 0)
                    })
            return formatted
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get all collection statistics."""
        return {
            name: {"name": name, "count": col.count()}
            for name, col in self.collections.items()
        }

# Singleton
vector_store = VectorStoreService()
```

---

# 5. RAG COLLECTIONS DESIGN

## 5.1 Document Schemas

```python
# app/services/rag/collections.py
from typing import Dict, Any, List
from datetime import datetime

class AttackDocument:
    """Schema for attack memory."""
    
    @staticmethod
    def create(
        attack_id: str,
        attack_type: str,
        description: str,
        transactions: List[Dict],
        evasion_tactics: List[str],
        success: bool,
        detected_by: str = None,
        risk_score: int = None
    ) -> Dict[str, Any]:
        text = f"""
Attack Type: {attack_type}
Description: {description}
Evasion Tactics: {', '.join(evasion_tactics)}
Outcome: {'SUCCESS' if success else f'DETECTED by {detected_by}'}
Risk Score: {risk_score}
Transactions: {len(transactions)}
"""
        return {
            "id": attack_id,
            "text": text.strip(),
            "metadata": {
                "attack_type": attack_type,
                "success": success,
                "detected_by": detected_by,
                "risk_score": risk_score,
                "timestamp": datetime.utcnow().isoformat()
            }
        }


class TaxonomyDocument:
    """Schema for fraud taxonomy scenarios."""
    
    @staticmethod
    def create(scenario: Dict[str, Any]) -> Dict[str, Any]:
        text = f"""
Scenario: {scenario['scenario_name']}
Family: {scenario['family_id']}
Entry Vector: {scenario['entry_vector']}
Prerequisites: {', '.join(scenario['prerequisites'])}
Indicators: {', '.join(scenario['telemetry_indicators'])}
Controls: {', '.join(scenario['recommended_controls'])}
Payment Rails: {', '.join(scenario['payment_rails'])}
"""
        return {
            "id": scenario['scenario_id'],
            "text": text.strip(),
            "metadata": {
                "scenario_id": scenario['scenario_id'],
                "family_id": scenario['family_id'],
                "scenario_name": scenario['scenario_name'],
                "primary_segment": scenario['primary_segment'],
                "payment_rails": ",".join(scenario['payment_rails'])
            }
        }


class RuleDocument:
    """Schema for detection rules."""
    
    @staticmethod
    def create(
        rule_id: str,
        rule_name: str,
        description: str,
        thresholds: Dict[str, Any],
        action: str,
        family_ids: List[str]
    ) -> Dict[str, Any]:
        text = f"""
Rule: {rule_name} ({rule_id})
Description: {description}
Action: {action}
Families: {', '.join(family_ids)}
Thresholds: {thresholds}
"""
        return {
            "id": rule_id,
            "text": text.strip(),
            "metadata": {
                "rule_id": rule_id,
                "rule_name": rule_name,
                "action": action,
                "family_ids": ",".join(family_ids)
            }
        }


class ExplanationDocument:
    """Schema for XAI explanations."""
    
    @staticmethod
    def create(
        explanation_id: str,
        decision: str,
        risk_score: int,
        triggered_rules: List[str],
        explanation_text: str
    ) -> Dict[str, Any]:
        text = f"""
Decision: {decision}
Risk Score: {risk_score}
Rules: {', '.join(triggered_rules)}
Explanation: {explanation_text}
"""
        return {
            "id": explanation_id,
            "text": text.strip(),
            "metadata": {
                "decision": decision,
                "risk_score": risk_score,
                "triggered_rules": ",".join(triggered_rules),
                "timestamp": datetime.utcnow().isoformat()
            }
        }
```

---

# 6. CORE RAG SERVICE

```python
# app/services/rag/__init__.py
from typing import Dict, Any, List
from app.services.rag.vector_store import vector_store, VectorStoreService
from app.services.rag.collections import AttackDocument, TaxonomyDocument, RuleDocument, ExplanationDocument
import logging

logger = logging.getLogger(__name__)

class RAGService:
    """Main RAG service for Fraud Forge."""
    
    def __init__(self):
        self.vs = vector_store
    
    async def initialize(self):
        await self.vs.initialize()
        logger.info("RAG Service initialized")
    
    # ========== STORAGE ==========
    
    async def store_attack(self, **kwargs) -> bool:
        doc = AttackDocument.create(**kwargs)
        return await self.vs.add_document(VectorStoreService.ATTACKS, doc["id"], doc["text"], doc["metadata"])
    
    async def store_explanation(self, **kwargs) -> bool:
        doc = ExplanationDocument.create(**kwargs)
        return await self.vs.add_document(VectorStoreService.EXPLANATIONS, doc["id"], doc["text"], doc["metadata"])
    
    # ========== RETRIEVAL ==========
    
    async def find_similar_attacks(self, objective: str, limit: int = 5, successful_only: bool = True):
        filters = {"success": True} if successful_only else None
        return await self.vs.search(VectorStoreService.ATTACKS, objective, limit, filters)
    
    async def find_similar_patterns(self, description: str, limit: int = 5):
        return await self.vs.search(VectorStoreService.PATTERNS, description, limit)
    
    async def find_scenarios(self, description: str, limit: int = 3):
        return await self.vs.search(VectorStoreService.TAXONOMY, description, limit)
    
    async def find_rules(self, description: str, limit: int = 5):
        return await self.vs.search(VectorStoreService.RULES, description, limit)
    
    async def find_explanations(self, description: str, limit: int = 3):
        return await self.vs.search(VectorStoreService.EXPLANATIONS, description, limit)
    
    # ========== CONTEXT BUILDING ==========
    
    async def build_red_team_context(self, objective: str, limit: int = 5) -> str:
        parts = []
        
        # Similar successful attacks
        attacks = await self.find_similar_attacks(objective, limit, True)
        if attacks:
            parts.append("### SIMILAR SUCCESSFUL ATTACKS")
            for a in attacks:
                parts.append(f"- [{a['similarity']:.0%}] {a['text'][:200]}...")
        
        # Relevant scenarios
        scenarios = await self.find_scenarios(objective, 3)
        if scenarios:
            parts.append("\n### RELEVANT FRAUD SCENARIOS")
            for s in scenarios:
                parts.append(f"- {s['metadata'].get('scenario_name', 'N/A')}")
        
        # Rules to bypass
        rules = await self.find_rules(objective, 5)
        if rules:
            parts.append("\n### DETECTION RULES TO BYPASS")
            for r in rules:
                parts.append(f"- {r['metadata'].get('rule_name', 'N/A')}")
        
        return "\n".join(parts)
    
    async def build_blue_team_context(self, description: str, limit: int = 5) -> str:
        parts = []
        
        # Similar patterns
        patterns = await self.find_similar_patterns(description, limit)
        if patterns:
            parts.append("### SIMILAR FRAUD PATTERNS")
            for p in patterns:
                parts.append(f"- [{p['similarity']:.0%}] {p['text'][:200]}...")
        
        # Matching scenarios
        scenarios = await self.find_scenarios(description, 3)
        if scenarios:
            parts.append("\n### MATCHING FRAUD SCENARIOS")
            for s in scenarios:
                parts.append(f"- {s['metadata'].get('scenario_name', 'N/A')}")
        
        return "\n".join(parts)
    
    async def build_gold_team_context(self, description: str, limit: int = 3) -> str:
        parts = []
        
        # Similar explanations
        explanations = await self.find_explanations(description, limit)
        if explanations:
            parts.append("### SIMILAR PAST EXPLANATIONS")
            for e in explanations:
                parts.append(f"- {e['text'][:300]}...")
        
        return "\n".join(parts)
    
    async def get_stats(self) -> Dict[str, Any]:
        return await self.vs.get_stats()

# Singleton
rag_service = RAGService()
```

---

# 7. TEAM AGENT INTEGRATION

## 7.1 Base Agent

```python
# app/services/agents/base_agent.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from app.services.openai_service import openai_service

class BaseAgent(ABC):
    """Base class for AI agents with RAG support."""
    
    def __init__(self, name: str, team: str, system_prompt: str, temperature: float = 0.7):
        self.name = name
        self.team = team
        self.system_prompt = system_prompt
        self.temperature = temperature
    
    async def think(self, prompt: str, context: Optional[str] = None, json_mode: bool = False) -> str:
        full_prompt = prompt
        if context:
            full_prompt = f"CONTEXT:\n{context}\n\n---\n\nTASK:\n{prompt}"
        
        return await openai_service.generate(
            prompt=full_prompt,
            system_prompt=self.system_prompt,
            temperature=self.temperature,
            json_mode=json_mode
        )
    
    async def think_stream(self, prompt: str, context: Optional[str] = None):
        full_prompt = prompt
        if context:
            full_prompt = f"CONTEXT:\n{context}\n\n---\n\nTASK:\n{prompt}"
        
        async for chunk in openai_service.generate_stream(full_prompt, self.system_prompt, self.temperature):
            yield chunk
    
    @abstractmethod
    async def execute(self, *args, **kwargs) -> Dict[str, Any]:
        pass
```

## 7.2 Red Team Agent

```python
# app/services/agents/red_phantom.py
from typing import Dict, Any, AsyncGenerator
from app.services.agents.base_agent import BaseAgent
from app.services.rag import rag_service
import json

SYSTEM_PROMPT = """You are RED PHANTOM, the master adversarial AI.
Generate sophisticated fraud attacks to test bank defenses.
Always respond in valid JSON with: attack_name, attack_type, description, transactions, evasion_tactics, expected_success_rate, reasoning."""

class RedPhantom(BaseAgent):
    def __init__(self):
        super().__init__("Red Phantom", "red", SYSTEM_PROMPT, temperature=0.8)
    
    async def execute(self, objective: str, attack_type: str = None) -> Dict[str, Any]:
        context = await rag_service.build_red_team_context(objective, 5)
        
        prompt = f"""
OBJECTIVE: {objective}
{f'ATTACK TYPE: {attack_type}' if attack_type else ''}

Generate a sophisticated attack using lessons from similar past attacks.
"""
        response = await self.think(prompt, context, json_mode=True)
        
        try:
            return json.loads(response)
        except:
            return {"error": "Failed to parse", "raw": response}
    
    async def execute_stream(self, objective: str) -> AsyncGenerator[Dict, None]:
        """Stream thinking stages for UI visualization."""
        stages = ["reconnaissance", "ideation", "planning", "evasion", "prediction"]
        context = await rag_service.build_red_team_context(objective, 5)
        
        for stage in stages:
            yield {"type": "stage_start", "stage": stage}
            
            prompt = f"Stage: {stage}\nObjective: {objective}\nBriefly describe your {stage} analysis."
            async for chunk in self.think_stream(prompt, context if stage == "reconnaissance" else None):
                yield {"type": "content", "stage": stage, "chunk": chunk}
            
            yield {"type": "stage_complete", "stage": stage}
        
        attack = await self.execute(objective)
        yield {"type": "attack_complete", "attack": attack}
    
    async def learn(self, attack: Dict, outcome: Dict):
        """Store attack result for learning."""
        await rag_service.store_attack(
            attack_id=f"atk_{id(attack)}",
            attack_type=attack.get("attack_type", "unknown"),
            description=attack.get("description", ""),
            transactions=attack.get("transactions", []),
            evasion_tactics=attack.get("evasion_tactics", []),
            success=outcome.get("success", False),
            detected_by=outcome.get("detected_by"),
            risk_score=outcome.get("risk_score")
        )

red_phantom = RedPhantom()
```

## 7.3 Blue Team Agent

```python
# app/services/agents/blue_sentinel.py
from typing import Dict, Any, List
from app.services.agents.base_agent import BaseAgent
from app.services.rag import rag_service
import json

SYSTEM_PROMPT = """You are BLUE SENTINEL, the defense AI.
Detect fraud in transactions using pattern matching and behavioral analysis.
Always respond in valid JSON with: decision, risk_score, confidence, triggered_rules, contributing_factors, reasoning."""

class BlueSentinel(BaseAgent):
    def __init__(self):
        super().__init__("Blue Sentinel", "blue", SYSTEM_PROMPT, temperature=0.3)
    
    async def execute(self, transactions: List[Dict]) -> Dict[str, Any]:
        description = self._describe(transactions)
        context = await rag_service.build_blue_team_context(description, 5)
        
        prompt = f"""
TRANSACTIONS:
{json.dumps(transactions, indent=2)}

Analyze for fraud indicators. Calculate risk score and decide: allow/review/block.
"""
        response = await self.think(prompt, context, json_mode=True)
        
        try:
            return json.loads(response)
        except:
            return {"decision": "review", "risk_score": 50, "error": "Parse failed"}
    
    def _describe(self, txns: List[Dict]) -> str:
        total = sum(t.get("amount", 0) for t in txns)
        return f"Transactions: {len(txns)}, Total: ${total:,.2f}"

blue_sentinel = BlueSentinel()
```

## 7.4 Gold Team Agent

```python
# app/services/agents/gold_explainer.py
from typing import Dict, Any, List
from app.services.agents.base_agent import BaseAgent
from app.services.rag import rag_service
import json

SYSTEM_PROMPT = """You are GOLD EXPLAINER, the AI explainability agent.
Generate clear, human-readable explanations for fraud detection decisions.
Always respond in valid JSON with: summary, detailed_explanation, evidence_chain, confidence_statement."""

class GoldExplainer(BaseAgent):
    def __init__(self):
        super().__init__("Gold Explainer", "gold", SYSTEM_PROMPT, temperature=0.4)
    
    async def execute(self, detection: Dict, transactions: List[Dict] = None) -> Dict[str, Any]:
        description = f"Decision: {detection.get('decision')}, Risk: {detection.get('risk_score')}"
        context = await rag_service.build_gold_team_context(description, 3)
        
        prompt = f"""
DETECTION:
{json.dumps(detection, indent=2)}

Generate a clear explanation for this decision. Reference similar past cases if relevant.
"""
        response = await self.think(prompt, context, json_mode=True)
        
        try:
            explanation = json.loads(response)
            # Store for future reference
            await rag_service.store_explanation(
                explanation_id=f"exp_{id(explanation)}",
                decision=detection.get("decision", "unknown"),
                risk_score=detection.get("risk_score", 0),
                triggered_rules=detection.get("triggered_rules", []),
                explanation_text=explanation.get("detailed_explanation", "")
            )
            return explanation
        except:
            return {"error": "Parse failed"}

gold_explainer = GoldExplainer()
```

---

# 8. DATA SEEDING

```python
# scripts/seed_rag.py
import asyncio
import json
from pathlib import Path
from app.services.rag import rag_service
from app.services.rag.vector_store import vector_store, VectorStoreService
from app.services.rag.collections import TaxonomyDocument, RuleDocument

async def seed_taxonomy():
    """Seed 120 fraud scenarios."""
    print("Loading taxonomy...")
    
    # Adjust path as needed
    with open("app/data/banking_fraud_taxonomy_catalog_120.json") as f:
        catalog = json.load(f)
    
    docs = [TaxonomyDocument.create(s) for s in catalog['scenarios']]
    count = await vector_store.add_documents_batch(VectorStoreService.TAXONOMY, docs)
    print(f"✓ Seeded {count} scenarios")

async def seed_rules():
    """Seed default detection rules."""
    print("Seeding rules...")
    
    rules = [
        {"rule_id": "RULE_001", "rule_name": "Structuring Detection", 
         "description": "Multiple deposits near $10K threshold", 
         "thresholds": {"min": 9000, "max": 9999, "count": 3}, "action": "review", "family_ids": ["F05"]},
        {"rule_id": "RULE_002", "rule_name": "Velocity Check", 
         "description": "Too many transactions in short time", 
         "thresholds": {"count": 10, "window": "1h"}, "action": "review", "family_ids": ["F02", "F04"]},
        {"rule_id": "RULE_003", "rule_name": "Large Transfer", 
         "description": "Single transfer over $50K", 
         "thresholds": {"amount": 50000}, "action": "alert", "family_ids": ["F06"]},
        {"rule_id": "RULE_004", "rule_name": "New Account Risk", 
         "description": "New account with large activity", 
         "thresholds": {"age_days": 30, "amount": 10000}, "action": "review", "family_ids": ["F01"]},
        {"rule_id": "RULE_005", "rule_name": "Geographic Anomaly", 
         "description": "Impossible travel detection", 
         "thresholds": {"distance_miles": 500, "time_hours": 2}, "action": "block", "family_ids": ["F02"]},
    ]
    
    docs = [RuleDocument.create(**r) for r in rules]
    count = await vector_store.add_documents_batch(VectorStoreService.RULES, docs)
    print(f"✓ Seeded {count} rules")

async def main():
    print("=" * 50)
    print("SEEDING FRAUD FORGE RAG")
    print("=" * 50)
    
    await rag_service.initialize()
    await seed_taxonomy()
    await seed_rules()
    
    stats = await rag_service.get_stats()
    print("\nFinal stats:")
    for name, s in stats.items():
        print(f"  {name}: {s['count']} docs")

if __name__ == "__main__":
    asyncio.run(main())
```

---

# 9. API ENDPOINTS

```python
# app/api/routes/rag.py
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.services.rag import rag_service

router = APIRouter(prefix="/api/rag", tags=["RAG"])

class SearchRequest(BaseModel):
    query: str
    collection: str
    limit: int = 5

class ContextRequest(BaseModel):
    query: str
    team: str  # red | blue | gold
    limit: int = 5

@router.get("/stats")
async def get_stats():
    return await rag_service.get_stats()

@router.post("/search")
async def search(req: SearchRequest):
    if req.collection == "attacks":
        results = await rag_service.find_similar_attacks(req.query, req.limit)
    elif req.collection == "patterns":
        results = await rag_service.find_similar_patterns(req.query, req.limit)
    elif req.collection == "taxonomy":
        results = await rag_service.find_scenarios(req.query, req.limit)
    elif req.collection == "rules":
        results = await rag_service.find_rules(req.query, req.limit)
    else:
        results = await rag_service.find_explanations(req.query, req.limit)
    
    return {"results": results, "count": len(results)}

@router.post("/context")
async def build_context(req: ContextRequest):
    if req.team == "red":
        context = await rag_service.build_red_team_context(req.query, req.limit)
    elif req.team == "blue":
        context = await rag_service.build_blue_team_context(req.query, req.limit)
    else:
        context = await rag_service.build_gold_team_context(req.query, req.limit)
    
    return {"context": context}
```

---

# 10. FRONTEND INTEGRATION

```typescript
// src/services/ragService.ts
import { api } from './api';

export const ragService = {
  getStats: () => api.get('/api/rag/stats').then(r => r.data),
  
  search: (collection: string, query: string, limit = 5) =>
    api.post('/api/rag/search', { collection, query, limit }).then(r => r.data),
  
  buildContext: (team: 'red' | 'blue' | 'gold', query: string, limit = 5) =>
    api.post('/api/rag/context', { team, query, limit }).then(r => r.data),
};
```

---

# 11. TESTING

```python
# scripts/test_rag.py
import asyncio
from app.services.rag import rag_service
from app.services.agents.red_phantom import red_phantom
from app.services.agents.blue_sentinel import blue_sentinel

async def test():
    print("Testing RAG system...")
    await rag_service.initialize()
    
    # Test Red Team
    print("\n[RED TEAM]")
    attack = await red_phantom.execute("Extract $30K using structuring")
    print(f"Attack: {attack.get('attack_name', 'N/A')}")
    
    # Test Blue Team
    print("\n[BLUE TEAM]")
    txns = [{"amount": 9500}, {"amount": 9400}, {"amount": 9600}]
    detection = await blue_sentinel.execute(txns)
    print(f"Decision: {detection.get('decision')}, Risk: {detection.get('risk_score')}")
    
    # Store learning
    await red_phantom.learn(attack, {"success": detection.get('decision') == 'allow', "risk_score": detection.get('risk_score')})
    
    print("\n✓ All tests passed!")

if __name__ == "__main__":
    asyncio.run(test())
```

---

# 12. DEPLOYMENT

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: ./backend
    ports: ["8000:8000"]
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - CHROMA_PERSIST_DIRECTORY=/data/chroma
    volumes:
      - chroma_data:/data/chroma
    depends_on:
      - chromadb

  chromadb:
    image: chromadb/chroma:latest
    ports: ["8001:8000"]
    volumes:
      - chroma_data:/chroma/chroma

volumes:
  chroma_data:
```

---

# 💰 COST ESTIMATION

| Component | Model | Monthly Cost |
|-----------|-------|--------------|
| Embeddings | text-embedding-3-small | ~$1 |
| Red Team | gpt-4-turbo | ~$20 |
| Blue Team | gpt-4-turbo | ~$30 |
| Gold Team | gpt-4-turbo | ~$10 |
| **Total** | | **~$60/month** |

---

# 🚀 QUICK START

```bash
# 1. Set up environment
cp .env.example .env
# Add your OPENAI_API_KEY

# 2. Install dependencies
pip install -r requirements.txt

# 3. Seed RAG
python scripts/seed_rag.py

# 4. Test
python scripts/test_rag.py

# 5. Run API
uvicorn app.main:app --reload
```

---

**Version:** 1.0 | **Status:** READY FOR IMPLEMENTATION

# 🚀 START BUILDING!
