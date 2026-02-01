"""Local/mock provider adapter for offline fallback."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from app.llm.providers.base import LLMProvider, LLMResult


class LocalProvider(LLMProvider):
    provider_id = "local"

    async def generate(
        self,
        model_name: str,
        messages: List[Dict[str, str]],
        max_tokens: int | None = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> LLMResult:
        last_user = next((m["content"] for m in reversed(messages) if m.get("role") == "user"), "")
        import json

        content = json.dumps(
            {
                "summary": "Local fallback response.",
                "echo": last_user,
            },
            ensure_ascii=False,
        )
        return LLMResult(
            content=content,
            provider=self.provider_id,
            model_id=model_name,
            model_name=model_name,
            metadata={"note": "local-fallback"},
        )

    async def stream_generate(
        self,
        model_name: str,
        messages: List[Dict[str, str]],
        max_tokens: int | None = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> Iterable[str]:
        yield "Local fallback response."

    async def embeddings(self, model_name: str, text: str) -> List[float]:
        return [0.0] * 8
