"""
🎵 Music Recommendation System - Web Interface

Beautiful Streamlit dashboard for AI-powered music recommendations
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import asyncio
from typing import Optional, Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Configure page
st.set_page_config(
    page_title="🎵 Music Recommendation System",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import new features
try:
    from music_rec.analyzers.real_time_updater import StreamlitUpdater
    from music_rec.exporters.multi_platform_exporter import StreamlitExportHelper
    ENHANCED_FEATURES_AVAILABLE = True
except ImportError:
    ENHANCED_FEATURES_AVAILABLE = False

# Custom CSS for beautiful styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
    }
    
    .success-banner {
        background: linear-gradient(90deg, #56ab2f 0%, #a8e6cf 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 1rem 0;
    }
    
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        border: none;
        border-radius: 25px;
        color: white;
        font-weight: bold;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

# Configuration management
def get_config_value(key: str, default: str = "") -> str:
    """Get configuration value from Streamlit secrets or environment variables."""
    try:
        # Try Streamlit secrets first
        return st.secrets[key]
    except (KeyError, FileNotFoundError):
        # Fall back to environment variables
        return os.getenv(key, default)

# Set default configuration values
DEFAULT_CONFIG = {
    'LASTFM_USERNAME': 'zdjuna',
    'ROON_CORE_HOST': '192.168.1.213',
    'ROON_CORE_PORT': '9330',
    'MAX_TRACKS_PER_REQUEST': '200',
    'DEFAULT_DISCOVERY_LEVEL': 'medium',
    'LOG_LEVEL': 'INFO'
}

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_user_data(username: str) -> Dict[str, Any]:
    """Load user's music data and stats with caching"""
    data_dir = Path('data')
    
    # Check for data files
    scrobbles_file = data_dir / f"{username}_scrobbles.csv"
    enriched_file = data_dir / f"{username}_enriched.csv"
    stats_file = data_dir / f"{username}_stats.json"
    
    result = {
        'has_scrobbles': scrobbles_file.exists(),
        'has_enriched': enriched_file.exists(),
        'has_stats': stats_file.exists(),
        'scrobbles': None,
        'enriched': None,
        'stats': None
    }
    
    try:
        if result['has_scrobbles']:
            result['scrobbles'] = pd.read_csv(scrobbles_file)
            
        if result['has_enriched']:
            result['enriched'] = pd.read_csv(enriched_file)
            
        if result['has_stats']:
            with open(stats_file) as f:
                result['stats'] = json.load(f)
    except Exception as e:
        st.error(f"Error loading data: {e}")
        # Log the error for debugging
        import logging
        logging.error(f"Data loading error for {username}: {e}")
    
    return result

@st.cache_data(ttl=600)  # Cache for 10 minutes
def create_listening_timeline(df: pd.DataFrame) -> go.Figure:
    """Create beautiful listening timeline chart with caching"""
    if df is None or df.empty:
        return go.Figure()
    
    # Convert timestamp to datetime
    df['date'] = pd.to_datetime(df['timestamp'])
    df['hour'] = df['date'].dt.hour
    df['day_of_week'] = df['date'].dt.day_name()
    
    # Create heatmap of listening patterns
    heatmap_data = df.groupby(['day_of_week', 'hour']).size().reset_index(name='count')
    
    # Reorder days
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
            )
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

def create_mood_distribution(df: pd.DataFrame) -> go.Figure:
    """Create mood distribution pie chart"""
    if df is None or df.empty or 'mood_primary' not in df.columns:
        return go.Figure()
    
    mood_counts = df['mood_primary'].value_counts()
    
    fig = go.Figure(data=[go.Pie(
        labels=mood_counts.index,
        values=mood_counts.values,
        hole=0.3,
        marker=dict(colors=px.colors.qualitative.Set3)
    )])
    
    fig.update_layout(
        title="🎭 Your Music Moods",
        font=dict(family="Arial", size=12),
        height=400
    )
    
    return fig

def show_dashboard():
    """Main dashboard page"""
    
    # Main header
    st.markdown("""
    <div class="main-header">
        <h1>🎵 Music Recommendation System</h1>
        <p>AI-powered insights into your musical journey</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize real-time features if available
    username = get_config_value('LASTFM_USERNAME', 'TestUser')
    if ENHANCED_FEATURES_AVAILABLE:
        StreamlitUpdater.initialize_realtime_updates(username)
    
    # Load user data
    user_data = load_user_data(username)
    
    # Real-time status (if available)
    if ENHANCED_FEATURES_AVAILABLE:
        st.subheader("⚡ Real-Time Status")
        StreamlitUpdater.show_realtime_status()
        st.markdown("---")
    
    # Quick stats overview
    st.subheader("📊 Quick Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    scrobbles_count = len(user_data['scrobbles']) if user_data['scrobbles'] is not None else 0
    enriched_count = len(user_data['enriched']) if user_data['enriched'] is not None else 0
    
    with col1:
        st.metric("Total Scrobbles", f"{scrobbles_count:,}")
    
    with col2:
        if user_data['scrobbles'] is not None:
            unique_artists = user_data['scrobbles']['artist'].nunique()
            st.metric("Unique Artists", f"{unique_artists:,}")
        else:
            st.metric("Unique Artists", "N/A")
    
    with col3:
        st.metric("Enriched Tracks", f"{enriched_count:,}")
    
    with col4:
        if user_data['stats']:
            listening_time = user_data['stats'].get('total_listening_time_days', 0)
            st.metric("Days of Music", f"{listening_time:.1f}")
        else:
            st.metric("Days of Music", "N/A")
    
    # Show charts if data is available
    if user_data['scrobbles'] is not None and not user_data['scrobbles'].empty:
        
        # Timeline and patterns
        col1, col2 = st.columns(2)
        
        with col1:
            with st.spinner("Creating listening timeline..."):
                timeline_fig = create_listening_timeline(user_data['scrobbles'])
                st.plotly_chart(timeline_fig, use_container_width=True)
        
        with col2:
            with st.spinner("Analyzing top artists..."):
                artists_fig = create_top_artists_chart(user_data['scrobbles'])
                st.plotly_chart(artists_fig, use_container_width=True)
        
        # Mood distribution if available
        if user_data['enriched'] is not None and not user_data['enriched'].empty:
            mood_fig = create_mood_distribution(user_data['enriched'])
            if mood_fig:
                st.plotly_chart(mood_fig, use_container_width=True)
        
        # Recent listening activity
        st.subheader("🎵 Recent Activity")
        recent_tracks = user_data['scrobbles'].head(10)[['artist', 'track', 'timestamp']]
        recent_tracks['timestamp'] = pd.to_datetime(recent_tracks['timestamp'])
        recent_tracks['timestamp'] = recent_tracks['timestamp'].dt.strftime('%Y-%m-%d %H:%M')
        st.dataframe(recent_tracks, use_container_width=True)
        
    else:
        st.warning("📭 No scrobble data found. Check the Data Management page to fetch your Last.fm data!")

def show_recommendations():
    """Recommendations page"""
    st.header("🎯 Generate Recommendations")
    
    username = st.sidebar.text_input("Last.fm Username", value=get_config_value('LASTFM_USERNAME', 'TestUser'))
    
    if not username:
        st.warning("⚠️ Please enter your Last.fm username")
        return
    
    # Check if data exists
    user_data = load_user_data(username)
    if not user_data['has_scrobbles']:
        st.error("❌ No music data found. Please fetch your data first!")
        return
    
    # Recommendation form
    st.subheader("🎵 Customize Your Playlist")
    
    col1, col2 = st.columns(2)
    
    with col1:
        mood = st.selectbox(
            "🎭 Mood",
            ["", "happy", "sad", "calm", "energetic", "melancholic", "upbeat", "chill"],
            help="Choose the mood for your playlist"
        )
        
        energy_level = st.selectbox(
            "⚡ Energy Level",
            ["", "low", "medium", "high"],
            help="Energy level of the tracks"
        )
        
        time_context = st.selectbox(
            "🕐 Time Context",
            ["", "morning", "afternoon", "evening", "night"],
            help="When will you listen to this playlist?"
        )
    
    with col2:
        playlist_length = st.slider(
            "📝 Playlist Length",
            min_value=5,
            max_value=50,
            value=20,
            help="Number of tracks in the playlist"
        )
        
        discovery_level = st.slider(
            "🔍 Discovery Level",
            min_value=0.0,
            max_value=1.0,
            value=0.3,
            step=0.1,
            help="0.0 = only familiar tracks, 1.0 = only new discoveries"
        )
        
        exclude_recent = st.checkbox(
            "🚫 Exclude Recent Tracks",
            value=True,
            help="Exclude recently played tracks"
        )
    
    # Generate button
    if st.button("🎵 Generate Playlist", type="primary"):
        with st.spinner("🤖 AI is creating your perfect playlist..."):
            try:
                # Import here to avoid startup delays
                from music_rec.recommenders import RecommendationEngine, RecommendationRequest
                
                # Create recommendation request
                request = RecommendationRequest(
                    mood=mood if mood else None,
                    energy_level=energy_level if energy_level else None,
                    time_context=time_context if time_context else None,
                    playlist_length=playlist_length,
                    discovery_level=discovery_level,
                    exclude_recent=exclude_recent
                )
                
                # Generate recommendations
                engine = RecommendationEngine(username=username)
                result = engine.generate_recommendations(request)
                
                if result.tracks:
                    st.markdown("""
                    <div class="success-banner">
                        <h3>🎉 Your Playlist is Ready!</h3>
                        <p>AI confidence: {:.1%}</p>
                    </div>
                    """.format(result.confidence_score), unsafe_allow_html=True)
                    
                    # Display explanation
                    st.info(f"💭 **Playlist Explanation:** {result.explanation}")
                    
                    # Create playlist DataFrame
                    playlist_df = pd.DataFrame([
                        {
                            'Track': track.get('track', 'Unknown'),
                            'Artist': track.get('artist', 'Unknown'),
                            'Album': track.get('album', 'Unknown'),
                            'Score': f"{track.get('total_score', 0):.3f}",
                            'Mood': track.get('mood', 'N/A'),
                            'Energy': track.get('energy', 'N/A')
                        }
                        for track in result.tracks
                    ])
                    
                    st.subheader("🎵 Your Personalized Playlist")
                    st.dataframe(playlist_df, use_container_width=True, height=400)
                    
                    # Download options
                    st.subheader("💾 Download Options")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        csv_data = playlist_df.to_csv(index=False)
                        st.download_button(
                            "📊 Download CSV",
                            csv_data,
                            f"playlist_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            "text/csv"
                        )
                    
                    with col2:
                        json_data = json.dumps(result.tracks, indent=2)
                        st.download_button(
                            "📄 Download JSON",
                            json_data,
                            f"playlist_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            "application/json"
                        )
                    
                    with col3:
                        # Download as M3U playlist
                        track_list = []
                        for track in result.tracks:
                            artist = track.get('artist', 'Unknown')
                            title = track.get('track', 'Unknown')
                            track_list.append(f"{artist} - {title}")
                        
                        m3u_content = "#EXTM3U\n" + "\n".join(track_list)
                        
                        st.download_button(
                            "🎵 Download M3U",
                            m3u_content,
                            f"playlist_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.m3u",
                            "audio/x-mpegurl"
                        )
                
                else:
                    st.error("❌ No recommendations generated. Try adjusting your parameters!")
                
                # Enhanced export functionality
                if ENHANCED_FEATURES_AVAILABLE and 'result' in locals() and result:
                    st.markdown("---")
                    st.subheader("🚀 Enhanced Export Options")
                    
                    # Create export interface
                    default_name = f"{mood.title()} Vibes - {datetime.now().strftime('%B %Y')}" if mood else "My Recommendations"
                    StreamlitExportHelper.show_export_interface(result.tracks, default_name)
                        
            except Exception as e:
                st.error(f"❌ Error generating recommendations: {e}")

def show_roon_integration():
    """Roon integration page"""
    st.header("🎵 Roon Integration")
    
    roon_host = st.sidebar.text_input(
        "Roon Core Host",
        value=get_config_value('ROON_CORE_HOST', '192.168.1.213'),
        help="IP address of your Roon Core"
    )
    
    if not roon_host:
        st.warning("⚠️ Please enter your Roon Core IP address")
        return
    
    st.info("""
    🎵 **Roon Integration Features:**
    - Direct playlist creation in Roon
    - Zone-specific recommendations
    - Real-time auto-sync
    - Context-aware suggestions
    """)
    
    # Connection test
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔌 Test Roon Connection"):
            st.info("🔄 Testing connection to Roon Core...")
            st.info(f"💡 In terminal, run: `python -m music_rec.cli roon-connect --core-host {roon_host}`")
    
    with col2:
        if st.button("🏠 Show Zones"):
            st.info("🔄 Getting zone information...")
            st.info(f"💡 In terminal, run: `python -m music_rec.cli roon-zones --core-host {roon_host}`")
    
    # Quick playlist creation
    st.subheader("🎵 Quick Roon Playlist")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        zone_id = st.text_input("Zone ID", placeholder="e.g., kitchen, living_room")
        
    with col2:
        playlist_mood = st.selectbox("Mood", ["", "energetic", "calm", "happy", "focus"])
        
    with col3:
        auto_play = st.checkbox("Auto-play", value=True)
    
    if st.button("🎵 Create Roon Playlist"):
        cmd_parts = [
            f"python -m music_rec.cli roon-playlist",
            f"--core-host {roon_host}"
        ]
        
        if zone_id:
            cmd_parts.append(f"--zone-id {zone_id}")
        if playlist_mood:
            cmd_parts.append(f"--mood {playlist_mood}")
        if auto_play:
            cmd_parts.append("--auto-play")
        
        command = " ".join(cmd_parts)
        
        st.code(command, language="bash")
        st.info("💡 Run this command in your terminal to create the playlist!")

def show_data_management():
    """Data management page"""
    st.header("📊 Data Management")
    
    username = st.sidebar.text_input("Last.fm Username", value=get_config_value('LASTFM_USERNAME', 'TestUser'))
    
    # Data status
    st.subheader("📈 Data Status")
    user_data = load_user_data(username)
    
    status_df = pd.DataFrame([
        {"Data Type": "Scrobbles", "Status": "✅ Available" if user_data['has_scrobbles'] else "❌ Missing"},
        {"Data Type": "Enriched", "Status": "✅ Available" if user_data['has_enriched'] else "❌ Missing"},
        {"Data Type": "Statistics", "Status": "✅ Available" if user_data['has_stats'] else "❌ Missing"}
    ])
    
    st.dataframe(status_df, use_container_width=True)
    
    # Cyanite.ai Integration
    st.subheader("🎭 Cyanite.ai Mood Analysis")
    
    # Check if Cyanite is configured
    cyanite_key = get_config_value('CYANITE_API_KEY')
    if not cyanite_key or cyanite_key == 'your_cyanite_api_key_here':
        st.warning("⚠️ Cyanite.ai API not configured")
        st.info("""
        🎵 **Professional Mood Analysis with Cyanite.ai**
        
        Get much more accurate mood classifications for your music using Cyanite's professional music analysis API.
        
        **To set up:**
        1. Run: `python setup_cyanite.py`
        2. Follow the setup guide to get your API key
        3. Come back here to enrich your data!
        """)
        
        if st.button("🔧 Run Cyanite Setup"):
            st.code("python setup_cyanite.py", language="bash")
            st.info("💡 Run this command in your terminal to set up Cyanite.ai")
    else:
        st.success("✅ Cyanite.ai API configured!")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🎭 Test Cyanite Connection"):
                st.code("python test_cyanite_simple.py", language="bash")
                st.info("💡 Run this to test your Cyanite.ai connection")
        
        with col2:
            if st.button("🎵 Enrich with Cyanite"):
                st.code("python enrich_with_cyanite.py", language="bash")
                st.info("💡 Run this to add professional mood analysis to your music")
        
        # Advanced Cyanite options
        with st.expander("🔧 Advanced Cyanite Options"):
            st.info("""
            **What Cyanite.ai provides:**
            - 🎭 Professional mood classification
            - ⚡ Energy and valence analysis  
            - 💃 Danceability scoring
            - 🎵 Tempo and key detection
            - 🏷️ Genre and style tags
            - 🎯 Much more accurate than basic APIs
            
            **Perfect for:**
            - 🎵 Creating mood-based playlists
            - 📊 Understanding your music taste
            - 🎯 Better recommendations
            """)
    
    # Data actions
    st.subheader("🔧 Data Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📥 Fetch Data"):
            st.code(f"python -m music_rec.cli fetch --username {username}", language="bash")
            st.info("💡 Run this command to fetch your Last.fm data")
    
    with col2:
        if st.button("🎨 Enrich Data"):
            st.code(f"python -m music_rec.cli enrich --username {username}", language="bash")
            st.info("💡 Run this command to add mood and genre data")
    
    with col3:
        if st.button("🧠 Analyze Data"):
            st.code(f"python -m music_rec.cli analyze --username {username}", language="bash")
            st.info("💡 Run this command for AI analysis")

def show_realtime_monitoring():
    """Real-Time Monitoring page"""
    st.header("⚡ Real-Time Monitoring")
    
    # Initialize real-time features if available
    username = get_config_value('LASTFM_USERNAME', 'TestUser')
    if ENHANCED_FEATURES_AVAILABLE:
        StreamlitUpdater.initialize_realtime_updates(username)
    
    # Show real-time status
    st.subheader("🎵 Real-Time Status")
    StreamlitUpdater.show_realtime_status()
    
    # Show recent activity and insights
    st.subheader("📈 Recent Activity Analysis")
    
    # Get recent updates if available
    if 'rt_updater' in st.session_state:
        recent_updates = st.session_state.rt_updater.get_recent_updates()
        
        if recent_updates.get('update_history'):
            st.subheader("📋 Update History")
            
            # Show recent updates in a table
            history_data = []
            for update in recent_updates['update_history'][-5:]:  # Last 5 updates
                history_data.append({
                    'Time': pd.to_datetime(update['timestamp']).strftime('%Y-%m-%d %H:%M'),
                    'New Scrobbles': update.get('new_scrobbles_count', 0),
                    'New Artists': len(update.get('new_artists', [])),
                    'Intensity': f"{update.get('listening_intensity', 0):.1f} tracks/hr"
                })
            
            if history_data:
                df = pd.DataFrame(history_data)
                st.dataframe(df, use_container_width=True)
        else:
            st.info("No recent updates yet. Check back after some music listening!")
    
    # Manual monitoring controls
    st.subheader("🔧 Monitoring Controls")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("▶️ Start Background Monitoring"):
            if ENHANCED_FEATURES_AVAILABLE:
                StreamlitUpdater.start_background_monitoring()
            else:
                st.error("Enhanced features not available")
    
    with col2:
        if st.button("⏹️ Stop Monitoring"):
            if 'rt_updater' in st.session_state:
                st.session_state.rt_updater.stop_monitoring()
                st.success("Monitoring stopped")
    
    # Real-time insights
    st.subheader("🎯 Real-Time Insights")
    st.info("""
    **Real-time monitoring provides:**
    - 🎵 Detection of new scrobbles as they happen
    - 🎨 Automatic mood shift analysis
    - 👥 Discovery of new artists in your listening
    - 📊 Listening intensity tracking
    - 🔄 Smart recommendation refresh triggers
    
    **Note:** Monitoring runs in the background and checks for updates every 5 minutes.
    """)

def main():
    """Main app function"""
    # Sidebar navigation
    st.sidebar.title("🎵 Navigation")
    
    # Navigation options (include new features if available)
    nav_options = ["🏠 Dashboard", "🎯 Recommendations", "🎵 Roon Integration", "📊 Data Management"]
    if ENHANCED_FEATURES_AVAILABLE:
        nav_options.insert(-1, "⚡ Real-Time Monitoring")
    
    page = st.sidebar.radio("Choose a page:", nav_options)
    
    # Show version and feature status
    st.sidebar.markdown("---")
    st.sidebar.markdown("**🔧 System Status**")
    if ENHANCED_FEATURES_AVAILABLE:
        st.sidebar.success("✅ Enhanced features active")
    else:
        st.sidebar.info("ℹ️ Basic features active")
    
    # Route to pages
    if page == "🏠 Dashboard":
        show_dashboard()
    elif page == "🎯 Recommendations":
        show_recommendations()
    elif page == "⚡ Real-Time Monitoring" and ENHANCED_FEATURES_AVAILABLE:
        show_realtime_monitoring()
    elif page == "🎵 Roon Integration":
        show_roon_integration()
    elif page == "📊 Data Management":
        show_data_management()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 1rem;">
        🎵 Music Recommendation System v5.2 | Built with ❤️ and AI
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 