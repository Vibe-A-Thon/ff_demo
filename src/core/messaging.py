import redis.asyncio as redis
import json
import asyncio
from typing import Any, Callable, Awaitable
import os


class MessageBroker:
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis: redis.Redis = None
        self.pubsub = None

    async def connect(self):
        if not self.redis:
            self.redis = redis.from_url(
                self.redis_url, encoding="utf-8", decode_responses=True
            )

    async def disconnect(self):
        if self.redis:
            await self.redis.close()
            self.redis = None

    async def publish(self, channel: str, message: dict):
        if not self.redis:
            await self.connect()
        await self.redis.publish(channel, json.dumps(message))

    async def subscribe(
        self, channel: str, callback: Callable[[dict], Awaitable[None]]
    ):
        if not self.redis:
            await self.connect()

        if not self.pubsub:
            self.pubsub = self.redis.pubsub()

        await self.pubsub.subscribe(channel)

        async def listener():
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])
                    await callback(data)

        # Return the listener task so it can be managed if needed
        return asyncio.create_task(listener())
