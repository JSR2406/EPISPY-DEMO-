"""
Pydantic schemas for mental health data ingestion and responses.
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class MentalHealthIndicatorEnum(str, Enum):
    """Mental health indicator types."""
    ANXIETY = "ANXIETY"
    DEPRESSION = "DEPRESSION"
    STRESS = "STRESS"
    CRISIS = "CRISIS"
    SUBSTANCE_ABUSE = "SUBSTANCE_ABUSE"
    SUICIDAL_IDEATION = "SUICIDAL_IDEATION"
    PTSD = "PTSD"
    EATING_DISORDER = "EATING_DISORDER"
    OTHER = "OTHER"


class MentalHealthSeverityEnum(str, Enum):
    """Mental health severity levels."""
    MILD = "MILD"
    MODERATE = "MODERATE"
    SEVERE = "SEVERE"
    CRITICAL = "CRITICAL"


# ============================================================================
# Counseling Session Schemas
# ============================================================================

class CounselingSessionRequest(BaseModel):
    """Request schema for counseling session data."""
    location_id: str = Field(..., description="Location ID (UUID)")
    session_date: datetime = Field(..., description="Session date")
    age_group: Optional[str] = Field(None, description="Age group (e.g., '18-25')")
    gender_group: Optional[str] = Field(None, description="Gender group (M/F/OTHER/UNKNOWN)")
    primary_indicator: MentalHealthIndicatorEnum = Field(..., description="Primary mental health indicator")
    severity: MentalHealthSeverityEnum = Field(..., description="Severity level")
    session_duration_minutes: Optional[int] = Field(None, ge=0, description="Session duration in minutes")
    intervention_type: Optional[str] = Field(None, description="Type of intervention")
    outcome_score: Optional[float] = Field(None, ge=0, le=10, description="Outcome score (0-10)")
    is_crisis_session: bool = Field(False, description="Whether this was a crisis session")
    anonymized_notes_summary: Optional[str] = Field(None, description="Anonymized notes summary")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    @validator("age_group")
    def validate_age_group(cls, v):
        """Validate age group format."""
        if v and not v.replace("-", "").replace("+", "").isdigit():
            raise ValueError("Age group must be in format like '18-25' or '65+'")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "location_id": "550e8400-e29b-41d4-a716-446655440000",
                "session_date": "2024-01-15T10:30:00Z",
                "age_group": "25-34",
                "gender_group": "F",
                "primary_indicator": "ANXIETY",
                "severity": "MODERATE",
                "session_duration_minutes": 60,
                "intervention_type": "Cognitive Behavioral Therapy",
                "outcome_score": 6.5,
                "is_crisis_session": False,
                "anonymized_notes_summary": "Client reported feeling anxious about work-related stress",
                "metadata": {}
            }
        }


class CounselingSessionResponse(BaseModel):
    """Response schema for counseling session."""
    id: str
    location_id: str
    session_date: datetime
    primary_indicator: str
    severity: str
    created_at: datetime


# ============================================================================
# Crisis Hotline Transcript Schemas
# ============================================================================

class CrisisHotlineTranscriptRequest(BaseModel):
    """Request schema for crisis hotline transcript."""
    location_id: str = Field(..., description="Location ID (UUID)")
    call_date: datetime = Field(..., description="Call date")
    call_duration_seconds: Optional[int] = Field(None, ge=0, description="Call duration in seconds")
    age_group: Optional[str] = Field(None, description="Age group")
    transcript: Optional[str] = Field(None, description="Transcript text (will be anonymized)")
    intervention_provided: Optional[str] = Field(None, description="Intervention provided")
    follow_up_required: bool = Field(False, description="Whether follow-up is required")
    
    class Config:
        json_schema_extra = {
            "example": {
                "location_id": "550e8400-e29b-41d4-a716-446655440000",
                "call_date": "2024-01-15T14:20:00Z",
                "call_duration_seconds": 1800,
                "age_group": "18-24",
                "transcript": "Caller reports feeling overwhelmed and hopeless...",
                "intervention_provided": "Crisis counseling and safety planning",
                "follow_up_required": True
            }
        }


class CrisisHotlineTranscriptResponse(BaseModel):
    """Response schema for crisis hotline transcript."""
    id: str
    location_id: str
    call_date: datetime
    crisis_score: float
    primary_indicators: List[str]
    created_at: datetime


# ============================================================================
# Social Media Sentiment Schemas
# ============================================================================

class SocialMediaSentimentRequest(BaseModel):
    """Request schema for social media sentiment data."""
    location_id: str = Field(..., description="Location ID (UUID)")
    date: datetime = Field(..., description="Date of data collection")
    platform: Optional[str] = Field(None, description="Social media platform")
    posts: Optional[List[Dict[str, Any]]] = Field(None, description="Post data (will be aggregated)")
    sentiment_score: Optional[float] = Field(None, ge=-1, le=1, description="Pre-calculated sentiment score")
    
    class Config:
        json_schema_extra = {
            "example": {
                "location_id": "550e8400-e29b-41d4-a716-446655440000",
                "date": "2024-01-15T00:00:00Z",
                "platform": "twitter",
                "posts": [
                    {"sentiment_score": -0.7, "keywords": ["anxiety", "stress"]},
                    {"sentiment_score": -0.5, "keywords": ["overwhelmed"]}
                ],
                "sentiment_score": -0.6
            }
        }


class SocialMediaSentimentResponse(BaseModel):
    """Response schema for social media sentiment."""
    id: str
    location_id: str
    date: datetime
    sentiment_score: float
    mental_health_keyword_frequency: float
    anxiety_mentions: int
    depression_mentions: int
    created_at: datetime


# ============================================================================
# School Absenteeism Schemas
# ============================================================================

class SchoolAbsenteeismRequest(BaseModel):
    """Request schema for school absenteeism data."""
    location_id: str = Field(..., description="Location ID (UUID)")
    date: datetime = Field(..., description="Date of attendance record")
    school_type: Optional[str] = Field(None, description="School type (ELEMENTARY/MIDDLE/HIGH)")
    total_enrollment: Optional[int] = Field(None, ge=0, description="Total enrollment")
    absent_count: int = Field(..., ge=0, description="Number of absences")
    mental_health_related_absences: Optional[int] = Field(None, ge=0, description="Mental health-related absences")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "location_id": "550e8400-e29b-41d4-a716-446655440000",
                "date": "2024-01-15T00:00:00Z",
                "school_type": "HIGH",
                "total_enrollment": 500,
                "absent_count": 75,
                "mental_health_related_absences": 15,
                "metadata": {}
            }
        }


class SchoolAbsenteeismResponse(BaseModel):
    """Response schema for school absenteeism."""
    id: str
    location_id: str
    date: datetime
    absence_rate: float
    chronic_absenteeism_rate: float
    created_at: datetime


# ============================================================================
# Hotspot Schemas
# ============================================================================

class MentalHealthHotspotResponse(BaseModel):
    """Response schema for mental health hotspot."""
    id: str
    location_id: str
    location_name: Optional[str]
    detected_date: datetime
    hotspot_score: float
    primary_indicators: List[str]
    severity: str
    affected_population_estimate: int
    trend: str
    is_active: bool
    created_at: datetime


class HotspotAlertResponse(BaseModel):
    """Response schema for hotspot alert."""
    alert_id: str
    hotspot_id: str
    location_id: str
    location_name: str
    severity: str
    message: str
    recommended_actions: List[str]
    created_at: datetime


# ============================================================================
# Resource Schemas
# ============================================================================

class MentalHealthResourceRequest(BaseModel):
    """Request schema for mental health resource."""
    location_id: str = Field(..., description="Location ID (UUID)")
    resource_type: str = Field(..., description="Resource type")
    name: Optional[str] = Field(None, description="Resource name")
    contact_info: Optional[Dict[str, Any]] = Field(None, description="Contact information")
    services_offered: Optional[List[str]] = Field(None, description="Services offered")
    capacity: Optional[int] = Field(None, ge=0, description="Capacity")
    availability_status: Optional[str] = Field(None, description="Availability status")
    
    class Config:
        json_schema_extra = {
            "example": {
                "location_id": "550e8400-e29b-41d4-a716-446655440000",
                "resource_type": "crisis_hotline",
                "name": "City Crisis Hotline",
                "contact_info": {"phone": "1-800-XXX-XXXX", "email": "crisis@example.com"},
                "services_offered": ["Crisis support", "Suicide prevention", "Mental health referrals"],
                "capacity": 100,
                "availability_status": "AVAILABLE"
            }
        }


class ResourceRecommendationResponse(BaseModel):
    """Response schema for resource recommendation."""
    resource_id: str
    resource_name: str
    resource_type: str
    relevance_score: float
    distance_km: Optional[float]
    availability_status: str
    services_match: List[str]
    recommended_actions: List[str]


class ActionPlanResponse(BaseModel):
    """Response schema for action plan."""
    hotspot_id: str
    location_id: str
    hotspot_score: float
    severity: str
    immediate_actions: List[str]
    resource_recommendations: List[Dict[str, Any]]
    national_resources: List[Dict[str, Any]]
    monitoring_actions: List[str]
    prevention_actions: List[str]

