"""
Integration tests for Personalized Risk API endpoints.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_user_endpoint(client: AsyncClient):
    """Test POST /api/v1/personal/register."""
    response = await client.post(
        "/api/v1/personal/register",
        json={
            "user_id": "test_user_123",
            "age_group": "31-50",
            "comorbidities": ["diabetes"],
            "vaccination_status": {"doses": 2},
            "occupation": "HEALTHCARE",
            "household_size": 3,
            "privacy_level": "STANDARD"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "test_user_123"
    assert data["age_group"] == "31-50"
    assert "id" in data


@pytest.mark.asyncio
async def test_get_risk_score_endpoint(client: AsyncClient, user_id: str):
    """Test GET /api/v1/personal/risk-score."""
    response = await client.get(
        f"/api/v1/personal/risk-score?user_id={user_id}&latitude=19.0760&longitude=72.8777"
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "risk_score" in data
    assert "risk_level" in data
    assert "factors" in data
    assert "recommendations" in data
    assert 0 <= data["risk_score"] <= 100
    assert data["risk_level"] in ["LOW", "MODERATE", "HIGH", "CRITICAL"]


@pytest.mark.asyncio
async def test_check_location_endpoint(client: AsyncClient, user_id: str):
    """Test POST /api/v1/personal/check-location."""
    response = await client.post(
        f"/api/v1/personal/check-location?user_id={user_id}",
        json={
            "latitude": 19.0760,
            "longitude": 72.8777
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "location" in data
    assert "risk_score" in data
    assert "risk_level" in data
    assert "recommendations" in data


@pytest.mark.asyncio
async def test_report_symptoms_endpoint(client: AsyncClient, user_id: str):
    """Test POST /api/v1/personal/report-symptoms."""
    response = await client.post(
        f"/api/v1/personal/report-symptoms?user_id={user_id}&severity=7",
        json={
            "symptoms": ["fever", "cough", "fatigue"]
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "updated_risk_score" in data
    assert "risk_level" in data


@pytest.mark.asyncio
async def test_travel_assessment_endpoint(client: AsyncClient, user_id: str):
    """Test POST /api/v1/personal/travel/assess."""
    response = await client.post(
        f"/api/v1/personal/travel/assess?user_id={user_id}",
        json={
            "destination_latitude": 19.0760,
            "destination_longitude": 72.8777,
            "departure_date": "2024-02-01T00:00:00Z",
            "duration_days": 7
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "destination_risk_score" in data
    assert "destination_risk_level" in data
    assert "recommendations" in data
    assert "requirements" in data
    assert "travel_advice" in data

