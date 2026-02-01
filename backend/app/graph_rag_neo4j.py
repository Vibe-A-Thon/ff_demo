"""Neo4j-backed GraphRAG retrieval."""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any, Dict, List, Optional, Tuple

from neo4j import GraphDatabase, Driver

from app.config import INTEGRATIONS_CONFIG
from app.rag_utils import keyword_score, tokenize


_driver: Optional[Driver] = None


def _get_neo4j_settings() -> Optional[Tuple[str, str, str]]:
    graph_cfg = (INTEGRATIONS_CONFIG or {}).get("graph_store") or {}
    if graph_cfg.get("provider") != "neo4j":
        return None
    connection = graph_cfg.get("connection", {})
    uri = connection.get("uri") or os.environ.get("NEO4J_URI")
    user_env = connection.get("user_env") or "NEO4J_USER"
    password_env = connection.get("password_env") or "NEO4J_PASSWORD"
    user = os.environ.get(user_env)
    password = os.environ.get(password_env)
    if not uri or not user or not password:
        return None
    return uri, user, password


def _get_driver() -> Optional[Driver]:
    global _driver
    if _driver is not None:
        return _driver
    settings = _get_neo4j_settings()
    if not settings:
        return None
    uri, user, password = settings
    _driver = GraphDatabase.driver(uri, auth=(user, password))
    return _driver


def _node_to_payload(node: Any) -> Dict[str, Any]:
    props = dict(node) if node is not None else {}
    node_id = getattr(node, "id", None)
    props.setdefault("id", str(node_id) if node_id is not None else props.get("id"))
    props.setdefault("name", props.get("name") or props.get("label") or "node")
    return props


def _node_text(node: Dict[str, Any]) -> str:
    name = str(node.get("name", ""))
    data = node.get("data") or {}
    node_type = node.get("node_type") or ""
    return f"{name} {node_type} {json.dumps(data, default=str)}".lower()


def _run_query(tokens: List[str], top_k: int, max_hops: int) -> List[Dict[str, Any]]:
    driver = _get_driver()
    if not driver or not tokens:
        return []
    with driver.session() as session:
        records = session.run(
            """
            MATCH (n)
            WHERE any(t IN $tokens WHERE toLower(n.name) CONTAINS t
                OR toLower(n.node_type) CONTAINS t
                OR toString(n.data) CONTAINS t)
            OPTIONAL MATCH (n)-[*1..$hops]-(m)
            RETURN n, collect(DISTINCT m)[0..10] AS neighbors
            LIMIT $limit
            """,
            tokens=tokens,
            hops=max(max_hops, 1),
            limit=max(top_k, 1),
        )
        hits: List[Dict[str, Any]] = []
        for record in records:
            node = _node_to_payload(record.get("n"))
            neighbors_raw = record.get("neighbors") or []
            neighbors = [_node_to_payload(n) for n in neighbors_raw]
            score = keyword_score(tokens, tokenize(_node_text(node)))
            hits.append({"node": node, "neighbors": neighbors, "score": round(score, 4)})
        hits.sort(key=lambda item: item.get("score", 0), reverse=True)
        return hits


async def neo4j_graph_retrieve(query: str, top_k: int = 5, max_hops: int = 1) -> List[Dict[str, Any]]:
    """Retrieve graph context from Neo4j with multi-hop expansion.

    Args:
        query: Query text.
        top_k: Max nodes to return.
        max_hops: Neighbor expansion depth.

    Returns:
        List[Dict[str, Any]]: Graph hits.
    """
    tokens = tokenize(query)
    if not tokens:
        return []
    driver = _get_driver()
    if driver is None:
        return []
    return await asyncio.to_thread(_run_query, tokens, top_k, max_hops)
