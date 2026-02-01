import types

import pytest

from app import db as db_module
from app.core.external_services import InMemoryVectorStore, OpenAIClientAdapter, VectorDocument
from app.deps import get_db
from app.rag_utils import get_embedding


class FakeLLMClient:
    async def embeddings_create(self, model: str, input: str):
        return [0.5, 0.25, 0.25]


class FakeOpenAI:
    def __init__(self):
        self.embeddings = types.SimpleNamespace(create=self._create_embedding)
        self.chat = types.SimpleNamespace(completions=types.SimpleNamespace(create=self._create_chat))

    async def _create_embedding(self, model: str, input: str):
        return types.SimpleNamespace(data=[types.SimpleNamespace(embedding=[0.1, 0.2, 0.3])])

    async def _create_chat(self, model: str, messages, max_tokens: int):
        message = types.SimpleNamespace(content="ok")
        return types.SimpleNamespace(choices=[types.SimpleNamespace(message=message)])


@pytest.mark.asyncio
async def test_get_embedding_uses_llm_client():
    vector = await get_embedding("test", llm_client=FakeLLMClient())
    assert vector == [0.5, 0.25, 0.25]


@pytest.mark.asyncio
async def test_openai_client_adapter_maps_methods():
    adapter = OpenAIClientAdapter(FakeOpenAI())
    embedding = await adapter.embeddings_create(model="embed", input="hello")
    assert embedding == [0.1, 0.2, 0.3]
    content = await adapter.chat_completions_create(
        model="chat",
        messages=[{"role": "user", "content": "hi"}],
        max_tokens=10,
    )
    assert content == "ok"


@pytest.mark.asyncio
async def test_in_memory_vector_store_query_orders_by_score():
    store = InMemoryVectorStore()
    await store.upsert(
        "rag",
        [
            VectorDocument(id="a", vector=[1.0, 0.0], metadata={"label": "a"}),
            VectorDocument(id="b", vector=[0.0, 1.0], metadata={"label": "b"}),
        ],
    )
    results = await store.query("rag", [1.0, 0.0], top_k=2)
    assert results[0].id == "a"
    assert results[0].score >= results[1].score


def test_get_db_returns_current_db_instance():
    sentinel = object()
    db_module.db = sentinel
    assert get_db() is sentinel