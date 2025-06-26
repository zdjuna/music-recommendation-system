"""
Chart components for music data visualization
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Optional

@st.cache_data(ttl=1800)  # Cache for 30 minutes
def create_listening_timeline(df: pd.DataFrame) -> go.Figure:
    """Create beautiful listening timeline chart with caching"""
    if df is None or df.empty:
        return go.Figure()
    
    # Ensure timestamp is datetime
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Group by day and count
        daily_counts = df.groupby(df['timestamp'].dt.date).size().reset_index()
        daily_counts.columns = ['date', 'count']
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=daily_counts['date'],
            y=daily_counts['count'],
            mode='lines+markers',
            name='Daily Listening',
            line=dict(color='#667eea', width=3),
            marker=dict(size=6, color='#764ba2'),
            fill='tonexty',
            fillcolor='rgba(102, 126, 234, 0.1)'
        ))
        
        fig.update_layout(
            title="📈 Your Listening Timeline",
            xaxis_title="Date",
            yaxis_title="Tracks Played",
            font=dict(family="Arial", size=12),
            height=400,
            showlegend=False
        )
        
        return fig
    
    return go.Figure()

@st.cache_data(ttl=1800)  # Cache for 30 minutes  
def create_top_artists_chart(df: pd.DataFrame, top_n: int = 15) -> go.Figure:
    """Create top artists bar chart"""
    if df is None or df.empty:
        return go.Figure()
    
    top_artists = df['artist'].value_counts().head(top_n)
    
    fig = go.Figure(data=[
        go.Bar(
            x=top_artists.values,
            y=top_artists.index,
            orientation='h',
            marker=dict(
                color=top_artists.values,
                colorscale='Plasma',
                showscale=False
            ),
            text=top_artists.values,
            textposition='outside'
        )
    ])
    
    fig.update_layout(
        title="🎤 Your Top Artists",
        xaxis_title="Plays",
        yaxis_title="Artist",
        height=600,
        font=dict(family="Arial", size=12)
    )
    
    return fig

@st.cache_data(ttl=1800)  # Cache for 30 minutes
def create_mood_distribution(df: pd.DataFrame) -> Optional[go.Figure]:
    """Create mood distribution pie chart"""
    if df is None or df.empty or 'mood_primary' not in df.columns:
        return None
    
    mood_counts = df['mood_primary'].value_counts()
    
    fig = go.Figure(data=[go.Pie(
        labels=mood_counts.index,
        values=mood_counts.values,
        hole=.4,
        marker_colors=px.colors.qualitative.Set3
    )])
    
    fig.update_layout(
        title="🎭 Mood Distribution",
        height=400,
        font=dict(family="Arial", size=12),
        showlegend=True
    )
    
    return fig

@st.cache_data(ttl=1800)  # Cache for 30 minutes
def create_listening_heatmap(df: pd.DataFrame) -> go.Figure:
    """Create listening pattern heatmap"""
    if df is None or df.empty:
        return go.Figure()
    
    # Ensure timestamp is datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Extract hour and day of week
    df['hour'] = df['timestamp'].dt.hour
    df['day_of_week'] = df['timestamp'].dt.day_name()
    
    # Create heatmap data
    heatmap_data = df.groupby(['day_of_week', 'hour']).size().reset_index(name='count')
    
    # Ensure all days and hours are represented
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    heatmap_data['day_of_week'] = pd.Categorical(heatmap_data['day_of_week'], categories=day_order, ordered=True)
    
    # Pivot for heatmap
    heatmap_pivot = heatmap_data.pivot(index='day_of_week', columns='hour', values='count').fillna(0)
    
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_pivot.values,
        x=[f"{h:02d}:00" for h in range(24)],
        y=day_order,
        colorscale='Viridis',
        showscale=True,
        colorbar=dict(title="Tracks Played")
    ))
    
    fig.update_layout(
        title="🕐 Your Listening Patterns",
        xaxis_title="Hour of Day",
        yaxis_title="Day of Week",
        font=dict(family="Arial", size=12),
        height=400
    )
    
    return fig

@st.cache_data(ttl=1800)  # Cache for 30 minutes
def create_artist_discovery_timeline(df: pd.DataFrame) -> go.Figure:
    """Create artist discovery timeline"""
    if df is None or df.empty:
        return go.Figure()
    
    # Find first occurrence of each artist
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    first_plays = df.groupby('artist')['timestamp'].min().reset_index()
    first_plays['year_month'] = first_plays['timestamp'].dt.to_period('M')
    
    # Count new artists per month
    discovery_counts = first_plays.groupby('year_month').size().reset_index(name='new_artists')
    discovery_counts['year_month'] = discovery_counts['year_month'].astype(str)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=discovery_counts['year_month'],
        y=discovery_counts['new_artists'],
        mode='lines+markers',
        name='New Artists Discovered',
        line=dict(color='#e74c3c', width=3),
        marker=dict(size=8, color='#c0392b')
    ))
    
    fig.update_layout(
        title="🔍 Artist Discovery Timeline",
        xaxis_title="Month",
        yaxis_title="New Artists Discovered",
        font=dict(family="Arial", size=12),
        height=400,
        showlegend=False
    )
    
    return fig

def render_charts_grid(df: pd.DataFrame, enriched_df: Optional[pd.DataFrame] = None):
    """Render a comprehensive grid of charts"""
    if df is None or df.empty:
        st.warning("📭 No data available for charts")
        return
    
    # Timeline and patterns
    col1, col2 = st.columns(2)
    
    with col1:
        with st.spinner("Creating listening timeline..."):
            timeline_fig = create_listening_timeline(df)
            st.plotly_chart(timeline_fig, use_container_width=True)
    
    with col2:
        with st.spinner("Analyzing top artists..."):
            artists_fig = create_top_artists_chart(df)
            st.plotly_chart(artists_fig, use_container_width=True)
    
    # Listening patterns
    col3, col4 = st.columns(2)
    
    with col3:
        with st.spinner("Creating listening heatmap..."):
            heatmap_fig = create_listening_heatmap(df)
            st.plotly_chart(heatmap_fig, use_container_width=True)
    
    with col4:
        with st.spinner("Analyzing artist discovery..."):
            discovery_fig = create_artist_discovery_timeline(df)
            st.plotly_chart(discovery_fig, use_container_width=True)
    
    # Mood distribution if available
    if enriched_df is not None and not enriched_df.empty:
        mood_fig = create_mood_distribution(enriched_df)
        if mood_fig:
            st.plotly_chart(mood_fig, use_container_width=True)