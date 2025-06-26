#!/usr/bin/env python3
"""
Simple Spotify Test - Direct approach to understand the 403 error
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_spotify_direct():
    """Test Spotify access step by step"""
    
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    
    print(f"Client ID exists: {bool(client_id)}")
    print(f"Client Secret exists: {bool(client_secret)}")
    
    if not client_id or not client_secret:
        print("❌ Missing Spotify credentials")
        return
    
    print(f"Client ID: {client_id[:10]}...")
    
    # Step 1: Get access token
    print("\n1. Getting access token...")
    auth_url = 'https://accounts.spotify.com/api/token'
    auth_data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret
    }
    
    try:
        auth_response = requests.post(auth_url, data=auth_data, timeout=10)
        print(f"Auth response status: {auth_response.status_code}")
        
        if auth_response.status_code == 200:
            token_data = auth_response.json()
            access_token = token_data['access_token']
            print("✅ Got access token successfully")
            
            # Step 2: Test search
            print("\n2. Testing search...")
            headers = {'Authorization': f'Bearer {access_token}'}
            search_url = 'https://api.spotify.com/v1/search'
            search_params = {
                'q': 'The Beatles Hey Jude',
                'type': 'track',
                'limit': 1
            }
            
            search_response = requests.get(search_url, headers=headers, params=search_params, timeout=10)
            print(f"Search response status: {search_response.status_code}")
            
            if search_response.status_code == 200:
                search_data = search_response.json()
                if search_data['tracks']['items']:
                    track = search_data['tracks']['items'][0]
                    track_id = track['id']
                    print(f"✅ Found track: {track['name']} by {track['artists'][0]['name']}")
                    print(f"Track ID: {track_id}")
                    
                    # Step 3: Test audio features - this is where we expect the 403
                    print("\n3. Testing audio features...")
                    features_url = f'https://api.spotify.com/v1/audio-features/{track_id}'
                    features_response = requests.get(features_url, headers=headers, timeout=10)
                    
                    print(f"Audio features response status: {features_response.status_code}")
                    print(f"Audio features response headers: {dict(features_response.headers)}")
                    print(f"Audio features response text: {features_response.text}")
                    
                    if features_response.status_code == 200:
                        print("✅ Audio features work!")
                        features_data = features_response.json()
                        print(f"Valence: {features_data.get('valence', 'N/A')}")
                        print(f"Energy: {features_data.get('energy', 'N/A')}")
                    else:
                        print(f"❌ Audio features failed with {features_response.status_code}")
                        
                        if features_response.status_code == 403:
                            print("This is the 403 Forbidden error we've been seeing")
                            print("This might indicate:")
                            print("- App needs different permissions/scopes")
                            print("- Track is not available in your region")
                            print("- API endpoint requires user authentication")
                else:
                    print("❌ No tracks found in search")
            else:
                print(f"❌ Search failed: {search_response.text}")
        else:
            print(f"❌ Auth failed: {auth_response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_spotify_direct()
