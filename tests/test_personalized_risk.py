"""
Tests for Personalized Risk system.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.resource_models import (
    UserProfile, UserLocation, ExposureEvent, RiskHistory,
    NotificationPreferences
)
from src.database.models import Location, OutbreakEvent
from src.personalized.risk_calculator import PersonalizedRiskCalculator
from src.personalized.notification_service import NotificationManager, NotificationType


@pytest.mark.asyncio
async def test_create_user_profile(db_session: AsyncSession):
    """Test creating a user profile."""
    profile = UserProfile(
        user_id="test_user_123",
        age_group="31-50",
        comorbidities=["diabetes", "hypertension"],
        vaccination_status={"doses": 2, "last_dose_date": "2023-06-01"},
        occupation="HEALTHCARE",
        household_size=3,
        privacy_level="STANDARD",
    )
    
    db_session.add(profile)
    await db_session.commit()
    await db_session.refresh(profile)
    
    assert profile.id is not None
    assert profile.user_id == "test_user_123"
    assert profile.age_group == "31-50"
    assert len(profile.comorbidities) == 2


@pytest.mark.asyncio
async def test_risk_calculation(db_session: AsyncSession):
    """Test risk score calculation."""
    # Create location with outbreak
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
    
    # Create outbreak
    outbreak = OutbreakEvent(
        location_id=location.id,
        disease_type="COVID-19",
        cases=1000,
        deaths=10,
        recovered=800,
        active_cases=190,
        timestamp=datetime.now(),
        severity=7.5,
    )
    db_session.add(outbreak)
    await db_session.commit()
    
    # Create user profile
    profile = UserProfile(
        user_id="test_user",
        age_group="65+",
        comorbidities=["diabetes"],
        vaccination_status={"doses": 2},
        occupation="HEALTHCARE",
        household_size=2,
    )
    db_session.add(profile)
    await db_session.commit()
    
    # Create notification preferences
    prefs = NotificationPreferences(
        user_id="test_user",
        push_enabled=True,
        email_enabled=True,
    )
    db_session.add(prefs)
    await db_session.commit()
    
    # Calculate risk
    calculator = PersonalizedRiskCalculator(db_session)
    result = await calculator.calculate_risk_score(
        "test_user",
        (location.latitude, location.longitude)
    )
    
    assert result.total_score >= 0
    assert result.total_score <= 100
    assert result.risk_level in ["LOW", "MODERATE", "HIGH", "CRITICAL"]
    assert len(result.recommendations) > 0
    assert result.factors.location_risk > 0


@pytest.mark.asyncio
async def test_exposure_event(db_session: AsyncSession):
    """Test exposure event creation and processing."""
    # Create profile
    profile = UserProfile(
        user_id="test_user",
        age_group="31-50",
    )
    db_session.add(profile)
    await db_session.commit()
    
    # Create exposure event
    exposure = ExposureEvent(
        user_id="test_user",
        exposure_date=datetime.now() - timedelta(days=3),
        risk_level="MODERATE",
        exposure_type="PROXIMITY",
        notification_sent=False,
    )
    db_session.add(exposure)
    await db_session.commit()
    await db_session.refresh(exposure)
    
    assert exposure.id is not None
    assert exposure.risk_level == "MODERATE"
    assert exposure.notification_sent == False


@pytest.mark.asyncio
async def test_notification_preferences(db_session: AsyncSession):
    """Test notification preferences."""
    prefs = NotificationPreferences(
        user_id="test_user",
        push_enabled=True,
        sms_enabled=False,
        email_enabled=True,
        quiet_hours_start=22,
        quiet_hours_end=7,
        sensitivity_level="MODERATE",
        max_daily_notifications=3,
    )
    
    db_session.add(prefs)
    await db_session.commit()
    await db_session.refresh(prefs)
    
    assert prefs.push_enabled == True
    assert prefs.sms_enabled == False
    assert prefs.quiet_hours_start == 22
    assert prefs.max_daily_notifications == 3


@pytest.mark.asyncio
async def test_risk_history(db_session: AsyncSession):
    """Test risk history tracking."""
    # Create profile
    profile = UserProfile(
        user_id="test_user",
        age_group="31-50",
    )
    db_session.add(profile)
    await db_session.commit()
    
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
    
    # Create risk history
    risk_history = RiskHistory(
        user_id="test_user",
        date=datetime.now(),
        risk_score=65.5,
        risk_level="HIGH",
        location_id=location.id,
        contributing_factors={
            "location_risk": 70.0,
            "exposure_risk": 60.0,
        },
    )
    
    db_session.add(risk_history)
    await db_session.commit()
    await db_session.refresh(risk_history)
    
    assert risk_history.id is not None
    assert risk_history.risk_score == 65.5
    assert risk_history.risk_level == "HIGH"
    assert risk_history.location_id == location.id

