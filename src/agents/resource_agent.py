"""
Resource Coordination Agent - EpiSPY

AI agent that monitors resource levels, proactively identifies shortages,
and automatically coordinates resource allocation.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from ..database.resource_models import (
    ResourceRequest, ResourceInventory, ResourceMatch, ResourceProvider,
    UrgencyLevel, ResourceType
)
from ..database.models import Location, OutbreakEvent
from ..marketplace.matching_engine import ResourceMatchingEngine
from ..utils.logger import api_logger


class ResourceCoordinationAgent:
    """
    AI agent for resource coordination.
    
    Capabilities:
    - Monitor resource levels across regions
    - Proactively identify shortages
    - Automatically match requests
    - Suggest resource reallocation
    - Trigger procurement orders
    - Coordinate emergency resource airlifts
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize resource coordination agent.
        
        Args:
            session: Database session
        """
        self.session = session
        self.matching_engine = ResourceMatchingEngine(session)
    
    async def monitor_resource_levels(self) -> Dict[str, Any]:
        """
        Monitor resource levels across all locations.
        
        Returns:
            Dictionary with resource level analysis
        """
        api_logger.info("Resource agent: Monitoring resource levels")
        
        # Get all active inventory by resource type
        result = await self.session.execute(
            select(ResourceInventory)
            .where(ResourceInventory.is_active == True)
            .where(ResourceInventory.quantity_available > 0)
        )
        inventory_items = result.scalars().all()
        
        # Aggregate by resource type
        resource_levels = {}
        for item in inventory_items:
            resource_type = item.resource_type.value
            if resource_type not in resource_levels:
                resource_levels[resource_type] = {
                    'total_available': 0,
                    'total_reserved': 0,
                    'locations': [],
                }
            resource_levels[resource_type]['total_available'] += item.quantity_available
            resource_levels[resource_type]['total_reserved'] += item.quantity_reserved
        
        # Get open requests by resource type
        req_result = await self.session.execute(
            select(ResourceRequest)
            .where(ResourceRequest.status == "OPEN")
        )
        requests = req_result.scalars().all()
        
        demand_by_type = {}
        for req in requests:
            resource_type = req.resource_type.value
            if resource_type not in demand_by_type:
                demand_by_type[resource_type] = 0
            demand_by_type[resource_type] += req.quantity_needed - req.quantity_fulfilled
        
        # Calculate shortages
        shortages = {}
        for resource_type in set(list(resource_levels.keys()) + list(demand_by_type.keys())):
            available = resource_levels.get(resource_type, {}).get('total_available', 0)
            demand = demand_by_type.get(resource_type, 0)
            deficit = max(0, demand - available)
            
            if deficit > 0:
                shortages[resource_type] = {
                    'deficit': deficit,
                    'available': available,
                    'demand': demand,
                    'severity': 'CRITICAL' if deficit > available * 2 else 'HIGH',
                }
        
        return {
            'resource_levels': resource_levels,
            'demand': demand_by_type,
            'shortages': shortages,
            'monitored_at': datetime.now().isoformat(),
        }
    
    async def identify_critical_shortages(self) -> List[Dict[str, Any]]:
        """
        Identify critical resource shortages before they become emergencies.
        
        Returns:
            List of critical shortages with recommendations
        """
        api_logger.info("Resource agent: Identifying critical shortages")
        
        # Get locations with active outbreaks
        outbreak_result = await self.session.execute(
            select(OutbreakEvent)
            .where(OutbreakEvent.timestamp >= datetime.now() - timedelta(days=7))
            .order_by(OutbreakEvent.severity.desc())
        )
        outbreaks = outbreak_result.scalars().all()
        
        critical_shortages = []
        
        for outbreak in outbreaks:
            location_id = outbreak.location_id
            
            # Predict resource needs for this location
            predictions = await self.matching_engine.predict_future_needs(
                str(location_id),
                days_ahead=7
            )
            
            # Check current availability
            # Get requests for this location
            req_result = await self.session.execute(
                select(ResourceRequest)
                .where(ResourceRequest.location_id == location_id)
                .where(ResourceRequest.status == "OPEN")
            )
            location_requests = req_result.scalars().all()
            
            # Check for critical shortages
            for resource_type, predicted_need in predictions.get('predicted_needs', {}).items():
                # Get current requests for this resource type
                current_demand = sum(
                    req.quantity_needed - req.quantity_fulfilled
                    for req in location_requests
                    if req.resource_type.value == resource_type
                )
                
                total_need = predicted_need + current_demand
                
                # Get available supply
                inv_result = await self.session.execute(
                    select(func.sum(ResourceInventory.quantity_available))
                    .where(ResourceInventory.resource_type == ResourceType[resource_type])
                    .where(ResourceInventory.is_active == True)
                )
                available = inv_result.scalar() or 0
                
                if total_need > available * 1.5:  # 50% deficit threshold
                    critical_shortages.append({
                        'location_id': str(location_id),
                        'resource_type': resource_type,
                        'predicted_need': predicted_need,
                        'current_demand': current_demand,
                        'available': available,
                        'deficit': total_need - available,
                        'severity': 'CRITICAL',
                        'recommendation': 'Immediate procurement or reallocation needed',
                    })
        
        return critical_shortages
    
    async def auto_match_requests(self) -> Dict[str, Any]:
        """
        Automatically match resource requests.
        
        Returns:
            Matching results
        """
        api_logger.info("Resource agent: Auto-matching requests")
        
        matches = await self.matching_engine.match_requests_to_inventory(
            auto_accept_threshold=85.0  # High threshold for auto-accept
        )
        
        return {
            'matches_created': len(matches),
            'auto_accepted': len([m for m in matches if m.status == MatchStatus.ACCEPTED]),
            'matches': [
                {
                    'id': str(m.id),
                    'request_id': str(m.request_id),
                    'match_score': m.match_score,
                    'status': m.status.value,
                }
                for m in matches
            ],
        }
    
    async def suggest_reallocation(self) -> List[Dict[str, Any]]:
        """
        Suggest resource reallocation between facilities.
        
        Returns:
            List of reallocation suggestions
        """
        api_logger.info("Resource agent: Suggesting reallocations")
        
        # Get locations with surplus and deficit
        # This is a simplified version - full implementation would use optimization
        
        suggestions = []
        
        # Get all locations
        loc_result = await self.session.execute(select(Location))
        locations = loc_result.scalars().all()
        
        # For each location, check resource balance
        for location in locations:
            # Get requests
            req_result = await self.session.execute(
                select(ResourceRequest)
                .where(ResourceRequest.location_id == location.id)
                .where(ResourceRequest.status == "OPEN")
            )
            requests = req_result.scalars().all()
            
            # Get inventory at this location
            prov_result = await self.session.execute(
                select(ResourceProvider)
                .where(ResourceProvider.location_id == location.id)
            )
            providers = prov_result.scalars().all()
            
            provider_ids = [str(p.id) for p in providers]
            
            if provider_ids:
                inv_result = await self.session.execute(
                    select(ResourceInventory)
                    .where(ResourceInventory.provider_id.in_(provider_ids))
                    .where(ResourceInventory.is_active == True)
                )
                inventory = inv_result.scalars().all()
                
                # Check for imbalances
                for req in requests:
                    available = sum(
                        inv.quantity_available - inv.quantity_reserved
                        for inv in inventory
                        if inv.resource_type == req.resource_type
                    )
                    
                    needed = req.quantity_needed - req.quantity_fulfilled
                    
                    if needed > available * 1.2:  # 20% deficit
                        suggestions.append({
                            'location_id': str(location.id),
                            'location_name': location.name,
                            'resource_type': req.resource_type.value,
                            'deficit': needed - available,
                            'suggestion': f'Reallocate from nearby locations with surplus',
                        })
        
        return suggestions
    
    async def trigger_procurement(self, resource_type: str, quantity: int, location_id: str) -> Dict[str, Any]:
        """
        Trigger procurement order for resources.
        
        Args:
            resource_type: Type of resource needed
            quantity: Quantity needed
            location_id: Location ID
            
        Returns:
            Procurement order details
        """
        api_logger.info(f"Resource agent: Triggering procurement for {quantity} {resource_type}")
        
        # Create urgent request for procurement
        # Find a procurement provider or create system request
        
        # For now, return placeholder
        return {
            'resource_type': resource_type,
            'quantity': quantity,
            'location_id': location_id,
            'status': 'PROCUREMENT_ORDERED',
            'estimated_delivery': (datetime.now() + timedelta(days=7)).isoformat(),
            'message': 'Procurement order created',
        }
    
    async def coordinate_emergency_airlift(self, resource_type: str, from_location_id: str, to_location_id: str, quantity: int) -> Dict[str, Any]:
        """
        Coordinate emergency resource airlift.
        
        Args:
            resource_type: Type of resource
            from_location_id: Source location
            to_location_id: Destination location
            quantity: Quantity to transport
            
        Returns:
            Airlift coordination details
        """
        api_logger.info(f"Resource agent: Coordinating emergency airlift for {quantity} {resource_type}")
        
        # This would integrate with logistics providers
        # For now, return placeholder
        
        return {
            'resource_type': resource_type,
            'from_location_id': from_location_id,
            'to_location_id': to_location_id,
            'quantity': quantity,
            'status': 'AIRLIFT_COORDINATED',
            'estimated_arrival': (datetime.now() + timedelta(hours=24)).isoformat(),
            'message': 'Emergency airlift coordinated',
        }
    
    async def run_cycle(self) -> Dict[str, Any]:
        """
        Run a complete agent cycle.
        
        Performs all monitoring and coordination tasks.
        
        Returns:
            Cycle results
        """
        api_logger.info("Resource agent: Running coordination cycle")
        
        results = {
            'monitoring': await self.monitor_resource_levels(),
            'critical_shortages': await self.identify_critical_shortages(),
            'auto_matches': await self.auto_match_requests(),
            'reallocation_suggestions': await self.suggest_reallocation(),
            'cycle_completed_at': datetime.now().isoformat(),
        }
        
        # Take action on critical shortages
        for shortage in results['critical_shortages']:
            if shortage['severity'] == 'CRITICAL':
                api_logger.warning(
                    f"CRITICAL SHORTAGE: {shortage['resource_type']} at location {shortage['location_id']}"
                )
                # Trigger procurement or reallocation
        
        return results

