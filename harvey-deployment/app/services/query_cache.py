"""
Query Result Caching Service

Caches static reference data and frequently-accessed queries:
- Ticker metadata (24 hour TTL)
- ML cluster dashboard (12 hour TTL)
- Common dividend queries (1 hour TTL)

Expected Results:
- Faster repeated queries
- Reduced database load
- Better user experience
"""

import time
import logging
from typing import Dict, Any, Optional, Callable
from collections import OrderedDict
from functools import wraps

logger = logging.getLogger("query_cache")


class QueryCache:
    """
    Cache for database query results and reference data.
    
    Features:
    - Configurable TTL per query type
    - LRU eviction
    - Automatic expiration
    - Cache statistics
    """
    
    def __init__(self, max_size: int = 500):
        """
        Initialize query cache.
        
        Args:
            max_size: Maximum number of cached entries
        """
        self.cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        
        # Default TTLs for different query types
        self.default_ttls = {
            "ticker_metadata": 86400,      # 24 hours
            "ml_cluster_dashboard": 43200, # 12 hours
            "dividend_query": 3600,        # 1 hour
            "price_query": 300,            # 5 minutes
            "default": 1800                # 30 minutes
        }
        
        logger.info(f"Query cache initialized with max_size={max_size}")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get cached query result.
        
        Args:
            key: Cache key
            
        Returns:
            Cached result or None
        """
        if key in self.cache:
            entry = self.cache[key]
            
            # Check if expired
            if time.time() < entry["expires_at"]:
                # Move to end (LRU)
                self.cache.move_to_end(key)
                self.hits += 1
                logger.debug(f"Query cache HIT: {key[:50]}... (hit rate: {self.get_hit_rate():.1%})")
                return entry["data"]
            else:
                # Expired - remove it
                del self.cache[key]
                logger.debug(f"Query cache EXPIRED: {key[:50]}...")
        
        self.misses += 1
        logger.debug(f"Query cache MISS: {key[:50]}... (hit rate: {self.get_hit_rate():.1%})")
        return None
    
    def set(self, key: str, data: Any, ttl: Optional[int] = None, query_type: str = "default"):
        """
        Cache query result.
        
        Args:
            key: Cache key
            data: Query result to cache
            ttl: Time-to-live in seconds (uses default for query_type if None)
            query_type: Type of query for default TTL lookup
        """
        if ttl is None:
            ttl = self.default_ttls.get(query_type, self.default_ttls["default"])
        
        # Check if we need to evict entries (LRU)
        if len(self.cache) >= self.max_size and key not in self.cache:
            evicted_key, _ = self.cache.popitem(last=False)
            self.evictions += 1
            logger.debug(f"Query cache EVICTION (LRU): {evicted_key[:50]}...")
        
        expires_at = time.time() + ttl
        
        self.cache[key] = {
            "data": data,
            "expires_at": expires_at,
            "cached_at": time.time(),
            "query_type": query_type
        }
        
        # Move to end (most recently used)
        self.cache.move_to_end(key)
        
        logger.debug(f"Query cache SET: {key[:50]}... (ttl={ttl}s, type={query_type})")
    
    def clear(self):
        """Clear all cache entries."""
        count = len(self.cache)
        self.cache.clear()
        logger.info(f"Query cache cleared: {count} entries removed")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0.0
        utilization = len(self.cache) / self.max_size if self.max_size > 0 else 0.0
        
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "total_requests": total_requests,
            "hit_rate": hit_rate,
            "cache_size": len(self.cache),
            "max_size": self.max_size,
            "utilization": utilization
        }
    
    def get_hit_rate(self) -> float:
        """Get current cache hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


# Decorator for caching query results
def cached_query(query_type: str = "default", ttl: Optional[int] = None, key_func: Optional[Callable] = None):
    """
    Decorator to cache query results.
    
    Args:
        query_type: Type of query for default TTL
        ttl: Custom TTL in seconds
        key_func: Function to generate cache key from arguments
    
    Example:
        @cached_query(query_type="ticker_metadata", ttl=86400)
        def get_ticker_info(symbol: str):
            # Query database
            return result
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_query_cache()
            
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default: use function name and arguments
                cache_key = f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
            
            # Check cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute query
            result = func(*args, **kwargs)
            
            # Cache result
            cache.set(cache_key, result, ttl=ttl, query_type=query_type)
            
            return result
        
        return wrapper
    return decorator


# Global query cache instance
_query_cache: Optional[QueryCache] = None


def get_query_cache() -> QueryCache:
    """Get or create global query cache instance."""
    global _query_cache
    if _query_cache is None:
        _query_cache = QueryCache()
    return _query_cache


def clear_query_cache():
    """Clear the global query cache."""
    global _query_cache
    if _query_cache:
        _query_cache.clear()
