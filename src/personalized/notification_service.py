"""
Notification Service - EpiSPY Personalized Risk

Manages notifications for personalized risk system with smart timing,
multiple channels, and privacy considerations.
"""

from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from ..database.resource_models import (
    UserProfile, NotificationPreferences, ExposureEvent
)
from ..utils.logger import api_logger


class NotificationType(str, Enum):
    """Notification types."""
    RISK_LEVEL_CHANGE = "RISK_LEVEL_CHANGE"
    EXPOSURE_ALERT = "EXPOSURE_ALERT"
    LOCATION_WARNING = "LOCATION_WARNING"
    POLICY_CHANGE = "POLICY_CHANGE"
    TESTING_RECOMMENDATION = "TESTING_RECOMMENDATION"
    VACCINATION_REMINDER = "VACCINATION_REMINDER"
    CRITICAL_ALERT = "CRITICAL_ALERT"


class NotificationChannel(str, Enum):
    """Notification channels."""
    PUSH = "PUSH"
    SMS = "SMS"
    EMAIL = "EMAIL"
    IN_APP = "IN_APP"


class NotificationManager:
    """
    Manages personalized risk notifications.
    
    Handles:
    - Multi-channel delivery (push, SMS, email)
    - Smart timing (quiet hours, rate limiting)
    - Priority-based delivery
    - Privacy-preserving notifications
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize notification manager.
        
        Args:
            session: Database session
        """
        self.session = session
        self.max_daily_notifications = 3
        self.quiet_hours = (22, 7)  # 10 PM to 7 AM
    
    async def send_notification(
        self,
        user_id: str,
        notification_type: NotificationType,
        title: str,
        message: str,
        priority: str = "NORMAL",
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send notification to user.
        
        Args:
            user_id: User identifier
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            priority: Priority level (LOW, NORMAL, HIGH, CRITICAL)
            data: Additional data payload
            
        Returns:
            True if notification was sent, False otherwise
        """
        # Get user preferences
        prefs = await self._get_notification_preferences(user_id)
        
        if not prefs:
            api_logger.warning(f"No notification preferences for user {user_id}")
            return False
        
        # Check if should send (quiet hours, rate limiting)
        if not await self._should_send_notification(user_id, priority, prefs):
            api_logger.info(f"Notification suppressed for user {user_id} (quiet hours or rate limit)")
            return False
        
        # Determine channels
        channels = self._get_channels_for_notification(notification_type, priority, prefs)
        
        if not channels:
            return False
        
        # Send via each channel
        sent = False
        for channel in channels:
            try:
                await self._send_via_channel(user_id, channel, title, message, data)
                sent = True
            except Exception as e:
                api_logger.error(f"Failed to send {channel} notification: {str(e)}")
        
        if sent:
            # Track notification
            await self._track_notification(user_id, notification_type, priority)
        
        return sent
    
    async def _get_notification_preferences(
        self,
        user_id: str
    ) -> Optional[NotificationPreferences]:
        """Get user notification preferences."""
        result = await self.session.execute(
            select(NotificationPreferences).where(
                NotificationPreferences.user_id == user_id
            )
        )
        return result.scalar_one_or_none()
    
    async def _should_send_notification(
        self,
        user_id: str,
        priority: str,
        prefs: NotificationPreferences
    ) -> bool:
        """Check if notification should be sent."""
        # Critical alerts always send
        if priority == "CRITICAL":
            return True
        
        # Check quiet hours
        if prefs.quiet_hours_start and prefs.quiet_hours_end:
            current_hour = datetime.now().hour
            start = prefs.quiet_hours_start
            end = prefs.quiet_hours_end
            
            if start > end:  # Overnight quiet hours
                if current_hour >= start or current_hour < end:
                    return False
            else:
                if start <= current_hour < end:
                    return False
        
        # Check daily limit
        # TODO: Implement daily notification count tracking
        # For now, use preference setting
        if prefs.max_daily_notifications:
            # Would check actual count here
            pass
        
        return True
    
    def _get_channels_for_notification(
        self,
        notification_type: NotificationType,
        priority: str,
        prefs: NotificationPreferences
    ) -> List[NotificationChannel]:
        """Determine which channels to use for notification."""
        channels = []
        
        # Critical alerts use all enabled channels
        if priority == "CRITICAL":
            if prefs.push_enabled:
                channels.append(NotificationChannel.PUSH)
            if prefs.sms_enabled:
                channels.append(NotificationChannel.SMS)
            if prefs.email_enabled:
                channels.append(NotificationChannel.EMAIL)
            channels.append(NotificationChannel.IN_APP)
            return channels
        
        # Normal priority uses preferred channels
        if prefs.push_enabled:
            channels.append(NotificationChannel.PUSH)
        if prefs.email_enabled:
            channels.append(NotificationChannel.EMAIL)
        channels.append(NotificationChannel.IN_APP)
        
        # SMS only for high priority
        if priority == "HIGH" and prefs.sms_enabled:
            channels.append(NotificationChannel.SMS)
        
        return channels
    
    async def _send_via_channel(
        self,
        user_id: str,
        channel: NotificationChannel,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]]
    ):
        """Send notification via specific channel."""
        # TODO: Integrate with actual notification services
        # - Firebase Cloud Messaging for push
        # - Twilio for SMS
        # - SendGrid/SES for email
        
        api_logger.info(
            f"Sending {channel.value} notification to user {user_id}: {title}"
        )
        
        # Placeholder implementation
        if channel == NotificationChannel.PUSH:
            # await send_push_notification(user_id, title, message, data)
            pass
        elif channel == NotificationChannel.SMS:
            # await send_sms_notification(user_id, message)
            pass
        elif channel == NotificationChannel.EMAIL:
            # await send_email_notification(user_id, title, message)
            pass
        elif channel == NotificationChannel.IN_APP:
            # Store in database for in-app display
            pass
    
    async def _track_notification(
        self,
        user_id: str,
        notification_type: NotificationType,
        priority: str
    ):
        """Track notification for analytics and rate limiting."""
        # TODO: Store in notification_log table
        pass
    
    async def notify_risk_level_change(
        self,
        user_id: str,
        old_level: str,
        new_level: str,
        score: float
    ):
        """Send notification when risk level changes."""
        if old_level == new_level:
            return
        
        priority = "HIGH" if new_level in ["HIGH", "CRITICAL"] else "NORMAL"
        
        title = f"Risk Level Changed: {new_level}"
        message = (
            f"Your risk level has changed from {old_level} to {new_level}. "
            f"Current risk score: {score:.1f}/100. "
            "Check the app for personalized recommendations."
        )
        
        await self.send_notification(
            user_id=user_id,
            notification_type=NotificationType.RISK_LEVEL_CHANGE,
            title=title,
            message=message,
            priority=priority,
            data={'old_level': old_level, 'new_level': new_level, 'score': score}
        )
    
    async def notify_exposure(
        self,
        user_id: str,
        exposure_date: datetime,
        risk_level: str
    ):
        """Send exposure alert notification."""
        days_ago = (datetime.now() - exposure_date).days
        
        title = "Potential Exposure Detected"
        message = (
            f"A potential exposure was detected {days_ago} day(s) ago. "
            f"Risk level: {risk_level}. "
            "Please get tested and monitor symptoms."
        )
        
        await self.send_notification(
            user_id=user_id,
            notification_type=NotificationType.EXPOSURE_ALERT,
            title=title,
            message=message,
            priority="HIGH",
            data={'exposure_date': exposure_date.isoformat(), 'risk_level': risk_level}
        )

