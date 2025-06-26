#!/usr/bin/env python3
"""
AcousticBrainz Music Analyzer
Uses AcousticBrainz API for REAL audio features - FREE alternative to Spotify!
"""

import requests
import pandas as pd
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json
import time
import logging
from collections import Counter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AcousticBrainzFeatures:
    """Real audio features from AcousticBrainz API"""
    # From tonal data
    key: str
    key_strength: float
    scale: str  # major/minor
    
    # From rhythm data
    bpm: float
    danceability: float
    
    # From lowlevel data
    average_loudness: float
    dynamic_complexity: float
    
    # High-level features
    mood_acoustic: float
    mood_aggressive: float
    mood_electronic: float
    mood_happy: float
    mood_party: float
    mood_relaxed: float
    mood_sad: float
    
    # Genre probabilities
    genre_electronic: float
    genre_rock: float
    genre_jazz: float
    genre_classical: float
    
    # Additional
    acoustic: float
    instrumental: float
    
    # Computed mood
    primary_mood: str
    mood_quadrant: str

class AcousticBrainzAnalyzer:
    """
    Analyze music using AcousticBrainz REAL DATA
    FREE alternative to deprecated Spotify audio features!
    """
    
    def __init__(self):
        self.base_url = "https://acousticbrainz.org"
        self.session = requests.Session()
        logger.info("Initialized AcousticBrainz analyzer")
    
    def search_musicbrainz(self, artist: str, track: str) -> Optional[str]:
        """Search MusicBrainz for recording MBID"""
        try:
            # Search MusicBrainz API
            search_url = "https://musicbrainz.org/ws/2/recording"
            params = {
                'query': f'artist:"{artist}" AND recording:"{track}"',
                'fmt': 'json',
                'limit': 1
            }
            
            # MusicBrainz requires user agent
            headers = {
                'User-Agent': 'MusicRecommendationSystem/1.0 (https://example.com)'
            }
            
            response = self.session.get(search_url, params=params, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('recordings'):
                    mbid = data['recordings'][0]['id']
                    logger.debug(f"Found MBID {mbid} for {artist} - {track}")
                    return mbid
                    
            # Rate limit for MusicBrainz
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"Error searching MusicBrainz: {e}")
        
        return None
    
    def get_acousticbrainz_features(self, mbid: str) -> Optional[AcousticBrainzFeatures]:
        """Get features from AcousticBrainz using MBID"""
        try:
            # Get low-level data
            low_url = f"{self.base_url}/{mbid}/low-level"
            low_response = self.session.get(low_url)
            
            if low_response.status_code != 200:
                return None
                
            low_data = low_response.json()
            
            # Get high-level data
            high_url = f"{self.base_url}/{mbid}/high-level"
            high_response = self.session.get(high_url)
            
            if high_response.status_code != 200:
                return None
                
            high_data = high_response.json()
            
            # Extract features
            features = self._extract_features(low_data, high_data)
            return features
            
        except Exception as e:
            logger.error(f"Error getting AcousticBrainz features: {e}")
            return None
    
    def _extract_features(self, low_data: dict, high_data: dict) -> AcousticBrainzFeatures:
        """Extract relevant features from AcousticBrainz data"""
        # Low-level features
        tonal = low_data.get('tonal', {})
        rhythm = low_data.get('rhythm', {})
        lowlevel = low_data.get('lowlevel', {})
        
        # High-level features
        highlevel = high_data.get('highlevel', {})
        
        # Extract moods (if available)
        moods = highlevel.get('moods_mirex', {}).get('all', {})
        
        # Extract genres
        genre_electronic = highlevel.get('genre_electronic', {}).get('all', {})
        genre_tzanetakis = highlevel.get('genre_tzanetakis', {}).get('all', {})
        
        # Calculate primary mood based on available data
        mood_scores = {
            'happy': moods.get('Cluster1', 0),  # Happy/Excited
            'sad': moods.get('Cluster2', 0),    # Sad/Depressed
            'relaxed': moods.get('Cluster3', 0), # Relaxed/Calm
            'aggressive': moods.get('Cluster4', 0), # Aggressive/Angry
            'party': moods.get('Cluster5', 0)    # Party/Danceable
        }
        
        primary_mood = max(mood_scores, key=mood_scores.get)
        
        # Determine mood quadrant
        # Using danceability and key mode as proxies for valence/energy
        danceability_val = float(highlevel.get('danceability', {}).get('all', {}).get('danceable', 0.5))
        is_major = tonal.get('key_scale', 'minor') == 'major'
        
        if danceability_val > 0.5 and is_major:
            mood_quadrant = "Happy/Energetic"
        elif danceability_val > 0.5 and not is_major:
            mood_quadrant = "Angry/Tense"
        elif danceability_val <= 0.5 and is_major:
            mood_quadrant = "Peaceful/Calm"
        else:
            mood_quadrant = "Sad/Depressed"
        
        return AcousticBrainzFeatures(
            # Tonal
            key=tonal.get('key_key', 'C'),
            key_strength=float(tonal.get('key_strength', 0.5)),
            scale=tonal.get('key_scale', 'major'),
            
            # Rhythm
            bpm=float(rhythm.get('bpm', 120)),
            danceability=danceability_val,
            
            # Lowlevel
            average_loudness=float(lowlevel.get('average_loudness', 0.5)),
            dynamic_complexity=float(lowlevel.get('dynamic_complexity', 5)),
            
            # Moods
            mood_acoustic=float(moods.get('acoustic', 0)),
            mood_aggressive=float(moods.get('aggressive', 0)),
            mood_electronic=float(moods.get('electronic', 0)),
            mood_happy=float(moods.get('happy', 0)),
            mood_party=float(moods.get('party', 0)),
            mood_relaxed=float(moods.get('relaxed', 0)),
            mood_sad=float(moods.get('sad', 0)),
            
            # Genres
            genre_electronic=float(genre_electronic.get('electronic', 0)),
            genre_rock=float(genre_tzanetakis.get('roc', 0)),
            genre_jazz=float(genre_tzanetakis.get('jaz', 0)),
            genre_classical=float(genre_tzanetakis.get('cla', 0)),
            
            # Additional
            acoustic=float(highlevel.get('voice_instrumental', {}).get('all', {}).get('instrumental', 0)),
            instrumental=float(highlevel.get('voice_instrumental', {}).get('all', {}).get('instrumental', 0)),
            
            # Computed
            primary_mood=primary_mood,
            mood_quadrant=mood_quadrant
        )
    
    def get_track_features(self, artist: str, track: str) -> Optional[AcousticBrainzFeatures]:
        """Main method: Get features for an artist/track combination"""
        # First, find the MBID
        mbid = self.search_musicbrainz(artist, track)
        if not mbid:
            logger.warning(f"No MBID found for {artist} - {track}")
            return None
        
        # Then get features from AcousticBrainz
        features = self.get_acousticbrainz_features(mbid)
        if not features:
            logger.warning(f"No AcousticBrainz data for {artist} - {track} (MBID: {mbid})")
            
        return features
    
    def analyze_mood_from_features(self, features: AcousticBrainzFeatures) -> Dict[str, any]:
        """Analyze mood from AcousticBrainz features"""
        return {
            'primary_mood': features.primary_mood,
            'mood_quadrant': features.mood_quadrant,
            'is_acoustic': features.acoustic > 0.5,
            'is_instrumental': features.instrumental > 0.5,
            'is_danceable': features.danceability > 0.5,
            'is_major_key': features.scale == 'major',
            'tempo_category': self._categorize_tempo(features.bpm),
            'energy_estimate': 1 - features.mood_relaxed,  # Inverse of relaxed
            'valence_estimate': features.mood_happy - features.mood_sad  # Happy minus sad
        }
    
    def _categorize_tempo(self, bpm: float) -> str:
        """Categorize tempo (BPM)"""
        if bpm < 70:
            return "very slow"
        elif bpm < 100:
            return "slow"
        elif bpm < 120:
            return "moderate"
        elif bpm < 140:
            return "fast"
        else:
            return "very fast"


# Example usage
if __name__ == "__main__":
    analyzer = AcousticBrainzAnalyzer()
    
    # Test with some popular tracks
    test_tracks = [
        ("The Beatles", "Here Comes the Sun"),
        ("Radiohead", "Creep"),
        ("Daft Punk", "Get Lucky"),
        ("Adele", "Someone Like You")
    ]
    
    print("🎵 Testing AcousticBrainz analyzer with popular tracks:\n")
    
    for artist, track in test_tracks:
        print(f"\n{'='*60}")
        print(f"🎵 {artist} - {track}")
        print(f"{'='*60}")
        
        features = analyzer.get_track_features(artist, track)
        
        if features:
            print(f"✅ Found audio features!")
            print(f"   BPM: {features.bpm}")
            print(f"   Key: {features.key} {features.scale}")
            print(f"   Danceability: {features.danceability:.2%}")
            print(f"   Primary mood: {features.primary_mood}")
            print(f"   Mood quadrant: {features.mood_quadrant}")
            
            mood_analysis = analyzer.analyze_mood_from_features(features)
            print(f"\n   Mood Analysis:")
            print(f"   - Tempo: {mood_analysis['tempo_category']}")
            print(f"   - Acoustic: {'Yes' if mood_analysis['is_acoustic'] else 'No'}")
            print(f"   - Danceable: {'Yes' if mood_analysis['is_danceable'] else 'No'}")
        else:
            print(f"❌ No audio features found")
            print(f"   This track might not be in AcousticBrainz database")