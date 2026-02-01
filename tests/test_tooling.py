from app.tooling import (
    derive_seed,
    simulate_transactions,
    apply_attack,
    score_risk,
    respond_actions,
)


def test_derive_seed_deterministic():
    assert derive_seed(123, "salt") == derive_seed(123, "salt")


def test_simulate_transactions_count():
    output = simulate_transactions({"count": 3, "rails": ["ach"]}, seed=1)
    assert output["count"] == 3
    assert all(event["rail"] == "ach" for event in output["events"])


def test_apply_attack_velocity_anomaly():
    events = [{"amount": 100, "velocity_bucket": "normal"}]
    attacked = apply_attack({"events": events, "attack_type": "velocity_anomaly"}, seed=5)
    assert attacked["attacked_events"][0]["velocity_bucket"] == "spike"


def test_score_risk_outputs_average():
    events = [{"event_id": "1", "velocity_bucket": "spike"}]
    scored = score_risk({"events": events}, seed=2)
    assert 0 <= scored["avg_score"] <= 0.99


def test_respond_actions_thresholds():
    scores = [
        {"event_id": "1", "risk_score": 0.85},
        {"event_id": "2", "risk_score": 0.6},
        {"event_id": "3", "risk_score": 0.2},
    ]
    actions = respond_actions({"scores": scores}, seed=3)
    outcomes = [item["action"] for item in actions["actions"]]
    assert outcomes == ["block", "review", "allow"]
