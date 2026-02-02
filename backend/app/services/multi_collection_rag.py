"""
5-Collection RAG Architecture Service

Implements the multi-collection RAG system with dedicated collections for:
1. attacks - Red Team offensive memory (successful attack vectors)
2. patterns - Blue Team defensive patterns (detection signatures)  
3. taxonomy - Static fraud scenarios (120 banking fraud taxonomy)
4. rules - Active rule code index (deployed detection rules)
5. explanations - Gold Team XAI outputs (past explanations)

This architecture enables specialized retrieval for each team's needs,
improving both accuracy and relevance of the RAG system.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.external_services import DatabaseClient, LLMClient
from app.core.logging_config import get_logger
from app.rag_utils import get_embedding, simple_embed

logger = get_logger(__name__)


# Collection definitions with metadata
RAG_COLLECTION_SCHEMA = {
    "attacks": {
        "name": "attacks",
        "display_name": "Attack Vectors",
        "description": "Red Team offensive memory - successful attack vectors and techniques",
        "team": "red",
        "color": "#FF4444",
        "icon": "⚔️",
        "retention_days": 365,
        "auto_learn": True
    },
    "patterns": {
        "name": "patterns", 
        "display_name": "Defense Patterns",
        "description": "Blue Team defensive patterns - detection signatures and blocking rules",
        "team": "blue",
        "color": "#4444FF",
        "icon": "🛡️",
        "retention_days": 365,
        "auto_learn": True
    },
    "taxonomy": {
        "name": "taxonomy",
        "display_name": "Fraud Taxonomy",
        "description": "120 banking fraud scenarios - static reference for attack simulation",
        "team": "all",
        "color": "#9944FF",
        "icon": "📚",
        "retention_days": None,  # Permanent
        "auto_learn": False
    },
    "rules": {
        "name": "rules",
        "display_name": "Rule Index",
        "description": "Active detection rules - indexed for RAG retrieval",
        "team": "purple",
        "color": "#44FF44",
        "icon": "⚙️",
        "retention_days": None,
        "auto_learn": False
    },
    "explanations": {
        "name": "explanations",
        "display_name": "XAI Explanations",
        "description": "Gold Team explanations - past decision rationales for consistency",
        "team": "gold",
        "color": "#FFD700",
        "icon": "💡",
        "retention_days": 180,
        "auto_learn": True
    }
}


class MultiCollectionRAGService:
    """
    Multi-collection RAG service implementing the 5-collection architecture.
    
    Each collection serves a specific purpose and team within Fraud Forge,
    enabling specialized retrieval and learning capabilities.
    """
    
    def __init__(self, db: DatabaseClient, llm_client: Optional[LLMClient] = None):
        self.db = db
        self.llm_client = llm_client
        self.collections = RAG_COLLECTION_SCHEMA
    
    async def initialize_collections(self) -> Dict[str, Any]:
        """
        Initialize all 5 RAG collections with their schemas and indexes.
        
        Returns:
            Dict with initialization results for each collection
        """
        results = {}
        
        for collection_name, schema in self.collections.items():
            try:
                # Create collection metadata document
                meta_doc = {
                    "collection_id": collection_name,
                    "schema": schema,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "document_count": 0,
                    "last_updated": datetime.now(timezone.utc).isoformat()
                }
                
                # Upsert collection metadata
                await self.db.rag_collection_meta.update_one(
                    {"collection_id": collection_name},
                    {"$set": meta_doc},
                    upsert=True
                )
                
                results[collection_name] = {
                    "status": "initialized",
                    "schema": schema
                }
                
                logger.info(
                    f"rag.collection.initialized",
                    extra={"payload": {"collection": collection_name}}
                )
                
            except Exception as e:
                results[collection_name] = {
                    "status": "error",
                    "error": str(e)
                }
                logger.error(
                    f"rag.collection.init_failed",
                    extra={"payload": {"collection": collection_name, "error": str(e)}}
                )
        
        return results
    
    async def add_document(
        self,
        collection: str,
        title: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        generate_embedding: bool = True
    ) -> Dict[str, Any]:
        """
        Add a document to a specific collection.
        
        Args:
            collection: Target collection name
            title: Document title
            content: Document content
            metadata: Optional metadata
            generate_embedding: Whether to generate embedding
            
        Returns:
            Dict with document ID and status
        """
        if collection not in self.collections:
            raise ValueError(f"Invalid collection: {collection}. Valid: {list(self.collections.keys())}")
        
        doc_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Generate embedding
        if generate_embedding:
            embedding = await get_embedding(content, llm_client=self.llm_client)
        else:
            embedding = simple_embed(content)
        
        doc = {
            "id": doc_id,
            "collection": collection,
            "title": title,
            "content": content,
            "embedding": embedding,
            "metadata": {
                "team": self.collections[collection]["team"],
                **(metadata or {})
            },
            "synthetic_only": True,
            "created_at": timestamp,
            "updated_at": timestamp
        }
        
        await self.db.rag_documents.insert_one(doc)
        
        # Update collection stats
        await self.db.rag_collection_meta.update_one(
            {"collection_id": collection},
            {
                "$inc": {"document_count": 1},
                "$set": {"last_updated": timestamp}
            }
        )
        
        logger.info(
            "rag.document.added",
            extra={"payload": {"doc_id": doc_id, "collection": collection, "title": title}}
        )
        
        return {
            "id": doc_id,
            "collection": collection,
            "status": "created"
        }
    
    async def search_collection(
        self,
        query: str,
        collection: Optional[str] = None,
        top_k: int = 5,
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Search documents in a specific collection or across all collections.
        
        Args:
            query: Search query
            collection: Optional collection filter
            top_k: Number of results to return
            min_score: Minimum similarity score threshold
            
        Returns:
            List of matching documents with scores
        """
        query_embedding = await get_embedding(query, llm_client=self.llm_client)
        
        # Build query filter
        filter_query = {}
        if collection:
            if collection not in self.collections:
                raise ValueError(f"Invalid collection: {collection}")
            filter_query["collection"] = collection
        
        # Retrieve documents
        docs = await self.db.rag_documents.find(
            filter_query,
            {"_id": 0}
        ).to_list(500)
        
        if not docs:
            return []
        
        # Score documents
        from app.rag_utils import cosine_similarity
        
        scored_docs = []
        for doc in docs:
            doc_embedding = doc.get("embedding", [])
            if doc_embedding:
                score = cosine_similarity(query_embedding, doc_embedding)
                if score >= min_score:
                    scored_docs.append({
                        **{k: v for k, v in doc.items() if k != "embedding"},
                        "score": round(score, 4)
                    })
        
        # Sort by score and return top_k
        scored_docs.sort(key=lambda x: x.get("score", 0), reverse=True)
        return scored_docs[:top_k]
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics for all RAG collections.
        
        Returns:
            Dict with stats for each collection
        """
        stats = {}
        
        for collection_name in self.collections:
            count = await self.db.rag_documents.count_documents(
                {"collection": collection_name}
            )
            
            stats[collection_name] = {
                **self.collections[collection_name],
                "document_count": count
            }
        
        total = sum(s["document_count"] for s in stats.values())
        
        return {
            "collections": stats,
            "total_documents": total,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def seed_taxonomy(self, taxonomy_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Seed the taxonomy collection from the 120-scenario catalog.
        
        Args:
            taxonomy_path: Path to taxonomy JSON file
            
        Returns:
            Dict with seeding results
        """
        if taxonomy_path is None:
            # Default path
            taxonomy_path = Path(__file__).resolve().parents[3] / "banking_fraud_taxonomy_catalog_120.json"
        
        if not taxonomy_path.exists():
            return {"status": "error", "message": f"Taxonomy file not found: {taxonomy_path}"}
        
        # Load taxonomy
        taxonomy_data = json.loads(taxonomy_path.read_text(encoding="utf-8"))
        
        seeded = 0
        errors = []
        
        # Get scenarios from the catalog
        scenarios = taxonomy_data.get("scenarios", [])
        families = {f["family_id"]: f for f in taxonomy_data.get("families", [])}
        
        for scenario in scenarios:
            try:
                scenario_id = scenario.get("scenario_id", "")
                family_id = scenario.get("family_id", "")
                family = families.get(family_id, {})
                
                # Build rich content
                content_parts = [
                    f"Scenario: {scenario.get('scenario_name', 'Unknown')}",
                    f"Family: {family.get('family_name', 'Unknown')}",
                    f"Entry Vector: {scenario.get('entry_vector', 'Unknown')}",
                    "",
                    "Prerequisites:",
                    *[f"  - {p}" for p in scenario.get("prerequisites", [])],
                    "",
                    "Telemetry Indicators:",
                    *[f"  - {t}" for t in scenario.get("telemetry_indicators", [])],
                    "",
                    "Recommended Controls:",
                    *[f"  - {c}" for c in scenario.get("recommended_controls", [])]
                ]
                
                content = "\n".join(content_parts)
                
                # Generate embedding
                embedding = await get_embedding(content, llm_client=self.llm_client)
                
                doc = {
                    "id": scenario_id,
                    "collection": "taxonomy",
                    "title": f"[{scenario_id}] {scenario.get('scenario_name', 'Unknown')}",
                    "content": content,
                    "embedding": embedding,
                    "metadata": {
                        "scenario_id": scenario_id,
                        "family_id": family_id,
                        "family_name": family.get("family_name"),
                        "tags": family.get("tags", []),
                        "entry_vector": scenario.get("entry_vector"),
                        "payment_rails": scenario.get("payment_rails", []),
                        "primary_segment": scenario.get("primary_segment"),
                        "team": "all"
                    },
                    "synthetic_only": True,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                
                # Upsert to avoid duplicates
                await self.db.rag_documents.update_one(
                    {"id": scenario_id, "collection": "taxonomy"},
                    {"$set": doc},
                    upsert=True
                )
                
                seeded += 1
                
            except Exception as e:
                errors.append({
                    "scenario_id": scenario.get("scenario_id"),
                    "error": str(e)
                })
        
        logger.info(
            "rag.taxonomy.seeded",
            extra={"payload": {"seeded": seeded, "errors": len(errors)}}
        )
        
        return {
            "status": "completed",
            "seeded": seeded,
            "errors": errors,
            "total_scenarios": len(scenarios)
        }
    
    async def seed_default_documents(self) -> Dict[str, Any]:
        """
        Seed default documents for all collections (except taxonomy which has its own seeder).
        
        Returns:
            Dict with seeding results
        """
        defaults = {
            "attacks": [
                {
                    "title": "Velocity Burst Attack",
                    "content": "Fraudsters split transactions into rapid bursts (5+ in 10 minutes) to evade single-threshold velocity rules. Often combined with round-dollar amounts and new device fingerprints.",
                    "metadata": {"attack_type": "velocity", "severity": "high"}
                },
                {
                    "title": "Credential Stuffing Attack",
                    "content": "Automated testing of stolen username/password pairs from data breaches. Characterized by high failed login rates followed by successful access from new devices.",
                    "metadata": {"attack_type": "ato", "severity": "critical"}
                },
                {
                    "title": "Synthetic Identity Creation",
                    "content": "Combining real and fabricated identity elements to create new identities. Often uses thin-file credit profiles and shared device fingerprints across multiple applications.",
                    "metadata": {"attack_type": "identity", "severity": "high"}
                }
            ],
            "patterns": [
                {
                    "title": "Account Takeover Detection Pattern",
                    "content": "ATO indicators: device fingerprint change, new payee addition within 24h, high-risk beneficiary transfers, unusual login locations, password reset requests. Detection confidence 0.92.",
                    "metadata": {"pattern_type": "ato", "confidence": 0.92}
                },
                {
                    "title": "Velocity Fraud Pattern",
                    "content": "Detection pattern for rapid transaction bursts: 5+ transactions within 10 minutes, round dollar amounts, new device signals, geographic anomalies. Block and challenge recommended.",
                    "metadata": {"pattern_type": "velocity", "confidence": 0.89}
                },
                {
                    "title": "Mule Account Pattern",
                    "content": "Network pattern for mule accounts: many-to-one then one-to-many transaction flows, new accounts with shared devices, ATM withdrawals clustered by time/location.",
                    "metadata": {"pattern_type": "mule", "confidence": 0.87}
                }
            ],
            "rules": [
                {
                    "title": "VEL-001: Velocity Check Rule",
                    "content": "Rule VEL-001 flags accounts with more than 5 transfers within 10 minutes. Proven 92% effective against automated fraud with less than 2% false positive rate. Triggers: flag, challenge.",
                    "metadata": {"rule_id": "VEL-001", "rule_type": "velocity", "effectiveness": 0.92}
                },
                {
                    "title": "ATO-099: Account Takeover Indicators",
                    "content": "Rule ATO-099 detects account takeover: new payee + high-risk beneficiary within 72h of profile change. Actions: block, alert_user. Priority 1, Critical severity.",
                    "metadata": {"rule_id": "ATO-099", "rule_type": "behavioral", "effectiveness": 0.88}
                },
                {
                    "title": "GEO-008: Impossible Travel Detection",
                    "content": "Rule GEO-008 flags impossible travel: distance > 500km with time difference < 4 hours. High severity flag. Common in ATO and device cloning scenarios.",
                    "metadata": {"rule_id": "GEO-008", "rule_type": "geo", "effectiveness": 0.95}
                }
            ],
            "explanations": [
                {
                    "title": "XAI Decision Template - Block",
                    "content": "Standard explanation template for BLOCK decisions: (1) Top 3 triggering signals with confidence scores, (2) Rules triggered with severity, (3) Overall confidence statement, (4) Alternative interpretations if confidence < 0.8.",
                    "metadata": {"template_type": "block", "team": "gold"}
                },
                {
                    "title": "XAI Decision Template - Flag",
                    "content": "Standard explanation template for FLAG decisions: (1) Warning signals identified, (2) Rules triggered (non-blocking), (3) Recommended follow-up actions, (4) Escalation path if confirmed.",
                    "metadata": {"template_type": "flag", "team": "gold"}
                },
                {
                    "title": "XAI Evidence Linking Guide",
                    "content": "Evidence linking requirements: Each decision must cite specific log IDs, transaction references, and rule matches. Include timestamp, agent ID, and confidence interval. Link to audit trail.",
                    "metadata": {"template_type": "evidence", "team": "gold"}
                }
            ]
        }
        
        results = {}
        
        for collection, docs in defaults.items():
            seeded = 0
            for doc_data in docs:
                try:
                    await self.add_document(
                        collection=collection,
                        title=doc_data["title"],
                        content=doc_data["content"],
                        metadata=doc_data.get("metadata", {})
                    )
                    seeded += 1
                except Exception as e:
                    logger.error(
                        "rag.seed.doc_failed",
                        extra={"payload": {"collection": collection, "title": doc_data["title"], "error": str(e)}}
                    )
            
            results[collection] = seeded
        
        return {
            "status": "completed",
            "documents_seeded": results,
            "total": sum(results.values())
        }


async def create_rag_service(
    db: DatabaseClient,
    llm_client: Optional[LLMClient] = None
) -> MultiCollectionRAGService:
    """Factory function to create a MultiCollectionRAGService instance."""
    service = MultiCollectionRAGService(db, llm_client)
    await service.initialize_collections()
    return service
