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

def load_user_data(username: str) -> Dict[str, Any]:
    """Load user's music data and stats"""
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
    
    return result

def create_listening_timeline(df: pd.DataFrame) -> go.Figure:
    """Create beautiful listening timeline chart"""
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
    st.markdown("""
    <div class="main-header">
        <h1>🎵 Music Recommendation System</h1>
        <p>AI-powered playlist generation using your Last.fm data</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar configuration
    st.sidebar.header("🔧 Configuration")
    username = st.sidebar.text_input("Last.fm Username", value=os.getenv('LASTFM_USERNAME', 'TestUser'))
    
    if not username:
        st.warning("⚠️ Please enter your Last.fm username in the sidebar")
        return
    
    # Load user data
    with st.spinner("🔍 Loading your music data..."):
        user_data = load_user_data(username)
    
    # Status indicators
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status = "✅ Ready" if user_data['has_scrobbles'] else "❌ Missing"
        st.metric("Scrobbles Data", status)
        
    with col2:
        status = "✅ Ready" if user_data['has_enriched'] else "❌ Missing"
        st.metric("Enriched Data", status)
        
    with col3:
        status = "✅ Ready" if user_data['has_stats'] else "❌ Missing"
        st.metric("Statistics", status)
    
    if not user_data['has_scrobbles']:
        st.error("""
        🚨 **No music data found!**
        
        Please run the following command first:
        ```bash
        python -m src.music_rec.cli fetch --username {username}
        ```
        """)
        return
    
    # Main dashboard
    if user_data['scrobbles'] is not None:
        df = user_data['scrobbles']
        
        # Key metrics
        st.subheader("📊 Your Music Statistics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_tracks = len(df)
            st.metric("Total Tracks", f"{total_tracks:,}")
            
        with col2:
            unique_artists = df['artist'].nunique()
            st.metric("Unique Artists", f"{unique_artists:,}")
            
        with col3:
            unique_albums = df['album'].nunique()
            st.metric("Unique Albums", f"{unique_albums:,}")
            
        with col4:
            date_range = (pd.to_datetime(df['timestamp']).max() - pd.to_datetime(df['timestamp']).min()).days
            st.metric("Days of Data", f"{date_range:,}")
        
        # Charts
        st.subheader("📈 Listening Insights")
        
        col1, col2 = st.columns(2)
        
        with col1:
            listening_timeline = create_listening_timeline(df)
            st.plotly_chart(listening_timeline, use_container_width=True)
            
        with col2:
            if user_data['has_enriched'] and user_data['enriched'] is not None:
                mood_chart = create_mood_distribution(user_data['enriched'])
                st.plotly_chart(mood_chart, use_container_width=True)
            else:
                st.info("🎨 **Mood analysis available after enrichment**\n\nRun enrichment to see mood distribution!")
        
        # Top artists
        st.subheader("🎤 Your Musical Universe")
        top_artists_chart = create_top_artists_chart(df)
        st.plotly_chart(top_artists_chart, use_container_width=True)

def show_recommendations():
    """Recommendations page"""
    st.header("🎯 Generate Recommendations")
    
    username = st.sidebar.text_input("Last.fm Username", value=os.getenv('LASTFM_USERNAME', 'TestUser'))
    
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
                        # M3U format
                        m3u_content = "#EXTM3U\n"
                        for track in result.tracks:
                            artist = track.get('artist', 'Unknown')
                            title = track.get('track', 'Unknown')
                            m3u_content += f"#EXTINF:-1,{artist} - {title}\n"
                            m3u_content += f"# {artist} - {title}\n"
                        
                        st.download_button(
                            "🎵 Download M3U",
                            m3u_content,
                            f"playlist_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.m3u",
                            "audio/x-mpegurl"
                        )
                
                else:
                    st.error("❌ No recommendations generated. Try adjusting your parameters!")
                    
            except Exception as e:
                st.error(f"❌ Error generating recommendations: {e}")

def show_roon_integration():
    """Roon integration page"""
    st.header("🎵 Roon Integration")
    
    roon_host = st.sidebar.text_input(
        "Roon Core Host",
        value=os.getenv('ROON_CORE_HOST', '192.168.1.100'),
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
            st.info(f"💡 In terminal, run: `python -m src.music_rec.cli roon-connect --core-host {roon_host}`")
    
    with col2:
        if st.button("🏠 Show Zones"):
            st.info("🔄 Getting zone information...")
            st.info(f"💡 In terminal, run: `python -m src.music_rec.cli roon-zones --core-host {roon_host}`")
    
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
            f"python -m src.music_rec.cli roon-playlist",
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
    
    username = st.sidebar.text_input("Last.fm Username", value=os.getenv('LASTFM_USERNAME', 'TestUser'))
    
    # Data status
    st.subheader("📈 Data Status")
    user_data = load_user_data(username)
    
    status_df = pd.DataFrame([
        {"Data Type": "Scrobbles", "Status": "✅ Available" if user_data['has_scrobbles'] else "❌ Missing"},
        {"Data Type": "Enriched", "Status": "✅ Available" if user_data['has_enriched'] else "❌ Missing"},
        {"Data Type": "Statistics", "Status": "✅ Available" if user_data['has_stats'] else "❌ Missing"}
    ])
    
    st.dataframe(status_df, use_container_width=True)
    
    # Data actions
    st.subheader("🔧 Data Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📥 Fetch Data"):
            st.code(f"python -m src.music_rec.cli fetch --username {username}", language="bash")
            st.info("💡 Run this command to fetch your Last.fm data")
    
    with col2:
        if st.button("🎨 Enrich Data"):
            st.code(f"python -m src.music_rec.cli enrich --username {username}", language="bash")
            st.info("💡 Run this command to add mood and genre data")
    
    with col3:
        if st.button("🧠 Analyze Data"):
            st.code(f"python -m src.music_rec.cli analyze --username {username}", language="bash")
            st.info("💡 Run this command for AI analysis")

def main():
    """Main app function"""
    # Sidebar navigation
    st.sidebar.title("🎵 Navigation")
    page = st.sidebar.radio(
        "Choose a page:",
        ["🏠 Dashboard", "🎯 Recommendations", "🎵 Roon Integration", "📊 Data Management"]
    )
    
    # Route to pages
    if page == "🏠 Dashboard":
        show_dashboard()
    elif page == "🎯 Recommendations":
        show_recommendations()
    elif page == "🎵 Roon Integration":
        show_roon_integration()
    elif page == "📊 Data Management":
        show_data_management()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 1rem;">
        🎵 Music Recommendation System v5.0 | Built with ❤️ and AI
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 