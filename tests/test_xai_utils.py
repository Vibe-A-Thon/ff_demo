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
    bundle = build_explanation_bundle("run-1", "review", items, {"avg_score": 0.7})
    assert bundle.evidence_graph is not None
    assert bundle.decision_id == "review"


def test_build_evidence_graph_nodes():
    items = build_evidence_items([{"event_type": "event", "payload": {}}])
    graph = build_evidence_graph("run-1", items)
    assert len(graph.nodes) == 2
    assert graph.nodes[0].node_type == "Run"


def test_build_counterfactuals():
    items = build_evidence_items(
        [
            {"event_type": "risk", "payload": {"risk_score": 0.9}},
            {"event_type": "device", "payload": {"device_risk": "high"}},
        ]
    )
    assert build_counterfactuals("block", items)[0]["expected_outcome"] == "review"
    assert build_counterfactuals("review", items)[0]["expected_outcome"] == "allow"


def test_build_counterfactuals_with_evidence_links():
    """Test that counterfactuals include evidence links."""
    items = build_evidence_items(
        [
            {"event_type": "risk", "payload": {"risk_score": 0.9}},
        ]
    )
    counterfactuals = build_counterfactuals("block", items)
    assert len(counterfactuals) >= 1
    # Counterfactuals should have changes dict
    assert "changes" in counterfactuals[0]


def test_build_explanation_bundle_has_counterfactuals():
    """Test that explanation bundle includes counterfactuals."""
    events = [
        {"event_type": "risk", "payload": {"risk_score": 0.85}},
        {"event_type": "velocity", "payload": {"velocity_score": 0.7}},
    ]
    items = build_evidence_items(events)
    bundle = build_explanation_bundle("run-1", "block", items, {"avg_score": 0.8})
    
    assert hasattr(bundle, "counterfactuals")
    assert isinstance(bundle.counterfactuals, list)


def test_build_explanation_bundle_has_similar_cases():
    """Test that explanation bundle has similar_cases list."""
    events = [{"event_type": "event", "payload": {}}]
    items = build_evidence_items(events)
    bundle = build_explanation_bundle("run-1", "block", items, {})
    
    assert hasattr(bundle, "similar_cases")
    assert isinstance(bundle.similar_cases, list)

