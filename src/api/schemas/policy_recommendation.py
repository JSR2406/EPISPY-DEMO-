"""Pydantic schemas for policy recommendation endpoints."""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class PolicyTypeEnum(str, Enum):
    """Policy type enumeration."""
    LOCKDOWN = "LOCKDOWN"
    TESTING_STRATEGY = "TESTING_STRATEGY"
    VACCINATION_CAMPAIGN = "VACCINATION_CAMPAIGN"
    CONTACT_TRACING = "CONTACT_TRACING"
    QUARANTINE = "QUARANTINE"
    TRAVEL_RESTRICTION = "TRAVEL_RESTRICTION"
    MASK_MANDATE = "MASK_MANDATE"
    SOCIAL_DISTANCING = "SOCIAL_DISTANCING"
    HEALTHCARE_CAPACITY = "HEALTHCARE_CAPACITY"
    PUBLIC_HEALTH_MESSAGING = "PUBLIC_HEALTH_MESSAGING"
    OTHER = "OTHER"


class EvidenceQualityEnum(str, Enum):
    """Evidence quality enumeration."""
    VERY_LOW = "VERY_LOW"
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


class PolicyRecommendationRequest(BaseModel):
    """Request for policy recommendations."""
    target_location_id: str = Field(..., description="UUID of target location")
    policy_types: Optional[List[PolicyTypeEnum]] = Field(
        None,
        description="Filter by specific policy types"
    )
    min_effectiveness: float = Field(
        0.0,
        ge=0.0,
        le=10.0,
        description="Minimum effectiveness score (0-10)"
    )
    min_evidence_quality: EvidenceQualityEnum = Field(
        EvidenceQualityEnum.MODERATE,
        description="Minimum evidence quality"
    )
    max_recommendations: int = Field(
        10,
        ge=1,
        le=50,
        description="Maximum number of recommendations"
    )
    include_ended_policies: bool = Field(
        True,
        description="Include policies that have ended"
    )
    time_window_days: Optional[int] = Field(
        None,
        ge=1,
        description="Only consider policies within this many days"
    )


class SituationBasedRequest(BaseModel):
    """Request for situation-based policy recommendations."""
    target_location_id: str = Field(..., description="UUID of target location")
    current_cases: int = Field(..., ge=0, description="Current number of cases")
    case_growth_rate: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Case growth rate (e.g., 0.15 for 15% daily growth)"
    )
    healthcare_utilization: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Healthcare system utilization (0-1)"
    )
    policy_types: Optional[List[PolicyTypeEnum]] = Field(
        None,
        description="Filter by specific policy types"
    )


class PolicyOutcomeResponse(BaseModel):
    """Policy outcome information."""
    effectiveness_score: float = Field(..., description="Effectiveness score (0-10)")
    case_reduction_percent: Optional[float] = Field(None, description="Case reduction %")
    death_reduction_percent: Optional[float] = Field(None, description="Death reduction %")
    r0_change: Optional[float] = Field(None, description="Change in R0")
    economic_impact_score: Optional[float] = Field(None, description="Economic impact (0-10)")
    social_impact_score: Optional[float] = Field(None, description="Social impact (0-10)")
    evidence_quality: EvidenceQualityEnum = Field(..., description="Evidence quality")
    measurement_period_start: datetime = Field(..., description="Measurement start")
    measurement_period_end: datetime = Field(..., description="Measurement end")


class LocationInfo(BaseModel):
    """Location information."""
    id: str = Field(..., description="Location UUID")
    name: str = Field(..., description="Location name")
    country: str = Field(..., description="Country")
    region: Optional[str] = Field(None, description="Region/state")


class PolicyInfo(BaseModel):
    """Policy information."""
    id: str = Field(..., description="Policy UUID")
    title: str = Field(..., description="Policy title")
    description: str = Field(..., description="Policy description")
    policy_type: PolicyTypeEnum = Field(..., description="Policy type")
    status: str = Field(..., description="Policy status")
    start_date: Optional[datetime] = Field(None, description="Start date")
    end_date: Optional[datetime] = Field(None, description="End date")
    source: Optional[str] = Field(None, description="Policy source")
    source_url: Optional[str] = Field(None, description="Source URL")
    implementation_details: Optional[Dict[str, Any]] = Field(
        None,
        description="Implementation details"
    )


class PolicyRecommendationResponse(BaseModel):
    """Policy recommendation response."""
    policy: PolicyInfo = Field(..., description="Recommended policy")
    similar_location: LocationInfo = Field(..., description="Similar location where policy worked")
    similarity_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Location similarity score (0-1)"
    )
    effectiveness_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Normalized effectiveness score (0-1)"
    )
    evidence_quality_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Evidence quality score (0-1)"
    )
    overall_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall recommendation score (0-1)"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Recommendation confidence (0-1)"
    )
    outcome: Optional[PolicyOutcomeResponse] = Field(
        None,
        description="Policy outcome data"
    )
    adaptation_notes: Optional[str] = Field(
        None,
        description="Notes for adapting policy to target location"
    )


class PolicyRecommendationsResponse(BaseModel):
    """Response containing multiple policy recommendations."""
    target_location_id: str = Field(..., description="Target location UUID")
    recommendations: List[PolicyRecommendationResponse] = Field(
        ...,
        description="List of policy recommendations"
    )
    total_found: int = Field(..., description="Total recommendations found")
    generated_at: datetime = Field(..., description="When recommendations were generated")


class PolicySummaryResponse(BaseModel):
    """Comprehensive policy summary."""
    policy: PolicyInfo = Field(..., description="Policy information")
    location: LocationInfo = Field(..., description="Location where policy was implemented")
    outcome: Optional[PolicyOutcomeResponse] = Field(
        None,
        description="Policy outcome"
    )
    implementations: List[Dict[str, Any]] = Field(
        ...,
        description="Implementation guides"
    )


class LocationContextRequest(BaseModel):
    """Request to create/update location context."""
    location_id: str = Field(..., description="Location UUID")
    population_density: Optional[float] = Field(None, ge=0, description="People per km²")
    gdp_per_capita: Optional[float] = Field(None, ge=0, description="GDP per capita in USD")
    healthcare_capacity: Optional[float] = Field(
        None,
        ge=0.0,
        le=10.0,
        description="Healthcare capacity score (0-10)"
    )
    urbanization_rate: Optional[float] = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Urbanization percentage"
    )
    literacy_rate: Optional[float] = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Literacy rate"
    )
    internet_penetration: Optional[float] = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Internet penetration %"
    )
    infrastructure_quality: Optional[float] = Field(
        None,
        ge=0.0,
        le=10.0,
        description="Infrastructure quality (0-10)"
    )
    governance_effectiveness: Optional[float] = Field(
        None,
        ge=0.0,
        le=10.0,
        description="Governance effectiveness (0-10)"
    )
    public_trust_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=10.0,
        description="Public trust score (0-10)"
    )
    climate_zone: Optional[str] = Field(None, description="Climate zone")
    geography_type: Optional[str] = Field(None, description="Geography type")
    cultural_factors: Optional[Dict[str, Any]] = Field(
        None,
        description="Cultural factors"
    )
    economic_structure: Optional[Dict[str, Any]] = Field(
        None,
        description="Economic structure"
    )
    context_json: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional context data"
    )

