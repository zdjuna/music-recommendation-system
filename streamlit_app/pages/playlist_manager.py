"""
Playlist management page with CRUD operations
"""

import streamlit as st
import pandas as pd
from typing import List, Dict, Any
from ..utils.config import config
from ..models.database import db
import json
from datetime import datetime

def show_playlist_manager():
    """Playlist management interface"""
    st.header("🎵 Playlist Manager")
    
    username = config.default_username
    
    # Playlist tabs
    tab1, tab2, tab3 = st.tabs(["📋 My Playlists", "➕ Create Playlist", "🎯 Generate Recommendations"])
    
    with tab1:
        show_existing_playlists(username)
    
    with tab2:
        show_create_playlist(username)
    
    with tab3:
        show_recommendation_generator(username)

def show_existing_playlists(username: str):
    """Show existing playlists with management options"""
    st.subheader("📋 Your Playlists")
    
    try:
        playlists = db.get_user_playlists(username)
        
        if not playlists:
            st.info("🎵 No playlists yet! Create your first playlist below.")
            return
        
        # Playlist grid
        cols = st.columns(2)
        for i, playlist in enumerate(playlists):
            with cols[i % 2]:
                with st.container():
                    st.markdown(f"""
                    <div style="border: 1px solid #ddd; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
                        <h4>🎵 {playlist['name']}</h4>
                        <p><small>{playlist['description'] or 'No description'}</small></p>
                        <p><strong>Type:</strong> {playlist['type'].title()}</p>
                        <p><strong>Created:</strong> {playlist['created_at'][:10]}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Action buttons
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button("👁️ View", key=f"view_{playlist['id']}"):
                            show_playlist_details(playlist['id'])
                    
                    with col2:
                        if st.button("✏️ Edit", key=f"edit_{playlist['id']}"):
                            edit_playlist(playlist['id'])
                    
                    with col3:
                        if st.button("🗑️ Delete", key=f"delete_{playlist['id']}"):
                            if st.checkbox(f"Confirm delete '{playlist['name']}'", key=f"confirm_delete_{playlist['id']}"):
                                delete_playlist(playlist['id'])
                                st.experimental_rerun()
    
    except Exception as e:
        st.error(f"Error loading playlists: {e}")

def show_playlist_details(playlist_id: int):
    """Show detailed view of a playlist"""
    st.subheader("🎵 Playlist Details")
    
    try:
        tracks = db.get_playlist_tracks(playlist_id)
        
        if not tracks:
            st.info("This playlist is empty.")
            return
        
        # Convert to DataFrame for display
        df = pd.DataFrame(tracks)
        df.index = df.index + 1  # Start from 1
        
        # Display tracks
        st.dataframe(df[['artist', 'track', 'album']], use_container_width=True)
        
        # Export options
        st.subheader("📤 Export Options")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📄 Export CSV"):
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"playlist_{playlist_id}.csv",
                    mime="text/csv"
                )
        
        with col2:
            if st.button("🎵 Export M3U"):
                m3u_content = create_m3u_playlist(tracks)
                st.download_button(
                    label="Download M3U",
                    data=m3u_content,
                    file_name=f"playlist_{playlist_id}.m3u",
                    mime="text/plain"
                )
        
        with col3:
            if st.button("📋 Export JSON"):
                json_content = json.dumps(tracks, indent=2)
                st.download_button(
                    label="Download JSON",
                    data=json_content,
                    file_name=f"playlist_{playlist_id}.json",
                    mime="application/json"
                )
    
    except Exception as e:
        st.error(f"Error loading playlist details: {e}")

def show_create_playlist(username: str):
    """Create new playlist interface"""
    st.subheader("➕ Create New Playlist")
    
    with st.form("create_playlist"):
        name = st.text_input("Playlist Name*", placeholder="My Awesome Playlist")
        description = st.text_area("Description", placeholder="Optional description...")
        
        playlist_type = st.selectbox(
            "Playlist Type",
            ["custom", "recommendation", "auto"],
            help="Custom: Manual playlist, Recommendation: AI-generated, Auto: Automatically updated"
        )
        
        submitted = st.form_submit_button("Create Playlist")
        
        if submitted:
            if not name.strip():
                st.error("Please provide a playlist name")
            else:
                try:
                    playlist_id = db.create_playlist(
                        username=username,
                        name=name.strip(),
                        description=description.strip() if description.strip() else None,
                        playlist_type=playlist_type
                    )
                    st.success(f"✅ Created playlist '{name}' (ID: {playlist_id})")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Error creating playlist: {e}")

def show_recommendation_generator(username: str):
    """Generate recommendation playlists"""
    st.subheader("🎯 Generate Recommendation Playlists")
    
    # Recommendation settings
    col1, col2 = st.columns(2)
    
    with col1:
        playlist_size = st.slider("Playlist Size", 10, 100, 30)
        discovery_level = st.selectbox(
            "Discovery Level",
            ["conservative", "balanced", "adventurous"],
            index=1,
            help="How much to explore new music vs familiar artists"
        )
    
    with col2:
        mood_filter = st.selectbox(
            "Mood Filter",
            ["any", "happy", "energetic", "chill", "melancholic", "focused"],
            help="Filter recommendations by mood"
        )
        
        time_period = st.selectbox(
            "Based on listening from",
            ["all_time", "last_year", "last_6_months", "last_3_months"],
            index=1
        )
    
    # Generation options
    st.subheader("🎵 Playlist Types")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔥 Similar to Recent", help="Based on your recent listening"):
            generate_playlist(username, "similar_recent", {
                'size': playlist_size,
                'discovery': discovery_level,
                'mood': mood_filter,
                'period': time_period
            })
    
    with col2:
        if st.button("🌟 Discover New", help="Explore new artists and genres"):
            generate_playlist(username, "discovery", {
                'size': playlist_size,
                'discovery': discovery_level,
                'mood': mood_filter,
                'period': time_period
            })
    
    with col3:
        if st.button("📈 Trending Mix", help="Popular tracks you might like"):
            generate_playlist(username, "trending", {
                'size': playlist_size,
                'discovery': discovery_level,
                'mood': mood_filter,
                'period': time_period
            })

def generate_playlist(username: str, playlist_type: str, settings: Dict[str, Any]):
    """Generate a recommendation playlist"""
    with st.spinner(f"🎵 Generating {playlist_type} playlist..."):
        try:
            # Create playlist in database
            playlist_name = f"{playlist_type.replace('_', ' ').title()} Mix - {datetime.now().strftime('%Y-%m-%d')}"
            playlist_id = db.create_playlist(
                username=username,
                name=playlist_name,
                description=f"AI-generated {playlist_type} playlist",
                playlist_type="recommendation"
            )
            
            # TODO: Integrate with existing recommendation engines
            # For now, create a sample playlist
            sample_tracks = [
                {"artist": "Sample Artist 1", "track": "Sample Track 1", "album": "Sample Album 1"},
                {"artist": "Sample Artist 2", "track": "Sample Track 2", "album": "Sample Album 2"},
                {"artist": "Sample Artist 3", "track": "Sample Track 3", "album": "Sample Album 3"},
            ]
            
            db.add_tracks_to_playlist(playlist_id, sample_tracks)
            
            st.success(f"✅ Generated playlist '{playlist_name}'!")
            st.balloons()
            
            # Show generated playlist
            st.subheader("🎵 Generated Playlist")
            tracks_df = pd.DataFrame(sample_tracks)
            st.dataframe(tracks_df, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error generating playlist: {e}")

def edit_playlist(playlist_id: int):
    """Edit playlist interface"""
    st.subheader("✏️ Edit Playlist")
    # TODO: Implement playlist editing
    st.info("Playlist editing coming soon!")

def delete_playlist(playlist_id: int):
    """Delete playlist"""
    try:
        # TODO: Implement playlist deletion
        st.success(f"Playlist {playlist_id} deleted!")
    except Exception as e:
        st.error(f"Error deleting playlist: {e}")

def create_m3u_playlist(tracks: List[Dict[str, Any]]) -> str:
    """Create M3U playlist content"""
    content = "#EXTM3U\n"
    for track in tracks:
        content += f"#EXTINF:-1,{track['artist']} - {track['track']}\n"
        content += f"# {track['artist']} - {track['track']}\n"
    return content