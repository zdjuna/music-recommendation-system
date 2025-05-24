#!/usr/bin/env python3
"""
🎵 Music Recommendation System - Web App Launcher

Launch the beautiful Streamlit web interface for the Music Recommendation System
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Launch the Streamlit web app"""
    app_path = Path(__file__).parent / "streamlit_app.py"
    
    print("🎵 Starting Music Recommendation System Web Interface...")
    print("🌐 Web app will open in your browser automatically!")
    print("🚀 Ready to explore your music universe!\n")
    
    # Set environment variable for better Streamlit experience
    env = os.environ.copy()
    env['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", str(app_path),
            "--server.headless", "false",
            "--server.port", "8501",
            "--browser.gatherUsageStats", "false",
            "--theme.base", "light"
        ], env=env)
    except KeyboardInterrupt:
        print("\n🛑 Web app stopped by user")
    except Exception as e:
        print(f"❌ Error starting web app: {e}")
        print("\n💡 Make sure you have Streamlit installed:")
        print("   pip install streamlit")

if __name__ == "__main__":
    main()
