"""Pydantic schemas for prediction endpoints."""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class AlertLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class TrendDirection(str, Enum):
    INCREASING = "INCREASING"
    STABLE = "STABLE"
    DECREASING = "DECREASING"

class PatientRecord(BaseModel):
    """Individual patient record schema."""
    patient_id: str = Field(..., description="Anonymized patient identifier")
    visit_date: datetime = Field(..., description="Date of visit")
    location: str = Field(..., description="Healthcare facility location")
    age_group: str = Field(..., description="Patient age group")
    symptoms: List[str] = Field(..., description="List of symptoms")
    severity_score: float = Field(..., ge=1, le=10, description="Severity score 1-10")
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    
    @validator('symptoms')
    def symptoms_not_empty(cls, v):
        if not v:
            raise ValueError('Symptoms list cannot be empty')
        return v

class PredictionRequest(BaseModel):
    """Request for epidemic prediction analysis."""
    patient_data: List[PatientRecord] = Field(..., description="Patient data to analyze")
    start_date: datetime = Field(..., description="Analysis start date")
    end_date: datetime = Field(..., description="Analysis end date")
    location_filter: Optional[str] = Field(None, description="Filter by location")
    analysis_type: str = Field("comprehensive", description="Type of analysis")
    
    @validator('patient_data')
    def patient_data_not_empty(cls, v):
        if not v:
            raise ValueError('Patient data cannot be empty')
        return v
    
    @validator('end_date')
    def end_date_after_start(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v

class PredictionResponse(BaseModel):
    """Response from epidemic prediction analysis."""
    analysis_id: str = Field(..., description="Unique analysis identifier")
    risk_score: float = Field(..., ge=0, le=10, description="Overall risk score 0-10")
    outbreak_probability: float = Field(..., ge=0, le=1, description="Outbreak probability 0-1")
    predicted_peak_date: Optional[datetime] = Field(None, description="Predicted outbreak peak")
    affected_locations: List[str] = Field(..., description="Locations at risk")
    symptom_patterns: List[str] = Field(..., description="Identified symptom patterns")
    recommended_actions: List[str] = Field(..., description="Recommended response actions")
    confidence_score: float = Field(..., ge=0, le=1, description="Model confidence 0-1")
    model_version: str = Field(..., description="Model version used")
    analysis_timestamp: datetime = Field(..., description="When analysis was performed")

class RiskAssessmentResponse(BaseModel):
    """Current risk assessment response."""
    location: str = Field(..., description="Location assessed")
    current_risk_score: float = Field(..., ge=0, le=10, description="Current risk score")
    alert_level: AlertLevel = Field(..., description="Current alert level")
    active_cases: int = Field(..., ge=0, description="Number of active cases")
    trend: TrendDirection = Field(..., description="Risk trend direction")
    last_updated: datetime = Field(..., description="Last update timestamp")
    next_update: datetime = Field(..., description="Next scheduled update")

class ContinuousMonitoringConfig(BaseModel):
    """Configuration for continuous monitoring."""
    monitoring_interval: int = Field(300, ge=60, description="Monitoring interval in seconds")
    alert_threshold: float = Field(0.7, ge=0, le=1, description="Alert threshold")
    locations: Optional[List[str]] = Field(None, description="Locations to monitor")
    enable_auto_alerts: bool = Field(True, description="Enable automatic alerts")

class MonitoringStatus(BaseModel):
    """Status of continuous monitoring."""
    is_active: bool = Field(..., description="Whether monitoring is active")
    last_check: datetime = Field(..., description="Last monitoring check")
    next_check: datetime = Field(..., description="Next scheduled check")
    total_checks: int = Field(..., ge=0, description="Total checks performed")
    alerts_generated: int = Field(..., ge=0, description="Alerts generated")
