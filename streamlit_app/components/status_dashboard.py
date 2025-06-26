"""
System status dashboard component
"""

import streamlit as st
from pathlib import Path
from ..utils.config import config
from ..models.database import db

def render_system_status():
    """Render comprehensive system status dashboard"""
    st.subheader("🔧 System Status")
    
    # API Configuration Status
    status_col1, status_col2, status_col3 = st.columns(3)
    
    with status_col1:
        st.markdown("**🔑 API Configuration**")
        api_status = config.api_status
        
        if api_status['lastfm']:
            st.success("✅ Last.fm API Key")
        else:
            st.error("❌ Last.fm API Key Missing")
        
        if api_status['cyanite']:
            st.success("✅ Cyanite API Key")
        else:
            st.warning("⚠️ Cyanite API Key Missing")
            
        if api_status['spotify']:
            st.success("✅ Spotify API Keys")
        else:
            st.warning("⚠️ Spotify API Keys Missing")
    
    with status_col2:
        st.markdown("**💾 Database Status**")
        try:
            stats = db.get_user_stats(config.default_username)
            st.success("✅ Database Connected")
            st.info(f"📊 {stats['total_scrobbles']:,} scrobbles")
            st.info(f"🎤 {stats['unique_artists']:,} artists")
            st.info(f"🎵 {stats['unique_tracks']:,} tracks")
        except Exception as e:
            st.error(f"❌ Database Error: {e}")
    
    with status_col3:
        st.markdown("**📁 Data Files**")
        data_dir = config.data_dir
        if data_dir.exists():
            st.success("✅ Data Directory")
            csv_files = list(data_dir.glob("*.csv"))
            json_files = list(data_dir.glob("*.json"))
            st.info(f"📄 {len(csv_files)} CSV files")
            st.info(f"📋 {len(json_files)} JSON files")
        else:
            st.error("❌ No Data Directory")
    
    # Overall System Health
    st.markdown("---")
    if config.is_production_ready:
        st.success("🚀 **System Ready for Production Use**")
    else:
        st.warning("⚠️ **System Needs Configuration**")
        
        missing_items = []
        if not api_status['lastfm']:
            missing_items.append("Last.fm API key")
        if not (config.data_dir / f"{config.default_username}_scrobbles.csv").exists():
            missing_items.append("User music data")
        
        if missing_items:
            st.info(f"**Missing:** {', '.join(missing_items)}")

def render_quick_actions():
    """Render quick action buttons for testing and setup"""
    st.markdown("### ⚡ Quick Actions")
    action_col1, action_col2, action_col3 = st.columns(3)
    
    with action_col1:
        if st.button("🎵 Test Spotify", key="test_spotify_main"):
            with st.spinner("Testing Spotify connection..."):
                try:
                    import subprocess
                    result = subprocess.run(['python', 'tests/integration/test_spotify.py'], 
                                          capture_output=True, text=True, timeout=30)
                    if "✅" in result.stdout:
                        st.success("Spotify connection working!")
                    else:
                        st.warning("Spotify connection issues detected")
                        with st.expander("Debug Info"):
                            st.code(result.stdout)
                except Exception as e:
                    st.error(f"Test failed: {e}")
    
    with action_col2:
        if st.button("🧪 Test LastFM", key="test_lastfm_main"):
            with st.spinner("Testing LastFM integration..."):
                try:
                    import subprocess
                    result = subprocess.run(['python', 'tests/integration/test_lastfm.py'], 
                                          capture_output=True, text=True, timeout=30)
                    if "✨" in result.stdout:
                        st.success("LastFM integration working!")
                    else:
                        st.warning("LastFM integration issues detected")
                        with st.expander("Debug Info"):
                            st.code(result.stdout)
                except Exception as e:
                    st.error(f"Test failed: {e}")
    
    with action_col3:
        if st.button("💾 Import Data", key="import_data_main"):
            with st.spinner("Importing CSV data to database..."):
                try:
                    # Import existing CSV data to database
                    username = config.default_username
                    csv_file = config.data_dir / f"{username}_scrobbles.csv"
                    if csv_file.exists():
                        db.import_csv_data(username, csv_file)
                        st.success("Data imported successfully!")
                        st.experimental_rerun()
                    else:
                        st.error("No scrobbles data found to import")
                except Exception as e:
                    st.error(f"Import failed: {e}")

def render_welcome_message():
    """Render welcome message for new users"""
    st.markdown("### 🚀 Welcome to Your Music Recommendation System!")
    st.info("""
    **Getting Started:**
    
    1. **Configure APIs:** Make sure you have API keys in your `.env` file:
       - `LASTFM_API_KEY` for music data (required)
       - `CYANITE_API_KEY` for mood analysis (optional)
       - `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` for Spotify features (optional)
    
    2. **Import Data:** Use the "Import Data" button above or go to "📊 Data Management"
    
    3. **Explore:** Once data is loaded, enjoy your personalized music insights!
    """)
    
    # Helpful links
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔧 Go to Data Management", key="goto_data_mgmt_welcome"):
            st.experimental_set_query_params(page="data")
    with col2:
        st.markdown("[📖 Setup Guide](docs/QUICK_START.md)")