import asyncio
import time
import pytest

from api.cache import CacheManager


@pytest.mark.asyncio
async def test_cache_get_set_and_metadata():
    cache = CacheManager(default_ttl_minutes=5)
    cache.set("k1", {"v": 1})
    result = cache.get("k1")
    assert result is not None
    assert result["cached"] is True
    assert result["data"] == {"v": 1}
    assert "cached_at" in result and "age_minutes" in result and "expires_in_minutes" in result


@pytest.mark.asyncio
async def test_cache_ttl_expiry():
    cache = CacheManager(default_ttl_minutes=0.001)  # ~0.06s
    cache.set("k2", 123)
    # Immediately available
    assert cache.get("k2") is not None
    # After sleep, should expire
    await asyncio.sleep(0.2)
    assert cache.get("k2") is None


@pytest.mark.asyncio
async def test_get_or_compute_deduplicates_inflight():
    cache = CacheManager(default_ttl_minutes=1)
    calls = {"count": 0}

    async def slow_compute():
        calls["count"] += 1
        await asyncio.sleep(0.1)
        return "done"

    # Start two concurrent requests for the same key
    res1, res2 = await asyncio.gather(
        cache.get_or_compute("key", slow_compute),
        cache.get_or_compute("key", slow_compute),
    )

    assert calls["count"] == 1  # only computed once
    assert res1["data"] == "done"
    assert res2["data"] == "done"
    # Second wave should be served from cache without recomputation
    res3 = await cache.get_or_compute("key", slow_compute)
    assert res3["cached"] is True
    assert calls["count"] == 1
