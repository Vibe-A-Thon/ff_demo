"""Agentic RAG planner and tool routing."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.core.external_services import DatabaseClient, LLMClient
from app.rag_utils import select_rag_mode


@dataclass(slots=True)
class AgenticStep:
    step_id: int
    action: str
    query: str
    details: Dict[str, Any]


async def plan_agentic_steps(query: str, llm_client: Optional[LLMClient]) -> List[AgenticStep]:
    """Plan multi-step retrieval actions.

    Args:
        query: User query.
        llm_client: Optional LLM client.

    Returns:
        List[AgenticStep]: Planned steps.
    """
    if llm_client:
        try:
            prompt = (
                "You are a retrieval planner. Produce a JSON array of steps with fields: action, query, details. "
                "Actions allowed: vector, hybrid, graph, cache. Keep 2-4 steps.\n\n"
                f"User query: {query}"
            )
            response = await llm_client.chat_completions_create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
            )
            raw = json.loads(response)
            steps = []
            for idx, item in enumerate(raw):
                steps.append(
                    AgenticStep(
                        step_id=idx + 1,
                        action=str(item.get("action", "hybrid")),
                        query=str(item.get("query", query)),
                        details=item.get("details", {}),
                    )
                )
            if steps:
                return steps
        except Exception:
            pass

    mode = select_rag_mode(query, "auto")
    fallback = [
        AgenticStep(step_id=1, action=mode, query=query, details={"reason": "auto"}),
        AgenticStep(step_id=2, action="graph", query=query, details={"reason": "relationship_check"}),
    ]
    return fallback


async def run_agentic_steps(
    steps: List[AgenticStep],
    db: DatabaseClient,
    llm_client: Optional[LLMClient],
    retrieve_fn,
    graph_fn,
    role: Optional[str],
    synthetic_only: bool,
    use_hybrid: bool,
    top_k: int,
) -> Dict[str, Any]:
    """Execute planned steps and aggregate hits.

    Returns:
        Dict[str, Any]: Aggregated hits and trace steps.
    """
    aggregated_hits: List[Dict[str, Any]] = []
    graph_hits: List[Dict[str, Any]] = []
    trace: List[Dict[str, Any]] = []

    for step in steps:
        if step.action in {"vector", "hybrid"}:
            hits = await retrieve_fn(
                step.query,
                None,
                synthetic_only,
                use_hybrid,
                top_k,
                db,
                llm_client,
                role,
            )
            aggregated_hits.extend(hits)
        elif step.action == "graph":
            graph_hits = await graph_fn(step.query, db, top_k, step.details.get("graph_hops", 1))
        elif step.action == "cache":
            hits = await retrieve_fn(
                step.query,
                None,
                synthetic_only,
                use_hybrid,
                top_k,
                db,
                llm_client,
                role,
            )
            aggregated_hits.extend(hits)
        trace.append({"step": step.step_id, "action": step.action, "query": step.query, "details": step.details})

    return {"hits": aggregated_hits, "graph_hits": graph_hits, "trace": trace}
