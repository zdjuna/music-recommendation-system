#!/usr/bin/env python3
"""
🎵 Music Recommendation System - Web App Demo

This script demonstrates the beautiful web interface capabilities
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Demo the Streamlit web app"""
    print("🎵 Music Recommendation System Web Interface Demo")
    print("=" * 50)
    
    print("\n✨ NEW FEATURES:")
    print("📊 Interactive Dashboard with visualizations")
    print("🎯 Drag-and-drop playlist generation")
    print("🎵 Roon integration controls")
    print("📱 Mobile-responsive design")
    print("💾 Multiple export formats (CSV, JSON, M3U)")
    
    print("\n🌐 HOSTING OPTIONS:")
    print("🆓 Streamlit Cloud (FREE!)")
    print("💻 Railway, Render, Google Cloud Run")
    print("🏠 Home server / Raspberry Pi")
    print("📱 Works on all devices")
    
    print("\n🚀 TO LAUNCH THE WEB APP:")
    print("1. Ensure you're in the project directory")
    print("2. Run: python launch_web_app.py")
    print("3. Your browser will open automatically!")
    print("4. Access at: http://localhost:8501")
    
    print("\n🎯 WEB FEATURES:")
    print("• Beautiful gradient UI with modern design")
    print("• Interactive charts showing your listening patterns")
    print("• Real-time playlist generation with AI insights")
    print("• Zone-specific Roon integration")
    print("• Data management dashboard")
    print("• Export playlists in multiple formats")
    
    choice = input("\n🌟 Launch web app now? (y/n): ").lower().strip()
    
    if choice in ['y', 'yes']:
        print("\n🎵 Starting beautiful web interface...")
        app_path = Path(__file__).parent / "streamlit_app.py"
        
        # Set environment variable for better experience
        env = os.environ.copy()
        env['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
        
        try:
            subprocess.run([
                sys.executable, "-m", "streamlit", "run", str(app_path),
                "--server.headless", "false",
                "--server.port", "8501",
                "--browser.gatherUsageStats", "false"
            ], env=env)
        except KeyboardInterrupt:
            print("\n🛑 Web app stopped")
        except Exception as e:
            print(f"❌ Error: {e}")
    else:
        print("\n💡 To launch later, run: python launch_web_app.py")
        print("🌐 Or deploy to Streamlit Cloud for online access!")

if __name__ == "__main__":
    main() 