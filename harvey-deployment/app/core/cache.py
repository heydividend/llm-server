import os
import time
import hashlib
from functools import wraps
from typing import Any, Callable, Optional, Tuple

CACHE_TTL = int(os.getenv("CACHE_TTL_SECONDS", "300"))
CACHE_MAX_SIZE = int(os.getenv("CACHE_MAX_SIZE", "1000"))

_cache_store = {}
_cache_timestamps = {}

def _generate_cache_key(*args, **kwargs) -> str:
    key_data = str(args) + str(sorted(kwargs.items()))
    return hashlib.md5(key_data.encode()).hexdigest()

def _is_cache_valid(cache_key: str) -> bool:
    if cache_key not in _cache_timestamps:
        return False
    age = time.time() - _cache_timestamps[cache_key]
    return age < CACHE_TTL

def _evict_oldest_if_needed():
    if len(_cache_store) >= CACHE_MAX_SIZE:
        oldest_key = min(_cache_timestamps.keys(), key=lambda k: _cache_timestamps[k])
        del _cache_store[oldest_key]
        del _cache_timestamps[oldest_key]

def cached_query(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args, **kwargs):
        cache_key = _generate_cache_key(*args, **kwargs)
        
        if _is_cache_valid(cache_key):
            return _cache_store[cache_key]
        
        result = func(*args, **kwargs)
        
        _evict_oldest_if_needed()
        _cache_store[cache_key] = result
        _cache_timestamps[cache_key] = time.time()
        
        return result
    return wrapper

def invalidate_cache(cache_key: Optional[str] = None):
    if cache_key:
        _cache_store.pop(cache_key, None)
        _cache_timestamps.pop(cache_key, None)
    else:
        _cache_store.clear()
        _cache_timestamps.clear()

def get_cache_stats() -> dict:
    return {
        "size": len(_cache_store),
        "max_size": CACHE_MAX_SIZE,
        "ttl_seconds": CACHE_TTL,
        "entries": list(_cache_store.keys())
    }
