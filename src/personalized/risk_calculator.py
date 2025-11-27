"""
Personalized Risk Calculator - EpiSPY

Calculates individual risk scores based on multiple factors:
- Current location risk
- Travel history
- Exposure events
- Individual vulnerability
- Behavior patterns
- Occupation
- Household contacts
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload

from ..database.resource_models import (
    UserProfile, UserLocation, ExposureEvent, RiskHistory
)
from ..database.models import Location, OutbreakEvent, RiskAssessment
from ..utils.logger import api_logger


@dataclass
class RiskFactors:
    """Risk factors breakdown."""
    location_risk: float
    travel_risk: float
    exposure_risk: float
    vulnerability_risk: float
    behavior_risk: float
    occupation_risk: float
    household_risk: float


@dataclass
class RiskResult:
    """Complete risk assessment result."""
    total_score: float  # 0-100
    risk_level: str  # LOW, MODERATE, HIGH, CRITICAL
    factors: RiskFactors
    contributing_factors: List[Dict[str, Any]]
    recommendations: List[str]


class PersonalizedRiskCalculator:
    """
    Personalized risk calculator for individuals.
    
    Calculates risk scores based on multiple factors while preserving privacy.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize risk calculator.
        
        Args:
            session: Database session
        """
        self.session = session
        
        # Risk factor weights (sum to 1.0)
        self.weights = {
            'location': 0.30,        # Current location risk
            'travel': 0.15,          # Recent travel
            'exposure': 0.25,        # Exposure events
            'vulnerability': 0.15,   # Individual factors
            'behavior': 0.05,        # Behavior patterns
            'occupation': 0.05,      # Occupation risk
            'household': 0.05,       # Household contacts
        }
        
        # Age group vulnerability multipliers
        self.age_vulnerability = {
            '0-17': 0.5,
            '18-30': 0.7,
            '31-50': 0.8,
            '51-65': 1.2,
            '65+': 1.5,
        }
        
        # Occupation risk multipliers
        self.occupation_risk = {
            'HEALTHCARE': 1.5,
            'ESSENTIAL': 1.2,
            'EDUCATION': 1.1,
            'REMOTE': 0.7,
            'UNEMPLOYED': 0.9,
            'RETIRED': 0.8,
        }
    
    async def calculate_risk_score(
        self,
        user_id: str,
        current_location: Optional[Tuple[float, float]] = None
    ) -> RiskResult:
        """
        Calculate comprehensive personalized risk score.
        
        Args:
            user_id: User identifier
            current_location: Optional (latitude, longitude) tuple
            
        Returns:
            RiskResult with score, level, factors, and recommendations
        """
        api_logger.info(f"Calculating risk score for user {user_id}")
        
        # Get user profile
        result = await self.session.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        
        if not profile:
            # Return default low risk if no profile
            return RiskResult(
                total_score=20.0,
                risk_level="LOW",
                factors=RiskFactors(0, 0, 0, 0, 0, 0, 0),
                contributing_factors=[],
                recommendations=["Create a profile for personalized risk assessment"]
            )
        
        # Calculate individual risk factors
        location_risk = await self._calculate_location_risk(profile, current_location)
        travel_risk = await self._calculate_travel_risk(profile)
        exposure_risk = await self._calculate_exposure_risk(profile)
        vulnerability_risk = self._calculate_vulnerability_risk(profile)
        behavior_risk = self._calculate_behavior_risk(profile)
        occupation_risk = self._calculate_occupation_risk(profile)
        household_risk = self._calculate_household_risk(profile)
        
        factors = RiskFactors(
            location_risk=location_risk,
            travel_risk=travel_risk,
            exposure_risk=exposure_risk,
            vulnerability_risk=vulnerability_risk,
            behavior_risk=behavior_risk,
            occupation_risk=occupation_risk,
            household_risk=household_risk,
        )
        
        # Calculate weighted total score
        total_score = (
            self.weights['location'] * location_risk +
            self.weights['travel'] * travel_risk +
            self.weights['exposure'] * exposure_risk +
            self.weights['vulnerability'] * vulnerability_risk +
            self.weights['behavior'] * behavior_risk +
            self.weights['occupation'] * occupation_risk +
            self.weights['household'] * household_risk
        )
        
        # Clamp to 0-100
        total_score = max(0.0, min(100.0, total_score))
        
        # Determine risk level
        risk_level = self._score_to_level(total_score)
        
        # Get contributing factors
        contributing_factors = self._get_contributing_factors(factors, total_score)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            total_score, risk_level, factors, profile
        )
        
        # Save to history
        await self._save_risk_history(user_id, total_score, risk_level, current_location, factors)
        
        return RiskResult(
            total_score=total_score,
            risk_level=risk_level,
            factors=factors,
            contributing_factors=contributing_factors,
            recommendations=recommendations
        )
    
    async def _calculate_location_risk(
        self,
        profile: UserProfile,
        current_location: Optional[Tuple[float, float]]
    ) -> float:
        """Calculate risk based on current location."""
        location_id = None
        
        # Get current location
        if current_location:
            lat, lon = current_location
            # Find nearest location in database
            result = await self.session.execute(
                select(Location)
                .order_by(
                    func.sqrt(
                        (Location.latitude - lat) ** 2 +
                        (Location.longitude - lon) ** 2
                    )
                )
                .limit(1)
            )
            nearest_location = result.scalar_one_or_none()
            if nearest_location:
                location_id = nearest_location.id
        else:
            # Get most recent user location
            result = await self.session.execute(
                select(UserLocation)
                .where(UserLocation.user_id == profile.user_id)
                .where(UserLocation.is_current == True)
                .order_by(UserLocation.timestamp.desc())
                .limit(1)
            )
            user_loc = result.scalar_one_or_none()
            if user_loc:
                # Find location by coordinates
                result = await self.session.execute(
                    select(Location)
                    .where(
                        and_(
                            func.abs(Location.latitude - user_loc.latitude) < 0.1,
                            func.abs(Location.longitude - user_loc.longitude) < 0.1
                        )
                    )
                    .limit(1)
                )
                nearest_location = result.scalar_one_or_none()
                if nearest_location:
                    location_id = nearest_location.id
        
        if not location_id:
            return 30.0  # Default moderate risk if location unknown
        
        # Get outbreak data for location
        result = await self.session.execute(
            select(OutbreakEvent)
            .where(OutbreakEvent.location_id == location_id)
            .order_by(OutbreakEvent.timestamp.desc())
            .limit(1)
        )
        outbreak = result.scalar_one_or_none()
        
        if not outbreak:
            return 20.0  # Low risk if no outbreak data
        
        # Calculate risk based on outbreak severity
        # Normalize severity (0-10) to risk score (0-100)
        severity_score = outbreak.severity * 10.0
        
        # Factor in case growth
        case_rate = outbreak.cases / max(1, outbreak.active_cases) if outbreak.active_cases > 0 else 0
        growth_factor = min(1.5, 1.0 + case_rate * 0.1)
        
        risk_score = severity_score * growth_factor
        return max(0.0, min(100.0, risk_score))
    
    async def _calculate_travel_risk(self, profile: UserProfile) -> float:
        """Calculate risk from recent travel history."""
        # Get locations visited in last 14 days
        cutoff_date = datetime.now() - timedelta(days=14)
        
        result = await self.session.execute(
            select(UserLocation)
            .where(UserLocation.user_id == profile.user_id)
            .where(UserLocation.timestamp >= cutoff_date)
            .order_by(UserLocation.timestamp.desc())
        )
        recent_locations = result.scalars().all()
        
        if not recent_locations:
            return 10.0  # Low risk if no travel
        
        # Calculate average risk of visited locations
        total_risk = 0.0
        count = 0
        
        for user_loc in recent_locations:
            # Find location
            result = await self.session.execute(
                select(Location)
                .where(
                    and_(
                        func.abs(Location.latitude - user_loc.latitude) < 0.1,
                        func.abs(Location.longitude - user_loc.longitude) < 0.1
                    )
                )
                .limit(1)
            )
            location = result.scalar_one_or_none()
            
            if location:
                # Get outbreak data
                result = await self.session.execute(
                    select(OutbreakEvent)
                    .where(OutbreakEvent.location_id == location.id)
                    .order_by(OutbreakEvent.timestamp.desc())
                    .limit(1)
                )
                outbreak = result.scalar_one_or_none()
                
                if outbreak:
                    total_risk += outbreak.severity * 10.0
                    count += 1
        
        if count == 0:
            return 10.0
        
        avg_risk = total_risk / count
        return max(0.0, min(100.0, avg_risk))
    
    async def _calculate_exposure_risk(self, profile: UserProfile) -> float:
        """Calculate risk from exposure events."""
        # Get recent exposure events (last 14 days)
        cutoff_date = datetime.now() - timedelta(days=14)
        
        result = await self.session.execute(
            select(ExposureEvent)
            .where(ExposureEvent.user_id == profile.user_id)
            .where(ExposureEvent.exposure_date >= cutoff_date)
        )
        exposures = result.scalars().all()
        
        if not exposures:
            return 0.0
        
        # Calculate risk based on exposure events
        total_risk = 0.0
        for exposure in exposures:
            risk_scores = {
                'LOW': 20.0,
                'MODERATE': 50.0,
                'HIGH': 80.0,
            }
            total_risk += risk_scores.get(exposure.risk_level, 50.0)
        
        # Average and decay over time
        avg_risk = total_risk / len(exposures)
        
        # Most recent exposure matters more
        if exposures:
            most_recent = max(exposures, key=lambda e: e.exposure_date)
            days_ago = (datetime.now() - most_recent.exposure_date).days
            decay_factor = max(0.5, 1.0 - days_ago / 14.0)
            avg_risk *= decay_factor
        
        return max(0.0, min(100.0, avg_risk))
    
    def _calculate_vulnerability_risk(self, profile: UserProfile) -> float:
        """Calculate individual vulnerability risk."""
        base_risk = 30.0
        
        # Age factor
        if profile.age_group:
            multiplier = self.age_vulnerability.get(profile.age_group, 1.0)
            base_risk *= multiplier
        
        # Comorbidities
        if profile.comorbidities:
            comorbidity_count = len(profile.comorbidities) if isinstance(profile.comorbidities, list) else 1
            base_risk += comorbidity_count * 15.0
        
        # Vaccination status
        if profile.vaccination_status:
            if isinstance(profile.vaccination_status, dict):
                doses = profile.vaccination_status.get('doses', 0)
                if doses >= 2:
                    base_risk *= 0.6  # Reduce risk by 40% if fully vaccinated
                elif doses == 1:
                    base_risk *= 0.8  # Reduce risk by 20% if partially vaccinated
        
        return max(0.0, min(100.0, base_risk))
    
    def _calculate_behavior_risk(self, profile: UserProfile) -> float:
        """Calculate risk from behavior patterns."""
        # Default moderate risk
        base_risk = 30.0
        
        # Adjust based on risk factors if available
        if profile.risk_factors:
            if isinstance(profile.risk_factors, dict):
                # Mask wearing compliance
                mask_compliance = profile.risk_factors.get('mask_compliance', 0.5)
                base_risk *= (1.0 - mask_compliance * 0.3)  # Up to 30% reduction
                
                # Social distancing
                social_distancing = profile.risk_factors.get('social_distancing', 0.5)
                base_risk *= (1.0 - social_distancing * 0.2)  # Up to 20% reduction
        
        return max(0.0, min(100.0, base_risk))
    
    def _calculate_occupation_risk(self, profile: UserProfile) -> float:
        """Calculate risk from occupation."""
        if not profile.occupation:
            return 20.0  # Default low risk
        
        # Get occupation risk multiplier
        occupation_upper = profile.occupation.upper()
        multiplier = 1.0
        
        for occ_type, mult in self.occupation_risk.items():
            if occ_type in occupation_upper:
                multiplier = mult
                break
        
        base_risk = 30.0 * multiplier
        return max(0.0, min(100.0, base_risk))
    
    def _calculate_household_risk(self, profile: UserProfile) -> float:
        """Calculate risk from household contacts."""
        if not profile.household_size or profile.household_size <= 1:
            return 10.0  # Low risk if living alone
        
        # More household members = higher risk
        base_risk = 20.0 + (profile.household_size - 1) * 10.0
        return max(0.0, min(100.0, base_risk))
    
    def _score_to_level(self, score: float) -> str:
        """Convert numeric score to risk level."""
        if score < 30:
            return "LOW"
        elif score < 50:
            return "MODERATE"
        elif score < 75:
            return "HIGH"
        else:
            return "CRITICAL"
    
    def _get_contributing_factors(
        self,
        factors: RiskFactors,
        total_score: float
    ) -> List[Dict[str, Any]]:
        """Get ranked list of contributing factors."""
        factor_list = [
            {'name': 'Location Risk', 'value': factors.location_risk, 'weight': self.weights['location']},
            {'name': 'Travel Risk', 'value': factors.travel_risk, 'weight': self.weights['travel']},
            {'name': 'Exposure Risk', 'value': factors.exposure_risk, 'weight': self.weights['exposure']},
            {'name': 'Vulnerability', 'value': factors.vulnerability_risk, 'weight': self.weights['vulnerability']},
            {'name': 'Behavior', 'value': factors.behavior_risk, 'weight': self.weights['behavior']},
            {'name': 'Occupation', 'value': factors.occupation_risk, 'weight': self.weights['occupation']},
            {'name': 'Household', 'value': factors.household_risk, 'weight': self.weights['household']},
        ]
        
        # Calculate contribution to total score
        for factor in factor_list:
            factor['contribution'] = factor['value'] * factor['weight']
            factor['percentage'] = (factor['contribution'] / total_score * 100) if total_score > 0 else 0
        
        # Sort by contribution (descending)
        factor_list.sort(key=lambda x: x['contribution'], reverse=True)
        
        return factor_list
    
    def _generate_recommendations(
        self,
        score: float,
        level: str,
        factors: RiskFactors,
        profile: UserProfile
    ) -> List[str]:
        """Generate personalized recommendations."""
        recommendations = []
        
        # High location risk
        if factors.location_risk > 70:
            recommendations.append("Consider limiting time in high-risk areas")
            recommendations.append("Wear N95 masks when outdoors")
        
        # High exposure risk
        if factors.exposure_risk > 50:
            recommendations.append("Get tested immediately")
            recommendations.append("Self-isolate for 7 days")
            recommendations.append("Monitor symptoms closely")
        
        # High vulnerability
        if factors.vulnerability_risk > 60:
            recommendations.append("Consider additional precautions due to age/health conditions")
            if not profile.vaccination_status or (
                isinstance(profile.vaccination_status, dict) and
                profile.vaccination_status.get('doses', 0) < 2
            ):
                recommendations.append("Get fully vaccinated if eligible")
        
        # High travel risk
        if factors.travel_risk > 50:
            recommendations.append("Limit non-essential travel")
            recommendations.append("Get tested after returning from travel")
        
        # High occupation risk
        if factors.occupation_risk > 60:
            recommendations.append("Use enhanced PPE at work")
            recommendations.append("Follow workplace safety protocols strictly")
        
        # General recommendations based on risk level
        if level == "CRITICAL":
            recommendations.insert(0, "URGENT: Take immediate protective measures")
            recommendations.insert(1, "Avoid all non-essential activities")
        elif level == "HIGH":
            recommendations.insert(0, "Take extra precautions")
            recommendations.insert(1, "Limit social interactions")
        elif level == "MODERATE":
            recommendations.insert(0, "Follow standard health guidelines")
        else:
            recommendations.insert(0, "Continue following basic precautions")
        
        return recommendations[:10]  # Limit to 10 recommendations
    
    async def _save_risk_history(
        self,
        user_id: str,
        score: float,
        level: str,
        location: Optional[Tuple[float, float]],
        factors: RiskFactors
    ):
        """Save risk assessment to history."""
        location_id = None
        
        if location:
            # Find location
            lat, lon = location
            result = await self.session.execute(
                select(Location)
                .order_by(
                    func.sqrt(
                        (Location.latitude - lat) ** 2 +
                        (Location.longitude - lon) ** 2
                    )
                )
                .limit(1)
            )
            nearest = result.scalar_one_or_none()
            if nearest:
                location_id = nearest.id
        
        risk_history = RiskHistory(
            user_id=user_id,
            date=datetime.now(),
            risk_score=score,
            risk_level=level,
            location_id=location_id,
            contributing_factors={
                'location_risk': factors.location_risk,
                'travel_risk': factors.travel_risk,
                'exposure_risk': factors.exposure_risk,
                'vulnerability_risk': factors.vulnerability_risk,
                'behavior_risk': factors.behavior_risk,
                'occupation_risk': factors.occupation_risk,
                'household_risk': factors.household_risk,
            }
        )
        
        self.session.add(risk_history)
        await self.session.commit()

