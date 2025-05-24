"""
Music Recommendation Engine

Phase 4: Intelligent playlist generation using:
- AI-analyzed listening patterns
- MusicBrainz metadata enrichment
- Mood and genre classification
- Temporal listening patterns
"""

from .playlist_generator import PlaylistGenerator
from .recommendation_engine import RecommendationEngine, RecommendationRequest, RecommendationResult

__all__ = ['PlaylistGenerator', 'RecommendationEngine', 'RecommendationRequest', 'RecommendationResult'] 