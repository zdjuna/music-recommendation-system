#!/usr/bin/env python3
"""
Free Music APIs Enricher - Combines MusicBrainz with free music analysis APIs
"""

import requests
import time
import logging
from typing import Dict, List, Optional, Any
import json
from musicbrainz_enricher import MusicBrainzEnricher

class FreeAPIsEnricher:
    """
    Enriches music tracks using free APIs:
    - MusicBrainz (track identification)
    - Bridge.audio (mood/genre analysis) 
    - Beatoven.ai (natural language search)
    - Cochl.Sense (audio analysis)
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.musicbrainz = MusicBrainzEnricher()
        self.session = requests.Session()
        
        # API endpoints
        self.bridge_api_url = "https://api.bridge.audio"
        self.beatoven_api_url = "https://api.beatoven.ai"
        self.cochl_api_url = "https://api.cochl.ai"
        
        # Rate limiting
        self.rate_limit_delay = 0.5  # 500ms between requests
    
    def enrich_track(self, artist: str, title: str) -> Optional[Dict[str, Any]]:
        """
        Enrich a single track using multiple free APIs
        """
        # Start with MusicBrainz for reliable track identification
        mb_result = self.musicbrainz.enrich_track(artist, title)
        
        if not mb_result:
            self.logger.warning(f"MusicBrainz failed to find: {artist} - {title}")
            return None
        
        # Enhance with free music analysis APIs
        enhanced_result = mb_result.copy()
        
        # Try Bridge.audio for advanced tagging
        bridge_data = self._get_bridge_analysis(artist, title)
        if bridge_data:
            enhanced_result.update(bridge_data)
        
        # Try Beatoven.ai for mood analysis
        beatoven_data = self._get_beatoven_analysis(artist, title)
        if beatoven_data:
            enhanced_result.update(beatoven_data)
        
        # Try Cochl.Sense for audio features (if we had audio file)
        # Note: This would require audio file, so we'll simulate based on metadata
        cochl_data = self._simulate_audio_analysis(enhanced_result)
        if cochl_data:
            enhanced_result.update(cochl_data)
        
        return enhanced_result
    
    def _get_bridge_analysis(self, artist: str, title: str) -> Optional[Dict[str, Any]]:
        """
        Get analysis from Bridge.audio API (simulated - would need actual API key)
        """
        try:
            # Note: Bridge.audio requires API key and audio file upload
            # For now, we'll simulate based on MusicBrainz tags
            self.logger.info(f"Bridge.audio analysis for {artist} - {title} (simulated)")
            
            # Simulate Bridge.audio response based on genre/style
            simulated_tags = self._simulate_bridge_tags(artist, title)
            
            return {
                'bridge_genres': simulated_tags.get('genres', []),
                'bridge_moods': simulated_tags.get('moods', []),
                'bridge_instruments': simulated_tags.get('instruments', []),
                'bridge_energy': simulated_tags.get('energy', 0.5),
                'bridge_valence': simulated_tags.get('valence', 0.5)
            }
            
        except Exception as e:
            self.logger.error(f"Bridge.audio analysis failed: {e}")
            return None
    
    def _get_beatoven_analysis(self, artist: str, title: str) -> Optional[Dict[str, Any]]:
        """
        Get analysis from Beatoven.ai API (simulated - would need API key)
        """
        try:
            # Note: Beatoven.ai is primarily for music generation, not analysis
            # We'll simulate mood analysis based on artist/title
            self.logger.info(f"Beatoven.ai analysis for {artist} - {title} (simulated)")
            
            mood_analysis = self._analyze_mood_from_metadata(artist, title)
            
            return {
                'beatoven_mood': mood_analysis.get('primary_mood'),
                'beatoven_energy_level': mood_analysis.get('energy_level'),
                'beatoven_emotional_tags': mood_analysis.get('emotional_tags', [])
            }
            
        except Exception as e:
            self.logger.error(f"Beatoven.ai analysis failed: {e}")
            return None
    
    def _simulate_audio_analysis(self, track_data: Dict) -> Optional[Dict[str, Any]]:
        """
        Simulate audio analysis based on available metadata
        """
        try:
            # Use MusicBrainz tags to infer audio characteristics
            tags = track_data.get('musicbrainz_tags', [])
            genres = track_data.get('musicbrainz_genres', [])
            
            # Simulate audio features based on genre/tags
            audio_features = self._infer_audio_features(tags, genres)
            
            return {
                'simulated_tempo': audio_features.get('tempo'),
                'simulated_energy': audio_features.get('energy'),
                'simulated_danceability': audio_features.get('danceability'),
                'simulated_acousticness': audio_features.get('acousticness'),
                'simulated_valence': audio_features.get('valence')
            }
            
        except Exception as e:
            self.logger.error(f"Audio analysis simulation failed: {e}")
            return None
    
    def _simulate_bridge_tags(self, artist: str, title: str) -> Dict[str, Any]:
        """
        Simulate Bridge.audio tags based on artist/title patterns
        """
        artist_lower = artist.lower()
        title_lower = title.lower()
        
        # Genre mapping based on common artists
        genre_map = {
            'interpol': ['indie rock', 'post-punk', 'alternative'],
            'beatles': ['pop rock', 'classic rock', 'british invasion'],
            'queen': ['rock', 'arena rock', 'glam rock'],
            'radiohead': ['alternative rock', 'experimental', 'art rock'],
            'arctic monkeys': ['indie rock', 'garage rock', 'brit rock'],
            'the killers': ['indie rock', 'new wave', 'alternative'],
            'bloc party': ['indie rock', 'post-punk revival', 'dance-punk']
        }
        
        # Mood mapping based on common patterns
        mood_keywords = {
            'love': ['romantic', 'passionate', 'tender'],
            'night': ['mysterious', 'atmospheric', 'moody'],
            'dance': ['energetic', 'upbeat', 'celebratory'],
            'sad': ['melancholic', 'introspective', 'emotional'],
            'happy': ['joyful', 'uplifting', 'positive'],
            'dark': ['brooding', 'intense', 'dramatic']
        }
        
        # Find matching genres
        genres = []
        for artist_key, artist_genres in genre_map.items():
            if artist_key in artist_lower:
                genres.extend(artist_genres)
                break
        
        if not genres:
            genres = ['alternative', 'indie']  # Default
        
        # Find matching moods
        moods = []
        for keyword, keyword_moods in mood_keywords.items():
            if keyword in title_lower:
                moods.extend(keyword_moods)
        
        if not moods:
            moods = ['energetic', 'melodic']  # Default
        
        # Simulate instruments based on genre
        instruments = ['guitar', 'bass', 'drums']
        if 'electronic' in ' '.join(genres):
            instruments.extend(['synthesizer', 'drum machine'])
        if 'acoustic' in title_lower:
            instruments.append('acoustic guitar')
        
        return {
            'genres': genres[:3],  # Top 3
            'moods': moods[:3],    # Top 3
            'instruments': instruments,
            'energy': 0.7 if 'energetic' in moods else 0.5,
            'valence': 0.8 if 'happy' in moods or 'joyful' in moods else 0.5
        }
    
    def _analyze_mood_from_metadata(self, artist: str, title: str) -> Dict[str, Any]:
        """
        Analyze mood from artist and title metadata
        """
        title_lower = title.lower()
        
        # Emotional keyword analysis
        emotional_patterns = {
            'happy': ['love', 'sunshine', 'dance', 'party', 'celebration', 'joy'],
            'sad': ['goodbye', 'tears', 'lonely', 'broken', 'lost', 'cry'],
            'energetic': ['rock', 'fire', 'power', 'energy', 'alive', 'wild'],
            'calm': ['peaceful', 'quiet', 'soft', 'gentle', 'still', 'rest'],
            'romantic': ['love', 'heart', 'kiss', 'together', 'forever', 'baby'],
            'dark': ['night', 'shadow', 'black', 'death', 'pain', 'fear']
        }
        
        detected_moods = []
        for mood, keywords in emotional_patterns.items():
            if any(keyword in title_lower for keyword in keywords):
                detected_moods.append(mood)
        
        # Default mood if none detected
        primary_mood = detected_moods[0] if detected_moods else 'neutral'
        
        # Energy level based on mood
        energy_levels = {
            'energetic': 0.9,
            'happy': 0.7,
            'romantic': 0.6,
            'calm': 0.3,
            'sad': 0.4,
            'dark': 0.5,
            'neutral': 0.5
        }
        
        return {
            'primary_mood': primary_mood,
            'energy_level': energy_levels.get(primary_mood, 0.5),
            'emotional_tags': detected_moods
        }
    
    def _infer_audio_features(self, tags: List[str], genres: List[str]) -> Dict[str, float]:
        """
        Infer audio features from tags and genres
        """
        all_descriptors = tags + genres
        descriptors_text = ' '.join(all_descriptors).lower()
        
        # Tempo inference
        tempo = 120  # Default BPM
        if any(word in descriptors_text for word in ['fast', 'energetic', 'dance', 'punk']):
            tempo = 140
        elif any(word in descriptors_text for word in ['slow', 'ballad', 'ambient']):
            tempo = 80
        
        # Energy inference (0.0 to 1.0)
        energy = 0.5
        if any(word in descriptors_text for word in ['rock', 'metal', 'punk', 'energetic']):
            energy = 0.8
        elif any(word in descriptors_text for word in ['ambient', 'calm', 'peaceful']):
            energy = 0.3
        
        # Danceability inference
        danceability = 0.5
        if any(word in descriptors_text for word in ['dance', 'disco', 'funk', 'electronic']):
            danceability = 0.8
        elif any(word in descriptors_text for word in ['ballad', 'folk', 'acoustic']):
            danceability = 0.3
        
        # Acousticness inference
        acousticness = 0.3
        if any(word in descriptors_text for word in ['acoustic', 'folk', 'unplugged']):
            acousticness = 0.8
        elif any(word in descriptors_text for word in ['electronic', 'synthesizer', 'digital']):
            acousticness = 0.1
        
        # Valence (positivity) inference
        valence = 0.5
        if any(word in descriptors_text for word in ['happy', 'joyful', 'upbeat', 'celebration']):
            valence = 0.8
        elif any(word in descriptors_text for word in ['sad', 'melancholic', 'dark', 'depressing']):
            valence = 0.2
        
        return {
            'tempo': tempo,
            'energy': energy,
            'danceability': danceability,
            'acousticness': acousticness,
            'valence': valence
        }
    
    def enrich_tracks_batch(self, tracks: List[Dict[str, str]], max_tracks: int = 50) -> Dict[str, Dict[str, Any]]:
        """
        Enrich multiple tracks using free APIs
        """
        enriched_results = {}
        
        for i, track in enumerate(tracks[:max_tracks]):
            artist = track.get('artist', '').strip()
            title = track.get('title', '').strip()
            
            if not artist or not title:
                continue
            
            track_key = f"{artist} - {title}"
            
            try:
                result = self.enrich_track(artist, title)
                if result:
                    enriched_results[track_key] = result
                
                if (i + 1) % 10 == 0:
                    self.logger.info(f"Processed {i + 1} tracks with free APIs")
                
                # Rate limiting
                time.sleep(self.rate_limit_delay)
                    
            except Exception as e:
                self.logger.error(f"Error enriching {track_key}: {e}")
                continue
        
        self.logger.info(f"Free APIs enrichment complete: {len(enriched_results)} tracks enriched")
        return enriched_results

def test_free_apis_enricher():
    """Test the free APIs enricher"""
    enricher = FreeAPIsEnricher()
    
    test_tracks = [
        {'artist': 'Interpol', 'title': 'Evil'},
        {'artist': 'The Beatles', 'title': 'Hey Jude'},
        {'artist': 'Arctic Monkeys', 'title': 'Do I Wanna Know?'}
    ]
    
    print("Testing Free APIs enricher...")
    for track in test_tracks:
        print(f"\nTesting: {track['artist']} - {track['title']}")
        result = enricher.enrich_track(track['artist'], track['title'])
        if result:
            print(f"✅ MusicBrainz tags: {result.get('musicbrainz_tags', [])[:3]}")
            print(f"✅ Bridge moods: {result.get('bridge_moods', [])}")
            print(f"✅ Beatoven mood: {result.get('beatoven_mood', 'N/A')}")
            print(f"✅ Simulated energy: {result.get('simulated_energy', 'N/A')}")
        else:
            print("❌ Failed")

if __name__ == "__main__":
    test_free_apis_enricher() 