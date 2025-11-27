# Redis Cache Integration Guide

This document describes the Redis caching and real-time processing layer integrated into EpiSPY.

## Overview

The Redis caching layer provides:
- **High-performance caching** for expensive operations
- **Distributed rate limiting** across multiple servers
- **Real-time event streaming** using Redis Streams
- **Session management** for users and agents
- **Circuit breaker pattern** for resilience

## Components

### 1. Redis Client (`src/cache/redis_client.py`)

Async Redis client with connection pooling and automatic reconnection.

**Features:**
- Connection pool management
- Circuit breaker (CLOSED/OPEN/HALF_OPEN states)
- Automatic reconnection with exponential backoff
- Health checks and metrics
- JSON support with fallback

**Usage:**
```python
from src.cache.redis_client import get_redis_client

redis = await get_redis_client()
await redis.set("key", "value", ex=60)
value = await redis.get("key")
```

### 2. Cache Service (`src/cache/cache_service.py`)

Generic caching service with decorators and TTL management.

**Cache Types:**
- `OUTBREAK_DATA`: 5 minutes TTL
- `RISK_ASSESSMENT`: 10 minutes TTL
- `PREDICTION_RESULTS`: 1 hour TTL
- `LOCATION_METADATA`: 24 hours TTL
- `AGENT_MEMORY`: 1 hour TTL
- `MODEL_INFERENCE`: 30 minutes TTL

**Usage:**
```python
from src.cache.cache_service import cache_result, CacheType

@cache_result(cache_type=CacheType.OUTBREAK_DATA, ttl=300)
async def get_outbreak_data(location_id: str):
    # Expensive operation
    return await fetch_from_database(location_id)
```

### 3. Stream Processor (`src/cache/stream_processor.py`)

Real-time event processing using Redis Streams.

**Streams:**
- `outbreak_events`: New outbreak data
- `risk_alerts`: Risk level changes
- `agent_completions`: Agent task completions
- `predictions`: Prediction updates

**Usage:**
```python
from src.cache.stream_processor import publish_outbreak_event

await publish_outbreak_event(
    location_id="mumbai",
    event_data={"cases": 1500, "deaths": 25}
)
```

### 4. Rate Limiter (`src/cache/rate_limiter.py`)

Distributed rate limiting with multiple strategies.

**Strategies:**
- **Token Bucket**: Allows bursts, smooth rate limiting
- **Sliding Window**: Accurate, uses more memory
- **Fixed Window**: Simple, memory efficient

**Usage:**
```python
from src.cache.rate_limiter import get_rate_limiter

limiter = await get_rate_limiter()
allowed, info = await limiter.check_rate_limit(
    identifier="user:123",
    max_requests=100,
    window_seconds=60
)
```

### 5. Session Manager (`src/cache/session_manager.py`)

Session storage for users and agent state.

**Features:**
- User session management
- Agent conversation state
- Temporary workflow data
- Automatic expiration

**Usage:**
```python
from src.cache.session_manager import get_session_manager

session_manager = await get_session_manager()
session_id = await session_manager.create_session(
    user_id="user123",
    data={"name": "John", "role": "admin"}
)
```

## FastAPI Integration

### Rate Limiting Middleware

The rate limiting middleware is automatically integrated in `src/api/main.py`:

```python
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=60,
    requests_per_hour=1000,
    burst_size=10
)
```

### Health Checks

Redis health is included in the detailed health check endpoint:

```bash
curl http://localhost:8000/api/v1/health/detailed
```

### Cache Management Endpoints

New endpoints for cache management:

- `GET /api/v1/cache/health` - Redis health status
- `GET /api/v1/cache/stats` - Cache statistics
- `DELETE /api/v1/cache/invalidate/{cache_type}` - Invalidate cache
- `POST /api/v1/cache/warm/{cache_type}` - Warm cache
- `GET /api/v1/cache/rate-limit/{identifier}` - Get rate limit info
- `POST /api/v1/cache/rate-limit/{identifier}/reset` - Reset rate limit
- `GET /api/v1/cache/session/{session_id}` - Get session
- `DELETE /api/v1/cache/session/{session_id}` - Delete session

## Configuration

### Environment Variables

Add to `.env`:

```bash
REDIS_URL=redis://localhost:6379/0
```

### Redis Connection

The Redis client automatically:
- Connects on first use (lazy initialization)
- Reconnects on failure with exponential backoff
- Opens circuit breaker after 5 consecutive failures
- Closes circuit breaker after 60 seconds

## Usage Examples

See `examples/redis_cache_usage.py` for complete examples:

1. **Basic Caching**: Store and retrieve cached data
2. **Cache Decorator**: Use decorator for automatic caching
3. **Rate Limiting**: Check and enforce rate limits
4. **Session Management**: Manage user sessions and agent state
5. **Stream Processing**: Publish and consume real-time events
6. **Cache Warming**: Pre-populate cache for frequently accessed data
7. **Complete Workflow**: Combine all features in a real scenario

## Monitoring

### Cache Statistics

Get cache hit/miss rates:

```python
from src.cache.cache_service import CacheService

cache_service = CacheService()
stats = cache_service.get_stats()
print(f"Hit rate: {stats['hit_rate']}")
```

### Redis Metrics

Get Redis client metrics:

```python
from src.cache.redis_client import get_redis_client

redis = await get_redis_client()
metrics = redis.get_metrics()
print(f"Success rate: {metrics['success_rate']}")
```

### Health Checks

Check Redis health:

```python
from src.cache.redis_client import check_redis_health

health = await check_redis_health()
if health["status"] == "healthy":
    print(f"Latency: {health['latency_ms']}ms")
```

## Best Practices

1. **Use appropriate TTLs**: Match TTL to data freshness requirements
2. **Invalidate on updates**: Clear cache when data changes
3. **Monitor hit rates**: Low hit rates indicate cache issues
4. **Use circuit breaker**: System degrades gracefully if Redis fails
5. **Warm frequently accessed data**: Pre-populate cache at startup
6. **Use appropriate rate limits**: Balance user experience and protection

## Troubleshooting

### Redis Connection Failed

- Check `REDIS_URL` in `.env`
- Verify Redis server is running
- Check network connectivity
- Review logs for connection errors

### Low Cache Hit Rate

- Check TTL values (may be too short)
- Verify cache keys are consistent
- Monitor cache invalidation frequency
- Review cache warming strategy

### Rate Limiting Issues

- Check rate limit configuration
- Verify identifier extraction (user ID, IP, API key)
- Review rate limit headers in responses
- Check Redis connection for distributed limiting

## Performance Considerations

- **Connection Pooling**: Reuses connections for better performance
- **Lazy Initialization**: Redis connects only when needed
- **Circuit Breaker**: Prevents cascading failures
- **JSON Caching**: Reduces serialization overhead
- **Batch Operations**: Use for multiple keys when possible

## Security

- **Session Data**: Sensitive data should be encrypted before caching
- **Rate Limiting**: Prevents abuse and DoS attacks
- **Key Namespacing**: Prevents key collisions
- **TTL Management**: Ensures data doesn't persist indefinitely

## Next Steps

1. **Add monitoring dashboards**: Grafana/Prometheus integration
2. **Implement cache warming**: Pre-populate on startup
3. **Add cache analytics**: Track cache performance over time
4. **Optimize TTLs**: Based on actual usage patterns
5. **Scale Redis**: Use Redis Cluster for high availability

