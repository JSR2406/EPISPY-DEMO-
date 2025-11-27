"""
Examples of using the Redis caching layer in EpiSPY.

This file demonstrates:
- Basic caching operations
- Cache decorators
- Rate limiting
- Session management
- Stream processing
"""
import asyncio
from datetime import datetime
from typing import Dict, Any

# Example 1: Basic Caching
async def example_basic_caching():
    """Example of basic cache operations."""
    from src.cache.cache_service import CacheService, CacheType
    
    cache_service = CacheService()
    
    # Store data in cache
    await cache_service.set(
        CacheType.OUTBREAK_DATA,
        "location:mumbai",
        {
            "cases": 1500,
            "deaths": 25,
            "recovered": 1200,
            "timestamp": datetime.now().isoformat()
        },
        ttl=300  # 5 minutes
    )
    
    # Retrieve from cache
    data = await cache_service.get(
        CacheType.OUTBREAK_DATA,
        "location:mumbai"
    )
    print(f"Cached data: {data}")
    
    # Check if key exists
    exists = await cache_service.exists(
        CacheType.OUTBREAK_DATA,
        "location:mumbai"
    )
    print(f"Key exists: {exists}")
    
    # Get TTL
    ttl = await cache_service.get_ttl(
        CacheType.OUTBREAK_DATA,
        "location:mumbai"
    )
    print(f"TTL: {ttl} seconds")
    
    # Invalidate cache
    await cache_service.delete(
        CacheType.OUTBREAK_DATA,
        "location:mumbai"
    )


# Example 2: Using Cache Decorator
async def example_cache_decorator():
    """Example of using cache decorator."""
    from src.cache.cache_service import cache_result, CacheType
    
    @cache_result(cache_type=CacheType.PREDICTION_RESULTS, ttl=3600)
    async def expensive_prediction(location_id: str, days_ahead: int):
        """Simulate expensive prediction operation."""
        print(f"Computing prediction for {location_id}...")
        await asyncio.sleep(1)  # Simulate computation
        return {
            "location_id": location_id,
            "predicted_cases": 2000,
            "confidence": 0.85,
            "days_ahead": days_ahead
        }
    
    # First call - cache miss (computes)
    result1 = await expensive_prediction("mumbai", 7)
    print(f"First call result: {result1}")
    
    # Second call - cache hit (returns cached)
    result2 = await expensive_prediction("mumbai", 7)
    print(f"Second call result: {result2}")


# Example 3: Rate Limiting
async def example_rate_limiting():
    """Example of rate limiting."""
    from src.cache.rate_limiter import get_rate_limiter, RateLimitStrategy
    
    limiter = await get_rate_limiter()
    
    identifier = "user:123"
    
    # Check rate limit
    for i in range(5):
        allowed, info = await limiter.check_rate_limit(
            identifier=identifier,
            max_requests=3,  # Only 3 requests allowed
            window_seconds=60,
            strategy=RateLimitStrategy.TOKEN_BUCKET,
            burst_size=5
        )
        
        print(f"Request {i+1}: Allowed={allowed}, Remaining={info['remaining']}")
        
        if not allowed:
            print(f"Rate limit exceeded! Retry after {info['retry_after']} seconds")
            break


# Example 4: Session Management
async def example_session_management():
    """Example of session management."""
    from src.cache.session_manager import get_session_manager
    
    session_manager = await get_session_manager()
    
    # Create session
    session_id = await session_manager.create_session(
        user_id="user123",
        data={
            "name": "John Doe",
            "role": "admin",
            "login_time": datetime.now().isoformat()
        },
        ttl=3600  # 1 hour
    )
    print(f"Created session: {session_id}")
    
    # Get session
    session = await session_manager.get_session(session_id)
    print(f"Session data: {session}")
    
    # Update session
    await session_manager.update_session(
        session_id,
        data={"last_activity": datetime.now().isoformat()}
    )
    
    # Store agent state
    await session_manager.store_agent_state(
        agent_id="epidemic_analyzer",
        conversation_id="conv123",
        state={
            "messages": [
                {"role": "user", "content": "What's the risk in Mumbai?"},
                {"role": "assistant", "content": "Risk level is HIGH"}
            ],
            "context": {"location": "Mumbai", "disease": "COVID-19"}
        }
    )
    
    # Get agent state
    agent_state = await session_manager.get_agent_state(
        "epidemic_analyzer",
        "conv123"
    )
    print(f"Agent state: {agent_state}")


# Example 5: Stream Processing
async def example_stream_processing():
    """Example of Redis Streams for real-time events."""
    from src.cache.stream_processor import (
        get_stream_processor,
        publish_outbreak_event,
        publish_risk_alert
    )
    
    processor = await get_stream_processor()
    
    # Publish outbreak event
    msg_id = await publish_outbreak_event(
        location_id="mumbai",
        event_data={
            "cases": 1500,
            "deaths": 25,
            "severity": 7.5
        }
    )
    print(f"Published outbreak event: {msg_id}")
    
    # Publish risk alert
    msg_id = await publish_risk_alert(
        location_id="mumbai",
        risk_level="HIGH",
        risk_score=7.5,
        alert_data={
            "message": "High risk detected",
            "recommendations": ["Increase testing", "Enhance monitoring"]
        }
    )
    print(f"Published risk alert: {msg_id}")
    
    # Consumer example (would run in background)
    async def process_outbreak_event(event_data: Dict[str, Any]):
        """Process outbreak event."""
        print(f"Processing outbreak event: {event_data}")
        # Send notifications, update dashboard, etc.
    
    # Start consuming events (in production, this would run in a worker)
    # async for message in processor.consume_outbreak_events(
    #     consumer_group="alert_processors",
    #     consumer_name="worker1",
    #     handler=process_outbreak_event
    # ):
    #     print(f"Processed: {message['id']}")


# Example 6: Cache Warming
async def example_cache_warming():
    """Example of cache warming."""
    from src.cache.cache_service import CacheService, CacheType
    
    cache_service = CacheService()
    
    # Define fetch function
    async def fetch_outbreak_data(location_id: str):
        """Simulate fetching data from database."""
        print(f"Fetching data for {location_id}...")
        await asyncio.sleep(0.5)
        return {
            "location_id": location_id,
            "cases": 1000,
            "deaths": 10,
            "timestamp": datetime.now().isoformat()
        }
    
    # Warm cache for multiple locations
    location_ids = ["mumbai", "delhi", "bangalore"]
    results = await cache_service.warm_outbreak_cache(
        location_ids,
        fetch_func=fetch_outbreak_data
    )
    
    print(f"Cache warming results: {results}")


# Example 7: Complete Workflow
async def example_complete_workflow():
    """Complete example combining caching, rate limiting, and streams."""
    from src.cache.cache_service import CacheService, CacheType, cache_result
    from src.cache.stream_processor import publish_outbreak_event
    from src.cache.rate_limiter import get_rate_limiter
    
    # Check rate limit
    limiter = await get_rate_limiter()
    allowed, info = await limiter.check_rate_limit(
        identifier="user:123",
        max_requests=100,
        window_seconds=60
    )
    
    if not allowed:
        print("Rate limit exceeded!")
        return
    
    # Get cached data or compute
    @cache_result(cache_type=CacheType.OUTBREAK_DATA, ttl=300)
    async def get_outbreak_data(location_id: str):
        # Simulate database query
        await asyncio.sleep(1)
        return {
            "location_id": location_id,
            "cases": 1500,
            "deaths": 25
        }
    
    data = await get_outbreak_data("mumbai")
    print(f"Outbreak data: {data}")
    
    # Publish event if threshold exceeded
    if data["cases"] > 1000:
        await publish_outbreak_event(
            location_id="mumbai",
            event_data=data
        )
        print("Published high-case event")


# Run examples
async def main():
    """Run all examples."""
    print("=" * 60)
    print("Redis Cache Usage Examples")
    print("=" * 60)
    
    print("\n1. Basic Caching:")
    await example_basic_caching()
    
    print("\n2. Cache Decorator:")
    await example_cache_decorator()
    
    print("\n3. Rate Limiting:")
    await example_rate_limiting()
    
    print("\n4. Session Management:")
    await example_session_management()
    
    print("\n5. Stream Processing:")
    await example_stream_processing()
    
    print("\n6. Cache Warming:")
    await example_cache_warming()
    
    print("\n7. Complete Workflow:")
    await example_complete_workflow()
    
    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

