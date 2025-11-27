"""Cache management and monitoring endpoints."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional, List
from pydantic import BaseModel

from ...utils.logger import api_logger
from ...cache.cache_service import CacheService, CacheType
from ...cache.redis_client import check_redis_health, get_redis_client
from ...cache.rate_limiter import get_rate_limiter
from ...cache.session_manager import get_session_manager

router = APIRouter()


@router.get("/health")
async def cache_health() -> Dict[str, Any]:
    """Get Redis cache health status."""
    try:
        health = await check_redis_health()
        return health
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache health check failed: {str(e)}")


@router.get("/stats")
async def cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    try:
        cache_service = CacheService()
        stats = cache_service.get_stats()
        
        redis = await get_redis_client()
        redis_metrics = redis.get_metrics()
        
        return {
            "cache": stats,
            "redis": redis_metrics,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")


@router.delete("/invalidate/{cache_type}")
async def invalidate_cache_endpoint(
    cache_type: str,
    pattern: Optional[str] = "*",
) -> Dict[str, Any]:
    """
    Invalidate cache by type and pattern.
    
    Args:
        cache_type: Cache type (outbreak_data, risk_assessment, etc.)
        pattern: Pattern to match (default: "*" for all)
    """
    try:
        cache_type_enum = CacheType(cache_type)
        cache_service = CacheService()
        
        count = await cache_service.invalidate_pattern(cache_type_enum, pattern)
        
        return {
            "status": "success",
            "cache_type": cache_type,
            "pattern": pattern,
            "keys_deleted": count,
        }
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid cache type: {cache_type}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache invalidation failed: {str(e)}")


@router.post("/warm/{cache_type}")
async def warm_cache_endpoint(
    cache_type: str,
    keys: List[str],
) -> Dict[str, Any]:
    """
    Warm cache for specified keys.
    
    Args:
        cache_type: Cache type
        keys: List of keys to warm
    """
    try:
        cache_type_enum = CacheType(cache_type)
        cache_service = CacheService()
        
        # This would need a fetch function - for now just return info
        return {
            "status": "info",
            "message": "Cache warming requires fetch function - implement in service",
            "cache_type": cache_type,
            "keys": keys,
        }
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid cache type: {cache_type}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache warming failed: {str(e)}")


@router.get("/rate-limit/{identifier}")
async def get_rate_limit_info(
    identifier: str,
    endpoint: Optional[str] = None,
) -> Dict[str, Any]:
    """Get rate limit information for identifier."""
    try:
        limiter = await get_rate_limiter()
        info = await limiter.get_rate_limit_info(identifier, endpoint)
        return info
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get rate limit info: {str(e)}")


@router.post("/rate-limit/{identifier}/reset")
async def reset_rate_limit(
    identifier: str,
    endpoint: Optional[str] = None,
) -> Dict[str, Any]:
    """Reset rate limit for identifier."""
    try:
        limiter = await get_rate_limiter()
        success = await limiter.reset_rate_limit(identifier, endpoint)
        return {
            "status": "success" if success else "failed",
            "identifier": identifier,
            "endpoint": endpoint,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset rate limit: {str(e)}")


@router.get("/session/{session_id}")
async def get_session(session_id: str) -> Dict[str, Any]:
    """Get session data."""
    try:
        session_manager = await get_session_manager()
        session = await session_manager.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return session
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session: {str(e)}")


@router.delete("/session/{session_id}")
async def delete_session(session_id: str) -> Dict[str, Any]:
    """Delete session."""
    try:
        session_manager = await get_session_manager()
        success = await session_manager.delete_session(session_id)
        
        return {
            "status": "success" if success else "failed",
            "session_id": session_id,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")

