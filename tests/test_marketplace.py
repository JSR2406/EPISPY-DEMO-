"""
Tests for Resource Marketplace system.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.resource_models import (
    ResourceProvider, ResourceInventory, ResourceRequest, ResourceMatch,
    ProviderType, ResourceType, UrgencyLevel, MatchStatus
)
from src.database.models import Location
from src.marketplace.matching_engine import ResourceMatchingEngine
from src.database.connection import get_async_session


@pytest.mark.asyncio
async def test_create_provider(db_session: AsyncSession):
    """Test creating a resource provider."""
    provider = ResourceProvider(
        name="Test Hospital",
        provider_type=ProviderType.HOSPITAL,
        verified=False,
        contact_info={"email": "test@hospital.com", "phone": "+1234567890"},
    )
    
    db_session.add(provider)
    await db_session.commit()
    await db_session.refresh(provider)
    
    assert provider.id is not None
    assert provider.name == "Test Hospital"
    assert provider.provider_type == ProviderType.HOSPITAL
    assert provider.verified == False


@pytest.mark.asyncio
async def test_create_inventory(db_session: AsyncSession):
    """Test creating inventory item."""
    # Create provider first
    provider = ResourceProvider(
        name="Test Supplier",
        provider_type=ProviderType.SUPPLIER,
        verified=True,
    )
    db_session.add(provider)
    await db_session.commit()
    await db_session.refresh(provider)
    
    # Create inventory
    inventory = ResourceInventory(
        provider_id=provider.id,
        resource_type=ResourceType.VENTILATOR,
        quantity_available=10,
        unit_price=50000.00,
        currency="USD",
        is_active=True,
    )
    
    db_session.add(inventory)
    await db_session.commit()
    await db_session.refresh(inventory)
    
    assert inventory.id is not None
    assert inventory.quantity_available == 10
    assert inventory.resource_type == ResourceType.VENTILATOR


@pytest.mark.asyncio
async def test_create_request(db_session: AsyncSession):
    """Test creating a resource request."""
    # Create requester
    requester = ResourceProvider(
        name="Needy Hospital",
        provider_type=ProviderType.HOSPITAL,
        verified=True,
    )
    db_session.add(requester)
    await db_session.commit()
    await db_session.refresh(requester)
    
    # Create request
    request = ResourceRequest(
        requester_id=requester.id,
        resource_type=ResourceType.VENTILATOR,
        quantity_needed=5,
        urgency=UrgencyLevel.CRITICAL,
        status="OPEN",
    )
    
    db_session.add(request)
    await db_session.commit()
    await db_session.refresh(request)
    
    assert request.id is not None
    assert request.quantity_needed == 5
    assert request.urgency == UrgencyLevel.CRITICAL


@pytest.mark.asyncio
async def test_matching_engine(db_session: AsyncSession):
    """Test resource matching engine."""
    # Create location
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
    
    # Create provider with inventory
    provider = ResourceProvider(
        name="Supplier A",
        provider_type=ProviderType.SUPPLIER,
        location_id=location.id,
        verified=True,
    )
    db_session.add(provider)
    await db_session.commit()
    await db_session.refresh(provider)
    
    inventory = ResourceInventory(
        provider_id=provider.id,
        resource_type=ResourceType.VENTILATOR,
        quantity_available=10,
        is_active=True,
    )
    db_session.add(inventory)
    await db_session.commit()
    await db_session.refresh(inventory)
    
    # Create requester
    requester = ResourceProvider(
        name="Hospital B",
        provider_type=ProviderType.HOSPITAL,
        location_id=location.id,
        verified=True,
    )
    db_session.add(requester)
    await db_session.commit()
    await db_session.refresh(requester)
    
    # Create request
    request = ResourceRequest(
        requester_id=requester.id,
        resource_type=ResourceType.VENTILATOR,
        quantity_needed=5,
        urgency=UrgencyLevel.URGENT,
        location_id=location.id,
        status="OPEN",
    )
    db_session.add(request)
    await db_session.commit()
    await db_session.refresh(request)
    
    # Test matching
    engine = ResourceMatchingEngine(db_session)
    matches = await engine.match_requests_to_inventory(request_id=str(request.id))
    
    assert len(matches) > 0
    match = matches[0]
    assert match.request_id == request.id
    assert match.inventory_id == inventory.id
    assert match.match_score > 0
    assert match.status == MatchStatus.PENDING or match.status == MatchStatus.ACCEPTED


@pytest.mark.asyncio
async def test_match_score_calculation(db_session: AsyncSession):
    """Test match score calculation."""
    # Create location
    location = Location(
        name="Test City",
        latitude=19.0760,
        longitude=72.8777,
        country="India",
    )
    db_session.add(location)
    await db_session.commit()
    await db_session.refresh(location)
    
    # Create provider
    provider = ResourceProvider(
        name="Supplier",
        provider_type=ProviderType.SUPPLIER,
        location_id=location.id,
        verified=True,
        rating=4.5,
        total_transactions=10,
    )
    db_session.add(provider)
    await db_session.commit()
    await db_session.refresh(provider)
    
    # Create inventory
    inventory = ResourceInventory(
        provider_id=provider.id,
        resource_type=ResourceType.VENTILATOR,
        quantity_available=10,
        is_active=True,
    )
    db_session.add(inventory)
    await db_session.commit()
    await db_session.refresh(inventory)
    
    # Create request
    requester = ResourceProvider(
        name="Hospital",
        provider_type=ProviderType.HOSPITAL,
        location_id=location.id,
    )
    db_session.add(requester)
    await db_session.commit()
    await db_session.refresh(requester)
    
    request = ResourceRequest(
        requester_id=requester.id,
        resource_type=ResourceType.VENTILATOR,
        quantity_needed=5,
        urgency=UrgencyLevel.CRITICAL,
        location_id=location.id,
        status="OPEN",
    )
    db_session.add(request)
    await db_session.commit()
    await db_session.refresh(request)
    
    # Calculate score
    engine = ResourceMatchingEngine(db_session)
    score = await engine.calculate_match_score(request, inventory)
    
    assert score.total_score > 0
    assert score.total_score <= 100
    assert score.geographic_score > 0
    assert score.urgency_score > 0
    assert score.reliability_score > 0

