"""Tests for cache key builders and CacheService."""

import uuid

from app.cache.keys import report_cache_key, report_children_cache_key, tenant_invalidation_pattern


class TestCacheKeys:
    def test_report_cache_key_format(self):
        key = report_cache_key("tenant1", "inter_month", "prop1", "mtd", "2026-03-01", "2026-03-12")
        assert key == "hotel_am:tenant1:report:inter_month:prop1:mtd:2026-03-01:2026-03-12"

    def test_report_children_cache_key_format(self):
        key = report_children_cache_key("tenant1", "prop1", "parent1", "mtd")
        assert key == "hotel_am:tenant1:children:prop1:parent1:mtd"

    def test_tenant_invalidation_pattern(self):
        pattern = tenant_invalidation_pattern("tenant1")
        assert pattern == "hotel_am:tenant1:*"

    def test_keys_with_uuids(self):
        tid = str(uuid.uuid4())
        pid = str(uuid.uuid4())
        key = report_cache_key(tid, "inter_month", pid, "ytd", "2026-01-01", "2026-03-12")
        assert tid in key
        assert pid in key
