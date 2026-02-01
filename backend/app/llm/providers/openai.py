"""OpenAI provider adapter."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from openai import AsyncOpenAI

from app.llm.providers.base import LLMProvider, LLMResult, LLMUsage


class OpenAIProvider(LLMProvider):
    provider_id = "openai"

    def __init__(self, api_key: str) -> None:
        self._client = AsyncOpenAI(api_key=api_key)

    async def generate(
        self,
        model_name: str,
        messages: List[Dict[str, str]],
        max_tokens: int | None = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> LLMResult:
        response = await self._client.chat.completions.create(
            model=model_name,
            messages=messages,
            max_tokens=max_tokens,
            tools=tools,
            response_format=response_format,
        )
        choice = response.choices[0]
        content = choice.message.content or ""
        usage = None
        if response.usage:
            usage = LLMUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
            )
        return LLMResult(
            content=content,
            provider=self.provider_id,
            model_id=model_name,
            model_name=model_name,
            usage=usage,
            raw=response.model_dump() if hasattr(response, "model_dump") else None,
            tool_calls=[tc.model_dump() for tc in (choice.message.tool_calls or [])]
            if getattr(choice.message, "tool_calls", None)
            else None,
        )

    async def stream_generate(
        self,
        model_name: str,
        messages: List[Dict[str, str]],
        max_tokens: int | None = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> Iterable[str]:
        stream = await self._client.chat.completions.create(
            model=model_name,
            messages=messages,
            max_tokens=max_tokens,
            tools=tools,
            response_format=response_format,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta and delta.content:
                yield delta.content

    async def embeddings(self, model_name: str, text: str) -> List[float]:
        response = await self._client.embeddings.create(model=model_name, input=text)
        return response.data[0].embedding
