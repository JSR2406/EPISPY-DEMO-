"""Health check endpoints."""
from fastapi import APIRouter, Depends
from typing import Dict, Any
import asyncio
from datetime import datetime

from ...utils.logger import api_logger
from src.utils.app_state import get_app_state, AppState

router = APIRouter()

@router.get("/")
async def health_check() -> Dict[str, Any]:
    """Basic health check."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "epidemic-prediction-api"
    }

@router.get("/detailed")
async def detailed_health_check(
    app_state: AppState = Depends(get_app_state)
) -> Dict[str, Any]:
    """Detailed health check including AI models."""
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "epidemic-prediction-api",
        "components": {}
    }
    
    # Check Ollama client
    try:
        if app_state.ollama_client:
            # Quick test
            test_result = await asyncio.wait_for(
                app_state.ollama_client._generate_async(
                    "llama3.2", "Say 'OK' if you're working"
                ),
                timeout=5.0
            )
            health_status["components"]["ollama"] = {
                "status": "healthy" if "OK" in test_result else "degraded",
                "response_time": "< 5s"
            }
        else:
            health_status["components"]["ollama"] = {"status": "unavailable"}
    except Exception as e:
        health_status["components"]["ollama"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check SEIR model
    try:
        if app_state.seir_model:
            # Quick simulation test
            test_sim = app_state.seir_model.simulate(days=1)
            health_status["components"]["seir_model"] = {
                "status": "healthy" if len(test_sim) > 0 else "degraded"
            }
        else:
            health_status["components"]["seir_model"] = {"status": "unavailable"}
    except Exception as e:
        health_status["components"]["seir_model"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check ChromaDB
    try:
        if app_state.chroma_client:
            # Test connection
            collections = app_state.chroma_client.list_collections()
            health_status["components"]["chroma_db"] = {
                "status": "healthy",
                "collections": len(collections)
            }
        else:
            health_status["components"]["chroma_db"] = {"status": "unavailable"}
    except Exception as e:
        health_status["components"]["chroma_db"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Determine overall status
    component_statuses = [
        comp.get("status", "unknown") 
        for comp in health_status["components"].values()
    ]
    
    if any(status == "unhealthy" for status in component_statuses):
        health_status["status"] = "unhealthy"
    elif any(status in ["degraded", "unavailable"] for status in component_statuses):
        health_status["status"] = "degraded"
    
    return health_status

@router.get("/metrics")
async def get_metrics() -> Dict[str, Any]:
    """Get basic system metrics."""
    import psutil
    import sys
    
    return {
        "system": {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent
        },
        "process": {
            "memory_mb": psutil.Process().memory_info().rss / 1024 / 1024,
            "cpu_percent": psutil.Process().cpu_percent(),
            "threads": psutil.Process().num_threads()
        },
        "python": {
            "version": sys.version,
            "implementation": sys.implementation.name
        }
    }
