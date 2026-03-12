import json

import redis.asyncio as redis


class CacheService:
    DEFAULT_TTL = 3600  # 1 hour

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def get(self, key: str) -> dict | None:
        data = await self.redis.get(key)
        if data:
            return json.loads(data)
        return None

    async def set(self, key: str, data: dict, ttl: int | None = None) -> None:
        await self.redis.setex(
            key,
            ttl or self.DEFAULT_TTL,
            json.dumps(data, default=str),
        )

    async def invalidate_pattern(self, pattern: str) -> int:
        """Delete all keys matching the given pattern. Returns count deleted."""
        count = 0
        async for key in self.redis.scan_iter(match=pattern, count=100):
            await self.redis.delete(key)
            count += 1
        return count
