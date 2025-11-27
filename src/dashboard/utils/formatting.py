"""Formatting utilities for the dashboard."""
from typing import Union


def format_number(value: Union[int, float], decimals: int = 0) -> str:
    """
    Format a number with thousand separators.
    
    Args:
        value: Number to format
        decimals: Number of decimal places
        
    Returns:
        Formatted number string
    """
    if decimals == 0:
        return f"{int(value):,}"
    else:
        return f"{value:,.{decimals}f}"


def format_percentage(value: float, decimals: int = 1) -> str:
    """
    Format a value as a percentage.
    
    Args:
        value: Value to format (0-1 or 0-100)
        decimals: Number of decimal places
        
    Returns:
        Formatted percentage string
    """
    # If value is between 0 and 1, assume it's a decimal
    if 0 <= value <= 1:
        value = value * 100
    
    return f"{value:.{decimals}f}%"


def format_risk_score(score: float) -> str:
    """
    Format a risk score with color coding.
    
    Args:
        score: Risk score (0-10)
        
    Returns:
        Formatted risk score string
    """
    return f"{score:.1f}/10"


def format_delta(value: float, is_percentage: bool = False) -> str:
    """
    Format a delta value with sign.
    
    Args:
        value: Delta value
        is_percentage: Whether to format as percentage
        
    Returns:
        Formatted delta string
    """
    sign = "+" if value >= 0 else ""
    
    if is_percentage:
        return f"{sign}{value:.1f}%"
    else:
        return f"{sign}{value:.1f}"


def format_duration(seconds: int) -> str:
    """
    Format a duration in seconds to human-readable format.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes}m"
    elif seconds < 86400:
        hours = seconds // 3600
        return f"{hours}h"
    else:
        days = seconds // 86400
        return f"{days}d"


def format_bytes(bytes_value: int) -> str:
    """
    Format bytes to human-readable format.
    
    Args:
        bytes_value: Number of bytes
        
    Returns:
        Formatted bytes string
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"


def truncate_text(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def format_location_name(location: str) -> str:
    """
    Format a location name for display.
    
    Args:
        location: Location name
        
    Returns:
        Formatted location name
    """
    # Replace underscores with spaces and title case
    return location.replace('_', ' ').title()


def get_severity_emoji(severity: str) -> str:
    """
    Get emoji for severity level.
    
    Args:
        severity: Severity level
        
    Returns:
        Emoji string
    """
    severity_map = {
        'CRITICAL': '🚨',
        'HIGH': '⚠️',
        'MEDIUM': '⚡',
        'LOW': 'ℹ️',
        'INFO': '📌'
    }
    return severity_map.get(severity.upper(), '❓')


def get_risk_level_text(risk_score: float) -> str:
    """
    Get risk level text based on score.
    
    Args:
        risk_score: Risk score (0-10)
        
    Returns:
        Risk level text
    """
    if risk_score >= 8:
        return "CRITICAL"
    elif risk_score >= 6:
        return "HIGH"
    elif risk_score >= 4:
        return "MEDIUM"
    else:
        return "LOW"


def get_risk_color(risk_score: float) -> str:
    """
    Get color code based on risk score.
    
    Args:
        risk_score: Risk score (0-10)
        
    Returns:
        Hex color code
    """
    if risk_score >= 8:
        return '#dc3545'  # Red
    elif risk_score >= 6:
        return '#fd7e14'  # Orange
    elif risk_score >= 4:
        return '#ffc107'  # Yellow
    else:
        return '#28a745'  # Green
