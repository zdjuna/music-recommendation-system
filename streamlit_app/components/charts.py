"""
Chart components for music data visualization
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Optional, Dict

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
    heatmap_data = df.groupby(['day_of_week', 'hour']).size().reset_index()
    heatmap_data.columns = ['day_of_week', 'hour', 'count']
    
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
    discovery_counts = first_plays.groupby('year_month').size().reset_index()
    discovery_counts.columns = ['year_month', 'new_artists']
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

@st.cache_data(ttl=1800)
def create_musical_phases_timeline(phases_data: dict) -> go.Figure:
    """Create musical phases timeline visualization"""
    if not phases_data or 'quarterly_metrics' not in phases_data:
        return go.Figure()
    
    quarterly_metrics = phases_data['quarterly_metrics']
    detected_phases = phases_data.get('detected_phases', [])
    
    if not quarterly_metrics:
        return go.Figure()
    
    quarters = [q['quarter'] for q in quarterly_metrics]
    artist_diversity = [q['artist_diversity'] for q in quarterly_metrics]
    listening_intensity = [q['listening_intensity'] for q in quarterly_metrics]
    
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Artist Diversity Index', 'Listening Intensity'),
        vertical_spacing=0.1
    )
    
    fig.add_trace(
        go.Scatter(
            x=quarters,
            y=artist_diversity,
            mode='lines+markers',
            name='Artist Diversity',
            line=dict(color='#3498db', width=3),
            marker=dict(size=8)
        ),
        row=1, col=1
    )
    
    # Listening intensity line
    fig.add_trace(
        go.Scatter(
            x=quarters,
            y=listening_intensity,
            mode='lines+markers',
            name='Listening Intensity',
            line=dict(color='#e74c3c', width=3),
            marker=dict(size=8)
        ),
        row=2, col=1
    )
    
    for phase in detected_phases:
        quarter = phase['quarter']
        phase_type = phase['phase_type']
        
        fig.add_vline(
            x=quarter,
            line_dash="dash",
            line_color="orange",
            annotation_text=phase_type,
            annotation_position="top"
        )
    
    fig.update_layout(
        title="🎭 Musical Phases Detection",
        height=600,
        font=dict(family="Arial", size=12),
        showlegend=True
    )
    
    return fig

@st.cache_data(ttl=1800)
def create_year_over_year_comparison(evolution_data: dict) -> go.Figure:
    """Create year-over-year comparison chart"""
    if not evolution_data or 'yearly_metrics' not in evolution_data:
        return go.Figure()
    
    yearly_metrics = evolution_data['yearly_metrics']
    
    if len(yearly_metrics) < 2:
        return go.Figure()
    
    years = [y['year'] for y in yearly_metrics]
    total_plays = [y['total_plays'] for y in yearly_metrics]
    unique_artists = [y['unique_artists'] for y in yearly_metrics]
    artist_diversity = [y['artist_diversity_index'] for y in yearly_metrics]
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Total Plays', 'Unique Artists', 'Artist Diversity Index', 'Discovery Rate'),
        vertical_spacing=0.1,
        horizontal_spacing=0.1
    )
    
    fig.add_trace(
        go.Bar(x=years, y=total_plays, name='Total Plays', marker_color='#3498db'),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Bar(x=years, y=unique_artists, name='Unique Artists', marker_color='#2ecc71'),
        row=1, col=2
    )
    
    fig.add_trace(
        go.Scatter(x=years, y=artist_diversity, mode='lines+markers', 
                  name='Diversity Index', line=dict(color='#e74c3c', width=3)),
        row=2, col=1
    )
    
    discovery_rates = [y.get('discovery_rate', 0) for y in yearly_metrics]
    fig.add_trace(
        go.Scatter(x=years, y=discovery_rates, mode='lines+markers',
                  name='Discovery Rate', line=dict(color='#f39c12', width=3)),
        row=2, col=2
    )
    
    fig.update_layout(
        title="📊 Year-over-Year Evolution",
        height=600,
        font=dict(family="Arial", size=12),
        showlegend=False
    )
    
    return fig

@st.cache_data(ttl=1800)
def create_listening_evolution_chart(evolution_data: dict) -> go.Figure:
    """Create listening evolution trend chart"""
    if not evolution_data or 'evolution_trends' not in evolution_data:
        return go.Figure()
    
    trends = evolution_data['evolution_trends']
    
    if not trends:
        return go.Figure()
    
    transitions = [t['year_transition'] for t in trends]
    plays_changes = [t['plays_change_pct'] for t in trends]
    diversity_changes = [t['artist_diversity_change'] * 100 for t in trends]  # Convert to percentage
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=transitions,
        y=plays_changes,
        name='Plays Change %',
        marker_color=['green' if x > 0 else 'red' for x in plays_changes],
        text=[f"{x:.1f}%" for x in plays_changes],
        textposition='outside'
    ))
    
    fig.add_trace(go.Scatter(
        x=transitions,
        y=diversity_changes,
        mode='lines+markers',
        name='Diversity Change %',
        yaxis='y2',
        line=dict(color='orange', width=3),
        marker=dict(size=10)
    ))
    
    fig.update_layout(
        title="📈 Listening Evolution Trends",
        xaxis_title="Year Transition",
        yaxis_title="Plays Change (%)",
        yaxis2=dict(
            title="Diversity Change (%)",
            overlaying='y',
            side='right'
        ),
        height=400,
        font=dict(family="Arial", size=12)
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

@st.cache_data(ttl=1800)
def create_yearly_evolution_chart(patterns: Dict) -> go.Figure:
    """Create year-over-year evolution chart"""
    yearly_data = patterns.get('yearly_evolution', {}).get('yearly_stats', {})
    
    if not yearly_data:
        return go.Figure()
    
    years = sorted(yearly_data.keys())
    total_plays = [yearly_data[year]['total_plays'] for year in years]
    artists = [yearly_data[year]['unique_artists'] for year in years]
    diversity = [yearly_data[year]['artist_diversity'] for year in years]
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Total Plays by Year', 'Unique Artists by Year', 
                       'Artist Diversity Index', 'Discovery Rate by Year'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    fig.add_trace(
        go.Scatter(x=years, y=total_plays, mode='lines+markers', name='Total Plays',
                  line=dict(color='#667eea', width=3), marker=dict(size=8)),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(x=years, y=artists, mode='lines+markers', name='Artists',
                  line=dict(color='#e74c3c', width=3), marker=dict(size=8)),
        row=1, col=2
    )
    
    fig.add_trace(
        go.Scatter(x=years, y=diversity, mode='lines+markers', name='Diversity',
                  line=dict(color='#2ecc71', width=3), marker=dict(size=8)),
        row=2, col=1
    )
    
    discovery_rates = [yearly_data[year].get('discovery_rate', yearly_data[year]['avg_daily_plays']) for year in years]
    fig.add_trace(
        go.Scatter(x=years, y=discovery_rates, mode='lines+markers', name='Discovery Rate',
                  line=dict(color='#f39c12', width=3), marker=dict(size=8)),
        row=2, col=2
    )
    
    fig.update_layout(
        title="📈 Your Musical Evolution Over Time",
        height=600,
        showlegend=False,
        font=dict(family="Arial", size=12)
    )
    
    return fig

@st.cache_data(ttl=1800)
def create_musical_phases_chart(patterns: Dict) -> go.Figure:
    """Create musical phases timeline chart"""
    phases_data = patterns.get('yearly_evolution', {}).get('musical_phases', [])
    
    if not phases_data:
        return go.Figure()
    
    fig = go.Figure()
    
    colors = {'Exploration Phase': '#e74c3c', 'Focused Phase': '#3498db', 
             'Intensive Phase': '#f39c12', 'Stable Phase': '#2ecc71'}
    
    for i, phase in enumerate(phases_data):
        start_period = phase.get('start_period', f'Phase {i+1}')
        end_period = phase.get('end_period', f'Phase {i+1}')
        
        fig.add_trace(go.Scatter(
            x=[start_period, end_period],
            y=[i, i],
            mode='lines+markers',
            name=f'Phase {i+1}',
            line=dict(color=colors.get(f'Phase {i+1}', '#95a5a6'), width=8),
            marker=dict(size=12),
            hovertemplate=f"<b>Phase {i+1}</b><br>Period: {start_period} to {end_period}<extra></extra>"
        ))
    
    fig.update_layout(
        title="🎭 Your Musical Phases Over Time",
        xaxis_title="Time Period",
        yaxis_title="Musical Phases",
        height=400,
        font=dict(family="Arial", size=12),
        yaxis=dict(tickmode='array', tickvals=list(range(len(phases_data))), 
                  ticktext=[f"Phase {i+1}" for i in range(len(phases_data))])
    )
    
    return fig

@st.cache_data(ttl=1800)
def create_temporal_heatmap_enhanced(df: pd.DataFrame) -> go.Figure:
    """Create enhanced temporal heatmap with year progression"""
    if df is None or df.empty:
        return go.Figure()
    
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['hour'] = df['timestamp'].dt.hour
    df['year'] = df['timestamp'].dt.year
    
    heatmap_data = df.groupby(['year', 'hour']).size().reset_index(name='count')
    heatmap_pivot = heatmap_data.pivot(index='year', columns='hour', values='count').fillna(0)
    
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_pivot.values,
        x=[f"{h:02d}:00" for h in range(24)],
        y=heatmap_pivot.index,
        colorscale='Viridis',
        showscale=True,
        colorbar=dict(title="Tracks Played")
    ))
    
    fig.update_layout(
        title="🕐 Listening Patterns: Years vs Hours",
        xaxis_title="Hour of Day",
        yaxis_title="Year",
        font=dict(family="Arial", size=12),
        height=500
    )
    
    return fig
