"""
Resource Matching Engine - EpiSPY Marketplace

Optimization algorithms for matching resource requests with available inventory.
Uses linear programming and multi-criteria decision analysis.
"""

from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import math
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload

from ..database.resource_models import (
    ResourceRequest, ResourceInventory, ResourceMatch, ResourceProvider,
    UrgencyLevel, MatchStatus, ResourceType
)
from ..database.models import Location
from ..utils.logger import api_logger


@dataclass
class MatchScore:
    """Match score breakdown."""
    total_score: float
    geographic_score: float
    urgency_score: float
    quality_score: float
    cost_score: float
    reliability_score: float
    availability_score: float


class ResourceMatchingEngine:
    """
    Resource matching engine with optimization algorithms.
    
    Matches resource requests with available inventory using:
    - Multi-criteria decision analysis
    - Geographic proximity optimization
    - Urgency-weighted allocation
    - Quality and reliability scoring
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize matching engine.
        
        Args:
            session: Database session
        """
        self.session = session
        
        # Scoring weights (sum to 1.0)
        self.weights = {
            'geographic': 0.25,      # Distance matters
            'urgency': 0.30,         # Urgency is critical
            'quality': 0.15,         # Resource quality
            'cost': 0.10,            # Cost efficiency
            'reliability': 0.15,     # Provider reliability
            'availability': 0.05,    # Immediate availability
        }
        
        # Urgency multipliers
        self.urgency_multipliers = {
            UrgencyLevel.ROUTINE: 1.0,
            UrgencyLevel.URGENT: 1.5,
            UrgencyLevel.CRITICAL: 2.0,
            UrgencyLevel.EMERGENCY: 3.0,
        }
    
    async def match_requests_to_inventory(
        self,
        request_id: Optional[str] = None,
        auto_accept_threshold: float = 80.0
    ) -> List[ResourceMatch]:
        """
        Match resource requests with available inventory.
        
        Uses optimization to find best matches considering:
        - Geographic proximity
        - Urgency level
        - Resource quality
        - Provider reliability
        - Cost efficiency
        
        Args:
            request_id: Specific request to match (None = match all open requests)
            auto_accept_threshold: Auto-accept matches above this score
            
        Returns:
            List of created ResourceMatch objects
        """
        api_logger.info(f"Matching resources (request_id={request_id})")
        
        # Get open requests
        if request_id:
            result = await self.session.execute(
                select(ResourceRequest)
                .where(ResourceRequest.id == request_id)
                .where(ResourceRequest.status == "OPEN")
                .options(selectinload(ResourceRequest.location))
            )
            requests = [result.scalar_one_or_none()]
            requests = [r for r in requests if r is not None]
        else:
            result = await self.session.execute(
                select(ResourceRequest)
                .where(ResourceRequest.status == "OPEN")
                .options(selectinload(ResourceRequest.location))
            )
            requests = result.scalars().all()
        
        if not requests:
            api_logger.info("No open requests to match")
            return []
        
        matches_created = []
        
        for request in requests:
            # Find compatible inventory
            compatible_inventory = await self._find_compatible_inventory(request)
            
            if not compatible_inventory:
                api_logger.warning(f"No compatible inventory for request {request.id}")
                continue
            
            # Calculate match scores
            scored_matches = []
            for inventory in compatible_inventory:
                score = await self.calculate_match_score(request, inventory)
                scored_matches.append((inventory, score))
            
            # Sort by score (descending)
            scored_matches.sort(key=lambda x: x[1].total_score, reverse=True)
            
            # Create matches (top 5 per request)
            for inventory, score in scored_matches[:5]:
                # Check if match already exists
                existing = await self.session.execute(
                    select(ResourceMatch)
                    .where(ResourceMatch.request_id == request.id)
                    .where(ResourceMatch.inventory_id == inventory.id)
                    .where(ResourceMatch.status == MatchStatus.PENDING)
                )
                if existing.scalar_one_or_none():
                    continue
                
                # Calculate quantity to match
                quantity_needed = request.quantity_needed - request.quantity_fulfilled
                quantity_available = inventory.quantity_available - inventory.quantity_reserved
                quantity_matched = min(quantity_needed, quantity_available)
                
                if quantity_matched <= 0:
                    continue
                
                # Create match
                match = ResourceMatch(
                    request_id=request.id,
                    inventory_id=inventory.id,
                    provider_id=inventory.provider_id,
                    quantity_matched=quantity_matched,
                    match_score=score.total_score,
                    status=MatchStatus.PENDING,
                    metadata_json={
                        'geographic_score': score.geographic_score,
                        'urgency_score': score.urgency_score,
                        'quality_score': score.quality_score,
                        'cost_score': score.cost_score,
                        'reliability_score': score.reliability_score,
                        'availability_score': score.availability_score,
                    }
                )
                
                self.session.add(match)
                matches_created.append(match)
                
                # Auto-accept high-scoring matches
                if score.total_score >= auto_accept_threshold:
                    match.status = MatchStatus.ACCEPTED
                    match.accepted_at = datetime.now()
                    api_logger.info(
                        f"Auto-accepted match {match.id} with score {score.total_score:.2f}"
                    )
        
        await self.session.commit()
        api_logger.info(f"Created {len(matches_created)} matches")
        
        return matches_created
    
    async def _find_compatible_inventory(
        self,
        request: ResourceRequest
    ) -> List[ResourceInventory]:
        """
        Find compatible inventory for a request.
        
        Args:
            request: Resource request
            
        Returns:
            List of compatible inventory items
        """
        # Base query
        query = (
            select(ResourceInventory)
            .where(ResourceInventory.resource_type == request.resource_type)
            .where(ResourceInventory.is_active == True)
            .where(
                ResourceInventory.quantity_available - ResourceInventory.quantity_reserved > 0
            )
            .options(selectinload(ResourceInventory.provider))
        )
        
        # Filter by expiry date if applicable
        if request.resource_type in [
            ResourceType.VACCINE, ResourceType.ANTIVIRAL, ResourceType.ANTIBIOTIC
        ]:
            query = query.where(
                or_(
                    ResourceInventory.expiry_date.is_(None),
                    ResourceInventory.expiry_date > datetime.now() + timedelta(days=30)
                )
            )
        
        result = await self.session.execute(query)
        inventory_items = result.scalars().all()
        
        return list(inventory_items)
    
    async def calculate_match_score(
        self,
        request: ResourceRequest,
        inventory: ResourceInventory
    ) -> MatchScore:
        """
        Calculate comprehensive match score.
        
        Args:
            request: Resource request
            inventory: Available inventory item
            
        Returns:
            MatchScore object with breakdown
        """
        # Geographic score (0-100)
        geographic_score = await self._calculate_geographic_score(request, inventory)
        
        # Urgency score (0-100)
        urgency_score = self._calculate_urgency_score(request)
        
        # Quality score (0-100)
        quality_score = self._calculate_quality_score(inventory)
        
        # Cost score (0-100)
        cost_score = self._calculate_cost_score(inventory)
        
        # Reliability score (0-100)
        reliability_score = await self._calculate_reliability_score(inventory.provider_id)
        
        # Availability score (0-100)
        availability_score = self._calculate_availability_score(inventory, request)
        
        # Weighted total score
        total_score = (
            self.weights['geographic'] * geographic_score +
            self.weights['urgency'] * urgency_score +
            self.weights['quality'] * quality_score +
            self.weights['cost'] * cost_score +
            self.weights['reliability'] * reliability_score +
            self.weights['availability'] * availability_score
        )
        
        # Apply urgency multiplier
        urgency_mult = self.urgency_multipliers.get(request.urgency, 1.0)
        total_score = min(100.0, total_score * urgency_mult)
        
        return MatchScore(
            total_score=total_score,
            geographic_score=geographic_score,
            urgency_score=urgency_score,
            quality_score=quality_score,
            cost_score=cost_score,
            reliability_score=reliability_score,
            availability_score=availability_score,
        )
    
    async def _calculate_geographic_score(
        self,
        request: ResourceRequest,
        inventory: ResourceInventory
    ) -> float:
        """
        Calculate geographic proximity score.
        
        Closer = higher score (0-100).
        """
        if not request.location_id or not inventory.provider.location_id:
            return 50.0  # Neutral score if location unknown
        
        # Get locations
        req_loc_result = await self.session.execute(
            select(Location).where(Location.id == request.location_id)
        )
        req_location = req_loc_result.scalar_one_or_none()
        
        prov_loc_result = await self.session.execute(
            select(Location).where(Location.id == inventory.provider.location_id)
        )
        prov_location = prov_loc_result.scalar_one_or_none()
        
        if not req_location or not prov_location:
            return 50.0
        
        # Calculate distance (Haversine formula)
        distance_km = self._haversine_distance(
            req_location.latitude, req_location.longitude,
            prov_location.latitude, prov_location.longitude
        )
        
        # Score: 100 at 0km, 0 at 1000km+
        # Exponential decay
        score = 100.0 * math.exp(-distance_km / 200.0)
        return max(0.0, min(100.0, score))
    
    def _calculate_urgency_score(self, request: ResourceRequest) -> float:
        """Calculate urgency-based score."""
        urgency_scores = {
            UrgencyLevel.ROUTINE: 25.0,
            UrgencyLevel.URGENT: 50.0,
            UrgencyLevel.CRITICAL: 75.0,
            UrgencyLevel.EMERGENCY: 100.0,
        }
        base_score = urgency_scores.get(request.urgency, 50.0)
        
        # Boost if deadline is near
        if request.deadline:
            hours_until_deadline = (request.deadline - datetime.now()).total_seconds() / 3600
            if hours_until_deadline < 24:
                base_score = min(100.0, base_score * 1.5)
            elif hours_until_deadline < 72:
                base_score = min(100.0, base_score * 1.2)
        
        return base_score
    
    def _calculate_quality_score(self, inventory: ResourceInventory) -> float:
        """Calculate quality-based score."""
        if not inventory.quality_grade:
            return 50.0  # Neutral if unknown
        
        quality_scores = {
            'A': 100.0,
            'B': 75.0,
            'C': 50.0,
            'D': 25.0,
        }
        return quality_scores.get(inventory.quality_grade.value, 50.0)
    
    def _calculate_cost_score(self, inventory: ResourceInventory) -> float:
        """Calculate cost efficiency score."""
        if not inventory.unit_price:
            return 50.0  # Neutral if price unknown
        
        # Lower price = higher score
        # Normalize to 0-100 (assuming max reasonable price)
        max_price = 10000.0  # Adjust based on resource type
        normalized_price = min(1.0, inventory.unit_price / max_price)
        score = 100.0 * (1.0 - normalized_price)
        
        return max(0.0, min(100.0, score))
    
    async def _calculate_reliability_score(self, provider_id: str) -> float:
        """Calculate provider reliability score."""
        # Get provider
        result = await self.session.execute(
            select(ResourceProvider).where(ResourceProvider.id == provider_id)
        )
        provider = result.scalar_one_or_none()
        
        if not provider:
            return 0.0
        
        # Base score from rating
        rating_score = (provider.rating or 0.0) * 20.0  # 0-5 -> 0-100
        
        # Boost for verified providers
        verified_boost = 20.0 if provider.verified else 0.0
        
        # Boost for transaction history
        transaction_boost = min(20.0, provider.total_transactions * 2.0)
        
        total_score = rating_score + verified_boost + transaction_boost
        return max(0.0, min(100.0, total_score))
    
    def _calculate_availability_score(
        self,
        inventory: ResourceInventory,
        request: ResourceRequest
    ) -> float:
        """Calculate immediate availability score."""
        quantity_available = inventory.quantity_available - inventory.quantity_reserved
        quantity_needed = request.quantity_needed - request.quantity_fulfilled
        
        if quantity_available >= quantity_needed:
            return 100.0  # Can fulfill completely
        else:
            # Partial fulfillment
            fulfillment_ratio = quantity_available / quantity_needed
            return fulfillment_ratio * 100.0
    
    @staticmethod
    def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two points using Haversine formula.
        
        Returns distance in kilometers.
        """
        R = 6371.0  # Earth radius in km
        
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (
            math.sin(dlat / 2) ** 2 +
            math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
            math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    async def predict_future_needs(
        self,
        location_id: str,
        days_ahead: int = 14
    ) -> Dict[str, Any]:
        """
        Predict future resource needs based on outbreak forecasts.
        
        Args:
            location_id: Location to predict for
            days_ahead: Prediction horizon in days
            
        Returns:
            Dictionary with predicted resource needs
        """
        # TODO: Integrate with outbreak prediction models
        # For now, return placeholder structure
        
        api_logger.info(f"Predicting resource needs for location {location_id} ({days_ahead} days)")
        
        # Get current outbreak data
        from ..database.models import OutbreakEvent
        result = await self.session.execute(
            select(OutbreakEvent)
            .where(OutbreakEvent.location_id == location_id)
            .order_by(OutbreakEvent.timestamp.desc())
            .limit(1)
        )
        outbreak = result.scalar_one_or_none()
        
        predictions = {
            'location_id': location_id,
            'prediction_date': datetime.now(),
            'horizon_days': days_ahead,
            'predicted_needs': {},
        }
        
        if outbreak:
            # Simple heuristic: scale based on current cases
            case_multiplier = outbreak.cases / 1000.0 if outbreak.cases > 0 else 1.0
            
            predictions['predicted_needs'] = {
                'ICU_BED': int(10 * case_multiplier),
                'VENTILATOR': int(5 * case_multiplier),
                'OXYGEN_CYLINDER': int(20 * case_multiplier),
                'N95_MASK': int(1000 * case_multiplier),
                'DOCTOR': int(5 * case_multiplier),
                'NURSE': int(15 * case_multiplier),
            }
        
        return predictions
    
    async def optimize_logistics(
        self,
        transfer_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Optimize logistics for multiple resource transfers.
        
        Args:
            transfer_ids: List of transfer IDs to optimize
            
        Returns:
            Optimization results with routes and schedules
        """
        # TODO: Integrate with routing APIs (Google Maps, Mapbox)
        # For now, return placeholder structure
        
        api_logger.info(f"Optimizing logistics for {len(transfer_ids)} transfers")
        
        return {
            'optimized_routes': [],
            'total_distance_km': 0.0,
            'estimated_time_hours': 0.0,
            'cost_estimate': 0.0,
        }

