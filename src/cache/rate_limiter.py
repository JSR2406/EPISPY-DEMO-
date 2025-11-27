"""
Redis-based rate limiter with token bucket algorithm.

This module provides advanced rate limiting using Redis for distributed systems:
- Token bucket algorithm implementation
- Per-user and per-endpoint rate limiting
- FastAPI middleware integration
- Sliding window rate limiting
- Burst handling

Example usage:
    from src.cache.rate_limiter import RateLimiter, rate_limit_middleware
    
    # Create rate limiter
    limiter = RateLimiter()
    
    # Check rate limit
    allowed = await limiter.check_rate_limit(
        identifier="user:123",
        max_requests=100,
        window_seconds=60
    )
    
    # FastAPI middleware
    app.add_middleware(rate_limit_middleware)
"""
import time
from typing import Optional, Dict, Any, Tuple
from enum import Enum

from .redis_client import get_redis_client, RedisClient
from ..utils.logger import api_logger


class RateLimitStrategy(str, Enum):
    """Rate limiting strategies."""
    TOKEN_BUCKET = "token_bucket"  # Token bucket algorithm
    SLIDING_WINDOW = "sliding_window"  # Sliding window counter
    FIXED_WINDOW = "fixed_window"  # Fixed window counter


class RateLimiter:
    """
    Redis-based rate limiter with multiple strategies.
    
    Features:
    - Token bucket algorithm (default)
    - Sliding window rate limiting
    - Per-user and per-endpoint limits
    - Burst handling
    - Distributed rate limiting (works across multiple servers)
    
    Attributes:
        redis: Redis client instance
        default_strategy: Default rate limiting strategy
    """
    
    def __init__(self, default_strategy: RateLimitStrategy = RateLimitStrategy.TOKEN_BUCKET):
        """
        Initialize rate limiter.
        
        Args:
            default_strategy: Default rate limiting strategy
        """
        self.default_strategy = default_strategy
        self._redis: Optional[RedisClient] = None
    
    async def _get_redis(self) -> RedisClient:
        """Get Redis client (lazy initialization)."""
        if self._redis is None:
            self._redis = await get_redis_client()
        return self._redis
    
    def _make_key(self, identifier: str, endpoint: Optional[str] = None) -> str:
        """
        Generate rate limit key.
        
        Args:
            identifier: User/API key identifier
            endpoint: Optional endpoint path
            
        Returns:
            Redis key for rate limiting
        """
        if endpoint:
            return f"ratelimit:{identifier}:{endpoint}"
        return f"ratelimit:{identifier}"
    
    async def check_rate_limit(
        self,
        identifier: str,
        max_requests: int,
        window_seconds: int,
        endpoint: Optional[str] = None,
        strategy: Optional[RateLimitStrategy] = None,
        burst_size: Optional[int] = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if request is within rate limit.
        
        Args:
            identifier: User/API key identifier
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
            endpoint: Optional endpoint path for per-endpoint limiting
            strategy: Rate limiting strategy (defaults to instance default)
            burst_size: Maximum burst size (for token bucket)
            
        Returns:
            Tuple of (allowed: bool, info: dict)
            Info dict contains:
            - allowed: Whether request is allowed
            - remaining: Remaining requests
            - reset_time: When limit resets
            - retry_after: Seconds to wait before retry
            
        Example:
            allowed, info = await limiter.check_rate_limit(
                identifier="user:123",
                max_requests=100,
                window_seconds=60
            )
            if not allowed:
                print(f"Rate limit exceeded. Retry after {info['retry_after']}s")
        """
        strategy = strategy or self.default_strategy
        
        if strategy == RateLimitStrategy.TOKEN_BUCKET:
            return await self._token_bucket_check(
                identifier, max_requests, window_seconds, endpoint, burst_size
            )
        elif strategy == RateLimitStrategy.SLIDING_WINDOW:
            return await self._sliding_window_check(
                identifier, max_requests, window_seconds, endpoint
            )
        else:  # FIXED_WINDOW
            return await self._fixed_window_check(
                identifier, max_requests, window_seconds, endpoint
            )
    
    async def _token_bucket_check(
        self,
        identifier: str,
        max_requests: int,
        window_seconds: int,
        endpoint: Optional[str],
        burst_size: Optional[int],
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Token bucket rate limiting algorithm.
        
        Tokens are added at a constant rate. Each request consumes a token.
        Allows bursts up to bucket capacity.
        """
        redis = await self._get_redis()
        key = self._make_key(identifier, endpoint)
        
        # Calculate tokens per second
        tokens_per_second = max_requests / window_seconds
        bucket_capacity = burst_size or max_requests
        
        current_time = time.time()
        
        try:
            # Use Lua script for atomic operations
            lua_script = """
            local key = KEYS[1]
            local now = tonumber(ARGV[1])
            local tokens_per_second = tonumber(ARGV[2])
            local bucket_capacity = tonumber(ARGV[3])
            local tokens_to_consume = tonumber(ARGV[4])
            
            local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
            local tokens = tonumber(bucket[1]) or bucket_capacity
            local last_refill = tonumber(bucket[2]) or now
            
            -- Refill tokens based on time passed
            local time_passed = now - last_refill
            local tokens_to_add = time_passed * tokens_per_second
            tokens = math.min(bucket_capacity, tokens + tokens_to_add)
            
            -- Check if enough tokens available
            if tokens >= tokens_to_consume then
                tokens = tokens - tokens_to_consume
                redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
                redis.call('EXPIRE', key, 3600)  -- Expire after 1 hour
                return {1, tokens, now + (bucket_capacity - tokens) / tokens_per_second}
            else
                local retry_after = (tokens_to_consume - tokens) / tokens_per_second
                return {0, tokens, now + retry_after}
            end
            """
            
            result = await redis._execute_with_retry(
                redis.client.eval,
                lua_script,
                1,  # Number of keys
                key,
                current_time,
                tokens_per_second,
                bucket_capacity,
                1,  # Tokens to consume per request
            )
            
            allowed = bool(result[0])
            remaining = int(result[1])
            reset_time = float(result[2])
            
            return (
                allowed,
                {
                    "allowed": allowed,
                    "remaining": max(0, remaining),
                    "reset_time": reset_time,
                    "retry_after": max(0, int(reset_time - current_time)),
                    "strategy": "token_bucket",
                },
            )
            
        except Exception as e:
            api_logger.error(f"Token bucket rate limit check failed: {str(e)}")
            # Fail open - allow request if Redis fails
            return (
                True,
                {
                    "allowed": True,
                    "remaining": max_requests,
                    "reset_time": current_time + window_seconds,
                    "retry_after": 0,
                    "error": str(e),
                },
            )
    
    async def _sliding_window_check(
        self,
        identifier: str,
        max_requests: int,
        window_seconds: int,
        endpoint: Optional[str],
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Sliding window rate limiting.
        
        Uses sorted set to track requests in sliding window.
        More accurate than fixed window but uses more memory.
        """
        redis = await self._get_redis()
        key = self._make_key(identifier, endpoint)
        
        current_time = time.time()
        window_start = current_time - window_seconds
        
        try:
            # Use sorted set to track requests
            # Score is timestamp, value is unique request ID
            lua_script = """
            local key = KEYS[1]
            local window_start = tonumber(ARGV[1])
            local current_time = tonumber(ARGV[2])
            local max_requests = tonumber(ARGV[3])
            local request_id = ARGV[4]
            
            -- Remove old entries outside window
            redis.call('ZREMRANGEBYSCORE', key, 0, window_start)
            
            -- Count current requests in window
            local count = redis.call('ZCARD', key)
            
            if count < max_requests then
                -- Add current request
                redis.call('ZADD', key, current_time, request_id)
                redis.call('EXPIRE', key, 3600)
                return {1, max_requests - count - 1, current_time + 60}
            else
                -- Get oldest request time
                local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
                local retry_after = 0
                if oldest[2] then
                    retry_after = oldest[2] + 60 - current_time
                end
                return {0, 0, current_time + retry_after}
            end
            """
            
            request_id = f"{identifier}:{current_time}:{time.time_ns()}"
            result = await redis._execute_with_retry(
                redis.client.eval,
                lua_script,
                1,
                key,
                window_start,
                current_time,
                max_requests,
                request_id,
            )
            
            allowed = bool(result[0])
            remaining = int(result[1])
            reset_time = float(result[2])
            
            return (
                allowed,
                {
                    "allowed": allowed,
                    "remaining": max(0, remaining),
                    "reset_time": reset_time,
                    "retry_after": max(0, int(reset_time - current_time)),
                    "strategy": "sliding_window",
                },
            )
            
        except Exception as e:
            api_logger.error(f"Sliding window rate limit check failed: {str(e)}")
            return (
                True,
                {
                    "allowed": True,
                    "remaining": max_requests,
                    "reset_time": current_time + window_seconds,
                    "retry_after": 0,
                    "error": str(e),
                },
            )
    
    async def _fixed_window_check(
        self,
        identifier: str,
        max_requests: int,
        window_seconds: int,
        endpoint: Optional[str],
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Fixed window rate limiting.
        
        Simple counter that resets at fixed intervals.
        Less accurate but more memory efficient.
        """
        redis = await self._get_redis()
        key = self._make_key(identifier, endpoint)
        
        # Create window key based on current time window
        current_window = int(time.time() / window_seconds)
        window_key = f"{key}:{current_window}"
        
        try:
            # Increment counter
            current_count = await redis._execute_with_retry(
                redis.client.incr,
                window_key,
            )
            
            # Set expiration on first request in window
            if current_count == 1:
                await redis._execute_with_retry(
                    redis.client.expire,
                    window_key,
                    window_seconds + 1,  # Add 1 second buffer
                )
            
            allowed = current_count <= max_requests
            remaining = max(0, max_requests - current_count)
            reset_time = (current_window + 1) * window_seconds
            
            return (
                allowed,
                {
                    "allowed": allowed,
                    "remaining": remaining,
                    "reset_time": reset_time,
                    "retry_after": max(0, int(reset_time - time.time())),
                    "strategy": "fixed_window",
                },
            )
            
        except Exception as e:
            api_logger.error(f"Fixed window rate limit check failed: {str(e)}")
            return (
                True,
                {
                    "allowed": True,
                    "remaining": max_requests,
                    "reset_time": time.time() + window_seconds,
                    "retry_after": 0,
                    "error": str(e),
                },
            )
    
    async def get_rate_limit_info(
        self,
        identifier: str,
        endpoint: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get current rate limit information.
        
        Args:
            identifier: User/API key identifier
            endpoint: Optional endpoint path
            
        Returns:
            Rate limit information
        """
        redis = await self._get_redis()
        key = self._make_key(identifier, endpoint)
        
        try:
            # Try to get token bucket info
            bucket_info = await redis.hgetall(key)
            
            if bucket_info:
                tokens = float(bucket_info.get("tokens", 0))
                last_refill = float(bucket_info.get("last_refill", 0))
                
                return {
                    "tokens": tokens,
                    "last_refill": last_refill,
                    "time_since_refill": time.time() - last_refill,
                }
            
            return {}
            
        except Exception as e:
            api_logger.error(f"Failed to get rate limit info: {str(e)}")
            return {}
    
    async def reset_rate_limit(
        self,
        identifier: str,
        endpoint: Optional[str] = None,
    ) -> bool:
        """
        Reset rate limit for identifier.
        
        Args:
            identifier: User/API key identifier
            endpoint: Optional endpoint path
            
        Returns:
            True if reset successful
        """
        redis = await self._get_redis()
        key = self._make_key(identifier, endpoint)
        
        try:
            # Delete rate limit key
            await redis.delete(key)
            
            # Also delete window-based keys
            pattern = f"{key}:*"
            # Use SCAN to find and delete matching keys
            cursor = 0
            while True:
                cursor, keys = await redis._execute_with_retry(
                    redis.client.scan, cursor, match=pattern, count=100
                )
                if keys:
                    await redis.delete(*keys)
                if cursor == 0:
                    break
            
            api_logger.info(f"Rate limit reset for {identifier}")
            return True
            
        except Exception as e:
            api_logger.error(f"Failed to reset rate limit: {str(e)}")
            return False


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


async def get_rate_limiter() -> RateLimiter:
    """Get or create global rate limiter instance."""
    global _rate_limiter
    
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    
    return _rate_limiter


# FastAPI middleware integration
async def rate_limit_middleware(
    request,
    call_next,
    max_requests: int = 100,
    window_seconds: int = 60,
    per_endpoint: bool = False,
):
    """
    FastAPI middleware for rate limiting.
    
    Usage:
        from src.cache.rate_limiter import rate_limit_middleware
        
        app.add_middleware(
            BaseHTTPMiddleware,
            dispatch=rate_limit_middleware,
            max_requests=100,
            window_seconds=60
        )
    """
    from fastapi import Request, HTTPException
    from fastapi.responses import JSONResponse
    
    # Get identifier (user ID, API key, or IP)
    identifier = None
    
    # Try to get from authentication
    if hasattr(request.state, "user_id"):
        identifier = f"user:{request.state.user_id}"
    elif "X-API-Key" in request.headers:
        identifier = f"api_key:{request.headers['X-API-Key'][:8]}"
    else:
        # Fall back to IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            identifier = f"ip:{forwarded.split(',')[0].strip()}"
        else:
            identifier = f"ip:{request.client.host if request.client else 'unknown'}"
    
    # Get endpoint if per-endpoint limiting enabled
    endpoint = request.url.path if per_endpoint else None
    
    # Check rate limit
    limiter = await get_rate_limiter()
    allowed, info = await limiter.check_rate_limit(
        identifier=identifier,
        max_requests=max_requests,
        window_seconds=window_seconds,
        endpoint=endpoint,
    )
    
    if not allowed:
        response = JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded",
                "message": "Too many requests. Please try again later.",
                "retry_after": info["retry_after"],
                "reset_time": info["reset_time"],
            },
        )
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(int(info["reset_time"]))
        response.headers["Retry-After"] = str(info["retry_after"])
        return response
    
    # Process request
    response = await call_next(request)
    
    # Add rate limit headers
    response.headers["X-RateLimit-Limit"] = str(max_requests)
    response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
    response.headers["X-RateLimit-Reset"] = str(int(info["reset_time"]))
    
    return response

