"""
API routes for mental health surveillance module.

Provides endpoints for:
- Counseling session data ingestion
- Crisis hotline transcript processing
- Social media sentiment analysis
- School absenteeism tracking
- Hotspot detection and alerts
- Resource recommendations
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from ...utils.logger import api_logger
from ...utils.app_state import AppState, get_app_state
from ...database.connection import get_db
from ...database.models import Location
from ..middleware.auth import optional_auth
from ..schemas.mental_health import (
    CounselingSessionRequest,
    CounselingSessionResponse,
    CrisisHotlineTranscriptRequest,
    CrisisHotlineTranscriptResponse,
    SocialMediaSentimentRequest,
    SocialMediaSentimentResponse,
    SchoolAbsenteeismRequest,
    SchoolAbsenteeismResponse,
    MentalHealthHotspotResponse,
    HotspotAlertResponse,
    ResourceRecommendationResponse,
    ActionPlanResponse,
    MentalHealthResourceRequest
)

# Import mental health modules
from ...mental_health.models import (
    CounselingSession,
    CrisisHotlineTranscript,
    SocialMediaSentiment,
    SchoolAbsenteeism,
    MentalHealthHotspot,
    MentalHealthResource,
    MentalHealthIndicator,
    MentalHealthSeverity
)
from ...mental_health.anonymization import (
    anonymize_counseling_session,
    anonymize_hotline_transcript,
    anonymize_social_media_data,
    anonymize_school_absenteeism
)
from ...mental_health.signal_detection import (
    detect_mental_health_signals,
    analyze_sentiment,
    calculate_crisis_score,
    initialize_nlp_models
)
from ...mental_health.clustering import detect_hotspots
from ...mental_health.alert_system import (
    process_hotspots_for_alerts,
    MentalHealthAlertSystem
)
from ...mental_health.resource_recommender import ResourceRecommendationEngine

router = APIRouter()


# ============================================================================
# Counseling Session Endpoints
# ============================================================================

@router.post("/counseling-sessions", response_model=Dict[str, Any])
async def ingest_counseling_sessions(
    sessions: List[CounselingSessionRequest],
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    app_state: AppState = Depends(get_app_state),
    user: Optional[dict] = Depends(optional_auth)
) -> Dict[str, Any]:
    """
    Ingest counseling session data (anonymized).
    
    Accepts counseling session records and stores them after anonymization.
    """
    try:
        api_logger.info(f"Ingesting {len(sessions)} counseling sessions")
        
        anonymized_sessions = []
        errors = []
        
        for session_data in sessions:
            try:
                # Anonymize session data
                anonymized = anonymize_counseling_session(session_data.dict())
                
                # Create database record
                session_record = CounselingSession(
                    id=uuid.uuid4(),
                    location_id=uuid.UUID(session_data.location_id),
                    session_date=session_data.session_date,
                    age_group=anonymized.get("age_group"),
                    gender_group=anonymized.get("gender_group", "UNKNOWN"),
                    primary_indicator=anonymized.get("primary_indicator"),
                    severity=anonymized.get("severity"),
                    session_duration_minutes=anonymized.get("session_duration_minutes"),
                    intervention_type=anonymized.get("intervention_type"),
                    outcome_score=anonymized.get("outcome_score"),
                    is_crisis_session=anonymized.get("is_crisis_session", False),
                    anonymized_notes_summary=anonymized.get("anonymized_notes_summary"),
                    metadata_json=anonymized.get("metadata_json")
                )
                
                db.add(session_record)
                anonymized_sessions.append(str(session_record.id))
                
            except Exception as e:
                api_logger.error(f"Failed to process counseling session: {str(e)}")
                errors.append({"error": str(e), "data": session_data.dict()})
        
        await db.commit()
        
        # Process signals in background
        background_tasks.add_task(_process_session_signals, anonymized_sessions, app_state)
        
        return {
            "status": "success",
            "ingested_count": len(anonymized_sessions),
            "error_count": len(errors),
            "session_ids": anonymized_sessions,
            "errors": errors if errors else None
        }
        
    except Exception as e:
        api_logger.error(f"Failed to ingest counseling sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to ingest sessions: {str(e)}")


# ============================================================================
# Crisis Hotline Endpoints
# ============================================================================

@router.post("/crisis-hotline", response_model=CrisisHotlineTranscriptResponse)
async def process_hotline_transcript(
    transcript_data: CrisisHotlineTranscriptRequest,
    db: AsyncSession = Depends(get_db),
    app_state: AppState = Depends(get_app_state),
    user: Optional[dict] = Depends(optional_auth)
) -> CrisisHotlineTranscriptResponse:
    """
    Process crisis hotline transcript.
    
    Accepts transcript data, anonymizes it, and performs NLP analysis
    to detect mental health signals.
    """
    try:
        api_logger.info(f"Processing crisis hotline transcript for location {transcript_data.location_id}")
        
        # Anonymize transcript
        anonymized = anonymize_hotline_transcript(transcript_data.dict())
        
        # Detect mental health signals from transcript
        transcript_text = anonymized.get("transcript_anonymized", "") or transcript_data.transcript or ""
        signals = detect_mental_health_signals(transcript_text)
        
        # Calculate crisis score
        sentiment = analyze_sentiment(transcript_text) if transcript_text else {}
        crisis_score = calculate_crisis_score(signals, sentiment)
        
        # Extract primary indicators
        primary_indicators = [s.indicator_type for s in signals[:3]]  # Top 3
        if not primary_indicators:
            primary_indicators = ["OTHER"]
        
        # Create database record
        transcript_record = CrisisHotlineTranscript(
            id=uuid.uuid4(),
            location_id=uuid.UUID(transcript_data.location_id),
            call_date=transcript_data.call_date,
            call_duration_seconds=transcript_data.call_duration_seconds,
            age_group=anonymized.get("age_group"),
            primary_indicators=primary_indicators,
            crisis_score=crisis_score,
            language_patterns={s.language_patterns for s in signals} if signals else None,
            sentiment_scores=sentiment,
            keywords_detected=anonymized.get("keywords_detected"),
            intervention_provided=transcript_data.intervention_provided,
            follow_up_required=transcript_data.follow_up_required,
            anonymized_themes=anonymized.get("anonymized_themes"),
            metadata_json=anonymized.get("metadata_json")
        )
        
        db.add(transcript_record)
        await db.commit()
        await db.refresh(transcript_record)
        
        return CrisisHotlineTranscriptResponse(
            id=str(transcript_record.id),
            location_id=str(transcript_record.location_id),
            call_date=transcript_record.call_date,
            crisis_score=transcript_record.crisis_score,
            primary_indicators=transcript_record.primary_indicators,
            created_at=transcript_record.created_at
        )
        
    except Exception as e:
        api_logger.error(f"Failed to process hotline transcript: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process transcript: {str(e)}")


# ============================================================================
# Social Media Sentiment Endpoints
# ============================================================================

@router.post("/social-media-sentiment", response_model=SocialMediaSentimentResponse)
async def ingest_social_media_sentiment(
    sentiment_data: SocialMediaSentimentRequest,
    db: AsyncSession = Depends(get_db),
    user: Optional[dict] = Depends(optional_auth)
) -> SocialMediaSentimentResponse:
    """
    Ingest social media sentiment data (aggregated).
    
    Accepts social media sentiment data and stores aggregated results.
    """
    try:
        api_logger.info(f"Ingesting social media sentiment for location {sentiment_data.location_id}")
        
        # Anonymize and aggregate data
        anonymized = anonymize_social_media_data(sentiment_data.dict())
        
        # Create database record
        sentiment_record = SocialMediaSentiment(
            id=uuid.uuid4(),
            location_id=uuid.UUID(sentiment_data.location_id),
            date=sentiment_data.date,
            platform=anonymized.get("platform"),
            sentiment_score=anonymized.get("sentiment_score", sentiment_data.sentiment_score or 0.0),
            mental_health_keyword_frequency=anonymized.get("mental_health_keyword_frequency"),
            anxiety_mentions=anonymized.get("anxiety_mentions", 0),
            depression_mentions=anonymized.get("depression_mentions", 0),
            crisis_keywords=anonymized.get("crisis_keywords", 0),
            engagement_level=anonymized.get("engagement_level"),
            sample_size=anonymized.get("sample_size"),
            metadata_json=anonymized.get("metadata_json")
        )
        
        db.add(sentiment_record)
        await db.commit()
        await db.refresh(sentiment_record)
        
        return SocialMediaSentimentResponse(
            id=str(sentiment_record.id),
            location_id=str(sentiment_record.location_id),
            date=sentiment_record.date,
            sentiment_score=sentiment_record.sentiment_score,
            mental_health_keyword_frequency=sentiment_record.mental_health_keyword_frequency or 0.0,
            anxiety_mentions=sentiment_record.anxiety_mentions or 0,
            depression_mentions=sentiment_record.depression_mentions or 0,
            created_at=sentiment_record.created_at
        )
        
    except Exception as e:
        api_logger.error(f"Failed to ingest social media sentiment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to ingest sentiment: {str(e)}")


# ============================================================================
# School Absenteeism Endpoints
# ============================================================================

@router.post("/school-absenteeism", response_model=SchoolAbsenteeismResponse)
async def ingest_school_absenteeism(
    absenteeism_data: SchoolAbsenteeismRequest,
    db: AsyncSession = Depends(get_db),
    user: Optional[dict] = Depends(optional_auth)
) -> SchoolAbsenteeismResponse:
    """
    Ingest school absenteeism data.
    
    Tracks school absenteeism as a mental health indicator.
    """
    try:
        api_logger.info(f"Ingesting school absenteeism for location {absenteeism_data.location_id}")
        
        # Anonymize data
        anonymized = anonymize_school_absenteeism(absenteeism_data.dict())
        
        # Calculate rates
        absence_rate = (anonymized.get("absent_count", 0) / anonymized.get("total_enrollment", 1)) * 100
        
        # Create database record
        absenteeism_record = SchoolAbsenteeism(
            id=uuid.uuid4(),
            location_id=uuid.UUID(absenteeism_data.location_id),
            date=absenteeism_data.date,
            school_type=absenteeism_data.school_type,
            total_enrollment=anonymized.get("total_enrollment"),
            absent_count=anonymized.get("absent_count", 0),
            absence_rate=absence_rate,
            mental_health_related_absences=anonymized.get("mental_health_related_absences"),
            chronic_absenteeism_rate=anonymized.get("chronic_absenteeism_rate", 0.0),
            metadata_json=absenteeism_data.metadata
        )
        
        db.add(absenteeism_record)
        await db.commit()
        await db.refresh(absenteeism_record)
        
        return SchoolAbsenteeismResponse(
            id=str(absenteeism_record.id),
            location_id=str(absenteeism_record.location_id),
            date=absenteeism_record.date,
            absence_rate=absenteeism_record.absence_rate,
            chronic_absenteeism_rate=absenteeism_record.chronic_absenteeism_rate or 0.0,
            created_at=absenteeism_record.created_at
        )
        
    except Exception as e:
        api_logger.error(f"Failed to ingest school absenteeism: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to ingest absenteeism: {str(e)}")


# ============================================================================
# Hotspot Detection Endpoints
# ============================================================================

@router.post("/hotspots/detect", response_model=List[MentalHealthHotspotResponse])
async def detect_mental_health_hotspots(
    days_back: int = 7,
    min_samples: int = 5,
    eps_km: float = 10.0,
    db: AsyncSession = Depends(get_db),
    user: Optional[dict] = Depends(optional_auth)
) -> List[MentalHealthHotspotResponse]:
    """
    Detect mental health hotspots from recent data.
    
    Uses geospatial clustering to identify hotspots of mental health indicators.
    """
    try:
        api_logger.info(f"Detecting mental health hotspots (days_back={days_back})")
        
        # Get recent data points
        cutoff_date = datetime.now().replace(tzinfo=None) - timedelta(days=days_back)
        
        # Get counseling sessions
        sessions_result = await db.execute(
            select(CounselingSession).where(
                CounselingSession.session_date >= cutoff_date
            )
        )
        sessions = sessions_result.scalars().all()
        
        # Get hotline transcripts
        transcripts_result = await db.execute(
            select(CrisisHotlineTranscript).where(
                CrisisHotlineTranscript.call_date >= cutoff_date
            )
        )
        transcripts = transcripts_result.scalars().all()
        
        # Prepare data points for clustering
        data_points = []
        location_coords = {}
        
        # Add sessions
        for session in sessions:
            location_id_str = str(session.location_id)
            data_points.append({
                "location_id": location_id_str,
                "crisis_score": 5.0 if session.is_crisis_session else 3.0,
                "primary_indicators": [session.primary_indicator.value]
            })
            
            # Get location coordinates
            if location_id_str not in location_coords and session.location:
                location_coords[location_id_str] = (
                    session.location.latitude,
                    session.location.longitude
                )
        
        # Add transcripts
        for transcript in transcripts:
            location_id_str = str(transcript.location_id)
            data_points.append({
                "location_id": location_id_str,
                "crisis_score": transcript.crisis_score,
                "primary_indicators": transcript.primary_indicators or []
            })
            
            if location_id_str not in location_coords and transcript.location:
                location_coords[location_id_str] = (
                    transcript.location.latitude,
                    transcript.location.longitude
                )
        
        if len(data_points) < min_samples:
            return []
        
        # Detect hotspots
        hotspot_objects = detect_hotspots(
            data_points,
            location_coords,
            min_samples=min_samples,
            eps_km=eps_km
        )
        
        # Save hotspots to database
        saved_hotspots = []
        for hotspot_obj in hotspot_objects:
            # Check if hotspot already exists
            existing_result = await db.execute(
                select(MentalHealthHotspot).where(
                    MentalHealthHotspot.location_id == uuid.UUID(hotspot_obj.location_id),
                    MentalHealthHotspot.is_active == True
                )
            )
            existing = existing_result.scalar_one_or_none()
            
            if existing:
                # Update existing hotspot
                existing.hotspot_score = hotspot_obj.hotspot_score
                existing.severity = hotspot_obj.severity
                existing.primary_indicators = hotspot_obj.primary_indicators
                existing.updated_at = datetime.now()
                saved_hotspots.append(existing)
            else:
                # Create new hotspot
                hotspot_record = MentalHealthHotspot(
                    id=uuid.uuid4(),
                    location_id=uuid.UUID(hotspot_obj.location_id),
                    detected_date=datetime.now(),
                    hotspot_score=hotspot_obj.hotspot_score,
                    primary_indicators=hotspot_obj.primary_indicators,
                    contributing_factors=hotspot_obj.contributing_factors,
                    severity=hotspot_obj.severity,
                    affected_population_estimate=hotspot_obj.affected_population_estimate,
                    trend=hotspot_obj.trend,
                    is_active=True
                )
                db.add(hotspot_record)
                saved_hotspots.append(hotspot_record)
        
        await db.commit()
        
        # Refresh hotspots to get location data
        for hotspot in saved_hotspots:
            await db.refresh(hotspot)
        
        return [
            MentalHealthHotspotResponse(
                id=str(h.id),
                location_id=str(h.location_id),
                location_name=h.location.name if h.location else None,
                detected_date=h.detected_date,
                hotspot_score=h.hotspot_score,
                primary_indicators=h.primary_indicators,
                severity=h.severity.value,
                affected_population_estimate=h.affected_population_estimate or 0,
                trend=h.trend or "STABLE",
                is_active=h.is_active,
                created_at=h.created_at
            )
            for h in saved_hotspots
        ]
        
    except Exception as e:
        api_logger.error(f"Failed to detect hotspots: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to detect hotspots: {str(e)}")


# ============================================================================
# Alert Endpoints
# ============================================================================

@router.post("/hotspots/{hotspot_id}/alerts", response_model=HotspotAlertResponse)
async def generate_hotspot_alert(
    hotspot_id: str,
    db: AsyncSession = Depends(get_db),
    user: Optional[dict] = Depends(optional_auth)
) -> HotspotAlertResponse:
    """
    Generate alert for a detected hotspot.
    """
    try:
        # Get hotspot
        result = await db.execute(
            select(MentalHealthHotspot).where(MentalHealthHotspot.id == uuid.UUID(hotspot_id))
        )
        hotspot = result.scalar_one_or_none()
        
        if not hotspot:
            raise HTTPException(status_code=404, detail="Hotspot not found")
        
        # Generate alert
        alert_system = MentalHealthAlertSystem()
        alert = await alert_system.create_alert_from_hotspot(hotspot, db)
        
        if not alert:
            raise HTTPException(status_code=400, detail="Hotspot does not meet alert threshold")
        
        await db.commit()
        await db.refresh(alert)
        
        # Extract recommended actions from alert message
        recommended_actions = []
        if "Recommended Actions:" in alert.message:
            actions_section = alert.message.split("Recommended Actions:")[1]
            recommended_actions = [
                line.strip().lstrip("- ").lstrip("1. ").lstrip("2. ").lstrip("3. ").lstrip("4. ").lstrip("5. ")
                for line in actions_section.split("\n")
                if line.strip() and not line.strip().startswith("Location:")
            ]
        
        return HotspotAlertResponse(
            alert_id=str(alert.id),
            hotspot_id=str(hotspot.id),
            location_id=str(hotspot.location_id),
            location_name=hotspot.location.name if hotspot.location else "Unknown",
            severity=alert.severity.value,
            message=alert.message,
            recommended_actions=recommended_actions,
            created_at=alert.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(f"Failed to generate alert: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate alert: {str(e)}")


# ============================================================================
# Resource Endpoints
# ============================================================================

@router.post("/resources", response_model=Dict[str, Any])
async def create_mental_health_resource(
    resource_data: MentalHealthResourceRequest,
    db: AsyncSession = Depends(get_db),
    user: Optional[dict] = Depends(optional_auth)
) -> Dict[str, Any]:
    """
    Create a mental health resource record.
    """
    try:
        resource = MentalHealthResource(
            id=uuid.uuid4(),
            location_id=uuid.UUID(resource_data.location_id),
            resource_type=resource_data.resource_type,
            name=resource_data.name,
            contact_info=resource_data.contact_info,
            services_offered=resource_data.services_offered,
            capacity=resource_data.capacity,
            availability_status=resource_data.availability_status
        )
        
        db.add(resource)
        await db.commit()
        await db.refresh(resource)
        
        return {
            "status": "success",
            "resource_id": str(resource.id),
            "message": "Resource created successfully"
        }
        
    except Exception as e:
        api_logger.error(f"Failed to create resource: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create resource: {str(e)}")


@router.get("/hotspots/{hotspot_id}/resources", response_model=List[ResourceRecommendationResponse])
async def get_resource_recommendations(
    hotspot_id: str,
    max_recommendations: int = 5,
    db: AsyncSession = Depends(get_db),
    user: Optional[dict] = Depends(optional_auth)
) -> List[ResourceRecommendationResponse]:
    """
    Get resource recommendations for a hotspot.
    """
    try:
        # Get hotspot
        result = await db.execute(
            select(MentalHealthHotspot).where(MentalHealthHotspot.id == uuid.UUID(hotspot_id))
        )
        hotspot = result.scalar_one_or_none()
        
        if not hotspot:
            raise HTTPException(status_code=404, detail="Hotspot not found")
        
        # Get recommendations
        recommender = ResourceRecommendationEngine()
        recommendations = await recommender.recommend_resources_for_hotspot(
            hotspot,
            db,
            max_recommendations=max_recommendations
        )
        
        return [
            ResourceRecommendationResponse(
                resource_id=r.resource_id,
                resource_name=r.resource_name,
                resource_type=r.resource_type,
                relevance_score=r.relevance_score,
                distance_km=r.distance_km,
                availability_status=r.availability_status,
                services_match=r.services_match,
                recommended_actions=r.recommended_actions
            )
            for r in recommendations
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(f"Failed to get recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")


@router.get("/hotspots/{hotspot_id}/action-plan", response_model=ActionPlanResponse)
async def get_action_plan(
    hotspot_id: str,
    db: AsyncSession = Depends(get_db),
    user: Optional[dict] = Depends(optional_auth)
) -> ActionPlanResponse:
    """
    Get comprehensive action plan for a hotspot.
    """
    try:
        # Get hotspot
        result = await db.execute(
            select(MentalHealthHotspot).where(MentalHealthHotspot.id == uuid.UUID(hotspot_id))
        )
        hotspot = result.scalar_one_or_none()
        
        if not hotspot:
            raise HTTPException(status_code=404, detail="Hotspot not found")
        
        # Get action plan
        recommender = ResourceRecommendationEngine()
        action_plan = await recommender.recommend_action_plan(hotspot, db)
        
        return ActionPlanResponse(**action_plan)
        
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(f"Failed to get action plan: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get action plan: {str(e)}")


# ============================================================================
# Background Tasks
# ============================================================================

async def _process_session_signals(session_ids: List[str], app_state: AppState):
    """Background task to process session signals."""
    # This would process signals from sessions in background
    # and trigger hotspot detection if needed
    pass

