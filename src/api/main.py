"""
Main entry point for the FastAPI application.
Initializes the application, loads configuration, and includes routers.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from datetime import datetime
import traceback

# FIX 2: Using standard relative imports from the current module (src/api/)
from ..utils.config import settings
from ..utils.logger import api_logger
from ..utils.app_state import app_state, AppState 

# Import routers (within src/api/routes)
from .routes import health, prediction, alerts, data_ingestion, policy_recommendation, marketplace, personalized

# Import middleware
from .middleware.rate_limiting import RateLimitMiddleware

# Import client wrappers
from ..integrations.ollama_client_wrapper import OllamaClient
from ..integrations.chroma_client import ChromaDBClient
from ..models.seir_model import SEIRModel

# Import database utilities
from ..data.storage.database import init_database, get_database_engine

# --- Application Startup/Shutdown Handlers ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and Shutdown event handler. Initializes external connections and 
    services required by the application.
    """
    api_logger.info("Application starting up...")
    
    try:
        # 1. Initialize App State
        app_state.startup_time = datetime.now()
        
        # 2. Initialize Database
        try:
            api_logger.info(f"Initializing database: {settings.database_url.split('@')[-1] if '@' in settings.database_url else settings.database_url}")
            init_database()
            api_logger.info("Database initialized successfully")
        except Exception as e:
            api_logger.error(f"Database initialization failed: {str(e)}")
            api_logger.warning("Continuing without database connection")
        
        # 3. Initialize Ollama Client
        try:
            api_logger.info(f"Initializing Ollama client: {settings.ollama_host}")
            ollama_client = OllamaClient()
            if ollama_client.initialize():
                app_state.ollama_client = ollama_client
                api_logger.info("Ollama client initialized successfully")
            else:
                api_logger.warning("Ollama client initialization failed - continuing without LLM support")
        except Exception as e:
            api_logger.error(f"Ollama client initialization error: {str(e)}")
            api_logger.warning("Continuing without Ollama client")
        
        # 4. Initialize ChromaDB Client
        try:
            api_logger.info("Initializing ChromaDB client...")
            chroma_client = ChromaDBClient()
            if chroma_client.initialize():
                app_state.chroma_client = chroma_client
                api_logger.info("ChromaDB client initialized successfully")
            else:
                api_logger.warning("ChromaDB client initialization failed - continuing without vector DB")
        except Exception as e:
            api_logger.error(f"ChromaDB client initialization error: {str(e)}")
            api_logger.warning("Continuing without ChromaDB client")
        
        # 5. Initialize SEIR Model
        try:
            api_logger.info("Initializing SEIR epidemic model...")
            seir_model = SEIRModel(population=100000, initial_infected=10)
            app_state.seir_model = seir_model
            api_logger.info("SEIR model initialized successfully")
        except Exception as e:
            api_logger.error(f"SEIR model initialization error: {str(e)}")
            api_logger.warning("Continuing without SEIR model")
        
        # 6. Initialize Redis Client
        try:
            api_logger.info(f"Initializing Redis client: {settings.redis_url}")
            from ..cache.redis_client import get_redis_client, check_redis_health
            
            redis_client = await get_redis_client()
            health = await check_redis_health()
            
            if health["status"] == "healthy":
                api_logger.info(f"Redis client initialized successfully (latency: {health.get('latency_ms', 0)}ms)")
            else:
                api_logger.warning("Redis client initialized but health check failed")
        except Exception as e:
            api_logger.error(f"Redis client initialization error: {str(e)}")
            api_logger.warning("Continuing without Redis (caching and rate limiting will be limited)")
        
        api_logger.info("Application startup completed successfully")
        
    except Exception as e:
        api_logger.critical(f"Critical error during startup: {str(e)}")
        api_logger.critical(traceback.format_exc())
    
    # Yield control to the application to handle requests
    yield
    
    # --- Shutdown ---
    api_logger.info("Application shutting down...")
    
    # Cleanup resources
    try:
        if app_state.ollama_client:
            api_logger.info("Cleaning up Ollama client...")
        if app_state.chroma_client:
            api_logger.info("Cleaning up ChromaDB client...")
        
        # Close Redis connection
        from ..cache.redis_client import close_redis_client
        await close_redis_client()
        api_logger.info("Redis connection closed")
    except Exception as e:
        api_logger.error(f"Error during shutdown: {str(e)}")
    
    api_logger.info("Application shutdown completed")

# --- FastAPI Initialization ---

app = FastAPI(
    title="EpiSPY Agentic AI System",
    description="Epidemic prediction and risk assessment using anonymous patient data and LLM reasoning.",
    version=getattr(settings, 'version', "1.0.0"), 
    lifespan=lifespan,
    debug=settings.debug
)

# --- Middleware ---

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else ["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate Limiting Middleware
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=60,
    requests_per_hour=1000,
    burst_size=10
)

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unhandled exceptions globally."""
    api_logger.error(f"Unhandled exception: {str(exc)}")
    api_logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please try again later.",
            "detail": str(exc) if settings.debug else None
        }
    )

# --- Include Routers ---
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(prediction.router, prefix="/api/v1/prediction", tags=["Prediction"])
app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["Alerts"])
app.include_router(data_ingestion.router, prefix="/api/v1/data", tags=["Data Ingestion"])

# Import and include cache routes
try:
    from .routes import cache
    app.include_router(cache.router, prefix="/api/v1/cache", tags=["Cache"])
except ImportError:
    api_logger.warning("Cache routes not available")

# Import and include mental health routes
try:
    from .routes import mental_health
    app.include_router(mental_health.router, prefix="/api/v1/mental-health", tags=["Mental Health"])
    api_logger.info("Mental health routes loaded successfully")
except ImportError as e:
    api_logger.warning(f"Mental health routes not available: {str(e)}")
except Exception as e:
    api_logger.error(f"Failed to load mental health routes: {str(e)}")

# Include policy recommendation routes
try:
    app.include_router(policy_recommendation.router, prefix="/api/v1", tags=["Policy Recommendations"])
    api_logger.info("Policy recommendation routes loaded successfully")
except ImportError as e:
    api_logger.warning(f"Policy recommendation routes not available: {str(e)}")
except Exception as e:
    api_logger.error(f"Failed to load policy recommendation routes: {str(e)}")

# Include marketplace routes
try:
    app.include_router(marketplace.router, prefix="/api/v1", tags=["Marketplace"])
    api_logger.info("Marketplace routes loaded successfully")
except ImportError as e:
    api_logger.warning(f"Marketplace routes not available: {str(e)}")
except Exception as e:
    api_logger.error(f"Failed to load marketplace routes: {str(e)}")

# Include personalized risk routes
try:
    app.include_router(personalized.router, prefix="/api/v1", tags=["Personalized Risk"])
    api_logger.info("Personalized risk routes loaded successfully")
except ImportError as e:
    api_logger.warning(f"Personalized risk routes not available: {str(e)}")
except Exception as e:
    api_logger.error(f"Failed to load personalized risk routes: {str(e)}")

# --- Root Endpoint ---
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "EpiSPY Agentic AI System",
        "version": getattr(settings, 'version', "1.0.0"),
        "status": "running",
        "docs": "/docs",
        "health": "/api/v1/health"
    }

# --- Helper function for state access (used for Dependency Injection) ---
def get_app_state() -> AppState:
    """
    Returns the global application state object.
    Used for Dependency Injection in route functions.
    """
    return app_state
