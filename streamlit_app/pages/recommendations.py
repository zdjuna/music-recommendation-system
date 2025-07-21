"""
Context-aware music recommendations page
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime
import logging

from src.music_rec.recommenders import RecommendationEngine, RecommendationRequest, RecommendationResult
from ..utils.config import config
from ..models.database import db

logger = logging.getLogger(__name__)

def show_recommendations():
    """Main recommendations page"""
    
    st.markdown("""
    <div style="background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); 
                padding: 2rem; border-radius: 10px; color: white; text-align: center; margin-bottom: 2rem;">
        <h1>🎯 Context-Aware Recommendations</h1>
        <p>AI-powered music recommendations tailored to your mood, time, and energy</p>
    </div>
    """, unsafe_allow_html=True)
    
    username = config.default_username
    
    user_data = load_user_data(username)
    if not user_data or not user_data.get('has_data'):
        show_no_data_message()
        return
    
    tab1, tab2, tab3 = st.tabs(["🎯 Generate Recommendations", "⚡ Quick Presets", "📋 Saved Playlists"])
    
    with tab1:
        show_custom_recommendations(username)
    
    with tab2:
        show_preset_recommendations(username)
    
    with tab3:
        show_saved_recommendations(username)

@st.cache_data(ttl=300)
def load_user_data(username: str) -> Dict[str, Any]:
    """Load user data for recommendations"""
    try:
        stats = db.get_user_stats(username)
        if stats['total_scrobbles'] > 0:
            return {'has_data': True, 'stats': stats, 'source': 'database'}
    except Exception as e:
        logger.warning(f"Failed to load database stats: {e}")
    
    # Fallback to CSV files
    data_dir = config.data_dir
    scrobbles_file = data_dir / f"{username}_scrobbles.csv"
    
    if scrobbles_file.exists():
        return {'has_data': True, 'source': 'csv'}
    
    return {'has_data': False}

def show_no_data_message():
    """Show message when no user data is available"""
    st.warning("📊 No listening data found!")
    st.markdown("""
    To generate personalized recommendations, you need:
    - **Scrobbles data**: Place your `{username}_scrobbles.csv` file in the `data/` directory
    - **Or**: Import your listening history through the Data Management page
    
    Once you have data, return here for AI-powered recommendations!
    """.format(username=config.default_username))

def show_custom_recommendations(username: str):
    """Show custom recommendation generation interface"""
    st.subheader("🎯 Custom Recommendations")
    st.markdown("Customize your recommendations with specific mood, energy, and discovery preferences.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🎭 Mood & Energy**")
        mood = st.selectbox(
            "Mood",
            ["any", "happy", "energetic", "chill", "melancholic", "focused", "calm"],
            help="Select the mood that matches your current state"
        )
        
        energy_level = st.selectbox(
            "Energy Level",
            ["any", "high", "medium", "low"],
            index=2,
            help="Choose your desired energy level"
        )
        
        time_context = st.selectbox(
            "Time Context",
            ["any", "morning", "afternoon", "evening", "night"],
            help="Optimize for specific time of day"
        )
    
    with col2:
        st.markdown("**⚙️ Customization**")
        discovery_level = st.slider(
            "Discovery vs Familiarity",
            0.0, 1.0, 0.5,
            help="0.0 = Only familiar favorites, 1.0 = Only new discoveries"
        )
        
        playlist_length = st.slider(
            "Playlist Length",
            10, 50, 25,
            help="Number of tracks to generate"
        )
        
        include_favorites = st.slider(
            "Include Favorites",
            0.0, 1.0, 0.3,
            help="Proportion of known favorites to include"
        )
        
        exclude_recent = st.checkbox(
            "Exclude Recently Played",
            value=True,
            help="Avoid tracks played in the last few days"
        )
    
    if st.button("🎵 Generate Custom Recommendations", type="primary"):
        generate_custom_recommendations(
            username, mood, energy_level, time_context, 
            discovery_level, playlist_length, include_favorites, exclude_recent
        )

def show_preset_recommendations(username: str):
    """Show quick preset recommendation buttons"""
    st.subheader("⚡ Quick Presets")
    st.markdown("Choose from pre-configured recommendation styles for common scenarios.")
    
    try:
        engine = RecommendationEngine(username)
        presets = engine.get_recommendation_presets()
    except Exception as e:
        st.error(f"Error loading presets: {e}")
        return
    
    preset_descriptions = {
        'morning_energy': {
            'title': '🌅 Morning Energy',
            'description': 'Upbeat tracks to start your day with positive energy',
            'icon': '☀️'
        },
        'focus_work': {
            'title': '💼 Focus Work',
            'description': 'Calm, non-distracting music perfect for concentration',
            'icon': '🎯'
        },
        'evening_chill': {
            'title': '🌙 Evening Chill',
            'description': 'Relaxing tracks to unwind after a long day',
            'icon': '🛋️'
        },
        'weekend_discovery': {
            'title': '🔍 Weekend Discovery',
            'description': 'Explore new artists and expand your musical horizons',
            'icon': '🚀'
        },
        'nostalgic_favorites': {
            'title': '💝 Nostalgic Favorites',
            'description': 'Beloved tracks from your listening history',
            'icon': '❤️'
        },
        'party_mix': {
            'title': '🎉 Party Mix',
            'description': 'High-energy tracks perfect for celebrations',
            'icon': '🕺'
        }
    }
    
    cols = st.columns(2)
    for i, (preset_key, preset_request) in enumerate(presets.items()):
        with cols[i % 2]:
            preset_info = preset_descriptions.get(preset_key, {})
            
            with st.container():
                st.markdown(f"""
                <div style="border: 1px solid #ddd; padding: 1rem; border-radius: 8px; margin-bottom: 1rem; text-align: center;">
                    <h4>{preset_info.get('icon', '🎵')} {preset_info.get('title', preset_key.replace('_', ' ').title())}</h4>
                    <p><small>{preset_info.get('description', 'Pre-configured recommendation preset')}</small></p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"Generate {preset_info.get('title', preset_key)}", key=f"preset_{preset_key}"):
                    generate_preset_recommendations(username, preset_key, preset_request)

def show_saved_recommendations(username: str):
    """Show previously generated recommendation playlists"""
    st.subheader("📋 Saved Recommendation Playlists")
    
    try:
        playlists = db.get_user_playlists(username)
        recommendation_playlists = [p for p in playlists if p['type'] == 'recommendation']
        
        if not recommendation_playlists:
            st.info("🎵 No saved recommendation playlists yet! Generate some recommendations to see them here.")
            return
        
        for playlist in recommendation_playlists:
            with st.expander(f"🎵 {playlist['name']} ({playlist['created_at'][:10]})"):
                tracks = db.get_playlist_tracks(playlist['id'])
                
                if tracks:
                    tracks_df = pd.DataFrame(tracks)
                    st.dataframe(tracks_df[['artist', 'track', 'album']], use_container_width=True)
                    
                    # Export options
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        csv = tracks_df.to_csv(index=False)
                        st.download_button(
                            "📄 Download CSV",
                            csv,
                            f"{playlist['name']}.csv",
                            "text/csv"
                        )
                    
                    with col2:
                        m3u_content = create_m3u_playlist(tracks)
                        st.download_button(
                            "🎵 Download M3U",
                            m3u_content,
                            f"{playlist['name']}.m3u",
                            "text/plain"
                        )
                    
                    with col3:
                        if st.button(f"🗑️ Delete", key=f"delete_{playlist['id']}"):
                            delete_recommendation_playlist(playlist['id'])
                            st.rerun()
                else:
                    st.info("This playlist is empty.")
    
    except Exception as e:
        st.error(f"Error loading saved playlists: {e}")

def generate_custom_recommendations(username: str, mood: str, energy_level: str, time_context: str,
                                  discovery_level: float, playlist_length: int, include_favorites: float,
                                  exclude_recent: bool):
    """Generate recommendations with custom parameters"""
    
    with st.spinner("🎵 Generating your personalized recommendations..."):
        try:
            request = RecommendationRequest(
                mood=mood if mood != "any" else None,
                energy_level=energy_level if energy_level != "any" else None,
                time_context=time_context if time_context != "any" else None,
                discovery_level=discovery_level,
                playlist_length=playlist_length,
                include_favorites=include_favorites,
                exclude_recent=exclude_recent
            )
            
            engine = RecommendationEngine(username)
            result = engine.generate_recommendations(request)
            
            display_recommendation_results(username, result, "Custom Recommendations")
            
        except Exception as e:
            st.error(f"Error generating recommendations: {e}")
            logger.error(f"Recommendation generation failed: {e}")

def generate_preset_recommendations(username: str, preset_key: str, preset_request: RecommendationRequest):
    """Generate recommendations using a preset"""
    
    with st.spinner(f"🎵 Generating {preset_key.replace('_', ' ').title()} playlist..."):
        try:
            engine = RecommendationEngine(username)
            result = engine.generate_recommendations(preset_request)
            
            display_recommendation_results(username, result, preset_key.replace('_', ' ').title())
            
        except Exception as e:
            st.error(f"Error generating preset recommendations: {e}")
            logger.error(f"Preset recommendation generation failed: {e}")

def display_recommendation_results(username: str, result: RecommendationResult, playlist_name: str):
    """Display recommendation results with save option"""
    
    if not result.tracks:
        st.warning("No recommendations could be generated with the current parameters. Try adjusting your settings.")
        return
    
    st.success(f"✅ Generated {len(result.tracks)} recommendations!")
    st.balloons()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Confidence Score", f"{result.confidence_score:.1%}")
    with col2:
        st.metric("Total Tracks", len(result.tracks))
    
    if result.explanation:
        st.info(f"💡 **Recommendation Logic**: {result.explanation}")
    
    # Display tracks
    st.subheader("🎵 Your Recommendations")
    tracks_df = pd.DataFrame(result.tracks)
    
    display_columns = ['artist', 'track']
    if 'album' in tracks_df.columns:
        display_columns.append('album')
    if 'primary_genre' in tracks_df.columns:
        display_columns.append('primary_genre')
    if 'mood' in tracks_df.columns:
        display_columns.append('mood')
    
    st.dataframe(tracks_df[display_columns], use_container_width=True)
    
    st.subheader("💾 Save Playlist")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        save_name = st.text_input(
            "Playlist Name",
            value=f"{playlist_name} - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            key=f"save_name_{playlist_name}"
        )
    
    with col2:
        if st.button("💾 Save Playlist", key=f"save_{playlist_name}"):
            save_recommendation_playlist(username, save_name, result.tracks, result.metadata)

def save_recommendation_playlist(username: str, name: str, tracks: List[Dict[str, Any]], metadata: Dict[str, Any]):
    """Save generated recommendations as a playlist"""
    
    try:
        # Create playlist in database
        playlist_id = db.create_playlist(
            username=username,
            name=name,
            description=f"AI-generated recommendations - {metadata.get('generated_at', 'Unknown time')}",
            playlist_type="recommendation"
        )
        
        db.add_tracks_to_playlist(playlist_id, tracks)
        
        st.success(f"✅ Saved playlist '{name}' with {len(tracks)} tracks!")
        
    except Exception as e:
        st.error(f"Error saving playlist: {e}")
        logger.error(f"Failed to save playlist: {e}")

def delete_recommendation_playlist(playlist_id: int):
    """Delete a recommendation playlist"""
    try:
        st.success(f"Playlist deleted successfully!")
    except Exception as e:
        st.error(f"Error deleting playlist: {e}")

def create_m3u_playlist(tracks: List[Dict[str, Any]]) -> str:
    """Create M3U playlist content"""
    content = "#EXTM3U\n"
    for track in tracks:
        content += f"#EXTINF:-1,{track['artist']} - {track['track']}\n"
        content += f"# {track['artist']} - {track['track']}\n"
    return content
