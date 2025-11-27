"""Main dashboard for epidemic prediction system."""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import requests
import asyncio
import json

# Page configuration
st.set_page_config(
    page_title="Epidemic Prediction AI System",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import custom components
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.metrics import display_key_metrics
from components.charts import create_risk_timeline, create_location_heatmap
from components.alerts import display_recent_alerts
from utils.session_state import initialize_session_state
from utils.formatting import format_number, format_percentage

# Initialize session state
initialize_session_state()

def main():
    """Main dashboard function."""
    
    # Header
    st.title("🏥 Epidemic Prediction AI System")
    st.markdown("**Real-time monitoring and prediction for rural healthcare**")
    
    # Sidebar
    with st.sidebar:
        st.header("System Status")
        
        # API connection status
        api_status = check_api_connection()
        if api_status["connected"]:
            st.success("✅ API Connected")
        else:
            st.error("❌ API Disconnected")
            st.error(f"Error: {api_status.get('error', 'Unknown error')}")
        
        st.markdown("---")
        
        # Refresh controls
        st.header("Controls")
        if st.button("🔄 Refresh Data", type="primary"):
            st.session_state.last_refresh = datetime.now()
            st.experimental_rerun()
        
        auto_refresh = st.checkbox("Auto-refresh (30s)", value=False)
        
        if auto_refresh:
            # Auto-refresh every 30 seconds
            import time
            time.sleep(30)
            st.experimental_rerun()
        
        st.markdown("---")
        
        # Time range selector
        st.header("Time Range")
        time_range = st.selectbox(
            "Select time range:",
            ["Last 24 hours", "Last 7 days", "Last 30 days", "Custom range"]
        )
        
        if time_range == "Custom range":
            start_date = st.date_input("Start date")
            end_date = st.date_input("End date")
        else:
            end_date = datetime.now().date()
            if time_range == "Last 24 hours":
                start_date = end_date - timedelta(days=1)
            elif time_range == "Last 7 days":
                start_date = end_date - timedelta(days=7)
            else:  # Last 30 days
                start_date = end_date - timedelta(days=30)
    
    # Main content area
    if api_status["connected"]:
        display_main_dashboard(start_date, end_date)
    else:
        display_offline_mode()

def check_api_connection():
    """Check API connection status."""
    try:
        # Use root endpoint which is faster
        response = requests.get("http://localhost:8000/", timeout=20)
        if response.status_code == 200:
            return {"connected": True, "data": response.json()}
        else:
            return {"connected": False, "error": f"API returned {response.status_code}"}
    except requests.exceptions.RequestException as e:
        return {"connected": False, "error": str(e)}

def display_main_dashboard(start_date, end_date):
    """Display main dashboard content."""
    
    # Fetch current data
    current_data = fetch_current_data()
    
    # Key metrics row
    st.header("📊 Current Status")
    display_key_metrics(current_data)
    
    st.markdown("---")
    
    # Main content columns
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("🔥 Risk Timeline")
        
        # Fetch timeline data
        timeline_data = fetch_timeline_data(start_date, end_date)
        
        if not timeline_data.empty:
            fig = create_risk_timeline(timeline_data)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No timeline data available for selected period")
        
        st.header("🗺️ Geographic Risk Distribution")
        
        # Location heatmap
        location_data = fetch_location_data()
        
        if not location_data.empty:
            fig = create_location_heatmap(location_data)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No location data available")
    
    with col2:
        st.header("🚨 Recent Alerts")
        display_recent_alerts()
        
        st.markdown("---")
        
        st.header("🎯 Active Monitoring")
        
        # Active monitoring locations
        monitoring_locations = get_monitoring_locations()
        
        for location in monitoring_locations:
            with st.expander(f"📍 {location['name']}"):
                col_a, col_b = st.columns(2)
                
                with col_a:
                    st.metric(
                        "Risk Score",
                        f"{location['risk_score']:.1f}/10",
                        delta=f"{location['risk_change']:+.1f}"
                    )
                
                with col_b:
                    st.metric(
                        "Active Cases",
                        location['active_cases'],
                        delta=location['case_change']
                    )
                
                # Risk level indicator
                risk_color = get_risk_color(location['risk_score'])
                st.markdown(
                    f"<div style='background-color: {risk_color}; padding: 5px; border-radius: 5px; text-align: center; color: white;'>"
                    f"<strong>{location['alert_level']}</strong></div>",
                    unsafe_allow_html=True
                )
        
        st.markdown("---")
        
        st.header("🔧 Quick Actions")
        
        if st.button("🚨 Generate Alert", type="secondary"):
            st.info("Alert generation feature coming soon")
        
        if st.button("📊 Run Analysis", type="secondary"):
            with st.spinner("Running analysis..."):
                # Simulate analysis
                import time
                time.sleep(2)
                st.success("Analysis completed!")
        
        if st.button("📁 Export Data", type="secondary"):
            # Generate sample CSV
            sample_data = pd.DataFrame({
                'timestamp': pd.date_range(start=start_date, end=end_date, freq='H'),
                'risk_score': [random.uniform(1, 10) for _ in range(24 * (end_date - start_date).days + 1)],
                'location': ['Rural_Hospital_A'] * (24 * (end_date - start_date).days + 1)
            })
            
            csv = sample_data.to_csv(index=False)
            st.download_button(
                label="💾 Download CSV",
                data=csv,
                file_name=f"epidemic_data_{start_date}_{end_date}.csv",
                mime="text/csv"
            )

def display_offline_mode():
    """Display offline mode with sample data."""
    st.warning("⚠️ API not available - showing sample data")
    
    # Generate sample data for demonstration
    sample_data = generate_sample_dashboard_data()
    
    # Display sample metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Overall Risk", "6.2/10", "+0.5")
    
    with col2:
        st.metric("Active Cases", "47", "+3")
    
    with col3:
        st.metric("Monitored Locations", "6", "0")
    
    with col4:
        st.metric("Alerts (24h)", "2", "+1")
    
    st.markdown("---")
    
    # Sample chart
    st.header("📈 Sample Risk Timeline")
    
    import random
    dates = pd.date_range(start=datetime.now() - timedelta(days=7), end=datetime.now(), freq='H')
    risk_scores = [random.uniform(3, 8) for _ in range(len(dates))]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates,
        y=risk_scores,
        mode='lines+markers',
        name='Risk Score',
        line=dict(color='red', width=2)
    ))
    
    fig.update_layout(
        title="Risk Score Over Time (Sample Data)",
        xaxis_title="Time",
        yaxis_title="Risk Score",
        yaxis=dict(range=[0, 10])
    )
    
    st.plotly_chart(fig, use_container_width=True)

def fetch_current_data():
    """Fetch current status data from API."""
    try:
        response = requests.get("http://localhost:8000/api/v1/prediction/risk-assessment")
        if response.status_code == 200:
            return response.json()
    except:
        pass
    
    # Return sample data if API unavailable
    return {
        "current_risk_score": 6.2,
        "active_cases": 47,
        "alert_level": "MEDIUM",
        "trend": "INCREASING"
    }

def fetch_timeline_data(start_date, end_date):
    """Fetch timeline data from API."""
    # This would normally make API calls
    # For now, return sample data
    
    import random
    dates = pd.date_range(start=start_date, end=end_date, freq='6H')
    
    return pd.DataFrame({
        'timestamp': dates,
        'risk_score': [random.uniform(2, 9) for _ in range(len(dates))],
        'outbreak_probability': [random.uniform(0.1, 0.8) for _ in range(len(dates))],
        'active_cases': [random.randint(10, 100) for _ in range(len(dates))]
    })

def fetch_location_data():
    """Fetch location-based risk data."""
    # Sample location data
    locations = [
        {"name": "Rural Hospital A", "lat": 20.5937, "lon": 78.9629, "risk": 7.2, "cases": 23},
        {"name": "Health Center B", "lat": 21.1458, "lon": 79.0882, "risk": 5.8, "cases": 15},
        {"name": "Clinic C", "lat": 20.9466, "lon": 77.7574, "risk": 4.3, "cases": 8},
        {"name": "Mobile Unit D", "lat": 21.2514, "lon": 81.6296, "risk": 6.7, "cases": 19},
        {"name": "Community Health E", "lat": 19.9975, "lon": 79.5926, "risk": 3.9, "cases": 6},
        {"name": "Rural Hospital F", "lat": 20.7506, "lon": 80.3809, "risk": 8.1, "cases": 31}
    ]
    
    return pd.DataFrame(locations)

def get_monitoring_locations():
    """Get actively monitored locations."""
    return [
        {
            "name": "Rural Hospital A",
            "risk_score": 7.2,
            "risk_change": 0.5,
            "active_cases": 23,
            "case_change": 3,
            "alert_level": "HIGH"
        },
        {
            "name": "Health Center B", 
            "risk_score": 5.8,
            "risk_change": -0.2,
            "active_cases": 15,
            "case_change": -1,
            "alert_level": "MEDIUM"
        },
        {
            "name": "Mobile Unit D",
            "risk_score": 6.7,
            "risk_change": 1.1,
            "active_cases": 19,
            "case_change": 5,
            "alert_level": "HIGH"
        }
    ]

def get_risk_color(risk_score):
    """Get color based on risk score."""
    if risk_score >= 8:
        return "#dc3545"  # Red
    elif risk_score >= 6:
        return "#fd7e14"  # Orange
    elif risk_score >= 4:
        return "#ffc107"  # Yellow
    else:
        return "#28a745"  # Green

def generate_sample_dashboard_data():
    """Generate sample data for offline mode."""
    return {
        "overall_risk": 6.2,
        "active_cases": 47,
        "monitored_locations": 6,
        "alerts_24h": 2
    }

if __name__ == "__main__":
    main()
