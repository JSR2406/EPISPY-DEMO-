"""Data normalization utilities."""
from typing import Dict, Any
from datetime import datetime
from ...utils.logger import data_logger


def normalize_patient_data(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize patient data to standard format.
    
    Args:
        record: Patient record dictionary
        
    Returns:
        Normalized record
    """
    normalized = record.copy()
    
    # Normalize date format
    if "visit_date" in normalized:
        if isinstance(normalized["visit_date"], str):
            try:
                normalized["visit_date"] = datetime.fromisoformat(normalized["visit_date"].replace("Z", "+00:00"))
            except:
                pass
    
    # Normalize symptoms to list
    if "symptoms" in normalized:
        if isinstance(normalized["symptoms"], str):
            normalized["symptoms"] = [s.strip() for s in normalized["symptoms"].split(",")]
        elif not isinstance(normalized["symptoms"], list):
            normalized["symptoms"] = []
    
    # Normalize severity score
    if "severity_score" in normalized:
        try:
            normalized["severity_score"] = float(normalized["severity_score"])
            # Clamp to valid range
            normalized["severity_score"] = max(1.0, min(10.0, normalized["severity_score"]))
        except (ValueError, TypeError):
            normalized["severity_score"] = 5.0  # Default
    
    # Normalize location (uppercase, trim)
    if "location" in normalized:
        normalized["location"] = str(normalized["location"]).strip().upper()
    
    # Normalize age group
    if "age_group" in normalized:
        normalized["age_group"] = str(normalized["age_group"]).strip()
    
    return normalized

