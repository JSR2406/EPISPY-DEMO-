"""
Factory Boy factories for generating test data.

This module provides factories for creating test instances of all models
in the EpiSPY system. Factories use realistic data patterns and can be
customized per test.
"""
import factory
from factory import fuzzy
from datetime import datetime, timedelta
import uuid
from typing import Optional, Dict, Any

# Import models
from src.database.models import (
    Location,
    OutbreakEvent,
    Prediction,
    RiskAssessment,
    Alert,
    AgentExecution,
    RiskLevel,
    AlertSeverity,
    AlertStatus,
    AgentStatus
)


class LocationFactory(factory.Factory):
    """Factory for creating Location test instances."""
    
    class Meta:
        model = Location
        sqlalchemy_session_persistence = 'commit'
    
    id = factory.LazyFunction(uuid.uuid4)
    name = factory.Faker('city')
    latitude = factory.LazyFunction(lambda: fuzzy.FuzzyFloat(-90, 90).fuzz())
    longitude = factory.LazyFunction(lambda: fuzzy.FuzzyFloat(-180, 180).fuzz())
    population = factory.LazyFunction(lambda: fuzzy.FuzzyInteger(1000, 50000000).fuzz())
    country = factory.Faker('country')
    region = factory.Faker('state')
    created_at = factory.LazyFunction(datetime.now)
    updated_at = factory.LazyFunction(datetime.now)


class OutbreakEventFactory(factory.Factory):
    """Factory for creating OutbreakEvent test instances."""
    
    class Meta:
        model = OutbreakEvent
        sqlalchemy_session_persistence = 'commit'
    
    id = factory.LazyFunction(uuid.uuid4)
    location_id = factory.LazyFunction(uuid.uuid4)
    disease_type = factory.Iterator(["COVID-19", "Dengue", "Malaria", "Influenza", "Cholera"])
    cases = factory.LazyFunction(lambda: fuzzy.FuzzyInteger(1, 10000).fuzz())
    deaths = factory.LazyFunction(lambda: fuzzy.FuzzyInteger(0, 500).fuzz())
    recovered = factory.LazyFunction(lambda: fuzzy.FuzzyInteger(0, 8000).fuzz())
    active_cases = factory.LazyFunction(lambda: fuzzy.FuzzyInteger(0, 5000).fuzz())
    timestamp = factory.LazyFunction(lambda: datetime.now() - timedelta(days=fuzzy.FuzzyInteger(0, 30).fuzz()))
    severity = factory.LazyFunction(lambda: fuzzy.FuzzyFloat(1.0, 10.0).fuzz())
    created_at = factory.LazyFunction(datetime.now)
    updated_at = factory.LazyFunction(datetime.now)


class PredictionFactory(factory.Factory):
    """Factory for creating Prediction test instances."""
    
    class Meta:
        model = Prediction
        sqlalchemy_session_persistence = 'commit'
    
    id = factory.LazyFunction(uuid.uuid4)
    location_id = factory.LazyFunction(uuid.uuid4)
    predicted_cases = factory.LazyFunction(lambda: fuzzy.FuzzyInteger(1, 50000).fuzz())
    confidence = factory.LazyFunction(lambda: fuzzy.FuzzyFloat(0.0, 1.0).fuzz())
    prediction_date = factory.LazyFunction(lambda: datetime.now() + timedelta(days=fuzzy.FuzzyInteger(1, 30).fuzz()))
    model_version = factory.Iterator(["seir-v1.0.0", "seir-v1.1.0", "ml-v2.0.0", "hybrid-v1.5.0"])
    metadata_json = factory.LazyFunction(lambda: {
        "r0": fuzzy.FuzzyFloat(1.0, 5.0).fuzz(),
        "peak_day": fuzzy.FuzzyInteger(7, 30).fuzz(),
        "peak_cases": fuzzy.FuzzyInteger(1000, 50000).fuzz()
    })
    created_at = factory.LazyFunction(datetime.now)
    updated_at = factory.LazyFunction(datetime.now)


class RiskAssessmentFactory(factory.Factory):
    """Factory for creating RiskAssessment test instances."""
    
    class Meta:
        model = RiskAssessment
        sqlalchemy_session_persistence = 'commit'
    
    id = factory.LazyFunction(uuid.uuid4)
    location_id = factory.LazyFunction(uuid.uuid4)
    risk_level = factory.Iterator([RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL])
    risk_score = factory.LazyFunction(lambda: fuzzy.FuzzyFloat(0.0, 10.0).fuzz())
    factors_json = factory.LazyFunction(lambda: {
        "case_growth_rate": fuzzy.FuzzyFloat(0.0, 1.0).fuzz(),
        "population_density": fuzzy.FuzzyFloat(0.0, 1.0).fuzz(),
        "healthcare_capacity": fuzzy.FuzzyFloat(0.0, 1.0).fuzz(),
        "travel_restrictions": fuzzy.FuzzyInteger(0, 1).fuzz()
    })
    timestamp = factory.LazyFunction(datetime.now)
    created_at = factory.LazyFunction(datetime.now)
    updated_at = factory.LazyFunction(datetime.now)


class AlertFactory(factory.Factory):
    """Factory for creating Alert test instances."""
    
    class Meta:
        model = Alert
        sqlalchemy_session_persistence = 'commit'
    
    id = factory.LazyFunction(uuid.uuid4)
    location_id = factory.LazyFunction(uuid.uuid4)
    severity = factory.Iterator([AlertSeverity.INFO, AlertSeverity.WARNING, AlertSeverity.SEVERE, AlertSeverity.CRITICAL])
    message = factory.LazyFunction(lambda: f"Test alert: {fuzzy.FuzzyText(length=50).fuzz()}")
    status = factory.Iterator([AlertStatus.ACTIVE, AlertStatus.ACKNOWLEDGED, AlertStatus.RESOLVED, AlertStatus.DISMISSED])
    recipient_list = factory.LazyFunction(lambda: [
        f"user{i}@example.com" for i in range(fuzzy.FuzzyInteger(1, 5).fuzz())
    ])
    acknowledged_at = factory.LazyAttribute(lambda obj: datetime.now() if obj.status != AlertStatus.ACTIVE else None)
    created_at = factory.LazyFunction(datetime.now)
    updated_at = factory.LazyFunction(datetime.now)


class AgentExecutionFactory(factory.Factory):
    """Factory for creating AgentExecution test instances."""
    
    class Meta:
        model = AgentExecution
        sqlalchemy_session_persistence = 'commit'
    
    id = factory.LazyFunction(uuid.uuid4)
    agent_type = factory.Iterator([
        "epidemic_analyzer",
        "risk_calculator",
        "prediction_engine",
        "alert_generator"
    ])
    task_description = factory.LazyFunction(lambda: f"Test task: {fuzzy.FuzzyText(length=100).fuzz()}")
    status = factory.Iterator([
        AgentStatus.PENDING,
        AgentStatus.RUNNING,
        AgentStatus.COMPLETED,
        AgentStatus.FAILED,
        AgentStatus.CANCELLED
    ])
    result_json = factory.LazyAttribute(lambda obj: {
        "result": "success",
        "data": {"key": "value"}
    } if obj.status == AgentStatus.COMPLETED else None)
    started_at = factory.LazyFunction(datetime.now)
    completed_at = factory.LazyAttribute(lambda obj: datetime.now() if obj.status == AgentStatus.COMPLETED else None)
    execution_time_ms = factory.LazyAttribute(
        lambda obj: fuzzy.FuzzyInteger(100, 5000).fuzz() if obj.status == AgentStatus.COMPLETED else None
    )
    error_message = factory.LazyAttribute(
        lambda obj: f"Test error: {fuzzy.FuzzyText(length=50).fuzz()}" if obj.status == AgentStatus.FAILED else None
    )
    created_at = factory.LazyFunction(datetime.now)
    updated_at = factory.LazyFunction(datetime.now)


# Helper functions for creating test data
def create_location_with_events(
    session,
    name: str = "Test City",
    num_events: int = 5,
    **location_kwargs
) -> Location:
    """Create a location with multiple outbreak events."""
    location = LocationFactory.build(**location_kwargs)
    if name:
        location.name = name
    session.add(location)
    session.flush()
    
    for _ in range(num_events):
        event = OutbreakEventFactory.build(location_id=location.id)
        session.add(event)
    
    session.commit()
    session.refresh(location)
    return location


def create_prediction_chain(
    session,
    location_id: uuid.UUID,
    num_predictions: int = 3
) -> list[Prediction]:
    """Create a chain of predictions for a location."""
    predictions = []
    base_date = datetime.now()
    
    for i in range(num_predictions):
        prediction = PredictionFactory.build(
            location_id=location_id,
            prediction_date=base_date + timedelta(days=i * 7)
        )
        session.add(prediction)
        predictions.append(prediction)
    
    session.commit()
    return predictions


def create_alert_with_assessment(
    session,
    location_id: uuid.UUID,
    risk_level: RiskLevel = RiskLevel.HIGH,
    alert_severity: AlertSeverity = AlertSeverity.WARNING
) -> tuple[RiskAssessment, Alert]:
    """Create a risk assessment and corresponding alert."""
    assessment = RiskAssessmentFactory.build(
        location_id=location_id,
        risk_level=risk_level,
        risk_score=7.5 if risk_level == RiskLevel.HIGH else 3.0
    )
    session.add(assessment)
    session.flush()
    
    alert = AlertFactory.build(
        location_id=location_id,
        severity=alert_severity,
        status=AlertStatus.ACTIVE
    )
    session.add(alert)
    session.commit()
    
    return assessment, alert

