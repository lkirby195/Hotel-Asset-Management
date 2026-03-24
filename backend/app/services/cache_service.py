import json
import logging

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class CacheService:
    DEFAULT_TTL = 3600  # 1 hour

    def __init__(self, redis_client: redis.Redis | None):
        self.redis = redis_client

    async def get(self, key: str) -> dict | None:
        if not self.redis:
            return None
        try:
            data = await self.redis.get(key)
            if data:
                return json.loads(data)
        except Exception:
            logger.warning("Redis cache get failed, skipping cache", exc_info=True)
        return None

    async def set(self, key: str, data: dict, ttl: int | None = None) -> None:
        if not self.redis:
            return
        try:
            await self.redis.setex(
                key,
                ttl or self.DEFAULT_TTL,
                json.dumps(data, default=str),
            )
        except Exception:
            logger.warning("Redis cache set failed, skipping cache", exc_info=True)

    async def invalidate_pattern(self, pattern: str) -> int:
        if not self.redis:
            return 0
        try:
            count = 0
            async for key in self.redis.scan_iter(match=pattern, count=100):
                await self.redis.delete(key)
                count += 1
            return count
        except Exception:
            logger.warning("Redis cache invalidate failed", exc_info=True)
            return 0
