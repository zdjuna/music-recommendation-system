#!/usr/bin/env python3
"""
REAL Music Analysis System
Uses actual music data instead of bullshit text analysis
"""

import pandas as pd
import requests
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json
import time
from collections import Counter
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TrackFeatures:
    """Real audio features from Spotify API"""
    valence: float  # 0-1 (sad to happy)
    energy: float   # 0-1 (calm to energetic)
    danceability: float
    acousticness: float
    instrumentalness: float
    speechiness: float
    tempo: float
    key: int
    mode: int  # 0=minor, 1=major
    loudness: float
    duration_ms: int

class RealMusicAnalyzer:
    """
    Analyze music using ACTUAL DATA:
    1. Spotify Audio Features API
    2. Last.fm user tags
    3. MusicBrainz genre/tag data
    
    NO FAKE TEXT ANALYSIS OF ARTIST NAMES!
    """
    
    def __init__(self, spotify_client_id: Optional[str] = None, 
                 spotify_client_secret: Optional[str] = None):
        self.spotify_token = None
        self.spotify_client_id = spotify_client_id or os.getenv('SPOTIFY_CLIENT_ID')
        self.spotify_client_secret = spotify_client_secret or os.getenv('SPOTIFY_CLIENT_SECRET')
        
        if self.spotify_client_id and self.spotify_client_secret:
            self._authenticate_spotify()
    
    def _authenticate_spotify(self):
        """Get Spotify access token"""
        auth_url = 'https://accounts.spotify.com/api/token'
        auth_response = requests.post(auth_url, {
            'grant_type': 'client_credentials',
            'client_id': self.spotify_client_id,
            'client_secret': self.spotify_client_secret,
        })
        
        if auth_response.status_code == 200:
            self.spotify_token = auth_response.json()['access_token']
            logger.info("Successfully authenticated with Spotify")
        else:
            logger.error(f"Failed to authenticate with Spotify: {auth_response.status_code}")
    
    def get_spotify_track_features(self, artist: str, track: str) -> Optional[TrackFeatures]:
        """Get real audio features from Spotify"""
        if not self.spotify_token:
            return None
        
        # Search for track
        search_url = 'https://api.spotify.com/v1/search'
        headers = {'Authorization': f'Bearer {self.spotify_token}'}
        params = {
            'q': f'artist:{artist} track:{track}',
            'type': 'track',
            'limit': 1
        }
        
        try:
            response = requests.get(search_url, headers=headers, params=params)
            logger.debug(f"Search response status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                logger.debug(f"Found {len(data['tracks']['items'])} tracks")
                if data['tracks']['items']:
                    track_id = data['tracks']['items'][0]['id']
                    
                    # Get audio features
                    features_url = f'https://api.spotify.com/v1/audio-features/{track_id}'
                    features_response = requests.get(features_url, headers=headers)
                    
                    if features_response.status_code == 200:
                        features = features_response.json()
                        return TrackFeatures(
                            valence=features['valence'],
                            energy=features['energy'],
                            danceability=features['danceability'],
                            acousticness=features['acousticness'],
                            instrumentalness=features['instrumentalness'],
                            speechiness=features['speechiness'],
                            tempo=features['tempo'],
                            key=features['key'],
                            mode=features['mode'],
                            loudness=features['loudness'],
                            duration_ms=features['duration_ms']
                        )
                else:
                    logger.debug(f"No tracks found for: {artist} - {track}")
            else:
                logger.error(f"Search failed with status {response.status_code}")
        except Exception as e:
            logger.error(f"Error getting Spotify features: {e}")
        
        return None
    
    def get_lastfm_tags(self, artist: str, track: str, api_key: Optional[str] = None) -> List[str]:
        """Get real user-generated tags from Last.fm"""
        api_key = api_key or os.getenv('LASTFM_API_KEY')
        if not api_key:
            return []
        
        url = 'http://ws.audioscrobbler.com/2.0/'
        params = {
            'method': 'track.getTopTags',
            'artist': artist,
            'track': track,
            'api_key': api_key,
            'format': 'json'
        }
        
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if 'toptags' in data and 'tag' in data['toptags']:
                    return [tag['name'] for tag in data['toptags']['tag'][:10]]
        except Exception as e:
            logger.error(f"Error getting Last.fm tags: {e}")
        
        return []
    
    def analyze_mood_from_features(self, features: TrackFeatures) -> Dict[str, any]:
        """Derive mood from REAL audio features"""
        mood = {
            'valence': features.valence,
            'energy': features.energy,
            'mood_quadrant': self._get_mood_quadrant(features.valence, features.energy),
            'is_acoustic': features.acousticness > 0.5,
            'is_instrumental': features.instrumentalness > 0.5,
            'is_danceable': features.danceability > 0.6,
            'is_major_key': features.mode == 1,
            'tempo_category': self._categorize_tempo(features.tempo)
        }
        
        # Derive primary mood from features
        if features.valence > 0.7 and features.energy > 0.7:
            mood['primary_mood'] = 'happy/energetic'
        elif features.valence > 0.7 and features.energy < 0.3:
            mood['primary_mood'] = 'peaceful/content'
        elif features.valence < 0.3 and features.energy > 0.7:
            mood['primary_mood'] = 'angry/aggressive'
        elif features.valence < 0.3 and features.energy < 0.3:
            mood['primary_mood'] = 'sad/melancholic'
        elif features.valence < 0.5 and features.energy < 0.5:
            mood['primary_mood'] = 'melancholic'
        else:
            mood['primary_mood'] = 'neutral'
        
        return mood
    
    def _get_mood_quadrant(self, valence: float, energy: float) -> str:
        """Get mood quadrant based on REAL valence and energy values"""
        if valence > 0.5 and energy > 0.5:
            return "Happy/Energetic"
        elif valence > 0.5 and energy <= 0.5:
            return "Peaceful/Calm"
        elif valence <= 0.5 and energy > 0.5:
            return "Angry/Tense"
        else:
            return "Sad/Depressed"
    
    def _categorize_tempo(self, tempo: float) -> str:
        """Categorize tempo (BPM)"""
        if tempo < 70:
            return "very slow"
        elif tempo < 100:
            return "slow"
        elif tempo < 120:
            return "moderate"
        elif tempo < 140:
            return "fast"
        else:
            return "very fast"
    
    def analyze_listening_patterns(self, scrobbles_df: pd.DataFrame) -> Dict[str, any]:
        """Analyze actual listening patterns from Last.fm data"""
        analysis = {}
        
        # Time-based patterns
        scrobbles_df['date'] = pd.to_datetime(scrobbles_df['date'])
        scrobbles_df['hour'] = scrobbles_df['date'].dt.hour
        scrobbles_df['day_of_week'] = scrobbles_df['date'].dt.day_name()
        scrobbles_df['month'] = scrobbles_df['date'].dt.month
        
        # Most active listening hours
        analysis['peak_listening_hours'] = scrobbles_df['hour'].value_counts().head(3).to_dict()
        
        # Most active days
        analysis['peak_listening_days'] = scrobbles_df['day_of_week'].value_counts().head(3).to_dict()
        
        # Top artists
        analysis['top_artists'] = scrobbles_df['artist'].value_counts().head(10).to_dict()
        
        # Top tracks
        analysis['top_tracks'] = scrobbles_df.groupby(['artist', 'track']).size().sort_values(ascending=False).head(10).to_dict()
        
        # Listening diversity
        analysis['unique_artists'] = scrobbles_df['artist'].nunique()
        analysis['unique_tracks'] = len(scrobbles_df.drop_duplicates(['artist', 'track']))
        analysis['listening_diversity'] = analysis['unique_tracks'] / len(scrobbles_df)
        
        # Repeat listening behavior
        track_plays = scrobbles_df.groupby(['artist', 'track']).size()
        analysis['tracks_played_once'] = (track_plays == 1).sum()
        analysis['tracks_played_10+_times'] = (track_plays >= 10).sum()
        analysis['average_plays_per_track'] = track_plays.mean()
        
        return analysis
    
    def create_music_profile(self, scrobbles_path: str, enriched_path: Optional[str] = None) -> Dict[str, any]:
        """Create a comprehensive music profile from REAL data"""
        # Load scrobbles
        scrobbles_df = pd.read_csv(scrobbles_path)
        
        # Analyze listening patterns
        profile = {
            'listening_patterns': self.analyze_listening_patterns(scrobbles_df),
            'total_scrobbles': len(scrobbles_df),
            'date_range': {
                'first_scrobble': scrobbles_df['date'].min(),
                'last_scrobble': scrobbles_df['date'].max()
            }
        }
        
        # If we have enriched data, analyze moods
        if enriched_path and os.path.exists(enriched_path):
            enriched_df = pd.read_csv(enriched_path)
            
            # Real mood distribution (from existing data)
            mood_counts = enriched_df['simplified_mood'].value_counts()
            profile['mood_distribution'] = mood_counts.to_dict()
            profile['dominant_mood'] = mood_counts.index[0] if len(mood_counts) > 0 else 'unknown'
            
            # Genre analysis from MusicBrainz tags
            if 'musicbrainz_genres' in enriched_df.columns:
                all_genres = []
                for genres in enriched_df['musicbrainz_genres'].dropna():
                    all_genres.extend([g.strip() for g in str(genres).split(',')])
                
                genre_counts = Counter(all_genres)
                profile['top_genres'] = dict(genre_counts.most_common(10))
        
        return profile


# Example usage
if __name__ == "__main__":
    analyzer = RealMusicAnalyzer()
    
    # Example: Get real Spotify audio features
    print("Example with Spotify features (if API credentials are set):")
    features = analyzer.get_spotify_track_features("Interpol", "Roland")
    if features:
        print(f"Interpol - Roland:")
        print(f"  Valence (happiness): {features.valence:.3f}")
        print(f"  Energy: {features.energy:.3f}")
        print(f"  Danceability: {features.danceability:.3f}")
        print(f"  Mode: {'Major' if features.mode == 1 else 'Minor'}")
        
        mood = analyzer.analyze_mood_from_features(features)
        print(f"  Mood analysis: {mood['primary_mood']} ({mood['mood_quadrant']})")
    else:
        print("  No Spotify credentials available")
    
    # Example: Analyze real listening patterns
    print("\nAnalyzing your Last.fm listening patterns...")
    profile = analyzer.create_music_profile('data/zdjuna_scrobbles.csv', 'data/zdjuna_enriched.csv')
    
    print(f"\nTotal scrobbles: {profile['total_scrobbles']}")
    print(f"Top 5 artists: {list(profile['listening_patterns']['top_artists'].items())[:5]}")
    print(f"Listening diversity: {profile['listening_patterns']['listening_diversity']:.1%}")
    print(f"Mood distribution: {profile.get('mood_distribution', 'N/A')}") 