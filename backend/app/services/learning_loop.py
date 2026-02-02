"""
Never Fail Twice Learning Loop Service

This module implements the core "Never Fail Twice" learning mechanism for Fraud Forge.
After each battle, outcomes are automatically embedded into the appropriate RAG collections:
- Red Team wins → Attack vectors stored in 'attacks' collection
- Blue Team wins → Defense patterns stored in 'patterns' collection

This creates a continuously improving defense system where the same attack 
never succeeds twice.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.core.external_services import DatabaseClient, LLMClient
from app.core.logging_config import get_logger
from app.rag_utils import get_embedding

logger = get_logger(__name__)


# Collection names for the 5-collection RAG architecture
RAG_COLLECTIONS = {
    "attacks": "Red Team offensive memory - successful attack vectors",
    "patterns": "Blue Team defensive patterns - detection signatures",
    "taxonomy": "Fraud scenario taxonomy - 120 static scenarios",
    "rules": "Active rule code index - deployed detection rules",
    "explanations": "Gold Team XAI outputs - past explanations"
}


class LearningLoopService:
    """
    Core learning loop service implementing the "Never Fail Twice" mechanism.
    
    This service is responsible for:
    1. Learning from battle outcomes
    2. Storing attack vectors (Red wins) and defense patterns (Blue wins)
    3. Updating the knowledge graph for visualization
    """
    
    def __init__(self, db: DatabaseClient, llm_client: Optional[LLMClient] = None):
        self.db = db
        self.llm_client = llm_client
    
    async def learn_from_battle(
        self,
        battle_id: str,
        winner: str,  # "red" or "blue"
        attack_vector: Dict[str, Any],
        defense_signature: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Learn from a completed battle and store the outcome for future defense.
        
        Args:
            battle_id: Unique battle identifier
            winner: "red" (attack succeeded) or "blue" (defense succeeded)
            attack_vector: Details of the attack used
            defense_signature: Details of the defense pattern (if Blue won)
            metadata: Additional context about the battle
            
        Returns:
            Dict containing learning results and document IDs
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        learning_result = {
            "battle_id": battle_id,
            "winner": winner,
            "learned_at": timestamp,
            "documents_created": [],
            "immunity_gained": False
        }
        
        if winner == "red":
            # Red Team won - store attack vector for future defense
            doc_id = await self._store_attack_vector(battle_id, attack_vector, metadata)
            learning_result["documents_created"].append({
                "collection": "attacks",
                "doc_id": doc_id,
                "type": "attack_vector"
            })
            logger.info(
                "learning.attack_stored",
                extra={"payload": {"battle_id": battle_id, "doc_id": doc_id}}
            )
        
        elif winner == "blue":
            # Blue Team won - store defense pattern
            doc_id = await self._store_defense_pattern(
                battle_id, attack_vector, defense_signature, metadata
            )
            learning_result["documents_created"].append({
                "collection": "patterns",
                "doc_id": doc_id,
                "type": "defense_pattern"
            })
            learning_result["immunity_gained"] = True
            logger.info(
                "learning.pattern_stored",
                extra={"payload": {"battle_id": battle_id, "doc_id": doc_id}}
            )
        
        # Update knowledge graph with new node
        await self._update_knowledge_graph(battle_id, winner, learning_result)
        
        # Record learning event
        await self.db.learning_events.insert_one({
            "battle_id": battle_id,
            "winner": winner,
            "learning_result": learning_result,
            "created_at": timestamp
        })
        
        return learning_result
    
    async def _store_attack_vector(
        self,
        battle_id: str,
        attack_vector: Dict[str, Any],
        metadata: Optional[Dict[str, Any]]
    ) -> str:
        """Store an attack vector in the attacks collection for future defense."""
        doc_id = str(uuid.uuid4())
        
        # Build rich content from attack vector
        content_parts = [
            f"Attack Vector from Battle {battle_id}",
            f"Attack Type: {attack_vector.get('attack_type', 'Unknown')}",
            f"Entry Vector: {attack_vector.get('entry_vector', 'Unknown')}",
            f"Target: {attack_vector.get('target', 'Unknown')}",
            f"Technique: {attack_vector.get('technique', 'Unknown')}",
        ]
        
        if attack_vector.get("indicators"):
            content_parts.append(f"Indicators: {', '.join(attack_vector['indicators'])}")
        
        if attack_vector.get("payload"):
            content_parts.append(f"Payload Pattern: {attack_vector['payload']}")
        
        content = "\n".join(content_parts)
        
        # Generate embedding
        embedding = await get_embedding(content, llm_client=self.llm_client)
        
        doc = {
            "id": doc_id,
            "collection": "attacks",
            "title": f"Attack: {attack_vector.get('attack_type', 'Unknown')} [{battle_id[:8]}]",
            "content": content,
            "embedding": embedding,
            "metadata": {
                "battle_id": battle_id,
                "attack_vector": attack_vector,
                "team": "red",
                "learned_at": datetime.now(timezone.utc).isoformat(),
                **(metadata or {})
            },
            "synthetic_only": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await self.db.rag_documents.insert_one(doc)
        return doc_id
    
    async def _store_defense_pattern(
        self,
        battle_id: str,
        attack_vector: Dict[str, Any],
        defense_signature: Optional[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]]
    ) -> str:
        """Store a defense pattern in the patterns collection."""
        doc_id = str(uuid.uuid4())
        
        # Build defense pattern content
        content_parts = [
            f"Defense Pattern from Battle {battle_id}",
            f"Attack Defended: {attack_vector.get('attack_type', 'Unknown')}",
            f"Entry Vector Blocked: {attack_vector.get('entry_vector', 'Unknown')}",
        ]
        
        if defense_signature:
            content_parts.append(f"Detection Method: {defense_signature.get('method', 'Unknown')}")
            content_parts.append(f"Confidence: {defense_signature.get('confidence', 0):.2%}")
            
            if defense_signature.get("rules_triggered"):
                content_parts.append(
                    f"Rules Triggered: {', '.join(defense_signature['rules_triggered'])}"
                )
            
            if defense_signature.get("indicators_detected"):
                content_parts.append(
                    f"Indicators Detected: {', '.join(defense_signature['indicators_detected'])}"
                )
        
        content = "\n".join(content_parts)
        
        # Generate embedding
        embedding = await get_embedding(content, llm_client=self.llm_client)
        
        doc = {
            "id": doc_id,
            "collection": "patterns",
            "title": f"Defense: {attack_vector.get('attack_type', 'Unknown')} [{battle_id[:8]}]",
            "content": content,
            "embedding": embedding,
            "metadata": {
                "battle_id": battle_id,
                "attack_vector": attack_vector,
                "defense_signature": defense_signature,
                "team": "blue",
                "learned_at": datetime.now(timezone.utc).isoformat(),
                **(metadata or {})
            },
            "synthetic_only": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await self.db.rag_documents.insert_one(doc)
        return doc_id
    
    async def _update_knowledge_graph(
        self,
        battle_id: str,
        winner: str,
        learning_result: Dict[str, Any]
    ) -> None:
        """Update the knowledge graph with new learning nodes."""
        node_id = str(uuid.uuid4())
        node_type = "attack_learned" if winner == "red" else "pattern_learned"
        
        knowledge_node = {
            "id": node_id,
            "node_type": node_type,
            "name": f"Learning: Battle {battle_id[:8]}",
            "data": {
                "battle_id": battle_id,
                "winner": winner,
                "documents": learning_result.get("documents_created", []),
                "immunity_gained": learning_result.get("immunity_gained", False)
            },
            "connections": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "pending_merge"  # For Brain Surgery visualization
        }
        
        await self.db.knowledge_nodes.insert_one(knowledge_node)
    
    async def get_immunity_score(self) -> Dict[str, Any]:
        """
        Calculate the current immunity score based on learned patterns.
        
        Returns:
            Dict with immunity metrics
        """
        total_attacks = await self.db.rag_documents.count_documents({"collection": "attacks"})
        total_patterns = await self.db.rag_documents.count_documents({"collection": "patterns"})
        total_battles = await self.db.learning_events.count_documents({})
        
        blue_wins = await self.db.learning_events.count_documents({"winner": "blue"})
        
        immunity_percentage = (blue_wins / max(total_battles, 1)) * 100
        
        return {
            "immunity_score": round(immunity_percentage, 2),
            "total_attacks_learned": total_attacks,
            "total_patterns_learned": total_patterns,
            "total_battles": total_battles,
            "blue_wins": blue_wins,
            "status": "protected" if immunity_percentage >= 80 else "learning"
        }
    
    async def check_immunity(self, attack_vector: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if the system has immunity against a specific attack vector.
        
        Args:
            attack_vector: The attack to check immunity for
            
        Returns:
            Dict with immunity status and matching patterns
        """
        # Build query from attack vector
        attack_description = f"{attack_vector.get('attack_type', '')} {attack_vector.get('technique', '')} {attack_vector.get('entry_vector', '')}"
        
        # Get embedding for similarity search
        query_embedding = await get_embedding(attack_description, llm_client=self.llm_client)
        
        # Search patterns collection
        patterns = await self.db.rag_documents.find(
            {"collection": "patterns"},
            {"_id": 0, "embedding": 0}
        ).to_list(100)
        
        if not patterns:
            return {
                "has_immunity": False,
                "matching_patterns": [],
                "confidence": 0.0,
                "recommendation": "No defense patterns learned yet"
            }
        
        # Simple similarity check (in production, use vector search)
        matching_patterns = []
        attack_type = attack_vector.get("attack_type", "").lower()
        
        for pattern in patterns:
            pattern_attack = pattern.get("metadata", {}).get("attack_vector", {})
            if attack_type in pattern.get("content", "").lower():
                matching_patterns.append({
                    "pattern_id": pattern.get("id"),
                    "title": pattern.get("title"),
                    "confidence": 0.85  # Simplified scoring
                })
        
        has_immunity = len(matching_patterns) > 0
        avg_confidence = sum(p["confidence"] for p in matching_patterns) / max(len(matching_patterns), 1)
        
        return {
            "has_immunity": has_immunity,
            "matching_patterns": matching_patterns[:5],
            "confidence": round(avg_confidence, 2),
            "recommendation": "Attack pattern recognized - defenses active" if has_immunity else "New attack vector - learning required"
        }


async def create_learning_service(
    db: DatabaseClient,
    llm_client: Optional[LLMClient] = None
) -> LearningLoopService:
    """Factory function to create a LearningLoopService instance."""
    return LearningLoopService(db, llm_client)
