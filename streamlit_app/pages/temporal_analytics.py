"""
Enhanced Temporal Analytics Dashboard
"""

import streamlit as st
import pandas as pd
import logging
import json
import sys
import os
from pathlib import Path
from typing import Optional, Dict

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from streamlit_app.utils.config import config
from streamlit_app.models.database import db
from streamlit_app.components.charts import (
    create_listening_timeline,
    create_artist_discovery_timeline,
    create_musical_phases_timeline, 
    create_year_over_year_comparison,
    create_listening_evolution_chart
)

try:
    from streamlit_app.components.charts import (
        create_yearly_evolution_chart, 
        create_musical_phases_chart
    )
except ImportError:
    def create_yearly_evolution_chart(patterns):
        import plotly.graph_objects as go
        return go.Figure().add_annotation(text="Chart loading...", x=0.5, y=0.5)
    
    def create_musical_phases_chart(patterns):
        import plotly.graph_objects as go
        return go.Figure().add_annotation(text="Chart loading...", x=0.5, y=0.5)

from src.music_rec.analyzers.pattern_analyzer import PatternAnalyzer
from src.music_rec.analyzers.ai_insights import AIInsightGenerator

@st.cache_data(ttl=300)
def load_and_analyze_temporal_data(username: str):
    """Load user data and perform temporal analysis"""
    try:
        data_dir = config.data_dir
        scrobbles_file = data_dir / f"{username}_scrobbles.csv"
        
        if not scrobbles_file.exists():
            return None
        
        df = pd.read_csv(scrobbles_file)
        
        if 'timestamp' in df.columns:
            df['datetime'] = pd.to_datetime(df['timestamp'])
        elif 'date' in df.columns:
            df['datetime'] = pd.to_datetime(df['date'])
        else:
            return None
        
        analyzer = PatternAnalyzer(df)
        patterns = analyzer.analyze_all_patterns()
        
        ai_generator = AIInsightGenerator(
            openai_api_key=os.getenv('OPENAI_API_KEY'),
            anthropic_api_key=os.getenv('ANTHROPIC_API_KEY')
        )
        insights = ai_generator.generate_comprehensive_insights(patterns)
        
        return {
            'data': df,
            'patterns': patterns,
            'insights': insights
        }
        
    except Exception as e:
        logging.error(f"Failed to load temporal data: {e}")
        return None

def show_temporal_analytics():
    """Enhanced temporal analytics dashboard page"""
    
    st.markdown("""
    <div style="background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); 
                padding: 2rem; border-radius: 10px; color: white; text-align: center; margin-bottom: 2rem;">
        <h1>📈 Enhanced Temporal Analytics</h1>
        <p>Deep insights into your musical evolution over time</p>
    </div>
    """, unsafe_allow_html=True)
    
    username = config.default_username
    
    with st.spinner("Analyzing your musical evolution..."):
        temporal_data = load_and_analyze_temporal_data(username)
    
    if not temporal_data:
        st.error("❌ No data available for temporal analysis. Please import your music data first.")
        st.info("""
        **To use temporal analytics:**
        1. Ensure you have scrobbles data in the `data/` directory
        2. File should be named `{username}_scrobbles.csv`
        3. Data should include timestamp and artist/track information
        """)
        return
    
    patterns = temporal_data['patterns']
    insights = temporal_data['insights']
    df = temporal_data['data']
    
    st.subheader("📊 Data Overview")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Scrobbles", f"{len(df):,}")
    
    with col2:
        date_range = (df['datetime'].max() - df['datetime'].min()).days
        st.metric("Date Range", f"{date_range:,} days")
    
    with col3:
        years_span = df['datetime'].dt.year.nunique()
        st.metric("Years Covered", f"{years_span}")
    
    with col4:
        avg_daily = len(df) / max(date_range, 1)
        st.metric("Avg Daily Plays", f"{avg_daily:.1f}")
    
    if 'temporal_evolution' in insights:
        st.subheader("🧠 AI Analysis of Your Musical Evolution")
        st.markdown(insights['temporal_evolution'])
        st.markdown("---")
    
    st.subheader("🎭 Musical Phases Detection")
    
    if 'enhanced_musical_phases' in patterns:
        phases_data = patterns['enhanced_musical_phases']
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_phases = phases_data.get('total_phases', 0)
            st.metric("Detected Phases", total_phases)
        
        with col2:
            phase_summary = phases_data.get('phase_summary', {})
            dominant_pattern = phase_summary.get('dominant_pattern', 'Unknown')
            st.metric("Dominant Pattern", dominant_pattern)
        
        with col3:
            quarterly_metrics = phases_data.get('quarterly_metrics', [])
            st.metric("Quarters Analyzed", len(quarterly_metrics))
        
        if phases_data:
            phases_fig = create_musical_phases_timeline(phases_data)
            st.plotly_chart(phases_fig, use_container_width=True)
        
        with st.expander("🔍 Phase Details"):
            detected_phases = phases_data.get('detected_phases', [])
            if detected_phases:
                phases_df = pd.DataFrame(detected_phases)
                st.dataframe(phases_df, use_container_width=True)
            else:
                st.info("No significant phase changes detected. Your listening patterns appear stable.")
    
    st.markdown("---")
    
    st.subheader("📊 Year-over-Year Evolution")
    
    col1, col2 = st.columns(2)
    
    with col1:
        with st.spinner("Creating evolution charts..."):
            evolution_fig = create_yearly_evolution_chart(patterns)
            st.plotly_chart(evolution_fig, use_container_width=True)
    
    with col2:
        with st.spinner("Analyzing musical phases..."):
            phases_fig = create_musical_phases_chart(patterns)
            st.plotly_chart(phases_fig, use_container_width=True)
    
    if 'year_over_year_evolution' in patterns:
        evolution_data = patterns['year_over_year_evolution']
        
        overall_growth = evolution_data.get('overall_growth', {})
        evolution_summary = evolution_data.get('listening_evolution_summary', {})
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_years = evolution_data.get('total_years', 0)
            st.metric("Years Analyzed", total_years)
        
        with col2:
            growth_pct = overall_growth.get('total_plays_growth_pct', 0)
            st.metric("Total Growth", f"{growth_pct:.1f}%")
        
        with col3:
            pattern = evolution_summary.get('pattern', 'Unknown')
            st.metric("Evolution Pattern", pattern)
        
        if evolution_data:
            evolution_fig = create_year_over_year_comparison(evolution_data)
            st.plotly_chart(evolution_fig, use_container_width=True)
        
        if evolution_data.get('evolution_trends'):
            trends_fig = create_listening_evolution_chart(evolution_data)
            st.plotly_chart(trends_fig, use_container_width=True)
        
        with st.expander("📅 Yearly Breakdown"):
            yearly_metrics = evolution_data.get('yearly_metrics', [])
            if yearly_metrics:
                yearly_df = pd.DataFrame(yearly_metrics)
                st.dataframe(yearly_df, use_container_width=True)
    
    yearly_evolution = patterns.get('yearly_evolution', {})
    musical_phases = yearly_evolution.get('musical_phases', [])
    
    if musical_phases:
        st.subheader("🎭 Your Musical Phases")
        
        for i, phase in enumerate(musical_phases):
            with st.expander(f"Phase {i+1}: {phase['start_period']} to {phase['end_period']}"):
                characteristics = phase['characteristics']
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Plays", f"{characteristics.get('total_plays', 0):,}")
                with col2:
                    st.metric("Unique Artists", f"{characteristics.get('unique_artists', 0):,}")
                with col3:
                    st.metric("Discovery Rate", f"{characteristics.get('discovery_rate', 0):.1%}")
                
                st.write("**Top Genres/Artists:**")
                top_genres = characteristics.get('top_genres', [])
                if top_genres:
                    st.write(", ".join(top_genres[:5]))
    
    st.subheader("🕐 Detailed Timeline Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        timeline_fig = create_listening_timeline(df)
        st.plotly_chart(timeline_fig, use_container_width=True)
    
    with col2:
        discovery_fig = create_artist_discovery_timeline(df)
        st.plotly_chart(discovery_fig, use_container_width=True)
    
    yearly_stats = yearly_evolution.get('yearly_stats', {})
    if yearly_stats:
        st.subheader("📋 Year-by-Year Statistics")
        
        stats_df = pd.DataFrame.from_dict(yearly_stats, orient='index')
        stats_df.index.name = 'Year'
        stats_df = stats_df.round(2)
        
        st.dataframe(stats_df, use_container_width=True)
    
    st.markdown("---")
    st.subheader("💾 Export Analysis")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Export Charts as Images"):
            st.info("Chart export functionality coming soon!")
    
    with col2:
        if st.button("📋 Export Data as CSV"):
            if yearly_stats:
                csv = pd.DataFrame.from_dict(yearly_stats, orient='index').to_csv()
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"{username}_temporal_analysis.csv",
                    mime="text/csv"
                )
    
    with col3:
        if st.button("📄 Generate Report"):
from streamlit_app.utils.config import
