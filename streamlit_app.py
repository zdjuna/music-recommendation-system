"""
🎵 Music Recommendation System - Modular Streamlit App
"""

import streamlit as st
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

# Import modular components
from streamlit_app.utils.config import config
from streamlit_app.pages.dashboard import show_dashboard
from streamlit_app.pages.playlist_manager import show_playlist_manager
from streamlit_app.pages.temporal_analytics import show_temporal_analytics

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
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }
    
    /* Mobile responsive */
    @media (max-width: 768px) {
        .main-header {
            padding: 1rem;
        }
        .main-header h1 {
            font-size: 1.5rem;
        }
        
        .stColumns > div {
            margin-bottom: 1rem;
        }
        
        .metric-card {
            padding: 0.5rem;
            margin-bottom: 0.5rem;
        }
        
        .stButton > button {
            width: 100%;
            margin-bottom: 0.5rem;
        }
        
        .sidebar .sidebar-content {
            font-size: 0.9rem;
        }
    }
    
    @media (max-width: 480px) {
        .main-header h1 {
            font-size: 1.2rem;
        }
        
        .main-header p {
            font-size: 0.9rem;
        }
        
        [data-testid="stSidebar"] {
            width: 100% !important;
        }
        
        .stDataFrame {
            font-size: 0.8rem;
        }
        
        .plotly-graph-div {
            height: 300px !important;
        }
    }
    
    /* Touch-friendly interface */
    .stButton > button {
        min-height: 44px;
        touch-action: manipulation;
    }
    
    .stSelectbox > div {
        min-height: 44px;
    }
    
    .stTextInput > div > div > input {
        min-height: 44px;
    }
    
    /* Improved loading states */
    .stSpinner {
        text-align: center;
        padding: 2rem;
    }
    
    /* Better error messages */
    .stAlert {
        border-radius: 8px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Main application function"""
    
    # Sidebar navigation
    st.sidebar.title("🎵 Navigation")
    
    # System status in sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("**🔧 System Status**")
    
    api_status = config.api_status
    status_indicators = []
    
    if api_status['lastfm']:
        status_indicators.append("✅ LastFM")
    else:
        status_indicators.append("❌ LastFM")
    
    if api_status['cyanite']:
        status_indicators.append("✅ Cyanite")
    else:
        status_indicators.append("⚠️ Cyanite")
    
    if api_status['spotify']:
        status_indicators.append("✅ Spotify")
    else:
        status_indicators.append("⚠️ Spotify")
    
    for indicator in status_indicators:
        st.sidebar.markdown(f"- {indicator}")
    
    # Production readiness indicator
    if config.is_production_ready:
        st.sidebar.success("🚀 Production Ready")
    else:
        st.sidebar.warning("⚠️ Setup Needed")
    
    # Navigation menu
    st.sidebar.markdown("---")
    
    # Navigation options
    nav_options = [
        "🏠 Dashboard",
        "🎵 Playlists", 
        "📈 Temporal Analytics",
        "🎯 Recommendations",
        "📊 Data Management",
        "⚡ Real-Time Monitoring",
        "🎼 Roon Integration"
    ]
    
    page = st.sidebar.radio("Choose a page:", nav_options)
    
    # User selection
    st.sidebar.markdown("---")
    st.sidebar.markdown("**👤 User Settings**")
    username = st.sidebar.text_input("Username", value=config.default_username)
    
    # Quick stats in sidebar
    try:
        from streamlit_app.models.database import db
        stats = db.get_user_stats(username)
        if stats['total_scrobbles'] > 0:
            st.sidebar.markdown(f"📊 **{stats['total_scrobbles']:,}** scrobbles")
            st.sidebar.markdown(f"🎤 **{stats['unique_artists']:,}** artists")
            st.sidebar.markdown(f"🎵 **{stats['playlists_count']:,}** playlists")
    except Exception:
        pass
    
    # Route to appropriate page
    if page == "🏠 Dashboard":
        show_dashboard()
    elif page == "🎵 Playlists":
        show_playlist_manager()
    elif page == "📈 Temporal Analytics":
        show_temporal_analytics()
    elif page == "🎯 Recommendations":
        show_enhanced_recommendations()
    elif page == "📊 Data Management":
        show_data_management()
    elif page == "⚡ Real-Time Monitoring":
        show_realtime_monitoring()
    elif page == "🎼 Roon Integration":
        show_roon_integration()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 1rem;">
        🎵 Music Recommendation System v6.0 | Built with ❤️ and AI
        <br><small>Modular Architecture • High Performance • Production Ready</small>
    </div>
    """, unsafe_allow_html=True)

def show_enhanced_recommendations():
    """Enhanced recommendations page (placeholder)"""
    st.header("🎯 Enhanced Music Recommendations")
    st.info("🚧 This page is being migrated to the new modular architecture. Coming soon!")
    
    # Quick recommendation buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🎵 Quick Mix"):
            st.success("Generating quick mix...")
    with col2:
        if st.button("🔍 Discovery"):
            st.success("Generating discovery playlist...")
    with col3:
        if st.button("❤️ Favorites"):
            st.success("Generating favorites mix...")

def show_data_management():
    """Data management page (placeholder)"""
    st.header("📊 Data Management")
    st.info("🚧 This page is being migrated to the new modular architecture. Coming soon!")
    
    # Quick actions
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📥 Import CSV Data"):
            try:
                from streamlit_app.models.database import db
                username = config.default_username
                csv_file = config.data_dir / f"{username}_scrobbles.csv"
                if csv_file.exists():
                    db.import_csv_data(username, csv_file)
                    st.success("Data imported successfully!")
                else:
                    st.error("No scrobbles data found")
            except Exception as e:
                st.error(f"Import failed: {e}")
    
    with col2:
        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()
            st.success("Cache cleared!")

def show_realtime_monitoring():
    """Real-time monitoring page (placeholder)"""
    st.header("⚡ Real-Time Monitoring")
    st.info("🚧 This page is being migrated to the new modular architecture. Coming soon!")

def show_roon_integration():
    """Roon integration page (placeholder)"""
    st.header("🎼 Roon Integration")
    st.info("🚧 This page is being migrated to the new modular architecture. Coming soon!")

if __name__ == "__main__":
    main()
