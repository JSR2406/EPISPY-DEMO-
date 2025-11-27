"""
Pytest configuration and shared fixtures for EpiSPY test suite.

This module provides fixtures for:
- Database sessions (test and production)
- Redis client (test instance)
- FastAPI test client
- Mock external services (OpenAI, Ollama, etc.)
- Test data generators
- Environment configuration
"""
import pytest
import asyncio
import os
import sys
from typing import AsyncGenerator, Generator, Dict, Any
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import uuid
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import test dependencies
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine
)
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from httpx import AsyncClient
import redis.asyncio as aioredis
from fakeredis import aioredis as fake_aioredis

# Import application components
from src.database.models import Base
from src.database.resource_models import Base as ResourceBase
from src.database.connection import get_database_url, create_engine, get_async_session_factory
from src.api.main import app
from src.utils.config import settings
from src.utils.logger import api_logger


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "chaos: Chaos engineering tests")
    config.addinivalue_line("markers", "database: Database tests")
    config.addinivalue_line("markers", "api: API tests")
    config.addinivalue_line("markers", "agent: Agent tests")
    config.addinivalue_line("markers", "ml: ML model tests")


def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on directory."""
    for item in items:
        # Mark based on directory
        if "test_database" in str(item.fspath):
            item.add_marker(pytest.mark.database)
        elif "test_api" in str(item.fspath):
            item.add_marker(pytest.mark.api)
        elif "test_agents" in str(item.fspath):
            item.add_marker(pytest.mark.agent)
        elif "test_ml" in str(item.fspath):
            item.add_marker(pytest.mark.ml)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
            item.add_marker(pytest.mark.slow)
        elif "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
            item.add_marker(pytest.mark.slow)
        elif "chaos" in str(item.fspath):
            item.add_marker(pytest.mark.chaos)
            item.add_marker(pytest.mark.slow)


# ============================================================================
# Test Database Configuration
# ============================================================================

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "sqlite+aiosqlite:///:memory:"
)

# Global test database engine
_test_engine: AsyncEngine = None
_test_session_factory: async_sessionmaker = None


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_db_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create test database engine for the entire test session."""
    global _test_engine
    
    if _test_engine is None:
        # Use in-memory SQLite for tests
        test_url = TEST_DATABASE_URL
        
        if "sqlite" in test_url:
            _test_engine = create_async_engine(
                test_url,
                connect_args={"check_same_thread": False} if "aiosqlite" in test_url else {},
                poolclass=StaticPool,
                echo=False,
            )
        else:
            # PostgreSQL or other databases
            _test_engine = create_async_engine(
                test_url,
                pool_pre_ping=True,
                echo=False,
                pool_size=5,
                max_overflow=10,
            )
        
        # Create all tables (merge both bases)
        async with _test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            # Add resource models tables
            for table in ResourceBase.metadata.tables.values():
                if table.name not in Base.metadata.tables:
                    table.create(conn.sync_engine, checkfirst=True)
    
    yield _test_engine
    
    # Cleanup
    if _test_engine:
        await _test_engine.dispose()
        _test_engine = None


@pytest.fixture
async def db_session(test_db_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """
    Provide a database session for a test.
    
    Creates a new session for each test and ensures proper cleanup.
    All changes are rolled back after the test.
    """
    async_session_maker = async_sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )
    
    async with async_session_maker() as session:
        transaction = await session.begin()
        yield session
        await transaction.rollback()
        await session.close()


# ============================================================================
# Redis Test Client
# ============================================================================

@pytest.fixture
async def redis_client() -> AsyncGenerator[Any, None]:
    """
    Provide a test Redis client using fakeredis.
    
    Uses an in-memory Redis implementation for fast, isolated tests.
    """
    try:
        # Use fakeredis for in-memory Redis
        fake_redis = await fake_aioredis.FakeRedis()
        yield fake_redis
        await fake_redis.flushall()
        await fake_redis.close()
    except Exception:
        # Fallback to mock if fakeredis not available
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.set = AsyncMock(return_value=True)
        mock_redis.delete = AsyncMock(return_value=1)
        mock_redis.exists = AsyncMock(return_value=0)
        mock_redis.ping = AsyncMock(return_value=True)
        mock_redis.flushall = AsyncMock(return_value=True)
        yield mock_redis


# ============================================================================
# FastAPI Test Client
# ============================================================================

@pytest.fixture
def test_client() -> TestClient:
    """
    Provide a FastAPI test client.
    
    Uses TestClient for synchronous tests. For async tests, use async_client.
    """
    return TestClient(app)


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Provide an async FastAPI test client.
    
    Use this for async endpoint tests.
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


# ============================================================================
# Mock External Services
# ============================================================================

@pytest.fixture
def mock_openai():
    """
    Mock OpenAI API client.
    
    Provides mocked responses for OpenAI API calls.
    """
    with patch("src.integrations.openai_client") as mock:
        mock_instance = Mock()
        
        # Mock chat completion
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Mocked analysis response"
        mock_response.usage = Mock(total_tokens=100)
        
        mock_instance.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_instance.models.list = AsyncMock(return_value=Mock(data=[]))
        
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_ollama():
    """
    Mock Ollama API client.
    
    Provides mocked responses for Ollama API calls.
    """
    with patch("src.integrations.ollama_client_wrapper.OllamaClient") as mock:
        mock_instance = Mock()
        mock_instance.initialize = Mock(return_value=True)
        mock_instance.analyze_medical_data = AsyncMock(
            return_value={
                "risk_score": 7.5,
                "symptom_patterns": ["fever", "cough"],
                "geographic_clusters": ["Mumbai", "Delhi"],
                "recommended_actions": ["Monitor closely", "Increase testing"],
                "confidence": 0.85
            }
        )
        mock_instance.generate_response = AsyncMock(
            return_value="Mocked agentic analysis"
        )
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_chromadb():
    """
    Mock ChromaDB client.
    
    Provides mocked responses for ChromaDB operations.
    """
    with patch("src.integrations.chroma_client.ChromaDBClient") as mock:
        mock_instance = Mock()
        mock_instance.initialize = Mock(return_value=True)
        mock_instance.add_documents = AsyncMock(return_value=["doc_id_1"])
        mock_instance.query = AsyncMock(return_value={
            "ids": [["doc_id_1"]],
            "documents": [["Sample document"]],
            "distances": [[0.5]]
        })
        mock.return_value = mock_instance
        yield mock_instance


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def sample_locations() -> list[Dict[str, Any]]:
    """
    Provide sample location data for tests.
    
    Returns a list of location dictionaries.
    """
    return [
        {
            "id": uuid.uuid4(),
            "name": "Mumbai",
            "latitude": 19.0760,
            "longitude": 72.8777,
            "population": 12442373,
            "country": "India",
            "region": "Maharashtra"
        },
        {
            "id": uuid.uuid4(),
            "name": "Delhi",
            "latitude": 28.6139,
            "longitude": 77.2090,
            "population": 11007835,
            "country": "India",
            "region": "Delhi"
        },
        {
            "id": uuid.uuid4(),
            "name": "New York City",
            "latitude": 40.7128,
            "longitude": -74.0060,
            "population": 8175133,
            "country": "USA",
            "region": "New York"
        }
    ]


@pytest.fixture
def sample_outbreak_data() -> list[Dict[str, Any]]:
    """
    Provide sample outbreak event data for tests.
    
    Returns a list of outbreak event dictionaries.
    """
    location_id = uuid.uuid4()
    return [
        {
            "id": uuid.uuid4(),
            "location_id": location_id,
            "disease_type": "COVID-19",
            "cases": 1500,
            "deaths": 25,
            "recovered": 1200,
            "active_cases": 275,
            "timestamp": datetime.now() - timedelta(days=1),
            "severity": 7.5
        },
        {
            "id": uuid.uuid4(),
            "location_id": location_id,
            "disease_type": "Dengue",
            "cases": 500,
            "deaths": 10,
            "recovered": 450,
            "active_cases": 40,
            "timestamp": datetime.now() - timedelta(days=2),
            "severity": 6.0
        }
    ]


@pytest.fixture
async def sample_location_model(db_session: AsyncSession, sample_locations: list[Dict]) -> Location:
    """
    Create and return a Location model instance in the test database.
    """
    location_data = sample_locations[0].copy()
    location_id = location_data.pop("id")
    
    location = Location(id=location_id, **location_data)
    db_session.add(location)
    await db_session.commit()
    await db_session.refresh(location)
    
    return location


@pytest.fixture
async def sample_outbreak_event_model(
    db_session: AsyncSession,
    sample_location_model: Location,
    sample_outbreak_data: list[Dict]
) -> OutbreakEvent:
    """
    Create and return an OutbreakEvent model instance in the test database.
    """
    event_data = sample_outbreak_data[0].copy()
    event_id = event_data.pop("id")
    event_data["location_id"] = sample_location_model.id
    
    event = OutbreakEvent(id=event_id, **event_data)
    db_session.add(event)
    await db_session.commit()
    await db_session.refresh(event)
    
    return event


# ============================================================================
# Environment Configuration
# ============================================================================

@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """
    Setup test environment variables.
    
    Automatically applied to all tests to ensure clean environment.
    """
    # Override settings for tests
    monkeypatch.setenv("DATABASE_URL", TEST_DATABASE_URL)
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/15")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-testing-only")
    monkeypatch.setenv("JWT_SECRET", "test-jwt-secret-for-testing-only")
    monkeypatch.setenv("ENCRYPTION_KEY", "test-encryption-key-32-chars-long!")
    monkeypatch.setenv("DEBUG", "True")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    
    yield
    
    # Cleanup (if needed)
    pass


# ============================================================================
# Helper Functions
# ============================================================================

def create_test_token(user_id: str = "test_user", username: str = "test", roles: list = None) -> str:
    """
    Create a test JWT token.
    
    Args:
        user_id: User ID
        username: Username
        roles: List of roles
        
    Returns:
        JWT token string
    """
    from jose import jwt
    from datetime import datetime, timedelta
    
    if roles is None:
        roles = ["user"]
    
    payload = {
        "sub": user_id,
        "username": username,
        "roles": roles,
        "exp": datetime.now() + timedelta(hours=1),
        "iat": datetime.now()
    }
    
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def get_auth_headers(token: str = None) -> Dict[str, str]:
    """
    Get authentication headers for test requests.
    
    Args:
        token: JWT token (creates one if not provided)
        
    Returns:
        Dictionary with Authorization header
    """
    if token is None:
        token = create_test_token()
    
    return {"Authorization": f"Bearer {token}"}


def get_api_key_headers(api_key: str = None) -> Dict[str, str]:
    """
    Get API key headers for test requests.
    
    Args:
        api_key: API key (uses test key if not provided)
        
    Returns:
        Dictionary with X-API-Key header
    """
    if api_key is None:
        api_key = settings.secret_key
    
    return {"X-API-Key": api_key}

