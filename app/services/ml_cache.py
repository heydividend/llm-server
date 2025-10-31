"""
ML Cache Service for Harvey

Provides in-memory caching for ML API calls to avoid repeated requests
and improve performance.
"""

import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger("ml_cache")


class MLCache:
    """
    In-memory cache for ML API responses.
    
    Features:
    - TTL-based expiration (default: 6 hours as per ML API best practices)
    - Automatic cleanup of expired entries
    - Cache hit/miss tracking for monitoring
    """
    
    def __init__(self, default_ttl_seconds: int = 21600):  # 6 hours
        """
        Initialize ML cache.
        
        Args:
            default_ttl_seconds: Default time-to-live for cached entries (default: 6 hours)
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl_seconds
        self.hits = 0
        self.misses = 0
        self.last_cleanup = time.time()
        
        logger.info(f"ML cache initialized with {default_ttl_seconds}s TTL")
    
    def _make_key(self, endpoint: str, params: Dict[str, Any]) -> str:
        """
        Generate cache key from endpoint and parameters.
        
        Args:
            endpoint: ML API endpoint (e.g., 'score_symbol', 'predict_yield')
            params: Request parameters
            
        Returns:
            Cache key string
        """
        # Sort params for consistent keys
        param_str = str(sorted(params.items()))
        return f"{endpoint}:{param_str}"
    
    def get(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get cached ML API response.
        
        Args:
            endpoint: ML API endpoint
            params: Request parameters
            
        Returns:
            Cached response if exists and not expired, None otherwise
        """
        key = self._make_key(endpoint, params)
        
        # Cleanup expired entries periodically (every 5 minutes)
        if time.time() - self.last_cleanup > 300:
            self._cleanup_expired()
        
        if key in self.cache:
            entry = self.cache[key]
            
            # Check if expired
            if time.time() < entry["expires_at"]:
                self.hits += 1
                logger.debug(f"Cache HIT: {endpoint} (hit rate: {self.get_hit_rate():.1%})")
                return entry["data"]
            else:
                # Expired - remove it
                del self.cache[key]
                logger.debug(f"Cache EXPIRED: {endpoint}")
        
        self.misses += 1
        logger.debug(f"Cache MISS: {endpoint} (hit rate: {self.get_hit_rate():.1%})")
        return None
    
    def set(self, endpoint: str, params: Dict[str, Any], data: Dict[str, Any], ttl: Optional[int] = None):
        """
        Cache ML API response.
        
        Args:
            endpoint: ML API endpoint
            params: Request parameters
            data: Response data to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        key = self._make_key(endpoint, params)
        expires_at = time.time() + (ttl or self.default_ttl)
        
        self.cache[key] = {
            "data": data,
            "expires_at": expires_at,
            "cached_at": time.time()
        }
        
        logger.debug(f"Cache SET: {endpoint} (expires in {ttl or self.default_ttl}s)")
    
    def _cleanup_expired(self):
        """Remove expired cache entries."""
        now = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if now >= entry["expires_at"]
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            logger.info(f"Cache cleanup: removed {len(expired_keys)} expired entries")
        
        self.last_cleanup = now
    
    def clear(self):
        """Clear all cache entries."""
        count = len(self.cache)
        self.cache.clear()
        logger.info(f"Cache cleared: {count} entries removed")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Cache stats including hit rate, size, etc.
        """
        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0.0
        
        return {
            "hits": self.hits,
            "misses": self.misses,
            "total_requests": total_requests,
            "hit_rate": hit_rate,
            "cache_size": len(self.cache),
            "default_ttl_seconds": self.default_ttl
        }
    
    def get_hit_rate(self) -> float:
        """Get current cache hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


# Global cache instance
_ml_cache = None


def get_ml_cache() -> MLCache:
    """Get or create global ML cache instance."""
    global _ml_cache
    if _ml_cache is None:
        _ml_cache = MLCache()
    return _ml_cache


def clear_ml_cache():
    """Clear the global ML cache."""
    global _ml_cache
    if _ml_cache:
        _ml_cache.clear()
