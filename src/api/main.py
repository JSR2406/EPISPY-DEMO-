"""
Main entry point for the FastAPI application.
Initializes the application, loads configuration, and includes routers.
"""
from fastapi import FastAPI
from contextlib import asynccontextmanager
from datetime import datetime

# FIX 2: Using standard relative imports from the current module (src/api/)
from ..utils.config import settings
from ..utils.logger import api_logger
from ..utils.app_state import app_state, AppState 

# Import routers (within src/api/routes)
from .routes import health, prediction, alerts, data_ingestion

# --- Application Startup/Shutdown Handlers ---
# ... (rest of the code remains the same as before)
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and Shutdown event handler. Initializes external connections and 
    services required by the application.
    """
    api_logger.info("Application starting up...")
    
    # 1. Initialize App State
    app_state.startup_time = datetime.now()
    
    # 2. Initialize Database Connections (PLACEHOLDERS)
    api_logger.info(f"Connecting to database: {settings.database_url}")
    api_logger.info(f"Connecting to Redis: {settings.redis_url}")
    
    # 3. Initialize Models (PLACEHOLDERS)
    api_logger.info("Initializing prediction models...")
    
    # Yield control to the application to handle requests
    yield
    
    # --- Shutdown ---
    api_logger.info("Application shutting down...")

# --- FastAPI Initialization ---

app = FastAPI(
    title="EpiSPY Agentic AI System",
    description="Epidemic prediction and risk assessment using anonymous patient data and LLM reasoning.",
    version=getattr(settings, 'version', "0.1.0"), 
    lifespan=lifespan,
    debug=settings.debug
)

# --- Include Routers ---
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(prediction.router, prefix="/api/v1/prediction", tags=["Prediction"])
app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["Alerts"])
app.include_router(data_ingestion.router, prefix="/api/v1/data", tags=["Data Ingestion"])

# --- Helper function for state access (used for Dependency Injection) ---
def get_app_state() -> AppState:
    """
    Returns the global application state object.
    Used for Dependency Injection in route functions.
    """
    return app_state
