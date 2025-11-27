"""
Mental health alert system for detecting and managing mental health hotspots.

This module provides alert generation, management, and integration with the
main epidemic monitoring system.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from ..utils.logger import api_logger
from .models import (
    MentalHealthHotspot,
    MentalHealthSeverity,
    MentalHealthIndicator,
    Alert as MentalHealthAlert
)
from ..database.models import Alert, AlertSeverity, AlertStatus, Location


@dataclass
class AlertRecommendation:
    """Alert recommendation from hotspot analysis."""
    should_alert: bool
    severity: AlertSeverity
    message: str
    hotspot_id: str
    location_id: str
    recommended_actions: List[str]
    resource_ids: List[str]


class MentalHealthAlertSystem:
    """Alert system for mental health hotspots."""
    
    def __init__(self, threshold_severe: float = 6.0, threshold_critical: float = 8.0):
        """
        Initialize alert system.
        
        Args:
            threshold_severe: Hotspot score threshold for SEVERE alerts
            threshold_critical: Hotspot score threshold for CRITICAL alerts
        """
        self.threshold_severe = threshold_severe
        self.threshold_critical = threshold_critical
    
    def evaluate_hotspot_for_alert(
        self,
        hotspot: MentalHealthHotspot,
        resource_recommendations: Optional[List[str]] = None
    ) -> AlertRecommendation:
        """
        Evaluate hotspot and determine if alert should be generated.
        
        Args:
            hotspot: Mental health hotspot to evaluate
            resource_recommendations: Optional list of resource IDs to recommend
            
        Returns:
            Alert recommendation
        """
        should_alert = False
        severity = AlertSeverity.INFO
        
        # Determine alert severity based on hotspot score
        if hotspot.hotspot_score >= self.threshold_critical:
            should_alert = True
            severity = AlertSeverity.CRITICAL
        elif hotspot.hotspot_score >= self.threshold_severe:
            should_alert = True
            severity = AlertSeverity.SEVERE
        elif hotspot.hotspot_score >= 4.0:
            should_alert = True
            severity = AlertSeverity.WARNING
        else:
            should_alert = False
            severity = AlertSeverity.INFO
        
        # Build alert message
        message = self._build_alert_message(hotspot, severity)
        
        # Generate recommended actions
        recommended_actions = self._generate_recommended_actions(hotspot, severity)
        
        return AlertRecommendation(
            should_alert=should_alert,
            severity=severity,
            message=message,
            hotspot_id=str(hotspot.id),
            location_id=str(hotspot.location_id),
            recommended_actions=recommended_actions,
            resource_ids=resource_recommendations or []
        )
    
    def _build_alert_message(
        self,
        hotspot: MentalHealthHotspot,
        severity: AlertSeverity
    ) -> str:
        """Build alert message from hotspot data."""
        location_name = "Unknown Location"
        if hotspot.location:
            location_name = hotspot.location.name
        
        indicators_str = ", ".join(hotspot.primary_indicators[:3])
        
        severity_prefix = {
            AlertSeverity.CRITICAL: "🚨 CRITICAL",
            AlertSeverity.SEVERE: "⚠️ SEVERE",
            AlertSeverity.WARNING: "⚠️ WARNING",
            AlertSeverity.INFO: "ℹ️ INFO"
        }.get(severity, "ℹ️")
        
        message = (
            f"{severity_prefix} Mental Health Hotspot Detected\n\n"
            f"Location: {location_name}\n"
            f"Hotspot Score: {hotspot.hotspot_score:.1f}/10\n"
            f"Severity: {hotspot.severity.value}\n"
            f"Primary Indicators: {indicators_str}\n"
            f"Affected Population Estimate: {hotspot.affected_population_estimate:,}\n"
            f"Trend: {hotspot.trend}\n"
        )
        
        if hotspot.contributing_factors:
            factors = hotspot.contributing_factors
            if "cluster_size" in factors:
                message += f"\nCluster Size: {factors['cluster_size']} data points\n"
            if "average_crisis_score" in factors:
                message += f"Average Crisis Score: {factors['average_crisis_score']:.1f}/10\n"
        
        return message
    
    def _generate_recommended_actions(
        self,
        hotspot: MentalHealthHotspot,
        severity: AlertSeverity
    ) -> List[str]:
        """Generate recommended actions based on hotspot."""
        actions = []
        
        # Base actions for all hotspots
        actions.append("Increase mental health resource availability in affected area")
        actions.append("Coordinate with local healthcare providers")
        
        # Severity-specific actions
        if severity in [AlertSeverity.SEVERE, AlertSeverity.CRITICAL]:
            actions.append("Activate crisis response team")
            actions.append("Increase hotline capacity")
            actions.append("Deploy mobile mental health units if available")
            
            if "CRISIS" in hotspot.primary_indicators or "SUICIDAL_IDEATION" in hotspot.primary_indicators:
                actions.append("Implement suicide prevention protocols")
                actions.append("Coordinate with emergency services")
        
        # Indicator-specific actions
        if MentalHealthIndicator.ANXIETY in hotspot.primary_indicators:
            actions.append("Provide anxiety management resources and information")
        
        if MentalHealthIndicator.DEPRESSION in hotspot.primary_indicators:
            actions.append("Increase depression screening and support services")
        
        if MentalHealthIndicator.SUBSTANCE_ABUSE in hotspot.primary_indicators:
            actions.append("Coordinate with substance abuse treatment centers")
        
        # Trend-based actions
        if hotspot.trend == "INCREASING":
            actions.append("Monitor trend closely and prepare for escalation")
            actions.append("Pre-position additional resources")
        
        return actions
    
    async def create_alert_from_hotspot(
        self,
        hotspot: MentalHealthHotspot,
        db_session,
        resource_ids: Optional[List[str]] = None
    ) -> Alert:
        """
        Create alert in database from hotspot.
        
        Args:
            hotspot: Mental health hotspot
            db_session: Database session
            resource_ids: Optional resource IDs to include in alert
            
        Returns:
            Created Alert instance
        """
        recommendation = self.evaluate_hotspot_for_alert(hotspot, resource_ids)
        
        if not recommendation.should_alert:
            api_logger.info(f"Hotspot {hotspot.id} does not meet alert threshold")
            return None
        
        # Get location name
        location_name = "Unknown Location"
        if hotspot.location:
            location_name = hotspot.location.name
        
        # Build alert message with recommendations
        full_message = recommendation.message
        if recommendation.recommended_actions:
            full_message += "\n\nRecommended Actions:\n"
            for i, action in enumerate(recommendation.recommended_actions, 1):
                full_message += f"{i}. {action}\n"
        
        # Determine recipients (in production, would query from config/database)
        recipients = self._get_alert_recipients(hotspot, recommendation.severity)
        
        # Create alert
        alert = Alert(
            location_id=hotspot.location_id,
            severity=recommendation.severity,
            message=full_message,
            status=AlertStatus.ACTIVE,
            recipient_list=recipients
        )
        
        db_session.add(alert)
        
        # Mark hotspot as having generated alert
        hotspot.alert_generated = True
        hotspot.updated_at = datetime.now()
        
        api_logger.info(
            f"Created {recommendation.severity.value} alert for hotspot {hotspot.id} "
            f"in location {location_name}"
        )
        
        return alert
    
    def _get_alert_recipients(
        self,
        hotspot: MentalHealthHotspot,
        severity: AlertSeverity
    ) -> List[str]:
        """
        Get list of alert recipients based on hotspot and severity.
        
        In production, this would query from a configuration or database.
        """
        recipients = []
        
        # Base recipients
        recipients.append("mental_health_team@epispy.local")
        recipients.append("public_health_department@epispy.local")
        
        # Severity-specific recipients
        if severity == AlertSeverity.CRITICAL:
            recipients.append("crisis_response_team@epispy.local")
            recipients.append("emergency_services@epispy.local")
            recipients.append("health_department_director@epispy.local")
        
        # Location-specific recipients (would be looked up in production)
        if hotspot.location:
            # In production, would query location-specific contacts
            recipients.append(f"health_dept_{hotspot.location.name.lower().replace(' ', '_')}@epispy.local")
        
        return recipients


async def process_hotspots_for_alerts(
    hotspots: List[MentalHealthHotspot],
    db_session,
    alert_system: Optional[MentalHealthAlertSystem] = None
) -> List[Alert]:
    """
    Process list of hotspots and generate alerts for those that meet criteria.
    
    Args:
        hotspots: List of mental health hotspots
        db_session: Database session
        alert_system: Optional alert system instance
        
    Returns:
        List of created alerts
    """
    if alert_system is None:
        alert_system = MentalHealthAlertSystem()
    
    created_alerts = []
    
    for hotspot in hotspots:
        # Check if hotspot is active and hasn't already generated alert
        if not hotspot.is_active or hotspot.alert_generated:
            continue
        
        try:
            alert = await alert_system.create_alert_from_hotspot(hotspot, db_session)
            if alert:
                created_alerts.append(alert)
                await db_session.commit()
        except Exception as e:
            api_logger.error(f"Failed to create alert for hotspot {hotspot.id}: {str(e)}")
            await db_session.rollback()
    
    return created_alerts


async def update_hotspot_status(
    hotspot_id: str,
    db_session,
    is_active: bool = False,
    deactivation_reason: Optional[str] = None
) -> bool:
    """
    Update hotspot status (activate/deactivate).
    
    Args:
        hotspot_id: Hotspot ID
        db_session: Database session
        is_active: New active status
        deactivation_reason: Optional reason for deactivation
        
    Returns:
        True if successful
    """
    try:
        from sqlalchemy import select
        result = await db_session.execute(
            select(MentalHealthHotspot).where(MentalHealthHotspot.id == hotspot_id)
        )
        hotspot = result.scalar_one_or_none()
        
        if not hotspot:
            api_logger.warning(f"Hotspot {hotspot_id} not found")
            return False
        
        hotspot.is_active = is_active
        
        if not is_active:
            hotspot.deactivated_date = datetime.now()
            if deactivation_reason:
                if hotspot.metadata_json is None:
                    hotspot.metadata_json = {}
                hotspot.metadata_json["deactivation_reason"] = deactivation_reason
        
        hotspot.updated_at = datetime.now()
        await db_session.commit()
        
        api_logger.info(f"Updated hotspot {hotspot_id} status to active={is_active}")
        return True
        
    except Exception as e:
        api_logger.error(f"Failed to update hotspot status: {str(e)}")
        await db_session.rollback()
        return False

