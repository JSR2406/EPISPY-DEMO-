"""
Privacy-preserving anonymization strategies for mental health data.

This module provides specialized anonymization functions for mental health
data to ensure HIPAA/GDPR compliance and prevent re-identification while
maintaining data utility for surveillance purposes.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import hashlib
import re
import json
from collections import Counter

from ..utils.logger import api_logger


# Mental health keywords that should be preserved (anonymized)
MENTAL_HEALTH_KEYWORDS = {
    "anxiety", "depression", "stress", "crisis", "panic", "trauma",
    "suicide", "self-harm", "isolation", "loneliness", "fear", "worry",
    "overwhelmed", "hopeless", "helpless", "numb", "angry", "irritable"
}

# PII patterns to detect and remove/anonymize
PII_PATTERNS = {
    "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
    "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
    "name": r'\b(?:Mr|Mrs|Ms|Dr)\.?\s+[A-Z][a-z]+\s+[A-Z][a-z]+\b'
}


def anonymize_counseling_session(session_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Anonymize counseling session data.
    
    Removes all PII while preserving aggregated mental health indicators.
    
    Args:
        session_data: Raw counseling session data
        
    Returns:
        Anonymized session data
    """
    anonymized = {}
    
    # Hash session ID if present
    if "session_id" in session_data:
        session_id = str(session_data["session_id"])
        anonymized["session_id_hash"] = hashlib.sha256(session_id.encode()).hexdigest()[:16]
    
    # Remove all PII fields
    pii_fields = [
        "patient_id", "patient_name", "name", "first_name", "last_name",
        "email", "phone", "address", "zip_code", "ssn", "national_id",
        "insurance_number", "medical_record_number"
    ]
    
    for field in pii_fields:
        if field in session_data:
            del session_data[field]
    
    # Generalize age to age group
    if "age" in session_data:
        age = session_data.get("age")
        if isinstance(age, (int, float)):
            anonymized["age_group"] = _generalize_age(age)
        del session_data["age"]
    elif "age_group" in session_data:
        anonymized["age_group"] = session_data["age_group"]
    
    # Generalize gender (preserve only if necessary, otherwise use UNKNOWN)
    if "gender" in session_data:
        gender = str(session_data["gender"]).upper()
        # Only preserve if it's standard (M/F), otherwise anonymize
        if gender in ["M", "MALE", "F", "FEMALE"]:
            anonymized["gender_group"] = "M" if gender in ["M", "MALE"] else "F"
        else:
            anonymized["gender_group"] = "UNKNOWN"
        del session_data["gender"]
    elif "gender_group" in session_data:
        anonymized["gender_group"] = session_data["gender_group"]
    else:
        anonymized["gender_group"] = "UNKNOWN"
    
    # Generalize location (keep only city/region, not street address)
    if "location" in session_data:
        location = session_data["location"]
        # Extract only city/region level
        anonymized["location_generalized"] = _generalize_location(location)
        del session_data["location"]
    
    if "location_id" in session_data:
        anonymized["location_id"] = session_data["location_id"]
    
    # Preserve mental health indicators
    for field in ["primary_indicator", "severity", "session_date", "session_duration_minutes",
                  "intervention_type", "outcome_score", "is_crisis_session"]:
        if field in session_data:
            anonymized[field] = session_data[field]
    
    # Anonymize session notes
    if "notes" in session_data:
        anonymized["anonymized_notes_summary"] = _anonymize_text(
            session_data["notes"],
            preserve_keywords=MENTAL_HEALTH_KEYWORDS
        )
        del session_data["notes"]
    elif "anonymized_notes_summary" in session_data:
        anonymized["anonymized_notes_summary"] = session_data["anonymized_notes_summary"]
    
    # Preserve metadata (after sanitization)
    if "metadata" in session_data:
        anonymized["metadata_json"] = _sanitize_metadata(session_data["metadata"])
    
    return anonymized


def anonymize_hotline_transcript(transcript_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Anonymize crisis hotline call transcript.
    
    Removes all PII and anonymizes the transcript while preserving
    mental health indicators and language patterns.
    
    Args:
        transcript_data: Raw hotline transcript data
        
    Returns:
        Anonymized transcript data with NLP-extracted features
    """
    anonymized = {}
    
    # Hash call ID if present
    if "call_id" in transcript_data:
        call_id = str(transcript_data["call_id"])
        anonymized["call_id_hash"] = hashlib.sha256(call_id.encode()).hexdigest()[:16]
    
    # Remove PII
    pii_fields = [
        "caller_id", "caller_name", "name", "phone", "email", "address",
        "caller_location", "caller_address"
    ]
    
    for field in pii_fields:
        if field in transcript_data:
            del transcript_data[field]
    
    # Generalize age
    if "age" in transcript_data:
        age = transcript_data.get("age")
        if isinstance(age, (int, float)):
            anonymized["age_group"] = _generalize_age(age)
        del transcript_data["age"]
    elif "age_group" in transcript_data:
        anonymized["age_group"] = transcript_data["age_group"]
    
    # Generalize location
    if "location_id" in transcript_data:
        anonymized["location_id"] = transcript_data["location_id"]
    
    # Preserve call metadata
    for field in ["call_date", "call_duration_seconds", "intervention_provided",
                  "follow_up_required"]:
        if field in transcript_data:
            anonymized[field] = transcript_data[field]
    
    # Anonymize transcript text
    if "transcript" in transcript_data:
        transcript_text = transcript_data["transcript"]
        
        # Extract keywords (anonymized)
        anonymized["keywords_detected"] = _extract_anonymized_keywords(
            transcript_text,
            MENTAL_HEALTH_KEYWORDS
        )
        
        # Extract anonymized themes
        anonymized["anonymized_themes"] = _extract_themes(transcript_text)
        
        # Anonymize full transcript (remove PII)
        anonymized["transcript_anonymized"] = _anonymize_text(
            transcript_text,
            preserve_keywords=MENTAL_HEALTH_KEYWORDS
        )
        
        del transcript_data["transcript"]
    
    # NLP-extracted features (if already processed)
    for field in ["primary_indicators", "crisis_score", "language_patterns",
                  "sentiment_scores"]:
        if field in transcript_data:
            anonymized[field] = transcript_data[field]
    
    return anonymized


def anonymize_social_media_data(social_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Anonymize social media data for mental health monitoring.
    
    Aggregates social media posts and removes all individual identifiers.
    Only stores aggregated patterns, never individual posts.
    
    Args:
        social_data: Raw social media data
        
    Returns:
        Anonymized aggregated social media data
    """
    anonymized = {}
    
    # Remove all individual post identifiers
    if "posts" in social_data:
        posts = social_data["posts"]
        
        # Aggregate data from posts
        anonymized["sample_size"] = len(posts)
        
        # Calculate aggregated metrics
        sentiment_scores = [p.get("sentiment_score", 0) for p in posts if "sentiment_score" in p]
        if sentiment_scores:
            anonymized["sentiment_score"] = sum(sentiment_scores) / len(sentiment_scores)
        
        # Count mental health keywords (aggregated)
        all_keywords = []
        for post in posts:
            if "keywords" in post:
                all_keywords.extend(post["keywords"])
        
        keyword_counts = Counter(all_keywords)
        anonymized["mental_health_keyword_frequency"] = len(all_keywords) / len(posts) if posts else 0
        anonymized["anxiety_mentions"] = keyword_counts.get("anxiety", 0) + keyword_counts.get("panic", 0)
        anonymized["depression_mentions"] = keyword_counts.get("depression", 0) + keyword_counts.get("hopeless", 0)
        anonymized["crisis_keywords"] = sum(
            keyword_counts.get(kw, 0) for kw in ["crisis", "suicide", "self-harm", "emergency"]
        )
        
        del social_data["posts"]
    
    # Preserve location (generalized)
    if "location_id" in social_data:
        anonymized["location_id"] = social_data["location_id"]
    
    # Preserve metadata
    for field in ["date", "platform", "engagement_level"]:
        if field in social_data:
            anonymized[field] = social_data[field]
    
    return anonymized


def anonymize_school_absenteeism(absenteeism_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Anonymize school absenteeism data.
    
    Aggregates student data and removes all individual identifiers.
    
    Args:
        absenteeism_data: Raw school absenteeism data
        
    Returns:
        Anonymized aggregated absenteeism data
    """
    anonymized = {}
    
    # Remove student-level PII
    if "students" in absenteeism_data:
        students = absenteeism_data["students"]
        
        # Aggregate data
        anonymized["total_enrollment"] = len(students)
        anonymized["absent_count"] = sum(1 for s in students if s.get("absent", False))
        
        if anonymized["total_enrollment"] > 0:
            anonymized["absence_rate"] = (
                anonymized["absent_count"] / anonymized["total_enrollment"] * 100
            )
        else:
            anonymized["absence_rate"] = 0.0
        
        # Count mental health-related absences (if flag present)
        mh_related = sum(1 for s in students if s.get("mental_health_related", False))
        anonymized["mental_health_related_absences"] = mh_related
        
        # Calculate chronic absenteeism (>10% of days)
        chronic = sum(1 for s in students if s.get("absence_rate", 0) > 10)
        if anonymized["total_enrollment"] > 0:
            anonymized["chronic_absenteeism_rate"] = (chronic / anonymized["total_enrollment"]) * 100
        else:
            anonymized["chronic_absenteeism_rate"] = 0.0
        
        del absenteeism_data["students"]
    
    # Preserve aggregated fields
    for field in ["date", "location_id", "school_type"]:
        if field in absenteeism_data:
            anonymized[field] = absenteeism_data[field]
    
    return anonymized


def _generalize_age(age: int) -> str:
    """Generalize specific age to age group."""
    if age < 13:
        return "0-12"
    elif age < 18:
        return "13-17"
    elif age < 25:
        return "18-24"
    elif age < 35:
        return "25-34"
    elif age < 45:
        return "35-44"
    elif age < 55:
        return "45-54"
    elif age < 65:
        return "55-64"
    else:
        return "65+"


def _generalize_location(location: Any) -> str:
    """Generalize location to city/region level only."""
    if isinstance(location, str):
        # Remove street addresses, keep only city/region
        parts = location.split(",")
        # Return last 2 parts (usually city, state/region)
        return ",".join(parts[-2:]).strip() if len(parts) >= 2 else location
    return str(location)


def _anonymize_text(text: str, preserve_keywords: Optional[set] = None) -> str:
    """Anonymize text by removing PII while preserving keywords."""
    if not text:
        return ""
    
    anonymized = text
    
    # Remove PII patterns
    for pattern_name, pattern in PII_PATTERNS.items():
        anonymized = re.sub(pattern, f"[{pattern_name}_REDACTED]", anonymized)
    
    # Remove names (if not already removed)
    # This is a simple heuristic - in production, use NER
    anonymized = re.sub(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', '[NAME_REDACTED]', anonymized)
    
    return anonymized


def _extract_anonymized_keywords(text: str, keyword_set: set) -> List[str]:
    """Extract mental health keywords from text (anonymized)."""
    if not text:
        return []
    
    text_lower = text.lower()
    found_keywords = []
    
    for keyword in keyword_set:
        if keyword.lower() in text_lower:
            found_keywords.append(keyword)
    
    return list(set(found_keywords))  # Remove duplicates


def _extract_themes(text: str) -> str:
    """Extract anonymized thematic summary from text."""
    # This is a simplified version - in production, use NLP models
    # to extract themes without PII
    
    # Count mental health keywords
    text_lower = text.lower()
    theme_counts = {}
    
    for keyword in MENTAL_HEALTH_KEYWORDS:
        count = text_lower.count(keyword.lower())
        if count > 0:
            theme_counts[keyword] = count
    
    # Create thematic summary
    if theme_counts:
        top_themes = sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        themes = [theme for theme, _ in top_themes]
        return f"Themes detected: {', '.join(themes)}"
    
    return "General mental health discussion"


def _sanitize_metadata(metadata: Any) -> Dict[str, Any]:
    """Sanitize metadata to remove PII."""
    if not isinstance(metadata, dict):
        return {}
    
    sanitized = {}
    pii_keys = ["name", "email", "phone", "address", "id", "identifier"]
    
    for key, value in metadata.items():
        # Skip PII keys
        if any(pii_key in key.lower() for pii_key in pii_keys):
            continue
        
        # Recursively sanitize nested dicts
        if isinstance(value, dict):
            sanitized[key] = _sanitize_metadata(value)
        elif isinstance(value, list):
            sanitized[key] = [
                _sanitize_metadata(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            sanitized[key] = value
    
    return sanitized


def validate_anonymization(data: Dict[str, Any]) -> bool:
    """
    Validate that data is properly anonymized.
    
    Checks for common PII patterns and ensures anonymization compliance.
    
    Args:
        data: Data to validate
        
    Returns:
        True if data appears properly anonymized
    """
    data_str = json.dumps(data, default=str).lower()
    
    # Check for PII patterns
    for pattern_name, pattern in PII_PATTERNS.items():
        matches = re.findall(pattern, data_str, re.IGNORECASE)
        if matches:
            api_logger.warning(f"Potential PII detected: {pattern_name} - {len(matches)} matches")
            return False
    
    # Check for common name patterns
    name_pattern = r'\b[A-Z][a-z]+ [A-Z][a-z]+\b'
    if re.search(name_pattern, data_str):
        api_logger.warning("Potential name pattern detected")
        return False
    
    return True

