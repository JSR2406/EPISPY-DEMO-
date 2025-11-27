"""
Custom assertion helpers for EpiSPY tests.

This module provides custom assertion functions for common test scenarios
including database validation, API response validation, and data structure checks.
"""
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import json


def assert_valid_location(location: Any, required_fields: Optional[List[str]] = None):
    """
    Assert that a location object has valid structure and data.
    
    Args:
        location: Location model instance or dict
        required_fields: Optional list of required field names
        
    Raises:
        AssertionError: If location is invalid
    """
    if required_fields is None:
        required_fields = ["name", "latitude", "longitude", "country"]
    
    for field in required_fields:
        assert hasattr(location, field) or field in location, f"Location missing required field: {field}"
        assert getattr(location, field, location.get(field)) is not None, f"Location field {field} is None"
    
    # Validate coordinates
    lat = getattr(location, "latitude", location.get("latitude"))
    lon = getattr(location, "longitude", location.get("longitude"))
    assert -90 <= lat <= 90, f"Invalid latitude: {lat}"
    assert -180 <= lon <= 180, f"Invalid longitude: {lon}"


def assert_valid_outbreak_event(event: Any):
    """
    Assert that an outbreak event has valid structure and data.
    
    Args:
        event: OutbreakEvent model instance or dict
        
    Raises:
        AssertionError: If event is invalid
    """
    assert hasattr(event, "location_id") or "location_id" in event, "Event missing location_id"
    assert hasattr(event, "disease_type") or "disease_type" in event, "Event missing disease_type"
    assert hasattr(event, "cases") or "cases" in event, "Event missing cases"
    
    cases = getattr(event, "cases", event.get("cases", 0))
    deaths = getattr(event, "deaths", event.get("deaths", 0))
    recovered = getattr(event, "recovered", event.get("recovered", 0))
    active_cases = getattr(event, "active_cases", event.get("active_cases", 0))
    
    assert cases >= 0, f"Cases cannot be negative: {cases}"
    assert deaths >= 0, f"Deaths cannot be negative: {deaths}"
    assert recovered >= 0, f"Recovered cannot be negative: {recovered}"
    assert active_cases >= 0, f"Active cases cannot be negative: {active_cases}"
    assert deaths <= cases, f"Deaths ({deaths}) cannot exceed cases ({cases})"
    assert active_cases <= cases, f"Active cases ({active_cases}) cannot exceed cases ({cases})"
    
    severity = getattr(event, "severity", event.get("severity"))
    if severity is not None:
        assert 0 <= severity <= 10, f"Severity must be between 0 and 10: {severity}"


def assert_valid_prediction(prediction: Any):
    """
    Assert that a prediction has valid structure and data.
    
    Args:
        prediction: Prediction model instance or dict
        
    Raises:
        AssertionError: If prediction is invalid
    """
    assert hasattr(prediction, "location_id") or "location_id" in prediction, "Prediction missing location_id"
    assert hasattr(prediction, "predicted_cases") or "predicted_cases" in prediction, "Prediction missing predicted_cases"
    assert hasattr(prediction, "confidence") or "confidence" in prediction, "Prediction missing confidence"
    
    predicted_cases = getattr(prediction, "predicted_cases", prediction.get("predicted_cases", 0))
    confidence = getattr(prediction, "confidence", prediction.get("confidence", 0))
    
    assert predicted_cases >= 0, f"Predicted cases cannot be negative: {predicted_cases}"
    assert 0 <= confidence <= 1, f"Confidence must be between 0 and 1: {confidence}"
    
    prediction_date = getattr(prediction, "prediction_date", prediction.get("prediction_date"))
    if prediction_date:
        assert isinstance(prediction_date, datetime), f"Prediction date must be datetime, got {type(prediction_date)}"
        # Prediction date should be in the future (or very recent past)
        assert prediction_date >= datetime.now() - timedelta(days=1), \
            f"Prediction date should be recent or future: {prediction_date}"


def assert_valid_risk_assessment(assessment: Any):
    """
    Assert that a risk assessment has valid structure and data.
    
    Args:
        assessment: RiskAssessment model instance or dict
        
    Raises:
        AssertionError: If assessment is invalid
    """
    from src.database.models import RiskLevel
    
    assert hasattr(assessment, "location_id") or "location_id" in assessment, "Assessment missing location_id"
    assert hasattr(assessment, "risk_level") or "risk_level" in assessment, "Assessment missing risk_level"
    assert hasattr(assessment, "risk_score") or "risk_score" in assessment, "Assessment missing risk_score"
    
    risk_level = getattr(assessment, "risk_level", assessment.get("risk_level"))
    risk_score = getattr(assessment, "risk_score", assessment.get("risk_score", 0))
    
    assert risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL], \
        f"Invalid risk level: {risk_level}"
    assert 0 <= risk_score <= 10, f"Risk score must be between 0 and 10: {risk_score}"
    
    # Validate risk level matches risk score range
    level_ranges = {
        RiskLevel.LOW: (0, 3),
        RiskLevel.MEDIUM: (3, 6),
        RiskLevel.HIGH: (6, 8),
        RiskLevel.CRITICAL: (8, 10)
    }
    min_score, max_score = level_ranges.get(risk_level, (0, 10))
    assert min_score <= risk_score <= max_score, \
        f"Risk score {risk_score} does not match risk level {risk_level} (expected {min_score}-{max_score})"


def assert_valid_alert(alert: Any):
    """
    Assert that an alert has valid structure and data.
    
    Args:
        alert: Alert model instance or dict
        
    Raises:
        AssertionError: If alert is invalid
    """
    from src.database.models import AlertSeverity, AlertStatus
    
    assert hasattr(alert, "location_id") or "location_id" in alert, "Alert missing location_id"
    assert hasattr(alert, "severity") or "severity" in alert, "Alert missing severity"
    assert hasattr(alert, "message") or "message" in alert, "Alert missing message"
    assert hasattr(alert, "status") or "status" in alert, "Alert missing status"
    
    severity = getattr(alert, "severity", alert.get("severity"))
    status = getattr(alert, "status", alert.get("status"))
    message = getattr(alert, "message", alert.get("message"))
    
    assert severity in [AlertSeverity.INFO, AlertSeverity.WARNING, AlertSeverity.SEVERE, AlertSeverity.CRITICAL], \
        f"Invalid alert severity: {severity}"
    assert status in [AlertStatus.ACTIVE, AlertStatus.ACKNOWLEDGED, AlertStatus.RESOLVED, AlertStatus.DISMISSED], \
        f"Invalid alert status: {status}"
    assert message and len(message.strip()) > 0, "Alert message cannot be empty"


def assert_valid_api_response(response: Any, status_code: int = 200, required_fields: Optional[List[str]] = None):
    """
    Assert that an API response has valid structure.
    
    Args:
        response: HTTP response object or dict
        status_code: Expected status code
        required_fields: Optional list of required field names in response body
        
    Raises:
        AssertionError: If response is invalid
    """
    if hasattr(response, "status_code"):
        assert response.status_code == status_code, \
            f"Expected status code {status_code}, got {response.status_code}"
    
    if hasattr(response, "json"):
        if callable(response.json):
            data = response.json()
        else:
            data = response.json
    else:
        data = response
    
    assert isinstance(data, dict), f"Response body should be dict, got {type(data)}"
    
    if required_fields:
        for field in required_fields:
            assert field in data, f"Response missing required field: {field}"


def assert_datetime_recent(dt: datetime, max_seconds_ago: int = 60):
    """
    Assert that a datetime is recent (within max_seconds_ago seconds from now).
    
    Args:
        dt: Datetime to check
        max_seconds_ago: Maximum seconds ago the datetime can be
        
    Raises:
        AssertionError: If datetime is too old
    """
    assert isinstance(dt, datetime), f"Expected datetime, got {type(dt)}"
    time_diff = (datetime.now() - dt).total_seconds()
    assert time_diff >= 0, f"Datetime is in the future: {dt}"
    assert time_diff <= max_seconds_ago, \
        f"Datetime is too old: {dt} ({time_diff:.1f} seconds ago, max {max_seconds_ago})"


def assert_json_structure(data: Any, structure: Dict[str, type], path: str = ""):
    """
    Assert that data matches a given JSON structure.
    
    Args:
        data: Data to validate
        structure: Dictionary mapping keys to expected types
        path: Current path in structure (for error messages)
        
    Raises:
        AssertionError: If structure doesn't match
    """
    assert isinstance(data, dict), f"Expected dict at {path}, got {type(data)}"
    
    for key, expected_type in structure.items():
        current_path = f"{path}.{key}" if path else key
        assert key in data, f"Missing key at {current_path}"
        
        value = data[key]
        if isinstance(expected_type, dict):
            # Nested structure
            assert_json_structure(value, expected_type, current_path)
        elif isinstance(expected_type, type):
            # Type check
            assert isinstance(value, expected_type), \
                f"Expected {expected_type.__name__} at {current_path}, got {type(value).__name__}"
        else:
            # Allow tuple of types
            assert isinstance(value, expected_type), \
                f"Expected one of {expected_type} at {current_path}, got {type(value).__name__}"


def assert_error_response(response: Any, status_code: int, error_message: Optional[str] = None):
    """
    Assert that an error response has correct format.
    
    Args:
        response: HTTP response object or dict
        status_code: Expected error status code
        error_message: Optional expected error message
        
    Raises:
        AssertionError: If error response is invalid
    """
    assert_valid_api_response(response, status_code)
    
    if hasattr(response, "json"):
        data = response.json() if callable(response.json) else response.json
    else:
        data = response
    
    assert "error" in data or "detail" in data or "message" in data, \
        "Error response should contain 'error', 'detail', or 'message' field"
    
    if error_message:
        error_text = data.get("error") or data.get("detail") or data.get("message", "")
        assert error_message.lower() in error_text.lower(), \
            f"Expected error message containing '{error_message}', got '{error_text}'"


def assert_pagination(response: Any, page: int = 1, page_size: int = 10):
    """
    Assert that a paginated response has correct structure.
    
    Args:
        response: HTTP response object or dict
        page: Expected page number
        page_size: Expected page size
        
    Raises:
        AssertionError: If pagination structure is invalid
    """
    if hasattr(response, "json"):
        data = response.json() if callable(response.json) else response.json
    else:
        data = response
    
    assert "items" in data or "data" in data, "Paginated response should contain 'items' or 'data'"
    assert "total" in data or "count" in data, "Paginated response should contain 'total' or 'count'"
    assert "page" in data or "current_page" in data, "Paginated response should contain 'page' or 'current_page'"
    
    items = data.get("items") or data.get("data", [])
    assert isinstance(items, list), "Paginated items should be a list"
    assert len(items) <= page_size, f"Page size should not exceed {page_size}"

