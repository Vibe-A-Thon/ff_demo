"""Tool registry loader and validator."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional
from pathlib import Path
import yaml
from jsonschema import validate, ValidationError

from app.config import ROOT_DIR


@dataclass(frozen=True)
class ToolSpec:
    name: str
    schema: Dict[str, Any]
    allowed_teams: Optional[list[str]] = None


def _default_tool_registry_path() -> Path:
    return ROOT_DIR / "llm" / "configs" / "tool_registry.yaml"


def load_tool_registry(path: Optional[Path] = None) -> Dict[str, ToolSpec]:
    registry_path = path or _default_tool_registry_path()
    if not registry_path.exists():
        return {}
    with registry_path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    registry: Dict[str, ToolSpec] = {}
    for entry in payload.get("tools", []) or []:
        name = entry.get("name")
        schema = entry.get("schema")
        if not name or not schema:
            continue
        registry[name] = ToolSpec(name=name, schema=schema, allowed_teams=entry.get("allowed_teams"))
    return registry


def validate_tool_call(tool_name: str, arguments: Dict[str, Any], registry: Dict[str, ToolSpec]) -> Optional[str]:
    spec = registry.get(tool_name)
    if not spec:
        return f"Tool {tool_name} is not registered."
    try:
        validate(instance=arguments, schema=spec.schema)
    except ValidationError as exc:
        return f"Tool {tool_name} arguments invalid: {exc.message}"
    return None
