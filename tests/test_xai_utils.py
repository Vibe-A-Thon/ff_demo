from app.xai_utils import (
    build_evidence_items,
    build_explanation_bundle,
    build_evidence_graph,
    build_counterfactuals,
)


def test_build_evidence_items_limit():
    events = [{"event_type": f"event-{i}", "payload": {}} for i in range(10)]
    items = build_evidence_items(events, max_items=4)
    assert len(items) == 4


def test_build_explanation_bundle_contains_graph():
    events = [{"event_type": "event", "payload": {}}]
    items = build_evidence_items(events)
    bundle = build_explanation_bundle("run-1", "review", items)
    assert bundle.evidence_graph is not None
    assert bundle.decision_id == "review"


def test_build_evidence_graph_nodes():
    items = build_evidence_items([{"event_type": "event", "payload": {}}])
    graph = build_evidence_graph("run-1", items)
    assert len(graph.nodes) == 2
    assert graph.nodes[0].node_type == "Run"


def test_build_counterfactuals():
    assert build_counterfactuals("block")[0]["expected_outcome"] == "review"
    assert build_counterfactuals("review")[0]["expected_outcome"] == "allow"
