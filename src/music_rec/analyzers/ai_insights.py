"""
AI-Powered Music Insights Generator

Uses OpenAI or Anthropic APIs to generate intelligent insights about
listening patterns and music preferences.
"""

import os
import json
import asyncio
from typing import Dict, List, Optional, Union
import logging

from rich.console import Console

# AI API clients
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

logger = logging.getLogger(__name__)
console = Console()

class AIInsightGenerator:
    """
    AI-powered insight generator for music listening patterns.
    
    Designed to provide actionable insights for busy professionals.
    """
    
    def __init__(self, openai_api_key: Optional[str] = None, 
                 anthropic_api_key: Optional[str] = None):
        """
        Initialize with API keys.
        
        Args:
            openai_api_key: OpenAI API key
            anthropic_api_key: Anthropic API key
        """
        self.openai_client = None
        self.anthropic_client = None
        
        # Initialize OpenAI if available
        if openai_api_key and OPENAI_AVAILABLE:
            openai.api_key = openai_api_key
            self.openai_client = openai
            logger.info("OpenAI client initialized")
        
        # Initialize Anthropic if available
        if anthropic_api_key and ANTHROPIC_AVAILABLE:
            self.anthropic_client = anthropic.Anthropic(api_key=anthropic_api_key)
            logger.info("Anthropic client initialized")
        
        if not self.openai_client and not self.anthropic_client:
            logger.warning("No AI clients available. Install openai and/or anthropic packages and provide API keys.")
    
    def generate_comprehensive_insights(self, patterns: Dict) -> Dict[str, str]:
        """
        Generate comprehensive AI insights from pattern analysis.
        
        Args:
            patterns: Dictionary containing pattern analysis results
            
        Returns:
            Dictionary with AI-generated insights
        """
        if not self._has_ai_client():
            return self._generate_fallback_insights(patterns)
        
        insights = {}
        
        # Generate different types of insights
        insights.update(self._generate_personality_insights(patterns))
        insights.update(self._generate_behavioral_insights(patterns))
        insights.update(self._generate_trend_insights(patterns))
        insights.update(self._generate_recommendation_insights(patterns))
        
        return insights
    
    def _generate_personality_insights(self, patterns: Dict) -> Dict[str, str]:
        """Generate insights about musical personality."""
        
        prompt = self._build_personality_prompt(patterns)
        
        if self.openai_client:
            response = self._call_openai(prompt, max_tokens=300)
        elif self.anthropic_client:
            response = self._call_anthropic(prompt, max_tokens=300)
        else:
            return {}
        
        return {"musical_personality": response}
    
    def _generate_behavioral_insights(self, patterns: Dict) -> Dict[str, str]:
        """Generate insights about listening behavior."""
        
        prompt = self._build_behavior_prompt(patterns)
        
        if self.openai_client:
            response = self._call_openai(prompt, max_tokens=250)
        elif self.anthropic_client:
            response = self._call_anthropic(prompt, max_tokens=250)
        else:
            return {}
        
        return {"listening_behavior": response}
    
    def _generate_trend_insights(self, patterns: Dict) -> Dict[str, str]:
        """Generate insights about musical trends and evolution."""
        
        prompt = self._build_trends_prompt(patterns)
        
        if self.openai_client:
            response = self._call_openai(prompt, max_tokens=250)
        elif self.anthropic_client:
            response = self._call_anthropic(prompt, max_tokens=250)
        else:
            return {}
        
        return {"musical_evolution": response}
    
    def _generate_recommendation_insights(self, patterns: Dict) -> Dict[str, str]:
        """Generate actionable recommendations based on patterns."""
        
        prompt = self._build_recommendations_prompt(patterns)
        
        if self.openai_client:
            response = self._call_openai(prompt, max_tokens=300)
        elif self.anthropic_client:
            response = self._call_anthropic(prompt, max_tokens=300)
        else:
            return {}
        
        return {"personalized_recommendations": response}
    
    def _build_personality_prompt(self, patterns: Dict) -> str:
        """Build prompt for musical personality analysis."""
        
        temporal = patterns.get('temporal', {})
        discovery = patterns.get('discovery', {})
        artist_loyalty = patterns.get('artist_loyalty', {})
        
        prompt = f"""
        You are a music psychology expert analyzing someone's listening patterns. Based on this data, describe their musical personality in 2-3 engaging sentences:

        Listening Times:
        - Peak hours: {temporal.get('peak_listening_hours', [])}
        - Peak days: {temporal.get('peak_listening_days', [])}
        - Average session length: {temporal.get('average_session_length', 0)} tracks

        Music Discovery:
        - Discovery ratio: {discovery.get('discovery_ratio', 0)}% of tracks played only once
        - Monthly new tracks: {discovery.get('avg_monthly_discovery', 0)} on average
        - Heavy rotation tracks: {discovery.get('heavy_rotation_tracks', 0)}

        Artist Preferences:
        - Unique artists: {artist_loyalty.get('unique_artists', 0)}
        - Artist exploration ratio: {artist_loyalty.get('exploration_ratio', 0)}%
        - Top artist concentration: {artist_loyalty.get('artist_concentration', 0)}%

        Write a warm, personal analysis that captures their unique musical personality. Focus on what this says about them as a person, not just statistics.
        """
        
        return prompt.strip()
    
    def _build_behavior_prompt(self, patterns: Dict) -> str:
        """Build prompt for listening behavior analysis."""
        
        temporal = patterns.get('temporal', {})
        intensity = patterns.get('listening_intensity', {})
        repetition = patterns.get('repetition', {})
        
        prompt = f"""
        Analyze this person's listening behavior patterns and explain what they reveal about their relationship with music:

        Temporal Patterns:
        - Listening consistency score: {temporal.get('listening_consistency', 0)}
        - Total sessions: {temporal.get('total_sessions', 0)}

        Listening Intensity:
        - Average daily plays: {intensity.get('avg_daily_plays', 0)}
        - High activity days: {intensity.get('high_activity_days', 0)}
        - Listening variability: {intensity.get('listening_variability', 0)}

        Repetition Patterns:
        - Immediate repeats: {repetition.get('immediate_repeats', 0)}
        - Most repeated track plays: {repetition.get('max_track_repeats', 0)}
        - Tracks played once: {repetition.get('tracks_played_once', 0)}

        Provide insights about their listening habits, music's role in their daily life, and what this suggests about their personality. Be conversational and insightful.
        """
        
        return prompt.strip()
    
    def _build_trends_prompt(self, patterns: Dict) -> str:
        """Build prompt for musical evolution analysis."""
        
        genre_evolution = patterns.get('genre_evolution', {})
        seasonal = patterns.get('seasonal', {})
        summary = patterns.get('summary_stats', {})
        
        prompt = f"""
        Analyze how this person's musical taste has evolved over time:

        Musical Evolution:
        - Years of data: {genre_evolution.get('total_timespan_years', 0)}
        - Yearly diversity changes: {genre_evolution.get('yearly_diversity_index', {})}
        - Most consistent artists: {genre_evolution.get('most_consistent_artists', [])}

        Seasonal Patterns:
        - Preferred season: {seasonal.get('preferred_season', 'Unknown')}
        - Seasonal distribution: {seasonal.get('seasonal_distribution', {})}

        Data Span:
        - Total scrobbles: {summary.get('total_scrobbles', 0)}
        - Date range: {summary.get('date_range_days', 0)} days
        - Data completeness: {summary.get('data_completeness', 'Unknown')}

        Describe their musical journey and evolution. What trends do you see? How has their taste changed or stayed consistent? Be engaging and insightful about their musical growth.
        """
        
        return prompt.strip()
    
    def _build_recommendations_prompt(self, patterns: Dict) -> str:
        """Build prompt for personalized recommendations."""
        
        discovery = patterns.get('discovery', {})
        temporal = patterns.get('temporal', {})
        artist_loyalty = patterns.get('artist_loyalty', {})
        
        prompt = f"""
        Based on this listening data, provide 3-4 specific, actionable recommendations for discovering new music:

        Current Discovery Pattern:
        - Discovery ratio: {discovery.get('discovery_ratio', 0)}%
        - Monthly new tracks: {discovery.get('avg_monthly_discovery', 0)}
        - Top artists: {list(artist_loyalty.get('top_artists', {}).keys())[:5]}

        Listening Habits:
        - Peak listening times: {temporal.get('peak_listening_hours', [])}
        - Peak days: {temporal.get('peak_listening_days', [])}

        Provide specific, personalized recommendations like:
        - Discovery strategies that match their current habits
        - Optimal times for music exploration
        - How to expand their taste based on current preferences
        - Specific approaches for their listening style

        Be practical and actionable for a busy professional. Focus on easy wins that will enhance their music experience.
        """
        
        return prompt.strip()
    
    def _call_openai(self, prompt: str, max_tokens: int = 3000) -> str:
        """Call OpenAI API."""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4.1-2025-04-14",
                messages=[
                    {"role": "system", "content": "You are a music psychology expert who provides insightful, personal analysis of listening patterns."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return f"AI analysis temporarily unavailable: {str(e)}"
    
    def _call_anthropic(self, prompt: str, max_tokens: int = 3000) -> str:
        """Call Anthropic API."""
        try:
            response = self.anthropic_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=max_tokens,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.content[0].text.strip()
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            return f"AI analysis temporarily unavailable: {str(e)}"
    
    def _has_ai_client(self) -> bool:
        """Check if any AI client is available."""
        return self.openai_client is not None or self.anthropic_client is not None
    
    def _generate_fallback_insights(self, patterns: Dict) -> Dict[str, str]:
        """Generate basic insights when AI is not available."""
        
        insights = {}
        
        # Temporal insights
        temporal = patterns.get('temporal', {})
        if temporal:
            peak_hours = temporal.get('peak_listening_hours', [])
            if peak_hours:
                peak_hour = peak_hours[0]
                if 6 <= peak_hour <= 11:
                    time_personality = "You're a morning music person who starts the day with tunes"
                elif 12 <= peak_hour <= 17:
                    time_personality = "You're an afternoon listener who enjoys music during the day"
                elif 18 <= peak_hour <= 22:
                    time_personality = "You're an evening music lover who winds down with songs"
                else:
                    time_personality = "You're a night owl who loves music in the quiet hours"
                
                insights['musical_personality'] = time_personality
        
        # Discovery insights
        discovery = patterns.get('discovery', {})
        if discovery:
            discovery_ratio = discovery.get('discovery_ratio', 0)
            if discovery_ratio > 70:
                discovery_style = "You're a musical explorer who constantly seeks new tracks and artists"
            elif discovery_ratio > 40:
                discovery_style = "You balance familiar favorites with regular musical discovery"
            else:
                discovery_style = "You're loyal to your favorites and prefer deeper exploration of known artists"
            
            insights['listening_behavior'] = discovery_style
        
        # Trend insights
        summary = patterns.get('summary_stats', {})
        if summary:
            total_years = patterns.get('genre_evolution', {}).get('total_timespan_years', 1)
            tracks_per_year = summary.get('unique_tracks', 0) / max(total_years, 1)
            
            if tracks_per_year > 1000:
                evolution = "Your musical journey shows incredible breadth with thousands of unique tracks explored"
            elif tracks_per_year > 500:
                evolution = "You have a rich musical journey with steady exploration of new music"
            else:
                evolution = "Your musical taste shows focused depth rather than broad exploration"
            
            insights['musical_evolution'] = evolution
        
        # Basic recommendations
        artist_loyalty = patterns.get('artist_loyalty', {})
        exploration_ratio = artist_loyalty.get('exploration_ratio', 0)
        
        if exploration_ratio > 60:
            recommendations = "Try genre-specific playlists and artist radio to discover similar artists to your one-time listens"
        else:
            recommendations = "Explore deep cuts and B-sides from your favorite artists, plus artists they've collaborated with"
        
        insights['personalized_recommendations'] = recommendations
        
        return insights
    
    def generate_music_dna_report(self, patterns: Dict) -> str:
        """Generate a comprehensive 'Music DNA' report."""
        
        if not patterns:
            return "No pattern data available for analysis."
        
        # Get AI insights
        ai_insights = self.generate_comprehensive_insights(patterns)
        
        # Build comprehensive report
        report_sections = []
        
        # Header
        summary = patterns.get('summary_stats', {})
        total_scrobbles = summary.get('total_scrobbles', 0)
        date_range = summary.get('date_range_days', 0)
        
        report_sections.append(f"""
🧬 YOUR MUSIC DNA ANALYSIS
{'=' * 50}

Data Overview: {total_scrobbles:,} scrobbles across {date_range} days
Analysis Period: {summary.get('first_scrobble', 'Unknown')[:10]} to {summary.get('last_scrobble', 'Unknown')[:10]}
""")
        
        # AI Insights sections
        if 'musical_personality' in ai_insights:
            report_sections.append(f"""
🎭 MUSICAL PERSONALITY
{ai_insights['musical_personality']}
""")
        
        if 'listening_behavior' in ai_insights:
            report_sections.append(f"""
🎵 LISTENING BEHAVIOR  
{ai_insights['listening_behavior']}
""")
        
        if 'musical_evolution' in ai_insights:
            report_sections.append(f"""
📈 MUSICAL EVOLUTION
{ai_insights['musical_evolution']}
""")
        
        if 'personalized_recommendations' in ai_insights:
            report_sections.append(f"""
💡 PERSONALIZED RECOMMENDATIONS
{ai_insights['personalized_recommendations']}
""")
        
        # Key Statistics
        temporal = patterns.get('temporal', {})
        discovery = patterns.get('discovery', {})
        artist_loyalty = patterns.get('artist_loyalty', {})
        
        report_sections.append(f"""
📊 KEY STATISTICS
Peak Listening: {temporal.get('peak_listening_hours', ['Unknown'])[0]}:00 on {temporal.get('peak_listening_days', ['Unknown'])[0]}s
Discovery Rate: {discovery.get('discovery_ratio', 0)}% of tracks are single plays
Artist Loyalty: {artist_loyalty.get('unique_artists', 0)} unique artists, {artist_loyalty.get('exploration_ratio', 0)}% exploration rate
Session Length: {temporal.get('average_session_length', 0)} tracks per listening session
""")
        
        return '\n'.join(report_sections)
    
    async def generate_async_insights(self, patterns: Dict) -> Dict[str, str]:
        """Generate insights asynchronously for better performance."""
        
        if not self._has_ai_client():
            return self._generate_fallback_insights(patterns)
        
        # Create async tasks for different insight types
        tasks = [
            self._generate_personality_insights(patterns),
            self._generate_behavioral_insights(patterns),
            self._generate_trend_insights(patterns),
            self._generate_recommendation_insights(patterns)
        ]
        
        # Note: This is a simplified async implementation
        # In practice, you'd want proper async API calls
        results = {}
        for task in tasks:
            results.update(task)
        
        return results 