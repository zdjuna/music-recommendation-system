#!/usr/bin/env python3
"""
Fix Spotify authentication issues - 403 Forbidden on audio-features
"""

print("🔧 Spotify Authentication Fix")
print("="*50)
print("\nThe issue: Your Spotify app is returning 403 Forbidden for audio features.")
print("This usually means the app needs to be reconfigured.\n")

print("📋 Solution Steps:\n")

print("1. Go to: https://developer.spotify.com/dashboard")
print("2. Click on your app 'Music Recommendation System'")
print("3. Click 'Settings'")
print("4. Check the following:")
print("   - Make sure 'Web API' is selected under 'Which API/SDKs are you planning to use?'")
print("   - The Redirect URI should be: http://localhost:8888/callback")
print("\n5. If those are correct, try:")
print("   a) Delete the current app")
print("   b) Create a new app with the same settings")
print("   c) Get new Client ID and Secret")
print("\n6. Alternative: The issue might be temporary rate limiting.")
print("   Wait a few minutes and try again.\n")

print("🔍 Quick Test:")
print("Once you've updated the app or created a new one, run:")
print("   python setup_spotify.py")
print("   python test_spotify_connection.py")
print("\nThe test should show audio features, not just find the track.")

# Also check if we're hitting rate limits
import os
import requests
from dotenv import load_dotenv
import time

load_dotenv()

print("\n" + "="*50)
print("🧪 Testing current credentials...")

client_id = os.getenv('SPOTIFY_CLIENT_ID')
client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')

if client_id and client_secret:
    # Get new token
    auth_response = requests.post('https://accounts.spotify.com/api/token', {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
    })
    
    if auth_response.status_code == 200:
        token = auth_response.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        
        # Test a simple search
        search_response = requests.get(
            'https://api.spotify.com/v1/search',
            headers=headers,
            params={'q': 'The Beatles', 'type': 'artist', 'limit': 1}
        )
        
        print(f"\n✅ Search API: {search_response.status_code}")
        
        # Test audio features with a known track ID
        # "Here Comes the Sun" by The Beatles
        test_track_id = '6dGnYIeXmHdcikdzNNDMm2'
        features_response = requests.get(
            f'https://api.spotify.com/v1/audio-features/{test_track_id}',
            headers=headers
        )
        
        print(f"❓ Audio Features API: {features_response.status_code}")
        
        if features_response.status_code == 403:
            print("\n❌ Confirmed: Audio features are blocked.")
            print("   You need to recreate your Spotify app.")
        elif features_response.status_code == 429:
            print("\n⏱️  Rate limited. Wait a few minutes.")
        elif features_response.status_code == 200:
            print("\n✅ Audio features work! The issue might be temporary.")
            print("   Try running the enrichment script again.")
else:
    print("\n❌ No credentials found in environment.") 