"""Tool call normalization helpers."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import json

from app.llm.tool_registry import ToolSpec


def normalize_inbound_tool_calls(
    provider: str,
    tool_calls: Optional[List[Dict[str, Any]]],
    requested_by: Optional[str] = None,
) -> List[Dict[str, Any]]:
    if not tool_calls:
        return []
    normalized: List[Dict[str, Any]] = []
    for call in tool_calls:
        if provider == "openai":
            function = call.get("function") or {}
            name = function.get("name") or call.get("name")
            raw_args = function.get("arguments") or call.get("arguments") or {}
            arguments = raw_args
            if isinstance(raw_args, str):
                try:
                    arguments = json.loads(raw_args)
                except json.JSONDecodeError:
                    arguments = {"_raw": raw_args}
            normalized.append(
                {
                    "tool_name": name,
                    "arguments": arguments,
                    "trace_id": call.get("id"),
                    "requested_by": requested_by,
                }
            )
        else:
            name = call.get("tool_name") or call.get("name")
            arguments = call.get("arguments") or call.get("params") or {}
            normalized.append(
                {
                    "tool_name": name,
                    "arguments": arguments,
                    "trace_id": call.get("trace_id") or call.get("id"),
                    "requested_by": requested_by,
                }
            )
    return normalized


def normalize_outbound_tools(provider: str, registry: Dict[str, ToolSpec]) -> Optional[List[Dict[str, Any]]]:
    if not registry:
        return None
    if provider == "openai":
        tools = []
        for name, spec in registry.items():
            tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": name,
                        "description": f"Tool: {name}",
                        "parameters": spec.schema,
                    },
                }
            )
        return tools
    return [
        {
            "tool_name": name,
            "schema": spec.schema,
        }
        for name, spec in registry.items()
    ]
