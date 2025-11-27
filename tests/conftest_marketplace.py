"""
Pytest fixtures for marketplace and personalized risk tests.
"""

import pytest
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from src.database.models import Base
from src.database.resource_models import Base as ResourceBase
from src.database.connection import get_async_session


# Create test database engine
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    # Use in-memory SQLite for testing
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(ResourceBase.metadata.create_all)
    
    yield engine
    
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine):
    """Create a database session for testing."""
    async_session_maker = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(test_engine):
    """Create test client."""
    from fastapi.testclient import TestClient
    from src.api.main import app
    
    # Override database dependency
    async def override_get_db():
        async_session_maker = async_sessionmaker(
            test_engine, class_=AsyncSession, expire_on_commit=False
        )
        async with async_session_maker() as session:
            yield session
    
    app.dependency_overrides[get_async_session] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
async def sample_location(db_session):
    """Create a sample location for testing."""
    from src.database.models import Location
    
    location = Location(
        name="Test City",
        latitude=19.0760,
        longitude=72.8777,
        country="India",
        population=1000000,
    )
    db_session.add(location)
    await db_session.commit()
    await db_session.refresh(location)
    return location


@pytest.fixture
async def sample_provider(db_session, sample_location):
    """Create a sample provider for testing."""
    from src.database.resource_models import ResourceProvider, ProviderType
    
    provider = ResourceProvider(
        name="Test Hospital",
        provider_type=ProviderType.HOSPITAL,
        location_id=sample_location.id,
        verified=True,
        contact_info={"email": "test@hospital.com"},
    )
    db_session.add(provider)
    await db_session.commit()
    await db_session.refresh(provider)
    return provider


@pytest.fixture
async def provider_id(sample_provider):
    """Get provider ID as string."""
    return str(sample_provider.id)


@pytest.fixture
async def requester_id(db_session, sample_location):
    """Create a requester and return ID."""
    from src.database.resource_models import ResourceProvider, ProviderType
    
    requester = ResourceProvider(
        name="Needy Hospital",
        provider_type=ProviderType.HOSPITAL,
        location_id=sample_location.id,
        verified=True,
    )
    db_session.add(requester)
    await db_session.commit()
    await db_session.refresh(requester)
    return str(requester.id)


@pytest.fixture
async def request_id(db_session, requester_id, sample_location):
    """Create a request and return ID."""
    from src.database.resource_models import ResourceRequest, ResourceType, UrgencyLevel
    from uuid import UUID
    
    request = ResourceRequest(
        requester_id=UUID(requester_id),
        resource_type=ResourceType.VENTILATOR,
        quantity_needed=5,
        urgency=UrgencyLevel.CRITICAL,
        location_id=sample_location.id,
        status="OPEN",
    )
    db_session.add(request)
    await db_session.commit()
    await db_session.refresh(request)
    return str(request.id)


@pytest.fixture
async def user_id():
    """Get test user ID."""
    return "test_user_123"

