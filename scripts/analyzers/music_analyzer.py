#!/usr/bin/env python3
"""
Real Music Analyzer - Hybrid Approach

Since Spotify audio features are restricted and Cyanite has limited coverage,
this creates a sophisticated real music analyzer using:

1. Spotify metadata (track info, artist genres, popularity)
2. Last.fm tags and scrobble data
3. Research-based mood classification
4. Artist/genre-based emotional profiling

This replaces the fake emotion analysis with real, data-driven insights.
"""

import pandas as pd
import requests
import os
import json
import time
from dotenv import load_dotenv
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RealMusicAnalyzer:
    """Comprehensive real music analyzer using multiple data sources"""
    
    def __init__(self):
        load_dotenv()
        
        # Initialize APIs
        self.spotify_client_id = os.getenv('SPOTIFY_CLIENT_ID')
        self.spotify_client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        self.lastfm_api_key = os.getenv('LASTFM_API_KEY')
        
        self.spotify_token = None
        self.cache = {}
        self.load_cache()
        
        # Statistics
        self.stats = {
            'tracks_analyzed': 0,
            'spotify_matches': 0,
            'lastfm_enriched': 0,
            'cache_hits': 0,
            'errors': 0
        }
        
        # Initialize Spotify access
        self._get_spotify_token()
    
    def load_cache(self):
        """Load analysis cache"""
        cache_file = "cache/real_music_analysis_cache.json"
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    self.cache = json.load(f)
                logger.info(f"Loaded {len(self.cache)} cached analyses")
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")
                self.cache = {}
        else:
            os.makedirs("cache", exist_ok=True)
    
    def save_cache(self):
        """Save analysis cache"""
        cache_file = "cache/real_music_analysis_cache.json"
        try:
            with open(cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
            logger.info(f"Saved {len(self.cache)} cached analyses")
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
    
    def _get_spotify_token(self):
        """Get Spotify access token"""
        try:
            auth_url = 'https://accounts.spotify.com/api/token'
            auth_data = {
                'grant_type': 'client_credentials',
                'client_id': self.spotify_client_id,
                'client_secret': self.spotify_client_secret
            }
            
            response = requests.post(auth_url, data=auth_data, timeout=10)
            if response.status_code == 200:
                self.spotify_token = response.json()['access_token']
                logger.info("✅ Spotify token obtained")
            else:
                logger.error(f"Failed to get Spotify token: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error getting Spotify token: {e}")
    
    def get_spotify_track_info(self, artist, track):
        """Get comprehensive Spotify track information"""
        if not self.spotify_token:
            return None
        
        try:
            headers = {'Authorization': f'Bearer {self.spotify_token}'}
            search_url = 'https://api.spotify.com/v1/search'
            search_params = {
                'q': f'artist:"{artist}" track:"{track}"',
                'type': 'track',
                'limit': 1
            }
            
            response = requests.get(search_url, headers=headers, params=search_params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data['tracks']['items']:
                    track_info = data['tracks']['items'][0]
                    
                    # Get artist details for additional info
                    artist_id = track_info['artists'][0]['id']
                    artist_response = requests.get(
                        f'https://api.spotify.com/v1/artists/{artist_id}',
                        headers=headers,
                        timeout=10
                    )
                    
                    artist_info = artist_response.json() if artist_response.status_code == 200 else {}
                    
                    return {
                        'spotify_id': track_info['id'],
                        'name': track_info['name'],
                        'artist_name': track_info['artists'][0]['name'],
                        'album_name': track_info['album']['name'],
                        'release_date': track_info['album']['release_date'],
                        'popularity': track_info['popularity'],
                        'explicit': track_info['explicit'],
                        'duration_ms': track_info['duration_ms'],
                        'artist_genres': artist_info.get('genres', []),
                        'artist_popularity': artist_info.get('popularity', 0),
                        'artist_followers': artist_info.get('followers', {}).get('total', 0)
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Spotify search error for {artist} - {track}: {e}")
            return None
    
    def get_lastfm_tags(self, artist, track):
        """Get Last.fm tags for additional mood/genre information"""
        if not self.lastfm_api_key:
            return []
        
        try:
            url = "http://ws.audioscrobbler.com/2.0/"
            params = {
                'method': 'track.getTopTags',
                'artist': artist,
                'track': track,
                'api_key': self.lastfm_api_key,
                'format': 'json'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'toptags' in data and 'tag' in data['toptags']:
                    tags = data['toptags']['tag']
                    # Return top tags with their counts
                    return [(tag['name'].lower(), int(tag['count'])) for tag in tags[:10]]
            
            return []
            
        except Exception as e:
            logger.error(f"Last.fm tags error for {artist} - {track}: {e}")
            return []
    
    def classify_mood_from_metadata(self, spotify_info, lastfm_tags):
        """Classify mood using available metadata and research-based rules"""
        
        mood_score = {
            'happy': 0,
            'sad': 0,
            'energetic': 0,
            'calm': 0,
            'angry': 0,
            'romantic': 0
        }
        
        if spotify_info:
            # Genre-based mood classification
            genres = [g.lower() for g in spotify_info.get('artist_genres', [])]
            
            for genre in genres:
                if any(word in genre for word in ['pop', 'dance', 'funk', 'disco', 'reggae']):
                    mood_score['happy'] += 3
                    mood_score['energetic'] += 2
                elif any(word in genre for word in ['blues', 'folk', 'indie', 'melancholy']):
                    mood_score['sad'] += 3
                    mood_score['calm'] += 1
                elif any(word in genre for word in ['rock', 'metal', 'punk', 'hardcore']):
                    mood_score['energetic'] += 3
                    mood_score['angry'] += 2
                elif any(word in genre for word in ['ambient', 'classical', 'new age', 'meditative']):
                    mood_score['calm'] += 3
                elif any(word in genre for word in ['r&b', 'soul', 'jazz', 'romantic']):
                    mood_score['romantic'] += 2
                    mood_score['calm'] += 1
            
            # Popularity-based adjustment
            popularity = spotify_info.get('popularity', 0)
            if popularity > 80:  # Very popular tracks tend to be upbeat
                mood_score['happy'] += 1
                mood_score['energetic'] += 1
            
            # Duration-based hints
            duration_ms = spotify_info.get('duration_ms', 0)
            duration_minutes = duration_ms / 60000
            if duration_minutes > 6:  # Long tracks often more serious/progressive
                mood_score['calm'] += 1
            elif duration_minutes < 2.5:  # Short tracks often punchy/energetic
                mood_score['energetic'] += 1
        
        # Last.fm tags analysis
        for tag, count in lastfm_tags:
            weight = min(count / 10, 3)  # Scale tag weight
            
            if any(word in tag for word in ['happy', 'upbeat', 'cheerful', 'positive', 'uplifting']):
                mood_score['happy'] += weight
            elif any(word in tag for word in ['sad', 'melancholy', 'depressing', 'dark', 'mournful']):
                mood_score['sad'] += weight
            elif any(word in tag for word in ['energetic', 'driving', 'intense', 'powerful', 'aggressive']):
                mood_score['energetic'] += weight
            elif any(word in tag for word in ['calm', 'peaceful', 'relaxing', 'mellow', 'chill']):
                mood_score['calm'] += weight
            elif any(word in tag for word in ['angry', 'rage', 'furious', 'violent', 'harsh']):
                mood_score['angry'] += weight
            elif any(word in tag for word in ['romantic', 'love', 'sensual', 'intimate', 'tender']):
                mood_score['romantic'] += weight
        
        # Find dominant mood
        if max(mood_score.values()) == 0:
            return 'unknown'
        
        return max(mood_score, key=mood_score.get)
    
    def classify_energy_level(self, spotify_info, lastfm_tags, mood):
        """Classify energy level based on available data"""
        
        energy_indicators = {
            'high': 0,
            'medium': 0,
            'low': 0
        }
        
        if spotify_info:
            genres = [g.lower() for g in spotify_info.get('artist_genres', [])]
            
            for genre in genres:
                if any(word in genre for word in ['dance', 'electronic', 'techno', 'house', 'punk', 'metal']):
                    energy_indicators['high'] += 3
                elif any(word in genre for word in ['pop', 'rock', 'funk', 'hip hop']):
                    energy_indicators['medium'] += 2
                elif any(word in genre for word in ['ambient', 'classical', 'folk', 'blues', 'jazz']):
                    energy_indicators['low'] += 2
        
        # Mood-based energy correlation
        if mood in ['energetic', 'angry']:
            energy_indicators['high'] += 2
        elif mood in ['happy', 'romantic']:
            energy_indicators['medium'] += 2
        elif mood in ['sad', 'calm']:
            energy_indicators['low'] += 2
        
        # Last.fm tags
        for tag, count in lastfm_tags:
            weight = min(count / 10, 2)
            
            if any(word in tag for word in ['energetic', 'driving', 'intense', 'fast', 'upbeat']):
                energy_indicators['high'] += weight
            elif any(word in tag for word in ['calm', 'slow', 'peaceful', 'mellow', 'quiet']):
                energy_indicators['low'] += weight
        
        if max(energy_indicators.values()) == 0:
            return 'medium'
        
        return max(energy_indicators, key=energy_indicators.get)
    
    def analyze_track(self, artist, track):
        """Comprehensive track analysis using real data sources"""
        
        # Check cache first
        cache_key = f"{artist.lower()}||{track.lower()}"
        if cache_key in self.cache:
            self.stats['cache_hits'] += 1
            return self.cache[cache_key]
        
        self.stats['tracks_analyzed'] += 1
        
        try:
            # Get Spotify information
            spotify_info = self.get_spotify_track_info(artist, track)
            if spotify_info:
                self.stats['spotify_matches'] += 1
            
            # Get Last.fm tags
            lastfm_tags = self.get_lastfm_tags(artist, track)
            if lastfm_tags:
                self.stats['lastfm_enriched'] += 1
            
            # Classify mood and energy
            mood = self.classify_mood_from_metadata(spotify_info, lastfm_tags)
            energy = self.classify_energy_level(spotify_info, lastfm_tags, mood)
            
            # Create comprehensive analysis result
            analysis = {
                'artist': artist,
                'track': track,
                'spotify_matched': spotify_info is not None,
                'mood_primary': mood,
                'energy_level': energy,
                'analysis_method': 'metadata_hybrid',
                'analyzed_at': datetime.now().isoformat(),
                'lastfm_tags': [tag for tag, _ in lastfm_tags[:5]],  # Top 5 tags
                'confidence': self._calculate_confidence(spotify_info, lastfm_tags)
            }
            
            # Add Spotify metadata if available
            if spotify_info:
                analysis.update({
                    'spotify_id': spotify_info['spotify_id'],
                    'matched_name': spotify_info['name'],
                    'matched_artist': spotify_info['artist_name'],
                    'popularity': spotify_info['popularity'],
                    'genres': spotify_info['artist_genres'],
                    'release_year': spotify_info['release_date'][:4] if spotify_info['release_date'] else None
                })
            
            # Cache and return
            self.cache[cache_key] = analysis
            return analysis
            
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Analysis error for {artist} - {track}: {e}")
            return {
                'artist': artist,
                'track': track,
                'mood_primary': 'unknown',
                'energy_level': 'medium',
                'analysis_method': 'error',
                'error': str(e),
                'analyzed_at': datetime.now().isoformat(),
                'confidence': 'low'
            }
    
    def _calculate_confidence(self, spotify_info, lastfm_tags):
        """Calculate confidence level of the analysis"""
        score = 0
        
        if spotify_info:
            score += 3
            if spotify_info.get('artist_genres'):
                score += 2
            if spotify_info.get('popularity', 0) > 50:
                score += 1
        
        if lastfm_tags:
            score += min(len(lastfm_tags), 3)
        
        if score >= 6:
            return 'high'
        elif score >= 3:
            return 'medium'
        else:
            return 'low'
    
    def enrich_dataset(self, df, artist_col='artist', track_col='track', max_tracks=None, delay=0.3):
        """Enrich dataset with real music analysis"""
        
        logger.info(f"🎵 Starting real music analysis for {len(df)} tracks...")
        
        if max_tracks:
            df = df.head(max_tracks)
            logger.info(f"📊 Processing limited dataset of {max_tracks} tracks")
        
        enriched_data = []
        
        for idx, row in df.iterrows():
            artist = str(row[artist_col])
            track = str(row[track_col])
            
            if idx % 50 == 0:
                logger.info(f"📈 Processing track {idx + 1}/{len(df)}: {artist} - {track}")
                self._log_progress()
            
            # Analyze track
            analysis = self.analyze_track(artist, track)
            
            # Combine with original data
            enriched_row = row.to_dict()
            enriched_row.update(analysis)
            enriched_data.append(enriched_row)
            
            # Rate limiting
            if delay > 0:
                time.sleep(delay)
            
            # Save progress
            if idx % 100 == 0 and idx > 0:
                self.save_cache()
        
        # Final save
        self.save_cache()
        
        enriched_df = pd.DataFrame(enriched_data)
        self._log_final_stats(len(df))
        
        return enriched_df
    
    def _log_progress(self):
        """Log current progress"""
        stats = self.stats
        total = stats['tracks_analyzed']
        if total > 0:
            spotify_rate = (stats['spotify_matches'] / total) * 100
            lastfm_rate = (stats['lastfm_enriched'] / total) * 100
            logger.info(f"   📊 {spotify_rate:.1f}% Spotify matched, {lastfm_rate:.1f}% Last.fm enriched")
    
    def _log_final_stats(self, total_tracks):
        """Log comprehensive final statistics"""
        stats = self.stats
        
        logger.info(f"🎉 Real music analysis complete!")
        logger.info(f"📊 Final Statistics:")
        logger.info(f"   - Total tracks: {total_tracks}")
        logger.info(f"   - Tracks analyzed: {stats['tracks_analyzed']}")
        logger.info(f"   - Spotify matches: {stats['spotify_matches']}")
        logger.info(f"   - Last.fm enriched: {stats['lastfm_enriched']}")
        logger.info(f"   - Cache hits: {stats['cache_hits']}")
        logger.info(f"   - Errors: {stats['errors']}")
        
        if stats['tracks_analyzed'] > 0:
            spotify_rate = (stats['spotify_matches'] / stats['tracks_analyzed']) * 100
            lastfm_rate = (stats['lastfm_enriched'] / stats['tracks_analyzed']) * 100
            logger.info(f"   - Spotify match rate: {spotify_rate:.1f}%")
            logger.info(f"   - Last.fm enrichment rate: {lastfm_rate:.1f}%")


def main():
    """Test the real music analyzer"""
    
    analyzer = RealMusicAnalyzer()
    
    # Load user data
    logger.info("Loading user's scrobbles...")
    df = pd.read_csv('data/zdjuna_scrobbles.csv')
    
    # Test with sample
    test_df = df.head(25)
    logger.info(f"Testing with {len(test_df)} tracks...")
    
    # Analyze
    enriched_df = analyzer.enrich_dataset(test_df, delay=0.5)
    
    # Save results
    output_file = f'data/zdjuna_real_analysis_test_{len(test_df)}_tracks.csv'
    enriched_df.to_csv(output_file, index=False)
    logger.info(f"💾 Results saved to: {output_file}")
    
    # Show sample results
    logger.info("\n🎵 Sample analysis results:")
    for _, row in enriched_df.head(5).iterrows():
        logger.info(f"   {row['artist']} - {row['track']}")
        logger.info(f"   → Mood: {row['mood_primary']}, Energy: {row['energy_level']}")
        logger.info(f"   → Confidence: {row['confidence']}, Method: {row['analysis_method']}")
        if row.get('genres'):
            logger.info(f"   → Genres: {row['genres'][:3]}")
        if row.get('lastfm_tags'):
            logger.info(f"   → Tags: {row['lastfm_tags']}")
        logger.info("")


if __name__ == "__main__":
    main()
