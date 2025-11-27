# Mental Health Surveillance API Documentation

## Overview

The Mental Health Surveillance API provides endpoints for monitoring mental health indicators during epidemics. All endpoints maintain strict privacy by processing only anonymized, aggregated data.

## Base URL

```
/api/v1/mental-health
```

## Authentication

Most endpoints support optional authentication. For sensitive operations, authentication may be required.

## Endpoints

### 1. Counseling Session Data Ingestion

**POST** `/counseling-sessions`

Ingest anonymized counseling session data.

**Request Body:**
```json
[
  {
    "location_id": "550e8400-e29b-41d4-a716-446655440000",
    "session_date": "2024-01-15T10:30:00Z",
    "age_group": "25-34",
    "gender_group": "F",
    "primary_indicator": "ANXIETY",
    "severity": "MODERATE",
    "session_duration_minutes": 60,
    "intervention_type": "Cognitive Behavioral Therapy",
    "outcome_score": 6.5,
    "is_crisis_session": false,
    "anonymized_notes_summary": "Client reported feeling anxious about work-related stress"
  }
]
```

**Response:**
```json
{
  "status": "success",
  "ingested_count": 1,
  "error_count": 0,
  "session_ids": ["session-uuid"],
  "errors": null
}
```

---

### 2. Crisis Hotline Transcript Processing

**POST** `/crisis-hotline`

Process and analyze crisis hotline transcript.

**Request Body:**
```json
{
  "location_id": "550e8400-e29b-41d4-a716-446655440000",
  "call_date": "2024-01-15T14:20:00Z",
  "call_duration_seconds": 1800,
  "age_group": "18-24",
  "transcript": "Caller reports feeling overwhelmed and hopeless...",
  "intervention_provided": "Crisis counseling and safety planning",
  "follow_up_required": true
}
```

**Response:**
```json
{
  "id": "transcript-uuid",
  "location_id": "550e8400-e29b-41d4-a716-446655440000",
  "call_date": "2024-01-15T14:20:00Z",
  "crisis_score": 7.5,
  "primary_indicators": ["CRISIS", "DEPRESSION"],
  "created_at": "2024-01-15T14:25:00Z"
}
```

---

### 3. Social Media Sentiment Ingestion

**POST** `/social-media-sentiment`

Ingest aggregated social media sentiment data.

**Request Body:**
```json
{
  "location_id": "550e8400-e29b-41d4-a716-446655440000",
  "date": "2024-01-15T00:00:00Z",
  "platform": "twitter",
  "posts": [
    {"sentiment_score": -0.7, "keywords": ["anxiety", "stress"]},
    {"sentiment_score": -0.5, "keywords": ["overwhelmed"]}
  ]
}
```

**Response:**
```json
{
  "id": "sentiment-uuid",
  "location_id": "550e8400-e29b-41d4-a716-446655440000",
  "date": "2024-01-15T00:00:00Z",
  "sentiment_score": -0.6,
  "mental_health_keyword_frequency": 0.8,
  "anxiety_mentions": 15,
  "depression_mentions": 8,
  "created_at": "2024-01-15T01:00:00Z"
}
```

---

### 4. School Absenteeism Tracking

**POST** `/school-absenteeism`

Ingest school absenteeism data as a mental health indicator.

**Request Body:**
```json
{
  "location_id": "550e8400-e29b-41d4-a716-446655440000",
  "date": "2024-01-15T00:00:00Z",
  "school_type": "HIGH",
  "total_enrollment": 500,
  "absent_count": 75,
  "mental_health_related_absences": 15
}
```

**Response:**
```json
{
  "id": "absenteeism-uuid",
  "location_id": "550e8400-e29b-41d4-a716-446655440000",
  "date": "2024-01-15T00:00:00Z",
  "absence_rate": 15.0,
  "chronic_absenteeism_rate": 8.5,
  "created_at": "2024-01-15T01:00:00Z"
}
```

---

### 5. Hotspot Detection

**POST** `/hotspots/detect`

Detect mental health hotspots from recent data using geospatial clustering.

**Query Parameters:**
- `days_back` (int, default: 7): Number of days to look back
- `min_samples` (int, default: 5): Minimum samples for cluster
- `eps_km` (float, default: 10.0): Maximum distance in km for cluster

**Response:**
```json
[
  {
    "id": "hotspot-uuid",
    "location_id": "550e8400-e29b-41d4-a716-446655440000",
    "location_name": "Mumbai",
    "detected_date": "2024-01-15T10:00:00Z",
    "hotspot_score": 7.5,
    "primary_indicators": ["CRISIS", "DEPRESSION", "ANXIETY"],
    "severity": "SEVERE",
    "affected_population_estimate": 5000,
    "trend": "INCREASING",
    "is_active": true,
    "created_at": "2024-01-15T10:00:00Z"
  }
]
```

---

### 6. Generate Hotspot Alert

**POST** `/hotspots/{hotspot_id}/alerts`

Generate alert for a detected hotspot.

**Response:**
```json
{
  "alert_id": "alert-uuid",
  "hotspot_id": "hotspot-uuid",
  "location_id": "550e8400-e29b-41d4-a716-446655440000",
  "location_name": "Mumbai",
  "severity": "SEVERE",
  "message": "⚠️ SEVERE Mental Health Hotspot Detected...",
  "recommended_actions": [
    "Increase mental health resource availability",
    "Coordinate with local healthcare providers",
    "Activate crisis response team"
  ],
  "created_at": "2024-01-15T10:05:00Z"
}
```

---

### 7. Resource Recommendations

**GET** `/hotspots/{hotspot_id}/resources`

Get resource recommendations for a hotspot.

**Query Parameters:**
- `max_recommendations` (int, default: 5): Maximum recommendations

**Response:**
```json
[
  {
    "resource_id": "resource-uuid",
    "resource_name": "City Crisis Hotline",
    "resource_type": "crisis_hotline",
    "relevance_score": 0.9,
    "distance_km": 0.0,
    "availability_status": "AVAILABLE",
    "services_match": ["CRISIS", "crisis_support"],
    "recommended_actions": [
      "Promote City Crisis Hotline in affected area",
      "Distribute hotline number through public health channels"
    ]
  }
]
```

---

### 8. Action Plan

**GET** `/hotspots/{hotspot_id}/action-plan`

Get comprehensive action plan for a hotspot.

**Response:**
```json
{
  "hotspot_id": "hotspot-uuid",
  "location_id": "550e8400-e29b-41d4-a716-446655440000",
  "hotspot_score": 7.5,
  "severity": "SEVERE",
  "immediate_actions": [
    "Activate crisis response team immediately",
    "Deploy mobile mental health units"
  ],
  "resource_recommendations": [...],
  "national_resources": [
    {
      "name": "National Suicide Prevention Lifeline",
      "type": "crisis_hotline",
      "contact": "988"
    }
  ],
  "monitoring_actions": [
    "Monitor hotspot trend daily",
    "Track resource utilization"
  ],
  "prevention_actions": [
    "Provide mental health education resources",
    "Promote community support programs"
  ]
}
```

---

### 9. Create Resource

**POST** `/resources`

Create a mental health resource record.

**Request Body:**
```json
{
  "location_id": "550e8400-e29b-41d4-a716-446655440000",
  "resource_type": "crisis_hotline",
  "name": "City Crisis Hotline",
  "contact_info": {
    "phone": "1-800-XXX-XXXX",
    "email": "crisis@example.com"
  },
  "services_offered": [
    "Crisis support",
    "Suicide prevention",
    "Mental health referrals"
  ],
  "capacity": 100,
  "availability_status": "AVAILABLE"
}
```

**Response:**
```json
{
  "status": "success",
  "resource_id": "resource-uuid",
  "message": "Resource created successfully"
}
```

---

## Privacy Protection

All endpoints implement strict privacy protections:

1. **No PII Storage**: Personal identifiers are removed or hashed
2. **Aggregation Only**: Individual records are never stored
3. **Location Generalization**: Only city/region level location data
4. **Age Generalization**: Age groups only, never specific ages
5. **Text Anonymization**: Transcripts are anonymized before storage

## Error Responses

All endpoints return standard error responses:

```json
{
  "detail": "Error message here"
}
```

**Status Codes:**
- `200`: Success
- `400`: Bad Request
- `401`: Unauthorized
- `404`: Not Found
- `500`: Internal Server Error

## Rate Limiting

API endpoints are subject to rate limiting:
- Per IP: 60 requests/minute
- Per API Key: 1000 requests/hour

## Examples

### Python Example

```python
import requests
from datetime import datetime

# Ingest counseling session
session_data = {
    "location_id": "550e8400-e29b-41d4-a716-446655440000",
    "session_date": datetime.now().isoformat(),
    "primary_indicator": "ANXIETY",
    "severity": "MODERATE",
    "is_crisis_session": False
}

response = requests.post(
    "http://localhost:8000/api/v1/mental-health/counseling-sessions",
    json=[session_data]
)
print(response.json())

# Detect hotspots
response = requests.post(
    "http://localhost:8000/api/v1/mental-health/hotspots/detect",
    params={"days_back": 7, "min_samples": 5}
)
hotspots = response.json()
print(f"Detected {len(hotspots)} hotspots")

# Get action plan for hotspot
if hotspots:
    hotspot_id = hotspots[0]["id"]
    response = requests.get(
        f"http://localhost:8000/api/v1/mental-health/hotspots/{hotspot_id}/action-plan"
    )
    action_plan = response.json()
    print(action_plan)
```

### cURL Examples

```bash
# Ingest counseling session
curl -X POST "http://localhost:8000/api/v1/mental-health/counseling-sessions" \
  -H "Content-Type: application/json" \
  -d '[{
    "location_id": "550e8400-e29b-41d4-a716-446655440000",
    "session_date": "2024-01-15T10:30:00Z",
    "primary_indicator": "ANXIETY",
    "severity": "MODERATE"
  }]'

# Detect hotspots
curl -X POST "http://localhost:8000/api/v1/mental-health/hotspots/detect?days_back=7"

# Get resource recommendations
curl "http://localhost:8000/api/v1/mental-health/hotspots/{hotspot_id}/resources"
```

## Integration with Main System

The mental health module integrates with the main EpiSPY epidemic monitoring system:

1. **Shared Location Data**: Uses same Location model
2. **Unified Alert System**: Mental health alerts integrated with epidemic alerts
3. **Combined Risk Assessment**: Mental health indicators contribute to overall risk
4. **Shared API Base**: All endpoints under `/api/v1/`

## Next Steps

1. Set up NLP models (optional - transformers library)
2. Configure location coordinates
3. Populate resource database
4. Set up scheduled hotspot detection
5. Configure alert recipients

