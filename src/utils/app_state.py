import os
from typing import Optional, Any
from pydantic import BaseModel
from ..utils.config import settings

# Import client wrappers
from ..integrations.ollama_client_wrapper import OllamaClient
from ..integrations.chroma_client import ChromaDBClient
from ..models.seir_model import SEIRModel


class AppState(BaseModel):
    """
    Defines the shared application state and dependencies that are initialized
    when the FastAPI application starts up.
    """
    ollama_client: Optional[OllamaClient] = None
    chroma_client: Optional[ChromaDBClient] = None
    seir_model: Optional[SEIRModel] = None
    startup_time: Optional[Any] = None
    
    class Config:
        arbitrary_types_allowed = True


# Initialize the shared state object
app_state = AppState()

def get_app_state() -> AppState:
    """
    Dependency injection function to retrieve the current application state.
    """
    return app_state
