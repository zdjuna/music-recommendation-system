#!/usr/bin/env python3
"""
Musimap API enricher for music mood and metadata analysis
"""

import requests
import time
import logging
from typing import Dict, List, Optional, Any
import json
from dataclasses import dataclass

@dataclass
class MusimapConfig:
    """Configuration for Musimap API"""
    base_url: str = "https://api-v2.musimap.io"
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    access_token: Optional[str] = None
    rate_limit_delay: float = 0.1  # 100ms between requests

class MusimapEnricher:
    """
    Enriches music tracks with Musimap's emotional AI and metadata analysis
    
    Features:
    - MusiMotion: Mood, genre, and situation tagging
    - MusiMatch: Audio-based similarity matching
    - Weighted relevancy scores for all tags
    """
    
    def __init__(self, config: Optional[MusimapConfig] = None):
        self.config = config or MusimapConfig()
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        
        # Set up authentication headers if token is available
        if self.config.access_token:
            self.session.headers.update({
                'Authorization': f'Bearer {self.config.access_token}',
                'Content-Type': 'application/json'
            })
    
    def authenticate(self, client_id: str, client_secret: str) -> bool:
        """
        Authenticate with Musimap API using OAuth2 client credentials flow
        """
        auth_url = f"{self.config.base_url}/oauth/token"
        
        auth_data = {
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret
        }
        
        try:
            response = requests.post(auth_url, data=auth_data)
            response.raise_for_status()
            
            token_data = response.json()
            self.config.access_token = token_data.get('access_token')
            
            if self.config.access_token:
                self.session.headers.update({
                    'Authorization': f'Bearer {self.config.access_token}',
                    'Content-Type': 'application/json'
                })
                self.logger.info("Successfully authenticated with Musimap API")
                return True
            else:
                self.logger.error("No access token received from Musimap")
                return False
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Authentication failed: {e}")
            return False
    
    def search_track(self, artist: str, title: str) -> Optional[Dict[str, Any]]:
        """
        Search for a track in Musimap's catalog
        """
        search_url = f"{self.config.base_url}/search"
        
        # Try different search strategies
        search_queries = [
            f'artist:"{artist}" title:"{title}"',
            f'"{artist}" "{title}"',
            f'{artist} {title}'
        ]
        
        for query in search_queries:
            try:
                params = {
                    'q': query,
                    'type': 'track',
                    'limit': 10
                }
                
                response = self.session.get(search_url, params=params)
                
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 1))
                    self.logger.warning(f"Rate limited, waiting {retry_after} seconds")
                    time.sleep(retry_after)
                    continue
                
                response.raise_for_status()
                data = response.json()
                
                if data.get('status') == 200 and data.get('data'):
                    tracks = data['data']
                    
                    # Find best match using fuzzy matching
                    best_match = self._find_best_match(artist, title, tracks)
                    if best_match:
                        self.logger.info(f"Found track match for '{artist} - {title}': {best_match.get('title', 'Unknown')}")
                        return best_match
                
                # Rate limiting between attempts
                time.sleep(self.config.rate_limit_delay)
                
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Search request failed for '{artist} - {title}': {e}")
                continue
        
        self.logger.warning(f"No track found for '{artist} - {title}'")
        return None
    
    def get_track_analysis(self, track_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed analysis for a track using MusiMotion
        """
        analysis_url = f"{self.config.base_url}/tracks/{track_id}/analysis"
        
        try:
            response = self.session.get(analysis_url)
            
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 1))
                self.logger.warning(f"Rate limited, waiting {retry_after} seconds")
                time.sleep(retry_after)
                response = self.session.get(analysis_url)
            
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') == 200:
                return data.get('data')
            else:
                self.logger.error(f"Analysis request failed with status: {data.get('status')}")
                return None
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Analysis request failed for track {track_id}: {e}")
            return None
    
    def enrich_track(self, artist: str, title: str) -> Optional[Dict[str, Any]]:
        """
        Enrich a single track with Musimap data
        """
        # Search for the track
        track_data = self.search_track(artist, title)
        if not track_data:
            return None
        
        track_id = track_data.get('id')
        if not track_id:
            self.logger.error(f"No track ID found for '{artist} - {title}'")
            return None
        
        # Get detailed analysis
        analysis = self.get_track_analysis(track_id)
        if not analysis:
            return None
        
        # Extract and structure the enrichment data
        enriched_data = self._extract_enrichment_data(track_data, analysis)
        
        self.logger.info(f"Successfully enriched '{artist} - {title}' with Musimap data")
        return enriched_data
    
    def enrich_tracks_batch(self, tracks: List[Dict[str, str]], max_tracks: int = 50) -> Dict[str, Dict[str, Any]]:
        """
        Enrich multiple tracks in batch
        """
        enriched_results = {}
        processed_count = 0
        
        for track in tracks[:max_tracks]:
            if processed_count >= max_tracks:
                break
            
            artist = track.get('artist', '').strip()
            title = track.get('title', '').strip()
            
            if not artist or not title:
                continue
            
            track_key = f"{artist} - {title}"
            
            try:
                enriched_data = self.enrich_track(artist, title)
                if enriched_data:
                    enriched_results[track_key] = enriched_data
                    processed_count += 1
                    
                    if processed_count % 10 == 0:
                        self.logger.info(f"Processed {processed_count} tracks")
                
                # Rate limiting
                time.sleep(self.config.rate_limit_delay)
                
            except Exception as e:
                self.logger.error(f"Error enriching '{track_key}': {e}")
                continue
        
        self.logger.info(f"Batch enrichment complete: {len(enriched_results)} tracks enriched")
        return enriched_results
    
    def _find_best_match(self, target_artist: str, target_title: str, tracks: List[Dict]) -> Optional[Dict]:
        """
        Find the best matching track using fuzzy string matching
        """
        from difflib import SequenceMatcher
        
        best_match = None
        best_score = 0.0
        
        for track in tracks:
            track_artist = track.get('artist', {}).get('name', '') if isinstance(track.get('artist'), dict) else str(track.get('artist', ''))
            track_title = track.get('title', '') or track.get('name', '')
            
            # Calculate similarity scores
            artist_score = SequenceMatcher(None, target_artist.lower(), track_artist.lower()).ratio()
            title_score = SequenceMatcher(None, target_title.lower(), track_title.lower()).ratio()
            
            # Combined score with title weighted more heavily
            combined_score = (artist_score * 0.4) + (title_score * 0.6)
            
            if combined_score > best_score and combined_score > 0.7:  # Minimum threshold
                best_score = combined_score
                best_match = track
        
        return best_match
    
    def _extract_enrichment_data(self, track_data: Dict, analysis: Dict) -> Dict[str, Any]:
        """
        Extract and structure enrichment data from Musimap response
        """
        # Extract basic track info
        artist_info = track_data.get('artist', {})
        artist_name = artist_info.get('name', '') if isinstance(artist_info, dict) else str(artist_info)
        
        enriched = {
            'artist': artist_name,
            'title': track_data.get('title', '') or track_data.get('name', ''),
            'musimap_id': track_data.get('id'),
            'musimap_url': f"{self.config.base_url}/tracks/{track_data.get('id')}",
        }
        
        # Extract moods with weights
        moods = analysis.get('moods', [])
        if moods:
            mood_tags = []
            mood_weights = {}
            for mood in moods:
                if isinstance(mood, dict):
                    mood_name = mood.get('name', '')
                    mood_weight = mood.get('weight', 0)
                    if mood_name:
                        mood_tags.append(mood_name)
                        mood_weights[mood_name] = mood_weight
                else:
                    mood_tags.append(str(mood))
            
            enriched['musimap_moods'] = mood_tags
            enriched['mood_weights'] = mood_weights
            
            # Determine primary mood (highest weight)
            if mood_weights:
                primary_mood = max(mood_weights.items(), key=lambda x: x[1])[0]
                enriched['primary_mood'] = primary_mood
        
        # Extract genres with weights
        genres = analysis.get('genres', [])
        if genres:
            genre_tags = []
            genre_weights = {}
            for genre in genres:
                if isinstance(genre, dict):
                    genre_name = genre.get('name', '')
                    genre_weight = genre.get('weight', 0)
                    if genre_name:
                        genre_tags.append(genre_name)
                        genre_weights[genre_name] = genre_weight
                else:
                    genre_tags.append(str(genre))
            
            enriched['musimap_genres'] = genre_tags
            enriched['genre_weights'] = genre_weights
        
        # Extract situations
        situations = analysis.get('situations', [])
        if situations:
            situation_tags = []
            situation_weights = {}
            for situation in situations:
                if isinstance(situation, dict):
                    situation_name = situation.get('name', '')
                    situation_weight = situation.get('weight', 0)
                    if situation_name:
                        situation_tags.append(situation_name)
                        situation_weights[situation_name] = situation_weight
                else:
                    situation_tags.append(str(situation))
            
            enriched['musimap_situations'] = situation_tags
            enriched['situation_weights'] = situation_weights
        
        # Extract musical attributes
        attributes = analysis.get('attributes', {})
        if attributes:
            enriched['key'] = attributes.get('key')
            enriched['bpm'] = attributes.get('bpm')
            enriched['energy'] = attributes.get('energy')
            enriched['valence'] = attributes.get('valence')
            enriched['danceability'] = attributes.get('danceability')
            enriched['acousticness'] = attributes.get('acousticness')
            enriched['instrumentalness'] = attributes.get('instrumentalness')
            enriched['liveness'] = attributes.get('liveness')
            enriched['speechiness'] = attributes.get('speechiness')
        
        # Create simplified mood for compatibility
        if enriched.get('musimap_moods'):
            primary_moods = enriched['musimap_moods'][:3]  # Top 3 moods
            enriched['simplified_mood'] = ', '.join(primary_moods)
        else:
            enriched['simplified_mood'] = 'neutral'
        
        return enriched

def test_musimap_enricher():
    """Test the Musimap enricher with sample tracks"""
    
    # Note: You'll need to set up authentication first
    enricher = MusimapEnricher()
    
    # Test tracks
    test_tracks = [
        {'artist': 'The Beatles', 'title': 'Hey Jude'},
        {'artist': 'Queen', 'title': 'Bohemian Rhapsody'},
        {'artist': 'Interpol', 'title': 'Evil'}
    ]
    
    print("Testing Musimap enricher...")
    print("Note: Authentication required - set up client credentials first")
    
    for track in test_tracks:
        print(f"\nTesting: {track['artist']} - {track['title']}")
        result = enricher.enrich_track(track['artist'], track['title'])
        if result:
            print(f"✅ Success: Found moods: {result.get('musimap_moods', [])}")
            print(f"   Genres: {result.get('musimap_genres', [])}")
            print(f"   Primary mood: {result.get('primary_mood', 'Unknown')}")
        else:
            print("❌ Failed to enrich")

if __name__ == "__main__":
    test_musimap_enricher() 