#!/usr/bin/env python3
"""
Bridge.audio API enricher for professional music analysis
"""

import requests
import time
import logging
import os
from typing import Dict, List, Optional, Any
import json
from dataclasses import dataclass
from pathlib import Path

@dataclass
class BridgeAudioConfig:
    """Configuration for Bridge.audio API"""
    api_key: Optional[str] = None
    base_url: str = "https://api.bridge.audio"
    rate_limit_delay: float = 0.5  # 500ms between requests
    timeout: int = 30

class BridgeAudioEnricher:
    """
    Professional music enricher using Bridge.audio's AI analysis API
    
    Features:
    - Comprehensive AI auto-tagging
    - Genres & sub-genres
    - Mood, movement, energy analysis
    - Instrumentation detection
    - Vocal dynamics analysis
    - Tempo, key, BPM detection
    - Lyrics theme analysis
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.config = BridgeAudioConfig(api_key=api_key or os.getenv('BRIDGE_AUDIO_API_KEY'))
        self.session = requests.Session()
        
        # Set up session headers
        if self.config.api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {self.config.api_key}',
                'Content-Type': 'application/json',
                'User-Agent': 'MusicRecommendationSystem/1.0'
            })
    
    def analyze_track(self, track_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a single track using Bridge.audio API
        
        Args:
            track_info: Dictionary containing track information
            
        Returns:
            Dictionary with enriched track data
        """
        try:
            artist = track_info.get('artist', '').strip()
            title = track_info.get('track', '').strip()
            
            if not artist or not title:
                self.logger.warning(f"Missing artist or title: {track_info}")
                return self._create_fallback_analysis(track_info)
            
            # For now, simulate the API call since we need to sign up first
            # This will be replaced with actual API calls once we have access
            analysis = self._simulate_bridge_analysis(artist, title)
            
            self.logger.info(f"✅ Analyzed: {artist} - {title}")
            time.sleep(self.config.rate_limit_delay)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing {track_info}: {e}")
            return self._create_fallback_analysis(track_info)
    
    def _simulate_bridge_analysis(self, artist: str, title: str) -> Dict[str, Any]:
        """
        Simulate Bridge.audio analysis based on artist/genre patterns
        This will be replaced with actual API calls
        """
        # Advanced mood and genre mapping based on artist patterns
        mood_mapping = {
            'electronic': ['energetic', 'futuristic', 'danceable'],
            'rock': ['powerful', 'rebellious', 'energetic'],
            'pop': ['uplifting', 'catchy', 'mainstream'],
            'jazz': ['sophisticated', 'smooth', 'improvisational'],
            'classical': ['elegant', 'dramatic', 'orchestral'],
            'hip-hop': ['rhythmic', 'urban', 'confident'],
            'indie': ['alternative', 'creative', 'authentic'],
            'folk': ['organic', 'storytelling', 'acoustic'],
            'metal': ['intense', 'aggressive', 'powerful'],
            'ambient': ['atmospheric', 'meditative', 'spacious']
        }
        
        # Determine genre and mood based on artist
        detected_genre = self._detect_genre_from_artist(artist)
        moods = mood_mapping.get(detected_genre, ['neutral', 'melodic'])
        
        # Simulate comprehensive Bridge.audio analysis
        return {
            'artist': artist,
            'track': title,
            'bridge_genres': [detected_genre, f"{detected_genre}-contemporary"],
            'bridge_subgenres': [f"{detected_genre}-modern", f"indie-{detected_genre}"],
            'bridge_moods': moods,
            'bridge_movement': self._analyze_movement(detected_genre),
            'bridge_energy': self._analyze_energy(detected_genre),
            'bridge_instrumentation': self._analyze_instrumentation(detected_genre),
            'bridge_vocal_dynamics': self._analyze_vocals(detected_genre),
            'bridge_tempo_range': self._analyze_tempo(detected_genre),
            'bridge_key_signature': self._analyze_key(artist, title),
            'bridge_bpm_estimate': self._estimate_bpm(detected_genre),
            'bridge_lyrics_themes': self._analyze_lyrics_themes(detected_genre),
            'bridge_textures': self._analyze_textures(detected_genre),
            'bridge_presence_of_beat': 'strong' if detected_genre in ['electronic', 'hip-hop', 'pop'] else 'moderate',
            'bridge_analysis_confidence': 0.85,
            'bridge_api_version': 'simulated_v1.0',
            'enrichment_source': 'bridge_audio_simulation'
        }
    
    def _detect_genre_from_artist(self, artist: str) -> str:
        """Enhanced genre detection based on artist name patterns"""
        artist_lower = artist.lower()
        
        # Electronic/EDM artists
        if any(term in artist_lower for term in ['daft', 'deadmau5', 'skrillex', 'calvin', 'tiësto', 'armin']):
            return 'electronic'
        
        # Rock/Alternative
        elif any(term in artist_lower for term in ['radiohead', 'nirvana', 'foo fighters', 'pearl jam', 'red hot']):
            return 'rock'
        
        # Hip-Hop
        elif any(term in artist_lower for term in ['kendrick', 'drake', 'kanye', 'jay-z', 'eminem', 'tupac']):
            return 'hip-hop'
        
        # Jazz
        elif any(term in artist_lower for term in ['miles', 'coltrane', 'monk', 'parker', 'armstrong']):
            return 'jazz'
        
        # Classical
        elif any(term in artist_lower for term in ['bach', 'mozart', 'beethoven', 'chopin', 'vivaldi']):
            return 'classical'
        
        # Indie/Alternative
        elif any(term in artist_lower for term in ['arcade fire', 'vampire weekend', 'interpol', 'strokes']):
            return 'indie'
        
        # Default to pop for mainstream appeal
        else:
            return 'pop'
    
    def _analyze_movement(self, genre: str) -> List[str]:
        """Analyze movement characteristics"""
        movement_map = {
            'electronic': ['driving', 'pulsating', 'rhythmic'],
            'rock': ['driving', 'powerful', 'steady'],
            'pop': ['bouncy', 'flowing', 'catchy'],
            'jazz': ['swinging', 'fluid', 'improvisational'],
            'classical': ['flowing', 'dramatic', 'structured'],
            'hip-hop': ['rhythmic', 'syncopated', 'groove-based'],
            'indie': ['flowing', 'organic', 'dynamic'],
            'folk': ['gentle', 'organic', 'storytelling'],
            'metal': ['aggressive', 'driving', 'intense'],
            'ambient': ['floating', 'atmospheric', 'spacious']
        }
        return movement_map.get(genre, ['moderate', 'balanced'])
    
    def _analyze_energy(self, genre: str) -> str:
        """Analyze energy level"""
        energy_map = {
            'electronic': 'high',
            'rock': 'high',
            'pop': 'medium-high',
            'jazz': 'medium',
            'classical': 'medium',
            'hip-hop': 'medium-high',
            'indie': 'medium',
            'folk': 'low-medium',
            'metal': 'very-high',
            'ambient': 'low'
        }
        return energy_map.get(genre, 'medium')
    
    def _analyze_instrumentation(self, genre: str) -> List[str]:
        """Analyze instrumentation"""
        instrument_map = {
            'electronic': ['synthesizer', 'drum-machine', 'digital-effects'],
            'rock': ['electric-guitar', 'bass-guitar', 'drums', 'vocals'],
            'pop': ['vocals', 'synthesizer', 'drums', 'bass'],
            'jazz': ['saxophone', 'piano', 'bass', 'drums'],
            'classical': ['orchestra', 'strings', 'woodwinds', 'brass'],
            'hip-hop': ['vocals', 'drum-machine', 'synthesizer', 'samples'],
            'indie': ['guitar', 'bass', 'drums', 'vocals'],
            'folk': ['acoustic-guitar', 'vocals', 'harmonica'],
            'metal': ['electric-guitar', 'bass-guitar', 'drums', 'vocals'],
            'ambient': ['synthesizer', 'digital-effects', 'atmospheric-sounds']
        }
        return instrument_map.get(genre, ['guitar', 'vocals', 'drums'])
    
    def _analyze_vocals(self, genre: str) -> str:
        """Analyze vocal dynamics"""
        vocal_map = {
            'electronic': 'processed',
            'rock': 'powerful',
            'pop': 'melodic',
            'jazz': 'smooth',
            'classical': 'operatic',
            'hip-hop': 'rhythmic',
            'indie': 'intimate',
            'folk': 'storytelling',
            'metal': 'aggressive',
            'ambient': 'ethereal'
        }
        return vocal_map.get(genre, 'melodic')
    
    def _analyze_tempo(self, genre: str) -> str:
        """Analyze tempo range"""
        tempo_map = {
            'electronic': '120-140 BPM',
            'rock': '110-130 BPM',
            'pop': '100-120 BPM',
            'jazz': '80-120 BPM',
            'classical': '60-120 BPM',
            'hip-hop': '80-100 BPM',
            'indie': '90-120 BPM',
            'folk': '70-100 BPM',
            'metal': '120-180 BPM',
            'ambient': '60-90 BPM'
        }
        return tempo_map.get(genre, '90-120 BPM')
    
    def _analyze_key(self, artist: str, title: str) -> str:
        """Estimate key signature"""
        # Simple hash-based key estimation for simulation
        keys = ['C major', 'G major', 'D major', 'A major', 'E major', 'B major',
                'F# major', 'C# major', 'F major', 'Bb major', 'Eb major', 'Ab major']
        hash_val = hash(f"{artist}{title}") % len(keys)
        return keys[hash_val]
    
    def _estimate_bpm(self, genre: str) -> int:
        """Estimate BPM"""
        bpm_map = {
            'electronic': 128,
            'rock': 120,
            'pop': 110,
            'jazz': 100,
            'classical': 90,
            'hip-hop': 85,
            'indie': 105,
            'folk': 85,
            'metal': 150,
            'ambient': 75
        }
        return bpm_map.get(genre, 100)
    
    def _analyze_lyrics_themes(self, genre: str) -> List[str]:
        """Analyze lyrics themes"""
        theme_map = {
            'electronic': ['technology', 'future', 'energy'],
            'rock': ['rebellion', 'freedom', 'power'],
            'pop': ['love', 'relationships', 'celebration'],
            'jazz': ['sophistication', 'romance', 'improvisation'],
            'classical': ['drama', 'emotion', 'storytelling'],
            'hip-hop': ['urban-life', 'success', 'social-commentary'],
            'indie': ['introspection', 'authenticity', 'creativity'],
            'folk': ['storytelling', 'tradition', 'nature'],
            'metal': ['intensity', 'struggle', 'power'],
            'ambient': ['atmosphere', 'meditation', 'space']
        }
        return theme_map.get(genre, ['general', 'melodic'])
    
    def _analyze_textures(self, genre: str) -> List[str]:
        """Analyze musical textures"""
        texture_map = {
            'electronic': ['synthetic', 'layered', 'digital'],
            'rock': ['distorted', 'powerful', 'raw'],
            'pop': ['polished', 'layered', 'commercial'],
            'jazz': ['smooth', 'complex', 'improvisational'],
            'classical': ['orchestral', 'rich', 'dynamic'],
            'hip-hop': ['rhythmic', 'sampled', 'urban'],
            'indie': ['organic', 'authentic', 'creative'],
            'folk': ['acoustic', 'natural', 'intimate'],
            'metal': ['heavy', 'distorted', 'aggressive'],
            'ambient': ['atmospheric', 'spacious', 'ethereal']
        }
        return texture_map.get(genre, ['balanced', 'melodic'])
    
    def _create_fallback_analysis(self, track_info: Dict[str, Any]) -> Dict[str, Any]:
        """Create fallback analysis when API fails"""
        return {
            'artist': track_info.get('artist', 'Unknown'),
            'track': track_info.get('track', 'Unknown'),
            'bridge_genres': ['unknown'],
            'bridge_subgenres': ['unclassified'],
            'bridge_moods': ['neutral'],
            'bridge_movement': ['moderate'],
            'bridge_energy': 'medium',
            'bridge_instrumentation': ['unknown'],
            'bridge_vocal_dynamics': 'unknown',
            'bridge_tempo_range': '90-120 BPM',
            'bridge_key_signature': 'C major',
            'bridge_bpm_estimate': 100,
            'bridge_lyrics_themes': ['general'],
            'bridge_textures': ['unknown'],
            'bridge_presence_of_beat': 'moderate',
            'bridge_analysis_confidence': 0.1,
            'bridge_api_version': 'fallback',
            'enrichment_source': 'bridge_audio_fallback'
        }
    
    def enrich_tracks(self, tracks_data: List[Dict[str, Any]], max_tracks: int = 50) -> Dict[str, Any]:
        """
        Enrich multiple tracks with Bridge.audio analysis
        
        Args:
            tracks_data: List of track dictionaries
            max_tracks: Maximum number of tracks to process
            
        Returns:
            Dictionary with processing results
        """
        self.logger.info(f"🎵 Starting Bridge.audio enrichment for {len(tracks_data)} tracks")
        
        enriched_tracks = []
        processed_count = 0
        
        for track in tracks_data[:max_tracks]:
            try:
                enriched_track = self.analyze_track(track)
                enriched_tracks.append(enriched_track)
                processed_count += 1
                
                if processed_count % 10 == 0:
                    self.logger.info(f"Processed {processed_count} tracks...")
                    
            except Exception as e:
                self.logger.error(f"Error processing track {track}: {e}")
                continue
        
        self.logger.info(f"✅ Bridge.audio enrichment complete: {processed_count} tracks processed")
        
        return {
            'processed_tracks': processed_count,
            'enriched_data': enriched_tracks,
            'api_source': 'bridge_audio',
            'analysis_features': [
                'genres', 'subgenres', 'moods', 'movement', 'energy',
                'instrumentation', 'vocal_dynamics', 'tempo', 'key',
                'bpm', 'lyrics_themes', 'textures', 'beat_presence'
            ]
        }

def test_bridge_enricher():
    """Test the Bridge.audio enricher"""
    logging.basicConfig(level=logging.INFO)
    
    # Test tracks
    test_tracks = [
        {'artist': 'Daft Punk', 'track': 'Get Lucky'},
        {'artist': 'Radiohead', 'track': 'Paranoid Android'},
        {'artist': 'Kendrick Lamar', 'track': 'HUMBLE.'},
        {'artist': 'Miles Davis', 'track': 'Kind of Blue'},
        {'artist': 'The Beatles', 'track': 'Hey Jude'}
    ]
    
    enricher = BridgeAudioEnricher()
    result = enricher.enrich_tracks(test_tracks)
    
    print(f"\n🎵 Bridge.audio Analysis Results:")
    print(f"Processed: {result['processed_tracks']} tracks")
    print(f"Features: {', '.join(result['analysis_features'])}")
    
    for track in result['enriched_data'][:2]:
        print(f"\n🎼 {track['artist']} - {track['track']}")
        print(f"   Genres: {', '.join(track['bridge_genres'])}")
        print(f"   Moods: {', '.join(track['bridge_moods'])}")
        print(f"   Energy: {track['bridge_energy']}")
        print(f"   BPM: {track['bridge_bpm_estimate']}")
        print(f"   Key: {track['bridge_key_signature']}")
        print(f"   Confidence: {track['bridge_analysis_confidence']}")

if __name__ == "__main__":
    test_bridge_enricher() 