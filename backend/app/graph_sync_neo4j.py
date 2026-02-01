"""Neo4j synchronization utilities for knowledge nodes."""

from __future__ import annotations

import os
import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from neo4j import GraphDatabase, Driver

from app.config import INTEGRATIONS_CONFIG, get_integration_setting


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


def _health_check_sync() -> Dict[str, Any]:
    driver = _get_driver()
    if not driver:
        return {"status": "unavailable", "reason": "neo4j_not_configured"}
    try:
        with driver.session() as session:
            session.run("RETURN 1")
        return {"status": "ok"}
    except Exception as exc:
        return {"status": "error", "reason": str(exc)}


async def health_check() -> Dict[str, Any]:
    """Check Neo4j connectivity."""
    return await asyncio.to_thread(_health_check_sync)


def sync_nodes(nodes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Sync knowledge nodes into Neo4j.

    Args:
        nodes: Knowledge nodes list.

    Returns:
        Dict[str, Any]: Sync summary.
    """
    driver = _get_driver()
    if not driver:
        return {"status": "skipped", "reason": "neo4j_not_configured"}

    created = 0
    relationships = 0
    with driver.session() as session:
        for node in nodes:
            node_id = node.get("id")
            if not node_id:
                continue
            session.run(
                """
                MERGE (n:KnowledgeNode {id: $id})
                SET n.name = $name,
                    n.node_type = $node_type,
                    n.data = $data
                """,
                id=node_id,
                name=node.get("name"),
                node_type=node.get("node_type"),
                data=node.get("data") or {},
            )
            created += 1
            for target_id in node.get("connections", []) or []:
                session.run(
                    """
                    MATCH (a:KnowledgeNode {id: $source})
                    MERGE (b:KnowledgeNode {id: $target})
                    MERGE (a)-[:RELATED_TO]->(b)
                    """,
                    source=node_id,
                    target=target_id,
                )
                relationships += 1

    return {"status": "ok", "nodes": created, "relationships": relationships}


async def sync_nodes_async(nodes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Async wrapper for sync_nodes."""
    return await asyncio.to_thread(sync_nodes, nodes)


async def run_sync_loop(fetch_nodes, on_result) -> None:
    """Background sync loop for Neo4j ingestion.

    Args:
        fetch_nodes: Coroutine to fetch nodes.
        on_result: Callback to record results.
    """
    interval_raw = get_integration_setting("graph_sync", "interval_seconds", "300")
    interval = int(interval_raw or 300)
    while True:
        nodes = await fetch_nodes()
        result = await sync_nodes_async(nodes)
        result["timestamp"] = datetime.now(timezone.utc).isoformat()
        await on_result(result)
        await asyncio.sleep(max(interval, 30))
