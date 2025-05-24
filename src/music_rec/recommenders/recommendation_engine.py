"""
Advanced Recommendation Engine

Uses multiple signals to generate personalized recommendations:
- Listening history patterns
- AI-generated insights 
- MusicBrainz metadata
- Mood & genre preferences
- Temporal patterns
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import json
import logging
from collections import Counter, defaultdict
from dataclasses import dataclass
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

@dataclass
class RecommendationRequest:
    """Configuration for generating recommendations"""
    mood: Optional[str] = None
    energy_level: Optional[str] = None  # 'high', 'medium', 'low'
    discovery_level: float = 0.3  # 0.0 = only familiar, 1.0 = only new
    playlist_length: int = 20
    time_context: Optional[str] = None  # 'morning', 'afternoon', 'evening', 'night'
    exclude_recent: bool = True  # Don't recommend recently played tracks
    include_favorites: float = 0.2  # Portion of recommendations from favorites
    genre_focus: Optional[List[str]] = None
    decade_preference: Optional[str] = None

@dataclass  
class RecommendationResult:
    """Result of recommendation generation"""
    tracks: List[Dict[str, Any]]
    confidence_score: float
    explanation: str
    metadata: Dict[str, Any]

class RecommendationEngine:
    """
    Advanced recommendation engine using multiple data sources and AI insights
    """
    
    def __init__(self, username: str, data_dir: str = 'data'):
        self.username = username
        self.data_dir = Path(data_dir)
        
        # Load data
        self.scrobbles_df = None
        self.enriched_df = None
        self.patterns = None
        self.ai_insights = None
        
        # Features
        self.artist_features = None
        self.track_features = None
        self.mood_profiles = {}
        self.genre_profiles = {}
        self.temporal_profiles = {}
        
        self._load_data()
        self._build_features()
    
    def _load_data(self) -> None:
        """Load all available data sources"""
        
        # Load main scrobbles data
        scrobbles_file = self.data_dir / f'{self.username}_scrobbles.csv'
        if scrobbles_file.exists():
            self.scrobbles_df = pd.read_csv(scrobbles_file)
            logger.info(f"Loaded {len(self.scrobbles_df)} scrobbles")
        
        # Load enriched data if available
        enriched_file = self.data_dir / f'{self.username}_enriched.csv'
        if enriched_file.exists():
            self.enriched_df = pd.read_csv(enriched_file)
            logger.info(f"Loaded enriched data for {len(self.enriched_df)} tracks")
        
        # Load analysis patterns
        patterns_file = Path('reports') / f'{self.username}_patterns.json'
        if patterns_file.exists():
            with open(patterns_file, 'r') as f:
                self.patterns = json.load(f)
            logger.info("Loaded listening patterns")
        
        # Load AI insights
        insights_file = Path('reports') / f'{self.username}_ai_insights.json'
        if insights_file.exists():
            with open(insights_file, 'r') as f:
                self.ai_insights = json.load(f)
            logger.info("Loaded AI insights")
    
    def _build_features(self) -> None:
        """Build recommendation features from available data"""
        
        if self.scrobbles_df is None:
            logger.warning("No scrobbles data available")
            return
        
        # Build artist listening profiles
        self._build_artist_profiles()
        
        # Build mood and genre profiles if enriched data is available
        if self.enriched_df is not None:
            self._build_mood_profiles()
            self._build_genre_profiles()
        
        # Build temporal listening patterns
        self._build_temporal_profiles()
        
        logger.info("Feature building complete")
    
    def _build_artist_profiles(self) -> None:
        """Build artist listening frequency and recency profiles"""
        
        # Convert timestamps
        self.scrobbles_df['datetime'] = pd.to_datetime(self.scrobbles_df['timestamp'], unit='s')
        
        # Calculate artist listening stats
        artist_stats = self.scrobbles_df.groupby('artist').agg({
            'track': 'count',  # play count
            'datetime': ['min', 'max'],  # first and last played
            'album': 'nunique'  # unique albums
        }).round(2)
        
        artist_stats.columns = ['play_count', 'first_played', 'last_played', 'unique_albums']
        
        # Calculate recency score (more recent = higher score)
        now = datetime.now()
        artist_stats['days_since_last'] = (now - artist_stats['last_played']).dt.days
        artist_stats['recency_score'] = 1 / (1 + artist_stats['days_since_last'] / 30)  # Decay over months
        
        # Calculate diversity score (more albums = more diverse)
        artist_stats['diversity_score'] = artist_stats['unique_albums'] / artist_stats['play_count']
        
        self.artist_features = artist_stats
        
        logger.info(f"Built profiles for {len(artist_stats)} artists")
    
    def _build_mood_profiles(self) -> None:
        """Build mood listening preferences from enriched data"""
        
        if 'mood' not in self.enriched_df.columns and 'mood_primary' not in self.enriched_df.columns:
            return
        
        # Use whichever mood column is available
        mood_col = 'mood' if 'mood' in self.enriched_df.columns else 'mood_primary'
        
        # Merge with scrobbles to get play counts
        mood_data = self.enriched_df.merge(
            self.scrobbles_df.groupby(['artist', 'track']).size().reset_index(name='play_count'),
            on=['artist', 'track'],
            how='left'
        )
        
        # Calculate mood preferences
        mood_stats = mood_data.groupby(mood_col).agg({
            'play_count': ['sum', 'mean', 'count']
        }).round(3)
        
        mood_stats.columns = ['total_plays', 'avg_plays_per_track', 'track_count']
        
        # Calculate preference scores
        total_plays = mood_stats['total_plays'].sum()
        if total_plays > 0:
            mood_stats['preference_score'] = mood_stats['total_plays'] / total_plays
        else:
            mood_stats['preference_score'] = 0.0
        
        self.mood_profiles = mood_stats.to_dict('index')
        
        logger.info(f"Built mood profiles for {len(mood_stats)} moods")
    
    def _build_genre_profiles(self) -> None:
        """Build genre listening preferences from enriched data"""
        
        if 'primary_genre' not in self.enriched_df.columns:
            return
        
        # Merge with scrobbles
        genre_data = self.enriched_df.merge(
            self.scrobbles_df.groupby(['artist', 'track']).size().reset_index(name='play_count'),
            on=['artist', 'track'],
            how='left'
        )
        
        # Calculate genre preferences
        genre_stats = genre_data.groupby('primary_genre').agg({
            'play_count': ['sum', 'count'],
            'artist': 'nunique'
        }).round(3)
        
        genre_stats.columns = ['total_plays', 'track_count', 'unique_artists']
        
        # Calculate preference scores
        total_plays = genre_stats['total_plays'].sum()
        genre_stats['preference_score'] = genre_stats['total_plays'] / total_plays
        
        self.genre_profiles = genre_stats.to_dict('index')
        
        logger.info(f"Built genre profiles for {len(genre_stats)} genres")
    
    def _build_temporal_profiles(self) -> None:
        """Build temporal listening patterns"""
        
        df = self.scrobbles_df.copy()
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
        df['hour'] = df['datetime'].dt.hour
        df['day_of_week'] = df['datetime'].dt.day_name()
        
        # Hour-based patterns
        hourly_patterns = df.groupby('hour').agg({
            'track': 'count',
            'artist': 'nunique'
        })
        hourly_patterns.columns = ['play_count', 'unique_artists']
        
        # Day-based patterns  
        daily_patterns = df.groupby('day_of_week').agg({
            'track': 'count',
            'artist': 'nunique'
        })
        daily_patterns.columns = ['play_count', 'unique_artists']
        
        self.temporal_profiles = {
            'hourly': hourly_patterns.to_dict('index'),
            'daily': daily_patterns.to_dict('index')
        }
        
        logger.info("Built temporal listening profiles")
    
    def generate_recommendations(self, request: RecommendationRequest) -> RecommendationResult:
        """
        Generate personalized recommendations based on request parameters
        """
        
        logger.info(f"Generating recommendations with parameters: {request}")
        
        # Get candidate tracks
        candidates = self._get_candidate_tracks(request)
        
        # Score and rank candidates
        scored_candidates = self._score_candidates(candidates, request)
        
        # Select final recommendations
        recommendations = self._select_recommendations(scored_candidates, request)
        
        # Generate explanation
        explanation = self._generate_explanation(recommendations, request)
        
        # Calculate confidence score
        confidence = self._calculate_confidence(recommendations, request)
        
        # Prepare metadata
        metadata = self._prepare_metadata(recommendations, request)
        
        return RecommendationResult(
            tracks=recommendations[:request.playlist_length],
            confidence_score=confidence,
            explanation=explanation,
            metadata=metadata
        )
    
    def _get_candidate_tracks(self, request: RecommendationRequest) -> pd.DataFrame:
        """Get candidate tracks for recommendations"""
        
        # Start with all available tracks
        if self.enriched_df is not None:
            candidates = self.enriched_df.copy()
        else:
            # Fallback to unique tracks from scrobbles
            candidates = self.scrobbles_df.drop_duplicates(['artist', 'track']).copy()
        
        # Apply filters based on request
        
        # Mood filter - check for both possible column names
        if request.mood:
            mood_col = None
            if 'mood' in candidates.columns:
                mood_col = 'mood'
            elif 'mood_primary' in candidates.columns:
                mood_col = 'mood_primary'
            
            if mood_col:
                candidates = candidates[candidates[mood_col] == request.mood]
        
        # Genre filter
        if request.genre_focus and 'primary_genre' in candidates.columns:
            candidates = candidates[candidates['primary_genre'].isin(request.genre_focus)]
        
        # Energy level filter
        if request.energy_level and 'energy' in candidates.columns:
            if request.energy_level == 'high':
                candidates = candidates[candidates['energy'] >= 0.7]
            elif request.energy_level == 'medium':
                candidates = candidates[(candidates['energy'] >= 0.3) & (candidates['energy'] < 0.7)]
            elif request.energy_level == 'low':
                candidates = candidates[candidates['energy'] < 0.3]
        
        # Exclude recent if requested
        if request.exclude_recent:
            candidates = self._exclude_recent_tracks(candidates)
        
        logger.info(f"Found {len(candidates)} candidate tracks after filtering")
        return candidates
    
    def _exclude_recent_tracks(self, candidates: pd.DataFrame) -> pd.DataFrame:
        """Exclude tracks played in the last 7 days"""
        
        if self.scrobbles_df is None:
            return candidates
        
        # Get tracks played in last 7 days
        cutoff_date = datetime.now() - timedelta(days=7)
        recent_df = self.scrobbles_df.copy()
        recent_df['datetime'] = pd.to_datetime(recent_df['timestamp'], unit='s')
        recent_tracks = recent_df[recent_df['datetime'] >= cutoff_date][['artist', 'track']].drop_duplicates()
        
        # Exclude from candidates
        merged = candidates.merge(recent_tracks, on=['artist', 'track'], how='left', indicator=True)
        filtered = merged[merged['_merge'] == 'left_only'].drop('_merge', axis=1)
        
        logger.info(f"Excluded {len(candidates) - len(filtered)} recently played tracks")
        return filtered
    
    def _score_candidates(self, candidates: pd.DataFrame, request: RecommendationRequest) -> pd.DataFrame:
        """Score candidate tracks for recommendation quality"""
        
        candidates = candidates.copy()
        
        # Initialize scores
        candidates['total_score'] = 0.0
        candidates['familiarity_score'] = 0.0
        candidates['mood_score'] = 0.0
        candidates['temporal_score'] = 0.0
        candidates['diversity_score'] = 0.0
        
        # Score based on listening history (familiarity)
        candidates = self._score_familiarity(candidates, request)
        
        # Score based on mood preferences
        if request.mood:
            candidates = self._score_mood_match(candidates, request)
        
        # Score based on temporal patterns
        if request.time_context:
            candidates = self._score_temporal_match(candidates, request)
        
        # Score for diversity
        candidates = self._score_diversity(candidates, request)
        
        # Combine scores
        candidates['total_score'] = (
            candidates['familiarity_score'] * (1 - request.discovery_level) +
            candidates['mood_score'] * 0.3 +
            candidates['temporal_score'] * 0.2 +
            candidates['diversity_score'] * request.discovery_level
        )
        
        return candidates.sort_values('total_score', ascending=False)
    
    def _score_familiarity(self, candidates: pd.DataFrame, request: RecommendationRequest) -> pd.DataFrame:
        """Score based on artist familiarity from listening history"""
        
        if self.artist_features is None:
            candidates['familiarity_score'] = 0.5  # Neutral score
            return candidates
        
        # Merge with artist features
        candidates = candidates.merge(
            self.artist_features[['play_count', 'recency_score']].reset_index(),
            on='artist',
            how='left'
        )
        
        # Fill missing values (new artists)
        candidates['play_count'] = candidates['play_count'].fillna(0)
        candidates['recency_score'] = candidates['recency_score'].fillna(0)
        
        # Normalize scores
        if candidates['play_count'].max() > 0:
            candidates['familiarity_score'] = candidates['play_count'] / candidates['play_count'].max()
        else:
            candidates['familiarity_score'] = 0.0
        
        # Boost with recency
        candidates['familiarity_score'] = (
            candidates['familiarity_score'] * 0.7 + 
            candidates['recency_score'] * 0.3
        )
        
        return candidates
    
    def _score_mood_match(self, candidates: pd.DataFrame, request: RecommendationRequest) -> pd.DataFrame:
        """Score based on mood preference match"""
        
        # Check if we have mood data and profiles
        mood_col = None
        if 'mood' in candidates.columns:
            mood_col = 'mood'
        elif 'mood_primary' in candidates.columns:
            mood_col = 'mood_primary'
        
        if not self.mood_profiles or not mood_col:
            candidates['mood_score'] = 0.5
            return candidates
        
        # Get user's preference for this mood
        mood_pref = self.mood_profiles.get(request.mood, {}).get('preference_score', 0.1)
        
        # Score tracks matching the requested mood higher
        candidates['mood_score'] = np.where(
            candidates[mood_col] == request.mood,
            0.8 + mood_pref * 0.2,  # High score for matching mood
            0.3  # Lower score for non-matching
        )
        
        return candidates
    
    def _score_temporal_match(self, candidates: pd.DataFrame, request: RecommendationRequest) -> pd.DataFrame:
        """Score based on temporal listening patterns"""
        
        if not self.temporal_profiles:
            candidates['temporal_score'] = 0.5
            return candidates
        
        # Map time context to hours
        time_hour_map = {
            'morning': [6, 7, 8, 9, 10, 11],
            'afternoon': [12, 13, 14, 15, 16, 17],
            'evening': [18, 19, 20, 21],
            'night': [22, 23, 0, 1, 2, 3, 4, 5]
        }
        
        if request.time_context not in time_hour_map:
            candidates['temporal_score'] = 0.5
            return candidates
        
        # Calculate average listening activity for these hours
        target_hours = time_hour_map[request.time_context]
        hourly_data = self.temporal_profiles['hourly']
        
        avg_activity = np.mean([
            hourly_data.get(hour, {}).get('play_count', 0) 
            for hour in target_hours
        ])
        
        # Normalize and assign score
        max_activity = max([
            data.get('play_count', 0) 
            for data in hourly_data.values()
        ])
        
        if max_activity > 0:
            temporal_score = avg_activity / max_activity
        else:
            temporal_score = 0.5
        
        candidates['temporal_score'] = temporal_score
        
        return candidates
    
    def _score_diversity(self, candidates: pd.DataFrame, request: RecommendationRequest) -> pd.DataFrame:
        """Score for diversity and discovery potential"""
        
        if self.artist_features is None:
            candidates['diversity_score'] = np.random.random(len(candidates))
            return candidates
        
        # Merge with artist features
        candidates = candidates.merge(
            self.artist_features[['diversity_score']].reset_index(),
            on='artist',
            how='left'
        )
        
        # Fill missing values with high diversity (new artists)
        if 'diversity_score' not in candidates.columns:
            candidates['diversity_score'] = 0.8
        else:
            candidates['diversity_score'] = candidates['diversity_score'].fillna(0.8)
        
        # Add some randomness for discovery
        candidates['diversity_score'] += np.random.random(len(candidates)) * 0.2
        
        return candidates
    
    def _select_recommendations(self, scored_candidates: pd.DataFrame, request: RecommendationRequest) -> List[Dict[str, Any]]:
        """Select final recommendations with diversity constraints"""
        
        recommendations = []
        used_artists = set()
        used_albums = set()
        
        # Include some favorites first
        favorites_count = int(request.playlist_length * request.include_favorites)
        
        for _, track in scored_candidates.iterrows():
            if len(recommendations) >= request.playlist_length:
                break
            
            # Avoid artist repetition (allow some for favorites)
            if track['artist'] in used_artists and len(recommendations) > favorites_count:
                continue
            
            # Avoid album repetition
            album_key = f"{track['artist']}_{track.get('album', 'Unknown')}"
            if album_key in used_albums and len(recommendations) > favorites_count * 2:
                continue
            
            # Add to recommendations
            track_dict = track.to_dict()
            recommendations.append(track_dict)
            
            used_artists.add(track['artist'])
            used_albums.add(album_key)
        
        logger.info(f"Selected {len(recommendations)} recommendations from {len(scored_candidates)} candidates")
        return recommendations
    
    def _generate_explanation(self, recommendations: List[Dict], request: RecommendationRequest) -> str:
        """Generate human-readable explanation for recommendations"""
        
        explanations = []
        
        # Mood explanation
        if request.mood:
            explanations.append(f"Focused on {request.mood} mood tracks")
        
        # Discovery level explanation
        if request.discovery_level > 0.7:
            explanations.append("Emphasizing musical discovery and new artists")
        elif request.discovery_level < 0.3:
            explanations.append("Focusing on familiar favorites from your listening history")
        else:
            explanations.append("Balancing familiar favorites with some discovery")
        
        # Temporal context
        if request.time_context:
            explanations.append(f"Optimized for {request.time_context} listening")
        
        # Exclusion explanation
        if request.exclude_recent:
            explanations.append("Excluding recently played tracks for freshness")
        
        return ". ".join(explanations) + "."
    
    def _calculate_confidence(self, recommendations: List[Dict], request: RecommendationRequest) -> float:
        """Calculate confidence score for recommendations"""
        
        if not recommendations:
            return 0.0
        
        # Base confidence on data availability
        confidence = 0.3  # Base confidence
        
        # Boost if we have enriched data
        if self.enriched_df is not None:
            confidence += 0.2
        
        # Boost if we have AI insights
        if self.ai_insights:
            confidence += 0.2
        
        # Boost if we have listening history
        if self.artist_features is not None:
            confidence += 0.2
        
        # Reduce if too few candidates
        if len(recommendations) < request.playlist_length * 0.5:
            confidence -= 0.2
        
        return max(0.0, min(1.0, confidence))
    
    def _prepare_metadata(self, recommendations: List[Dict], request: RecommendationRequest) -> Dict[str, Any]:
        """Prepare metadata about the recommendations"""
        
        if not recommendations:
            return {}
        
        # Aggregate stats
        artists = [r['artist'] for r in recommendations]
        artist_counts = Counter(artists)
        
        metadata = {
            'total_tracks': len(recommendations),
            'unique_artists': len(set(artists)),
            'most_featured_artist': artist_counts.most_common(1)[0] if artist_counts else None,
            'request_parameters': {
                'mood': request.mood,
                'energy_level': request.energy_level,
                'discovery_level': request.discovery_level,
                'time_context': request.time_context
            },
            'generated_at': datetime.now().isoformat()
        }
        
        # Add genre distribution if available
        if recommendations and 'primary_genre' in recommendations[0]:
            genres = [r.get('primary_genre') for r in recommendations if r.get('primary_genre')]
            metadata['genre_distribution'] = dict(Counter(genres))
        
        # Add mood distribution if available
        if recommendations and 'mood' in recommendations[0]:
            moods = [r.get('mood') for r in recommendations if r.get('mood')]
            metadata['mood_distribution'] = dict(Counter(moods))
        
        return metadata
    
    def get_recommendation_presets(self) -> Dict[str, RecommendationRequest]:
        """Get pre-configured recommendation presets"""
        
        presets = {
            'morning_energy': RecommendationRequest(
                mood='happy',
                energy_level='high',
                discovery_level=0.2,
                time_context='morning',
                playlist_length=25,
                include_favorites=0.3
            ),
            'focus_work': RecommendationRequest(
                mood='calm',
                energy_level='medium',
                discovery_level=0.1,
                playlist_length=30,
                include_favorites=0.4
            ),
            'evening_chill': RecommendationRequest(
                mood='calm',
                energy_level='low',
                discovery_level=0.3,
                time_context='evening',
                playlist_length=20,
                include_favorites=0.5
            ),
            'weekend_discovery': RecommendationRequest(
                discovery_level=0.8,
                playlist_length=25,
                include_favorites=0.1,
                exclude_recent=True
            ),
            'nostalgic_favorites': RecommendationRequest(
                discovery_level=0.0,
                playlist_length=30,
                include_favorites=0.8,
                exclude_recent=False
            ),
            'party_mix': RecommendationRequest(
                mood='energetic',
                energy_level='high',
                discovery_level=0.4,
                playlist_length=40,
                include_favorites=0.3
            )
        }
        
        return presets 