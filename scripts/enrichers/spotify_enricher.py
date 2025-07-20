#!/usr/bin/env python3
"""
Comprehensive Spotify Permissions and Access Fix

This script will:
1. Test current Spotify authentication 
2. Try different API scopes and approaches
3. Implement a complete re-authorization flow if needed
4. Create a working Spotify audio features analyzer
"""

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
import os
import requests
import json
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

class SpotifyAccessFixer:
    """Comprehensive Spotify access troubleshooter and fixer"""
    
    def __init__(self):
        self.client_id = os.getenv('SPOTIFY_CLIENT_ID')
        self.client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        self.redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI', 'http://localhost:8888/callback')
        
        if not self.client_id or not self.client_secret:
            raise ValueError("Spotify credentials not found in environment variables")
    
    def test_client_credentials_flow(self):
        """Test the simplest Spotify access method (no user authorization needed)"""
        print("🔍 Testing Spotify Client Credentials Flow...")
        
        try:
            # Client Credentials flow - good for accessing public data
            client_credentials_manager = SpotifyClientCredentials(
                client_id=self.client_id,
                client_secret=self.client_secret
            )
            sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
            
            # Test with a simple search
            results = sp.search(q='artist:The Beatles track:Hey Jude', type='track', limit=1)
            
            if results and results['tracks']['items']:
                track = results['tracks']['items'][0]
                track_id = track['id']
                print(f"✅ Search successful! Found: {track['name']} by {track['artists'][0]['name']}")
                
                # Now try to get audio features - this is where we were failing
                try:
                    audio_features = sp.audio_features([track_id])
                    if audio_features and audio_features[0]:
                        print("✅ Audio features access successful!")
                        features = audio_features[0]
                        print(f"   Valence: {features['valence']:.3f}")
                        print(f"   Energy: {features['energy']:.3f}")
                        print(f"   Danceability: {features['danceability']:.3f}")
                        return sp, True
                    else:
                        print("❌ Audio features returned None")
                        return sp, False
                        
                except Exception as e:
                    print(f"❌ Audio features error: {e}")
                    return sp, False
            else:
                print("❌ Search failed - no results")
                return None, False
                
        except Exception as e:
            print(f"❌ Client credentials flow failed: {e}")
            return None, False
    
    def test_authorization_code_flow(self):
        """Test the full OAuth flow (requires user authorization)"""
        print("\n🔍 Testing Spotify Authorization Code Flow...")
        
        try:
            # Authorization code flow with all needed scopes
            scope = "user-read-private user-read-email playlist-read-private user-library-read"
            
            sp_oauth = SpotifyOAuth(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                scope=scope,
                cache_path=".spotify_cache"
            )
            
            sp = spotipy.Spotify(auth_manager=sp_oauth)
            
            # Test user access
            user = sp.current_user()
            print(f"✅ User authorization successful! User: {user.get('display_name', user['id'])}")
            
            # Test audio features with user auth
            results = sp.search(q='artist:The Beatles track:Hey Jude', type='track', limit=1)
            if results and results['tracks']['items']:
                track_id = results['tracks']['items'][0]['id']
                audio_features = sp.audio_features([track_id])
                
                if audio_features and audio_features[0]:
                    print("✅ Audio features with user auth successful!")
                    return sp, True
                else:
                    print("❌ Audio features still failing with user auth")
                    return sp, False
            else:
                print("❌ Search failed with user auth")
                return sp, False
                
        except Exception as e:
            print(f"❌ Authorization code flow failed: {e}")
            return None, False
    
    def test_direct_api_calls(self):
        """Test direct Spotify Web API calls to bypass spotipy"""
        print("\n🔍 Testing Direct Spotify Web API Calls...")
        
        try:
            # Get access token directly
            auth_url = 'https://accounts.spotify.com/api/token'
            auth_data = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }
            
            auth_response = requests.post(auth_url, data=auth_data, timeout=30)
            auth_response.raise_for_status()
            
            access_token = auth_response.json()['access_token']
            print("✅ Got access token directly")
            
            # Test search
            headers = {'Authorization': f'Bearer {access_token}'}
            search_url = 'https://api.spotify.com/v1/search'
            search_params = {
                'q': 'artist:The Beatles track:Hey Jude',
                'type': 'track',
                'limit': 1
            }
            
            search_response = requests.get(search_url, headers=headers, params=search_params, timeout=30)
            search_response.raise_for_status()
            
            search_data = search_response.json()
            if search_data['tracks']['items']:
                track = search_data['tracks']['items'][0]
                track_id = track['id']
                print(f"✅ Direct search successful: {track['name']}")
                
                # Test audio features directly
                features_url = f'https://api.spotify.com/v1/audio-features/{track_id}'
                features_response = requests.get(features_url, headers=headers, timeout=30)
                
                print(f"Audio features response status: {features_response.status_code}")
                print(f"Audio features response: {features_response.text[:200]}...")
                
                if features_response.status_code == 200:
                    features_data = features_response.json()
                    print("✅ Direct audio features successful!")
                    print(f"   Valence: {features_data['valence']:.3f}")
                    print(f"   Energy: {features_data['energy']:.3f}")
                    return True, access_token
                else:
                    print(f"❌ Direct audio features failed: {features_response.status_code}")
                    print(f"   Error: {features_response.text}")
                    return False, access_token
            else:
                print("❌ Direct search found no results")
                return False, None
                
        except Exception as e:
            print(f"❌ Direct API calls failed: {e}")
            return False, None
    
    def create_working_spotify_analyzer(self, sp_client=None, access_token=None):
        """Create a working Spotify analyzer based on successful method"""
        print("\n🔧 Creating working Spotify analyzer...")
        
        if sp_client:
            # Use spotipy client
            analyzer_code = '''
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
from dotenv import load_dotenv

class WorkingSpotifyAnalyzer:
    """Working Spotify music analyzer"""
    
    def __init__(self):
        load_dotenv()
        client_credentials_manager = SpotifyClientCredentials(
            client_id=os.getenv('SPOTIFY_CLIENT_ID'),
            client_secret=os.getenv('SPOTIFY_CLIENT_SECRET')
        )
        self.sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    
    def analyze_track(self, artist, track):
        """Get comprehensive audio analysis for a track"""
        try:
            # Search for track
            query = f'artist:"{artist}" track:"{track}"'
            results = self.sp.search(q=query, type='track', limit=1)
            
            if results and results['tracks']['items']:
                track_info = results['tracks']['items'][0]
                track_id = track_info['id']
                
                # Get audio features
                audio_features = self.sp.audio_features([track_id])
                
                if audio_features and audio_features[0]:
                    features = audio_features[0]
                    
                    return {
                        'spotify_id': track_id,
                        'matched_name': track_info['name'],
                        'matched_artist': track_info['artists'][0]['name'],
                        'valence': features['valence'],
                        'energy': features['energy'],
                        'danceability': features['danceability'],
                        'acousticness': features['acousticness'],
                        'instrumentalness': features['instrumentalness'],
                        'liveness': features['liveness'],
                        'speechiness': features['speechiness'],
                        'tempo': features['tempo'],
                        'loudness': features['loudness'],
                        'mode': features['mode'],
                        'key': features['key'],
                        'time_signature': features['time_signature'],
                        'analysis_successful': True
                    }
            
            return {'analysis_successful': False, 'error': 'Track not found or no audio features'}
            
        except Exception as e:
            return {'analysis_successful': False, 'error': str(e)}
'''
        
        elif access_token:
            # Use direct API calls
            analyzer_code = f'''
import requests
import os
from dotenv import load_dotenv

class WorkingSpotifyAnalyzer:
    """Working Spotify analyzer using direct API calls"""
    
    def __init__(self):
        load_dotenv()
        self.client_id = os.getenv('SPOTIFY_CLIENT_ID')
        self.client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        self.access_token = None
        self._get_access_token()
    
    def _get_access_token(self):
        """Get fresh access token"""
        auth_url = 'https://accounts.spotify.com/api/token'
        auth_data = {{
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }}
        
        response = requests.post(auth_url, data=auth_data, timeout=30)
        response.raise_for_status()
        self.access_token = response.json()['access_token']
    
    def analyze_track(self, artist, track):
        """Get comprehensive audio analysis for a track"""
        try:
            headers = {{'Authorization': f'Bearer {{self.access_token}}'}}
            
            # Search for track
            search_url = 'https://api.spotify.com/v1/search'
            search_params = {{
                'q': f'artist:"{{artist}}" track:"{{track}}"',
                'type': 'track',
                'limit': 1
            }}
            
            search_response = requests.get(search_url, headers=headers, params=search_params, timeout=30)
            search_response.raise_for_status()
            
            search_data = search_response.json()
            if search_data['tracks']['items']:
                track_info = search_data['tracks']['items'][0]
                track_id = track_info['id']
                
                # Get audio features
                features_url = f'https://api.spotify.com/v1/audio-features/{{track_id}}'
                features_response = requests.get(features_url, headers=headers, timeout=30)
                
                if features_response.status_code == 200:
                    features = features_response.json()
                    
                    return {{
                        'spotify_id': track_id,
                        'matched_name': track_info['name'],
                        'matched_artist': track_info['artists'][0]['name'],
                        'valence': features['valence'],
                        'energy': features['energy'],
                        'danceability': features['danceability'],
                        'acousticness': features['acousticness'],
                        'instrumentalness': features['instrumentalness'],
                        'liveness': features['liveness'],
                        'speechiness': features['speechiness'],
                        'tempo': features['tempo'],
                        'loudness': features['loudness'],
                        'mode': features['mode'],
                        'key': features['key'],
                        'time_signature': features['time_signature'],
                        'analysis_successful': True
                    }}
            
            return {{'analysis_successful': False, 'error': 'Track not found or no audio features'}}
            
        except Exception as e:
            return {{'analysis_successful': False, 'error': str(e)}}
'''
        
        # Save the working analyzer
        with open('working_spotify_analyzer.py', 'w') as f:
            f.write(analyzer_code)
        
        print("✅ Created working_spotify_analyzer.py")
        return True
    
    def run_comprehensive_test(self):
        """Run all tests and create working analyzer"""
        print("🔧 Running comprehensive Spotify access test...\n")
        
        # Test 1: Client Credentials Flow
        sp_client, client_success = self.test_client_credentials_flow()
        
        # Test 2: Authorization Code Flow (only if client credentials failed)
        if not client_success:
            sp_auth, auth_success = self.test_authorization_code_flow()
        else:
            sp_auth, auth_success = None, False
        
        # Test 3: Direct API calls (if spotipy methods failed)
        if not client_success and not auth_success:
            direct_success, access_token = self.test_direct_api_calls()
        else:
            direct_success, access_token = False, None
        
        # Create working analyzer based on successful method
        if client_success:
            print("\n✅ Client Credentials Flow works - creating analyzer...")
            self.create_working_spotify_analyzer(sp_client=sp_client)
            return sp_client
        elif auth_success:
            print("\n✅ Authorization Code Flow works - creating analyzer...")
            self.create_working_spotify_analyzer(sp_client=sp_auth)
            return sp_auth
        elif direct_success:
            print("\n✅ Direct API calls work - creating analyzer...")
            self.create_working_spotify_analyzer(access_token=access_token)
            return access_token
        else:
            print("\n❌ All Spotify access methods failed!")
            print("Possible issues:")
            print("1. Invalid Spotify credentials")
            print("2. App not properly registered with Spotify")
            print("3. Rate limiting or API restrictions")
            print("4. Network connectivity issues")
            return None


def main():
    """Test and fix Spotify access"""
    print("🎵 Spotify Access Comprehensive Fix\n")
    
    try:
        fixer = SpotifyAccessFixer()
        result = fixer.run_comprehensive_test()
        
        if result:
            print("\n🎉 SUCCESS! Spotify access is now working.")
            print("You can now use working_spotify_analyzer.py for music analysis.")
            
            # Test the working analyzer
            print("\n🧪 Testing the working analyzer...")
            if os.path.exists('working_spotify_analyzer.py'):
                import importlib.util
                spec = importlib.util.spec_from_file_location("working_analyzer", "working_spotify_analyzer.py")
                working_analyzer = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(working_analyzer)
                
                analyzer = working_analyzer.WorkingSpotifyAnalyzer()
                test_result = analyzer.analyze_track("The Beatles", "Hey Jude")
                
                if test_result.get('analysis_successful'):
                    print("✅ Working analyzer test successful!")
                    print(f"   Track: {test_result['matched_name']}")
                    print(f"   Valence: {test_result['valence']:.3f}")
                    print(f"   Energy: {test_result['energy']:.3f}")
                else:
                    print(f"❌ Working analyzer test failed: {test_result.get('error')}")
        else:
            print("\n❌ FAILED! Could not establish working Spotify access.")
            print("Please check your Spotify app credentials and registration.")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")


if __name__ == "__main__":
    main()
