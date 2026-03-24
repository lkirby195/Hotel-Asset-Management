import logging

import redis.asyncio as redis

from app.config import settings

logger = logging.getLogger(__name__)

_pool: redis.ConnectionPool | None = None
_redis_available: bool | None = None


def get_redis_pool() -> redis.ConnectionPool | None:
    global _pool, _redis_available
    if _redis_available is False:
        return None
    if _pool is None:
        try:
            _pool = redis.ConnectionPool.from_url(
                settings.redis_url,
                decode_responses=True,
            )
            _redis_available = True
        except Exception:
            logger.warning("Redis not available, caching disabled")
            _redis_available = False
            return None
    return _pool


async def get_redis() -> redis.Redis | None:
    pool = get_redis_pool()
    if pool is None:
        return None
    try:
        client = redis.Redis(connection_pool=pool)
        await client.ping()
        return client
    except Exception:
        logger.warning("Redis connection failed, caching disabled")
        return None
