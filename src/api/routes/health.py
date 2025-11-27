"""Health check endpoints."""
from fastapi import APIRouter, Depends
from typing import Dict, Any
import asyncio
from datetime import datetime

from ...utils.logger import api_logger
from src.utils.app_state import get_app_state, AppState

router = APIRouter()

@router.get("/")
@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Basic health check - responds immediately."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "epidemic-prediction-api",
        "version": "1.0.0"
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
    
    # Check SEIR model (quick check only)
    try:
        if app_state.seir_model:
            health_status["components"]["seir_model"] = {"status": "available"}
        else:
            health_status["components"]["seir_model"] = {"status": "unavailable"}
    except Exception as e:
        health_status["components"]["seir_model"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Check Ollama client (without testing)
    try:
        if app_state.ollama_client:
            health_status["components"]["ollama"] = {"status": "available"}
        else:
            health_status["components"]["ollama"] = {"status": "unavailable"}
    except Exception as e:
        health_status["components"]["ollama"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Check ChromaDB (without testing)
    try:
        if app_state.chroma_client:
            health_status["components"]["chroma_db"] = {"status": "available"}
        else:
            health_status["components"]["chroma_db"] = {"status": "unavailable"}
    except Exception as e:
        health_status["components"]["chroma_db"] = {
            "status": "error",
            "error": str(e)
        }
    
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
