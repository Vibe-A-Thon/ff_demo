"""LLM service with routing, schema guard, and fallback handling."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import json
import time

from app.llm.audit_events import record_llm_event
from app.llm.model_registry import load_model_registry
from app.llm.providers.base import LLMProvider, LLMResult
from app.llm.providers.local import LocalProvider
from app.llm.providers.openai import OpenAIProvider
from app.llm.router import LLMRouter
from app.llm.routing_policy import load_routing_policy, RoutingPolicy
from app.llm.schema_guard import validate_json_payload
from app.llm.schemas import LLMFailure
from app.llm.tool_registry import load_tool_registry, validate_tool_call
from app.llm.normalizers.tool_calls import normalize_inbound_tool_calls, normalize_outbound_tools
from app.audit import compute_checksum
from app.config import OPENAI_API_KEY
from app.llm.telemetry import record_llm_telemetry_event
from app.db import db


class LLMService:
    def __init__(self) -> None:
        self._registry = load_model_registry()
        self._policy = load_routing_policy()
        self._tool_registry = load_tool_registry()
        self._router = LLMRouter(self._registry, self._policy)
        self._providers: Dict[str, LLMProvider] = {
            "local": LocalProvider(),
        }
        if OPENAI_API_KEY:
            self._providers["openai"] = OpenAIProvider(OPENAI_API_KEY)

    async def _execute(
        self,
        provider: LLMProvider,
        model_name: str,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int],
        tools: Optional[List[Dict[str, Any]]],
        response_format: Optional[Dict[str, Any]],
    ) -> LLMResult:
        return await provider.generate(
            model_name=model_name,
            messages=messages,
            max_tokens=max_tokens,
            tools=tools,
            response_format=response_format,
        )

    async def _load_overrides(self) -> Dict[str, Any]:
        record = await db.platform_settings.find_one({"key": "llm_overrides"}, {"_id": 0})
        if record and "payload" in record:
            return record.get("payload") or {}
        return {}

    def _merge_policy(self, overrides: Dict[str, Any]) -> RoutingPolicy:
        if not overrides:
            return self._policy
        return RoutingPolicy(
            global_default=overrides.get("global_default") or self._policy.global_default,
            team_defaults={**self._policy.team_defaults, **(overrides.get("team_defaults") or {})},
            agent_defaults={**self._policy.agent_defaults, **(overrides.get("agent_defaults") or {})},
            intent_defaults={**self._policy.intent_defaults, **(overrides.get("intent_defaults") or {})},
            fallback_chains={**self._policy.fallback_chains, **(overrides.get("fallback_chains") or {})},
        )

    async def _resolve_router(self) -> tuple[LLMRouter, Dict[str, Any]]:
        overrides = await self._load_overrides()
        policy = self._merge_policy(overrides)
        return LLMRouter(self._registry, policy), overrides

    async def generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        response_schema: Any = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        requested_model: Optional[str] = None,
        team_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        intent: Optional[str] = None,
        actor_id: Optional[str] = None,
        run_id: Optional[str] = None,
        turn_id: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> str:
        router, overrides = await self._resolve_router()
        selection = router.select(
            requested_model=requested_model,
            team_id=team_id,
            agent_id=agent_id,
            intent=intent,
        )
        candidates = [selection.model] + selection.fallbacks
        last_error: Optional[str] = None

        simulate = overrides.get("simulate_failure") if overrides else None
        force_models = set((simulate or {}).get("model_ids", []) or [])
        force_provider = (simulate or {}).get("provider")
        simulate_enabled = bool((simulate or {}).get("enabled"))

        for index, model in enumerate(candidates):
            start_time = time.monotonic()
            provider = self._providers.get(model.provider)
            if not provider:
                last_error = f"Provider {model.provider} unavailable"
                continue
            if simulate_enabled and (model.model_id in force_models or (force_provider and model.provider == force_provider)):
                last_error = "Simulated provider failure"
                await record_llm_event(
                    action="MODEL_ERROR",
                    actor_id=actor_id or agent_id or "system",
                    model_id=model.model_id,
                    metadata={"error": last_error, "simulated": True},
                    provider=model.provider,
                    model_name=model.model_name,
                    version_pin=model.version_pin,
                    run_id=run_id,
                    turn_id=turn_id,
                    team_id=team_id,
                    agent_id=agent_id,
                    trace_id=trace_id,
                )
                await record_llm_telemetry_event(
                    action="MODEL_ERROR",
                    model_id=model.model_id,
                    provider=model.provider,
                    model_name=model.model_name,
                    run_id=run_id,
                    turn_id=turn_id,
                    team_id=team_id,
                    agent_id=agent_id,
                    trace_id=trace_id,
                    latency_ms=(time.monotonic() - start_time) * 1000,
                    schema_valid=False,
                    error=last_error,
                )
                continue
            await record_llm_event(
                action="MODEL_SELECTED",
                actor_id=actor_id or agent_id or "system",
                model_id=model.model_id,
                metadata={"attempt": index + 1},
                provider=model.provider,
                model_name=model.model_name,
                version_pin=model.version_pin,
                run_id=run_id,
                turn_id=turn_id,
                team_id=team_id,
                agent_id=agent_id,
                trace_id=trace_id,
            )
            response_format = None
            if response_schema and model.supports_json_mode:
                response_format = {"type": "json_object"}
            normalized_tools = normalize_outbound_tools(model.provider, self._tool_registry)
            try:
                result = await self._execute(
                    provider,
                    model.model_name,
                    messages,
                    max_tokens=max_tokens,
                    tools=tools or normalized_tools,
                    response_format=response_format,
                )
                normalized_calls = normalize_inbound_tool_calls(
                    model.provider,
                    result.tool_calls,
                    requested_by=agent_id or actor_id,
                )
                for tool_call in normalized_calls:
                    tool_name = tool_call.get("tool_name")
                    if not tool_name:
                        await record_llm_event(
                            action="TOOL_CALL_INVALID",
                            actor_id=actor_id or agent_id or "system",
                            model_id=model.model_id,
                            metadata={"error": "Missing tool name"},
                            provider=model.provider,
                            model_name=model.model_name,
                            version_pin=model.version_pin,
                            run_id=run_id,
                            turn_id=turn_id,
                            team_id=team_id,
                            agent_id=agent_id,
                            trace_id=trace_id,
                        )
                        continue
                    arguments = tool_call.get("arguments") or {}
                    err = validate_tool_call(tool_name, arguments, self._tool_registry)
                    if err:
                        await record_llm_event(
                            action="TOOL_CALL_INVALID",
                            actor_id=actor_id or agent_id or "system",
                            model_id=model.model_id,
                            metadata={"error": err, "tool": tool_name},
                            provider=model.provider,
                            model_name=model.model_name,
                            version_pin=model.version_pin,
                            run_id=run_id,
                            turn_id=turn_id,
                            team_id=team_id,
                            agent_id=agent_id,
                            trace_id=trace_id,
                        )
                    else:
                        await record_llm_event(
                            action="TOOL_CALL",
                            actor_id=actor_id or agent_id or "system",
                            model_id=model.model_id,
                            metadata={
                                "tool": tool_name,
                                "trace_id": tool_call.get("trace_id"),
                                "arguments_hash": compute_checksum({"tool": tool_name, "args": arguments}),
                            },
                            provider=model.provider,
                            model_name=model.model_name,
                            version_pin=model.version_pin,
                            run_id=run_id,
                            turn_id=turn_id,
                            team_id=team_id,
                            agent_id=agent_id,
                            trace_id=trace_id,
                        )
                ok, payload, error = validate_json_payload(result.content, response_schema)
                if ok:
                    await record_llm_telemetry_event(
                        action="SUCCESS",
                        model_id=model.model_id,
                        provider=model.provider,
                        model_name=model.model_name,
                        run_id=run_id,
                        turn_id=turn_id,
                        team_id=team_id,
                        agent_id=agent_id,
                        trace_id=trace_id,
                        latency_ms=(time.monotonic() - start_time) * 1000,
                        schema_valid=True,
                    )
                    if payload is not None:
                        return json.dumps(payload, sort_keys=True, ensure_ascii=False)
                    return result.content
                await record_llm_event(
                    action="SCHEMA_REPAIR",
                    actor_id=actor_id or agent_id or "system",
                    model_id=model.model_id,
                    metadata={"error": error},
                    provider=model.provider,
                    model_name=model.model_name,
                    version_pin=model.version_pin,
                    run_id=run_id,
                    turn_id=turn_id,
                    team_id=team_id,
                    agent_id=agent_id,
                    trace_id=trace_id,
                )
                repair_messages = [
                    {"role": "system", "content": "Return ONLY valid JSON that matches the expected schema."},
                    *messages,
                ]
                repair = await self._execute(
                    provider,
                    model.model_name,
                    repair_messages,
                    max_tokens=max_tokens,
                    tools=tools or normalized_tools,
                    response_format={"type": "json_object"} if model.supports_json_mode else None,
                )
                ok, payload, error = validate_json_payload(repair.content, response_schema)
                if ok:
                    await record_llm_telemetry_event(
                        action="REPAIR_SUCCESS",
                        model_id=model.model_id,
                        provider=model.provider,
                        model_name=model.model_name,
                        run_id=run_id,
                        turn_id=turn_id,
                        team_id=team_id,
                        agent_id=agent_id,
                        trace_id=trace_id,
                        latency_ms=(time.monotonic() - start_time) * 1000,
                        schema_valid=True,
                        repair_used=True,
                    )
                    if payload is not None:
                        return json.dumps(payload, sort_keys=True, ensure_ascii=False)
                    return repair.content
                last_error = error or "Schema repair failed"
            except Exception as exc:
                last_error = str(exc)
                await record_llm_event(
                    action="MODEL_ERROR",
                    actor_id=actor_id or agent_id or "system",
                    model_id=model.model_id,
                    metadata={"error": last_error},
                    provider=model.provider,
                    model_name=model.model_name,
                    version_pin=model.version_pin,
                    run_id=run_id,
                    turn_id=turn_id,
                    team_id=team_id,
                    agent_id=agent_id,
                    trace_id=trace_id,
                )
                await record_llm_telemetry_event(
                    action="MODEL_ERROR",
                    model_id=model.model_id,
                    provider=model.provider,
                    model_name=model.model_name,
                    run_id=run_id,
                    turn_id=turn_id,
                    team_id=team_id,
                    agent_id=agent_id,
                    trace_id=trace_id,
                    latency_ms=(time.monotonic() - start_time) * 1000,
                    schema_valid=False,
                    error=last_error,
                )
                continue

            if index < len(candidates) - 1:
                await record_llm_event(
                    action="FALLBACK_USED",
                    actor_id=actor_id or agent_id or "system",
                    model_id=model.model_id,
                    metadata={"error": last_error},
                    provider=model.provider,
                    model_name=model.model_name,
                    version_pin=model.version_pin,
                    run_id=run_id,
                    turn_id=turn_id,
                    team_id=team_id,
                    agent_id=agent_id,
                    trace_id=trace_id,
                )
                await record_llm_telemetry_event(
                    action="FALLBACK_USED",
                    model_id=model.model_id,
                    provider=model.provider,
                    model_name=model.model_name,
                    run_id=run_id,
                    turn_id=turn_id,
                    team_id=team_id,
                    agent_id=agent_id,
                    trace_id=trace_id,
                    latency_ms=(time.monotonic() - start_time) * 1000,
                    schema_valid=False,
                    fallback_used=True,
                    error=last_error,
                )

        failure = LLMFailure(error_type="LLM_FAILURE", message=last_error or "LLM failure")
        return failure.model_dump_json()

    async def embeddings(self, text: str, requested_model: Optional[str] = None) -> List[float]:
        selection = self._router.select(requested_model=requested_model)
        provider = self._providers.get(selection.model.provider) or LocalProvider()
        return await provider.embeddings(selection.model.model_name, text)
