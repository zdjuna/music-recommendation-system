#!/usr/bin/env python3
"""
Test Spotify API connection with credentials
"""

import os
from pathlib import Path
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

print("🎵 Testing Spotify API Connection")
print("="*50)

# Get credentials
client_id = os.getenv('SPOTIFY_CLIENT_ID')
client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')

print(f"\n🔑 Credentials loaded:")
print(f"   Client ID: {client_id[:8]}..." if client_id else "   Client ID: Not found")
print(f"   Client Secret: {client_secret[:8]}..." if client_secret else "   Client Secret: Not found")

if not client_id or not client_secret:
    print("\n❌ Credentials not found in environment!")
    print("Make sure .env file contains:")
    print("   SPOTIFY_CLIENT_ID=your_client_id")
    print("   SPOTIFY_CLIENT_SECRET=your_client_secret")
    exit(1)

# Test authentication
print("\n🔍 Testing authentication...")
auth_url = 'https://accounts.spotify.com/api/token'
auth_response = requests.post(auth_url, {
    'grant_type': 'client_credentials',
    'client_id': client_id,
    'client_secret': client_secret,
})

if auth_response.status_code == 200:
    token = auth_response.json()['access_token']
    print("✅ Authentication successful!")
    print(f"   Access token: {token[:20]}...")
    
    # Test with a sample track
    print("\n🧪 Testing track search...")
    headers = {'Authorization': f'Bearer {token}'}
    search_url = 'https://api.spotify.com/v1/search'
    params = {
        'q': 'artist:Radiohead track:Creep',
        'type': 'track',
        'limit': 1
    }
    
    search_response = requests.get(search_url, headers=headers, params=params)
    
    if search_response.status_code == 200:
        data = search_response.json()
        if data['tracks']['items']:
            track = data['tracks']['items'][0]
            track_id = track['id']
            print(f"✅ Found track: {track['artists'][0]['name']} - {track['name']}")
            
            # Get audio features
            features_url = f'https://api.spotify.com/v1/audio-features/{track_id}'
            features_response = requests.get(features_url, headers=headers)
            
            if features_response.status_code == 200:
                features = features_response.json()
                print(f"\n📊 Audio Features for '{track['name']}':")
                print(f"   Valence (happiness): {features['valence']:.3f}")
                print(f"   Energy: {features['energy']:.3f}")
                print(f"   Danceability: {features['danceability']:.3f}")
                print(f"   Tempo: {features['tempo']:.0f} BPM")
                print(f"   Key: {features['key']} ({'Major' if features['mode'] == 1 else 'Minor'})")
                print(f"   Acousticness: {features['acousticness']:.3f}")
                print(f"   Instrumentalness: {features['instrumentalness']:.3f}")
                
                print("\n✨ Spotify API is working perfectly!")
                print("\n📋 Next step: Run `python enrich_with_spotify.py` to analyze your music library!")
else:
    print("❌ Authentication failed!")
    print(f"   Status: {auth_response.status_code}")
    print(f"   Error: {auth_response.text}")
    print("\nPlease check your credentials and try again.") 