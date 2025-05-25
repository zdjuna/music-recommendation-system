"""
🎵 Music Recommendation System - Web Interface

Beautiful Streamlit dashboard for AI-powered music recommendations
"""

# Load environment variables first thing
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file or config/config.env
env_file = Path('.env')
config_env_file = Path('config/config.env')

# Read the API key once at the top
LASTFM_API_KEY_GLOBAL = None
CYANITE_API_KEY_GLOBAL = None

# Try to load from .env first, then config/config.env
if env_file.exists():
    load_dotenv(env_file, override=True)
    print(f"✅ Loaded environment variables from {env_file}")
elif config_env_file.exists():
    load_dotenv(config_env_file, override=True)
    print(f"✅ Loaded environment variables from {config_env_file}")
else:
    print("⚠️ No .env or config/config.env file found")

LASTFM_API_KEY_GLOBAL = os.getenv('LASTFM_API_KEY')
CYANITE_API_KEY_GLOBAL = os.getenv('CYANITE_API_KEY')
print(f"[DEBUG streamlit_app top] LASTFM_API_KEY_GLOBAL: {LASTFM_API_KEY_GLOBAL}")
print(f"[DEBUG streamlit_app top] CYANITE_API_KEY_GLOBAL: {CYANITE_API_KEY_GLOBAL}")

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import sys
from datetime import datetime, timedelta
import asyncio
from typing import Optional, Dict, Any

# Imports for Roon direct integration
from music_rec.recommenders import RecommendationEngine, RecommendationRequest
from music_rec.exporters import RoonIntegration
# datetime is already imported, asyncio is already imported

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
    from music_rec.data_fetchers import LastFMFetcher
    from music_rec.enrichers import MetadataEnricher  
    from music_rec.analyzers import AIInsightGenerator
    # Import Cyanite functionality
    import test_cyanite_simple
    import enrich_with_cyanite
    ENHANCED_FEATURES_AVAILABLE = True
    CLI_FUNCTIONS_AVAILABLE = True
    CYANITE_FUNCTIONS_AVAILABLE = True
except ImportError as e:
    ENHANCED_FEATURES_AVAILABLE = False
    CLI_FUNCTIONS_AVAILABLE = False
    CYANITE_FUNCTIONS_AVAILABLE = False
    # Debug: print what's missing
    print(f"Import error: {e}")

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

@st.cache_data(ttl=60)  # Cache for 1 minute only
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
        # Using a unique key for the direct integration input
        zone_id_input_direct = st.text_input("Zone ID (Optional)", key="direct_zone_id", placeholder="e.g., kitchen, living_room")

    with col2:
        playlist_mood_input_direct = st.selectbox(
            "Mood (Optional)", 
            ["", "energetic", "calm", "happy", "focus", "sad", "upbeat", "chill", "melancholic"], 
            key="direct_playlist_mood"
        )

    with col3:
        auto_play_input_direct = st.checkbox("Auto-play", value=True, key="direct_auto_play")

    if st.button("🚀 Create Roon Playlist Directly"):
        lastfm_username = get_config_value('LASTFM_USERNAME', 'TestUser')
        if not lastfm_username:
            st.error("🚨 Last.fm username not configured. Please set it up.")
            # Changed to return instead of st.stop() for better flow control
            return

        async def async_create_roon_playlist(
            host: str, 
            user: str, 
            mood: Optional[str], 
            zone: Optional[str], 
            autoplay: bool
        ):
            engine = RecommendationEngine(username=user)
            # Ensure data is loaded for the engine
            if engine.scrobbles_df is None: # Or check specific data needed by engine for recommendations
                return "❌ Last.fm scrobble data not found for the user. Please fetch data first from the 'Data Management' page."

            roon_integration = RoonIntegration(core_host=host, recommendation_engine=engine)
            
            try:
                await roon_integration.connect()
                if not roon_integration.is_connected():
                    return "❌ Failed to connect to Roon Core. Check host IP, ensure Roon Core is running, and the extension is enabled in Roon settings (Settings > Extensions)."

                # Create RecommendationRequest
                req = RecommendationRequest(
                    mood=mood if mood else None, # Pass mood if selected
                    playlist_length=20, # Default playlist length for this quick create
                    # Other RecommendationRequest fields can be left as default or set to None
                    # e.g., energy_level=None, discovery_level=0.3 (default), time_context=None etc.
                )
                
                # Generate a dynamic playlist name
                playlist_name = f"Streamlit {mood.title() if mood else 'Mix'} - {datetime.now().strftime('%Y%m%d %H%M')}"
                
                success = await roon_integration.create_recommendation_playlist(
                    request=req,
                    playlist_name=playlist_name,
                    zone_id=zone if zone else None, # Pass None if zone is empty string or not provided
                    auto_play=autoplay
                )
                
                if success:
                    playback_message = ""
                    if autoplay:
                        if zone:
                            playback_message = "Playback started."
                        else:
                            playback_message = "Playlist created, but playback not started as no zone was specified for autoplay."
                    else:
                        playback_message = "Ready for playback."
                    return f"✅ Successfully created playlist '{playlist_name}' in Roon! {playback_message}"
                else:
                    # Provide more specific feedback if possible
                    return f"⚠️ Failed to create playlist in Roon. This could be due to Roon logs, app permissions, or no tracks matching the recommendation criteria. Please check Roon."
            except Exception as e:
                # Log the full error for debugging
                import logging
                logging.error(f"Error during Roon playlist creation: {e}", exc_info=True)
                return f"❌ An error occurred during Roon playlist creation: {str(e)}"
            finally:
                # Ensure disconnection happens even if errors occurred mid-process
                if roon_integration.is_connected(): 
                    await roon_integration.disconnect()

        with st.spinner(f"🤖 Connecting to Roon and creating '{playlist_mood_input_direct.title() if playlist_mood_input_direct else 'Mix'}' playlist..."):
            result_message = asyncio.run(async_create_roon_playlist(
                host=roon_host,
                user=lastfm_username,
                mood=playlist_mood_input_direct if playlist_mood_input_direct else None,
                zone=zone_id_input_direct if zone_id_input_direct else None,
                autoplay=auto_play_input_direct
            ))
            
            if "✅" in result_message:
                st.success(result_message)
                st.balloons()
            elif "⚠️" in result_message:
                st.warning(result_message)
            else:
                st.error(result_message)

    st.markdown("---")
    st.caption("Legacy CLI command generation (for reference or manual use):")
    # Using different keys for CLI widgets to avoid conflict with direct input widgets
    col_cli1, col_cli2, col_cli3 = st.columns(3)
    with col_cli1:
        zone_id_cli = st.text_input("Zone ID (CLI)", key="cli_zone_id_input", placeholder="e.g., kitchen")
    with col_cli2:
        playlist_mood_cli = st.selectbox("Mood (CLI)", key="cli_playlist_mood_input", options=["", "energetic", "calm", "happy", "focus"])
    with col_cli3:
        auto_play_cli = st.checkbox("Auto-play (CLI)", key="cli_auto_play_input", value=True)

    if st.button("🛠️ Generate Roon Playlist CLI Command"):
        cmd_parts = [
            f"python -m music_rec.cli roon-playlist",
            f"--core-host {roon_host}"
        ]
        
        if zone_id_cli:
            cmd_parts.append(f"--zone-id {zone_id_cli}")
        if playlist_mood_cli:
            cmd_parts.append(f"--mood {playlist_mood_cli}")
        if auto_play_cli:
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
                if CYANITE_FUNCTIONS_AVAILABLE:
                    with st.spinner("Testing Cyanite.ai connection..."):
                        try:
                            # Run the test function
                            result = test_cyanite_simple.test_connection()
                            if result.get('success', False):
                                st.success("✅ Cyanite.ai connection successful!")
                                st.balloons()
                            else:
                                st.error(f"❌ Connection failed: {result.get('error', 'Unknown error')}")
                        except Exception as e:
                            st.error(f"❌ Error testing connection: {str(e)}")
                else:
                    st.code("python test_cyanite_simple.py", language="bash")
                    st.info("💡 Run this to test your Cyanite.ai connection")
        
        with col2:
            if st.button("🎵 Enrich with Cyanite"):
                if CYANITE_FUNCTIONS_AVAILABLE:
                    with st.spinner("Enriching with Cyanite.ai mood analysis... This may take a while."):
                        try:
                            # Run the enrichment function
                            result = execute_enrich_data(username)
                            st.success(f"✅ Cyanite enrichment complete! Processed {result.get('processed_tracks', 0)} tracks")
                            st.balloons()
                            st.cache_data.clear()
                        except Exception as e:
                            st.error(f"❌ Error during Cyanite enrichment: {str(e)}")
                else:
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
    
    if CLI_FUNCTIONS_AVAILABLE:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📥 Fetch Data"):
                with st.spinner("Fetching Last.fm data..."):
                    try:
                        result = execute_fetch_data(username)
                        if result["success"]:
                            st.success(f"✅ Fetched {result.get('total_scrobbles', 0)} scrobbles!")
                            st.balloons()
                            # Clear cache to show updated data
                            st.cache_data.clear()
                        else:
                            st.error(f"❌ Error: {result.get('error', 'Unknown error')}")
                    except Exception as e:
                        st.error(f"❌ Error fetching data: {str(e)}")
        
        with col2:
            if st.button("🎨 Enrich Data"):
                with st.spinner("Enriching data with mood and genre info..."):
                    try:
                        result = execute_enrich_data(username)
                        if result["success"]:
                            st.success(f"✅ Enriched {result.get('processed_tracks', 0)} tracks with research-based emotion analysis!")
                            st.balloons()
                            # Clear cache to show updated data
                            st.cache_data.clear()
                            # Force refresh by rerunning the app
                            st.rerun()
                        else:
                            st.error(f"❌ Error: {result.get('error', 'Unknown error')}")
                    except Exception as e:
                        st.error(f"❌ Error enriching data: {str(e)}")
        
        with col3:
            if st.button("🧠 Analyze Data"):
                with st.spinner("Running AI analysis..."):
                    try:
                        result = execute_analyze_data(username)
                        if result["success"]:
                            st.success("✅ AI analysis complete!")
                            st.balloons()
                            st.cache_data.clear()
                        else:
                            st.error(f"❌ Error: {result.get('error', 'Unknown error')}")
                    except Exception as e:
                        st.error(f"❌ Error during analysis: {str(e)}")
    else:
        # Fallback to showing commands if CLI functions not available
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

def execute_fetch_data(username):
    """Wrapper function to fetch Last.fm data using the actual CLI modules"""
    # import os # No longer needed here if key is passed
    
    # Get API key from the globally loaded variable
    # api_key = os.getenv('LASTFM_API_KEY') # Old way
    api_key = LASTFM_API_KEY_GLOBAL # Use the globally loaded key
    print(f"[DEBUG execute_fetch_data] Using LASTFM_API_KEY: {api_key}") # Debug print

    if not api_key or api_key == "your_lastfm_api_key_here": # Added check for placeholder
        print(f"[ERROR execute_fetch_data] Invalid or placeholder Last.fm API key found: '{api_key}'") # More specific log
        st.error(f"Last.fm API key is missing or a placeholder. Please check your .env file. Key found: '{api_key}'") # Show in UI
        return {"success": False, "error": "LASTFM_API_KEY not found or is a placeholder"}
    
    try:
        # Use the actual CLI fetcher
        print(f"[DEBUG execute_fetch_data] Instantiating LastFMFetcher with API key: '{api_key}' and username: '{username}'") # Log exact key
        fetcher = LastFMFetcher(
            api_key=api_key,
            username=username,
            data_dir='data'
        )
        
        # Fetch data
        df = fetcher.fetch_all_scrobbles(incremental=True)
        
        if df is None or df.empty: # Added df is None check
            return {"success": False, "error": "No data fetched or error during fetch."} # Modified error
        
        # Export to CSV format
        fetcher.export_to_formats(df, ['csv'])
        
        # Get stats
        stats = fetcher.get_summary_stats()
        
        return {
            "success": True,
            "total_scrobbles": len(df),
            "unique_artists": df['artist'].nunique() if 'artist' in df.columns else 0,
            "stats": stats
        }
        
    except Exception as e:
        # Log the full error for debugging
        import logging
        logging.error(f"Exception in execute_fetch_data for {username}: {e}", exc_info=True)
        return {"success": False, "error": str(e)}

def execute_enrich_data(username):
    """Wrapper function to enrich data using MusicBrainz API"""
    
    try:
        # Import from the root directory where the file actually is
        # This import might be problematic if streamlit_app.py is not in the project root
        # For now, assuming it works as per original structure
        from musicbrainz_enricher import MusicBrainzEnricher
        
        # Load scrobbles
        data_file = Path('data') / f"{username}_scrobbles.csv" # Use Path object
        if not data_file.exists(): # Used Path object's exists()
            return {"success": False, "error": f"No scrobble data found for {username} at {data_file}. Please fetch data first."}
        df = pd.read_csv(data_file)
        
        # Get unique tracks to avoid processing duplicates
        unique_tracks = df[['artist', 'track']].drop_duplicates().dropna() # Added dropna
        
        if unique_tracks.empty:
            return {"success": True, "processed_tracks": 0, "message": "No unique tracks to process."}

        # Initialize MusicBrainz enricher with research-based mood analysis
        # These imports might also be problematic if not in PYTHONPATH
        from research_based_emotion_analyzer import ResearchBasedEmotionAnalyzer
        from research_based_mood_analyzer import ResearchBasedMoodAnalyzer
        enricher = MusicBrainzEnricher() # Assuming this has the necessary methods
        # emotion_analyzer = ResearchBasedEmotionAnalyzer() # Not directly used in original snippet with enricher
        mood_analyzer = ResearchBasedMoodAnalyzer() # Used for emotion_vector
        
        # Process with a reasonable limit for web interface
        max_tracks_to_process = min(50, len(unique_tracks))
        
        # Convert to list of dictionaries for MusicBrainz enricher
        tracks_to_process = []
        for _, row in unique_tracks.head(max_tracks_to_process).iterrows():
            tracks_to_process.append({
                'artist': row['artist'],
                'title': row['track'] # 'track' is the correct column name from scrobbles
            })
        
        # Enrich tracks using MusicBrainz (assuming enrich_tracks_batch exists on MusicBrainzEnricher)
        # The original code had `enricher.enrich_tracks_batch`, let's assume it's there.
        if not hasattr(enricher, 'enrich_tracks_batch'):
            st.error("MusicBrainzEnricher does not have `enrich_tracks_batch` method. Cannot proceed with enrichment.")
            return {"success": False, "error": "Enricher method missing."}

        enriched_results = enricher.enrich_tracks_batch(tracks_to_process, max_tracks=max_tracks_to_process)
        
        # Convert results back to DataFrame format with advanced mood analysis
        enriched_data = []
        for track_key, enriched_info in enriched_results.items():
            # track_key is usually "artist - title"
            artist, title = track_key.split(' - ', 1) if ' - ' in track_key else (track_key, "Unknown")

            # Get research-based emotion analysis
            emotion_vector = mood_analyzer.analyze_track_emotion(artist, title) # Assuming this method exists
            
            enriched_data.append({
                'artist': artist,
                'track': title,
                'musicbrainz_tags': ', '.join(enriched_info.get('musicbrainz_tags', [])),
                'musicbrainz_genres': ', '.join(enriched_info.get('musicbrainz_genres', [])),
                'emotion_label': emotion_vector.to_mood_label() if emotion_vector else "N/A",
                'valence': f"{emotion_vector.valence:+.2f}" if emotion_vector else "N/A",
                'arousal': f"{emotion_vector.arousal:+.2f}" if emotion_vector else "N/A",
                'dominance': f"{emotion_vector.dominance:+.2f}" if emotion_vector else "N/A",
                'emotion_confidence': f"{emotion_vector.confidence:.2f}" if emotion_vector else "N/A",
                'emotional_quadrant': _get_emotional_quadrant(emotion_vector) if emotion_vector else "N/A",
                'simplified_mood': enriched_info.get('simplified_mood', 'neutral'),
                'first_release_date': enriched_info.get('first_release_date'),
                'country': enriched_info.get('country'),
                'label': enriched_info.get('label'),
                'musicbrainz_id': enriched_info.get('musicbrainz_id'),
                'musicbrainz_url': enriched_info.get('musicbrainz_url'),
                'length': enriched_info.get('length')
            })
        
        if not enriched_data:
             return {"success": True, "processed_tracks": 0, "message": "No data was enriched."}

        enriched_df = pd.DataFrame(enriched_data)
        
        # Save results
        output_file = Path('data') / f"{username}_enriched.csv" # Use Path object
        enriched_df.to_csv(output_file, index=False)
        
        return {
            "success": True,
            "processed_tracks": len(enriched_df),
            "total_unique_tracks": len(unique_tracks),
            "output_file": str(output_file) # Return string for consistency
        }
        
    except ImportError as e:
        st.error(f"Import error during enrichment: {e}. Please ensure all dependencies are installed and paths are correct.")
        return {"success": False, "error": f"ImportError: {e}"}
    except Exception as e:
        # Log the full error for debugging
        import logging
        logging.error(f"Exception in execute_enrich_data for {username}: {e}", exc_info=True)
        return {"success": False, "error": str(e)}

def _get_emotional_quadrant(emotion_vector): # Assuming emotion_vector can be None
    """Get emotional quadrant for display"""
    if not emotion_vector: return "N/A" # Handle None case
    if emotion_vector.valence > 0 and emotion_vector.arousal > 0:
        return "High Energy Positive"
    elif emotion_vector.valence > 0 and emotion_vector.arousal < 0:
        return "Low Energy Positive"
    elif emotion_vector.valence < 0 and emotion_vector.arousal > 0:
        return "High Energy Negative"
    else: # Handles valence < 0 and arousal < 0, and cases where one is zero
        return "Low Energy Negative"

def execute_analyze_data(username):
    """Wrapper function to analyze data using the actual CLI modules"""
    try:
        # Check if data file exists
        data_file = f"data/{username}_scrobbles.csv"
        if not os.path.exists(data_file):
            return {"success": False, "error": f"No scrobble data found for {username}. Please fetch data first."}
        
        # Load and analyze data
        import pandas as pd
        df = pd.read_csv(data_file)
        
        # Use pattern analyzer from CLI
        from music_rec.analyzers import PatternAnalyzer
        analyzer = PatternAnalyzer(df)
        patterns = analyzer.analyze_all_patterns()
        
        # Try AI insights if API keys are available
        insights = {}
        openai_key = os.getenv('OPENAI_API_KEY')
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        
        if openai_key or anthropic_key:
            ai_generator = AIInsightGenerator(
                openai_api_key=openai_key,
                anthropic_api_key=anthropic_key
            )
            insights = ai_generator.generate_comprehensive_insights(patterns)
        
        # Save analysis results
        results = {
            "patterns": patterns,
            "insights": insights,
            "timestamp": datetime.now().isoformat()
        }
        
        analysis_file = f"data/{username}_analysis.json"
        with open(analysis_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        return {
            "success": True,
            "patterns_analyzed": len(patterns),
            "insights_generated": len(insights),
            "analysis_file": analysis_file
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

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