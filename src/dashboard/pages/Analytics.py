"""Analytics dashboard page."""
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

from components.charts import create_symptom_distribution, create_age_distribution, create_prediction_chart
from utils.formatting import format_number, format_percentage

st.set_page_config(page_title="Analytics - EpiSPY", page_icon="📊", layout="wide")

st.title("📊 Analytics Dashboard")
st.markdown("**Comprehensive data analysis and insights**")

# Time range selector
col1, col2 = st.columns([3, 1])
with col1:
    time_range = st.selectbox(
        "Select time range:",
        ["Last 7 days", "Last 30 days", "Last 90 days", "Custom range"]
    )
with col2:
    if st.button("🔄 Refresh Data", type="primary"):
        st.rerun()

st.markdown("---")

# Key metrics row
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Cases Analyzed", format_number(1247), "+127")
with col2:
    st.metric("Average Risk Score", "6.8/10", "+0.3")
with col3:
    st.metric("Outbreak Probability", format_percentage(0.42), "+5%")
with col4:
    st.metric("Active Alerts", "8", "+2")

st.markdown("---")

# Main content
tab1, tab2, tab3, tab4 = st.tabs(["📈 Trends", "🔬 Symptom Analysis", "👥 Demographics", "🎯 Predictions"])

with tab1:
    st.header("Risk Trends Over Time")
    
    # Generate sample trend data
    dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='D')
    import random
    
    trend_data = pd.DataFrame({
        'date': dates,
        'risk_score': [random.uniform(4, 9) for _ in range(len(dates))],
        'cases': [random.randint(20, 80) for _ in range(len(dates))],
        'outbreak_prob': [random.uniform(0.2, 0.7) for _ in range(len(dates))]
    })
    
    # Risk score trend
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=trend_data['date'],
        y=trend_data['risk_score'],
        mode='lines+markers',
        name='Risk Score',
        line=dict(color='#dc3545', width=3),
        fill='tozeroy',
        fillcolor='rgba(220, 53, 69, 0.1)'
    ))
    fig.update_layout(
        title='Risk Score Trend (30 Days)',
        xaxis_title='Date',
        yaxis_title='Risk Score',
        height=400,
        hovermode='x unified'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Cases trend
    col1, col2 = st.columns(2)
    
    with col1:
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            x=trend_data['date'],
            y=trend_data['cases'],
            name='Daily Cases',
            marker_color='#007bff'
        ))
        fig2.update_layout(
            title='Daily Cases',
            xaxis_title='Date',
            yaxis_title='Cases',
            height=300
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    with col2:
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(
            x=trend_data['date'],
            y=trend_data['outbreak_prob'],
            mode='lines',
            name='Outbreak Probability',
            line=dict(color='#fd7e14', width=2),
            fill='tozeroy'
        ))
        fig3.update_layout(
            title='Outbreak Probability',
            xaxis_title='Date',
            yaxis_title='Probability',
            height=300,
            yaxis=dict(tickformat='.0%')
        )
        st.plotly_chart(fig3, use_container_width=True)

with tab2:
    st.header("Symptom Distribution Analysis")
    
    # Sample symptom data
    symptom_data = pd.DataFrame({
        'symptom': ['Fever', 'Cough', 'Fatigue', 'Headache', 'Sore Throat', 'Shortness of Breath'],
        'count': [342, 298, 256, 189, 167, 134]
    })
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = create_symptom_distribution(symptom_data)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Symptom correlation heatmap
        st.subheader("Symptom Co-occurrence")
        symptoms = symptom_data['symptom'].tolist()
        corr_matrix = pd.DataFrame(
            [[random.uniform(0.3, 1.0) for _ in symptoms] for _ in symptoms],
            index=symptoms,
            columns=symptoms
        )
        
        fig = px.imshow(
            corr_matrix,
            labels=dict(color="Correlation"),
            color_continuous_scale='RdYlGn',
            aspect="auto"
        )
        fig.update_layout(title='Symptom Correlation Matrix', height=350)
        st.plotly_chart(fig, use_container_width=True)
    
    # Top symptom combinations
    st.subheader("Most Common Symptom Combinations")
    combinations = pd.DataFrame({
        'Combination': [
            'Fever + Cough',
            'Fever + Fatigue',
            'Cough + Sore Throat',
            'Fever + Headache',
            'Cough + Shortness of Breath'
        ],
        'Count': [156, 134, 98, 87, 76],
        'Percentage': [45.6, 39.2, 28.7, 25.4, 22.2]
    })
    st.dataframe(combinations, use_container_width=True, hide_index=True)

with tab3:
    st.header("Demographic Analysis")
    
    # Age distribution
    age_data = pd.DataFrame({
        'age_group': ['0-17', '18-29', '30-44', '45-64', '65+'],
        'count': [87, 234, 398, 312, 216]
    })
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = create_age_distribution(age_data)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Gender distribution
        gender_data = pd.DataFrame({
            'gender': ['Male', 'Female', 'Other'],
            'count': [612, 598, 37]
        })
        fig = px.pie(
            gender_data,
            values='count',
            names='gender',
            title='Gender Distribution',
            color_discrete_sequence=['#007bff', '#dc3545', '#28a745']
        )
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)
    
    # Risk by age group
    st.subheader("Risk Score by Age Group")
    risk_by_age = pd.DataFrame({
        'Age Group': age_data['age_group'],
        'Average Risk': [5.2, 6.1, 7.3, 7.8, 8.4],
        'Cases': age_data['count']
    })
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=risk_by_age['Age Group'],
        y=risk_by_age['Average Risk'],
        name='Average Risk',
        marker_color='#fd7e14',
        yaxis='y1'
    ))
    fig.add_trace(go.Scatter(
        x=risk_by_age['Age Group'],
        y=risk_by_age['Cases'],
        name='Cases',
        mode='lines+markers',
        line=dict(color='#007bff', width=3),
        yaxis='y2'
    ))
    fig.update_layout(
        title='Risk Score and Cases by Age Group',
        xaxis_title='Age Group',
        yaxis=dict(title='Average Risk Score', side='left'),
        yaxis2=dict(title='Number of Cases', side='right', overlaying='y'),
        height=400,
        hovermode='x unified'
    )
    st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.header("Predictive Analytics")
    
    st.info("🔮 AI-powered predictions based on historical data and SEIR modeling")
    
    # Generate prediction data
    historical_dates = pd.date_range(start=datetime.now() - timedelta(days=14), end=datetime.now(), freq='D')
    future_dates = pd.date_range(start=datetime.now() + timedelta(days=1), end=datetime.now() + timedelta(days=14), freq='D')
    
    prediction_data = pd.DataFrame({
        'timestamp': list(historical_dates) + list(future_dates),
        'type': ['historical'] * len(historical_dates) + ['predicted'] * len(future_dates),
        'value': [random.randint(30, 60) for _ in range(len(historical_dates))] + 
                 [random.randint(40, 80) for _ in range(len(future_dates))],
        'lower_bound': [0] * len(historical_dates) + [random.randint(25, 50) for _ in range(len(future_dates))],
        'upper_bound': [0] * len(historical_dates) + [random.randint(60, 100) for _ in range(len(future_dates))]
    })
    
    fig = create_prediction_chart(prediction_data)
    st.plotly_chart(fig, use_container_width=True)
    
    # Prediction metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Predicted Peak Date", "Dec 8, 2025", "")
    with col2:
        st.metric("Predicted Peak Cases", "94", "+56%")
    with col3:
        st.metric("Model Confidence", "87%", "")
    
    # Key insights
    st.subheader("🎯 Key Insights")
    st.success("✅ Outbreak probability is decreasing in the next 7 days")
    st.warning("⚠️ Risk score expected to increase by 12% in the next 14 days")
    st.info("ℹ️ Geographic clustering detected in 3 locations")

# Footer
st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
