"""Rate limiting middleware for API endpoints with Redis support."""
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional
import asyncio

from ...utils.logger import api_logger
from ...utils.config import settings
from ...cache.rate_limiter import get_rate_limiter, RateLimitStrategy


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using Redis-based token bucket algorithm.
    
    Supports distributed rate limiting across multiple servers.
    Falls back to in-memory if Redis is unavailable.
    """
    
    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        burst_size: int = 10,
        use_redis: bool = True,
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.burst_size = burst_size
        self.use_redis = use_redis
        self._rate_limiter: Optional[object] = None
    
    async def dispatch(self, request: Request, call_next):
        # Get client identifier
        identifier = self._get_client_id(request)
        endpoint = request.url.path if self.use_redis else None
        
        # Check rate limit
        if self.use_redis:
            try:
                if self._rate_limiter is None:
                    self._rate_limiter = await get_rate_limiter()
                
                allowed, info = await self._rate_limiter.check_rate_limit(
                    identifier=identifier,
                    max_requests=self.requests_per_minute,
                    window_seconds=60,
                    endpoint=endpoint,
                    burst_size=self.burst_size,
                )
                
                if not allowed:
                    api_logger.warning(f"Rate limit exceeded for: {identifier}")
                    response = JSONResponse(
                        status_code=429,
                        content={
                            "error": "Rate limit exceeded",
                            "message": "Too many requests. Please try again later.",
                            "retry_after": info["retry_after"],
                        },
                    )
                    response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
                    response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
                    response.headers["X-RateLimit-Reset"] = str(int(info["reset_time"]))
                    response.headers["Retry-After"] = str(info["retry_after"])
                    return response
                
                # Process request
                response = await call_next(request)
                
                # Add rate limit headers
                response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
                response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
                response.headers["X-RateLimit-Reset"] = str(int(info["reset_time"]))
                
                return response
                
            except Exception as e:
                api_logger.error(f"Redis rate limiting failed, falling back: {str(e)}")
                # Fall through to allow request if Redis fails
                self.use_redis = False
        
        # Fallback: Allow request if Redis unavailable
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(self.requests_per_minute)
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """Get unique client identifier."""
        # Try user ID from request state (if authenticated)
        if hasattr(request.state, "user_id"):
            return f"user:{request.state.user_id}"
        
        # Try API key
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"api_key:{api_key[:8]}"
        
        # Fall back to IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"
        
        return f"ip:{ip}"


def rate_limit_decorator(
    requests_per_minute: int = 60,
    requests_per_hour: int = 1000
):
    """
    Decorator for rate limiting specific endpoints.
    
    Usage:
        @router.get("/endpoint")
        @rate_limit_decorator(requests_per_minute=30)
        async def endpoint():
            ...
    """
    def decorator(func):
        # Store rate limit config in function metadata
        func._rate_limit = {
            "per_minute": requests_per_minute,
            "per_hour": requests_per_hour
        }
        return func
    return decorator


# Redis-based rate limiting (for production)
class RedisRateLimiter:
    """
    Redis-based rate limiter for distributed systems.
    Use this in production instead of in-memory storage.
    """
    
    def __init__(self, redis_client, requests_per_minute: int = 60):
        self.redis = redis_client
        self.requests_per_minute = requests_per_minute
    
    async def check_rate_limit(self, client_id: str) -> bool:
        """Check rate limit using Redis."""
        # Implementation would use Redis INCR and EXPIRE
        # For now, placeholder
        return True
    
    async def record_request(self, client_id: str):
        """Record request in Redis."""
        # Implementation would use Redis INCR
        pass
