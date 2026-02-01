"""LLM routing policy engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from app.llm.model_registry import ModelSpec
from app.llm.routing_policy import RoutingPolicy


@dataclass(frozen=True)
class RouteSelection:
    model: ModelSpec
    fallbacks: List[ModelSpec]


class LLMRouter:
    def __init__(self, registry: dict[str, ModelSpec], policy: RoutingPolicy) -> None:
        self._registry = registry
        self._policy = policy

    def _resolve_model_id(
        self,
        requested_model: Optional[str],
        team_id: Optional[str],
        agent_id: Optional[str],
        intent: Optional[str],
    ) -> Optional[str]:
        if requested_model and requested_model in self._registry:
            return requested_model
        if agent_id and agent_id in self._policy.agent_defaults:
            return self._policy.agent_defaults[agent_id]
        if team_id and team_id in self._policy.team_defaults:
            return self._policy.team_defaults[team_id]
        if intent and intent in self._policy.intent_defaults:
            return self._policy.intent_defaults[intent]
        return self._policy.global_default

    def select(
        self,
        requested_model: Optional[str] = None,
        team_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        intent: Optional[str] = None,
    ) -> RouteSelection:
        model_id = self._resolve_model_id(requested_model, team_id, agent_id, intent)
        if not model_id or model_id not in self._registry:
            raise ValueError("No model available for routing")
        model = self._registry[model_id]
        fallback_ids = self._policy.fallback_chains.get(model_id, [])
        fallbacks = [self._registry[fid] for fid in fallback_ids if fid in self._registry]
        return RouteSelection(model=model, fallbacks=fallbacks)
