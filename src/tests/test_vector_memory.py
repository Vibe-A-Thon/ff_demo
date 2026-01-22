import pytest
from core.memory.vector import VectorMemory
from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_chroma():
    with patch("chromadb.HttpClient") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection

        yield mock_client, mock_collection


def test_initialization(mock_chroma):
    mock_client, mock_collection = mock_chroma
    memory = VectorMemory()

    mock_client.get_or_create_collection.assert_called_with(name="fraud_forge")
    assert memory.collection == mock_collection


def test_add(mock_chroma):
    mock_client, mock_collection = mock_chroma
    memory = VectorMemory()

    doc_id = memory.add("test text", {"type": "test"}, "doc1")

    mock_collection.add.assert_called_with(
        documents=["test text"], metadatas=[{"type": "test"}], ids=["doc1"]
    )
    assert doc_id == "doc1"


def test_query(mock_chroma):
    mock_client, mock_collection = mock_chroma
    memory = VectorMemory()

    mock_collection.query.return_value = {
        "ids": [["doc1"]],
        "documents": [["test text"]],
        "metadatas": [[{"type": "test"}]],
        "distances": [[0.1]],
    }

    results = memory.query("query")

    assert len(results) == 1
    assert results[0]["id"] == "doc1"
    assert results[0]["document"] == "test text"
