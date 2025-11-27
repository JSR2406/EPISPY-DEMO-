"""Alert display components for the dashboard."""
import streamlit as st
import requests
from datetime import datetime
from typing import List, Dict, Optional


def display_recent_alerts(limit: int = 5) -> None:
    """
    Display recent alerts from the system.
    
    Args:
        limit: Maximum number of alerts to display
    """
    alerts = fetch_alerts(limit)
    
    if not alerts:
        st.info("No recent alerts")
        return
    
    for alert in alerts:
        severity = alert.get('severity', 'MEDIUM')
        alert_type = alert.get('alert_type', 'GENERAL')
        message = alert.get('message', 'No message')
        timestamp = alert.get('created_at', datetime.now().isoformat())
        location = alert.get('location', 'Unknown')
        
        # Color based on severity
        if severity == 'CRITICAL':
            color = '#dc3545'
            icon = '🚨'
        elif severity == 'HIGH':
            color = '#fd7e14'
            icon = '⚠️'
        elif severity == 'MEDIUM':
            color = '#ffc107'
            icon = '⚡'
        else:
            color = '#28a745'
            icon = 'ℹ️'
        
        # Display alert
        with st.container():
            st.markdown(
                f"""
                <div style='
                    border-left: 4px solid {color};
                    padding: 10px;
                    margin: 10px 0;
                    background-color: rgba(0,0,0,0.05);
                    border-radius: 5px;
                '>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <div>
                            <strong>{icon} {alert_type}</strong><br>
                            <span style='font-size: 0.9em;'>{message}</span><br>
                            <span style='font-size: 0.8em; color: #666;'>📍 {location} • {format_timestamp(timestamp)}</span>
                        </div>
                        <div style='
                            background-color: {color};
                            color: white;
                            padding: 5px 10px;
                            border-radius: 3px;
                            font-size: 0.8em;
                            font-weight: bold;
                        '>
                            {severity}
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )


def fetch_alerts(limit: int = 5) -> List[Dict]:
    """
    Fetch alerts from the API.
    
    Args:
        limit: Maximum number of alerts to fetch
        
    Returns:
        List of alert dictionaries
    """
    try:
        response = requests.get(
            f"http://localhost:8000/api/v1/alerts",
            params={'limit': limit},
            timeout=5
        )
        if response.status_code == 200:
            return response.json().get('alerts', [])
    except:
        pass
    
    # Return sample alerts if API unavailable
    return get_sample_alerts(limit)


def get_sample_alerts(limit: int = 5) -> List[Dict]:
    """
    Generate sample alerts for demonstration.
    
    Args:
        limit: Maximum number of alerts to generate
        
    Returns:
        List of sample alert dictionaries
    """
    sample_alerts = [
        {
            'alert_id': 'ALT001',
            'alert_type': 'OUTBREAK_WARNING',
            'severity': 'HIGH',
            'location': 'Rural Hospital A',
            'message': 'Unusual spike in respiratory symptoms detected',
            'created_at': datetime.now().isoformat(),
            'status': 'active'
        },
        {
            'alert_id': 'ALT002',
            'alert_type': 'RISK_INCREASE',
            'severity': 'MEDIUM',
            'location': 'Mobile Unit D',
            'message': 'Risk score increased by 15% in the last 6 hours',
            'created_at': datetime.now().isoformat(),
            'status': 'active'
        },
        {
            'alert_id': 'ALT003',
            'alert_type': 'PATTERN_DETECTED',
            'severity': 'MEDIUM',
            'location': 'Health Center B',
            'message': 'Similar symptom pattern detected across multiple patients',
            'created_at': datetime.now().isoformat(),
            'status': 'active'
        },
        {
            'alert_id': 'ALT004',
            'alert_type': 'GEOGRAPHIC_CLUSTER',
            'severity': 'HIGH',
            'location': 'Rural Hospital F',
            'message': 'Geographic clustering of cases detected',
            'created_at': datetime.now().isoformat(),
            'status': 'active'
        },
        {
            'alert_id': 'ALT005',
            'alert_type': 'SYSTEM_INFO',
            'severity': 'LOW',
            'location': 'System',
            'message': 'Daily analysis completed successfully',
            'created_at': datetime.now().isoformat(),
            'status': 'resolved'
        }
    ]
    
    return sample_alerts[:limit]


def format_timestamp(timestamp_str: str) -> str:
    """
    Format timestamp for display.
    
    Args:
        timestamp_str: ISO format timestamp string
        
    Returns:
        Formatted timestamp string
    """
    try:
        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        now = datetime.now()
        diff = now - timestamp.replace(tzinfo=None)
        
        if diff.seconds < 60:
            return 'Just now'
        elif diff.seconds < 3600:
            minutes = diff.seconds // 60
            return f'{minutes}m ago'
        elif diff.seconds < 86400:
            hours = diff.seconds // 3600
            return f'{hours}h ago'
        else:
            days = diff.days
            return f'{days}d ago'
    except:
        return 'Recently'


def create_alert_summary(alerts: List[Dict]) -> Dict[str, int]:
    """
    Create a summary of alerts by severity.
    
    Args:
        alerts: List of alert dictionaries
        
    Returns:
        Dictionary with counts by severity
    """
    summary = {
        'CRITICAL': 0,
        'HIGH': 0,
        'MEDIUM': 0,
        'LOW': 0
    }
    
    for alert in alerts:
        severity = alert.get('severity', 'LOW')
        if severity in summary:
            summary[severity] += 1
    
    return summary
