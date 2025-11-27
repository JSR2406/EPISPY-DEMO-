"""Alert Management dashboard page."""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import requests
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.alerts import display_recent_alerts, get_sample_alerts
from utils.formatting import get_severity_emoji, get_risk_color

st.set_page_config(page_title="Alert Management - EpiSPY", page_icon="🚨", layout="wide")

st.title("🚨 Alert Management")
st.markdown("**Monitor and manage epidemic alerts and warnings**")

# Controls
col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    severity_filter = st.multiselect(
        "Filter by Severity:",
        ["CRITICAL", "HIGH", "MEDIUM", "LOW"],
        default=["CRITICAL", "HIGH", "MEDIUM"]
    )
with col2:
    status_filter = st.selectbox(
        "Status:",
        ["All", "Active", "Resolved"]
    )
with col3:
    if st.button("🔄 Refresh", type="primary"):
        st.rerun()

st.markdown("---")

# Alert statistics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Alerts (24h)", "23", "+5")
with col2:
    st.metric("Critical Alerts", "3", "+1", delta_color="inverse")
with col3:
    st.metric("Active Alerts", "18", "+2")
with col4:
    st.metric("Avg Response Time", "12 min", "-3 min")

st.markdown("---")

# Main content tabs
tab1, tab2, tab3 = st.tabs(["📋 Active Alerts", "📊 Alert Analytics", "⚙️ Alert Configuration"])

with tab1:
    st.header("Active Alerts")
    
    # Get sample alerts
    alerts = get_sample_alerts(20)
    
    # Filter alerts
    filtered_alerts = [a for a in alerts if a['severity'] in severity_filter]
    if status_filter != "All":
        filtered_alerts = [a for a in filtered_alerts if a['status'] == status_filter.lower()]
    
    # Display alerts
    for alert in filtered_alerts[:10]:
        severity = alert.get('severity', 'MEDIUM')
        alert_type = alert.get('alert_type', 'GENERAL')
        message = alert.get('message', 'No message')
        location = alert.get('location', 'Unknown')
        timestamp = alert.get('created_at', datetime.now().isoformat())
        
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
        
        with st.expander(f"{icon} {alert_type} - {location}", expanded=False):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**Message:** {message}")
                st.caption(f"📍 Location: {location}")
                st.caption(f"🕐 Time: {timestamp[:19]}")
            
            with col2:
                st.markdown(f"<div style='background-color: {color}; color: white; padding: 10px; border-radius: 5px; text-align: center; font-weight: bold;'>{severity}</div>", unsafe_allow_html=True)
                
                if alert['status'] == 'active':
                    if st.button("✅ Resolve", key=f"resolve_{alert['alert_id']}"):
                        st.success(f"Alert {alert['alert_id']} marked as resolved")
                else:
                    st.success("Resolved")

with tab2:
    st.header("Alert Analytics")
    
    # Alert trends
    dates = pd.date_range(start=datetime.now() - timedelta(days=7), end=datetime.now(), freq='D')
    import random
    
    alert_trend = pd.DataFrame({
        'date': dates,
        'critical': [random.randint(0, 5) for _ in range(len(dates))],
        'high': [random.randint(2, 8) for _ in range(len(dates))],
        'medium': [random.randint(5, 15) for _ in range(len(dates))],
        'low': [random.randint(3, 10) for _ in range(len(dates))]
    })
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=alert_trend['date'], y=alert_trend['critical'], mode='lines+markers', name='Critical', line=dict(color='#dc3545', width=3), stackgroup='one'))
    fig.add_trace(go.Scatter(x=alert_trend['date'], y=alert_trend['high'], mode='lines+markers', name='High', line=dict(color='#fd7e14', width=3), stackgroup='one'))
    fig.add_trace(go.Scatter(x=alert_trend['date'], y=alert_trend['medium'], mode='lines+markers', name='Medium', line=dict(color='#ffc107', width=3), stackgroup='one'))
    fig.add_trace(go.Scatter(x=alert_trend['date'], y=alert_trend['low'], mode='lines+markers', name='Low', line=dict(color='#28a745', width=3), stackgroup='one'))
    
    fig.update_layout(
        title='Alert Trends (7 Days)',
        xaxis_title='Date',
        yaxis_title='Number of Alerts',
        height=400,
        hovermode='x unified'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Alert distribution
    col1, col2 = st.columns(2)
    
    with col1:
        # By severity
        severity_dist = pd.DataFrame({
            'Severity': ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'],
            'Count': [12, 34, 67, 45]
        })
        fig = px.pie(severity_dist, values='Count', names='Severity', title='Alerts by Severity',
                     color='Severity',
                     color_discrete_map={'CRITICAL': '#dc3545', 'HIGH': '#fd7e14', 'MEDIUM': '#ffc107', 'LOW': '#28a745'})
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # By type
        type_dist = pd.DataFrame({
            'Type': ['Outbreak Warning', 'Risk Increase', 'Pattern Detected', 'Geographic Cluster', 'System Info'],
            'Count': [45, 38, 29, 24, 22]
        })
        fig = px.bar(type_dist, x='Type', y='Count', title='Alerts by Type', color='Count', color_continuous_scale='Reds')
        st.plotly_chart(fig, use_container_width=True)
    
    # Response time analysis
    st.subheader("Response Time Analysis")
    response_data = pd.DataFrame({
        'Severity': ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'],
        'Avg Response (min)': [8, 15, 32, 67],
        'Target (min)': [10, 20, 45, 90]
    })
    
    fig = go.Figure()
    fig.add_trace(go.Bar(name='Actual', x=response_data['Severity'], y=response_data['Avg Response (min)'], marker_color='#007bff'))
    fig.add_trace(go.Bar(name='Target', x=response_data['Severity'], y=response_data['Target (min)'], marker_color='#28a745'))
    fig.update_layout(title='Response Time vs Target', barmode='group', height=300)
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.header("Alert Configuration")
    
    st.subheader("Alert Thresholds")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.number_input("Risk Score Threshold (Critical)", min_value=0.0, max_value=10.0, value=8.0, step=0.1)
        st.number_input("Risk Score Threshold (High)", min_value=0.0, max_value=10.0, value=6.0, step=0.1)
        st.number_input("Risk Score Threshold (Medium)", min_value=0.0, max_value=10.0, value=4.0, step=0.1)
    
    with col2:
        st.number_input("Case Increase Threshold (%)", min_value=0, max_value=100, value=20, step=5)
        st.number_input("Outbreak Probability Threshold", min_value=0.0, max_value=1.0, value=0.7, step=0.05)
        st.number_input("Geographic Cluster Radius (km)", min_value=1, max_value=100, value=10, step=1)
    
    st.subheader("Notification Settings")
    
    st.checkbox("Enable email notifications", value=True)
    st.checkbox("Enable SMS notifications", value=False)
    st.checkbox("Enable push notifications", value=True)
    st.checkbox("Auto-escalate critical alerts", value=True)
    
    st.text_area("Notification Recipients (comma-separated emails)", 
                 value="admin@epispy.com, alerts@epispy.com")
    
    if st.button("💾 Save Configuration", type="primary"):
        st.success("✅ Configuration saved successfully!")

# Footer
st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
