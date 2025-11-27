"""Session state management for the dashboard."""
import streamlit as st
from datetime import datetime


def initialize_session_state():
    """Initialize session state variables."""
    
    # Last refresh timestamp
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = datetime.now()
    
    # API connection status
    if 'api_connected' not in st.session_state:
        st.session_state.api_connected = False
    
    # Selected location filter
    if 'selected_location' not in st.session_state:
        st.session_state.selected_location = 'All'
    
    # Selected time range
    if 'time_range' not in st.session_state:
        st.session_state.time_range = 'Last 7 days'
    
    # Alert filters
    if 'alert_severity_filter' not in st.session_state:
        st.session_state.alert_severity_filter = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
    
    # Dashboard view mode
    if 'view_mode' not in st.session_state:
        st.session_state.view_mode = 'overview'
    
    # User preferences
    if 'dark_mode' not in st.session_state:
        st.session_state.dark_mode = False
    
    # Data cache
    if 'cached_data' not in st.session_state:
        st.session_state.cached_data = {}
    
    # Cache timestamp
    if 'cache_timestamp' not in st.session_state:
        st.session_state.cache_timestamp = {}


def reset_session_state():
    """Reset all session state variables."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    initialize_session_state()


def update_cache(key: str, data: any):
    """
    Update cached data.
    
    Args:
        key: Cache key
        data: Data to cache
    """
    st.session_state.cached_data[key] = data
    st.session_state.cache_timestamp[key] = datetime.now()


def get_cached_data(key: str, max_age_seconds: int = 300):
    """
    Get cached data if it exists and is not too old.
    
    Args:
        key: Cache key
        max_age_seconds: Maximum age of cache in seconds
        
    Returns:
        Cached data or None if not found or too old
    """
    if key not in st.session_state.cached_data:
        return None
    
    if key not in st.session_state.cache_timestamp:
        return None
    
    cache_age = (datetime.now() - st.session_state.cache_timestamp[key]).total_seconds()
    
    if cache_age > max_age_seconds:
        return None
    
    return st.session_state.cached_data[key]


def clear_cache():
    """Clear all cached data."""
    st.session_state.cached_data = {}
    st.session_state.cache_timestamp = {}
