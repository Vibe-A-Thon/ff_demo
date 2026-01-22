import pytest
import pytest_asyncio
import asyncio
from core.messaging import MessageBroker
import json
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_redis():
    with patch("redis.asyncio.from_url") as mock:
        mock_redis_instance = AsyncMock()
        mock.return_value = mock_redis_instance

        # Mock pubsub
        mock_pubsub = AsyncMock()
        # pubsub() is synchronous in redis-py mostly but returns a PubSub object
        # In async redis, client.pubsub() returns a PubSub instance immediately
        # We need to make sure that mock_redis_instance.pubsub() returns mock_pubsub
        # Since mock_redis_instance is an AsyncMock, its methods are AsyncMocks by default.
        # We need to explicitly set pubsub to be a MagicMock (synchronous)
        mock_redis_instance.pubsub = MagicMock(return_value=mock_pubsub)

        # Mock subscribe to be an async method
        mock_pubsub.subscribe = AsyncMock()

        # Mock listen to return an async iterator
        async def mock_listen():
            yield {
                "type": "subscribe",
                "pattern": None,
                "channel": "test_channel",
                "data": 1,
            }
            yield {
                "type": "message",
                "pattern": None,
                "channel": "test_channel",
                "data": json.dumps({"test": "data"}),
            }

        mock_pubsub.listen = mock_listen

        yield mock_redis_instance


@pytest.mark.asyncio
async def test_connect(mock_redis):
    broker = MessageBroker()
    await broker.connect()
    assert broker.redis is not None


@pytest.mark.asyncio
async def test_publish(mock_redis):
    broker = MessageBroker()
    await broker.connect()
    await broker.publish("test_channel", {"hello": "world"})

    mock_redis.publish.assert_called_with(
        "test_channel", json.dumps({"hello": "world"})
    )


@pytest.mark.asyncio
async def test_subscribe(mock_redis):
    broker = MessageBroker()
    await broker.connect()

    received_messages = []

    async def callback(data):
        received_messages.append(data)

    task = await broker.subscribe("test_channel", callback)

    # Give the loop a chance to process the message
    await asyncio.sleep(0.1)
    task.cancel()

    assert len(received_messages) == 1
    assert received_messages[0] == {"test": "data"}
