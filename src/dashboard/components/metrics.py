"""Metrics display components."""
import streamlit as st
from typing import Dict, Any

def display_key_metrics(data: Dict[str, Any]):
    """Display key system metrics."""
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        risk_score = data.get('current_risk_score', 0)
        risk_delta = calculate_risk_delta(risk_score)
        
        st.metric(
            "Overall Risk Score",
            f"{risk_score:.1f}/10",
            delta=f"{risk_delta:+.1f}",
            delta_color="inverse"  # Red for increase, green for decrease
        )
    
    with col2:
        active_cases = data.get('active_cases', 0)
        case_delta = calculate_case_delta(active_cases)
        
        st.metric(
            "Active Cases",
            f"{active_cases:,}",
            delta=f"{case_delta:+d}",
            delta_color="inverse"
        )
    
    with col3:
        alert_level = data.get('alert_level', 'LOW')
        alert_color = get_alert_color(alert_level)
        
        st.markdown(
            f"""
            <div style="text-align: center;">
                <h3 style="margin: 0; font-size: 14px; color: #666;">Alert Level</h3>
                <div style="
                    background-color: {alert_color}; 
                    color: white; 
                    padding: 10px; 
                    border-radius: 5px; 
                    font-size: 24px; 
                    font-weight: bold;
                    margin-top: 5px;
                ">
                    {alert_level}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with col4:
        trend = data.get('trend', 'STABLE')
        trend_icon = get_trend_icon(trend)
        
        st.markdown(
            f"""
            <div style="text-align: center;">
                <h3 style="margin: 0; font-size: 14px; color: #666;">Trend</h3>
                <div style="font-size: 24px; margin-top: 10px;">
                    {trend_icon} {trend}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

def calculate_risk_delta(current_risk: float) -> float:
    """Calculate risk score change (simulated)."""
    # In real implementation, this would compare with historical data
    import random
    return random.uniform(-1.0, 1.0)

def calculate_case_delta(current_cases: int) -> int:
    """Calculate case count change (simulated)."""
    # In real implementation, this would compare with historical data
    import random
    return random.randint(-10, 15)

def get_alert_color(alert_level: str) -> str:
    """Get color for alert level."""
    colors = {
        'LOW': '#28a745',
        'MEDIUM': '#ffc107',
        'HIGH': '#fd7e14',
        'CRITICAL': '#dc3545'
    }
    return colors.get(alert_level, '#6c757d')

def get_trend_icon(trend: str) -> str:
    """Get icon for trend direction."""
    icons = {
        'INCREASING': '📈',
        'STABLE': '➡️',
        'DECREASING': '📉'
    }
    return icons.get(trend, '➡️')

def display_location_metrics(location_data: Dict[str, Any]):
    """Display metrics for specific location."""
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Risk Score",
            f"{location_data.get('risk_score', 0):.1f}/10",
            delta=f"{location_data.get('risk_change', 0):+.1f}"
        )
    
    with col2:
        st.metric(
            "Cases",
            location_data.get('active_cases', 0),
            delta=location_data.get('case_change', 0)
        )
    
    with col3:
        capacity = location_data.get('bed_capacity', 100)
        occupied = location_data.get('beds_occupied', 50)
        utilization = (occupied / capacity) * 100 if capacity > 0 else 0
        
        st.metric(
            "Bed Utilization",
            f"{utilization:.0f}%",
            delta=f"{location_data.get('utilization_change', 0):+.0f}%"
        )

def display_prediction_metrics(prediction_data: Dict[str, Any]):
    """Display prediction-specific metrics."""
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        prob = prediction_data.get('outbreak_probability', 0)
        st.metric(
            "Outbreak Probability",
            f"{prob:.1%}",
            delta=f"{prediction_data.get('prob_change', 0):+.1%}"
        )
    
    with col2:
        peak_cases = prediction_data.get('predicted_peak_cases', 0)
        st.metric(
            "Predicted Peak",
            f"{peak_cases:,} cases",
            delta=f"{prediction_data.get('peak_change', 0):+,}"
        )
    
    with col3:
        confidence = prediction_data.get('confidence_score', 0)
        confidence_color = "normal" if confidence > 0.7 else "off"
        
        st.metric(
            "Model Confidence",
            f"{confidence:.1%}",
            delta=f"{prediction_data.get('confidence_change', 0):+.1%}",
            delta_color=confidence_color
        )
