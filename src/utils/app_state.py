import os
from typing import Optional
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
from ..utils.config import settings

# CRITICAL FIX: Use absolute import path from project root (src is in sys.path via run_api.py)
# This resolves the Uvicorn/FastAPI circular import issue.
from src.integrations.ollama_client import get_ollama_analysis as OllamaClient 


class AppState(BaseModel):
    """
    Defines the shared application state and dependencies that are initialized
    when the FastAPI application starts up.
    """
    ollama_client: Optional[OllamaClient] = None
    # Add other long-lived dependencies here (e.g., database connection, Redis client)
    
    # Example:
    # db_session: Optional[Any] = None
    # redis_client: Optional[Any] = None


# Initialize the shared state object
app_state = AppState()

def get_app_state() -> AppState:
    """
    Dependency injection function to retrieve the current application state.
    """
    return app_state
