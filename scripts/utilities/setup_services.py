#!/usr/bin/env python3
"""
Spotify API Setup Helper
Guides you through getting Spotify API credentials for REAL music analysis
"""

import os
import json
import requests
from pathlib import Path
import webbrowser
from dotenv import load_dotenv, set_key

def setup_spotify():
    print("🎵 Spotify API Setup for Real Music Analysis")
    print("=" * 50)
    print("\nThis will help you get Spotify API credentials to analyze:")
    print("- Audio features (valence, energy, danceability)")
    print("- Tempo, key, mode (major/minor)")
    print("- Acousticness, instrumentalness")
    print("\n📝 Follow these steps:\n")
    
    # Step 1: Open Spotify Developer Dashboard
    print("1️⃣ Opening Spotify Developer Dashboard...")
    dashboard_url = "https://developer.spotify.com/dashboard"
    
    input(f"\nPress Enter to open: {dashboard_url}")
    webbrowser.open(dashboard_url)
    
    print("\n2️⃣ In the dashboard:")
    print("   - Log in with your Spotify account (free account works!)")
    print("   - Click 'Create app'")
    print("   - Fill in:")
    print("     • App name: 'Music Recommendation System'")
    print("     • App description: 'Personal music analysis'")
    print("     • Redirect URI: http://localhost:8888/callback")
    print("     • Select 'Web API' for APIs used")
    print("   - Agree to terms and click 'Save'")
    
    input("\n✅ Press Enter when you've created the app...")
    
    print("\n3️⃣ Getting your credentials:")
    print("   - Click on your new app")
    print("   - Click 'Settings'")
    print("   - You'll see your Client ID")
    print("   - Click 'View client secret' to see the secret")
    
    # Get credentials from user
    print("\n4️⃣ Enter your credentials:\n")
    client_id = input("Spotify Client ID: ").strip()
    client_secret = input("Spotify Client Secret: ").strip()
    
    # Test the credentials
    print("\n🔍 Testing credentials...")
    auth_url = 'https://accounts.spotify.com/api/token'
    auth_response = requests.post(auth_url, {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
    })
    
    if auth_response.status_code == 200:
        print("✅ Credentials are valid!")
        
        # Save to .env file
        env_path = Path('.env')
        
        # Create .env if it doesn't exist
        if not env_path.exists():
            env_path.touch()
        
        # Load existing environment variables
        load_dotenv()
        
        # Set the new keys
        set_key('.env', 'SPOTIFY_CLIENT_ID', client_id)
        set_key('.env', 'SPOTIFY_CLIENT_SECRET', client_secret)
        
        print("\n✅ Credentials saved to .env file!")
        print("\n🎵 You're ready to analyze real music features!")
        
        # Quick test
        print("\n🧪 Quick test - let's analyze a sample track...")
        print("   (This will verify everything is working)")
        
        # Import here to avoid circular imports
        from real_music_analyzer import RealMusicAnalyzer
        
        try:
            analyzer = RealMusicAnalyzer(client_id, client_secret)
            features = analyzer.get_spotify_track_features("Radiohead", "Creep")
            
            if features:
                print(f"\n📊 Analysis of 'Radiohead - Creep':")
                print(f"   Valence (happiness): {features.valence:.3f}")
                print(f"   Energy: {features.energy:.3f}")
                print(f"   Danceability: {features.danceability:.3f}")
                print(f"   Tempo: {features.tempo:.0f} BPM")
                print(f"   Key: {'Major' if features.mode == 1 else 'Minor'}")
                print("\n✨ Real music analysis is working perfectly!")
            else:
                print("\n⚠️  Couldn't analyze the test track, but credentials are valid.")
                print("   This might happen if the track isn't on Spotify.")
        except Exception as e:
            print(f"\n⚠️  Test analysis failed: {e}")
            print("   But your credentials are saved and valid!")
        
        print("\n🚀 Next step: Run 'python enrich_with_spotify.py' to analyze your library!")
        
    else:
        print("❌ Invalid credentials. Please check and try again.")
        print(f"Error: {auth_response.text}")
        return False
    
    return True

if __name__ == "__main__":
    setup_spotify()
