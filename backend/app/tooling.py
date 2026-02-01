"""Synthetic tooling helpers for war loop simulations."""

import hashlib
import random
from datetime import datetime, timezone
from typing import Any, Dict
from app.models import ToolSpec


def derive_seed(base_seed: int, salt: str) -> int:
    seed_input = f"{base_seed}:{salt}".encode("utf-8")
    return int(hashlib.sha256(seed_input).hexdigest()[:12], 16)


def rng(seed: int) -> random.Random:
    return random.Random(seed)


def simulate_transactions(params: Dict[str, Any], seed: int) -> Dict[str, Any]:
    randomizer = rng(seed)
    count = int(params.get("count", 25))
    scenario = params.get("scenario", "demo")
    rails = params.get("rails", ["cards", "upi", "ach"])
    events = []
    for idx in range(count):
        amount = round(randomizer.uniform(5, 5000), 2)
        event = {
            "event_id": f"tx_{seed}_{idx}",
            "scenario": scenario,
            "rail": rails[idx % len(rails)],
            "amount": amount,
            "velocity_bucket": "high" if amount > 2500 else "normal",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        events.append(event)
    return {"events": events, "count": len(events)}


def apply_attack(params: Dict[str, Any], seed: int) -> Dict[str, Any]:
    randomizer = rng(seed)
    events = params.get("events", [])
    attack_type = params.get("attack_type", "velocity_anomaly")
    mutated = []
    for event in events:
        mutated_event = {**event}
        if attack_type == "velocity_anomaly":
            mutated_event["velocity_bucket"] = "spike"
            mutated_event["amount"] = round(float(event.get("amount", 0)) * randomizer.uniform(1.2, 2.2), 2)
        elif attack_type == "identity_mismatch":
            mutated_event["identity_match"] = False
        else:
            mutated_event["signal"] = "synthetic_variation"
        mutated.append(mutated_event)
    return {"attacked_events": mutated, "attack_type": attack_type}


def score_risk(params: Dict[str, Any], seed: int) -> Dict[str, Any]:
    randomizer = rng(seed)
    events = params.get("events", [])
    scores = []
    for event in events:
        base = 0.35 if event.get("velocity_bucket") == "spike" else 0.15
        score = min(0.99, base + randomizer.uniform(0.05, 0.4))
        scores.append({"event_id": event.get("event_id"), "risk_score": round(score, 3)})
    return {
        "scores": scores,
        "avg_score": round(sum(s["risk_score"] for s in scores) / max(len(scores), 1), 3),
    }


def respond_actions(params: Dict[str, Any], seed: int) -> Dict[str, Any]:
    randomizer = rng(seed)
    scores = params.get("scores", [])
    actions = []
    for score in scores:
        risk = score.get("risk_score", 0)
        if risk >= 0.8:
            action = "block"
        elif risk >= 0.5:
            action = "review"
        else:
            action = "allow"
        actions.append({"event_id": score.get("event_id"), "action": action, "risk_score": risk})
    return {"actions": actions, "decision": randomizer.choice(["contain", "monitor", "escalate"])}


TOOL_REGISTRY: Dict[str, ToolSpec] = {
    "simulate_transactions": ToolSpec(
        tool_name="simulate_transactions",
        description="Generate synthetic transaction events for a scenario.",
        input_schema={"scenario": "string", "count": "int", "rails": "list"},
        output_schema={"events": "list", "count": "int"},
        allowed_teams=["red", "blue", "black", "gold"],
    ),
    "apply_attack": ToolSpec(
        tool_name="apply_attack",
        description="Apply synthetic attack patterns to events.",
        input_schema={"events": "list", "attack_type": "string"},
        output_schema={"attacked_events": "list", "attack_type": "string"},
        allowed_teams=["red"],
    ),
    "score_risk": ToolSpec(
        tool_name="score_risk",
        description="Score synthetic events for risk.",
        input_schema={"events": "list"},
        output_schema={"scores": "list", "avg_score": "float"},
        allowed_teams=["blue", "green", "black"],
    ),
    "respond_actions": ToolSpec(
        tool_name="respond_actions",
        description="Generate response actions based on risk scores.",
        input_schema={"scores": "list"},
        output_schema={"actions": "list", "decision": "string"},
        allowed_teams=["blue", "orange", "white"],
    ),
}

TOOL_IMPLEMENTATIONS = {
    "simulate_transactions": simulate_transactions,
    "apply_attack": apply_attack,
    "score_risk": score_risk,
    "respond_actions": respond_actions,
}
