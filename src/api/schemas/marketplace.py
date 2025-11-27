"""Pydantic schemas for marketplace endpoints."""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
from uuid import UUID


class ProviderTypeEnum(str, Enum):
    """Provider type enumeration."""
    HOSPITAL = "HOSPITAL"
    CLINIC = "CLINIC"
    SUPPLIER = "SUPPLIER"
    NGO = "NGO"
    GOVERNMENT = "GOVERNMENT"
    INDIVIDUAL = "INDIVIDUAL"


class ResourceTypeEnum(str, Enum):
    """Resource type enumeration."""
    VENTILATOR = "VENTILATOR"
    ICU_BED = "ICU_BED"
    HOSPITAL_BED = "HOSPITAL_BED"
    OXYGEN_CYLINDER = "OXYGEN_CYLINDER"
    OXYGEN_CONCENTRATOR = "OXYGEN_CONCENTRATOR"
    MONITOR = "MONITOR"
    DEFIBRILLATOR = "DEFIBRILLATOR"
    N95_MASK = "N95_MASK"
    SURGICAL_MASK = "SURGICAL_MASK"
    FACE_SHIELD = "FACE_SHIELD"
    GOWN = "GOWN"
    GLOVES = "GLOVES"
    SANITIZER = "SANITIZER"
    ANTIVIRAL = "ANTIVIRAL"
    ANTIBIOTIC = "ANTIBIOTIC"
    VACCINE = "VACCINE"
    IV_FLUID = "IV_FLUID"
    DOCTOR = "DOCTOR"
    NURSE = "NURSE"
    RESPIRATORY_THERAPIST = "RESPIRATORY_THERAPIST"
    PARAMEDIC = "PARAMEDIC"
    AMBULANCE = "AMBULANCE"
    TESTING_KIT = "TESTING_KIT"
    OTHER = "OTHER"


class UrgencyLevelEnum(str, Enum):
    """Urgency level enumeration."""
    ROUTINE = "ROUTINE"
    URGENT = "URGENT"
    CRITICAL = "CRITICAL"
    EMERGENCY = "EMERGENCY"


class QualityGradeEnum(str, Enum):
    """Quality grade enumeration."""
    A = "A"
    B = "B"
    C = "C"
    D = "D"


# Provider Schemas
class ProviderCreate(BaseModel):
    """Create provider request."""
    name: str = Field(..., description="Provider name")
    provider_type: ProviderTypeEnum = Field(..., description="Provider type")
    location_id: Optional[str] = Field(None, description="Location UUID")
    contact_info: Dict[str, Any] = Field(..., description="Contact information")


class ProviderResponse(BaseModel):
    """Provider response."""
    id: str
    name: str
    provider_type: str
    location_id: Optional[str]
    verified: bool
    rating: float
    total_transactions: int
    created_at: datetime


# Inventory Schemas
class InventoryCreate(BaseModel):
    """Create inventory item request."""
    resource_type: ResourceTypeEnum = Field(..., description="Resource type")
    quantity_available: int = Field(..., ge=0, description="Quantity available")
    unit_price: Optional[float] = Field(None, ge=0, description="Price per unit")
    currency: str = Field("USD", description="Currency code")
    quality_grade: Optional[QualityGradeEnum] = Field(None, description="Quality grade")
    expiry_date: Optional[datetime] = Field(None, description="Expiry date")
    certification_info: Optional[Dict[str, Any]] = Field(None, description="Certifications")
    description: Optional[str] = Field(None, description="Description")


class InventoryUpdate(BaseModel):
    """Update inventory item request."""
    quantity_available: Optional[int] = Field(None, ge=0)
    unit_price: Optional[float] = Field(None, ge=0)
    quality_grade: Optional[QualityGradeEnum] = None
    expiry_date: Optional[datetime] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None


class InventoryResponse(BaseModel):
    """Inventory item response."""
    id: str
    provider_id: str
    resource_type: str
    quantity_available: int
    quantity_reserved: int
    unit_price: Optional[float]
    currency: str
    quality_grade: Optional[str]
    expiry_date: Optional[datetime]
    is_active: bool
    created_at: datetime


# Request Schemas
class RequestCreate(BaseModel):
    """Create resource request."""
    resource_type: ResourceTypeEnum = Field(..., description="Resource type needed")
    quantity_needed: int = Field(..., ge=1, description="Quantity needed")
    urgency: UrgencyLevelEnum = Field(UrgencyLevelEnum.URGENT, description="Urgency level")
    location_id: Optional[str] = Field(None, description="Location UUID")
    deadline: Optional[datetime] = Field(None, description="Deadline for fulfillment")
    description: Optional[str] = Field(None, description="Description of need")


class RequestResponse(BaseModel):
    """Resource request response."""
    id: str
    requester_id: str
    resource_type: str
    quantity_needed: int
    quantity_fulfilled: int
    urgency: str
    location_id: Optional[str]
    deadline: Optional[datetime]
    status: str
    priority_score: Optional[float]
    created_at: datetime


# Match Schemas
class MatchResponse(BaseModel):
    """Resource match response."""
    id: str
    request_id: str
    inventory_id: str
    provider_id: str
    quantity_matched: int
    match_score: float
    status: str
    accepted_at: Optional[datetime]
    created_at: datetime
    provider_name: Optional[str] = None
    inventory_details: Optional[Dict[str, Any]] = None


# Transfer Schemas
class TransferResponse(BaseModel):
    """Resource transfer response."""
    id: str
    match_id: str
    from_location_id: Optional[str]
    to_location_id: Optional[str]
    quantity: int
    status: str
    estimated_arrival: Optional[datetime]
    actual_arrival: Optional[datetime]
    tracking_info: Optional[Dict[str, Any]]


# Volunteer Schemas
class VolunteerCreate(BaseModel):
    """Create volunteer registration."""
    name: str = Field(..., description="Volunteer name")
    email: str = Field(..., description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    specialization: Optional[str] = Field(None, description="Medical specialization")
    certifications: Optional[List[Dict[str, Any]]] = Field(None, description="Certifications")
    availability_dates: Optional[Dict[str, Any]] = Field(None, description="Availability")
    location_preferences: Optional[List[str]] = Field(None, description="Preferred locations")
    max_distance_km: int = Field(100, ge=0, description="Max travel distance")


class VolunteerResponse(BaseModel):
    """Volunteer response."""
    id: str
    name: str
    email: str
    specialization: Optional[str]
    verified: bool
    total_hours: int
    rating: float
    is_active: bool


class DeploymentCreate(BaseModel):
    """Create deployment request."""
    volunteer_id: str = Field(..., description="Volunteer UUID")
    facility_id: str = Field(..., description="Facility UUID")
    deployment_date: datetime = Field(..., description="Start date")
    return_date: Optional[datetime] = Field(None, description="End date")
    role: Optional[str] = Field(None, description="Role/position")


# Dashboard Schemas
class MarketplaceOverview(BaseModel):
    """Marketplace overview statistics."""
    total_providers: int
    total_inventory_items: int
    total_requests: int
    open_requests: int
    active_matches: int
    pending_transfers: int
    total_volunteers: int
    active_deployments: int


class SupplyDemandAnalytics(BaseModel):
    """Supply-demand analytics."""
    resource_type: str
    total_supply: int
    total_demand: int
    deficit: int
    match_rate: float
    avg_match_score: float

