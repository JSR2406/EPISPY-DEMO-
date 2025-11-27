"""
Resource recommendation engine for mental health hotspots.

This module provides intelligent resource recommendations based on detected
mental health hotspots and available resources.
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

from ..utils.logger import api_logger
from .models import (
    MentalHealthHotspot,
    MentalHealthResource,
    MentalHealthIndicator,
    MentalHealthSeverity
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class ResourceRecommendation:
    """Resource recommendation for a hotspot."""
    resource_id: str
    resource_name: str
    resource_type: str
    relevance_score: float  # 0-1
    distance_km: Optional[float]
    availability_status: str
    services_match: List[str]
    recommended_actions: List[str]


class ResourceRecommendationEngine:
    """Engine for recommending mental health resources."""
    
    def __init__(self):
        """Initialize resource recommendation engine."""
        # Resource type priority mapping
        self.resource_priority = {
            "CRISIS": ["crisis_hotline", "crisis_center", "emergency_mental_health"],
            "SUICIDAL_IDEATION": ["crisis_hotline", "suicide_prevention", "emergency_services"],
            "ANXIETY": ["counselor", "therapist", "anxiety_support_group", "crisis_hotline"],
            "DEPRESSION": ["counselor", "therapist", "depression_support_group", "psychiatrist"],
            "SUBSTANCE_ABUSE": ["substance_abuse_center", "addiction_counselor", "detox_center"],
            "STRESS": ["counselor", "stress_management", "support_group"],
            "PTSD": ["trauma_therapist", "ptsd_support_group", "psychiatrist"],
            "EATING_DISORDER": ["eating_disorder_clinic", "nutritionist", "therapist"]
        }
    
    async def recommend_resources_for_hotspot(
        self,
        hotspot: MentalHealthHotspot,
        db_session: AsyncSession,
        max_recommendations: int = 5
    ) -> List[ResourceRecommendation]:
        """
        Recommend resources for a mental health hotspot.
        
        Args:
            hotspot: Mental health hotspot
            db_session: Database session
            max_recommendations: Maximum number of recommendations
            
        Returns:
            List of resource recommendations
        """
        # Get available resources in location
        available_resources = await self._get_resources_for_location(
            hotspot.location_id,
            db_session
        )
        
        if not available_resources:
            api_logger.warning(f"No resources found for location {hotspot.location_id}")
            return []
        
        # Score resources based on hotspot indicators
        scored_resources = []
        
        for resource in available_resources:
            score, matched_services = self._score_resource_relevance(
                resource,
                hotspot
            )
            
            if score > 0.0:  # Only recommend relevant resources
                # Calculate distance (simplified - would use actual geocoding)
                distance = self._calculate_distance(
                    hotspot,
                    resource
                )
                
                scored_resources.append(ResourceRecommendation(
                    resource_id=str(resource.id),
                    resource_name=resource.name or "Unnamed Resource",
                    resource_type=resource.resource_type,
                    relevance_score=score,
                    distance_km=distance,
                    availability_status=resource.availability_status or "UNKNOWN",
                    services_match=matched_services,
                    recommended_actions=self._generate_resource_actions(
                        resource,
                        hotspot
                    )
                ))
        
        # Sort by relevance score and distance
        scored_resources.sort(
            key=lambda r: (r.relevance_score, -r.distance_km if r.distance_km else 0),
            reverse=True
        )
        
        # Return top recommendations
        return scored_resources[:max_recommendations]
    
    async def _get_resources_for_location(
        self,
        location_id: str,
        db_session: AsyncSession
    ) -> List[MentalHealthResource]:
        """Get available resources for a location."""
        try:
            result = await db_session.execute(
                select(MentalHealthResource).where(
                    MentalHealthResource.location_id == location_id
                )
            )
            resources = result.scalars().all()
            return list(resources)
        except Exception as e:
            api_logger.error(f"Failed to get resources for location: {str(e)}")
            return []
    
    def _score_resource_relevance(
        self,
        resource: MentalHealthResource,
        hotspot: MentalHealthHotspot
    ) -> Tuple[float, List[str]]:
        """
        Score resource relevance for hotspot.
        
        Returns:
            Tuple of (score, matched_services)
        """
        score = 0.0
        matched_services = []
        
        # Base score for resource type
        resource_type = resource.resource_type.lower()
        
        # Score based on primary indicators
        for indicator in hotspot.primary_indicators:
            indicator_str = indicator.upper() if isinstance(indicator, str) else indicator.value
            
            # Check if resource type matches indicator priority
            priority_types = self.resource_priority.get(indicator_str, [])
            if any(pt in resource_type for pt in priority_types):
                score += 0.4
                matched_services.append(indicator_str)
            
            # Check services offered
            if resource.services_offered:
                services = resource.services_offered
                if isinstance(services, list):
                    service_str = " ".join(services).lower()
                else:
                    service_str = str(services).lower()
                
                # Match services to indicators
                if indicator_str == "CRISIS" and any(
                    kw in service_str for kw in ["crisis", "emergency", "hotline"]
                ):
                    score += 0.3
                    matched_services.append(f"crisis_support")
                
                elif indicator_str == "ANXIETY" and any(
                    kw in service_str for kw in ["anxiety", "panic", "stress"]
                ):
                    score += 0.3
                    matched_services.append(f"anxiety_support")
                
                elif indicator_str == "DEPRESSION" and any(
                    kw in service_str for kw in ["depression", "mood", "mental health"]
                ):
                    score += 0.3
                    matched_services.append(f"depression_support")
        
        # Adjust score based on hotspot severity
        severity_multiplier = {
            MentalHealthSeverity.CRITICAL: 1.2,
            MentalHealthSeverity.SEVERE: 1.1,
            MentalHealthSeverity.MODERATE: 1.0,
            MentalHealthSeverity.MILD: 0.9
        }.get(hotspot.severity, 1.0)
        
        score *= severity_multiplier
        
        # Adjust for availability
        if resource.availability_status:
            availability = resource.availability_status.upper()
            if "AVAILABLE" in availability or "OPEN" in availability:
                score *= 1.1
            elif "FULL" in availability or "UNAVAILABLE" in availability:
                score *= 0.7
            elif "WAITLIST" in availability:
                score *= 0.9
        
        # Normalize score
        score = min(1.0, score)
        
        return score, list(set(matched_services))
    
    def _calculate_distance(
        self,
        hotspot: MentalHealthHotspot,
        resource: MentalHealthResource
    ) -> Optional[float]:
        """
        Calculate distance between hotspot and resource.
        
        Returns distance in km, or None if coordinates unavailable.
        """
        # This is simplified - in production would use actual geocoding
        # For now, assume resources at same location are 0km distance
        if hotspot.location_id == resource.location_id:
            return 0.0
        
        # In production, would calculate actual distance
        return None
    
    def _generate_resource_actions(
        self,
        resource: MentalHealthResource,
        hotspot: MentalHealthHotspot
    ) -> List[str]:
        """Generate recommended actions for resource."""
        actions = []
        
        resource_type = resource.resource_type.lower()
        
        if "hotline" in resource_type or "crisis" in resource_type:
            actions.append(f"Promote {resource.name or 'crisis hotline'} in affected area")
            actions.append("Distribute hotline number through public health channels")
        
        if "counselor" in resource_type or "therapist" in resource_type:
            actions.append(f"Refer individuals to {resource.name or 'counseling services'}")
            actions.append("Coordinate appointment scheduling")
        
        if "support_group" in resource_type:
            actions.append("Organize support group meetings in affected area")
            actions.append("Provide transportation assistance if needed")
        
        if "emergency" in resource_type:
            actions.append("Pre-position emergency mental health services")
            actions.append("Coordinate with emergency response teams")
        
        # General actions
        if resource.capacity:
            actions.append(f"Monitor capacity: {resource.capacity} available slots")
        
        return actions
    
    async def get_national_resources(
        self,
        db_session: AsyncSession,
        indicator: Optional[MentalHealthIndicator] = None
    ) -> List[Dict[str, Any]]:
        """
        Get national-level resources (e.g., national hotlines).
        
        Args:
            db_session: Database session
            indicator: Optional filter by indicator type
            
        Returns:
            List of national resources
        """
        # In production, would query from a national resources database
        # For now, return hardcoded national resources
        
        national_resources = [
            {
                "name": "National Suicide Prevention Lifeline",
                "type": "crisis_hotline",
                "contact": "988",
                "available_24_7": True,
                "languages": ["English", "Spanish"],
                "services": ["Crisis support", "Suicide prevention", "Mental health support"]
            },
            {
                "name": "Crisis Text Line",
                "type": "crisis_hotline",
                "contact": "Text HOME to 741741",
                "available_24_7": True,
                "services": ["Crisis support via text", "Mental health support"]
            },
            {
                "name": "SAMHSA National Helpline",
                "type": "information_and_referral",
                "contact": "1-800-662-HELP (4357)",
                "available_24_7": True,
                "services": ["Substance abuse support", "Mental health referrals", "Treatment locator"]
            }
        ]
        
        # Filter by indicator if specified
        if indicator:
            filtered = []
            for resource in national_resources:
                services = " ".join(resource.get("services", [])).lower()
                indicator_str = indicator.value.lower()
                
                if indicator == MentalHealthIndicator.CRISIS or indicator == MentalHealthIndicator.SUICIDAL_IDEATION:
                    if "crisis" in services or "suicide" in services:
                        filtered.append(resource)
                elif indicator_str in services:
                    filtered.append(resource)
            
            return filtered
        
        return national_resources
    
    async def recommend_action_plan(
        self,
        hotspot: MentalHealthHotspot,
        db_session: AsyncSession
    ) -> Dict[str, Any]:
        """
        Generate comprehensive action plan for hotspot.
        
        Args:
            hotspot: Mental health hotspot
            db_session: Database session
            
        Returns:
            Action plan dictionary
        """
        # Get resource recommendations
        resources = await self.recommend_resources_for_hotspot(hotspot, db_session)
        
        # Get national resources
        national_resources = await self.get_national_resources(
            db_session,
            hotspot.primary_indicators[0] if hotspot.primary_indicators else None
        )
        
        # Build action plan
        action_plan = {
            "hotspot_id": str(hotspot.id),
            "location_id": str(hotspot.location_id),
            "hotspot_score": hotspot.hotspot_score,
            "severity": hotspot.severity.value,
            "immediate_actions": [],
            "resource_recommendations": [
                {
                    "resource_id": r.resource_id,
                    "name": r.resource_name,
                    "type": r.resource_type,
                    "relevance_score": r.relevance_score,
                    "distance_km": r.distance_km,
                    "actions": r.recommended_actions
                }
                for r in resources
            ],
            "national_resources": national_resources,
            "monitoring_actions": [],
            "prevention_actions": []
        }
        
        # Immediate actions based on severity
        if hotspot.severity == MentalHealthSeverity.CRITICAL:
            action_plan["immediate_actions"].extend([
                "Activate crisis response team immediately",
                "Deploy mobile mental health units",
                "Increase hotline staffing",
                "Coordinate with emergency services"
            ])
        elif hotspot.severity == MentalHealthSeverity.SEVERE:
            action_plan["immediate_actions"].extend([
                "Mobilize mental health resources",
                "Increase counseling availability",
                "Distribute crisis support information"
            ])
        
        # Indicator-specific immediate actions
        if MentalHealthIndicator.CRISIS in hotspot.primary_indicators:
            action_plan["immediate_actions"].append("Implement suicide prevention protocols")
        
        # Monitoring actions
        action_plan["monitoring_actions"].extend([
            "Monitor hotspot trend daily",
            "Track resource utilization",
            "Review alert effectiveness",
            "Collect feedback from providers"
        ])
        
        # Prevention actions
        action_plan["prevention_actions"].extend([
            "Provide mental health education resources",
            "Promote community support programs",
            "Increase awareness of available resources",
            "Coordinate with schools and workplaces"
        ])
        
        return action_plan

