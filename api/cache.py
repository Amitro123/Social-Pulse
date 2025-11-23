from datetime import datetime
from typing import Dict, Any, Optional, Tuple
import asyncio

class CacheManager:
    """Smart cache with TTL and duplicate request prevention"""
    
    def __init__(self, default_ttl_minutes: int = 10):
        self.cache: Dict[str, Tuple[Any, datetime]] = {}
        self.active_requests: Dict[str, asyncio.Task] = {}
        self.default_ttl = default_ttl_minutes
    
    def get(self, key: str, max_age_minutes: Optional[int] = None) -> Optional[Dict]:
        """Get cached value if not expired"""
        if key not in self.cache:
            return None
        
        data, timestamp = self.cache[key]
        age_minutes = (datetime.now() - timestamp).total_seconds() / 60
        ttl = max_age_minutes or self.default_ttl
        
        if age_minutes < ttl:
            return {
                "data": data,
                "cached": True,
                "cached_at": timestamp.isoformat(),
                "age_minutes": round(age_minutes, 1),
                "expires_in_minutes": round(ttl - age_minutes, 1)
            }
        
        return None
    
    def set(self, key: str, value: Any):
        """Cache value with current timestamp"""
        self.cache[key] = (value, datetime.now())
    
    def clear(self, pattern: Optional[str] = None):
        """Clear cache (all or by pattern)"""
        if pattern:
            keys_to_delete = [k for k in list(self.cache.keys()) if pattern in k]
            for key in keys_to_delete:
                del self.cache[key]
        else:
            self.cache.clear()
    
    async def get_or_compute(self, key: str, compute_fn, force_refresh: bool = False):
        """Get from cache or compute (prevents duplicate work)"""
        
        # Check cache first
        if not force_refresh:
            cached = self.get(key)
            if cached:
                return cached
        
        # Check if already computing
        if key in self.active_requests:
            result = await self.active_requests[key]
            return {"data": result, "cached": False, "note": "waited for active request"}
        
        # Compute new value
        task = asyncio.create_task(compute_fn())
        self.active_requests[key] = task
        
        try:
            result = await task
            self.set(key, result)
            return {"data": result, "cached": False, "fresh": True}
        finally:
            del self.active_requests[key]

# Global instance
cache_manager = CacheManager(default_ttl_minutes=10)
