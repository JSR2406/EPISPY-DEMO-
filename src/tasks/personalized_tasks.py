"""
Background tasks for Personalized Risk System.

Celery tasks for risk recalculation, notifications, and data cleanup.
"""

from celery import shared_task
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database.connection import get_async_session
from ..database.resource_models import UserProfile, RiskHistory, UserLocation, ExposureEvent
from ..personalized.risk_calculator import PersonalizedRiskCalculator
from ..personalized.notification_service import NotificationManager, NotificationType
from ..utils.logger import api_logger


@shared_task(name="personalized.update_all_risk_scores")
def update_all_risk_scores():
    """
    Recalculate risk scores for all users.
    
    Runs daily to update risk assessments.
    """
    api_logger.info("Starting risk score updates for all users")
    
    async def _update():
        async with get_async_session() as session:
            # Get all active profiles
            result = await session.execute(
                select(UserProfile)
            )
            profiles = result.scalars().all()
            
            calculator = PersonalizedRiskCalculator(session)
            notification_manager = NotificationManager(session)
            
            updated = 0
            risk_changes = 0
            
            for profile in profiles:
                try:
                    # Get previous risk score
                    prev_result = await session.execute(
                        select(RiskHistory)
                        .where(RiskHistory.user_id == profile.user_id)
                        .order_by(RiskHistory.date.desc())
                        .limit(1)
                    )
                    prev_risk = prev_result.scalar_one_or_none()
                    old_level = prev_risk.risk_level if prev_risk else None
                    
                    # Calculate new risk
                    new_result = await calculator.calculate_risk_score(profile.user_id)
                    
                    # Check if risk level changed
                    if old_level and old_level != new_result.risk_level:
                        await notification_manager.notify_risk_level_change(
                            profile.user_id,
                            old_level,
                            new_result.risk_level,
                            new_result.total_score
                        )
                        risk_changes += 1
                    
                    updated += 1
                except Exception as e:
                    api_logger.error(f"Error updating risk for user {profile.user_id}: {str(e)}")
            
            api_logger.info(f"Updated {updated} risk scores, {risk_changes} level changes")
            return {"updated": updated, "risk_changes": risk_changes}
    
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(_update())


@shared_task(name="personalized.process_exposure_events")
def process_exposure_events():
    """
    Process potential exposure events and send notifications.
    
    Runs every hour to check for new exposures.
    """
    api_logger.info("Processing exposure events")
    
    async def _process():
        async with get_async_session() as session:
            # Get unprocessed exposure events
            result = await session.execute(
                select(ExposureEvent)
                .where(ExposureEvent.notification_sent == False)
            )
            exposures = result.scalars().all()
            
            notification_manager = NotificationManager(session)
            
            notified = 0
            for exposure in exposures:
                try:
                    await notification_manager.notify_exposure(
                        exposure.user_id,
                        exposure.exposure_date,
                        exposure.risk_level
                    )
                    exposure.notification_sent = True
                    notified += 1
                except Exception as e:
                    api_logger.error(f"Error processing exposure {exposure.id}: {str(e)}")
            
            if notified > 0:
                await session.commit()
                api_logger.info(f"Processed {notified} exposure events")
            
            return notified
    
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(_process())


@shared_task(name="personalized.generate_personalized_reports")
def generate_personalized_reports():
    """
    Generate weekly personalized reports for users.
    
    Runs weekly to generate summary reports.
    """
    api_logger.info("Generating personalized reports")
    
    async def _generate():
        async with get_async_session() as session:
            # Get all active profiles
            result = await session.execute(
                select(UserProfile)
            )
            profiles = result.scalars().all()
            
            generated = 0
            for profile in profiles:
                try:
                    # Get risk history for last 7 days
                    week_ago = datetime.now() - timedelta(days=7)
                    hist_result = await session.execute(
                        select(RiskHistory)
                        .where(RiskHistory.user_id == profile.user_id)
                        .where(RiskHistory.date >= week_ago)
                        .order_by(RiskHistory.date)
                    )
                    history = hist_result.scalars().all()
                    
                    if history:
                        # Generate report summary
                        avg_risk = sum(h.risk_score for h in history) / len(history)
                        risk_trend = "increasing" if len(history) > 1 and history[-1].risk_score > history[0].risk_score else "decreasing"
                        
                        # TODO: Send report via email/notification
                        api_logger.debug(f"Generated report for user {profile.user_id}: avg_risk={avg_risk:.1f}, trend={risk_trend}")
                        generated += 1
                except Exception as e:
                    api_logger.error(f"Error generating report for user {profile.user_id}: {str(e)}")
            
            api_logger.info(f"Generated {generated} reports")
            return generated
    
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(_generate())


@shared_task(name="personalized.cleanup_old_location_data")
def cleanup_old_location_data():
    """
    Clean up old location data for privacy compliance.
    
    Runs daily to delete location data older than retention period.
    """
    api_logger.info("Cleaning up old location data")
    
    async def _cleanup():
        async with get_async_session() as session:
            # Delete location data older than 30 days (privacy compliance)
            cutoff = datetime.now() - timedelta(days=30)
            
            result = await session.execute(
                select(UserLocation)
                .where(UserLocation.timestamp < cutoff)
                .where(UserLocation.is_current == False)
            )
            old_locations = result.scalars().all()
            
            count = 0
            for loc in old_locations:
                await session.delete(loc)
                count += 1
            
            if count > 0:
                await session.commit()
                api_logger.info(f"Deleted {count} old location records")
            
            return count
    
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(_cleanup())

