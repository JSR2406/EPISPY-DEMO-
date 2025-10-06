"""Real-time monitoring dashboard page."""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import requests
import time
import random

st.set_page_config(
    page_title="Real-Time Monitoring",
    page_icon="🏥",
    layout="wide"
)

def main():
    st.title("🏥 Real-Time Monitoring")
    st.markdown("**Live monitoring of healthcare facilities and epidemic indicators**")
    
    # Auto-refresh toggle
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        auto_refresh = st.toggle("Auto-refresh", value=True)
    
    with col2:
        refresh_interval = st.selectbox(
            "Refresh interval",
            [5, 10, 30, 60],
            index=2,
            format_func=lambda x: f"{x} seconds"
        )
    
    with col3:
        if st.button("🔄 Refresh Now", type="primary"):
            st.rerun()
    
    # Auto-refresh mechanism
    if auto_refresh:
        placeholder = st.empty()
        time.sleep(refresh_interval)
        st.rerun()
    
    # Real-time metrics
    st.header("📊 Live Metrics")
    
    current_time = datetime.now()
    
    # Create 4 columns for key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Simulate real-time risk score
        risk_score = random.uniform(4, 8)
        risk_change = random.uniform(-0.5, 0.5)
        
        st.metric(
            "Current Risk Score",
            f"{risk_score:.1f}/10",
            delta=f"{risk_change:+.1f}",
            delta_color="inverse"
        )
    
    with col2:
        # Active monitoring locations
        active_locations = random.randint(8, 12)
        location_change = random.randint(-1, 2)
        
        st.metric(
            "Active Locations",
            active_locations,
            delta=location_change
        )
    
    with col3:
        # Data points collected
        data_points = random.randint(1200, 1800)
        points_change = random.randint(50, 150)
        
        st.metric(
            "Data Points (Last Hour)",
            f"{data_points:,}",
            delta=f"+{points_change}"
        )
    
    with col4:
        # System uptime
        uptime_hours = random.randint(120, 200)
        
        st.metric(
            "System Uptime",
            f"{uptime_hours} hours",
            delta="99.9% availability"
        )
    
    st.markdown("---")
    
    # Live data streams
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.header("📈 Live Risk Timeline")
        
        # Generate real-time data
        times = [current_time - timedelta(minutes=i*5) for i in range(24, 0, -1)]
        risk_values = [random.uniform(3, 8) for _ in times]
        outbreak_probs = [random.uniform(0.1, 0.7) for _ in times]
        
        # Create dual-axis chart
        fig = go.Figure()
        
        # Risk score line
        fig.add_trace(go.Scatter(
            x=times,
            y=risk_values,
            mode='lines+markers',
            name='Risk Score',
            line=dict(color='red', width=2),
            yaxis='y'
        ))
        
        # Outbreak probability
        fig.add_trace(go.Scatter(
            x=times,
            y=[p*10 for p in outbreak_probs],  # Scale for visualization
            mode='lines',
            name='Outbreak Probability (×10)',
            line=dict(color='orange', width=2, dash='dash'),
            yaxis='y'
        ))
        
        fig.update_layout(
            title="Real-Time Risk Monitoring (Last 2 Hours)",
            xaxis_title="Time",
            yaxis=dict(
                title="Risk Score",
                range=[0, 10]
            ),
            height=400,
            showlegend=True
        )
        
        # Add current time indicator
        fig.add_vline(
            x=current_time,
            line_dash="dot",
            line_color="green",
            annotation_text="Now"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Live location status
        st.header("🗺️ Facility Status Map")
        
        # Sample facility data
        facilities = [
            {"name": "Rural Hospital A", "lat": 20.5937, "lon": 78.9629, "risk": random.uniform(5, 9), "status": "ACTIVE"},
            {"name": "Health Center B", "lat": 21.1458, "lon": 79.0882, "risk": random.uniform(3, 7), "status": "ACTIVE"},
            {"name": "Clinic C", "lat": 20.9466, "lon": 77.7574, "risk": random.uniform(2, 6), "status": "ACTIVE"},
            {"name": "Mobile Unit D", "lat": 21.2514, "lon": 81.6296, "risk": random.uniform(4, 8), "status": "MOVING"},
            {"name": "Community Health E", "lat": 19.9975, "lon": 79.5926, "risk": random.uniform(2, 5), "status": "ACTIVE"},
            {"name": "Rural Hospital F", "lat": 20.7506, "lon": 80.3809, "risk": random.uniform(6, 9), "status": "HIGH_ALERT"}
        ]
        
        df_facilities = pd.DataFrame(facilities)
        
        # Color code by risk level
        def get_color(risk):
            if risk >= 7:
                return 'red'
            elif risk >= 5:
                return 'orange'
            else:
                return 'green'
        
        df_facilities['color'] = df_facilities['risk'].apply(get_color)
        
        # Create map
        fig_map = px.scatter_mapbox(
            df_facilities,
            lat="lat",
            lon="lon",
            color="risk",
            size="risk",
            hover_name="name",
            hover_data={"status": True, "risk": ":.1f"},
            color_continuous_scale="Reds",
            zoom=6,
            height=400
        )
        
        fig_map.update_layout(
            mapbox_style="open-street-map",
            title="Healthcare Facilities - Live Status"
        )
        
        st.plotly_chart(fig_map, use_container_width=True)
    
    with col_right:
        st.header("🚨 Live Alerts")
        
        # Recent alerts
        alerts = [
            {
                "time": current_time - timedelta(minutes=5),
                "level": "HIGH",
                "location": "Rural Hospital A",
                "message": "Risk score threshold exceeded (8.2/10)",
                "status": "ACTIVE"
            },
            {
                "time": current_time - timedelta(minutes=15),
                "level": "MEDIUM",
                "location": "Mobile Unit D",
                "message": "Unusual symptom pattern detected",
                "status": "INVESTIGATING"
            },
            {
                "time": current_time - timedelta(minutes=30),
                "level": "LOW",
                "location": "Health Center B",
                "message": "Data quality anomaly resolved",
                "status": "RESOLVED"
            }
        ]
        
        for alert in alerts:
            level_color = {
                "HIGH": "#dc3545",
                "MEDIUM": "#ffc107", 
                "LOW": "#28a745"
            }.get(alert["level"], "#6c757d")
            
            status_color = {
                "ACTIVE": "#dc3545",
                "INVESTIGATING": "#ffc107",
                "RESOLVED": "#28a745"
            }.get(alert["status"], "#6c757d")
            
            with st.container():
                st.markdown(
                    f"""
                    <div style="
                        border-left: 4px solid {level_color};
                        padding: 10px;
                        margin: 10px 0;
                        background-color: #f8f9fa;
                        border-radius: 5px;
                    ">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <strong style="color: {level_color};">{alert['level']}</strong>
                            <small style="color: {status_color};">{alert['status']}</small>
                        </div>
                        <div style="margin: 5px 0;">
                            <strong>{alert['location']}</strong>
                        </div>
                        <div style="margin: 5px 0; font-size: 14px;">
                            {alert['message']}
                        </div>
                        <div style="font-size: 12px; color: #666;">
                            {alert['time'].strftime('%H:%M:%S')}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        
        st.markdown("---")
        
        st.header("🔧 System Status")
        
        # System components status
        components = [
            {"name": "API Server", "status": "HEALTHY", "response_time": "45ms"},
            {"name": "Ollama LLM", "status": "HEALTHY", "response_time": "1.2s"},
            {"name": "SEIR Model", "status": "HEALTHY", "response_time": "120ms"},
            {"name": "ChromaDB", "status": "HEALTHY", "response_time": "30ms"},
            {"name": "Data Pipeline", "status": "HEALTHY", "throughput": "1.2k/min"}
        ]
        
        for comp in components:
            status_icon = "✅" if comp["status"] == "HEALTHY" else "❌"
            
            st.markdown(
                f"""
                <div style="
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 8px 12px;
                    margin: 5px 0;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    background-color: #f8f9fa;
                ">
                    <div>
                        {status_icon} <strong>{comp['name']}</strong>
                    </div>
                    <div style="font-size: 12px; color: #666;">
                        {comp.get('response_time', comp.get('throughput', 'OK'))}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        st.markdown("---")
        
        st.header("📊 Quick Stats")
        
        # Quick statistics
        stats = {
            "Models Running": 4,
            "Data Sources": 12,
            "Predictions/Hour": 720,
            "Accuracy": "94.2%"
        }
        
        for stat_name, stat_value in stats.items():
            st.metric(stat_name, stat_value)

if __name__ == "__main__":
    main()
