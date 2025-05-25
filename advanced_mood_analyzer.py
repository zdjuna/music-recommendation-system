#!/usr/bin/env python3
"""
Advanced Mood Analyzer - Sophisticated music mood and style analysis
Goes far beyond basic "rock/pop" tags to provide nuanced emotional and stylistic insights
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any
import re
from collections import defaultdict
import logging

class AdvancedMoodAnalyzer:
    """
    Advanced mood analysis that provides sophisticated emotional and stylistic insights
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Sophisticated mood mappings based on musical characteristics
        self.artist_mood_profiles = {
            # Post-punk/Indie sophistication
            'interpol': {
                'primary_moods': ['brooding', 'sophisticated', 'melancholic', 'atmospheric'],
                'energy_profile': 'controlled intensity',
                'emotional_depth': 'introspective',
                'sonic_characteristics': ['angular guitars', 'driving bass', 'precise drums'],
                'listening_contexts': ['late night', 'contemplative', 'urban walking'],
                'sophistication_level': 'high'
            },
            'arctic monkeys': {
                'primary_moods': ['witty', 'energetic', 'observational', 'cheeky'],
                'energy_profile': 'dynamic range',
                'emotional_depth': 'clever storytelling',
                'sonic_characteristics': ['tight rhythms', 'melodic hooks', 'lyrical wordplay'],
                'listening_contexts': ['social gatherings', 'driving', 'getting ready'],
                'sophistication_level': 'medium-high'
            },
            'radiohead': {
                'primary_moods': ['experimental', 'anxious', 'transcendent', 'complex'],
                'energy_profile': 'variable intensity',
                'emotional_depth': 'existential',
                'sonic_characteristics': ['electronic textures', 'unconventional structures', 'layered soundscapes'],
                'listening_contexts': ['deep focus', 'emotional processing', 'artistic appreciation'],
                'sophistication_level': 'very high'
            },
            'the strokes': {
                'primary_moods': ['nostalgic', 'effortless', 'cool', 'garage-rock revival'],
                'energy_profile': 'laid-back intensity',
                'emotional_depth': 'casual sophistication',
                'sonic_characteristics': ['lo-fi production', 'catchy riffs', 'vintage sound'],
                'listening_contexts': ['casual hangouts', 'nostalgic moments', 'indie discovery'],
                'sophistication_level': 'medium'
            },
            'bloc party': {
                'primary_moods': ['urgent', 'danceable', 'political', 'rhythmic'],
                'energy_profile': 'high energy',
                'emotional_depth': 'socially conscious',
                'sonic_characteristics': ['angular rhythms', 'dance-punk fusion', 'sharp guitars'],
                'listening_contexts': ['dancing', 'workout', 'political awareness'],
                'sophistication_level': 'medium-high'
            },
            'the killers': {
                'primary_moods': ['anthemic', 'dramatic', 'americana-tinged', 'theatrical'],
                'energy_profile': 'stadium-sized',
                'emotional_depth': 'populist emotion',
                'sonic_characteristics': ['big choruses', 'synth elements', 'desert rock'],
                'listening_contexts': ['sing-alongs', 'road trips', 'celebration'],
                'sophistication_level': 'medium'
            },
            'modest mouse': {
                'primary_moods': ['quirky', 'existential', 'indie-experimental', 'off-kilter'],
                'energy_profile': 'unpredictable',
                'emotional_depth': 'philosophical',
                'sonic_characteristics': ['unusual song structures', 'distinctive vocals', 'creative arrangements'],
                'listening_contexts': ['indie exploration', 'thoughtful listening', 'creative work'],
                'sophistication_level': 'high'
            },
            'amy winehouse': {
                'primary_moods': ['soulful', 'retro-sophisticated', 'emotionally raw', 'jazzy'],
                'energy_profile': 'emotionally intense',
                'emotional_depth': 'deeply personal',
                'sonic_characteristics': ['vintage soul', 'powerful vocals', 'live instrumentation'],
                'listening_contexts': ['emotional moments', 'late night', 'appreciation of craft'],
                'sophistication_level': 'very high'
            },
            'sade': {
                'primary_moods': ['smooth', 'sensual', 'sophisticated', 'timeless'],
                'energy_profile': 'controlled elegance',
                'emotional_depth': 'mature romance',
                'sonic_characteristics': ['silky vocals', 'jazz influences', 'polished production'],
                'listening_contexts': ['romantic evenings', 'relaxation', 'sophisticated ambiance'],
                'sophistication_level': 'very high'
            },
            'james morrison': {
                'primary_moods': ['soulful', 'contemporary-classic', 'heartfelt', 'accessible'],
                'energy_profile': 'moderate warmth',
                'emotional_depth': 'relatable emotion',
                'sonic_characteristics': ['strong vocals', 'pop-soul fusion', 'radio-friendly'],
                'listening_contexts': ['easy listening', 'background music', 'emotional connection'],
                'sophistication_level': 'medium'
            }
        }
        
        # Advanced mood categories beyond basic genres
        self.sophisticated_moods = {
            'atmospheric': ['ethereal', 'spacious', 'immersive', 'cinematic'],
            'brooding': ['contemplative', 'dark', 'introspective', 'moody'],
            'sophisticated': ['refined', 'cultured', 'intelligent', 'nuanced'],
            'melancholic': ['wistful', 'bittersweet', 'nostalgic', 'pensive'],
            'energetic': ['driving', 'dynamic', 'powerful', 'invigorating'],
            'experimental': ['avant-garde', 'innovative', 'unconventional', 'artistic'],
            'soulful': ['emotional', 'heartfelt', 'expressive', 'passionate'],
            'rhythmic': ['groove-based', 'danceable', 'percussive', 'syncopated'],
            'anthemic': ['uplifting', 'communal', 'celebratory', 'inspiring'],
            'quirky': ['eccentric', 'playful', 'unconventional', 'charming']
        }
        
        # Contextual listening scenarios
        self.listening_contexts = {
            'late_night': ['introspective', 'atmospheric', 'contemplative'],
            'social_gathering': ['energetic', 'danceable', 'communal'],
            'focused_work': ['ambient', 'non-distracting', 'flow-inducing'],
            'emotional_processing': ['cathartic', 'expressive', 'healing'],
            'discovery': ['innovative', 'challenging', 'expanding'],
            'relaxation': ['soothing', 'peaceful', 'stress-relieving'],
            'motivation': ['energizing', 'empowering', 'driving']
        }
    
    def analyze_track_advanced(self, artist: str, track: str, basic_tags: List[str] = None) -> Dict[str, Any]:
        """
        Provide sophisticated mood analysis for a track
        """
        artist_lower = artist.lower()
        
        # Get sophisticated profile if available
        profile = self._get_artist_profile(artist_lower)
        
        if profile:
            return self._create_sophisticated_analysis(artist, track, profile, basic_tags)
        else:
            return self._infer_sophisticated_analysis(artist, track, basic_tags)
    
    def _get_artist_profile(self, artist_lower: str) -> Dict[str, Any]:
        """Get sophisticated artist profile"""
        # Direct match
        if artist_lower in self.artist_mood_profiles:
            return self.artist_mood_profiles[artist_lower]
        
        # Partial match for multi-word artists
        for known_artist in self.artist_mood_profiles:
            if known_artist in artist_lower or any(word in artist_lower for word in known_artist.split()):
                return self.artist_mood_profiles[known_artist]
        
        return None
    
    def _create_sophisticated_analysis(self, artist: str, track: str, profile: Dict[str, Any], basic_tags: List[str]) -> Dict[str, Any]:
        """Create sophisticated analysis from known profile"""
        
        # Expand primary moods into detailed sub-moods
        detailed_moods = []
        for mood in profile['primary_moods']:
            if mood in self.sophisticated_moods:
                detailed_moods.extend(self.sophisticated_moods[mood])
            else:
                detailed_moods.append(mood)
        
        # Analyze track title for additional context
        track_context = self._analyze_track_title(track)
        
        return {
            'artist': artist,
            'track': track,
            'primary_moods': profile['primary_moods'],
            'detailed_moods': detailed_moods[:6],  # Top 6 most relevant
            'energy_profile': profile['energy_profile'],
            'emotional_depth': profile['emotional_depth'],
            'sonic_characteristics': profile['sonic_characteristics'],
            'listening_contexts': profile['listening_contexts'],
            'sophistication_level': profile['sophistication_level'],
            'track_specific_context': track_context,
            'mood_confidence': 0.9,
            'analysis_type': 'sophisticated_profile',
            'basic_tags_enhanced': self._enhance_basic_tags(basic_tags) if basic_tags else [],
            'recommendation_weight': self._calculate_recommendation_weight(profile)
        }
    
    def _infer_sophisticated_analysis(self, artist: str, track: str, basic_tags: List[str]) -> Dict[str, Any]:
        """Infer sophisticated analysis for unknown artists"""
        
        # Analyze artist name patterns
        artist_characteristics = self._analyze_artist_name(artist)
        track_characteristics = self._analyze_track_title(track)
        
        # Enhance basic tags
        enhanced_tags = self._enhance_basic_tags(basic_tags) if basic_tags else []
        
        # Infer sophisticated moods
        inferred_moods = self._infer_moods_from_context(artist_characteristics, track_characteristics, enhanced_tags)
        
        return {
            'artist': artist,
            'track': track,
            'primary_moods': inferred_moods['primary'],
            'detailed_moods': inferred_moods['detailed'],
            'energy_profile': inferred_moods['energy'],
            'emotional_depth': inferred_moods['depth'],
            'sonic_characteristics': inferred_moods['sonic'],
            'listening_contexts': inferred_moods['contexts'],
            'sophistication_level': inferred_moods['sophistication'],
            'track_specific_context': track_characteristics,
            'mood_confidence': 0.6,
            'analysis_type': 'inferred_analysis',
            'basic_tags_enhanced': enhanced_tags,
            'recommendation_weight': 0.7
        }
    
    def _analyze_track_title(self, track: str) -> Dict[str, Any]:
        """Analyze track title for emotional/thematic context"""
        track_lower = track.lower()
        
        context = {
            'emotional_indicators': [],
            'thematic_elements': [],
            'energy_indicators': []
        }
        
        # Emotional keywords
        emotional_keywords = {
            'melancholic': ['sad', 'blue', 'lonely', 'empty', 'lost', 'gone'],
            'romantic': ['love', 'heart', 'kiss', 'together', 'forever'],
            'energetic': ['fire', 'run', 'dance', 'move', 'alive', 'electric'],
            'introspective': ['think', 'mind', 'soul', 'inside', 'deep'],
            'rebellious': ['break', 'fight', 'rebel', 'against', 'free']
        }
        
        for mood, keywords in emotional_keywords.items():
            if any(keyword in track_lower for keyword in keywords):
                context['emotional_indicators'].append(mood)
        
        # Time/setting indicators
        if any(word in track_lower for word in ['night', 'midnight', 'dark', 'moon']):
            context['thematic_elements'].append('nocturnal')
        if any(word in track_lower for word in ['morning', 'sun', 'light', 'day']):
            context['thematic_elements'].append('diurnal')
        if any(word in track_lower for word in ['city', 'street', 'urban', 'downtown']):
            context['thematic_elements'].append('urban')
        
        return context
    
    def _analyze_artist_name(self, artist: str) -> Dict[str, Any]:
        """Analyze artist name for stylistic hints"""
        artist_lower = artist.lower()
        
        characteristics = {
            'style_indicators': [],
            'sophistication_hints': []
        }
        
        # Style indicators from name patterns
        if any(word in artist_lower for word in ['the ', 'arctic', 'vampire', 'crystal']):
            characteristics['style_indicators'].append('indie_rock')
        if any(word in artist_lower for word in ['dj', 'electronic', 'digital']):
            characteristics['style_indicators'].append('electronic')
        if len(artist.split()) == 1 and artist.islower():
            characteristics['sophistication_hints'].append('minimalist_aesthetic')
        
        return characteristics
    
    def _enhance_basic_tags(self, basic_tags: List[str]) -> List[str]:
        """Enhance basic genre tags with sophisticated descriptors"""
        if not basic_tags:
            return []
        
        enhanced = []
        
        tag_enhancements = {
            'rock': ['guitar-driven', 'rhythmic', 'energetic', 'band-based'],
            'pop': ['melodic', 'accessible', 'hook-based', 'commercial'],
            'indie': ['independent', 'creative', 'non-mainstream', 'artistic'],
            'electronic': ['synthesized', 'programmed', 'digital', 'atmospheric'],
            'folk': ['acoustic', 'storytelling', 'traditional', 'organic'],
            'jazz': ['improvisational', 'sophisticated', 'complex', 'instrumental'],
            'classical': ['orchestral', 'composed', 'formal', 'timeless']
        }
        
        for tag in basic_tags:
            tag_lower = tag.lower()
            enhanced.append(tag)  # Keep original
            
            # Add sophisticated descriptors
            for genre, descriptors in tag_enhancements.items():
                if genre in tag_lower:
                    enhanced.extend(descriptors[:2])  # Add top 2 descriptors
        
        return list(set(enhanced))  # Remove duplicates
    
    def _infer_moods_from_context(self, artist_chars: Dict, track_chars: Dict, enhanced_tags: List[str]) -> Dict[str, Any]:
        """Infer sophisticated moods from available context"""
        
        # Default sophisticated analysis
        moods = {
            'primary': ['contemplative', 'melodic'],
            'detailed': ['thoughtful', 'musical', 'engaging', 'crafted'],
            'energy': 'moderate',
            'depth': 'accessible',
            'sonic': ['well-produced', 'balanced'],
            'contexts': ['background listening', 'discovery'],
            'sophistication': 'medium'
        }
        
        # Enhance based on enhanced tags
        if any(tag in enhanced_tags for tag in ['guitar-driven', 'energetic', 'rhythmic']):
            moods['primary'] = ['energetic', 'driving']
            moods['energy'] = 'high'
            moods['contexts'] = ['active listening', 'motivation']
        
        if any(tag in enhanced_tags for tag in ['atmospheric', 'synthesized', 'complex']):
            moods['primary'] = ['atmospheric', 'sophisticated']
            moods['sophistication'] = 'high'
            moods['contexts'] = ['focused listening', 'ambient']
        
        return moods
    
    def _calculate_recommendation_weight(self, profile: Dict[str, Any]) -> float:
        """Calculate recommendation weight based on sophistication"""
        sophistication_weights = {
            'very high': 1.0,
            'high': 0.9,
            'medium-high': 0.8,
            'medium': 0.7,
            'low': 0.5
        }
        
        return sophistication_weights.get(profile.get('sophistication_level', 'medium'), 0.7)
    
    def analyze_library_batch(self, tracks_df: pd.DataFrame) -> pd.DataFrame:
        """Analyze entire library with sophisticated mood analysis"""
        
        results = []
        
        for _, row in tracks_df.iterrows():
            artist = row.get('artist', '')
            track = row.get('track', '')
            basic_tags = row.get('musicbrainz_tags', '').split(', ') if row.get('musicbrainz_tags') else []
            
            analysis = self.analyze_track_advanced(artist, track, basic_tags)
            
            # Flatten for DataFrame
            flattened = {
                'artist': analysis['artist'],
                'track': analysis['track'],
                'sophisticated_moods': ', '.join(analysis['primary_moods']),
                'detailed_moods': ', '.join(analysis['detailed_moods']),
                'energy_profile': analysis['energy_profile'],
                'emotional_depth': analysis['emotional_depth'],
                'sonic_characteristics': ', '.join(analysis['sonic_characteristics']),
                'listening_contexts': ', '.join(analysis['listening_contexts']),
                'sophistication_level': analysis['sophistication_level'],
                'mood_confidence': analysis['mood_confidence'],
                'analysis_type': analysis['analysis_type'],
                'recommendation_weight': analysis['recommendation_weight']
            }
            
            results.append(flattened)
        
        return pd.DataFrame(results)

def test_advanced_analyzer():
    """Test the advanced mood analyzer"""
    logging.basicConfig(level=logging.INFO)
    
    analyzer = AdvancedMoodAnalyzer()
    
    # Test tracks
    test_tracks = [
        {'artist': 'Interpol', 'track': 'Evil'},
        {'artist': 'Arctic Monkeys', 'track': 'Brianstorm'},
        {'artist': 'Amy Winehouse', 'track': 'Rehab'},
        {'artist': 'Unknown Artist', 'track': 'Night Song'},
        {'artist': 'Bloc Party', 'track': 'Banquet'}
    ]
    
    print("🎵 Advanced Mood Analysis Results:")
    print("=" * 60)
    
    for track_info in test_tracks:
        analysis = analyzer.analyze_track_advanced(
            track_info['artist'], 
            track_info['track'],
            ['rock', 'indie']  # Simulate basic tags
        )
        
        print(f"\n🎼 {analysis['artist']} - {analysis['track']}")
        print(f"   Primary Moods: {', '.join(analysis['primary_moods'])}")
        print(f"   Detailed Moods: {', '.join(analysis['detailed_moods'])}")
        print(f"   Energy Profile: {analysis['energy_profile']}")
        print(f"   Emotional Depth: {analysis['emotional_depth']}")
        print(f"   Sophistication: {analysis['sophistication_level']}")
        print(f"   Listening Contexts: {', '.join(analysis['listening_contexts'])}")
        print(f"   Confidence: {analysis['mood_confidence']:.1%}")

if __name__ == "__main__":
    test_advanced_analyzer() 