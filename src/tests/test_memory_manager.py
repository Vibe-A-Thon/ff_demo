import pytest
from core.memory.manager import MemoryManager
from unittest.mock import MagicMock


def test_memory_manager_initialization():
    mock_vector = MagicMock()
    mock_relational = MagicMock()

    manager = MemoryManager(
        vector_memory=mock_vector, relational_memory=mock_relational
    )

    assert manager.vector == mock_vector
    assert manager.relational == mock_relational


def test_remember_battle():
    mock_vector = MagicMock()
    mock_relational = MagicMock()
    manager = MemoryManager(
        vector_memory=mock_vector, relational_memory=mock_relational
    )

    battle_data = {"description": "Red team won using SQL injection"}
    manager.remember_battle("123", battle_data)

    mock_vector.add.assert_called_with(
        text="Red team won using SQL injection",
        metadata={"type": "battle", "battle_id": "123"},
        doc_id="battle_123",
    )


def test_retrieve_context():
    mock_vector = MagicMock()
    mock_relational = MagicMock()
    manager = MemoryManager(
        vector_memory=mock_vector, relational_memory=mock_relational
    )

    mock_vector.query.return_value = [{"id": "1", "document": "test"}]

    context = manager.retrieve_context("SQL injection")

    assert len(context["similar_events"]) == 1
    assert context["similar_events"][0]["id"] == "1"
