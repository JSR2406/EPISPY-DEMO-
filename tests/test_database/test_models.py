"""
Tests for SQLAlchemy database models.

This module tests:
- Model creation and initialization
- Model relationships
- Model constraints and validations
- Model serialization
- Model querying
"""
import pytest
from datetime import datetime, timedelta
import uuid
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

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
from tests.utils.factories import (
    LocationFactory,
    OutbreakEventFactory,
    PredictionFactory,
    RiskAssessmentFactory,
    AlertFactory,
    AgentExecutionFactory
)
from tests.utils.assertions import (
    assert_valid_location,
    assert_valid_outbreak_event,
    assert_valid_prediction,
    assert_valid_risk_assessment,
    assert_valid_alert
)


@pytest.mark.unit
@pytest.mark.database
class TestLocationModel:
    """Tests for Location model."""
    
    async def test_create_location(self, db_session):
        """Test creating a Location instance."""
        location = LocationFactory.build()
        db_session.add(location)
        await db_session.commit()
        
        assert location.id is not None
        assert_valid_location(location)
    
    async def test_location_relationships(self, db_session):
        """Test Location relationships with other models."""
        location = LocationFactory.build()
        db_session.add(location)
        await db_session.flush()
        
        # Create related records
        event = OutbreakEventFactory.build(location_id=location.id)
        prediction = PredictionFactory.build(location_id=location.id)
        assessment = RiskAssessmentFactory.build(location_id=location.id)
        alert = AlertFactory.build(location_id=location.id)
        
        db_session.add_all([event, prediction, assessment, alert])
        await db_session.commit()
        await db_session.refresh(location)
        
        # Check relationships
        assert len(location.outbreak_events) >= 1
        assert len(location.predictions) >= 1
        assert len(location.risk_assessments) >= 1
        assert len(location.alerts) >= 1
    
    async def test_location_coordinates_validation(self, db_session):
        """Test location coordinate validation."""
        # Valid coordinates
        location = LocationFactory.build(latitude=19.0760, longitude=72.8777)
        db_session.add(location)
        await db_session.commit()
        
        assert -90 <= location.latitude <= 90
        assert -180 <= location.longitude <= 180
    
    async def test_location_timestamps(self, db_session):
        """Test location timestamp fields."""
        location = LocationFactory.build()
        db_session.add(location)
        await db_session.commit()
        
        assert location.created_at is not None
        assert location.updated_at is not None
        assert isinstance(location.created_at, datetime)
        assert isinstance(location.updated_at, datetime)
    
    async def test_location_unique_constraints(self, db_session):
        """Test location unique constraints if any."""
        # Locations can have same name in different countries
        location1 = LocationFactory.build(name="Springfield", country="USA")
        location2 = LocationFactory.build(name="Springfield", country="Canada")
        
        db_session.add_all([location1, location2])
        await db_session.commit()
        
        assert location1.id != location2.id


@pytest.mark.unit
@pytest.mark.database
class TestOutbreakEventModel:
    """Tests for OutbreakEvent model."""
    
    async def test_create_outbreak_event(self, db_session, sample_location_model):
        """Test creating an OutbreakEvent instance."""
        event = OutbreakEventFactory.build(location_id=sample_location_model.id)
        db_session.add(event)
        await db_session.commit()
        
        assert event.id is not None
        assert_valid_outbreak_event(event)
    
    async def test_outbreak_event_relationship(self, db_session, sample_location_model):
        """Test OutbreakEvent relationship with Location."""
        event = OutbreakEventFactory.build(location_id=sample_location_model.id)
        db_session.add(event)
        await db_session.commit()
        await db_session.refresh(event)
        
        assert event.location is not None
        assert event.location.id == sample_location_model.id
    
    async def test_outbreak_event_cascade_delete(self, db_session, sample_location_model):
        """Test cascade delete when location is deleted."""
        event = OutbreakEventFactory.build(location_id=sample_location_model.id)
        db_session.add(event)
        await db_session.commit()
        
        event_id = event.id
        await db_session.delete(sample_location_model)
        await db_session.commit()
        
        # Event should be deleted
        deleted_event = await db_session.get(OutbreakEvent, event_id)
        assert deleted_event is None
    
    async def test_outbreak_event_data_consistency(self, db_session, sample_location_model):
        """Test outbreak event data consistency."""
        event = OutbreakEventFactory.build(
            location_id=sample_location_model.id,
            cases=1000,
            deaths=20,
            recovered=800,
            active_cases=180
        )
        
        db_session.add(event)
        await db_session.commit()
        
        # Verify consistency
        assert event.cases == event.deaths + event.recovered + event.active_cases
        assert event.deaths <= event.cases
        assert event.active_cases <= event.cases
    
    async def test_outbreak_event_severity_range(self, db_session, sample_location_model):
        """Test outbreak event severity is within valid range."""
        event = OutbreakEventFactory.build(
            location_id=sample_location_model.id,
            severity=5.5
        )
        
        db_session.add(event)
        await db_session.commit()
        
        assert 1.0 <= event.severity <= 10.0


@pytest.mark.unit
@pytest.mark.database
class TestPredictionModel:
    """Tests for Prediction model."""
    
    async def test_create_prediction(self, db_session, sample_location_model):
        """Test creating a Prediction instance."""
        prediction = PredictionFactory.build(location_id=sample_location_model.id)
        db_session.add(prediction)
        await db_session.commit()
        
        assert prediction.id is not None
        assert_valid_prediction(prediction)
    
    async def test_prediction_confidence_range(self, db_session, sample_location_model):
        """Test prediction confidence is within valid range."""
        prediction = PredictionFactory.build(
            location_id=sample_location_model.id,
            confidence=0.85
        )
        
        db_session.add(prediction)
        await db_session.commit()
        
        assert 0.0 <= prediction.confidence <= 1.0
    
    async def test_prediction_metadata_json(self, db_session, sample_location_model):
        """Test prediction metadata JSON field."""
        metadata = {
            "r0": 2.5,
            "peak_day": 14,
            "peak_cases": 5000,
            "growth_rate": 0.15
        }
        
        prediction = PredictionFactory.build(
            location_id=sample_location_model.id,
            metadata_json=metadata
        )
        
        db_session.add(prediction)
        await db_session.commit()
        await db_session.refresh(prediction)
        
        assert prediction.metadata_json == metadata
        assert "r0" in prediction.metadata_json
        assert "peak_day" in prediction.metadata_json
    
    async def test_prediction_future_date(self, db_session, sample_location_model):
        """Test prediction date is in the future."""
        prediction = PredictionFactory.build(
            location_id=sample_location_model.id,
            prediction_date=datetime.now() + timedelta(days=7)
        )
        
        db_session.add(prediction)
        await db_session.commit()
        
        assert prediction.prediction_date > datetime.now() - timedelta(days=1)


@pytest.mark.unit
@pytest.mark.database
class TestRiskAssessmentModel:
    """Tests for RiskAssessment model."""
    
    async def test_create_risk_assessment(self, db_session, sample_location_model):
        """Test creating a RiskAssessment instance."""
        assessment = RiskAssessmentFactory.build(location_id=sample_location_model.id)
        db_session.add(assessment)
        await db_session.commit()
        
        assert assessment.id is not None
        assert_valid_risk_assessment(assessment)
    
    async def test_risk_level_enum(self, db_session, sample_location_model):
        """Test risk level enum values."""
        for risk_level in RiskLevel:
            assessment = RiskAssessmentFactory.build(
                location_id=sample_location_model.id,
                risk_level=risk_level
            )
            db_session.add(assessment)
            
        await db_session.commit()
        
        # All assessments should be valid
        assessments = await db_session.execute(
            select(RiskAssessment).where(RiskAssessment.location_id == sample_location_model.id)
        )
        assert assessments.scalars().count() == len(RiskLevel)
    
    async def test_risk_score_range(self, db_session, sample_location_model):
        """Test risk score is within valid range."""
        assessment = RiskAssessmentFactory.build(
            location_id=sample_location_model.id,
            risk_score=7.5
        )
        
        db_session.add(assessment)
        await db_session.commit()
        
        assert 0.0 <= assessment.risk_score <= 10.0
    
    async def test_risk_factors_json(self, db_session, sample_location_model):
        """Test risk factors JSON field."""
        factors = {
            "case_growth_rate": 0.15,
            "population_density": 0.8,
            "healthcare_capacity": 0.6
        }
        
        assessment = RiskAssessmentFactory.build(
            location_id=sample_location_model.id,
            factors_json=factors
        )
        
        db_session.add(assessment)
        await db_session.commit()
        await db_session.refresh(assessment)
        
        assert assessment.factors_json == factors


@pytest.mark.unit
@pytest.mark.database
class TestAlertModel:
    """Tests for Alert model."""
    
    async def test_create_alert(self, db_session, sample_location_model):
        """Test creating an Alert instance."""
        alert = AlertFactory.build(location_id=sample_location_model.id)
        db_session.add(alert)
        await db_session.commit()
        
        assert alert.id is not None
        assert_valid_alert(alert)
    
    async def test_alert_severity_enum(self, db_session, sample_location_model):
        """Test alert severity enum values."""
        for severity in AlertSeverity:
            alert = AlertFactory.build(
                location_id=sample_location_model.id,
                severity=severity
            )
            db_session.add(alert)
            
        await db_session.commit()
        
        # All alerts should be valid
        alerts = await db_session.execute(
            select(Alert).where(Alert.location_id == sample_location_model.id)
        )
        assert alerts.scalars().count() == len(AlertSeverity)
    
    async def test_alert_status_enum(self, db_session, sample_location_model):
        """Test alert status enum values."""
        for status in AlertStatus:
            alert = AlertFactory.build(
                location_id=sample_location_model.id,
                status=status,
                acknowledged_at=datetime.now() if status != AlertStatus.ACTIVE else None
            )
            db_session.add(alert)
            
        await db_session.commit()
        
        # All alerts should be valid
        alerts = await db_session.execute(
            select(Alert).where(Alert.location_id == sample_location_model.id)
        )
        assert alerts.scalars().count() == len(AlertStatus)
    
    async def test_alert_recipient_list(self, db_session, sample_location_model):
        """Test alert recipient list JSON field."""
        recipients = ["admin@example.com", "health_dept@example.com", "user@example.com"]
        
        alert = AlertFactory.build(
            location_id=sample_location_model.id,
            recipient_list=recipients
        )
        
        db_session.add(alert)
        await db_session.commit()
        await db_session.refresh(alert)
        
        assert alert.recipient_list == recipients
        assert len(alert.recipient_list) == 3


@pytest.mark.unit
@pytest.mark.database
class TestAgentExecutionModel:
    """Tests for AgentExecution model."""
    
    async def test_create_agent_execution(self, db_session):
        """Test creating an AgentExecution instance."""
        execution = AgentExecutionFactory.build()
        db_session.add(execution)
        await db_session.commit()
        
        assert execution.id is not None
        assert execution.agent_type is not None
        assert execution.task_description is not None
        assert execution.status is not None
    
    async def test_agent_status_enum(self, db_session):
        """Test agent status enum values."""
        for status in AgentStatus:
            execution = AgentExecutionFactory.build(status=status)
            db_session.add(execution)
            
        await db_session.commit()
        
        # All executions should be valid
        executions = await db_session.execute(select(AgentExecution))
        assert executions.scalars().count() == len(AgentStatus)
    
    async def test_agent_execution_timing(self, db_session):
        """Test agent execution timing fields."""
        execution = AgentExecutionFactory.build(
            status=AgentStatus.COMPLETED,
            started_at=datetime.now() - timedelta(seconds=5),
            completed_at=datetime.now()
        )
        
        db_session.add(execution)
        await db_session.commit()
        
        assert execution.started_at is not None
        assert execution.completed_at is not None
        assert execution.completed_at > execution.started_at
        
        if execution.execution_time_ms:
            execution_time = (execution.completed_at - execution.started_at).total_seconds() * 1000
            assert abs(execution.execution_time_ms - execution_time) < 1000  # Within 1 second
    
    async def test_agent_execution_result_json(self, db_session):
        """Test agent execution result JSON field."""
        result = {
            "result": "success",
            "data": {"key": "value"},
            "metrics": {"execution_time": 1000, "memory_used": 500}
        }
        
        execution = AgentExecutionFactory.build(
            status=AgentStatus.COMPLETED,
            result_json=result
        )
        
        db_session.add(execution)
        await db_session.commit()
        await db_session.refresh(execution)
        
        assert execution.result_json == result


@pytest.mark.unit
@pytest.mark.database
class TestModelQueries:
    """Tests for model querying."""
    
    async def test_query_locations_by_country(self, db_session):
        """Test querying locations by country."""
        # Create test locations
        location1 = LocationFactory.build(country="USA")
        location2 = LocationFactory.build(country="USA")
        location3 = LocationFactory.build(country="India")
        
        db_session.add_all([location1, location2, location3])
        await db_session.commit()
        
        # Query USA locations
        usa_locations = await db_session.execute(
            select(Location).where(Location.country == "USA")
        )
        usa_locations = usa_locations.scalars().all()
        
        assert len(usa_locations) == 2
        assert all(loc.country == "USA" for loc in usa_locations)
    
    async def test_query_outbreak_events_by_date_range(self, db_session, sample_location_model):
        """Test querying outbreak events by date range."""
        # Create events with different timestamps
        event1 = OutbreakEventFactory.build(
            location_id=sample_location_model.id,
            timestamp=datetime.now() - timedelta(days=5)
        )
        event2 = OutbreakEventFactory.build(
            location_id=sample_location_model.id,
            timestamp=datetime.now() - timedelta(days=3)
        )
        event3 = OutbreakEventFactory.build(
            location_id=sample_location_model.id,
            timestamp=datetime.now() - timedelta(days=1)
        )
        
        db_session.add_all([event1, event2, event3])
        await db_session.commit()
        
        # Query events in last 4 days
        start_date = datetime.now() - timedelta(days=4)
        recent_events = await db_session.execute(
            select(OutbreakEvent).where(
                OutbreakEvent.timestamp >= start_date,
                OutbreakEvent.location_id == sample_location_model.id
            )
        )
        recent_events = recent_events.scalars().all()
        
        assert len(recent_events) == 2
        assert all(event.timestamp >= start_date for event in recent_events)
    
    async def test_query_high_risk_assessments(self, db_session, sample_location_model):
        """Test querying high risk assessments."""
        # Create assessments with different risk levels
        assessment1 = RiskAssessmentFactory.build(
            location_id=sample_location_model.id,
            risk_level=RiskLevel.LOW,
            risk_score=2.0
        )
        assessment2 = RiskAssessmentFactory.build(
            location_id=sample_location_model.id,
            risk_level=RiskLevel.HIGH,
            risk_score=7.5
        )
        assessment3 = RiskAssessmentFactory.build(
            location_id=sample_location_model.id,
            risk_level=RiskLevel.CRITICAL,
            risk_score=9.0
        )
        
        db_session.add_all([assessment1, assessment2, assessment3])
        await db_session.commit()
        
        # Query high risk assessments
        high_risk = await db_session.execute(
            select(RiskAssessment).where(
                RiskAssessment.risk_score >= 6.0,
                RiskAssessment.location_id == sample_location_model.id
            )
        )
        high_risk = high_risk.scalars().all()
        
        assert len(high_risk) == 2
        assert all(assessment.risk_score >= 6.0 for assessment in high_risk)

