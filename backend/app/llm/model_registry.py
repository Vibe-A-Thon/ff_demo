"""Model registry loading and validation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional
from pathlib import Path
import yaml

from app.config import ROOT_DIR


@dataclass(frozen=True)
class ModelSpec:
    model_id: str
    provider: str
    model_name: str
    version_pin: str | None = None
    context_window: int | None = None
    supports_tools: bool = False
    supports_json_mode: bool = False
    supports_streaming: bool = False
    latency_class: str | None = None
    cost_class: str | None = None
    reliability_score: float | None = None
    safety_level: str | None = None
    max_tool_calls: int | None = None
    max_output_tokens: int | None = None


def _default_registry_path() -> Path:
    return ROOT_DIR / "llm" / "configs" / "model_registry.yaml"


def load_model_registry(path: Optional[Path] = None) -> Dict[str, ModelSpec]:
    registry_path = path or _default_registry_path()
    if not registry_path.exists():
        return {}
    with registry_path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    models = payload.get("models", [])
    registry: Dict[str, ModelSpec] = {}
    for entry in models:
        if not entry:
            continue
        model_id = entry.get("id") or entry.get("model_id")
        if not model_id:
            continue
        registry[model_id] = ModelSpec(
            model_id=model_id,
            provider=entry.get("provider", "openai"),
            model_name=entry.get("model_name", model_id),
            version_pin=entry.get("version_pin"),
            context_window=entry.get("context_window"),
            supports_tools=bool(entry.get("supports_tools", False)),
            supports_json_mode=bool(entry.get("supports_json_mode", False)),
            supports_streaming=bool(entry.get("supports_streaming", False)),
            latency_class=entry.get("latency_class"),
            cost_class=entry.get("cost_class"),
            reliability_score=entry.get("reliability_score"),
            safety_level=entry.get("safety_level"),
            max_tool_calls=entry.get("max_tool_calls"),
            max_output_tokens=entry.get("max_output_tokens"),
        )
    return registry
