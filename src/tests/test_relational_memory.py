import pytest
from core.memory.relational import RelationalMemory
from unittest.mock import MagicMock, patch
import psycopg2


@pytest.fixture
def mock_psycopg2():
    with patch("psycopg2.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        yield mock_connect, mock_conn, mock_cursor


def test_initialization():
    memory = RelationalMemory(db_url="postgresql://user:pass@host:5432/db")
    assert memory.db_url == "postgresql://user:pass@host:5432/db"


def test_execute_query_select(mock_psycopg2):
    mock_connect, mock_conn, mock_cursor = mock_psycopg2
    memory = RelationalMemory("postgresql://test")

    mock_cursor.description = [("col1",), ("col2",)]
    mock_cursor.fetchall.return_value = [{"col1": 1, "col2": "test"}]

    results = memory.execute_query("SELECT * FROM table")

    mock_cursor.execute.assert_called_with("SELECT * FROM table", None)
    assert len(results) == 1
    assert results[0]["col1"] == 1


def test_execute_query_insert(mock_psycopg2):
    mock_connect, mock_conn, mock_cursor = mock_psycopg2
    memory = RelationalMemory("postgresql://test")

    mock_cursor.description = None  # No results for INSERT

    results = memory.execute_query("INSERT INTO table VALUES (1)")

    mock_cursor.execute.assert_called_with("INSERT INTO table VALUES (1)", None)
    mock_conn.commit.assert_called_once()
    assert results == []
