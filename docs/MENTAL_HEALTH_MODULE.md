# Mental Health Surveillance Module

## Overview

The Mental Health Surveillance Module for EpiSPY provides comprehensive mental health crisis detection during epidemics by analyzing anonymized healthcare data, counseling records, and digital biomarkers while maintaining strict privacy protections.

## Features

### 1. Data Sources
- **Counseling Session Data**: Aggregated, anonymized counseling session records
- **Crisis Hotline Transcripts**: NLP-processed anonymized hotline call data
- **Social Media Sentiment**: Aggregated social media sentiment analysis
- **School Absenteeism**: School attendance data as youth mental health indicator

### 2. Privacy-Preserving Anonymization
- HIPAA/GDPR compliant data anonymization
- No individual tracking or re-identification
- Aggregated data only
- Generalized location and demographics
- Text anonymization with keyword preservation

### 3. Signal Detection Algorithms
- **NLP-based Crisis Detection**: Detects mental health crisis language
- **Keyword-based Indicators**: Anxiety, depression, crisis keyword detection
- **Sentiment Analysis**: Negative sentiment pattern detection
- **Language Pattern Analysis**: Emotional intensity and self-focus patterns

### 4. Geospatial Clustering
- DBSCAN clustering for hotspot detection
- Identifies geographic clusters of mental health indicators
- Calculates hotspot severity scores
- Trend analysis (increasing/decreasing/stable)

### 5. Alert System
- Automated hotspot detection
- Alert generation for emerging mental health crises
- Integration with main epidemic monitoring system
- Severity-based alerting (MILD, MODERATE, SEVERE, CRITICAL)

### 6. Resource Recommendations
- Mental health resource database
- Location-based resource matching
- Resource availability tracking
- Integration with alert system

## Architecture

### Data Models

1. **CounselingSession**: Anonymized counseling session data
2. **CrisisHotlineTranscript**: NLP-processed hotline call data
3. **SocialMediaSentiment**: Aggregated social media sentiment
4. **SchoolAbsenteeism**: School attendance data
5. **MentalHealthHotspot**: Detected hotspots
6. **MentalHealthResource**: Available resources

### Key Modules

- `models.py`: Database models
- `anonymization.py`: Privacy-preserving anonymization strategies
- `signal_detection.py`: NLP-based signal detection algorithms
- `clustering.py`: Geospatial hotspot clustering

## Privacy Protection

### Anonymization Strategies

1. **Data Aggregation**: Only aggregated data is stored, never individual records
2. **PII Removal**: All personally identifiable information is removed
3. **Generalization**: Age → age groups, specific location → city/region
4. **Text Anonymization**: PII removed from text while preserving mental health keywords
5. **K-Anonymity**: Minimum sample sizes required before analysis

### Compliance

- HIPAA compliant
- GDPR compliant
- No individual tracking
- Audit logs for data access

## Usage Examples

### Anonymizing Counseling Session Data

```python
from src.mental_health.anonymization import anonymize_counseling_session

raw_session = {
    "patient_id": "12345",
    "name": "John Doe",
    "age": 28,
    "location": "123 Main St, City, State",
    "notes": "Patient reports feeling anxious and overwhelmed",
    "primary_indicator": "ANXIETY",
    "severity": "MODERATE"
}

anonymized = anonymize_counseling_session(raw_session)
# Returns anonymized data with no PII
```

### Detecting Mental Health Signals

```python
from src.mental_health.signal_detection import detect_mental_health_signals

text = "I'm feeling hopeless and can't cope anymore. Everything seems pointless."

signals = detect_mental_health_signals(text)
# Returns list of detected signals (crisis, depression, etc.)
```

### Detecting Hotspots

```python
from src.mental_health.clustering import detect_hotspots

data_points = [
    {"location_id": "loc1", "crisis_score": 8.5, "primary_indicators": ["CRISIS", "DEPRESSION"]},
    {"location_id": "loc2", "crisis_score": 7.2, "primary_indicators": ["ANXIETY"]},
    # ... more data points
]

location_coords = {
    "loc1": (19.0760, 72.8777),
    "loc2": (28.6139, 77.2090),
    # ... more locations
}

hotspots = detect_hotspots(data_points, location_coords)
# Returns list of detected hotspots
```

## Integration with Main System

The mental health module integrates with the main EpiSPY epidemic monitoring system:

1. **Shared Location Data**: Uses same Location model
2. **Unified Alert System**: Mental health alerts integrated with epidemic alerts
3. **Combined Risk Assessment**: Mental health indicators contribute to overall risk
4. **Shared API Routes**: Integrated API endpoints

## Next Steps

To complete the module:

1. ✅ Data models and schemas
2. ✅ Privacy-preserving anonymization
3. ✅ NLP signal detection algorithms
4. ✅ Geospatial clustering
5. ⏳ Social media sentiment analysis integration
6. ⏳ School absenteeism tracking implementation
7. ⏳ Alert system integration
8. ⏳ Resource recommendation engine
9. ⏳ API routes for mental health data ingestion
10. ⏳ Dashboard visualization for mental health hotspots

## Dependencies

- `transformers` (optional): For advanced NLP models
- `textblob` (optional): For sentiment analysis
- `scikit-learn` (optional): For DBSCAN clustering
- `numpy`: For numerical operations
- `sqlalchemy`: For database models

## Testing

Test suite covers:
- Anonymization validation
- Signal detection accuracy
- Clustering algorithms
- Privacy compliance checks

## License

Part of EpiSPY epidemic surveillance system.

