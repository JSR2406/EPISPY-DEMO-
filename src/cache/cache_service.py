"""
Cache service with decorators, TTL management, and cache invalidation.

This module provides a comprehensive caching layer for EpiSPY with:
- Generic caching decorator for expensive operations
- Configurable TTL per cache type
- Cache invalidation strategies
- Cache warming for frequently accessed data
- Cache hit/miss rate monitoring

Example usage:
    from src.cache.cache_service import cache_result, CacheType, CacheService
    
    # Using decorator
    @cache_result(cache_type=CacheType.OUTBREAK_DATA, ttl=300)
    async def get_outbreak_data(location_id: str):
        # Expensive operation
        return await fetch_from_database(location_id)
    
    # Using service directly
    cache_service = CacheService()
    await cache_service.set("key", {"data": "value"}, ttl=60)
    value = await cache_service.get("key")
    
    # Cache warming
    await cache_service.warm_outbreak_cache(location_ids=["loc1", "loc2"])
"""
import json
import hashlib
import functools
from typing import Any, Optional, Dict, List, Callable, Union
from enum import Enum
from datetime import datetime, timedelta

from .redis_client import get_redis_client, RedisClient
from ..utils.logger import api_logger


class CacheType(str, Enum):
    """Cache type enumeration with default TTL values."""
    OUTBREAK_DATA = "outbreak_data"  # TTL: 5 minutes
    RISK_ASSESSMENT = "risk_assessment"  # TTL: 10 minutes
    PREDICTION_RESULTS = "prediction_results"  # TTL: 1 hour
    LOCATION_METADATA = "location_metadata"  # TTL: 24 hours
    AGENT_MEMORY = "agent_memory"  # TTL: 1 hour
    MODEL_INFERENCE = "model_inference"  # TTL: 30 minutes


# Default TTL values in seconds
CACHE_TTL = {
    CacheType.OUTBREAK_DATA: 300,  # 5 minutes
    CacheType.RISK_ASSESSMENT: 600,  # 10 minutes
    CacheType.PREDICTION_RESULTS: 3600,  # 1 hour
    CacheType.LOCATION_METADATA: 86400,  # 24 hours
    CacheType.AGENT_MEMORY: 3600,  # 1 hour
    CacheType.MODEL_INFERENCE: 1800,  # 30 minutes
}


class CacheService:
    """
    Cache service for managing cached data with monitoring and invalidation.
    
    Features:
    - Automatic key generation with namespacing
    - TTL management per cache type
    - Cache hit/miss tracking
    - Batch operations
    - Cache invalidation patterns
    
    Attributes:
        redis: Redis client instance
        hit_count: Number of cache hits
        miss_count: Number of cache misses
        namespace_prefix: Prefix for all cache keys
    """
    
    def __init__(self, namespace_prefix: str = "epispy"):
        """
        Initialize cache service.
        
        Args:
            namespace_prefix: Prefix for all cache keys
        """
        self.namespace_prefix = namespace_prefix
        self.hit_count = 0
        self.miss_count = 0
        self._redis: Optional[RedisClient] = None
    
    async def _get_redis(self) -> RedisClient:
        """Get Redis client (lazy initialization)."""
        if self._redis is None:
            self._redis = await get_redis_client()
        return self._redis
    
    def _make_key(self, cache_type: CacheType, key: str) -> str:
        """
        Generate namespaced cache key.
        
        Args:
            cache_type: Type of cache
            key: Base key
            
        Returns:
            Namespaced key
        """
        return f"{self.namespace_prefix}:{cache_type.value}:{key}"
    
    def _make_pattern(self, cache_type: CacheType, pattern: str = "*") -> str:
        """
        Generate namespaced pattern for key matching.
        
        Args:
            cache_type: Type of cache
            pattern: Pattern to match (supports wildcards)
            
        Returns:
            Namespaced pattern
        """
        return f"{self.namespace_prefix}:{cache_type.value}:{pattern}"
    
    async def get(
        self,
        cache_type: CacheType,
        key: str,
        default: Any = None,
    ) -> Any:
        """
        Get value from cache.
        
        Args:
            cache_type: Type of cache
            key: Cache key
            default: Default value if key not found
            
        Returns:
            Cached value or default
            
        Example:
            value = await cache_service.get(
                CacheType.OUTBREAK_DATA,
                "location:123",
                default={}
            )
        """
        try:
            redis = await self._get_redis()
            cache_key = self._make_key(cache_type, key)
            
            # Try JSON get first
            value = await redis.json_get(cache_key)
            
            if value is not None:
                self.hit_count += 1
                api_logger.debug(f"Cache HIT: {cache_key}")
                return value
            
            self.miss_count += 1
            api_logger.debug(f"Cache MISS: {cache_key}")
            return default
            
        except Exception as e:
            api_logger.error(f"Cache get error: {str(e)}")
            self.miss_count += 1
            return default
    
    async def set(
        self,
        cache_type: CacheType,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Set value in cache.
        
        Args:
            cache_type: Type of cache
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds (defaults to cache type TTL)
            
        Returns:
            True if successful
            
        Example:
            await cache_service.set(
                CacheType.OUTBREAK_DATA,
                "location:123",
                {"cases": 100, "deaths": 5},
                ttl=300
            )
        """
        try:
            redis = await self._get_redis()
            cache_key = self._make_key(cache_type, key)
            
            # Use default TTL if not specified
            if ttl is None:
                ttl = CACHE_TTL.get(cache_type, 3600)
            
            # Store as JSON
            await redis.json_set(cache_key, "$", value, ex=ttl)
            
            api_logger.debug(f"Cache SET: {cache_key} (TTL: {ttl}s)")
            return True
            
        except Exception as e:
            api_logger.error(f"Cache set error: {str(e)}")
            return False
    
    async def delete(self, cache_type: CacheType, key: str) -> bool:
        """
        Delete key from cache.
        
        Args:
            cache_type: Type of cache
            key: Cache key
            
        Returns:
            True if deleted
        """
        try:
            redis = await self._get_redis()
            cache_key = self._make_key(cache_type, key)
            result = await redis.delete(cache_key)
            api_logger.debug(f"Cache DELETE: {cache_key}")
            return result > 0
        except Exception as e:
            api_logger.error(f"Cache delete error: {str(e)}")
            return False
    
    async def invalidate_pattern(
        self,
        cache_type: CacheType,
        pattern: str = "*",
    ) -> int:
        """
        Invalidate all keys matching pattern.
        
        Args:
            cache_type: Type of cache
            pattern: Pattern to match (supports wildcards)
            
        Returns:
            Number of keys deleted
            
        Example:
            # Delete all outbreak data for a location
            count = await cache_service.invalidate_pattern(
                CacheType.OUTBREAK_DATA,
                "location:123:*"
            )
        """
        try:
            redis = await self._get_redis()
            full_pattern = self._make_pattern(cache_type, pattern)
            
            # Use SCAN to find matching keys (more efficient than KEYS)
            deleted_count = 0
            cursor = 0
            
            while True:
                cursor, keys = await redis._execute_with_retry(
                    redis.client.scan, cursor, match=full_pattern, count=100
                )
                
                if keys:
                    deleted_count += await redis.delete(*keys)
                
                if cursor == 0:
                    break
            
            api_logger.info(
                f"Cache invalidated: {deleted_count} keys matching {full_pattern}"
            )
            return deleted_count
            
        except Exception as e:
            api_logger.error(f"Cache invalidation error: {str(e)}")
            return 0
    
    async def invalidate_all(self, cache_type: CacheType) -> int:
        """
        Invalidate all keys of a cache type.
        
        Args:
            cache_type: Type of cache to invalidate
            
        Returns:
            Number of keys deleted
        """
        return await self.invalidate_pattern(cache_type, "*")
    
    async def exists(self, cache_type: CacheType, key: str) -> bool:
        """
        Check if key exists in cache.
        
        Args:
            cache_type: Type of cache
            key: Cache key
            
        Returns:
            True if key exists
        """
        try:
            redis = await self._get_redis()
            cache_key = self._make_key(cache_type, key)
            result = await redis.exists(cache_key)
            return result > 0
        except Exception as e:
            api_logger.error(f"Cache exists check error: {str(e)}")
            return False
    
    async def get_ttl(self, cache_type: CacheType, key: str) -> int:
        """
        Get remaining TTL for key.
        
        Args:
            cache_type: Type of cache
            key: Cache key
            
        Returns:
            TTL in seconds (-1 if no expiration, -2 if key doesn't exist)
        """
        try:
            redis = await self._get_redis()
            cache_key = self._make_key(cache_type, key)
            return await redis.ttl(cache_key)
        except Exception as e:
            api_logger.error(f"Cache TTL check error: {str(e)}")
            return -2
    
    async def extend_ttl(
        self,
        cache_type: CacheType,
        key: str,
        additional_seconds: int,
    ) -> bool:
        """
        Extend TTL for existing key.
        
        Args:
            cache_type: Type of cache
            key: Cache key
            additional_seconds: Seconds to add to current TTL
            
        Returns:
            True if successful
        """
        try:
            redis = await self._get_redis()
            cache_key = self._make_key(cache_type, key)
            current_ttl = await redis.ttl(cache_key)
            
            if current_ttl > 0:
                new_ttl = current_ttl + additional_seconds
                return await redis.expire(cache_key, new_ttl)
            
            return False
        except Exception as e:
            api_logger.error(f"Cache TTL extension error: {str(e)}")
            return False
    
    # Cache warming methods
    async def warm_outbreak_cache(
        self,
        location_ids: List[str],
        fetch_func: Optional[Callable] = None,
    ) -> Dict[str, bool]:
        """
        Warm outbreak data cache for locations.
        
        Args:
            location_ids: List of location IDs to warm
            fetch_func: Optional function to fetch data if not cached
            
        Returns:
            Dictionary mapping location_id to success status
            
        Example:
            results = await cache_service.warm_outbreak_cache(
                ["loc1", "loc2"],
                fetch_func=fetch_outbreak_data
            )
        """
        results = {}
        
        for location_id in location_ids:
            key = f"location:{location_id}"
            
            # Check if already cached
            if await self.exists(CacheType.OUTBREAK_DATA, key):
                results[location_id] = True
                continue
            
            # Fetch and cache if function provided
            if fetch_func:
                try:
                    data = await fetch_func(location_id)
                    await self.set(CacheType.OUTBREAK_DATA, key, data)
                    results[location_id] = True
                except Exception as e:
                    api_logger.error(
                        f"Failed to warm cache for {location_id}: {str(e)}"
                    )
                    results[location_id] = False
            else:
                results[location_id] = False
        
        api_logger.info(
            f"Cache warming completed: {sum(results.values())}/{len(location_ids)} successful"
        )
        return results
    
    async def warm_risk_assessment_cache(
        self,
        location_ids: List[str],
        fetch_func: Optional[Callable] = None,
    ) -> Dict[str, bool]:
        """Warm risk assessment cache for locations."""
        results = {}
        
        for location_id in location_ids:
            key = f"location:{location_id}"
            
            if await self.exists(CacheType.RISK_ASSESSMENT, key):
                results[location_id] = True
                continue
            
            if fetch_func:
                try:
                    data = await fetch_func(location_id)
                    await self.set(CacheType.RISK_ASSESSMENT, key, data)
                    results[location_id] = True
                except Exception as e:
                    api_logger.error(
                        f"Failed to warm risk cache for {location_id}: {str(e)}"
                    )
                    results[location_id] = False
            else:
                results[location_id] = False
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics:
            - hit_count: Number of cache hits
            - miss_count: Number of cache misses
            - hit_rate: Hit rate (0-1)
            - total_requests: Total cache requests
        """
        total = self.hit_count + self.miss_count
        hit_rate = self.hit_count / total if total > 0 else 0.0
        
        return {
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "hit_rate": round(hit_rate, 4),
            "total_requests": total,
        }


def _generate_cache_key(func_name: str, *args, **kwargs) -> str:
    """
    Generate cache key from function name and arguments.
    
    Args:
        func_name: Function name
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        MD5 hash of cache key
    """
    # Create string representation of arguments
    key_parts = [func_name]
    
    # Add positional arguments
    for arg in args:
        if isinstance(arg, (str, int, float, bool)):
            key_parts.append(str(arg))
        elif isinstance(arg, (dict, list)):
            key_parts.append(json.dumps(arg, sort_keys=True))
    
    # Add keyword arguments (sorted for consistency)
    for k, v in sorted(kwargs.items()):
        if isinstance(v, (str, int, float, bool)):
            key_parts.append(f"{k}:{v}")
        elif isinstance(v, (dict, list)):
            key_parts.append(f"{k}:{json.dumps(v, sort_keys=True)}")
    
    # Create hash
    key_string = ":".join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()


def cache_result(
    cache_type: CacheType,
    ttl: Optional[int] = None,
    key_prefix: Optional[str] = None,
    invalidate_on: Optional[List[str]] = None,
):
    """
    Decorator for caching function results.
    
    Args:
        cache_type: Type of cache to use
        ttl: Time to live in seconds (defaults to cache type TTL)
        key_prefix: Optional prefix for cache key
        invalidate_on: List of cache types to invalidate when this function is called
        
    Returns:
        Decorated function
        
    Example:
        @cache_result(cache_type=CacheType.OUTBREAK_DATA, ttl=300)
        async def get_outbreak_data(location_id: str):
            # Expensive operation
            return await expensive_database_query(location_id)
        
        # Function result will be cached for 5 minutes
        data = await get_outbreak_data("loc123")
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            prefix = key_prefix or func.__name__
            cache_key = _generate_cache_key(prefix, *args, **kwargs)
            full_key = f"{prefix}:{cache_key}"
            
            # Get cache service
            cache_service = CacheService()
            
            # Try to get from cache
            cached_value = await cache_service.get(cache_type, full_key)
            
            if cached_value is not None:
                api_logger.debug(f"Cache HIT for {func.__name__}: {full_key}")
                return cached_value
            
            # Cache miss - execute function
            api_logger.debug(f"Cache MISS for {func.__name__}: {full_key}")
            result = await func(*args, **kwargs)
            
            # Store in cache
            await cache_service.set(cache_type, full_key, result, ttl=ttl)
            
            # Invalidate related caches if specified
            if invalidate_on:
                for invalidate_type in invalidate_on:
                    await cache_service.invalidate_all(invalidate_type)
            
            return result
        
        return wrapper
    return decorator


# Convenience functions
async def invalidate_cache(
    cache_type: CacheType,
    pattern: str = "*",
) -> int:
    """
    Invalidate cache by pattern.
    
    Args:
        cache_type: Type of cache
        pattern: Pattern to match
        
    Returns:
        Number of keys deleted
    """
    cache_service = CacheService()
    return await cache_service.invalidate_pattern(cache_type, pattern)


async def warm_cache(
    cache_type: CacheType,
    keys: List[str],
    fetch_func: Optional[Callable] = None,
) -> Dict[str, bool]:
    """
    Warm cache for multiple keys.
    
    Args:
        cache_type: Type of cache
        keys: List of keys to warm
        fetch_func: Function to fetch data (should accept key as argument)
        
    Returns:
        Dictionary mapping keys to success status
    """
    cache_service = CacheService()
    results = {}
    
    for key in keys:
        if await cache_service.exists(cache_type, key):
            results[key] = True
            continue
        
        if fetch_func:
            try:
                data = await fetch_func(key)
                await cache_service.set(cache_type, key, data)
                results[key] = True
            except Exception as e:
                api_logger.error(f"Failed to warm cache for {key}: {str(e)}")
                results[key] = False
        else:
            results[key] = False
    
    return results

