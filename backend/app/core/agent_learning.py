"""Agent Learning Engine - Reflection and Memory.

Provides self-learning capabilities for agents by recording outcomes and recalling
relevant lessons during task execution.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.db import db
from app.rag_utils import get_embedding, cosine_similarity
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class AgentLearningEngine:
    """Engine for agent memory and learning."""

    async def record_lesson(
        self,
        agent_id: str,
        team_id: str,
        task_type: str,
        content: str,
        outcome: str = "success",
        confidence: float = 1.0,
        tags: List[str] | None = None,
    ) -> str:
        """Record a lesson or reflection.

        Args:
            agent_id: Agent identifier.
            team_id: Team identifier.
            task_type: Task type context.
            content: textual lesson/reflection.
            outcome: success/failure outcome.
            confidence: Confidence score (0-1).
            tags: Optional tags.

        Returns:
            str: Memory ID.
        """
        try:
            embedding = await get_embedding(content)
            doc = {
                "agent_id": agent_id,
                "team_id": team_id,
                "task_type": task_type,
                "content": content,
                "outcome": outcome,
                "confidence": confidence,
                "embedding": embedding,
                "tags": tags or [],
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            res = await db.agent_memories.insert_one(doc)
            logger.info("Lesson recorded", extra={"payload": {"agent_id": agent_id, "task_type": task_type}})
            return str(res.inserted_id)
        except Exception as exc:
            logger.error("Failed to record lesson", extra={"payload": {"error": str(exc)}})
            return ""

    async def recall_lessons(
        self,
        agent_id: str,
        team_id: str,
        query: str,
        limit: int = 3,
        threshold: float = 0.65,
    ) -> List[Dict[str, Any]]:
        """Recall relevant lessons from memory.

        Args:
            agent_id: Agent identifier.
            team_id: Team identifier.
            query: Context query.
            limit: Max lessons to return.
            threshold: Similarity threshold.

        Returns:
            List[Dict[str, Any]]: Ranked lessons.
        """
        try:
            query_vec = await get_embedding(query)
            
            # Retrieve candidates (Team-scoped memory for shared learning)
            # In a real vector DB, this would be a vector query.
            # Here we fetch recent/relevant by metadata and re-rank.
            cursor = db.agent_memories.find(
                {"team_id": team_id}
            ).sort("created_at", -1).limit(200)
            
            candidates = await cursor.to_list(length=200)
            scored = []
            
            for doc in candidates:
                emb = doc.get("embedding")
                if not emb:
                    continue
                score = cosine_similarity(query_vec, emb)
                if score >= threshold:
                    doc_copy = doc.copy()
                    doc_copy["score"] = score
                    doc_copy.pop("embedding", None) # Remove vector from output
                    scored.append(doc_copy)
            
            scored.sort(key=lambda x: x["score"], reverse=True)
            return scored[:limit]
        except Exception as exc:
            logger.error("Failed to recall lessons", extra={"payload": {"error": str(exc)}})
            return []

    async def distill_run_learnings(
        self,
        run_id: str,
        artifacts: List[Dict[str, Any]]
    ) -> int:
        """Distill learnings from a completed run.
        
        Analyzes artifacts and outcomes to generate consolidated lessons.
        """
        count = 0
        # Simple heuristic: If artifact has 'confidence' > 0.9, treat as a strong lesson
        for art in artifacts:
            if art.get("confidence", 0) > 0.9:
                content = f"Produced high-confidence {art.get('artifact_type')}: {art.get('summary')}"
                await self.record_lesson(
                    agent_id=art.get("agent_id", "system"),
                    team_id=art.get("team_id", "system"),
                    task_type=art.get("lineage", {}).get("task_type", "unknown"),
                    content=content,
                    outcome="success",
                    confidence=art.get("confidence", 1.0)
                )
                count += 1
        return count


LEARNING_ENGINE = AgentLearningEngine()
