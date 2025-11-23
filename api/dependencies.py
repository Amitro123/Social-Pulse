import time
import asyncio
from typing import Any, Callable, Dict, Hashable, Tuple
from dataclasses import dataclass
from api import config

@dataclass
class CacheEntry:
    value: Any
    expires_at: float

class TTLCache:
    def __init__(self, ttl_seconds: int):
        self.ttl = ttl_seconds
        self.store: Dict[Hashable, CacheEntry] = {}

    def get(self, key: Hashable):
        now = time.time()
        entry = self.store.get(key)
        if not entry:
            return None
        if entry.expires_at < now:
            self.store.pop(key, None)
            return None
        return entry.value

    def set(self, key: Hashable, value: Any):
        self.store[key] = CacheEntry(value=value, expires_at=time.time() + self.ttl)

cache = TTLCache(config.CACHE_TTL_SECONDS)

# Simple async rate limiter (token every 1/QPS seconds)
_last_call_ts: float = 0.0
_lock = asyncio.Lock()

async def rate_limit():
    global _last_call_ts
    async with _lock:
        min_interval = 1.0 / max(config.RATE_LIMIT_QPS, 0.1)
        now = time.time()
        to_wait = max(0.0, (_last_call_ts + min_interval) - now)
        if to_wait > 0:
            await asyncio.sleep(to_wait)
        _last_call_ts = time.time()
