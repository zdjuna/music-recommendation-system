"""
Temporal Analytics page for enhanced music data analysis
"""

import streamlit as st
import pandas as pd
import logging
from typing import Optional, Dict
from ..utils.config import config
from ..models.database import db
from ..components.charts import (
    create_musical_phases_timeline, 
    create_year_over_year_comparison,
    create_listening_evolution_chart
)

@st.cache_data(ttl=600)
def load_temporal_data(username: str) -> Optional[pd.DataFrame]:
    """Load user data for temporal analysis"""
    try:
        stats = db.get_user_stats(username)
        if stats['total_scrobbles'] > 0:
            pass
    except Exception as e:
        logging.warning(f"Database load failed: {e}")
    
    data_dir = config.data_dir
    scrobbles_file = data_dir / f"{username}_scrobbles.csv"
    
    if scrobbles_file.exists():
        try:
            df = pd.read_csv(scrobbles_file)
            if 'timestamp' in df.columns:
                df['datetime'] = pd.to_datetime(df['timestamp'])
            elif 'date' in df.columns:
                df['datetime'] = pd.to_datetime(df['date'])
            else:
                st.error("No timestamp column found in data")
                return None
            
            return df
        except Exception as e:
            st.error(f"Error loading data: {e}")
            return None
    
    return None

@st.cache_data(ttl=600)
def analyze_temporal_patterns(df: pd.DataFrame) -> Dict:
    """Analyze temporal patterns using PatternAnalyzer"""
    try:
        import sys
        from pathlib import Path
        sys.path.append(str(Path(__file__).parent.parent.parent / 'src'))
        from music_rec.analyzers.pattern_analyzer import PatternAnalyzer
        
        analyzer = PatternAnalyzer(df)
        patterns = analyzer.analyze_all_patterns()
        
        return patterns
    except Exception as e:
        st.error(f"Error analyzing patterns: {e}")
        return {}

def show_temporal_analytics():
    """Main temporal analytics page"""
    
    # Header
    st.markdown("""
    <div style="background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); 
                padding: 2rem; border-radius: 10px; color: white; text-align: center; margin-bottom: 2rem;">
        <h1>📈 Temporal Analytics</h1>
        <p>Deep insights into your musical evolution and listening phases</p>
    </div>
    """, unsafe_allow_html=True)
    
    username = config.default_username
    
    with st.spinner("Loading temporal data..."):
        df = load_temporal_data(username)
    
    if df is None or df.empty:
        st.warning("📭 No temporal data available for analysis")
        st.info("""
        **To use temporal analytics:**
        1. Ensure you have scrobbles data in the `data/` directory
        2. File should be named `{username}_scrobbles.csv`
        3. Data should include timestamp and artist/track information
        """)
        return
    
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
    
    st.markdown("---")
    
    with st.spinner("Analyzing temporal patterns..."):
        patterns = analyze_temporal_patterns(df)
    
    if not patterns:
        st.error("Failed to analyze temporal patterns")
        return
    
    st.subheader("🎭 Musical Phases Detection")
    
    if 'musical_phases' in patterns:
        phases_data = patterns['musical_phases']
        
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
    
    st.markdown("---")
    
    st.subheader("🔍 Additional Insights")
    
    if 'genre_evolution' in patterns:
        genre_data = patterns['genre_evolution']
        
        with st.expander("🎵 Genre Evolution"):
            st.json(genre_data)
    
    if 'listening_intensity' in patterns:
        intensity_data = patterns['listening_intensity']
        
        with st.expander("⚡ Listening Intensity Analysis"):
            col1, col2 = st.columns(2)
            
            with col1:
                avg_daily = intensity_data.get('avg_daily_plays', 0)
                st.metric("Average Daily Plays", f"{avg_daily:.1f}")
                
                high_activity = intensity_data.get('high_activity_days', 0)
                st.metric("High Activity Days", high_activity)
            
            with col2:
                variability = intensity_data.get('listening_variability', 0)
                st.metric("Listening Variability", f"{variability:.1f}")
                
                consistency = intensity_data.get('consistency_score', 0)
                st.metric("Consistency Score", f"{consistency:.2f}")
    
    if 'discovery' in patterns:
        discovery_data = patterns['discovery']
        
        with st.expander("🔍 Discovery Patterns"):
            col1, col2 = st.columns(2)
            
            with col1:
                discovery_rate = discovery_data.get('discovery_rate', 0)
                st.metric("Discovery Rate", f"{discovery_rate:.3f}")
                
                peak_discovery = discovery_data.get('peak_discovery_month', 'Unknown')
                st.metric("Peak Discovery Month", peak_discovery)
            
            with col2:
                recent_discoveries = discovery_data.get('recent_discoveries', 0)
                st.metric("Recent Discoveries", recent_discoveries)
                
                discovery_trend = discovery_data.get('discovery_trend', 'Unknown')
                st.metric("Discovery Trend", discovery_trend)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 1rem;">
        📈 Temporal Analytics powered by advanced pattern recognition
        <br><small>Analyzing your musical journey through time</small>
    </div>
    """, unsafe_allow_html=True)
