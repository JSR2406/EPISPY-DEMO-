"""Policy recommendation API endpoints."""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from ...database.connection import get_db
from ...database.models import PolicyType, EvidenceQuality
from ...policy_recommendation import (
    PolicyRecommendationEngine,
    RecommendationContext,
)
from ..schemas.policy_recommendation import (
    PolicyRecommendationRequest,
    SituationBasedRequest,
    PolicyRecommendationsResponse,
    PolicyRecommendationResponse,
    PolicySummaryResponse,
    LocationContextRequest,
    PolicyInfo,
    LocationInfo,
    PolicyOutcomeResponse,
    PolicyTypeEnum,
    EvidenceQualityEnum,
)
from ...utils.logger import api_logger

router = APIRouter(prefix="/policy-recommendations", tags=["Policy Recommendations"])


def _convert_policy_type(enum_val: PolicyTypeEnum) -> PolicyType:
    """Convert API enum to database enum."""
    return PolicyType[enum_val.value]


def _convert_evidence_quality(enum_val: EvidenceQualityEnum) -> EvidenceQuality:
    """Convert API enum to database enum."""
    return EvidenceQuality[enum_val.value]


@router.post("/recommend", response_model=PolicyRecommendationsResponse)
async def recommend_policies(
    request: PolicyRecommendationRequest,
    db: AsyncSession = Depends(get_db)
) -> PolicyRecommendationsResponse:
    """
    Get policy recommendations for a target location.
    
    Uses similarity matching to find locations with similar contexts and
    recommends policies that were effective in those locations.
    """
    try:
        api_logger.info(
            f"Policy recommendation request for location {request.target_location_id}"
        )
        
        # Convert request to recommendation context
        context = RecommendationContext(
            target_location_id=request.target_location_id,
            policy_types=[
                _convert_policy_type(pt) for pt in request.policy_types
            ] if request.policy_types else None,
            min_effectiveness=request.min_effectiveness,
            min_evidence_quality=_convert_evidence_quality(request.min_evidence_quality),
            max_recommendations=request.max_recommendations,
            include_ended_policies=request.include_ended_policies,
            time_window_days=request.time_window_days,
        )
        
        # Generate recommendations
        engine = PolicyRecommendationEngine(db)
        recommendations = await engine.recommend_policies(context)
        
        # Convert to response format
        response_recommendations = []
        for rec in recommendations:
            response_recommendations.append(
                PolicyRecommendationResponse(
                    policy=PolicyInfo(
                        id=str(rec.policy.id),
                        title=rec.policy.title,
                        description=rec.policy.description,
                        policy_type=PolicyTypeEnum[rec.policy.policy_type.value],
                        status=rec.policy.status.value,
                        start_date=rec.policy.start_date,
                        end_date=rec.policy.end_date,
                        source=rec.policy.source,
                        source_url=rec.policy.source_url,
                        implementation_details=rec.policy.implementation_details,
                    ),
                    similar_location=LocationInfo(
                        id=str(rec.similar_location.id),
                        name=rec.similar_location.name,
                        country=rec.similar_location.country,
                        region=rec.similar_location.region,
                    ),
                    similarity_score=rec.similarity_score,
                    effectiveness_score=rec.effectiveness_score,
                    evidence_quality_score=rec.evidence_quality_score,
                    overall_score=rec.overall_score,
                    confidence=rec.confidence,
                    outcome=PolicyOutcomeResponse(
                        effectiveness_score=rec.outcome.effectiveness_score,
                        case_reduction_percent=rec.outcome.case_reduction_percent,
                        death_reduction_percent=rec.outcome.death_reduction_percent,
                        r0_change=rec.outcome.r0_change,
                        economic_impact_score=rec.outcome.economic_impact_score,
                        social_impact_score=rec.outcome.social_impact_score,
                        evidence_quality=EvidenceQualityEnum[rec.outcome.evidence_quality.value],
                        measurement_period_start=rec.outcome.measurement_period_start,
                        measurement_period_end=rec.outcome.measurement_period_end,
                    ) if rec.outcome else None,
                    adaptation_notes=rec.adaptation_notes,
                )
            )
        
        return PolicyRecommendationsResponse(
            target_location_id=request.target_location_id,
            recommendations=response_recommendations,
            total_found=len(response_recommendations),
            generated_at=datetime.now(),
        )
        
    except ValueError as e:
        api_logger.error(f"Invalid request: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        api_logger.error(f"Error generating recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/recommend-by-situation", response_model=PolicyRecommendationsResponse)
async def recommend_by_situation(
    request: SituationBasedRequest,
    db: AsyncSession = Depends(get_db)
) -> PolicyRecommendationsResponse:
    """
    Get policy recommendations based on current epidemic situation.
    
    Adjusts recommendations based on case counts, growth rate, and
    healthcare system utilization.
    """
    try:
        api_logger.info(
            f"Situation-based recommendation for location {request.target_location_id}"
        )
        
        engine = PolicyRecommendationEngine(db)
        
        policy_types = [
            _convert_policy_type(pt) for pt in request.policy_types
        ] if request.policy_types else None
        
        recommendations = await engine.recommend_by_situation(
            target_location_id=request.target_location_id,
            current_cases=request.current_cases,
            case_growth_rate=request.case_growth_rate,
            healthcare_utilization=request.healthcare_utilization,
            policy_types=policy_types,
        )
        
        # Convert to response format (same as above)
        response_recommendations = []
        for rec in recommendations:
            response_recommendations.append(
                PolicyRecommendationResponse(
                    policy=PolicyInfo(
                        id=str(rec.policy.id),
                        title=rec.policy.title,
                        description=rec.policy.description,
                        policy_type=PolicyTypeEnum[rec.policy.policy_type.value],
                        status=rec.policy.status.value,
                        start_date=rec.policy.start_date,
                        end_date=rec.policy.end_date,
                        source=rec.policy.source,
                        source_url=rec.policy.source_url,
                        implementation_details=rec.policy.implementation_details,
                    ),
                    similar_location=LocationInfo(
                        id=str(rec.similar_location.id),
                        name=rec.similar_location.name,
                        country=rec.similar_location.country,
                        region=rec.similar_location.region,
                    ),
                    similarity_score=rec.similarity_score,
                    effectiveness_score=rec.effectiveness_score,
                    evidence_quality_score=rec.evidence_quality_score,
                    overall_score=rec.overall_score,
                    confidence=rec.confidence,
                    outcome=PolicyOutcomeResponse(
                        effectiveness_score=rec.outcome.effectiveness_score,
                        case_reduction_percent=rec.outcome.case_reduction_percent,
                        death_reduction_percent=rec.outcome.death_reduction_percent,
                        r0_change=rec.outcome.r0_change,
                        economic_impact_score=rec.outcome.economic_impact_score,
                        social_impact_score=rec.outcome.social_impact_score,
                        evidence_quality=EvidenceQualityEnum[rec.outcome.evidence_quality.value],
                        measurement_period_start=rec.outcome.measurement_period_start,
                        measurement_period_end=rec.outcome.measurement_period_end,
                    ) if rec.outcome else None,
                    adaptation_notes=rec.adaptation_notes,
                )
            )
        
        return PolicyRecommendationsResponse(
            target_location_id=request.target_location_id,
            recommendations=response_recommendations,
            total_found=len(response_recommendations),
            generated_at=datetime.now(),
        )
        
    except ValueError as e:
        api_logger.error(f"Invalid request: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        api_logger.error(f"Error generating recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/policy/{policy_id}/summary", response_model=PolicySummaryResponse)
async def get_policy_summary(
    policy_id: str,
    db: AsyncSession = Depends(get_db)
) -> PolicySummaryResponse:
    """
    Get comprehensive summary of a policy including outcomes and implementations.
    """
    try:
        engine = PolicyRecommendationEngine(db)
        summary = await engine.get_policy_summary(policy_id)
        
        if not summary:
            raise HTTPException(status_code=404, detail="Policy not found")
        
        return PolicySummaryResponse(
            policy=PolicyInfo(
                id=summary["policy"]["id"],
                title=summary["policy"]["title"],
                description=summary["policy"]["description"],
                policy_type=PolicyTypeEnum[summary["policy"]["type"]],
                status=summary["policy"]["status"],
                start_date=summary["policy"]["start_date"],
                end_date=summary["policy"]["end_date"],
                source=summary["policy"]["source"],
                source_url=summary["policy"]["source_url"],
            ),
            location=LocationInfo(
                id=summary["location"]["id"],
                name=summary["location"]["name"],
                country=summary["location"]["country"],
                region=summary["location"]["region"],
            ),
            outcome=PolicyOutcomeResponse(
                effectiveness_score=summary["outcome"]["effectiveness_score"],
                case_reduction_percent=summary["outcome"]["case_reduction_percent"],
                death_reduction_percent=summary["outcome"]["death_reduction_percent"],
                evidence_quality=EvidenceQualityEnum[summary["outcome"]["evidence_quality"]],
                measurement_period_start=summary["outcome"]["measurement_period_start"],
                measurement_period_end=summary["outcome"]["measurement_period_end"],
            ) if summary.get("outcome") else None,
            implementations=summary.get("implementations", []),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(f"Error fetching policy summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/location-context")
async def create_or_update_location_context(
    request: LocationContextRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Create or update location context for similarity matching.
    """
    try:
        from ...database.models import LocationContext
        from sqlalchemy import select
        
        # Check if context exists
        result = await db.execute(
            select(LocationContext).where(
                LocationContext.location_id == request.location_id
            )
        )
        context = result.scalar_one_or_none()
        
        # Prepare update data
        update_data = {
            "population_density": request.population_density,
            "gdp_per_capita": request.gdp_per_capita,
            "healthcare_capacity": request.healthcare_capacity,
            "urbanization_rate": request.urbanization_rate,
            "literacy_rate": request.literacy_rate,
            "internet_penetration": request.internet_penetration,
            "infrastructure_quality": request.infrastructure_quality,
            "governance_effectiveness": request.governance_effectiveness,
            "public_trust_score": request.public_trust_score,
            "climate_zone": request.climate_zone,
            "geography_type": request.geography_type,
            "cultural_factors": request.cultural_factors,
            "economic_structure": request.economic_structure,
            "context_json": request.context_json,
        }
        
        # Remove None values
        update_data = {k: v for k, v in update_data.items() if v is not None}
        
        if context:
            # Update existing
            for key, value in update_data.items():
                setattr(context, key, value)
            await db.commit()
            return {"message": "Location context updated", "location_id": request.location_id}
        else:
            # Create new
            context = LocationContext(
                location_id=UUID(request.location_id),
                **update_data
            )
            db.add(context)
            await db.commit()
            return {"message": "Location context created", "location_id": request.location_id}
            
    except Exception as e:
        await db.rollback()
        api_logger.error(f"Error updating location context: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

