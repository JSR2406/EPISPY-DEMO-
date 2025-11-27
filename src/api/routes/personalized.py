"""Personalized risk API endpoints."""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from ...database.connection import get_db
from ...database.resource_models import (
    UserProfile, UserLocation, ExposureEvent, RiskHistory,
    NotificationPreferences
)
from ...personalized.risk_calculator import PersonalizedRiskCalculator
from ...personalized.notification_service import NotificationManager, NotificationType
from ..schemas.personalized import (
    UserProfileCreate, UserProfileUpdate, UserProfileResponse,
    LocationCheckRequest, RiskScoreResponse, ExposureEventResponse,
    NotificationPreferencesRequest, NotificationPreferencesResponse,
    TravelRiskRequest, TravelRiskResponse
)
from ...utils.logger import api_logger

router = APIRouter(prefix="/personal", tags=["Personalized Risk"])


@router.post("/register", response_model=UserProfileResponse)
async def register_user(
    profile_data: UserProfileCreate,
    db: AsyncSession = Depends(get_db)
) -> UserProfileResponse:
    """Register a new user profile."""
    try:
        # Check if profile already exists
        result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == profile_data.user_id)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            raise HTTPException(status_code=400, detail="Profile already exists")
        
        profile = UserProfile(
            user_id=profile_data.user_id,
            age_group=profile_data.age_group,
            comorbidities=profile_data.comorbidities,
            vaccination_status=profile_data.vaccination_status,
            occupation=profile_data.occupation,
            household_size=profile_data.household_size,
            risk_factors=profile_data.risk_factors,
            privacy_level=profile_data.privacy_level,
        )
        
        db.add(profile)
        
        # Create default notification preferences
        prefs = NotificationPreferences(
            user_id=profile_data.user_id,
            push_enabled=True,
            email_enabled=True,
            sms_enabled=False,
            quiet_hours_start=22,
            quiet_hours_end=7,
            sensitivity_level="MODERATE",
            max_daily_notifications=3,
        )
        db.add(prefs)
        
        await db.commit()
        await db.refresh(profile)
        
        return UserProfileResponse(
            id=str(profile.id),
            user_id=profile.user_id,
            age_group=profile.age_group,
            comorbidities=profile.comorbidities,
            vaccination_status=profile.vaccination_status,
            occupation=profile.occupation,
            household_size=profile.household_size,
            privacy_level=profile.privacy_level,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        api_logger.error(f"Error registering user: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/profile", response_model=UserProfileResponse)
async def update_profile(
    user_id: str,
    profile_data: UserProfileUpdate,
    db: AsyncSession = Depends(get_db)
) -> UserProfileResponse:
    """Update user profile."""
    try:
        result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Update fields
        if profile_data.age_group is not None:
            profile.age_group = profile_data.age_group
        if profile_data.comorbidities is not None:
            profile.comorbidities = profile_data.comorbidities
        if profile_data.vaccination_status is not None:
            profile.vaccination_status = profile_data.vaccination_status
        if profile_data.occupation is not None:
            profile.occupation = profile_data.occupation
        if profile_data.household_size is not None:
            profile.household_size = profile_data.household_size
        if profile_data.risk_factors is not None:
            profile.risk_factors = profile_data.risk_factors
        if profile_data.privacy_level is not None:
            profile.privacy_level = profile_data.privacy_level
        
        await db.commit()
        await db.refresh(profile)
        
        return UserProfileResponse(
            id=str(profile.id),
            user_id=profile.user_id,
            age_group=profile.age_group,
            comorbidities=profile.comorbidities,
            vaccination_status=profile.vaccination_status,
            occupation=profile.occupation,
            household_size=profile.household_size,
            privacy_level=profile.privacy_level,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        api_logger.error(f"Error updating profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/risk-score", response_model=RiskScoreResponse)
async def get_risk_score(
    user_id: str,
    latitude: Optional[float] = Query(None, ge=-90, le=90),
    longitude: Optional[float] = Query(None, ge=-180, le=180),
    db: AsyncSession = Depends(get_db)
) -> RiskScoreResponse:
    """Get current personalized risk score."""
    try:
        calculator = PersonalizedRiskCalculator(db)
        
        current_location = None
        if latitude is not None and longitude is not None:
            current_location = (latitude, longitude)
        
        result = await calculator.calculate_risk_score(user_id, current_location)
        
        return RiskScoreResponse(
            user_id=user_id,
            risk_score=result.total_score,
            risk_level=result.risk_level,
            factors={
                'location_risk': result.factors.location_risk,
                'travel_risk': result.factors.travel_risk,
                'exposure_risk': result.factors.exposure_risk,
                'vulnerability_risk': result.factors.vulnerability_risk,
                'behavior_risk': result.factors.behavior_risk,
                'occupation_risk': result.factors.occupation_risk,
                'household_risk': result.factors.household_risk,
            },
            contributing_factors=result.contributing_factors,
            recommendations=result.recommendations,
            calculated_at=datetime.now(),
        )
    except Exception as e:
        api_logger.error(f"Error calculating risk score: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check-location")
async def check_location_risk(
    user_id: str,
    location_data: LocationCheckRequest,
    db: AsyncSession = Depends(get_db)
):
    """Check risk for a specific location."""
    try:
        calculator = PersonalizedRiskCalculator(db)
        
        # Calculate risk with specific location
        result = await calculator.calculate_risk_score(
            user_id,
            (location_data.latitude, location_data.longitude)
        )
        
        return {
            "location": {
                "latitude": location_data.latitude,
                "longitude": location_data.longitude,
            },
            "risk_score": result.total_score,
            "risk_level": result.risk_level,
            "location_risk": result.factors.location_risk,
            "recommendations": result.recommendations,
        }
    except Exception as e:
        api_logger.error(f"Error checking location risk: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/advice", response_model=List[str])
async def get_personalized_advice(
    user_id: str,
    db: AsyncSession = Depends(get_db)
) -> List[str]:
    """Get personalized health advice."""
    try:
        calculator = PersonalizedRiskCalculator(db)
        result = await calculator.calculate_risk_score(user_id)
        return result.recommendations
    except Exception as e:
        api_logger.error(f"Error getting advice: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/report-symptoms")
async def report_symptoms(
    user_id: str,
    symptoms: List[str],
    severity: Optional[int] = Query(None, ge=1, le=10),
    db: AsyncSession = Depends(get_db)
):
    """Report symptoms (updates risk calculation)."""
    try:
        # Get profile
        result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Update risk factors with symptoms
        risk_factors = profile.risk_factors or {}
        risk_factors['reported_symptoms'] = symptoms
        if severity:
            risk_factors['symptom_severity'] = severity
        
        profile.risk_factors = risk_factors
        
        await db.commit()
        
        # Recalculate risk
        calculator = PersonalizedRiskCalculator(db)
        result = await calculator.calculate_risk_score(user_id)
        
        # Send notification if risk increased significantly
        if result.risk_level in ["HIGH", "CRITICAL"]:
            notification_manager = NotificationManager(db)
            await notification_manager.send_notification(
                user_id=user_id,
                notification_type=NotificationType.TESTING_RECOMMENDATION,
                title="Symptom Report - Testing Recommended",
                message="Based on your reported symptoms, we recommend getting tested immediately.",
                priority="HIGH",
            )
        
        return {
            "message": "Symptoms reported",
            "updated_risk_score": result.total_score,
            "risk_level": result.risk_level,
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        api_logger.error(f"Error reporting symptoms: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/exposure-history", response_model=List[ExposureEventResponse])
async def get_exposure_history(
    user_id: str,
    db: AsyncSession = Depends(get_db)
) -> List[ExposureEventResponse]:
    """Get exposure event history."""
    result = await db.execute(
        select(ExposureEvent)
        .where(ExposureEvent.user_id == user_id)
        .order_by(ExposureEvent.exposure_date.desc())
    )
    exposures = result.scalars().all()
    
    return [
        ExposureEventResponse(
            id=str(exp.id),
            exposure_date=exp.exposure_date,
            risk_level=exp.risk_level,
            exposure_type=exp.exposure_type,
            notification_sent=exp.notification_sent,
            acknowledged=exp.acknowledged,
            created_at=exp.created_at,
        )
        for exp in exposures
    ]


@router.put("/notification-preferences", response_model=NotificationPreferencesResponse)
async def update_notification_preferences(
    user_id: str,
    prefs_data: NotificationPreferencesRequest,
    db: AsyncSession = Depends(get_db)
) -> NotificationPreferencesResponse:
    """Update notification preferences."""
    try:
        result = await db.execute(
            select(NotificationPreferences).where(
                NotificationPreferences.user_id == user_id
            )
        )
        prefs = result.scalar_one_or_none()
        
        if not prefs:
            raise HTTPException(status_code=404, detail="Preferences not found")
        
        # Update fields
        if prefs_data.push_enabled is not None:
            prefs.push_enabled = prefs_data.push_enabled
        if prefs_data.sms_enabled is not None:
            prefs.sms_enabled = prefs_data.sms_enabled
        if prefs_data.email_enabled is not None:
            prefs.email_enabled = prefs_data.email_enabled
        if prefs_data.quiet_hours_start is not None:
            prefs.quiet_hours_start = prefs_data.quiet_hours_start
        if prefs_data.quiet_hours_end is not None:
            prefs.quiet_hours_end = prefs_data.quiet_hours_end
        if prefs_data.sensitivity_level is not None:
            prefs.sensitivity_level = prefs_data.sensitivity_level
        if prefs_data.max_daily_notifications is not None:
            prefs.max_daily_notifications = prefs_data.max_daily_notifications
        
        await db.commit()
        await db.refresh(prefs)
        
        return NotificationPreferencesResponse(
            user_id=prefs.user_id,
            push_enabled=prefs.push_enabled,
            sms_enabled=prefs.sms_enabled,
            email_enabled=prefs.email_enabled,
            quiet_hours_start=prefs.quiet_hours_start,
            quiet_hours_end=prefs.quiet_hours_end,
            sensitivity_level=prefs.sensitivity_level,
            max_daily_notifications=prefs.max_daily_notifications,
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        api_logger.error(f"Error updating preferences: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/travel/assess", response_model=TravelRiskResponse)
async def assess_travel_risk(
    user_id: str,
    travel_data: TravelRiskRequest,
    db: AsyncSession = Depends(get_db)
) -> TravelRiskResponse:
    """Assess risk for planned travel."""
    try:
        calculator = PersonalizedRiskCalculator(db)
        
        # Calculate risk at destination
        dest_result = await calculator.calculate_risk_score(
            user_id,
            (travel_data.destination_latitude, travel_data.destination_longitude)
        )
        
        # Generate travel-specific recommendations
        recommendations = [
            f"Destination risk level: {dest_result.risk_level}",
            "Check local health guidelines before travel",
            "Consider travel insurance",
        ]
        
        if dest_result.risk_level in ["HIGH", "CRITICAL"]:
            recommendations.append("Consider postponing non-essential travel")
            recommendations.append("If traveling, get tested before and after")
        
        requirements = {
            "testing_required": dest_result.risk_level in ["HIGH", "CRITICAL"],
            "quarantine_required": dest_result.risk_level == "CRITICAL",
            "vaccination_proof": True,
        }
        
        travel_advice = (
            f"Your destination has a {dest_result.risk_level.lower()} risk level. "
            f"Risk score: {dest_result.total_score:.1f}/100. "
            "Please follow all local health guidelines and consider the recommendations above."
        )
        
        return TravelRiskResponse(
            destination_risk_score=dest_result.total_score,
            destination_risk_level=dest_result.risk_level,
            route_risk=None,  # TODO: Calculate route risk
            recommendations=recommendations,
            requirements=requirements,
            travel_advice=travel_advice,
        )
    except Exception as e:
        api_logger.error(f"Error assessing travel risk: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

