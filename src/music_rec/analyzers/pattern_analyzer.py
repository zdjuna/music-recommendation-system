"""
Music Listening Pattern Analyzer

Analyzes listening data to extract meaningful patterns including:
- Temporal patterns (when you listen)
- Discovery patterns (how much new music)
- Genre evolution over time
- Artist loyalty and exploration
- Listening intensity patterns
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging

import pandas as pd
import numpy as np
from collections import Counter, defaultdict

logger = logging.getLogger(__name__)

class PatternAnalyzer:
    """
    Comprehensive analyzer for music listening patterns.
    
    Designed to extract actionable insights for busy professionals.
    """
    
    def __init__(self, data: pd.DataFrame):
        """
        Initialize with listening data.
        
        Args:
            data: DataFrame with columns: timestamp, artist, track, album, date
        """
        self.data = data.copy()
        self.prepare_data()
        
        # Analysis results storage
        self.patterns = {}
        self.insights = {}
    
    def prepare_data(self):
        """Prepare data for analysis by adding derived columns."""
        if self.data.empty:
            return
        
        # Convert timestamp to datetime if needed
        if 'timestamp' in self.data.columns:
            self.data['datetime'] = pd.to_datetime(self.data['timestamp'], unit='s')
        elif 'date' in self.data.columns:
            self.data['datetime'] = pd.to_datetime(self.data['date'])
        
        # Extract time components
        self.data['hour'] = self.data['datetime'].dt.hour
        self.data['day_of_week'] = self.data['datetime'].dt.day_name()
        self.data['month'] = self.data['datetime'].dt.month
        self.data['year'] = self.data['datetime'].dt.year
        self.data['quarter'] = self.data['datetime'].dt.quarter
        
        # Create unique track identifier
        self.data['track_id'] = (self.data['artist'] + ' - ' + self.data['track']).str.lower()
        
        # Sort by datetime
        self.data = self.data.sort_values('datetime').reset_index(drop=True)
        
        logger.info(f"Prepared {len(self.data)} scrobbles for analysis")
    
    def analyze_all_patterns(self) -> Dict:
        """
        Run comprehensive analysis of all patterns.
        
        Returns:
            Dictionary containing all pattern analysis results
        """
        logger.info("Starting comprehensive pattern analysis...")
        
        self.patterns = {
            'temporal': self.analyze_temporal_patterns(),
            'discovery': self.analyze_discovery_patterns(),
            'artist_loyalty': self.analyze_artist_patterns(),
            'genre_evolution': self.analyze_genre_evolution(),
            'yearly_evolution': self.analyze_yearly_evolution(),
            'musical_phases': self.detect_musical_phases(),
            'listening_intensity': self.analyze_listening_intensity(),
            'repetition': self.analyze_repetition_patterns(),
            'seasonal': self.analyze_seasonal_patterns(),
            'yearly_evolution': self.analyze_yearly_evolution(),
            'enhanced_musical_phases': self.analyze_musical_phases(),
            'year_over_year_evolution': self.analyze_year_over_year_evolution(),
            'summary_stats': self.get_summary_statistics()
        }
        
        logger.info("Pattern analysis complete")
        return self.patterns
    
    def analyze_temporal_patterns(self) -> Dict:
        """Analyze when the user listens to music."""
        if self.data.empty:
            return {}
        
        # Hour distribution
        hourly_counts = self.data['hour'].value_counts().sort_index()
        peak_hours = hourly_counts.nlargest(3).index.tolist()
        
        # Day of week distribution
        daily_counts = self.data['day_of_week'].value_counts()
        peak_days = daily_counts.nlargest(2).index.tolist()
        
        # Listening sessions (gaps > 1 hour = new session)
        sessions = []
        current_session = []
        
        for i, row in self.data.iterrows():
            if not current_session:
                current_session = [row['datetime']]
            else:
                time_diff = (row['datetime'] - current_session[-1]).total_seconds() / 3600
                if time_diff > 1:  # New session if gap > 1 hour
                    sessions.append(len(current_session))
                    current_session = [row['datetime']]
                else:
                    current_session.append(row['datetime'])
        
        if current_session:
            sessions.append(len(current_session))
        
        avg_session_length = np.mean(sessions) if sessions else 0
        
        return {
            'peak_listening_hours': peak_hours,
            'peak_listening_days': peak_days,
            'hourly_distribution': hourly_counts.to_dict(),
            'daily_distribution': daily_counts.to_dict(),
            'average_session_length': round(avg_session_length, 1),
            'total_sessions': len(sessions),
            'listening_consistency': self._calculate_consistency()
        }
    
    def analyze_discovery_patterns(self) -> Dict:
        """Analyze how much new music vs repeated listening."""
        if self.data.empty:
            return {}
        
        # Track first plays and repeats
        track_counts = self.data['track_id'].value_counts()
        unique_tracks = len(track_counts)
        total_plays = len(self.data)
        
        # Discovery rate over time (new tracks per month)
        monthly_discovery = self.data.groupby([self.data['datetime'].dt.year, 
                                             self.data['datetime'].dt.month])['track_id'].nunique()
        
        # Repetition analysis
        single_plays = len(track_counts[track_counts == 1])
        heavy_rotation = len(track_counts[track_counts >= 10])
        
        # Discovery timeline
        first_plays = self.data.groupby('track_id')['datetime'].min()
        discovery_timeline = first_plays.groupby([first_plays.dt.year, 
                                                first_plays.dt.month]).size()
        
        # Convert tuple keys to strings for JSON serialization
        discovery_trend_dict = {}
        for (year, month), count in discovery_timeline.tail(12).items():
            discovery_trend_dict[f"{int(year)}-{int(month):02d}"] = int(count)
        
        return {
            'unique_tracks': unique_tracks,
            'total_plays': total_plays,
            'repeat_ratio': round((total_plays - unique_tracks) / total_plays * 100, 1),
            'discovery_ratio': round(single_plays / unique_tracks * 100, 1),
            'heavy_rotation_tracks': heavy_rotation,
            'avg_monthly_discovery': round(float(monthly_discovery.mean()), 1),
            'discovery_trend': discovery_trend_dict,
            'most_played_tracks': track_counts.head(10).to_dict()
        }
    
    def analyze_artist_patterns(self) -> Dict:
        """Analyze artist loyalty and exploration patterns."""
        if self.data.empty:
            return {}
        
        artist_counts = self.data['artist'].value_counts()
        unique_artists = len(artist_counts)
        
        # Artist loyalty metrics
        top_artists = artist_counts.head(10)
        artist_concentration = top_artists.sum() / len(self.data) * 100
        
        # Artist discovery over time
        artist_first_plays = self.data.groupby('artist')['datetime'].min()
        monthly_new_artists = artist_first_plays.groupby([artist_first_plays.dt.year,
                                                         artist_first_plays.dt.month]).size()
        
        # Loyalty vs exploration
        single_track_artists = len(artist_counts[artist_counts == 1])
        loyal_artists = len(artist_counts[artist_counts >= 20])
        
        # Convert tuple keys to strings for JSON serialization
        artist_trend_dict = {}
        for (year, month), count in monthly_new_artists.tail(12).items():
            artist_trend_dict[f"{int(year)}-{int(month):02d}"] = int(count)
        
        return {
            'unique_artists': unique_artists,
            'top_artists': top_artists.to_dict(),
            'artist_concentration': round(artist_concentration, 1),
            'exploration_ratio': round(single_track_artists / unique_artists * 100, 1),
            'loyal_artists_count': loyal_artists,
            'avg_monthly_new_artists': round(float(monthly_new_artists.mean()), 1),
            'artist_discovery_trend': artist_trend_dict
        }
    
    def analyze_genre_evolution(self) -> Dict:
        """Analyze how music taste evolved (basic analysis without external genre data)."""
        if self.data.empty:
            return {}
        
        # For now, we'll use basic heuristics until we integrate MusicBrainz
        # This is a placeholder for more sophisticated genre analysis
        
        # Analyze artist diversity over time
        yearly_diversity = {}
        for year in self.data['year'].unique():
            year_data = self.data[self.data['year'] == year]
            artist_counts = year_data['artist'].value_counts()
            
            # Simpson's diversity index
            total = len(year_data)
            diversity = 1 - sum((count/total)**2 for count in artist_counts)
            yearly_diversity[int(year)] = round(diversity, 3)  # Convert numpy int to Python int
        
        # Top artists by year
        yearly_top_artists = {}
        for year in sorted(self.data['year'].unique()):
            year_data = self.data[self.data['year'] == year]
            top_artist = year_data['artist'].value_counts().head(1)
            if not top_artist.empty:
                yearly_top_artists[int(year)] = top_artist.index[0]  # Convert numpy int to Python int
        
        return {
            'yearly_diversity_index': yearly_diversity,
            'yearly_top_artists': yearly_top_artists,
            'total_timespan_years': len(self.data['year'].unique()),
            'most_consistent_artists': self._find_consistent_artists()
        }
    
    def analyze_listening_intensity(self) -> Dict:
        """Analyze listening intensity patterns."""
        if self.data.empty:
            return {}
        
        # Daily listening counts
        daily_plays = self.data.groupby(self.data['datetime'].dt.date).size()
        
        # Weekly patterns
        weekly_plays = self.data.groupby(self.data['datetime'].dt.isocalendar().week).size()
        
        # Monthly patterns
        monthly_plays = self.data.groupby([self.data['datetime'].dt.year, 
                                         self.data['datetime'].dt.month]).size()
        
        # Intensity metrics
        daily_plays_series = daily_plays.reset_index(drop=True) if hasattr(daily_plays, 'reset_index') else daily_plays
        high_activity_days = len(daily_plays_series[daily_plays_series > daily_plays_series.quantile(0.8)])
        low_activity_days = len(daily_plays_series[daily_plays_series < daily_plays_series.quantile(0.2)])
        
        # Convert tuple keys to strings for JSON serialization
        recent_trend_dict = {}
        for (year, month), count in monthly_plays.tail(6).items():
            recent_trend_dict[f"{int(year)}-{int(month):02d}"] = int(count)
        
        return {
            'avg_daily_plays': round(float(daily_plays_series.mean()), 1),
            'max_daily_plays': int(daily_plays_series.max()),
            'avg_monthly_plays': round(float(monthly_plays.mean()), 1),
            'high_activity_days': high_activity_days,
            'low_activity_days': low_activity_days,
            'listening_variability': round(float(daily_plays_series.std()), 1),
            'most_active_month': f"{int(monthly_plays.idxmax()[0])}-{int(monthly_plays.idxmax()[1]):02d}" if not monthly_plays.empty else None,
            'recent_trend': recent_trend_dict
        }
    
    def analyze_repetition_patterns(self) -> Dict:
        """Analyze how much users repeat tracks, artists, albums."""
        if self.data.empty:
            return {}
        
        # Track repetition
        track_repeats = self.data['track_id'].value_counts()
        
        # Album repetition  
        album_repeats = self.data['album'].value_counts()
        
        # Immediate repeats (same track played within 10 minutes)
        immediate_repeats = 0
        for i in range(1, len(self.data)):
            if (self.data.iloc[i]['track_id'] == self.data.iloc[i-1]['track_id'] and
                (self.data.iloc[i]['datetime'] - self.data.iloc[i-1]['datetime']).total_seconds() < 600):
                immediate_repeats += 1
        
        return {
            'tracks_played_once': len(track_repeats[track_repeats == 1]),
            'tracks_played_10_plus': len(track_repeats[track_repeats >= 10]),
            'most_repeated_track': track_repeats.index[0] if not track_repeats.empty else None,
            'max_track_repeats': int(track_repeats.max()) if not track_repeats.empty else 0,
            'immediate_repeats': immediate_repeats,
            'repeat_tendency': round(track_repeats.mean(), 1),
            'top_repeated_albums': album_repeats.head(5).to_dict()
        }
    
    def analyze_seasonal_patterns(self) -> Dict:
        """Analyze seasonal listening patterns."""
        if self.data.empty:
            return {}
        
        # Map months to seasons
        season_map = {12: 'Winter', 1: 'Winter', 2: 'Winter',
                     3: 'Spring', 4: 'Spring', 5: 'Spring',
                     6: 'Summer', 7: 'Summer', 8: 'Summer',
                     9: 'Fall', 10: 'Fall', 11: 'Fall'}
        
        self.data['season'] = self.data['month'].map(season_map)
        
        # Seasonal listening volume
        seasonal_counts = self.data['season'].value_counts()
        
        # Seasonal artist preferences
        seasonal_top_artists = {}
        for season in ['Spring', 'Summer', 'Fall', 'Winter']:
            season_data = self.data[self.data['season'] == season]
            if not season_data.empty:
                top_artist = season_data['artist'].value_counts().head(1)
                seasonal_top_artists[season] = top_artist.index[0] if not top_artist.empty else None
        
        return {
            'seasonal_distribution': seasonal_counts.to_dict(),
            'preferred_season': seasonal_counts.index[0] if not seasonal_counts.empty else None,
            'seasonal_top_artists': seasonal_top_artists,
            'seasonal_variety': len(seasonal_counts[seasonal_counts > 0])
        }
    
    def get_summary_statistics(self) -> Dict:
        """Get overall summary statistics."""
        if self.data.empty:
            return {}
        
        date_range = (self.data['datetime'].max() - self.data['datetime'].min()).days
        
        return {
            'total_scrobbles': len(self.data),
            'unique_tracks': self.data['track_id'].nunique(),
            'unique_artists': self.data['artist'].nunique(),
            'unique_albums': self.data['album'].nunique(),
            'date_range_days': date_range,
            'first_scrobble': self.data['datetime'].min().isoformat(),
            'last_scrobble': self.data['datetime'].max().isoformat(),
            'avg_scrobbles_per_day': round(len(self.data) / max(date_range, 1), 1),
            'data_completeness': self._assess_data_completeness()
        }
    
    def _calculate_consistency(self) -> float:
        """Calculate listening consistency score (0-1)."""
        if self.data.empty:
            return 0.0
        
        daily_counts = self.data.groupby(self.data['datetime'].dt.date).size()
        cv = daily_counts.std() / daily_counts.mean() if daily_counts.mean() > 0 else 0
        consistency = max(0, 1 - cv/2)  # Convert coefficient of variation to consistency score
        return round(consistency, 3)
    
    def _find_consistent_artists(self) -> List[str]:
        """Find artists that appear consistently across years."""
        if self.data.empty:
            return []
        
        artist_years = self.data.groupby('artist')['year'].nunique()
        total_years = self.data['year'].nunique()
        
        # Artists that appear in at least 50% of years
        consistent_threshold = max(1, total_years * 0.5)
        consistent_artists = artist_years[artist_years >= consistent_threshold]
        
        return consistent_artists.index.tolist()[:10]
    
    def _assess_data_completeness(self) -> str:
        """Assess the completeness of the data."""
        if self.data.empty:
            return "No data"
        
        total_days = (self.data['datetime'].max() - self.data['datetime'].min()).days
        days_with_data = self.data['datetime'].dt.date.nunique()
        
        completeness = days_with_data / max(total_days, 1)
        
        if completeness >= 0.8:
            return "Excellent"
        elif completeness >= 0.6:
            return "Good"
        elif completeness >= 0.4:
            return "Fair"
        else:
            return "Sparse"
    
    def export_patterns(self, filepath: str):
        """Export analysis results to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.patterns, f, indent=2, default=str)
        
        logger.info(f"Patterns exported to {filepath}")
    
    def get_insights_summary(self) -> Dict[str, str]:
        """Get human-readable insights summary."""
        if not self.patterns:
            return {"error": "No analysis performed yet. Run analyze_all_patterns() first."}
        
        insights = {}
        
        # Temporal insights
        temporal = self.patterns.get('temporal', {})
        if temporal:
            peak_hour = temporal.get('peak_listening_hours', [0])[0]
            peak_day = temporal.get('peak_listening_days', ['Unknown'])[0]
            
            if 6 <= peak_hour <= 11:
                time_type = "morning person"
            elif 12 <= peak_hour <= 17:
                time_type = "afternoon listener"
            elif 18 <= peak_hour <= 22:
                time_type = "evening music lover"
            else:
                time_type = "night owl"
            
            insights['listening_personality'] = f"You're a {time_type} who loves music most on {peak_day}s"
        
        # Discovery insights
        discovery = self.patterns.get('discovery', {})
        if discovery:
            discovery_ratio = discovery.get('discovery_ratio', 0)
            if discovery_ratio > 70:
                discovery_type = "musical explorer - you love discovering new tracks"
            elif discovery_ratio > 40:
                discovery_type = "balanced listener - you mix new and familiar music"
            else:
                discovery_type = "creature of habit - you love your favorites"
            
            insights['discovery_style'] = discovery_type
        
        # Artist loyalty insights
        artist = self.patterns.get('artist_loyalty', {})
        if artist:
            exploration_ratio = artist.get('exploration_ratio', 0)
            if exploration_ratio > 60:
                insights['artist_style'] = "You're an artist explorer who samples many different musicians"
            else:
                insights['artist_style'] = "You're loyal to your favorite artists and dive deep into their catalogs"
        
        return insights
    
    def analyze_musical_phases(self) -> Dict:
        """Detect musical phases based on listening pattern changes"""
        if self.data.empty:
            return {}
        
        self.data['quarter'] = self.data['datetime'].dt.to_period('Q')
        quarterly_data = []
        
        for quarter in self.data['quarter'].unique():
            quarter_data = self.data[self.data['quarter'] == quarter]
            
            artist_diversity = quarter_data['artist'].nunique() / len(quarter_data) if len(quarter_data) > 0 else 0
            genre_diversity = quarter_data['genre'].nunique() / len(quarter_data) if 'genre' in quarter_data.columns and len(quarter_data) > 0 else 0
            listening_intensity = len(quarter_data)
            
            # Top genres distribution
            top_genres = quarter_data['genre'].value_counts().head(3).to_dict() if 'genre' in quarter_data.columns else {}
            
            quarterly_data.append({
                'quarter': str(quarter),
                'artist_diversity': round(artist_diversity, 3),
                'genre_diversity': round(genre_diversity, 3),
                'listening_intensity': listening_intensity,
                'top_genres': top_genres,
                'unique_artists': quarter_data['artist'].nunique(),
                'total_plays': len(quarter_data)
            })
        
        phases = []
        if len(quarterly_data) > 1:
            for i in range(1, len(quarterly_data)):
                prev = quarterly_data[i-1]
                curr = quarterly_data[i]
                
                diversity_change = abs(curr['artist_diversity'] - prev['artist_diversity'])
                intensity_change = abs(curr['listening_intensity'] - prev['listening_intensity']) / max(prev['listening_intensity'], 1)
                
                if diversity_change > 0.1 or intensity_change > 0.3:
                    phase_type = "Discovery" if curr['artist_diversity'] > prev['artist_diversity'] else "Consolidation"
                    if intensity_change > 0.5:
                        phase_type = "High Activity" if curr['listening_intensity'] > prev['listening_intensity'] else "Low Activity"
                    
                    phases.append({
                        'quarter': curr['quarter'],
                        'phase_type': phase_type,
                        'diversity_change': round(diversity_change, 3),
                        'intensity_change': round(intensity_change, 3)
                    })
        
        return {
            'quarterly_metrics': quarterly_data,
            'detected_phases': phases,
            'total_phases': len(phases),
            'phase_summary': self._summarize_phases(phases)
        }
    
    def _summarize_phases(self, phases: list) -> Dict:
        """Summarize detected musical phases"""
        if not phases:
            return {'dominant_pattern': 'Stable', 'phase_count': 0}
        
        phase_types = [p['phase_type'] for p in phases]
        from collections import Counter
        phase_counts = Counter(phase_types)
        
        return {
            'dominant_pattern': phase_counts.most_common(1)[0][0] if phase_counts else 'Stable',
            'phase_count': len(phases),
            'phase_distribution': dict(phase_counts)
        }
    
    def analyze_year_over_year_evolution(self) -> Dict:
        """Analyze year-over-year changes in listening patterns"""
        if self.data.empty:
            return {}
        
        self.data['year'] = self.data['datetime'].dt.year
        yearly_data = []
        
        for year in sorted(self.data['year'].unique()):
            year_data = self.data[self.data['year'] == year]
            
            metrics = {
                'year': int(year),
                'total_plays': len(year_data),
                'unique_artists': year_data['artist'].nunique(),
                'unique_tracks': year_data.drop_duplicates(['artist', 'track']).shape[0],
                'artist_diversity_index': year_data['artist'].nunique() / len(year_data) if len(year_data) > 0 else 0,
                'top_artist': year_data['artist'].value_counts().index[0] if len(year_data) > 0 else None,
                'top_artist_plays': year_data['artist'].value_counts().iloc[0] if len(year_data) > 0 else 0,
                'avg_daily_plays': len(year_data) / 365,
                'discovery_rate': len(year_data.groupby('artist')['datetime'].min()) / len(year_data) if len(year_data) > 0 else 0
            }
            
            if 'genre' in year_data.columns:
                metrics.update({
                    'unique_genres': year_data['genre'].nunique(),
                    'genre_diversity_index': year_data['genre'].nunique() / len(year_data) if len(year_data) > 0 else 0,
                    'top_genre': year_data['genre'].value_counts().index[0] if len(year_data) > 0 else None
                })
            
            yearly_data.append(metrics)
        
        evolution_trends = []
        if len(yearly_data) > 1:
            for i in range(1, len(yearly_data)):
                prev_year = yearly_data[i-1]
                curr_year = yearly_data[i]
                
                trends = {
                    'year_transition': f"{prev_year['year']}-{curr_year['year']}",
                    'plays_change': curr_year['total_plays'] - prev_year['total_plays'],
                    'plays_change_pct': ((curr_year['total_plays'] - prev_year['total_plays']) / prev_year['total_plays'] * 100) if prev_year['total_plays'] > 0 else 0,
                    'artist_diversity_change': curr_year['artist_diversity_index'] - prev_year['artist_diversity_index'],
                    'new_artists_discovered': curr_year['unique_artists'] - prev_year['unique_artists'],
                    'listening_intensity_change': curr_year['avg_daily_plays'] - prev_year['avg_daily_plays']
                }
                
                if trends['plays_change_pct'] > 10:
                    trends['trend'] = 'Increasing'
                elif trends['plays_change_pct'] < -10:
                    trends['trend'] = 'Decreasing'
                else:
                    trends['trend'] = 'Stable'
                
                evolution_trends.append(trends)
        
        return {
            'yearly_metrics': yearly_data,
            'evolution_trends': evolution_trends,
            'total_years': len(yearly_data),
            'overall_growth': self._calculate_overall_growth(yearly_data),
            'listening_evolution_summary': self._summarize_evolution(evolution_trends)
        }
    
    def _calculate_overall_growth(self, yearly_data: list) -> Dict:
        """Calculate overall growth metrics across all years"""
        if len(yearly_data) < 2:
            return {}
        
        first_year = yearly_data[0]
        last_year = yearly_data[-1]
        years_span = last_year['year'] - first_year['year']
        
        return {
            'total_plays_growth': last_year['total_plays'] - first_year['total_plays'],
            'total_plays_growth_pct': ((last_year['total_plays'] - first_year['total_plays']) / first_year['total_plays'] * 100) if first_year['total_plays'] > 0 else 0,
            'artist_diversity_evolution': last_year['artist_diversity_index'] - first_year['artist_diversity_index'],
            'years_analyzed': years_span,
            'avg_annual_growth': ((last_year['total_plays'] - first_year['total_plays']) / years_span) if years_span > 0 else 0
        }
    
    def _summarize_evolution(self, evolution_trends: list) -> Dict:
        """Summarize evolution patterns"""
        if not evolution_trends:
            return {'pattern': 'Insufficient data', 'stability': 'Unknown'}
        
        trends = [t['trend'] for t in evolution_trends]
        from collections import Counter
        trend_counts = Counter(trends)
        
        if trend_counts['Increasing'] > trend_counts['Decreasing']:
            pattern = 'Growing'
        elif trend_counts['Decreasing'] > trend_counts['Increasing']:
            pattern = 'Declining'
        else:
            pattern = 'Fluctuating'
        
        stable_years = trend_counts.get('Stable', 0)
        stability = 'High' if stable_years > len(trends) / 2 else 'Low'
        
        return {
            'pattern': pattern,
            'stability': stability,
            'trend_distribution': dict(trend_counts)
        }
    
    def analyze_yearly_evolution(self) -> Dict:
        """Analyze year-over-year changes in listening patterns."""
        if self.data.empty:
            return {}
        
        yearly_stats = {}
        years = sorted(self.data['year'].unique())
        
        for year in years:
            year_data = self.data[self.data['year'] == year]
            yearly_stats[int(year)] = {
                'total_plays': len(year_data),
                'unique_artists': year_data['artist'].nunique(),
                'unique_tracks': year_data['track_id'].nunique(),
                'avg_daily_plays': len(year_data) / 365,
                'top_artist': year_data['artist'].value_counts().index[0] if not year_data.empty else None,
                'artist_diversity': self._calculate_diversity_index(year_data['artist'])
            }
        
        yoy_changes = {}
        for i in range(1, len(years)):
            prev_year, curr_year = years[i-1], years[i]
            prev_stats, curr_stats = yearly_stats[prev_year], yearly_stats[curr_year]
            
            yoy_changes[f"{prev_year}-{curr_year}"] = {
                'plays_change': ((curr_stats['total_plays'] - prev_stats['total_plays']) / prev_stats['total_plays'] * 100) if prev_stats['total_plays'] > 0 else 0,
                'artist_change': ((curr_stats['unique_artists'] - prev_stats['unique_artists']) / prev_stats['unique_artists'] * 100) if prev_stats['unique_artists'] > 0 else 0,
                'diversity_change': curr_stats['artist_diversity'] - prev_stats['artist_diversity']
            }
        
        return {
            'yearly_stats': yearly_stats,
            'year_over_year_changes': yoy_changes,
            'musical_phases': self._detect_musical_phases()
        }
    
    def _detect_musical_phases(self) -> List[Dict]:
        """Detect distinct musical phases in listening history."""
        if self.data.empty:
            return []
        
        self.data['year_quarter'] = self.data['year'].astype(str) + '-Q' + self.data['quarter'].astype(str)
        quarterly_stats = []
        
        for quarter in sorted(self.data['year_quarter'].unique()):
            quarter_data = self.data[self.data['year_quarter'] == quarter]
            if len(quarter_data) < 10:
                continue
                
            stats = {
                'period': quarter,
                'total_plays': len(quarter_data),
                'unique_artists': quarter_data['artist'].nunique(),
                'top_genres': self._estimate_genres(quarter_data),
                'avg_session_length': self._calculate_avg_session_length(quarter_data),
                'discovery_rate': len(quarter_data.drop_duplicates('track_id')) / len(quarter_data)
            }
            quarterly_stats.append(stats)
        
        phases = []
        current_phase = None
        
        for i, stats in enumerate(quarterly_stats):
            if i == 0:
                current_phase = {
                    'start_period': stats['period'],
                    'characteristics': stats,
                    'periods': [stats['period']]
                }
            else:
                prev_stats = quarterly_stats[i-1]
                plays_change = abs(stats['total_plays'] - prev_stats['total_plays']) / prev_stats['total_plays'] if prev_stats['total_plays'] > 0 else 0
                discovery_change = abs(stats['discovery_rate'] - prev_stats['discovery_rate'])
                
                if plays_change > 0.5 or discovery_change > 0.3:
                    current_phase['end_period'] = prev_stats['period']
                    phases.append(current_phase)
                    
                    current_phase = {
                        'start_period': stats['period'],
                        'characteristics': stats,
                        'periods': [stats['period']]
                    }
                else:
                    current_phase['periods'].append(stats['period'])
        
        if current_phase:
            current_phase['end_period'] = quarterly_stats[-1]['period']
            phases.append(current_phase)
        
        return phases
    
    def _calculate_diversity_index(self, series) -> float:
        """Calculate Simpson's diversity index."""
        counts = series.value_counts()
        total = len(series)
        return 1 - sum((count/total)**2 for count in counts) if total > 0 else 0
    
    def _estimate_genres(self, data) -> List[str]:
        """Estimate genres based on artist patterns (placeholder)."""
        top_artists = data['artist'].value_counts().head(3).index.tolist()
        return top_artists
    
    def _calculate_avg_session_length(self, data) -> float:
        """Calculate average session length for given data."""
        sessions = []
        current_session = []
        
        for i, row in data.iterrows():
            if not current_session:
                current_session = [row['datetime']]
            else:
                time_diff = (row['datetime'] - current_session[-1]).total_seconds() / 3600
                if time_diff > 1:
                    sessions.append(len(current_session))
                    current_session = [row['datetime']]
                else:
                    current_session.append(row['datetime'])
        
        if current_session:
            sessions.append(len(current_session))
        
        return np.mean(sessions) if sessions else 0       