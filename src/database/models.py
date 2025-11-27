"""
SQLAlchemy ORM models for EpiSPY epidemic surveillance system.

This module defines all database models using async SQLAlchemy with PostgreSQL.
All models use UUID primary keys, include timestamps, and have proper indexes
for performance optimization.

Example usage:
    from src.database.models import Location, OutbreakEvent
    from src.database.connection import get_async_session
    
    async with get_async_session() as session:
        location = Location(
            name="Mumbai",
            latitude=19.0760,
            longitude=72.8777,
            population=12442373,
            country="India",
            region="Maharashtra"
        )
        session.add(location)
        await session.commit()
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
    BigInteger,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, Dict, Any, List
import uuid
import enum

Base = declarative_base()


class RiskLevel(str, enum.Enum):
    """Risk level enumeration for risk assessments."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertSeverity(str, enum.Enum):
    """Alert severity levels."""
    INFO = "INFO"
    WARNING = "WARNING"
    SEVERE = "SEVERE"
    CRITICAL = "CRITICAL"


class AlertStatus(str, enum.Enum):
    """Alert status enumeration."""
    ACTIVE = "ACTIVE"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"


class AgentStatus(str, enum.Enum):
    """Agent execution status."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class Location(Base):
    """
    Geographic location model for tracking epidemic data.
    
    Stores information about locations where outbreaks occur or are monitored.
    Includes geographic coordinates, population data, and administrative information.
    
    Attributes:
        id: UUID primary key
        name: Location name (e.g., "Mumbai", "New York City")
        latitude: Latitude coordinate (-90 to 90)
        longitude: Longitude coordinate (-180 to 180)
        population: Total population of the location
        country: Country name
        region: State/province/region name
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
        
    Relationships:
        outbreak_events: List of OutbreakEvent records for this location
        predictions: List of Prediction records for this location
        risk_assessments: List of RiskAssessment records for this location
        alerts: List of Alert records for this location
        
    Indexes:
        idx_location_coordinates: Composite index on (latitude, longitude)
        idx_location_country_region: Composite index on (country, region)
        
    Example:
        location = Location(
            name="Mumbai",
            latitude=19.0760,
            longitude=72.8777,
            population=12442373,
            country="India",
            region="Maharashtra"
        )
    """
    __tablename__ = "locations"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        doc="Unique identifier for the location"
    )
    name = Column(
        String(255),
        nullable=False,
        index=True,
        doc="Name of the location"
    )
    latitude = Column(
        Float,
        nullable=False,
        doc="Latitude coordinate (-90 to 90)"
    )
    longitude = Column(
        Float,
        nullable=False,
        doc="Longitude coordinate (-180 to 180)"
    )
    population = Column(
        Integer,
        nullable=True,
        doc="Total population of the location"
    )
    country = Column(
        String(100),
        nullable=False,
        index=True,
        doc="Country name"
    )
    region = Column(
        String(100),
        nullable=True,
        index=True,
        doc="State/province/region name"
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
    outbreak_events = relationship(
        "OutbreakEvent",
        back_populates="location",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    predictions = relationship(
        "Prediction",
        back_populates="location",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    risk_assessments = relationship(
        "RiskAssessment",
        back_populates="location",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    alerts = relationship(
        "Alert",
        back_populates="location",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    policies = relationship(
        "Policy",
        back_populates="location",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    location_context = relationship(
        "LocationContext",
        back_populates="location",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_location_coordinates", "latitude", "longitude"),
        Index("idx_location_country_region", "country", "region"),
    )


class OutbreakEvent(Base):
    """
    Outbreak event model for tracking actual disease outbreaks.
    
    Records real outbreak data including case counts, deaths, recoveries,
    and severity metrics. Linked to a specific location and timestamp.
    
    Attributes:
        id: UUID primary key
        location_id: Foreign key to Location
        disease_type: Type of disease (e.g., "COVID-19", "Dengue")
        cases: Total number of cases
        deaths: Number of deaths
        recovered: Number of recovered cases
        active_cases: Number of currently active cases
        timestamp: When the outbreak event occurred
        severity: Severity score (1-10)
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
        
    Relationships:
        location: Location object this event belongs to
        
    Indexes:
        idx_outbreak_location_timestamp: Composite index on (location_id, timestamp)
        idx_outbreak_disease_timestamp: Composite index on (disease_type, timestamp)
        idx_outbreak_severity: Index on severity for filtering
        
    Example:
        event = OutbreakEvent(
            location_id=location.id,
            disease_type="COVID-19",
            cases=1500,
            deaths=25,
            recovered=1200,
            active_cases=275,
            timestamp=datetime.now(),
            severity=7.5
        )
    """
    __tablename__ = "outbreak_events"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        doc="Unique identifier for the outbreak event"
    )
    location_id = Column(
        UUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign key to locations table"
    )
    disease_type = Column(
        String(100),
        nullable=False,
        index=True,
        doc="Type of disease (e.g., COVID-19, Dengue, Malaria)"
    )
    cases = Column(
        Integer,
        nullable=False,
        default=0,
        doc="Total number of cases"
    )
    deaths = Column(
        Integer,
        nullable=False,
        default=0,
        doc="Number of deaths"
    )
    recovered = Column(
        Integer,
        nullable=False,
        default=0,
        doc="Number of recovered cases"
    )
    active_cases = Column(
        Integer,
        nullable=False,
        default=0,
        doc="Number of currently active cases"
    )
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        doc="When the outbreak event occurred"
    )
    severity = Column(
        Float,
        nullable=False,
        index=True,
        doc="Severity score (1-10)"
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
    location = relationship(
        "Location",
        back_populates="outbreak_events",
        lazy="selectin"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_outbreak_location_timestamp", "location_id", "timestamp"),
        Index("idx_outbreak_disease_timestamp", "disease_type", "timestamp"),
        Index("idx_outbreak_severity", "severity"),
    )


class Prediction(Base):
    """
    Prediction model for storing ML/AI model predictions.
    
    Stores predictions made by various models about future outbreak scenarios.
    Includes confidence scores, model versions, and prediction dates.
    
    Attributes:
        id: UUID primary key
        location_id: Foreign key to Location
        predicted_cases: Predicted number of cases
        confidence: Confidence score (0-1)
        prediction_date: Date for which prediction is made
        model_version: Version of the model used
        metadata_json: Additional metadata as JSON
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
        
    Relationships:
        location: Location object this prediction belongs to
        
    Indexes:
        idx_prediction_location_date: Composite index on (location_id, prediction_date)
        idx_prediction_confidence: Index on confidence for filtering
        idx_prediction_model_version: Index on model_version
        
    Example:
        prediction = Prediction(
            location_id=location.id,
            predicted_cases=2000,
            confidence=0.85,
            prediction_date=datetime.now() + timedelta(days=7),
            model_version="seir-v1.2.0",
            metadata_json={"r0": 2.5, "peak_day": 14}
        )
    """
    __tablename__ = "predictions"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        doc="Unique identifier for the prediction"
    )
    location_id = Column(
        UUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign key to locations table"
    )
    predicted_cases = Column(
        Integer,
        nullable=False,
        doc="Predicted number of cases"
    )
    confidence = Column(
        Float,
        nullable=False,
        index=True,
        doc="Confidence score (0-1)"
    )
    prediction_date = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        doc="Date for which prediction is made"
    )
    model_version = Column(
        String(50),
        nullable=False,
        index=True,
        doc="Version of the model used (e.g., seir-v1.2.0)"
    )
    metadata_json = Column(
        JSON,
        nullable=True,
        doc="Additional metadata as JSON (e.g., model parameters, features)"
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
    location = relationship(
        "Location",
        back_populates="predictions",
        lazy="selectin"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_prediction_location_date", "location_id", "prediction_date"),
        Index("idx_prediction_confidence", "confidence"),
        Index("idx_prediction_model_version", "model_version"),
    )


class RiskAssessment(Base):
    """
    Risk assessment model for storing risk analysis results.
    
    Stores risk assessments calculated for locations, including risk levels,
    scores, and contributing factors. Used for alert generation and monitoring.
    
    Attributes:
        id: UUID primary key
        location_id: Foreign key to Location
        risk_level: Risk level (LOW, MEDIUM, HIGH, CRITICAL)
        risk_score: Numeric risk score (0-10)
        factors_json: JSON object containing risk factors and their contributions
        timestamp: When the risk assessment was calculated
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
        
    Relationships:
        location: Location object this assessment belongs to
        
    Indexes:
        idx_risk_location_timestamp: Composite index on (location_id, timestamp)
        idx_risk_level: Index on risk_level for filtering
        idx_risk_score: Index on risk_score for sorting
        
    Example:
        assessment = RiskAssessment(
            location_id=location.id,
            risk_level=RiskLevel.HIGH,
            risk_score=7.5,
            factors_json={
                "case_growth_rate": 0.15,
                "population_density": 0.8,
                "healthcare_capacity": 0.6
            },
            timestamp=datetime.now()
        )
    """
    __tablename__ = "risk_assessments"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        doc="Unique identifier for the risk assessment"
    )
    location_id = Column(
        UUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign key to locations table"
    )
    risk_level = Column(
        SQLEnum(RiskLevel),
        nullable=False,
        index=True,
        doc="Risk level (LOW, MEDIUM, HIGH, CRITICAL)"
    )
    risk_score = Column(
        Float,
        nullable=False,
        index=True,
        doc="Numeric risk score (0-10)"
    )
    factors_json = Column(
        JSON,
        nullable=True,
        doc="JSON object containing risk factors and their contributions"
    )
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        doc="When the risk assessment was calculated"
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
    location = relationship(
        "Location",
        back_populates="risk_assessments",
        lazy="selectin"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_risk_location_timestamp", "location_id", "timestamp"),
        Index("idx_risk_level", "risk_level"),
        Index("idx_risk_score", "risk_score"),
    )


class Alert(Base):
    """
    Alert model for storing system-generated alerts.
    
    Stores alerts generated by the system based on risk assessments, predictions,
    or outbreak events. Tracks alert status, acknowledgment, and recipients.
    
    Attributes:
        id: UUID primary key
        location_id: Foreign key to Location
        severity: Alert severity (INFO, WARNING, SEVERE, CRITICAL)
        message: Alert message text
        status: Alert status (ACTIVE, ACKNOWLEDGED, RESOLVED, DISMISSED)
        recipient_list: JSON array of recipient identifiers
        acknowledged_at: When the alert was acknowledged
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
        
    Relationships:
        location: Location object this alert belongs to
        
    Indexes:
        idx_alert_location_status: Composite index on (location_id, status)
        idx_alert_severity_status: Composite index on (severity, status)
        idx_alert_created: Index on created_at for sorting
        
    Example:
        alert = Alert(
            location_id=location.id,
            severity=AlertSeverity.CRITICAL,
            message="High risk outbreak detected in Mumbai",
            status=AlertStatus.ACTIVE,
            recipient_list=["admin@example.com", "health_dept@example.com"]
        )
    """
    __tablename__ = "alerts"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        doc="Unique identifier for the alert"
    )
    location_id = Column(
        UUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign key to locations table"
    )
    severity = Column(
        SQLEnum(AlertSeverity),
        nullable=False,
        index=True,
        doc="Alert severity level"
    )
    message = Column(
        Text,
        nullable=False,
        doc="Alert message text"
    )
    status = Column(
        SQLEnum(AlertStatus),
        nullable=False,
        default=AlertStatus.ACTIVE,
        index=True,
        doc="Alert status"
    )
    recipient_list = Column(
        JSON,
        nullable=True,
        doc="JSON array of recipient identifiers (emails, user IDs, etc.)"
    )
    acknowledged_at = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="When the alert was acknowledged"
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
    location = relationship(
        "Location",
        back_populates="alerts",
        lazy="selectin"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_alert_location_status", "location_id", "status"),
        Index("idx_alert_severity_status", "severity", "status"),
        Index("idx_alert_created", "created_at"),
    )


class AgentExecution(Base):
    """
    Agent execution model for tracking LangGraph agent runs.
    
    Stores information about agent executions including task descriptions,
    status, results, and performance metrics. Used for monitoring and debugging
    agent-based workflows.
    
    Attributes:
        id: UUID primary key
        agent_type: Type of agent (e.g., "epidemic_analyzer", "risk_calculator")
        task_description: Description of the task being executed
        status: Execution status (PENDING, RUNNING, COMPLETED, FAILED, CANCELLED)
        result_json: JSON object containing execution results
        started_at: When execution started
        completed_at: When execution completed
        execution_time_ms: Execution time in milliseconds
        error_message: Error message if execution failed
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
        
    Indexes:
        idx_agent_type_status: Composite index on (agent_type, status)
        idx_agent_started: Index on started_at for sorting
        idx_agent_execution_time: Index on execution_time_ms for performance analysis
        
    Example:
        execution = AgentExecution(
            agent_type="epidemic_analyzer",
            task_description="Analyze outbreak risk for Mumbai",
            status=AgentStatus.RUNNING,
            started_at=datetime.now()
        )
    """
    __tablename__ = "agent_executions"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        doc="Unique identifier for the agent execution"
    )
    agent_type = Column(
        String(100),
        nullable=False,
        index=True,
        doc="Type of agent (e.g., epidemic_analyzer, risk_calculator)"
    )
    task_description = Column(
        Text,
        nullable=False,
        doc="Description of the task being executed"
    )
    status = Column(
        SQLEnum(AgentStatus),
        nullable=False,
        default=AgentStatus.PENDING,
        index=True,
        doc="Execution status"
    )
    result_json = Column(
        JSON,
        nullable=True,
        doc="JSON object containing execution results"
    )
    started_at = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        doc="When execution started"
    )
    completed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="When execution completed"
    )
    execution_time_ms = Column(
        BigInteger,
        nullable=True,
        index=True,
        doc="Execution time in milliseconds"
    )
    error_message = Column(
        Text,
        nullable=True,
        doc="Error message if execution failed"
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
    
    # Indexes
    __table_args__ = (
        Index("idx_agent_type_status", "agent_type", "status"),
        Index("idx_agent_started", "started_at"),
        Index("idx_agent_execution_time", "execution_time_ms"),
    )


class PolicyType(str, enum.Enum):
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


class PolicyStatus(str, enum.Enum):
    """Policy implementation status."""
    PROPOSED = "PROPOSED"
    ACTIVE = "ACTIVE"
    MODIFIED = "MODIFIED"
    ENDED = "ENDED"
    SUSPENDED = "SUSPENDED"


class EvidenceQuality(str, enum.Enum):
    """Evidence quality levels for policy outcomes."""
    VERY_LOW = "VERY_LOW"
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


class Policy(Base):
    """
    Global epidemic response policy model.
    
    Stores information about epidemic response policies implemented globally,
    including policy type, description, implementation details, and metadata.
    
    Attributes:
        id: UUID primary key
        location_id: Foreign key to Location (where policy was implemented)
        policy_type: Type of policy (LOCKDOWN, TESTING_STRATEGY, etc.)
        title: Policy title/name
        description: Detailed policy description
        implementation_details: JSON object with specific implementation parameters
        start_date: When policy was implemented
        end_date: When policy ended (if applicable)
        status: Current status of the policy
        source: Source of policy information (government, WHO, etc.)
        source_url: URL to original policy document
        metadata_json: Additional metadata (costs, compliance rates, etc.)
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
        
    Relationships:
        location: Location object where policy was implemented
        outcomes: List of PolicyOutcome records
        implementations: List of PolicyImplementation records
        
    Indexes:
        idx_policy_location_type: Composite index on (location_id, policy_type)
        idx_policy_type_status: Composite index on (policy_type, status)
        idx_policy_dates: Composite index on (start_date, end_date)
        
    Example:
        policy = Policy(
            location_id=location.id,
            policy_type=PolicyType.LOCKDOWN,
            title="National Lockdown Phase 1",
            description="Complete lockdown with essential services only",
            start_date=datetime(2020, 3, 25),
            status=PolicyStatus.ACTIVE,
            source="Government of India"
        )
    """
    __tablename__ = "policies"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        doc="Unique identifier for the policy"
    )
    location_id = Column(
        UUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign key to locations table"
    )
    policy_type = Column(
        SQLEnum(PolicyType),
        nullable=False,
        index=True,
        doc="Type of policy"
    )
    title = Column(
        String(500),
        nullable=False,
        doc="Policy title/name"
    )
    description = Column(
        Text,
        nullable=False,
        doc="Detailed policy description"
    )
    implementation_details = Column(
        JSON,
        nullable=True,
        doc="JSON object with specific implementation parameters (e.g., duration, restrictions, coverage)"
    )
    start_date = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        doc="When policy was implemented"
    )
    end_date = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        doc="When policy ended (if applicable)"
    )
    status = Column(
        SQLEnum(PolicyStatus),
        nullable=False,
        default=PolicyStatus.ACTIVE,
        index=True,
        doc="Current status of the policy"
    )
    source = Column(
        String(255),
        nullable=True,
        doc="Source of policy information (government, WHO, research institution, etc.)"
    )
    source_url = Column(
        String(1000),
        nullable=True,
        doc="URL to original policy document or announcement"
    )
    metadata_json = Column(
        JSON,
        nullable=True,
        doc="Additional metadata (costs, compliance rates, enforcement mechanisms, etc.)"
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
    location = relationship(
        "Location",
        back_populates="policies",
        lazy="selectin"
    )
    outcomes = relationship(
        "PolicyOutcome",
        back_populates="policy",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    implementations = relationship(
        "PolicyImplementation",
        back_populates="policy",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_policy_location_type", "location_id", "policy_type"),
        Index("idx_policy_type_status", "policy_type", "status"),
        Index("idx_policy_dates", "start_date", "end_date"),
    )


class PolicyOutcome(Base):
    """
    Policy outcome tracking model.
    
    Stores effectiveness metrics and outcomes for policies, including
    impact on case counts, deaths, economic effects, and other metrics.
    
    Attributes:
        id: UUID primary key
        policy_id: Foreign key to Policy
        effectiveness_score: Overall effectiveness score (0-10)
        case_reduction_percent: Percentage reduction in cases
        death_reduction_percent: Percentage reduction in deaths
        r0_change: Change in reproduction number
        economic_impact_score: Economic impact score (0-10, higher = more negative)
        social_impact_score: Social impact score (0-10, higher = more negative)
        healthcare_impact_score: Healthcare system impact score (0-10)
        measurement_period_start: Start of measurement period
        measurement_period_end: End of measurement period
        evidence_quality: Quality of evidence (VERY_LOW to VERY_HIGH)
        methodology: Description of how outcomes were measured
        data_sources: JSON array of data sources used
        metrics_json: Additional metrics as JSON
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
        
    Relationships:
        policy: Policy object this outcome belongs to
        
    Indexes:
        idx_outcome_policy: Index on policy_id
        idx_outcome_effectiveness: Index on effectiveness_score
        idx_outcome_evidence: Index on evidence_quality
        
    Example:
        outcome = PolicyOutcome(
            policy_id=policy.id,
            effectiveness_score=7.5,
            case_reduction_percent=45.2,
            death_reduction_percent=38.7,
            r0_change=-0.8,
            evidence_quality=EvidenceQuality.HIGH
        )
    """
    __tablename__ = "policy_outcomes"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        doc="Unique identifier for the policy outcome"
    )
    policy_id = Column(
        UUID(as_uuid=True),
        ForeignKey("policies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign key to policies table"
    )
    effectiveness_score = Column(
        Float,
        nullable=False,
        index=True,
        doc="Overall effectiveness score (0-10, higher = more effective)"
    )
    case_reduction_percent = Column(
        Float,
        nullable=True,
        doc="Percentage reduction in cases"
    )
    death_reduction_percent = Column(
        Float,
        nullable=True,
        doc="Percentage reduction in deaths"
    )
    r0_change = Column(
        Float,
        nullable=True,
        doc="Change in reproduction number (R0)"
    )
    economic_impact_score = Column(
        Float,
        nullable=True,
        doc="Economic impact score (0-10, higher = more negative impact)"
    )
    social_impact_score = Column(
        Float,
        nullable=True,
        doc="Social impact score (0-10, higher = more negative impact)"
    )
    healthcare_impact_score = Column(
        Float,
        nullable=True,
        doc="Healthcare system impact score (0-10, higher = better)"
    )
    measurement_period_start = Column(
        DateTime(timezone=True),
        nullable=False,
        doc="Start of measurement period"
    )
    measurement_period_end = Column(
        DateTime(timezone=True),
        nullable=False,
        doc="End of measurement period"
    )
    evidence_quality = Column(
        SQLEnum(EvidenceQuality),
        nullable=False,
        default=EvidenceQuality.MODERATE,
        index=True,
        doc="Quality of evidence"
    )
    methodology = Column(
        Text,
        nullable=True,
        doc="Description of how outcomes were measured"
    )
    data_sources = Column(
        JSON,
        nullable=True,
        doc="JSON array of data sources used"
    )
    metrics_json = Column(
        JSON,
        nullable=True,
        doc="Additional metrics as JSON (hospitalizations, ICU usage, etc.)"
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
    policy = relationship(
        "Policy",
        back_populates="outcomes",
        lazy="selectin"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_outcome_policy", "policy_id"),
        Index("idx_outcome_effectiveness", "effectiveness_score"),
        Index("idx_outcome_evidence", "evidence_quality"),
    )


class LocationContext(Base):
    """
    Location context model for similarity matching.
    
    Stores contextual information about locations needed for similarity
    matching, including demographics, economics, infrastructure, culture,
    and health system characteristics.
    
    Attributes:
        id: UUID primary key
        location_id: Foreign key to Location (one-to-one relationship)
        population_density: Population density (people per km²)
        gdp_per_capita: GDP per capita in USD
        healthcare_capacity: Healthcare capacity score (0-10)
        urbanization_rate: Urbanization percentage (0-100)
        literacy_rate: Literacy rate (0-100)
        internet_penetration: Internet penetration percentage (0-100)
        cultural_factors: JSON object with cultural characteristics
        economic_structure: JSON object with economic structure data
        infrastructure_quality: Infrastructure quality score (0-10)
        governance_effectiveness: Governance effectiveness score (0-10)
        public_trust_score: Public trust in government score (0-10)
        climate_zone: Climate zone classification
        geography_type: Geography type (urban, rural, mixed, etc.)
        context_json: Additional contextual data as JSON
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
        
    Relationships:
        location: Location object this context belongs to
        
    Indexes:
        idx_context_location: Unique index on location_id
        
    Example:
        context = LocationContext(
            location_id=location.id,
            population_density=20500,
            gdp_per_capita=2100,
            healthcare_capacity=6.5,
            urbanization_rate=45.2
        )
    """
    __tablename__ = "location_contexts"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        doc="Unique identifier for the location context"
    )
    location_id = Column(
        UUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
        doc="Foreign key to locations table (one-to-one)"
    )
    population_density = Column(
        Float,
        nullable=True,
        doc="Population density (people per km²)"
    )
    gdp_per_capita = Column(
        Float,
        nullable=True,
        doc="GDP per capita in USD"
    )
    healthcare_capacity = Column(
        Float,
        nullable=True,
        doc="Healthcare capacity score (0-10)"
    )
    urbanization_rate = Column(
        Float,
        nullable=True,
        doc="Urbanization percentage (0-100)"
    )
    literacy_rate = Column(
        Float,
        nullable=True,
        doc="Literacy rate (0-100)"
    )
    internet_penetration = Column(
        Float,
        nullable=True,
        doc="Internet penetration percentage (0-100)"
    )
    cultural_factors = Column(
        JSON,
        nullable=True,
        doc="JSON object with cultural characteristics (collectivism, religion, etc.)"
    )
    economic_structure = Column(
        JSON,
        nullable=True,
        doc="JSON object with economic structure data (sector distribution, etc.)"
    )
    infrastructure_quality = Column(
        Float,
        nullable=True,
        doc="Infrastructure quality score (0-10)"
    )
    governance_effectiveness = Column(
        Float,
        nullable=True,
        doc="Governance effectiveness score (0-10)"
    )
    public_trust_score = Column(
        Float,
        nullable=True,
        doc="Public trust in government score (0-10)"
    )
    climate_zone = Column(
        String(50),
        nullable=True,
        doc="Climate zone classification"
    )
    geography_type = Column(
        String(50),
        nullable=True,
        doc="Geography type (urban, rural, mixed, coastal, etc.)"
    )
    context_json = Column(
        JSON,
        nullable=True,
        doc="Additional contextual data as JSON"
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
    location = relationship(
        "Location",
        back_populates="location_context",
        uselist=False,
        lazy="selectin"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_context_location", "location_id", unique=True),
    )


class PolicyImplementation(Base):
    """
    Policy implementation guide model.
    
    Stores detailed implementation guides for policies, including
    step-by-step instructions, resource requirements, and adaptation
    recommendations for different contexts.
    
    Attributes:
        id: UUID primary key
        policy_id: Foreign key to Policy
        implementation_guide: Detailed implementation guide text
        resource_requirements: JSON object with resource requirements
        adaptation_recommendations: JSON object with context-specific adaptations
        estimated_cost: Estimated implementation cost
        estimated_duration: Estimated implementation duration in days
        prerequisites: JSON array of prerequisites
        success_factors: JSON array of key success factors
        potential_challenges: JSON array of potential challenges
        monitoring_indicators: JSON array of indicators to monitor
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
        
    Relationships:
        policy: Policy object this implementation guide belongs to
        
    Example:
        implementation = PolicyImplementation(
            policy_id=policy.id,
            implementation_guide="Step 1: Establish testing centers...",
            estimated_cost=5000000,
            estimated_duration=30
        )
    """
    __tablename__ = "policy_implementations"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        doc="Unique identifier for the policy implementation"
    )
    policy_id = Column(
        UUID(as_uuid=True),
        ForeignKey("policies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign key to policies table"
    )
    implementation_guide = Column(
        Text,
        nullable=False,
        doc="Detailed implementation guide text"
    )
    resource_requirements = Column(
        JSON,
        nullable=True,
        doc="JSON object with resource requirements (personnel, equipment, budget)"
    )
    adaptation_recommendations = Column(
        JSON,
        nullable=True,
        doc="JSON object with context-specific adaptation recommendations"
    )
    estimated_cost = Column(
        Float,
        nullable=True,
        doc="Estimated implementation cost in USD"
    )
    estimated_duration = Column(
        Integer,
        nullable=True,
        doc="Estimated implementation duration in days"
    )
    prerequisites = Column(
        JSON,
        nullable=True,
        doc="JSON array of prerequisites (infrastructure, legal framework, etc.)"
    )
    success_factors = Column(
        JSON,
        nullable=True,
        doc="JSON array of key success factors"
    )
    potential_challenges = Column(
        JSON,
        nullable=True,
        doc="JSON array of potential challenges and mitigation strategies"
    )
    monitoring_indicators = Column(
        JSON,
        nullable=True,
        doc="JSON array of indicators to monitor during implementation"
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
    policy = relationship(
        "Policy",
        back_populates="implementations",
        lazy="selectin"
    )
