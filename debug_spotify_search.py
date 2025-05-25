#!/usr/bin/env python3
"""
Debug why Spotify searches are failing
"""

import os
import requests
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()

def test_spotify_search():
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    
    # Get token
    auth_url = 'https://accounts.spotify.com/api/token'
    auth_response = requests.post(auth_url, {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
    })
    
    if auth_response.status_code != 200:
        print(f"❌ Auth failed: {auth_response.text}")
        return
    
    token = auth_response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    
    # Test tracks that should definitely exist
    test_tracks = [
        ("The Killers", "Bones"),
        ("Snow Patrol", "Chasing Cars"),
        ("Kate Nash", "Foundations"),
        ("Interpol", "Roland")
    ]
    
    print("🔍 Testing Spotify search with different query formats:\n")
    
    for artist, track in test_tracks:
        print(f"\n{'='*60}")
        print(f"🎵 {artist} - {track}")
        print(f"{'='*60}")
        
        # Try different search query formats
        queries = [
            f'artist:{artist} track:{track}',
            f'artist:"{artist}" track:"{track}"',
            f'{artist} {track}',
            f'"{artist}" "{track}"'
        ]
        
        for query in queries:
            search_url = 'https://api.spotify.com/v1/search'
            params = {
                'q': query,
                'type': 'track',
                'limit': 3
            }
            
            print(f"\n📝 Query: {query}")
            logger.debug(f"Full URL: {search_url}?q={query}&type=track&limit=3")
            
            response = requests.get(search_url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                tracks = data['tracks']['items']
                
                if tracks:
                    print(f"✅ Found {len(tracks)} results:")
                    for i, t in enumerate(tracks[:3]):
                        print(f"   {i+1}. {t['artists'][0]['name']} - {t['name']}")
                        if i == 0:  # Show details for first match
                            print(f"      Album: {t['album']['name']}")
                            print(f"      Popularity: {t['popularity']}")
                            print(f"      Track ID: {t['id']}")
                else:
                    print(f"❌ No results found")
            else:
                print(f"❌ Search failed: {response.status_code}")
                print(f"   Error: {response.text}")

if __name__ == "__main__":
    test_spotify_search() 