"""GraphRAG retrieval utilities."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from app.rag_utils import keyword_score, tokenize


def _node_text(node: Dict[str, Any]) -> str:
    name = str(node.get("name", ""))
    data = node.get("data") or {}
    return f"{name} {data}".lower()


def _build_graph(nodes: List[Dict[str, Any]]) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, List[str]]]:
    node_map = {node.get("id"): node for node in nodes if node.get("id")}
    adjacency: Dict[str, List[str]] = {node_id: [] for node_id in node_map.keys()}
    for node in nodes:
        node_id = node.get("id")
        if not node_id:
            continue
        for target in node.get("connections", []) or []:
            if target in node_map:
                adjacency.setdefault(node_id, []).append(target)
    return node_map, adjacency


def graph_retrieve(
    query: str,
    nodes: List[Dict[str, Any]],
    top_k: int = 5,
    max_hops: int = 1,
) -> List[Dict[str, Any]]:
    """Retrieve graph context by matching nodes and expanding neighbors.

    Args:
        query: Query string.
        nodes: Knowledge node list.
        top_k: Max nodes to return.
        max_hops: Neighbor expansion depth.

    Returns:
        List[Dict[str, Any]]: Graph hits with neighbors and scores.
    """
    if not nodes:
        return []
    query_tokens = tokenize(query)
    node_map, adjacency = _build_graph(nodes)
    scored: List[Dict[str, Any]] = []
    for node in nodes:
        text_tokens = tokenize(_node_text(node))
        score = keyword_score(query_tokens, text_tokens)
        if score <= 0:
            continue
        scored.append({"node": node, "score": score})
    scored.sort(key=lambda item: item["score"], reverse=True)

    hits: List[Dict[str, Any]] = []
    for item in scored[: max(top_k, 1)]:
        node = item["node"]
        node_id = node.get("id")
        neighbors: List[Dict[str, Any]] = []
        if node_id:
            frontier = {node_id}
            visited = {node_id}
            for _ in range(max(max_hops, 0)):
                next_frontier = set()
                for current in frontier:
                    for neighbor_id in adjacency.get(current, []):
                        if neighbor_id in visited:
                            continue
                        visited.add(neighbor_id)
                        neighbor = node_map.get(neighbor_id)
                        if neighbor:
                            neighbors.append(neighbor)
                        next_frontier.add(neighbor_id)
                frontier = next_frontier
                if not frontier:
                    break
        hits.append(
            {
                "node": node,
                "score": round(item["score"], 4),
                "neighbors": neighbors,
            }
        )
    return hits
