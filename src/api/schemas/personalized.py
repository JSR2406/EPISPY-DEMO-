"""Pydantic schemas for personalized risk endpoints."""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime


class UserProfileCreate(BaseModel):
    """Create user profile request."""
    user_id: str = Field(..., description="External user identifier")
    age_group: Optional[str] = Field(None, description="Age group")
    comorbidities: Optional[List[str]] = Field(None, description="Comorbidities")
    vaccination_status: Optional[Dict[str, Any]] = Field(None, description="Vaccination info")
    occupation: Optional[str] = Field(None, description="Occupation")
    household_size: Optional[int] = Field(None, ge=1, description="Household size")
    risk_factors: Optional[Dict[str, Any]] = Field(None, description="Risk factors")
    privacy_level: str = Field("STANDARD", description="Privacy level")


class UserProfileUpdate(BaseModel):
    """Update user profile request."""
    age_group: Optional[str] = None
    comorbidities: Optional[List[str]] = None
    vaccination_status: Optional[Dict[str, Any]] = None
    occupation: Optional[str] = None
    household_size: Optional[int] = Field(None, ge=1)
    risk_factors: Optional[Dict[str, Any]] = None
    privacy_level: Optional[str] = None


class UserProfileResponse(BaseModel):
    """User profile response."""
    id: str
    user_id: str
    age_group: Optional[str]
    comorbidities: Optional[List[str]]
    vaccination_status: Optional[Dict[str, Any]]
    occupation: Optional[str]
    household_size: Optional[int]
    privacy_level: str
    created_at: datetime
    updated_at: datetime


class LocationCheckRequest(BaseModel):
    """Check location risk request."""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude")


class RiskScoreResponse(BaseModel):
    """Risk score response."""
    user_id: str
    risk_score: float = Field(..., ge=0, le=100, description="Risk score (0-100)")
    risk_level: str = Field(..., description="Risk level (LOW, MODERATE, HIGH, CRITICAL)")
    factors: Dict[str, float] = Field(..., description="Risk factor breakdown")
    contributing_factors: List[Dict[str, Any]] = Field(..., description="Ranked contributing factors")
    recommendations: List[str] = Field(..., description="Personalized recommendations")
    calculated_at: datetime


class ExposureEventResponse(BaseModel):
    """Exposure event response."""
    id: str
    exposure_date: datetime
    risk_level: str
    exposure_type: Optional[str]
    notification_sent: bool
    acknowledged: bool
    created_at: datetime


class NotificationPreferencesRequest(BaseModel):
    """Update notification preferences."""
    push_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    email_enabled: Optional[bool] = None
    quiet_hours_start: Optional[int] = Field(None, ge=0, le=23)
    quiet_hours_end: Optional[int] = Field(None, ge=0, le=23)
    sensitivity_level: Optional[str] = Field(None, description="LOW, MODERATE, HIGH")
    max_daily_notifications: Optional[int] = Field(None, ge=1, le=20)


class NotificationPreferencesResponse(BaseModel):
    """Notification preferences response."""
    user_id: str
    push_enabled: bool
    sms_enabled: bool
    email_enabled: bool
    quiet_hours_start: Optional[int]
    quiet_hours_end: Optional[int]
    sensitivity_level: str
    max_daily_notifications: int


class TravelRiskRequest(BaseModel):
    """Travel risk assessment request."""
    destination_latitude: float = Field(..., ge=-90, le=90)
    destination_longitude: float = Field(..., ge=-180, le=180)
    departure_date: datetime = Field(..., description="Planned departure date")
    duration_days: int = Field(..., ge=1, description="Trip duration in days")


class TravelRiskResponse(BaseModel):
    """Travel risk assessment response."""
    destination_risk_score: float = Field(..., ge=0, le=100)
    destination_risk_level: str
    route_risk: Optional[float] = None
    recommendations: List[str]
    requirements: Dict[str, Any] = Field(..., description="Testing, quarantine requirements")
    travel_advice: str

