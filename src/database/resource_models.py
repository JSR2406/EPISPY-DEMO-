"""
Resource Marketplace and Personalized Risk models for EpiSPY.

This module defines database models for:
1. Resource marketplace (providers, inventory, requests, matches, transfers)
2. Volunteer management
3. Personalized risk profiles and notifications
"""

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    DateTime,
    ForeignKey,
    Index,
    Text,
    Enum as SQLEnum,
    JSON,
    Boolean,
    Numeric,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, Dict, Any
import uuid
import enum

from .models import Base, Location


# ============================================================================
# RESOURCE MARKETPLACE MODELS
# ============================================================================

class ProviderType(str, enum.Enum):
    """Resource provider type."""
    HOSPITAL = "HOSPITAL"
    CLINIC = "CLINIC"
    SUPPLIER = "SUPPLIER"
    NGO = "NGO"
    GOVERNMENT = "GOVERNMENT"
    INDIVIDUAL = "INDIVIDUAL"


class ResourceType(str, enum.Enum):
    """Resource type enumeration."""
    # Medical Equipment
    VENTILATOR = "VENTILATOR"
    ICU_BED = "ICU_BED"
    HOSPITAL_BED = "HOSPITAL_BED"
    OXYGEN_CYLINDER = "OXYGEN_CYLINDER"
    OXYGEN_CONCENTRATOR = "OXYGEN_CONCENTRATOR"
    MONITOR = "MONITOR"
    DEFIBRILLATOR = "DEFIBRILLATOR"
    
    # PPE
    N95_MASK = "N95_MASK"
    SURGICAL_MASK = "SURGICAL_MASK"
    FACE_SHIELD = "FACE_SHIELD"
    GOWN = "GOWN"
    GLOVES = "GLOVES"
    SANITIZER = "SANITIZER"
    
    # Medicine
    ANTIVIRAL = "ANTIVIRAL"
    ANTIBIOTIC = "ANTIBIOTIC"
    VACCINE = "VACCINE"
    IV_FLUID = "IV_FLUID"
    
    # Staff
    DOCTOR = "DOCTOR"
    NURSE = "NURSE"
    RESPIRATORY_THERAPIST = "RESPIRATORY_THERAPIST"
    PARAMEDIC = "PARAMEDIC"
    
    # Other
    AMBULANCE = "AMBULANCE"
    TESTING_KIT = "TESTING_KIT"
    OTHER = "OTHER"


class UrgencyLevel(str, enum.Enum):
    """Request urgency level."""
    ROUTINE = "ROUTINE"
    URGENT = "URGENT"
    CRITICAL = "CRITICAL"
    EMERGENCY = "EMERGENCY"


class MatchStatus(str, enum.Enum):
    """Resource match status."""
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    FULFILLED = "FULFILLED"
    CANCELLED = "CANCELLED"


class TransferStatus(str, enum.Enum):
    """Resource transfer status."""
    SCHEDULED = "SCHEDULED"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class QualityGrade(str, enum.Enum):
    """Resource quality grade."""
    A = "A"  # Excellent
    B = "B"  # Good
    C = "C"  # Acceptable
    D = "D"  # Poor


class ResourceProvider(Base):
    """
    Resource provider model (hospitals, suppliers, NGOs, etc.).
    
    Stores information about organizations or individuals that can provide
    resources during epidemic emergencies.
    """
    __tablename__ = "resource_providers"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        doc="Unique identifier for the provider"
    )
    name = Column(
        String(255),
        nullable=False,
        index=True,
        doc="Provider name"
    )
    provider_type = Column(
        SQLEnum(ProviderType),
        nullable=False,
        index=True,
        doc="Type of provider"
    )
    location_id = Column(
        UUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Foreign key to locations table"
    )
    verified = Column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        doc="Whether provider is verified"
    )
    contact_info = Column(
        JSON,
        nullable=True,
        doc="Contact information (email, phone, address)"
    )
    rating = Column(
        Float,
        nullable=True,
        default=0.0,
        doc="Average rating (0-5)"
    )
    total_transactions = Column(
        Integer,
        nullable=False,
        default=0,
        doc="Total number of completed transactions"
    )
    metadata_json = Column(
        JSON,
        nullable=True,
        doc="Additional metadata"
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp when record was created"
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Timestamp when record was last updated"
    )
    
    # Relationships
    location = relationship("Location", lazy="selectin")
    inventory_items = relationship(
        "ResourceInventory",
        back_populates="provider",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    requests = relationship(
        "ResourceRequest",
        back_populates="requester",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_provider_type_location", "provider_type", "location_id"),
        Index("idx_provider_verified", "verified"),
    )


class ResourceInventory(Base):
    """
    Resource inventory model.
    
    Stores available resources that providers have listed.
    """
    __tablename__ = "resource_inventory"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        doc="Unique identifier for the inventory item"
    )
    provider_id = Column(
        UUID(as_uuid=True),
        ForeignKey("resource_providers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign key to resource_providers table"
    )
    resource_type = Column(
        SQLEnum(ResourceType),
        nullable=False,
        index=True,
        doc="Type of resource"
    )
    quantity_available = Column(
        Integer,
        nullable=False,
        default=0,
        doc="Quantity available"
    )
    quantity_reserved = Column(
        Integer,
        nullable=False,
        default=0,
        doc="Quantity reserved for pending matches"
    )
    unit_price = Column(
        Numeric(10, 2),
        nullable=True,
        doc="Price per unit (if applicable)"
    )
    currency = Column(
        String(3),
        nullable=True,
        default="USD",
        doc="Currency code (ISO 4217)"
    )
    quality_grade = Column(
        SQLEnum(QualityGrade),
        nullable=True,
        doc="Quality grade"
    )
    expiry_date = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="Expiry date (for perishable items)"
    )
    certification_info = Column(
        JSON,
        nullable=True,
        doc="Certification information (FDA, WHO, etc.)"
    )
    description = Column(
        Text,
        nullable=True,
        doc="Description of the resource"
    )
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        doc="Whether listing is active"
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp when record was created"
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Timestamp when record was last updated"
    )
    
    # Relationships
    provider = relationship("ResourceProvider", back_populates="inventory_items", lazy="selectin")
    
    # Indexes
    __table_args__ = (
        Index("idx_inventory_type_active", "resource_type", "is_active"),
        Index("idx_inventory_provider_type", "provider_id", "resource_type"),
    )


class ResourceRequest(Base):
    """
    Resource request model.
    
    Stores requests for resources from facilities in need.
    """
    __tablename__ = "resource_requests"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        doc="Unique identifier for the request"
    )
    requester_id = Column(
        UUID(as_uuid=True),
        ForeignKey("resource_providers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign key to resource_providers table (requester)"
    )
    resource_type = Column(
        SQLEnum(ResourceType),
        nullable=False,
        index=True,
        doc="Type of resource needed"
    )
    quantity_needed = Column(
        Integer,
        nullable=False,
        doc="Quantity needed"
    )
    quantity_fulfilled = Column(
        Integer,
        nullable=False,
        default=0,
        doc="Quantity already fulfilled"
    )
    urgency = Column(
        SQLEnum(UrgencyLevel),
        nullable=False,
        default=UrgencyLevel.URGENT,
        index=True,
        doc="Urgency level"
    )
    location_id = Column(
        UUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Foreign key to locations table"
    )
    deadline = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="Deadline for fulfillment"
    )
    status = Column(
        String(50),
        nullable=False,
        default="OPEN",
        index=True,
        doc="Request status (OPEN, PARTIAL, FULFILLED, CANCELLED)"
    )
    priority_score = Column(
        Float,
        nullable=True,
        doc="Calculated priority score (0-100)"
    )
    description = Column(
        Text,
        nullable=True,
        doc="Description of the need"
    )
    metadata_json = Column(
        JSON,
        nullable=True,
        doc="Additional metadata"
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        doc="Timestamp when record was created"
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Timestamp when record was last updated"
    )
    
    # Relationships
    requester = relationship("ResourceProvider", back_populates="requests", lazy="selectin")
    location = relationship("Location", lazy="selectin")
    matches = relationship(
        "ResourceMatch",
        back_populates="request",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_request_status_urgency", "status", "urgency"),
        Index("idx_request_type_status", "resource_type", "status"),
        Index("idx_request_deadline", "deadline"),
    )


class ResourceMatch(Base):
    """
    Resource match model.
    
    Stores matches between requests and available inventory.
    """
    __tablename__ = "resource_matches"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        doc="Unique identifier for the match"
    )
    request_id = Column(
        UUID(as_uuid=True),
        ForeignKey("resource_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign key to resource_requests table"
    )
    inventory_id = Column(
        UUID(as_uuid=True),
        ForeignKey("resource_inventory.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign key to resource_inventory table"
    )
    provider_id = Column(
        UUID(as_uuid=True),
        ForeignKey("resource_providers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Provider offering the resource"
    )
    quantity_matched = Column(
        Integer,
        nullable=False,
        doc="Quantity matched"
    )
    match_score = Column(
        Float,
        nullable=False,
        doc="Match quality score (0-100)"
    )
    status = Column(
        SQLEnum(MatchStatus),
        nullable=False,
        default=MatchStatus.PENDING,
        index=True,
        doc="Match status"
    )
    accepted_at = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="When match was accepted"
    )
    rejected_reason = Column(
        Text,
        nullable=True,
        doc="Reason for rejection if applicable"
    )
    metadata_json = Column(
        JSON,
        nullable=True,
        doc="Additional metadata"
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        doc="Timestamp when record was created"
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Timestamp when record was last updated"
    )
    
    # Relationships
    request = relationship("ResourceRequest", back_populates="matches", lazy="selectin")
    inventory = relationship("ResourceInventory", lazy="selectin")
    provider = relationship("ResourceProvider", lazy="selectin")
    transfer = relationship(
        "ResourceTransfer",
        back_populates="match",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_match_status", "status"),
        Index("idx_match_score", "match_score"),
    )


class ResourceTransfer(Base):
    """
    Resource transfer model.
    
    Tracks logistics of resource transfers from provider to requester.
    """
    __tablename__ = "resource_transfers"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        doc="Unique identifier for the transfer"
    )
    match_id = Column(
        UUID(as_uuid=True),
        ForeignKey("resource_matches.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
        doc="Foreign key to resource_matches table"
    )
    from_location_id = Column(
        UUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Source location"
    )
    to_location_id = Column(
        UUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Destination location"
    )
    quantity = Column(
        Integer,
        nullable=False,
        doc="Quantity being transferred"
    )
    status = Column(
        SQLEnum(TransferStatus),
        nullable=False,
        default=TransferStatus.SCHEDULED,
        index=True,
        doc="Transfer status"
    )
    tracking_info = Column(
        JSON,
        nullable=True,
        doc="Tracking information (carrier, tracking number, etc.)"
    )
    estimated_arrival = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="Estimated arrival time"
    )
    actual_arrival = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="Actual arrival time"
    )
    logistics_cost = Column(
        Numeric(10, 2),
        nullable=True,
        doc="Logistics cost"
    )
    metadata_json = Column(
        JSON,
        nullable=True,
        doc="Additional metadata"
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp when record was created"
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Timestamp when record was last updated"
    )
    
    # Relationships
    match = relationship("ResourceMatch", back_populates="transfer", lazy="selectin")
    from_location = relationship("Location", foreign_keys=[from_location_id], lazy="selectin")
    to_location = relationship("Location", foreign_keys=[to_location_id], lazy="selectin")
    
    # Indexes
    __table_args__ = (
        Index("idx_transfer_status", "status"),
        Index("idx_transfer_eta", "estimated_arrival"),
    )


# ============================================================================
# VOLUNTEER MANAGEMENT MODELS
# ============================================================================

class VolunteerStaff(Base):
    """
    Volunteer medical staff model.
    
    Stores information about volunteer healthcare workers.
    """
    __tablename__ = "volunteer_staff"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        doc="Unique identifier for the volunteer"
    )
    name = Column(
        String(255),
        nullable=False,
        doc="Volunteer name"
    )
    email = Column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        doc="Email address"
    )
    phone = Column(
        String(50),
        nullable=True,
        doc="Phone number"
    )
    specialization = Column(
        String(100),
        nullable=True,
        index=True,
        doc="Medical specialization"
    )
    certifications = Column(
        JSON,
        nullable=True,
        doc="List of certifications and licenses"
    )
    availability_dates = Column(
        JSON,
        nullable=True,
        doc="Available dates (start, end, days of week)"
    )
    location_preferences = Column(
        JSON,
        nullable=True,
        doc="Preferred deployment locations"
    )
    max_distance_km = Column(
        Integer,
        nullable=True,
        default=100,
        doc="Maximum distance willing to travel (km)"
    )
    verified = Column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        doc="Whether credentials are verified"
    )
    total_hours = Column(
        Integer,
        nullable=False,
        default=0,
        doc="Total volunteer hours"
    )
    rating = Column(
        Float,
        nullable=True,
        default=0.0,
        doc="Average rating"
    )
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        doc="Whether volunteer is currently active"
    )
    metadata_json = Column(
        JSON,
        nullable=True,
        doc="Additional metadata"
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp when record was created"
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Timestamp when record was last updated"
    )
    
    # Relationships
    deployments = relationship(
        "StaffDeployment",
        back_populates="volunteer",
        cascade="all, delete-orphan",
        lazy="selectin"
    )


class StaffDeployment(Base):
    """
    Staff deployment model.
    
    Tracks volunteer deployments to facilities.
    """
    __tablename__ = "staff_deployments"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        doc="Unique identifier for the deployment"
    )
    volunteer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("volunteer_staff.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign key to volunteer_staff table"
    )
    facility_id = Column(
        UUID(as_uuid=True),
        ForeignKey("resource_providers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Facility where volunteer is deployed"
    )
    deployment_date = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        doc="Deployment start date"
    )
    return_date = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="Expected return date"
    )
    role = Column(
        String(100),
        nullable=True,
        doc="Role/position"
    )
    status = Column(
        String(50),
        nullable=False,
        default="PENDING",
        index=True,
        doc="Deployment status (PENDING, ACTIVE, COMPLETED, CANCELLED)"
    )
    hours_worked = Column(
        Integer,
        nullable=True,
        doc="Total hours worked"
    )
    metadata_json = Column(
        JSON,
        nullable=True,
        doc="Additional metadata"
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp when record was created"
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Timestamp when record was last updated"
    )
    
    # Relationships
    volunteer = relationship("VolunteerStaff", back_populates="deployments", lazy="selectin")
    facility = relationship("ResourceProvider", lazy="selectin")
    
    # Indexes
    __table_args__ = (
        Index("idx_deployment_status", "status"),
        Index("idx_deployment_dates", "deployment_date", "return_date"),
    )


# ============================================================================
# PERSONALIZED RISK MODELS
# ============================================================================

class UserProfile(Base):
    """
    User profile model for personalized risk assessment.
    
    Stores user health information and preferences.
    """
    __tablename__ = "user_profiles"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        doc="Unique identifier for the profile"
    )
    user_id = Column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        doc="External user identifier (from auth system)"
    )
    age_group = Column(
        String(20),
        nullable=True,
        doc="Age group (e.g., '18-30', '65+')"
    )
    comorbidities = Column(
        JSON,
        nullable=True,
        doc="List of comorbidities"
    )
    vaccination_status = Column(
        JSON,
        nullable=True,
        doc="Vaccination information (doses, dates, type)"
    )
    occupation = Column(
        String(100),
        nullable=True,
        index=True,
        doc="Occupation type"
    )
    household_size = Column(
        Integer,
        nullable=True,
        doc="Number of household members"
    )
    risk_factors = Column(
        JSON,
        nullable=True,
        doc="Additional risk factors"
    )
    privacy_level = Column(
        String(20),
        nullable=False,
        default="STANDARD",
        doc="Privacy level (MINIMAL, STANDARD, FULL)"
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp when record was created"
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Timestamp when record was last updated"
    )
    
    # Relationships
    locations = relationship(
        "UserLocation",
        back_populates="profile",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    exposure_events = relationship(
        "ExposureEvent",
        back_populates="profile",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    risk_history = relationship(
        "RiskHistory",
        back_populates="profile",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    notification_preferences = relationship(
        "NotificationPreferences",
        back_populates="profile",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin"
    )


class UserLocation(Base):
    """
    User location history model.
    
    Stores location data for risk calculation (privacy-preserving).
    """
    __tablename__ = "user_locations"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        doc="Unique identifier for the location record"
    )
    user_id = Column(
        String(255),
        ForeignKey("user_profiles.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign key to user_profiles table"
    )
    latitude = Column(
        Float,
        nullable=False,
        doc="Latitude"
    )
    longitude = Column(
        Float,
        nullable=False,
        doc="Longitude"
    )
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        doc="When location was recorded"
    )
    risk_score = Column(
        Float,
        nullable=True,
        doc="Risk score at this location"
    )
    is_current = Column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        doc="Whether this is the current location"
    )
    location_hash = Column(
        String(64),
        nullable=True,
        index=True,
        doc="Hashed location for privacy (optional)"
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp when record was created"
    )
    
    # Relationships
    profile = relationship("UserProfile", back_populates="locations", lazy="selectin")
    
    # Indexes
    __table_args__ = (
        Index("idx_location_user_timestamp", "user_id", "timestamp"),
        Index("idx_location_coords", "latitude", "longitude"),
    )


class ExposureEvent(Base):
    """
    Exposure event model.
    
    Stores potential exposure events for contact tracing.
    """
    __tablename__ = "exposure_events"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        doc="Unique identifier for the exposure event"
    )
    user_id = Column(
        String(255),
        ForeignKey("user_profiles.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign key to user_profiles table"
    )
    exposure_date = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        doc="Date of potential exposure"
    )
    risk_level = Column(
        String(20),
        nullable=False,
        doc="Risk level (LOW, MODERATE, HIGH)"
    )
    exposure_type = Column(
        String(50),
        nullable=True,
        doc="Type of exposure (PROXIMITY, CONTACT, etc.)"
    )
    notification_sent = Column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        doc="Whether notification was sent"
    )
    acknowledged = Column(
        Boolean,
        nullable=False,
        default=False,
        doc="Whether user acknowledged the exposure"
    )
    metadata_json = Column(
        JSON,
        nullable=True,
        doc="Additional metadata"
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp when record was created"
    )
    
    # Relationships
    profile = relationship("UserProfile", back_populates="exposure_events", lazy="selectin")
    
    # Indexes
    __table_args__ = (
        Index("idx_exposure_user_date", "user_id", "exposure_date"),
        Index("idx_exposure_notification", "notification_sent"),
    )


class RiskHistory(Base):
    """
    Risk history model.
    
    Stores historical risk scores for users.
    """
    __tablename__ = "risk_history"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        doc="Unique identifier for the risk record"
    )
    user_id = Column(
        String(255),
        ForeignKey("user_profiles.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign key to user_profiles table"
    )
    date = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        doc="Date of risk assessment"
    )
    risk_score = Column(
        Float,
        nullable=False,
        doc="Risk score (0-100)"
    )
    risk_level = Column(
        String(20),
        nullable=False,
        index=True,
        doc="Risk level category"
    )
    location_id = Column(
        UUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Location at time of assessment"
    )
    contributing_factors = Column(
        JSON,
        nullable=True,
        doc="Factors contributing to risk score"
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp when record was created"
    )
    
    # Relationships
    profile = relationship("UserProfile", back_populates="risk_history", lazy="selectin")
    location = relationship("Location", lazy="selectin")
    
    # Indexes
    __table_args__ = (
        Index("idx_risk_user_date", "user_id", "date"),
        Index("idx_risk_level", "risk_level"),
    )


class NotificationPreferences(Base):
    """
    Notification preferences model.
    
    Stores user notification settings.
    """
    __tablename__ = "notification_preferences"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        doc="Unique identifier for the preferences"
    )
    user_id = Column(
        String(255),
        ForeignKey("user_profiles.user_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
        doc="Foreign key to user_profiles table"
    )
    push_enabled = Column(
        Boolean,
        nullable=False,
        default=True,
        doc="Enable push notifications"
    )
    sms_enabled = Column(
        Boolean,
        nullable=False,
        default=False,
        doc="Enable SMS notifications"
    )
    email_enabled = Column(
        Boolean,
        nullable=False,
        default=True,
        doc="Enable email notifications"
    )
    quiet_hours_start = Column(
        Integer,
        nullable=True,
        default=22,
        doc="Quiet hours start (hour of day, 0-23)"
    )
    quiet_hours_end = Column(
        Integer,
        nullable=True,
        default=7,
        doc="Quiet hours end (hour of day, 0-23)"
    )
    sensitivity_level = Column(
        String(20),
        nullable=False,
        default="MODERATE",
        doc="Notification sensitivity (LOW, MODERATE, HIGH)"
    )
    max_daily_notifications = Column(
        Integer,
        nullable=False,
        default=3,
        doc="Maximum notifications per day"
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp when record was created"
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Timestamp when record was last updated"
    )
    
    # Relationships
    profile = relationship("UserProfile", back_populates="notification_preferences", lazy="selectin")

