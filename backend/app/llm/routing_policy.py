"""Routing policy loader for LLM selection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional
from pathlib import Path
import yaml

from app.config import ROOT_DIR


@dataclass(frozen=True)
class RoutingPolicy:
    global_default: Optional[str]
    team_defaults: Dict[str, str]
    agent_defaults: Dict[str, str]
    intent_defaults: Dict[str, str]
    fallback_chains: Dict[str, List[str]]


def _default_policy_path() -> Path:
    return ROOT_DIR / "llm" / "configs" / "routing_policy.yaml"


def load_routing_policy(path: Optional[Path] = None) -> RoutingPolicy:
    policy_path = path or _default_policy_path()
    if not policy_path.exists():
        return RoutingPolicy(
            global_default=None,
            team_defaults={},
            agent_defaults={},
            intent_defaults={},
            fallback_chains={},
        )
    with policy_path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    return RoutingPolicy(
        global_default=payload.get("global_default"),
        team_defaults=payload.get("team_defaults", {}) or {},
        agent_defaults=payload.get("agent_defaults", {}) or {},
        intent_defaults=payload.get("intent_defaults", {}) or {},
        fallback_chains=payload.get("fallback_chains", {}) or {},
    )
