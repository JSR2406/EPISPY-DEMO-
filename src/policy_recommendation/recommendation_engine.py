"""
Policy recommendation engine with collaborative filtering.

This module implements a recommendation system that suggests policies based on:
- Similarity matching between locations
- Policy effectiveness in similar contexts
- Evidence quality scoring
- Collaborative filtering (policies that worked in similar situations)
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from ..database.models import (
    Location, LocationContext, Policy, PolicyOutcome, PolicyType,
    EvidenceQuality, PolicyStatus
)
from .similarity_matcher import SimilarityMatcher, SimilarityWeights
from .evidence_scorer import EvidenceQualityScorer
from ..utils.logger import api_logger


@dataclass
class PolicyRecommendation:
    """Policy recommendation with scoring and context."""
    policy: Policy
    similarity_score: float
    effectiveness_score: float
    evidence_quality_score: float
    overall_score: float
    similar_location: Location
    outcome: Optional[PolicyOutcome]
    adaptation_notes: Optional[str] = None
    confidence: float = 0.0


@dataclass
class RecommendationContext:
    """Context for generating recommendations."""
    target_location_id: str
    policy_types: Optional[List[PolicyType]] = None
    min_effectiveness: float = 0.0
    min_evidence_quality: EvidenceQuality = EvidenceQuality.MODERATE
    max_recommendations: int = 10
    include_ended_policies: bool = True
    time_window_days: Optional[int] = None  # Only consider policies within time window


class PolicyRecommendationEngine:
    """
    Policy recommendation engine using collaborative filtering.
    
    Recommends policies based on:
    1. Similarity matching between locations
    2. Policy effectiveness in similar contexts
    3. Evidence quality
    4. Temporal relevance
    
    Example:
        engine = PolicyRecommendationEngine(session)
        recommendations = await engine.recommend_policies(
            target_location_id=location_id,
            policy_types=[PolicyType.LOCKDOWN, PolicyType.TESTING_STRATEGY]
        )
    """
    
    def __init__(
        self,
        session: AsyncSession,
        similarity_weights: Optional[SimilarityWeights] = None
    ):
        """
        Initialize recommendation engine.
        
        Args:
            session: Database session
            similarity_weights: Custom weights for similarity matching
        """
        self.session = session
        self.similarity_matcher = SimilarityMatcher(session, similarity_weights)
        self.evidence_scorer = EvidenceQualityScorer()
    
    async def recommend_policies(
        self,
        context: RecommendationContext
    ) -> List[PolicyRecommendation]:
        """
        Generate policy recommendations for target location.
        
        Args:
            context: Recommendation context
            
        Returns:
            List of policy recommendations sorted by overall score
        """
        api_logger.info(
            f"Generating policy recommendations for location {context.target_location_id}"
        )
        
        # Find similar locations
        similar_locations = await self.similarity_matcher.find_similar_locations(
            target_location_id=context.target_location_id,
            top_k=20,  # Get more candidates for better recommendations
            min_similarity=0.5
        )
        
        if not similar_locations:
            api_logger.warning("No similar locations found for recommendations")
            return []
        
        # Extract location IDs
        similar_location_ids = [str(loc.id) for loc, _ in similar_locations]
        similarity_scores = {str(loc.id): score for loc, score in similar_locations}
        
        # Build query for policies in similar locations
        query = (
            select(Policy)
            .where(Policy.location_id.in_(similar_location_ids))
            .options(
                selectinload(Policy.location),
                selectinload(Policy.outcomes),
                selectinload(Policy.implementations)
            )
        )
        
        # Filter by policy types if specified
        if context.policy_types:
            query = query.where(Policy.policy_type.in_(context.policy_types))
        
        # Filter by status
        if not context.include_ended_policies:
            query = query.where(
                or_(
                    Policy.status == PolicyStatus.ACTIVE,
                    Policy.status == PolicyStatus.MODIFIED
                )
            )
        
        # Filter by time window if specified
        if context.time_window_days:
            cutoff_date = datetime.now() - timedelta(days=context.time_window_days)
            query = query.where(Policy.start_date >= cutoff_date)
        
        # Execute query
        result = await self.session.execute(query)
        policies = result.scalars().all()
        
        # Generate recommendations
        recommendations = []
        for policy in policies:
            location_id = str(policy.location_id)
            similarity_score = similarity_scores.get(location_id, 0.0)
            
            # Get best outcome for this policy
            best_outcome = await self._get_best_outcome(policy.id)
            
            if best_outcome:
                # Check minimum thresholds
                if (best_outcome.effectiveness_score < context.min_effectiveness or
                    best_outcome.evidence_quality.value < context.min_evidence_quality.value):
                    continue
                
                # Compute scores
                effectiveness_score = best_outcome.effectiveness_score / 10.0  # Normalize to [0, 1]
                evidence_quality_score = self.evidence_scorer.score_quality(
                    best_outcome.evidence_quality
                )
                
                # Compute overall score (weighted combination)
                overall_score = (
                    0.4 * similarity_score +
                    0.4 * effectiveness_score +
                    0.2 * evidence_quality_score
                )
                
                # Generate adaptation notes
                adaptation_notes = await self._generate_adaptation_notes(
                    policy, context.target_location_id
                )
                
                recommendation = PolicyRecommendation(
                    policy=policy,
                    similarity_score=similarity_score,
                    effectiveness_score=effectiveness_score,
                    evidence_quality_score=evidence_quality_score,
                    overall_score=overall_score,
                    similar_location=policy.location,
                    outcome=best_outcome,
                    adaptation_notes=adaptation_notes,
                    confidence=self._compute_confidence(
                        similarity_score, effectiveness_score, evidence_quality_score
                    )
                )
                
                recommendations.append(recommendation)
        
        # Sort by overall score
        recommendations.sort(key=lambda r: r.overall_score, reverse=True)
        
        # Return top recommendations
        return recommendations[:context.max_recommendations]
    
    async def _get_best_outcome(
        self,
        policy_id: str
    ) -> Optional[PolicyOutcome]:
        """
        Get the best outcome for a policy (highest evidence quality, then effectiveness).
        
        Args:
            policy_id: Policy UUID
            
        Returns:
            Best PolicyOutcome or None
        """
        result = await self.session.execute(
            select(PolicyOutcome)
            .where(PolicyOutcome.policy_id == policy_id)
            .order_by(
                PolicyOutcome.evidence_quality.desc(),
                PolicyOutcome.effectiveness_score.desc()
            )
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    async def _generate_adaptation_notes(
        self,
        policy: Policy,
        target_location_id: str
    ) -> Optional[str]:
        """
        Generate adaptation notes for policy implementation in target location.
        
        Args:
            policy: Policy to adapt
            target_location_id: Target location UUID
            
        Returns:
            Adaptation notes string
        """
        # Get target location context
        result = await self.session.execute(
            select(LocationContext)
            .where(LocationContext.location_id == target_location_id)
        )
        target_context = result.scalar_one_or_none()
        
        # Get source location context
        result = await self.session.execute(
            select(LocationContext)
            .where(LocationContext.location_id == str(policy.location_id))
        )
        source_context = result.scalar_one_or_none()
        
        if not target_context or not source_context:
            return None
        
        notes = []
        
        # Compare key factors
        if (target_context.healthcare_capacity and source_context.healthcare_capacity and
            target_context.healthcare_capacity < source_context.healthcare_capacity * 0.7):
            notes.append(
                "Consider reduced healthcare capacity - may need additional support"
            )
        
        if (target_context.gdp_per_capita and source_context.gdp_per_capita and
            target_context.gdp_per_capita < source_context.gdp_per_capita * 0.5):
            notes.append(
                "Lower economic resources - consider cost-effective adaptations"
            )
        
        if (target_context.population_density and source_context.population_density and
            target_context.population_density > source_context.population_density * 1.5):
            notes.append(
                "Higher population density - may require stricter enforcement"
            )
        
        if (target_context.governance_effectiveness and source_context.governance_effectiveness and
            target_context.governance_effectiveness < source_context.governance_effectiveness * 0.8):
            notes.append(
                "Consider governance capacity - may need simplified implementation"
            )
        
        return "; ".join(notes) if notes else None
    
    def _compute_confidence(
        self,
        similarity_score: float,
        effectiveness_score: float,
        evidence_quality_score: float
    ) -> float:
        """
        Compute confidence score for recommendation.
        
        Args:
            similarity_score: Location similarity (0-1)
            effectiveness_score: Policy effectiveness (0-1)
            evidence_quality_score: Evidence quality (0-1)
            
        Returns:
            Confidence score (0-1)
        """
        # Confidence increases with all three factors
        # Weight evidence quality more heavily
        confidence = (
            0.3 * similarity_score +
            0.3 * effectiveness_score +
            0.4 * evidence_quality_score
        )
        
        # Penalize if any factor is very low
        if min(similarity_score, effectiveness_score, evidence_quality_score) < 0.3:
            confidence *= 0.7
        
        return float(min(1.0, max(0.0, confidence)))
    
    async def recommend_by_situation(
        self,
        target_location_id: str,
        current_cases: int,
        case_growth_rate: float,
        healthcare_utilization: float,
        policy_types: Optional[List[PolicyType]] = None
    ) -> List[PolicyRecommendation]:
        """
        Recommend policies based on current epidemic situation.
        
        Args:
            target_location_id: Target location UUID
            current_cases: Current number of cases
            case_growth_rate: Case growth rate (e.g., 0.15 for 15% daily growth)
            healthcare_utilization: Healthcare system utilization (0-1)
            policy_types: Optional filter by policy types
            
        Returns:
            List of policy recommendations
        """
        # Adjust recommendation context based on situation severity
        if case_growth_rate > 0.2 or healthcare_utilization > 0.8:
            # Critical situation - prioritize high-impact policies
            context = RecommendationContext(
                target_location_id=target_location_id,
                policy_types=policy_types or [
                    PolicyType.LOCKDOWN,
                    PolicyType.TESTING_STRATEGY,
                    PolicyType.QUARANTINE
                ],
                min_effectiveness=6.0,
                min_evidence_quality=EvidenceQuality.MODERATE,
                max_recommendations=5,
                time_window_days=180  # Recent policies only
            )
        elif case_growth_rate > 0.1 or healthcare_utilization > 0.6:
            # Moderate situation
            context = RecommendationContext(
                target_location_id=target_location_id,
                policy_types=policy_types,
                min_effectiveness=5.0,
                min_evidence_quality=EvidenceQuality.MODERATE,
                max_recommendations=10,
                time_window_days=365
            )
        else:
            # Low severity - preventive measures
            context = RecommendationContext(
                target_location_id=target_location_id,
                policy_types=policy_types or [
                    PolicyType.TESTING_STRATEGY,
                    PolicyType.CONTACT_TRACING,
                    PolicyType.PUBLIC_HEALTH_MESSAGING
                ],
                min_effectiveness=4.0,
                min_evidence_quality=EvidenceQuality.LOW,
                max_recommendations=10
            )
        
        return await self.recommend_policies(context)
    
    async def get_policy_summary(
        self,
        policy_id: str
    ) -> Dict[str, Any]:
        """
        Get comprehensive summary of a policy including outcomes and implementations.
        
        Args:
            policy_id: Policy UUID
            
        Returns:
            Dictionary with policy summary
        """
        result = await self.session.execute(
            select(Policy)
            .where(Policy.id == policy_id)
            .options(
                selectinload(Policy.location),
                selectinload(Policy.outcomes),
                selectinload(Policy.implementations)
            )
        )
        policy = result.scalar_one_or_none()
        
        if not policy:
            return {}
        
        best_outcome = await self._get_best_outcome(policy_id)
        
        return {
            "policy": {
                "id": str(policy.id),
                "title": policy.title,
                "description": policy.description,
                "type": policy.policy_type.value,
                "status": policy.status.value,
                "start_date": policy.start_date.isoformat() if policy.start_date else None,
                "end_date": policy.end_date.isoformat() if policy.end_date else None,
                "source": policy.source,
                "source_url": policy.source_url,
            },
            "location": {
                "id": str(policy.location.id),
                "name": policy.location.name,
                "country": policy.location.country,
                "region": policy.location.region,
            },
            "outcome": {
                "effectiveness_score": best_outcome.effectiveness_score if best_outcome else None,
                "case_reduction_percent": best_outcome.case_reduction_percent if best_outcome else None,
                "death_reduction_percent": best_outcome.death_reduction_percent if best_outcome else None,
                "evidence_quality": best_outcome.evidence_quality.value if best_outcome else None,
                "measurement_period_start": best_outcome.measurement_period_start.isoformat() if best_outcome and best_outcome.measurement_period_start else None,
                "measurement_period_end": best_outcome.measurement_period_end.isoformat() if best_outcome and best_outcome.measurement_period_end else None,
            } if best_outcome else None,
            "implementations": [
                {
                    "id": str(impl.id),
                    "estimated_cost": impl.estimated_cost,
                    "estimated_duration": impl.estimated_duration,
                    "has_guide": bool(impl.implementation_guide),
                }
                for impl in policy.implementations
            ],
        }

