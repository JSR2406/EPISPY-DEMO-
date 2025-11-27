"""
Async Redis client with connection pooling, automatic reconnection, and circuit breaker.

This module provides a production-ready Redis client for EpiSPY with:
- Connection pool management for high performance
- Automatic reconnection with exponential backoff
- Circuit breaker pattern for resilience
- Health checks and monitoring
- JSON support for complex objects

Example usage:
    from src.cache.redis_client import get_redis_client
    
    # Get Redis client
    redis = await get_redis_client()
    
    # Basic operations
    await redis.set("key", "value", ex=60)
    value = await redis.get("key")
    
    # JSON operations
    await redis.json_set("user:123", "$", {"name": "John", "age": 30})
    user = await redis.json_get("user:123", "$")
    
    # Health check
    health = await check_redis_health()
    if health["status"] == "healthy":
        print(f"Redis is healthy, latency: {health['latency_ms']}ms")
"""
import asyncio
import json
import time
from typing import Optional, Dict, Any, Union
from enum import Enum
from contextlib import asynccontextmanager

try:
    from redis.asyncio import Redis, ConnectionPool
    from redis.exceptions import (
        ConnectionError as RedisConnectionError,
        TimeoutError as RedisTimeoutError,
        RedisError,
    )
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    Redis = None
    ConnectionPool = None

from ..utils.config import settings
from ..utils.logger import api_logger


class CircuitBreakerState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "CLOSED"  # Normal operation
    OPEN = "OPEN"  # Failing, reject requests
    HALF_OPEN = "HALF_OPEN"  # Testing if service recovered


class RedisClient:
    """
    Async Redis client with connection pooling and circuit breaker.
    
    Features:
    - Connection pool management
    - Automatic reconnection with exponential backoff
    - Circuit breaker for resilience
    - Health monitoring
    - JSON support
    
    Attributes:
        pool: Redis connection pool
        client: Redis client instance
        circuit_breaker_state: Current circuit breaker state
        failure_count: Number of consecutive failures
        last_failure_time: Timestamp of last failure
        max_failures: Maximum failures before opening circuit
        circuit_timeout: Time to wait before attempting recovery
    """
    
    def __init__(
        self,
        url: Optional[str] = None,
        max_connections: int = 50,
        retry_on_timeout: bool = True,
        socket_connect_timeout: int = 5,
        socket_timeout: int = 5,
        max_failures: int = 5,
        circuit_timeout: int = 60,
    ):
        """
        Initialize Redis client.
        
        Args:
            url: Redis URL (defaults to settings.redis_url)
            max_connections: Maximum connections in pool
            retry_on_timeout: Whether to retry on timeout
            socket_connect_timeout: Connection timeout in seconds
            socket_timeout: Socket timeout in seconds
            max_failures: Max failures before opening circuit breaker
            circuit_timeout: Seconds to wait before attempting recovery
        """
        if not REDIS_AVAILABLE:
            raise ImportError(
                "aioredis not installed. Install with: pip install aioredis"
            )
        
        self.url = url or settings.redis_url
        self.max_connections = max_connections
        self.retry_on_timeout = retry_on_timeout
        self.socket_connect_timeout = socket_connect_timeout
        self.socket_timeout = socket_timeout
        
        # Circuit breaker configuration
        self.max_failures = max_failures
        self.circuit_timeout = circuit_timeout
        self.circuit_breaker_state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        
        # Connection pool and client
        self.pool: Optional[ConnectionPool] = None
        self.client: Optional[Redis] = None
        
        # Metrics
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        
    async def connect(self) -> bool:
        """
        Establish connection to Redis.
        
        Returns:
            True if connection successful, False otherwise
            
        Example:
            client = RedisClient()
            if await client.connect():
                print("Connected to Redis")
        """
        try:
            # Create connection pool
            self.pool = ConnectionPool.from_url(
                self.url,
                max_connections=self.max_connections,
                retry_on_timeout=self.retry_on_timeout,
                socket_connect_timeout=self.socket_connect_timeout,
                socket_timeout=self.socket_timeout,
                decode_responses=True,  # Auto-decode responses
            )
            
            # Create client from pool
            self.client = Redis(connection_pool=self.pool)
            
            # Test connection
            await self.client.ping()
            
            # Reset circuit breaker on successful connection
            self._reset_circuit_breaker()
            
            api_logger.info(f"Connected to Redis: {self.url.split('@')[-1] if '@' in self.url else self.url}")
            return True
            
        except Exception as e:
            api_logger.error(f"Failed to connect to Redis: {str(e)}")
            self._record_failure()
            return False
    
    async def disconnect(self) -> None:
        """
        Close Redis connection and cleanup.
        
        Example:
            await client.disconnect()
        """
        if self.client:
            await self.client.aclose()
            self.client = None
        
        if self.pool:
            await self.pool.aclose()
            self.pool = None
        
        api_logger.info("Redis connection closed")
    
    def _check_circuit_breaker(self) -> bool:
        """
        Check if circuit breaker allows request.
        
        Returns:
            True if request should proceed, False if blocked
        """
        if self.circuit_breaker_state == CircuitBreakerState.CLOSED:
            return True
        
        if self.circuit_breaker_state == CircuitBreakerState.OPEN:
            # Check if timeout has passed
            if (
                self.last_failure_time
                and time.time() - self.last_failure_time > self.circuit_timeout
            ):
                self.circuit_breaker_state = CircuitBreakerState.HALF_OPEN
                api_logger.info("Circuit breaker: HALF_OPEN (testing recovery)")
                return True
            return False
        
        # HALF_OPEN state - allow one request to test
        return True
    
    def _record_failure(self) -> None:
        """Record a failure and update circuit breaker state."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        self.failed_requests += 1
        
        if self.failure_count >= self.max_failures:
            self.circuit_breaker_state = CircuitBreakerState.OPEN
            api_logger.warning(
                f"Circuit breaker: OPEN (after {self.failure_count} failures)"
            )
    
    def _record_success(self) -> None:
        """Record a success and reset circuit breaker if needed."""
        if self.circuit_breaker_state == CircuitBreakerState.HALF_OPEN:
            self._reset_circuit_breaker()
            api_logger.info("Circuit breaker: CLOSED (recovery successful)")
        
        self.successful_requests += 1
    
    def _reset_circuit_breaker(self) -> None:
        """Reset circuit breaker to closed state."""
        self.circuit_breaker_state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
    
    async def _execute_with_retry(
        self,
        operation,
        *args,
        max_retries: int = 3,
        backoff_factor: float = 2.0,
        **kwargs,
    ) -> Any:
        """
        Execute Redis operation with exponential backoff retry.
        
        Args:
            operation: Async function to execute
            *args: Positional arguments for operation
            max_retries: Maximum retry attempts
            backoff_factor: Multiplier for exponential backoff
            **kwargs: Keyword arguments for operation
            
        Returns:
            Result of operation
            
        Raises:
            RedisError: If all retries fail
        """
        if not self._check_circuit_breaker():
            raise RedisConnectionError("Circuit breaker is OPEN")
        
        if not self.client:
            raise RedisConnectionError("Redis client not connected")
        
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                self.total_requests += 1
                result = await operation(*args, **kwargs)
                self._record_success()
                return result
                
            except (RedisConnectionError, RedisTimeoutError) as e:
                last_exception = e
                self._record_failure()
                
                if attempt < max_retries:
                    wait_time = backoff_factor ** attempt
                    api_logger.warning(
                        f"Redis operation failed (attempt {attempt + 1}/{max_retries + 1}), "
                        f"retrying in {wait_time}s: {str(e)}"
                    )
                    await asyncio.sleep(wait_time)
                    
                    # Try to reconnect
                    try:
                        await self.connect()
                    except Exception:
                        pass
                else:
                    api_logger.error(f"Redis operation failed after {max_retries + 1} attempts")
            
            except RedisError as e:
                # Non-recoverable errors
                self._record_failure()
                raise
        
        raise last_exception or RedisError("Operation failed")
    
    # Standard Redis operations with retry
    async def get(self, key: str) -> Optional[str]:
        """Get value by key."""
        return await self._execute_with_retry(self.client.get, key)
    
    async def set(
        self,
        key: str,
        value: Union[str, int, float],
        ex: Optional[int] = None,
        px: Optional[int] = None,
        nx: bool = False,
        xx: bool = False,
    ) -> bool:
        """Set key-value pair with optional expiration."""
        return await self._execute_with_retry(
            self.client.set, key, value, ex=ex, px=px, nx=nx, xx=xx
        )
    
    async def delete(self, *keys: str) -> int:
        """Delete one or more keys."""
        return await self._execute_with_retry(self.client.delete, *keys)
    
    async def exists(self, *keys: str) -> int:
        """Check if keys exist."""
        return await self._execute_with_retry(self.client.exists, *keys)
    
    async def expire(self, key: str, time: int) -> bool:
        """Set expiration time for key."""
        return await self._execute_with_retry(self.client.expire, key, time)
    
    async def ttl(self, key: str) -> int:
        """Get time to live for key."""
        return await self._execute_with_retry(self.client.ttl, key)
    
    # JSON operations (if RedisJSON module available)
    async def json_set(
        self,
        key: str,
        path: str,
        value: Any,
        ex: Optional[int] = None,
    ) -> bool:
        """
        Set JSON value at path.
        
        Args:
            key: Redis key
            path: JSON path (use "$" for root)
            value: Value to set (will be JSON serialized)
            ex: Expiration time in seconds
            
        Returns:
            True if successful
        """
        try:
            # Try RedisJSON module
            json_value = json.dumps(value) if not isinstance(value, str) else value
            result = await self._execute_with_retry(
                self.client.json().set, key, path, json_value
            )
            if ex:
                await self.expire(key, ex)
            return result
        except AttributeError:
            # Fallback to regular set with JSON string
            json_value = json.dumps(value)
            return await self.set(key, json_value, ex=ex)
    
    async def json_get(self, key: str, path: str = "$") -> Optional[Any]:
        """
        Get JSON value at path.
        
        Args:
            key: Redis key
            path: JSON path (use "$" for root)
            
        Returns:
            Deserialized JSON value or None
        """
        try:
            # Try RedisJSON module
            result = await self._execute_with_retry(
                self.client.json().get, key, path
            )
            return result
        except AttributeError:
            # Fallback to regular get with JSON parsing
            value = await self.get(key)
            if value:
                return json.loads(value)
            return None
    
    # Hash operations
    async def hset(self, name: str, key: str, value: str) -> int:
        """Set field in hash."""
        return await self._execute_with_retry(self.client.hset, name, key, value)
    
    async def hget(self, name: str, key: str) -> Optional[str]:
        """Get field from hash."""
        return await self._execute_with_retry(self.client.hget, name, key)
    
    async def hgetall(self, name: str) -> Dict[str, str]:
        """Get all fields from hash."""
        return await self._execute_with_retry(self.client.hgetall, name)
    
    # List operations
    async def lpush(self, name: str, *values: str) -> int:
        """Push values to left of list."""
        return await self._execute_with_retry(self.client.lpush, name, *values)
    
    async def rpush(self, name: str, *values: str) -> int:
        """Push values to right of list."""
        return await self._execute_with_retry(self.client.rpush, name, *values)
    
    async def lrange(self, name: str, start: int, end: int) -> list:
        """Get range of list."""
        return await self._execute_with_retry(self.client.lrange, name, start, end)
    
    # Set operations
    async def sadd(self, name: str, *values: str) -> int:
        """Add members to set."""
        return await self._execute_with_retry(self.client.sadd, name, *values)
    
    async def smembers(self, name: str) -> set:
        """Get all members of set."""
        return await self._execute_with_retry(self.client.smembers, name)
    
    # Metrics
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get client metrics.
        
        Returns:
            Dictionary with metrics:
            - total_requests: Total requests made
            - successful_requests: Successful requests
            - failed_requests: Failed requests
            - success_rate: Success rate (0-1)
            - circuit_breaker_state: Current circuit breaker state
        """
        success_rate = (
            self.successful_requests / self.total_requests
            if self.total_requests > 0
            else 0.0
        )
        
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": round(success_rate, 4),
            "circuit_breaker_state": self.circuit_breaker_state.value,
            "failure_count": self.failure_count,
        }


# Global Redis client instance
_redis_client: Optional[RedisClient] = None


async def get_redis_client() -> RedisClient:
    """
    Get or create global Redis client instance.
    
    Returns:
        RedisClient instance
        
    Example:
        redis = await get_redis_client()
        await redis.set("key", "value")
    """
    global _redis_client
    
    if _redis_client is None:
        _redis_client = RedisClient()
        await _redis_client.connect()
    
    return _redis_client


async def get_redis_pool() -> Optional[ConnectionPool]:
    """
    Get Redis connection pool.
    
    Returns:
        ConnectionPool instance or None
    """
    client = await get_redis_client()
    return client.pool


async def check_redis_health() -> Dict[str, Any]:
    """
    Check Redis connection health.
    
    Returns:
        Dictionary with health status:
        - status: "healthy" or "unhealthy"
        - latency_ms: Response latency in milliseconds
        - circuit_breaker_state: Circuit breaker state
        - metrics: Client metrics
        
    Example:
        health = await check_redis_health()
        if health["status"] == "healthy":
            print(f"Redis latency: {health['latency_ms']}ms")
    """
    try:
        client = await get_redis_client()
        
        start_time = time.time()
        await client.ping()
        latency_ms = (time.time() - start_time) * 1000
        
        metrics = client.get_metrics()
        
        return {
            "status": "healthy",
            "latency_ms": round(latency_ms, 2),
            "circuit_breaker_state": client.circuit_breaker_state.value,
            "metrics": metrics,
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "circuit_breaker_state": (
                _redis_client.circuit_breaker_state.value
                if _redis_client
                else "UNKNOWN"
            ),
        }


async def close_redis_client() -> None:
    """Close global Redis client connection."""
    global _redis_client
    
    if _redis_client:
        await _redis_client.disconnect()
        _redis_client = None

