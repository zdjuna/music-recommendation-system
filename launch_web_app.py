#!/usr/bin/env python3
"""
🎵 Music Recommendation System - Web App Launcher
Launch the beautiful Streamlit web interface with one command
"""

import subprocess
import sys
import webbrowser
import time
from pathlib import Path

def main():
    """Launch the Streamlit web application"""
    
    print("🎵 Music Recommendation System v5.2")
    print("=" * 50)
    print("🚀 Launching web interface...")
    print()
    
    # Check if streamlit_app.py exists
    app_file = Path("streamlit_app.py")
    if not app_file.exists():
        print("❌ Error: streamlit_app.py not found in current directory")
        print("💡 Make sure you're running this from the project root")
        return 1
    
    # Launch Streamlit
    try:
        print("🌐 Starting Streamlit server...")
        print("💡 The web interface will open automatically at http://localhost:8501")
        print()
        print("⚡ Features available:")
        print("   • 📊 Interactive dashboard with 437k+ scrobbles")
        print("   • 🎯 AI-powered recommendation engine") 
        print("   • 🎵 Roon integration for high-end audio")
        print("   • 🎭 Professional mood analysis with Cyanite.ai")
        print("   • 📱 Mobile-responsive design")
        print()
        print("🔧 Press Ctrl+C to stop the server")
        print("-" * 50)
        
        # Launch Streamlit with auto-open browser
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
            "--server.port", "8501",
            "--server.address", "localhost",
            "--browser.gatherUsageStats", "false"
        ])
        
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
        return 0
    except FileNotFoundError:
        print("❌ Error: Streamlit not installed")
        print("💡 Install with: pip install streamlit>=1.45.1")
        return 1
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())