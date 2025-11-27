"""
Background tasks for Resource Marketplace.

Celery tasks for automated resource matching, predictions, and notifications.
"""

from celery import shared_task
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ..database.connection import get_async_session
from ..database.resource_models import (
    ResourceRequest, ResourceInventory, ResourceMatch, ResourceTransfer,
    TransferStatus, MatchStatus, ResourceType
)
from ..marketplace.matching_engine import ResourceMatchingEngine
from ..utils.logger import api_logger


@shared_task(name="marketplace.auto_match_resources")
def auto_match_resources():
    """
    Automatically match resource requests with available inventory.
    
    Runs every 5 minutes to find matches for open requests.
    """
    api_logger.info("Starting automatic resource matching")
    
    async def _match():
        async with get_async_session() as session:
            engine = ResourceMatchingEngine(session)
            matches = await engine.match_requests_to_inventory()
            api_logger.info(f"Created {len(matches)} matches")
            return len(matches)
    
    # Run async function
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(_match())


@shared_task(name="marketplace.predict_resource_needs")
def predict_resource_needs():
    """
    Predict future resource needs based on outbreak forecasts.
    
    Runs daily to generate resource demand predictions.
    """
    api_logger.info("Starting resource need predictions")
    
    async def _predict():
        async with get_async_session() as session:
            from ..database.models import Location
            
            # Get all locations with active outbreaks
            result = await session.execute(
                select(Location).distinct()
            )
            locations = result.scalars().all()
            
            engine = ResourceMatchingEngine(session)
            predictions = []
            
            for location in locations:
                try:
                    pred = await engine.predict_future_needs(
                        str(location.id),
                        days_ahead=14
                    )
                    predictions.append(pred)
                except Exception as e:
                    api_logger.error(f"Error predicting for location {location.id}: {str(e)}")
            
            api_logger.info(f"Generated {len(predictions)} predictions")
            return len(predictions)
    
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(_predict())


@shared_task(name="marketplace.send_match_notifications")
def send_match_notifications():
    """
    Send notifications for new matches.
    
    Runs every minute to notify users of new matches.
    """
    api_logger.info("Sending match notifications")
    
    async def _notify():
        async with get_async_session() as session:
            # Get matches created in last 5 minutes that haven't been notified
            cutoff = datetime.now() - timedelta(minutes=5)
            
            result = await session.execute(
                select(ResourceMatch)
                .where(ResourceMatch.status == MatchStatus.PENDING)
                .where(ResourceMatch.created_at >= cutoff)
            )
            matches = result.scalars().all()
            
            # TODO: Send notifications via notification service
            api_logger.info(f"Found {len(matches)} new matches to notify")
            
            return len(matches)
    
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(_notify())


@shared_task(name="marketplace.update_transfer_status")
def update_transfer_status():
    """
    Update transfer statuses and track logistics.
    
    Runs every 15 minutes to update transfer statuses.
    """
    api_logger.info("Updating transfer statuses")
    
    async def _update():
        async with get_async_session() as session:
            # Get transfers in transit
            result = await session.execute(
                select(ResourceTransfer)
                .where(ResourceTransfer.status == TransferStatus.IN_TRANSIT)
            )
            transfers = result.scalars().all()
            
            # TODO: Integrate with logistics APIs to get real-time status
            # For now, mark as delivered if ETA has passed
            updated = 0
            for transfer in transfers:
                if transfer.estimated_arrival and transfer.estimated_arrival < datetime.now():
                    transfer.status = TransferStatus.DELIVERED
                    transfer.actual_arrival = datetime.now()
                    updated += 1
            
            if updated > 0:
                await session.commit()
                api_logger.info(f"Updated {updated} transfers to delivered")
            
            return updated
    
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(_update())


@shared_task(name="marketplace.generate_marketplace_analytics")
def generate_marketplace_analytics():
    """
    Generate daily marketplace analytics.
    
    Runs daily to generate supply-demand analytics.
    """
    api_logger.info("Generating marketplace analytics")
    
    async def _generate():
        async with get_async_session() as session:
            from sqlalchemy import select, func
            
            # Calculate supply-demand metrics by resource type
            analytics = {}
            
            # Get all resource types
            from ..database.resource_models import ResourceType
            
            for resource_type in ResourceType:
                # Total supply
                supply_result = await session.execute(
                    select(func.sum(ResourceInventory.quantity_available))
                    .where(ResourceInventory.resource_type == resource_type)
                    .where(ResourceInventory.is_active == True)
                )
                total_supply = supply_result.scalar() or 0
                
                # Total demand
                demand_result = await session.execute(
                    select(func.sum(ResourceRequest.quantity_needed))
                    .where(ResourceRequest.resource_type == resource_type)
                    .where(ResourceRequest.status == "OPEN")
                )
                total_demand = demand_result.scalar() or 0
                
                # Match rate
                match_result = await session.execute(
                    select(func.count(ResourceMatch.id))
                    .where(ResourceMatch.status == MatchStatus.ACCEPTED)
                )
                matches = match_result.scalar() or 0
                
                analytics[resource_type.value] = {
                    "total_supply": total_supply,
                    "total_demand": total_demand,
                    "deficit": max(0, total_demand - total_supply),
                    "match_rate": matches,
                }
            
            api_logger.info(f"Generated analytics for {len(analytics)} resource types")
            return analytics
    
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(_generate())


@shared_task(name="marketplace.expire_old_listings")
def expire_old_listings():
    """
    Expire old inventory listings.
    
    Runs daily to deactivate expired listings.
    """
    api_logger.info("Expiring old listings")
    
    async def _expire():
        async with get_async_session() as session:
            # Get listings that expired more than 7 days ago
            cutoff = datetime.now() - timedelta(days=7)
            
            result = await session.execute(
                select(ResourceInventory)
                .where(ResourceInventory.expiry_date < cutoff)
                .where(ResourceInventory.is_active == True)
            )
            expired = result.scalars().all()
            
            count = 0
            for item in expired:
                item.is_active = False
                count += 1
            
            if count > 0:
                await session.commit()
                api_logger.info(f"Expired {count} listings")
            
            return count
    
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(_expire())

