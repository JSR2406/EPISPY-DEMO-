"""Data validation utilities."""
from typing import Dict, Any, List
from datetime import datetime
from ...utils.logger import data_logger


def validate_patient_data(record: Dict[str, Any]) -> bool:
    """
    Validate patient data record.
    
    Args:
        record: Patient record dictionary
        
    Returns:
        True if valid
        
    Raises:
        ValueError: If validation fails
    """
    required_fields = ["patient_id", "visit_date", "location", "symptoms", "severity_score"]
    
    # Check required fields
    for field in required_fields:
        if field not in record:
            raise ValueError(f"Missing required field: {field}")
    
    # Validate severity score
    severity = record.get("severity_score")
    if not isinstance(severity, (int, float)) or not (1 <= severity <= 10):
        raise ValueError("severity_score must be between 1 and 10")
    
    # Validate symptoms
    symptoms = record.get("symptoms", [])
    if not isinstance(symptoms, list) or len(symptoms) == 0:
        raise ValueError("symptoms must be a non-empty list")
    
    # Validate location
    location = record.get("location", "")
    if not location or not isinstance(location, str):
        raise ValueError("location must be a non-empty string")
    
    # Validate coordinates if provided
    if "latitude" in record and record["latitude"] is not None:
        lat = record["latitude"]
        if not isinstance(lat, (int, float)) or not (-90 <= lat <= 90):
            raise ValueError("latitude must be between -90 and 90")
    
    if "longitude" in record and record["longitude"] is not None:
        lon = record["longitude"]
        if not isinstance(lon, (int, float)) or not (-180 <= lon <= 180):
            raise ValueError("longitude must be between -180 and 180")
    
    return True


def validate_batch_data(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate a batch of patient records.
    
    Returns:
        Dictionary with validation results
    """
    results = {
        "total": len(records),
        "valid": 0,
        "invalid": 0,
        "errors": []
    }
    
    for i, record in enumerate(records):
        try:
            validate_patient_data(record)
            results["valid"] += 1
        except ValueError as e:
            results["invalid"] += 1
            results["errors"].append({
                "index": i,
                "patient_id": record.get("patient_id", "unknown"),
                "error": str(e)
            })
    
    return results

