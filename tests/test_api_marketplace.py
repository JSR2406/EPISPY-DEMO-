"""
Integration tests for Marketplace API endpoints.
"""

import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient


@pytest.mark.asyncio
async def test_create_provider_endpoint(client: AsyncClient):
    """Test POST /api/v1/marketplace/providers."""
    response = await client.post(
        "/api/v1/marketplace/providers",
        json={
            "name": "Test Hospital",
            "provider_type": "HOSPITAL",
            "contact_info": {
                "email": "test@hospital.com",
                "phone": "+1234567890"
            }
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Hospital"
    assert data["provider_type"] == "HOSPITAL"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_inventory_endpoint(client: AsyncClient, provider_id: str):
    """Test POST /api/v1/marketplace/inventory."""
    response = await client.post(
        f"/api/v1/marketplace/inventory?provider_id={provider_id}",
        json={
            "resource_type": "VENTILATOR",
            "quantity_available": 10,
            "unit_price": 50000.00,
            "currency": "USD",
            "quality_grade": "A",
            "is_active": True
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["resource_type"] == "VENTILATOR"
    assert data["quantity_available"] == 10
    assert "id" in data


@pytest.mark.asyncio
async def test_create_request_endpoint(client: AsyncClient, requester_id: str):
    """Test POST /api/v1/marketplace/requests."""
    response = await client.post(
        f"/api/v1/marketplace/requests?requester_id={requester_id}",
        json={
            "resource_type": "VENTILATOR",
            "quantity_needed": 5,
            "urgency": "CRITICAL",
            "description": "Urgent need for ventilators"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["resource_type"] == "VENTILATOR"
    assert data["quantity_needed"] == 5
    assert data["urgency"] == "CRITICAL"
    assert "id" in data


@pytest.mark.asyncio
async def test_get_matches_endpoint(client: AsyncClient, request_id: str):
    """Test GET /api/v1/marketplace/requests/{id}/matches."""
    response = await client.get(
        f"/api/v1/marketplace/requests/{request_id}/matches"
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Matches may be empty if no compatible inventory
    if len(data) > 0:
        match = data[0]
        assert "id" in match
        assert "match_score" in match
        assert match["match_score"] > 0


@pytest.mark.asyncio
async def test_dashboard_overview(client: AsyncClient):
    """Test GET /api/v1/marketplace/dashboard/overview."""
    response = await client.get("/api/v1/marketplace/dashboard/overview")
    
    assert response.status_code == 200
    data = response.json()
    assert "total_providers" in data
    assert "total_inventory_items" in data
    assert "total_requests" in data
    assert "open_requests" in data
    assert isinstance(data["total_providers"], int)

