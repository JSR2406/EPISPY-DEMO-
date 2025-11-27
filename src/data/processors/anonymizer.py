"""Data anonymization utilities."""
from typing import Dict, Any
import hashlib
from ...utils.logger import data_logger


def anonymize_patient_data(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Anonymize patient data by hashing identifiers.
    
    Args:
        record: Patient record dictionary
        
    Returns:
        Anonymized record
    """
    anonymized = record.copy()
    
    # Hash patient ID if it looks like a real identifier
    if "patient_id" in anonymized:
        patient_id = str(anonymized["patient_id"])
        # Only hash if it doesn't look like already hashed
        if len(patient_id) < 32 and not patient_id.startswith("hash_"):
            anonymized["patient_id"] = f"hash_{hashlib.sha256(patient_id.encode()).hexdigest()[:16]}"
    
    # Remove or generalize sensitive fields
    sensitive_fields = ["name", "email", "phone", "address", "ssn", "national_id"]
    for field in sensitive_fields:
        if field in anonymized:
            del anonymized[field]
    
    # Generalize age to age group if specific age is present
    if "age" in anonymized and "age_group" not in anonymized:
        age = anonymized.get("age")
        if isinstance(age, (int, float)):
            if age < 18:
                anonymized["age_group"] = "0-17"
            elif age < 30:
                anonymized["age_group"] = "18-29"
            elif age < 45:
                anonymized["age_group"] = "30-44"
            elif age < 60:
                anonymized["age_group"] = "45-59"
            else:
                anonymized["age_group"] = "60+"
            del anonymized["age"]
    
    return anonymized

