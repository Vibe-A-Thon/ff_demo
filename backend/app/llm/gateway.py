"""Gateway adapter that matches the legacy LLMClient protocol."""

from __future__ import annotations

from typing import Dict, List, Optional

from app.core.external_services import LLMClient
from app.llm.service import LLMService


class LLMGateway(LLMClient):
    def __init__(self, service: Optional[LLMService] = None) -> None:
        self._service = service or LLMService()

    async def embeddings_create(self, model: str, input: str) -> List[float]:
        return await self._service.embeddings(input, requested_model=model)

    async def chat_completions_create(
        self,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: int,
    ) -> str:
        return await self._service.generate(
            messages=messages,
            max_tokens=max_tokens,
            requested_model=model,
        )
