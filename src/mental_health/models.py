"""
Data models for mental health surveillance.

This module defines database models for storing mental health indicators,
counseling records, hotline transcripts, and related data in a privacy-preserving way.
"""
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, ForeignKey,
    Index, Text, Enum as SQLEnum, JSON, Boolean
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import enum

from ..database.models import Base, Location


class MentalHealthIndicator(str, enum.Enum):
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


class MentalHealthSeverity(str, enum.Enum):
    """Mental health severity levels."""
    MILD = "MILD"
    MODERATE = "MODERATE"
    SEVERE = "SEVERE"
    CRITICAL = "CRITICAL"


class DataSourceType(str, enum.Enum):
    """Data source types for mental health indicators."""
    COUNSELING_SESSION = "COUNSELING_SESSION"
    CRISIS_HOTLINE = "CRISIS_HOTLINE"
    SOCIAL_MEDIA = "SOCIAL_MEDIA"
    SCHOOL_ABSENTEEISM = "SCHOOL_ABSENTEEISM"
    HEALTHCARE_RECORD = "HEALTHCARE_RECORD"
    COMMUNITY_SURVEY = "COMMUNITY_SURVEY"


class CounselingSession(Base):
    """
    Aggregated counseling session data (anonymized).
    
    Stores anonymized, aggregated data from counseling sessions to detect
    mental health patterns without identifying individuals.
    
    Attributes:
        id: UUID primary key
        location_id: Foreign key to Location
        session_date: Date of session
        age_group: Age group (e.g., "18-25", "26-35")
        gender_group: Generalized gender group (if available, "M", "F", "OTHER", "UNKNOWN")
        primary_indicator: Primary mental health indicator
        severity: Severity level
        session_duration_minutes: Session duration
        intervention_type: Type of intervention provided
        outcome_score: Outcome score (0-10, anonymized)
        is_crisis_session: Whether this was a crisis session
        anonymized_notes_summary: Anonymized summary of session themes
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
        
    Note: No personally identifiable information is stored.
    """
    __tablename__ = "counseling_sessions"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    location_id = Column(
        UUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    session_date = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )
    age_group = Column(
        String(20),
        nullable=True,
        index=True
    )
    gender_group = Column(
        String(20),
        nullable=True
    )
    primary_indicator = Column(
        SQLEnum(MentalHealthIndicator),
        nullable=False,
        index=True
    )
    severity = Column(
        SQLEnum(MentalHealthSeverity),
        nullable=False,
        index=True
    )
    session_duration_minutes = Column(
        Integer,
        nullable=True
    )
    intervention_type = Column(
        String(100),
        nullable=True
    )
    outcome_score = Column(
        Float,
        nullable=True
    )
    is_crisis_session = Column(
        Boolean,
        nullable=False,
        default=False,
        index=True
    )
    anonymized_notes_summary = Column(
        Text,
        nullable=True
    )
    metadata_json = Column(
        JSON,
        nullable=True
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships
    location = relationship("Location", lazy="selectin")
    
    # Indexes
    __table_args__ = (
        Index("idx_counseling_location_date", "location_id", "session_date"),
        Index("idx_counseling_indicator_severity", "primary_indicator", "severity"),
        Index("idx_counseling_crisis", "is_crisis_session", "session_date"),
    )


class CrisisHotlineTranscript(Base):
    """
    Anonymized crisis hotline call transcript analysis.
    
    Stores NLP-processed, anonymized data from crisis hotline calls.
    No actual transcripts are stored - only anonymized themes and indicators.
    
    Attributes:
        id: UUID primary key
        location_id: Foreign key to Location (generalized to city/region)
        call_date: Date of call
        call_duration_seconds: Call duration
        age_group: Generalized age group
        primary_indicators: List of detected mental health indicators
        crisis_score: Crisis severity score (0-10)
        language_patterns: Anonymized language patterns detected
        sentiment_scores: Sentiment analysis scores
        keywords_detected: Anonymized keywords (no PII)
        intervention_provided: Intervention type
        follow_up_required: Whether follow-up was recommended
        anonymized_themes: Anonymized thematic summary
        created_at: Timestamp when record was created
    """
    __tablename__ = "crisis_hotline_transcripts"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    location_id = Column(
        UUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    call_date = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )
    call_duration_seconds = Column(
        Integer,
        nullable=True
    )
    age_group = Column(
        String(20),
        nullable=True,
        index=True
    )
    primary_indicators = Column(
        JSON,  # Array of MentalHealthIndicator enum values
        nullable=False
    )
    crisis_score = Column(
        Float,
        nullable=False,
        index=True
    )
    language_patterns = Column(
        JSON,
        nullable=True
    )
    sentiment_scores = Column(
        JSON,
        nullable=True
    )
    keywords_detected = Column(
        JSON,  # Anonymized keywords only
        nullable=True
    )
    intervention_provided = Column(
        String(100),
        nullable=True
    )
    follow_up_required = Column(
        Boolean,
        nullable=False,
        default=False
    )
    anonymized_themes = Column(
        Text,
        nullable=True
    )
    metadata_json = Column(
        JSON,
        nullable=True
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Relationships
    location = relationship("Location", lazy="selectin")
    
    # Indexes
    __table_args__ = (
        Index("idx_hotline_location_date", "location_id", "call_date"),
        Index("idx_hotline_crisis_score", "crisis_score", "call_date"),
    )


class SocialMediaSentiment(Base):
    """
    Aggregated social media sentiment data for mental health monitoring.
    
    Stores anonymized, aggregated sentiment data from social media posts
    (no individual posts, only aggregated patterns).
    
    Attributes:
        id: UUID primary key
        location_id: Foreign key to Location
        date: Date of data collection
        platform: Social media platform (generalized)
        sentiment_score: Average sentiment score (-1 to 1)
        mental_health_keyword_frequency: Frequency of mental health keywords
        anxiety_mentions: Estimated anxiety-related mentions
        depression_mentions: Estimated depression-related mentions
        crisis_keywords: Crisis keyword frequency
        engagement_level: Overall engagement level
        sample_size: Number of posts analyzed (anonymized count)
        metadata_json: Additional metadata
        created_at: Timestamp when record was created
    """
    __tablename__ = "social_media_sentiment"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    location_id = Column(
        UUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    date = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )
    platform = Column(
        String(50),
        nullable=True
    )
    sentiment_score = Column(
        Float,
        nullable=False
    )
    mental_health_keyword_frequency = Column(
        Float,
        nullable=True
    )
    anxiety_mentions = Column(
        Integer,
        nullable=True
    )
    depression_mentions = Column(
        Integer,
        nullable=True
    )
    crisis_keywords = Column(
        Integer,
        nullable=True
    )
    engagement_level = Column(
        Float,
        nullable=True
    )
    sample_size = Column(
        Integer,
        nullable=True
    )
    metadata_json = Column(
        JSON,
        nullable=True
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Relationships
    location = relationship("Location", lazy="selectin")
    
    # Indexes
    __table_args__ = (
        Index("idx_social_location_date", "location_id", "date"),
        Index("idx_social_sentiment_date", "sentiment_score", "date"),
    )


class SchoolAbsenteeism(Base):
    """
    School absenteeism data as a mental health indicator.
    
    Tracks aggregated school absenteeism data which can be an early indicator
    of youth mental health issues during epidemics.
    
    Attributes:
        id: UUID primary key
        location_id: Foreign key to Location
        date: Date of attendance record
        school_type: Type of school (e.g., "ELEMENTARY", "MIDDLE", "HIGH")
        total_enrollment: Total enrollment (aggregated)
        absent_count: Number of absences
        absence_rate: Absence rate percentage
        mental_health_related_absences: Estimated mental health-related absences
        chronic_absenteeism_rate: Chronic absenteeism rate
        metadata_json: Additional metadata
        created_at: Timestamp when record was created
    """
    __tablename__ = "school_absenteeism"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    location_id = Column(
        UUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    date = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )
    school_type = Column(
        String(50),
        nullable=True,
        index=True
    )
    total_enrollment = Column(
        Integer,
        nullable=True
    )
    absent_count = Column(
        Integer,
        nullable=False
    )
    absence_rate = Column(
        Float,
        nullable=False,
        index=True
    )
    mental_health_related_absences = Column(
        Integer,
        nullable=True
    )
    chronic_absenteeism_rate = Column(
        Float,
        nullable=True,
        index=True
    )
    metadata_json = Column(
        JSON,
        nullable=True
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Relationships
    location = relationship("Location", lazy="selectin")
    
    # Indexes
    __table_args__ = (
        Index("idx_absenteeism_location_date", "location_id", "date"),
        Index("idx_absenteeism_rate_date", "absence_rate", "date"),
    )


class MentalHealthHotspot(Base):
    """
    Mental health hotspot detection results.
    
    Stores detected mental health hotspots based on clustering analysis
    of various indicators.
    
    Attributes:
        id: UUID primary key
        location_id: Foreign key to Location
        detected_date: Date when hotspot was detected
        hotspot_score: Hotspot risk score (0-10)
        primary_indicators: List of primary mental health indicators
        contributing_factors: Contributing factors to hotspot
        severity: Overall hotspot severity
        affected_population_estimate: Estimated affected population
        trend: Trend direction (INCREASING, DECREASING, STABLE)
        is_active: Whether hotspot is currently active
        deactivated_date: When hotspot was deactivated
        alert_generated: Whether alert was generated
        metadata_json: Additional metadata
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
    """
    __tablename__ = "mental_health_hotspots"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    location_id = Column(
        UUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    detected_date = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )
    hotspot_score = Column(
        Float,
        nullable=False,
        index=True
    )
    primary_indicators = Column(
        JSON,
        nullable=False
    )
    contributing_factors = Column(
        JSON,
        nullable=True
    )
    severity = Column(
        SQLEnum(MentalHealthSeverity),
        nullable=False,
        index=True
    )
    affected_population_estimate = Column(
        Integer,
        nullable=True
    )
    trend = Column(
        String(20),
        nullable=True
    )
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        index=True
    )
    deactivated_date = Column(
        DateTime(timezone=True),
        nullable=True
    )
    alert_generated = Column(
        Boolean,
        nullable=False,
        default=False
    )
    metadata_json = Column(
        JSON,
        nullable=True
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships
    location = relationship("Location", lazy="selectin")
    
    # Indexes
    __table_args__ = (
        Index("idx_hotspot_location_active", "location_id", "is_active"),
        Index("idx_hotspot_score_date", "hotspot_score", "detected_date"),
    )


class MentalHealthResource(Base):
    """
    Mental health resources available in locations.
    
    Stores information about available mental health resources for
    recommendation when hotspots are detected.
    
    Attributes:
        id: UUID primary key
        location_id: Foreign key to Location
        resource_type: Type of resource
        name: Resource name (if publicly available)
        contact_info: Contact information (generalized)
        services_offered: Services offered
        capacity: Capacity (if available)
        availability_status: Current availability
        metadata_json: Additional metadata
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
    """
    __tablename__ = "mental_health_resources"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    location_id = Column(
        UUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    resource_type = Column(
        String(100),
        nullable=False,
        index=True
    )
    name = Column(
        String(255),
        nullable=True
    )
    contact_info = Column(
        JSON,
        nullable=True
    )
    services_offered = Column(
        JSON,
        nullable=True
    )
    capacity = Column(
        Integer,
        nullable=True
    )
    availability_status = Column(
        String(50),
        nullable=True
    )
    metadata_json = Column(
        JSON,
        nullable=True
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships
    location = relationship("Location", lazy="selectin")
    
    # Indexes
    __table_args__ = (
        Index("idx_resource_location_type", "location_id", "resource_type"),
    )

