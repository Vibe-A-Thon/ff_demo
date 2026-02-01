"""Provider abstraction layer definitions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Protocol


@dataclass
class LLMUsage:
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


@dataclass
class LLMResult:
    content: str
    provider: str
    model_id: str
    model_name: str
    usage: Optional[LLMUsage] = None
    raw: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None


class LLMProvider(Protocol):
    provider_id: str

    async def generate(
        self,
        model_name: str,
        messages: List[Dict[str, str]],
        max_tokens: int | None = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> LLMResult:
        ...

    async def stream_generate(
        self,
        model_name: str,
        messages: List[Dict[str, str]],
        max_tokens: int | None = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> Iterable[str]:
        ...

    async def embeddings(self, model_name: str, text: str) -> List[float]:
        ...
