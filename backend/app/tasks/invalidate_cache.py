import logging

import redis

from app.cache.keys import tenant_invalidation_pattern
from app.config import settings
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="invalidate_cache")
def invalidate_cache_after_sync(tenant_id: str):
    """Clear all Redis cache keys for the synced tenant."""
    r = redis.from_url(settings.redis_url, decode_responses=True)

    pattern = tenant_invalidation_pattern(tenant_id)
    count = 0
    for key in r.scan_iter(match=pattern, count=100):
        r.delete(key)
        count += 1

    logger.info(f"Invalidated {count} cache keys for tenant {tenant_id}")
    return {"keys_invalidated": count}
