"""Chart components for the dashboard."""
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Optional


def create_risk_timeline(data: pd.DataFrame) -> go.Figure:
    """
    Create a risk timeline chart.
    
    Args:
        data: DataFrame with columns: timestamp, risk_score, outbreak_probability, active_cases
        
    Returns:
        Plotly figure object
    """
    fig = go.Figure()
    
    # Add risk score line
    fig.add_trace(go.Scatter(
        x=data['timestamp'],
        y=data['risk_score'],
        mode='lines+markers',
        name='Risk Score',
        line=dict(color='#dc3545', width=3),
        marker=dict(size=6),
        yaxis='y1'
    ))
    
    # Add outbreak probability line
    if 'outbreak_probability' in data.columns:
        fig.add_trace(go.Scatter(
            x=data['timestamp'],
            y=data['outbreak_probability'] * 10,  # Scale to 0-10
            mode='lines',
            name='Outbreak Probability',
            line=dict(color='#fd7e14', width=2, dash='dash'),
            yaxis='y1'
        ))
    
    # Add active cases as bar chart
    if 'active_cases' in data.columns:
        fig.add_trace(go.Bar(
            x=data['timestamp'],
            y=data['active_cases'],
            name='Active Cases',
            marker=dict(color='#6c757d', opacity=0.3),
            yaxis='y2'
        ))
    
    # Update layout
    fig.update_layout(
        title='Risk Timeline Analysis',
        xaxis=dict(title='Time'),
        yaxis=dict(
            title=dict(text='Risk Score / Probability (0-10)', font=dict(color='#dc3545')),
            tickfont=dict(color='#dc3545'),
            range=[0, 10]
        ),
        yaxis2=dict(
            title=dict(text='Active Cases', font=dict(color='#6c757d')),
            tickfont=dict(color='#6c757d'),
            overlaying='y',
            side='right'
        ),
        hovermode='x unified',
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        ),
        height=400
    )
    
    return fig


def create_location_heatmap(data: pd.DataFrame) -> go.Figure:
    """
    Create a geographic heatmap of risk levels.
    
    Args:
        data: DataFrame with columns: name, lat, lon, risk, cases
        
    Returns:
        Plotly figure object
    """
    # Create color scale based on risk
    def get_color(risk):
        if risk >= 8:
            return '#dc3545'  # Red
        elif risk >= 6:
            return '#fd7e14'  # Orange
        elif risk >= 4:
            return '#ffc107'  # Yellow
        else:
            return '#28a745'  # Green
    
    data['color'] = data['risk'].apply(get_color)
    
    # Create scatter mapbox
    fig = go.Figure(go.Scattermapbox(
        lat=data['lat'],
        lon=data['lon'],
        mode='markers+text',
        marker=dict(
            size=data['risk'] * 5,  # Size based on risk
            color=data['risk'],
            colorscale=[
                [0, '#28a745'],    # Green
                [0.4, '#ffc107'],  # Yellow
                [0.6, '#fd7e14'],  # Orange
                [1, '#dc3545']     # Red
            ],
            showscale=True,
            colorbar=dict(
                title='Risk Score',
                thickness=15,
                len=0.7
            ),
            cmin=0,
            cmax=10
        ),
        text=data['name'],
        textposition='top center',
        hovertemplate='<b>%{text}</b><br>' +
                      'Risk: %{marker.color:.1f}/10<br>' +
                      'Cases: %{customdata}<br>' +
                      '<extra></extra>',
        customdata=data['cases']
    ))
    
    # Update layout
    fig.update_layout(
        title='Geographic Risk Distribution',
        mapbox=dict(
            style='open-street-map',
            center=dict(
                lat=data['lat'].mean(),
                lon=data['lon'].mean()
            ),
            zoom=5
        ),
        height=500,
        margin=dict(l=0, r=0, t=30, b=0)
    )
    
    return fig


def create_symptom_distribution(data: pd.DataFrame) -> go.Figure:
    """
    Create a symptom distribution chart.
    
    Args:
        data: DataFrame with symptom counts
        
    Returns:
        Plotly figure object
    """
    fig = px.bar(
        data,
        x='symptom',
        y='count',
        title='Symptom Distribution',
        color='count',
        color_continuous_scale='Reds'
    )
    
    fig.update_layout(
        xaxis_title='Symptom',
        yaxis_title='Count',
        showlegend=False,
        height=350
    )
    
    return fig


def create_age_distribution(data: pd.DataFrame) -> go.Figure:
    """
    Create an age group distribution chart.
    
    Args:
        data: DataFrame with age group data
        
    Returns:
        Plotly figure object
    """
    fig = px.pie(
        data,
        values='count',
        names='age_group',
        title='Age Group Distribution',
        color_discrete_sequence=px.colors.sequential.RdBu
    )
    
    fig.update_layout(height=350)
    
    return fig


def create_prediction_chart(data: pd.DataFrame) -> go.Figure:
    """
    Create a prediction chart showing historical and predicted values.
    
    Args:
        data: DataFrame with historical and predicted data
        
    Returns:
        Plotly figure object
    """
    fig = go.Figure()
    
    # Historical data
    historical = data[data['type'] == 'historical']
    fig.add_trace(go.Scatter(
        x=historical['timestamp'],
        y=historical['value'],
        mode='lines+markers',
        name='Historical',
        line=dict(color='#007bff', width=2)
    ))
    
    # Predicted data
    predicted = data[data['type'] == 'predicted']
    fig.add_trace(go.Scatter(
        x=predicted['timestamp'],
        y=predicted['value'],
        mode='lines+markers',
        name='Predicted',
        line=dict(color='#28a745', width=2, dash='dash')
    ))
    
    # Confidence interval
    if 'lower_bound' in data.columns and 'upper_bound' in data.columns:
        fig.add_trace(go.Scatter(
            x=predicted['timestamp'].tolist() + predicted['timestamp'].tolist()[::-1],
            y=predicted['upper_bound'].tolist() + predicted['lower_bound'].tolist()[::-1],
            fill='toself',
            fillcolor='rgba(40, 167, 69, 0.2)',
            line=dict(color='rgba(255,255,255,0)'),
            name='Confidence Interval',
            showlegend=True
        ))
    
    fig.update_layout(
        title='Epidemic Prediction',
        xaxis_title='Time',
        yaxis_title='Cases',
        hovermode='x unified',
        height=400
    )
    
    return fig
