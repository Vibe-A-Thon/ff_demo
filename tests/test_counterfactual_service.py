"""Tests for the Counterfactual and Similar-Case Retrieval Service."""

from app.services.counterfactual_service import (
    CounterfactualService,
    SimilarCaseService,
    build_enhanced_explanation_bundle,
    FEATURE_WEIGHTS,
    CATEGORICAL_LEVELS,
    DECISION_HIERARCHY,
)
from app.models import EvidenceItem, ExplanationBundle


def test_extract_features_from_evidence():
    """Test feature extraction from evidence items."""
    service = CounterfactualService()
    
    evidence_items = [
        EvidenceItem(
            evidence_type="signal",
            summary="Risk score signal",
            payload={"risk_score": 0.85, "velocity_score": 0.7},
        ),
        EvidenceItem(
            evidence_type="device",
            summary="Device risk",
            payload={"device_risk": "high", "device_risk_score": 0.8},
        ),
    ]
    
    features = service.extract_features_from_evidence(evidence_items)
    
    assert "risk_score" in features
    assert features["risk_score"]["value"] == 0.85
    assert features["risk_score"]["kind"] == "numeric"
    
    assert "velocity_score" in features
    assert features["velocity_score"]["value"] == 0.7
    
    assert "device_risk" in features
    assert features["device_risk"]["raw"] == "high"
    assert features["device_risk"]["kind"] == "categorical"


def test_extract_features_handles_empty_evidence():
    """Test feature extraction with empty evidence."""
    service = CounterfactualService()
    features = service.extract_features_from_evidence([])
    assert features == {}


def test_extract_rules_from_evidence():
    """Test rule extraction from evidence items."""
    service = CounterfactualService()
    
    evidence_items = [
        EvidenceItem(
            evidence_type="rule",
            summary="Rule triggered",
            payload={
                "triggered_rules": ["R-ATO-001", "R-VELOCITY-004"],
                "rule_id": "R-GEO-002",
            },
        ),
    ]
    
    events = [
        {
            "event_type": "decision",
            "payload": {
                "triggered_rules": ["R-DEVICE-003"],
                "outputs": {"rule_id": "R-BEHAVIOR-001"},
            },
        },
    ]
    
    rules = service.extract_rules_from_evidence(evidence_items, events)
    
    rule_ids = {r["rule_id"] for r in rules}
    assert "R-ATO-001" in rule_ids
    assert "R-VELOCITY-004" in rule_ids
    assert "R-GEO-002" in rule_ids
    assert "R-DEVICE-003" in rule_ids
    assert "R-BEHAVIOR-001" in rule_ids


def test_generate_feature_counterfactuals():
    """Test counterfactual generation for numeric features."""
    service = CounterfactualService()
    
    features = {
        "risk_score": {
            "value": 0.9,
            "evidence_id": "ev-1",
            "evidence_type": "signal",
            "kind": "numeric",
        },
        "velocity_score": {
            "value": 0.8,
            "evidence_id": "ev-2",
            "evidence_type": "signal",
            "kind": "numeric",
        },
    }
    
    counterfactuals = service.generate_feature_counterfactuals(
        features, "block", {}
    )
    
    assert len(counterfactuals) >= 1
    assert counterfactuals[0]["expected_outcome"] == "review"
    assert len(counterfactuals[0]["evidence_links"]) > 0


def test_generate_rule_counterfactuals():
    """Test counterfactual generation for rules."""
    service = CounterfactualService()
    
    rules = [
        {
            "rule_id": "R-ATO-001",
            "threshold": 0.7,
            "actual_value": 0.85,
            "evidence_id": "ev-1",
        },
    ]
    
    counterfactuals = service.generate_rule_counterfactuals(rules, "block")
    
    assert len(counterfactuals) >= 1
    assert "R-ATO-001" in counterfactuals[0]["label"]
    assert counterfactuals[0]["expected_outcome"] == "review"
    assert counterfactuals[0]["rule_id"] == "R-ATO-001"


def test_generate_combined_counterfactuals_ranking():
    """Test combined counterfactuals are ranked by confidence."""
    service = CounterfactualService()
    
    features = {
        "risk_score": {"value": 0.9, "kind": "numeric", "evidence_id": "ev-1"},
    }
    rules = [{"rule_id": "R-TEST-001", "evidence_id": "ev-2"}]
    
    counterfactuals = service.generate_combined_counterfactuals(
        features, rules, "block", {}
    )
    
    # Should be sorted by confidence
    confidences = [cf.get("confidence", 0) for cf in counterfactuals]
    assert confidences == sorted(confidences, reverse=True)
    
    # Should be limited to 5
    assert len(counterfactuals) <= 5


def test_counterfactuals_for_allow_decision():
    """Test counterfactuals for allow decision returns empty."""
    service = CounterfactualService()
    
    features = {"risk_score": {"value": 0.3, "kind": "numeric"}}
    
    counterfactuals = service.generate_feature_counterfactuals(
        features, "allow", {}
    )
    
    # Allow has no target outcomes, so no counterfactuals
    assert len(counterfactuals) == 0


def test_build_case_signature():
    """Test case signature building."""
    service = SimilarCaseService()
    
    evidence_items = [
        EvidenceItem(
            evidence_type="signal",
            summary="High risk detected",
            payload={"triggered_rules": ["R-ATO-001"]},
            source_tool="risk_analyzer",
        ),
    ]
    
    events = [
        {"event_type": "decision", "payload": {"team": "blue", "agent": "detector"}},
    ]
    
    signature = service.build_case_signature(
        "run-1", "block", evidence_items, events, {"avg_score": 0.8}
    )
    
    assert signature["run_id"] == "run-1"
    assert signature["decision"] == "block"
    assert "R-ATO-001" in signature["rules"]
    assert "evidence:signal" in signature["artifacts"]
    assert "tool:risk_analyzer" in signature["artifacts"]
    assert signature["metrics"]["avg_score"] == 0.8
    assert len(signature["signature_hash"]) == 16


def test_build_pack_signature():
    """Test pack signature building."""
    service = SimilarCaseService()
    
    pack = {
        "id": "pack-1",
        "run_id": "run-1",
        "battle_id": "battle-1",
        "narrative": "High velocity transfer blocked",
        "triggered_rules": ["R-ATO-001", "R-VELOCITY-004"],
        "artifacts": [
            {"event_type": "detection", "agent": "blue-detector"},
        ],
        "metrics": {"avg_score": 0.75},
        "xai_bundle": {"decision_id": "block"},
    }
    
    signature = service.build_pack_signature(pack)
    
    assert signature["pack_id"] == "pack-1"
    assert signature["run_id"] == "run-1"
    assert "R-ATO-001" in signature["rules"]
    assert "R-VELOCITY-004" in signature["rules"]
    assert signature["decision"] == "block"


def test_score_similarity_identical_signatures():
    """Test similarity scoring for identical signatures."""
    service = SimilarCaseService()
    
    signature = {
        "rules": {"R-ATO-001", "R-VELOCITY-004"},
        "artifacts": {"event:detection", "team:blue"},
        "tokens": {"high", "velocity", "blocked"},
        "decision": "block",
        "metrics": {"avg_score": 0.8},
        "features": {"risk_score": 0.85},
        "signature_hash": "abc123",
    }
    
    similarity, details = service.score_similarity(signature, signature)
    
    assert similarity >= 0.95  # Should be very high for identical
    assert details["rules"] == 1.0
    assert details["artifacts"] == 1.0
    assert details["decision"] == 1.0


def test_score_similarity_different_signatures():
    """Test similarity scoring for different signatures."""
    service = SimilarCaseService()
    
    sig1 = {
        "rules": {"R-ATO-001", "R-VELOCITY-004"},
        "artifacts": {"event:detection"},
        "tokens": {"high", "velocity"},
        "decision": "block",
        "metrics": {},
        "features": {},
        "signature_hash": "abc",
    }
    
    sig2 = {
        "rules": {"R-GEO-001"},
        "artifacts": {"event:alert"},
        "tokens": {"geo", "risk"},
        "decision": "review",
        "metrics": {},
        "features": {},
        "signature_hash": "xyz",
    }
    
    similarity, details = service.score_similarity(sig1, sig2)
    
    assert similarity < 0.3  # Should be low for different
    assert details["rules"] == 0.0  # No overlap
    assert details["decision"] == 0.0  # Different decision


def test_feature_weights_coverage():
    """Test that feature weights are properly defined."""
    expected_features = {
        "risk_score",
        "velocity_score",
        "device_risk_score",
        "geo_risk_score",
        "behavior_score",
        "amount",
        "anomaly_count",
        "model_score",
    }
    
    assert set(FEATURE_WEIGHTS.keys()) == expected_features
    assert sum(FEATURE_WEIGHTS.values()) == 1.0


def test_categorical_levels_order():
    """Test that categorical levels are in increasing order."""
    for feature, levels in CATEGORICAL_LEVELS.items():
        assert levels == ["low", "medium", "high", "critical"]


def test_decision_hierarchy_completeness():
    """Test decision hierarchy covers all decisions."""
    assert "block" in DECISION_HIERARCHY
    assert "review" in DECISION_HIERARCHY
    assert "allow" in DECISION_HIERARCHY
    assert "monitor" in DECISION_HIERARCHY
    
    # Block should suggest review first
    assert DECISION_HIERARCHY["block"][0] == "review"
    # Allow has no further suggestions
    assert DECISION_HIERARCHY["allow"] == []


def test_build_enhanced_bundle_basic():
    """Test basic enhanced bundle building."""
    evidence_items = [
        EvidenceItem(
            evidence_type="signal",
            summary="High risk score",
            payload={"risk_score": 0.85},
        ),
    ]
    
    bundle = build_enhanced_explanation_bundle(
        run_id="run-1",
        decision="block",
        evidence_items=evidence_items,
    )
    
    assert isinstance(bundle, ExplanationBundle)
    assert bundle.decision_id == "block"
    assert len(bundle.counterfactuals) >= 0
