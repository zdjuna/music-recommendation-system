#!/usr/bin/env python3
"""
Smart Recommendation Generator
Generate intelligent recommendations from complete music library analysis
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from datetime import datetime
from typing import List, Dict, Any
import json

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SmartRecommendationEngine:
    """Generate smart recommendations using complete library analysis"""
    
    def __init__(self, dataset_path: str = 'data/zdjuna_unique_tracks_analysis_ULTIMATE.csv'):
        self.dataset_path = dataset_path
        self.df = None
        self.scrobbles_df = None
        self.load_data()
        
    def load_data(self):
        """Load the ultimate dataset and scrobbles"""
        logger.info("📂 Loading ultimate dataset...")
        self.df = pd.read_csv(self.dataset_path)
        logger.info(f"✅ Loaded {len(self.df):,} tracks with analysis")
        
        # Load scrobbles for play count information
        scrobbles_path = 'data/zdjuna_scrobbles.csv'
        if Path(scrobbles_path).exists():
            self.scrobbles_df = pd.read_csv(scrobbles_path)
            logger.info(f"✅ Loaded {len(self.scrobbles_df):,} scrobbles for play patterns")
            
            # Add play count information
            play_counts = self.scrobbles_df.groupby(['artist', 'track']).size().reset_index(name='play_count')
            self.df = self.df.merge(play_counts, on=['artist', 'track'], how='left')
            self.df['play_count'] = self.df['play_count'].fillna(0)
        else:
            logger.warning("⚠️  Scrobbles file not found, recommendations without play counts")
            self.df['play_count'] = 0
    
    def get_mood_recommendations(self, mood: str, count: int = 20) -> List[Dict[str, Any]]:
        """Get recommendations based on mood preference"""
        logger.info(f"🎭 Generating {mood} mood recommendations...")
        
        # Filter by mood
        if hasattr(self.df, 'mood_primary_mood'):
            mood_tracks = self.df[self.df['mood_primary_mood'].str.contains(mood, case=False, na=False)]
        else:
            # Fallback to energy-based mood matching
            if mood.lower() in ['happy', 'energetic', 'upbeat']:
                mood_tracks = self.df[self.df['audio_energy'] > 0.6]
            elif mood.lower() in ['calm', 'peaceful', 'chill']:
                mood_tracks = self.df[self.df['audio_energy'] < 0.4]
            else:
                mood_tracks = self.df.copy()
        
        # Sort by combination of mood match and play count
        if len(mood_tracks) > 0:
            mood_tracks = mood_tracks.nlargest(count * 3, 'play_count')  # Get more than needed
            recommendations = mood_tracks.sample(min(count, len(mood_tracks))).to_dict('records')
        else:
            # Fallback to popular tracks
            recommendations = self.df.nlargest(count, 'play_count').to_dict('records')
        
        return recommendations[:count]
    
    def get_energy_recommendations(self, energy_level: str, count: int = 20) -> List[Dict[str, Any]]:
        """Get recommendations based on energy level"""
        logger.info(f"⚡ Generating {energy_level} energy recommendations...")
        
        if energy_level == 'high':
            energy_tracks = self.df[self.df['audio_energy'] > 0.7]
        elif energy_level == 'low':
            energy_tracks = self.df[self.df['audio_energy'] < 0.3]
        else:  # medium
            energy_tracks = self.df[(self.df['audio_energy'] >= 0.3) & (self.df['audio_energy'] <= 0.7)]
        
        # Sort by play count and variety
        if len(energy_tracks) > 0:
            recommendations = energy_tracks.nlargest(count * 2, 'play_count').sample(
                min(count, len(energy_tracks))
            ).to_dict('records')
        else:
            recommendations = self.df.nlargest(count, 'play_count').to_dict('records')
        
        return recommendations[:count]
    
    def get_discovery_recommendations(self, count: int = 20) -> List[Dict[str, Any]]:
        """Get discovery recommendations - tracks you rarely play but might like"""
        logger.info(f"🔍 Generating discovery recommendations...")
        
        # Find tracks with low play count but good features
        discovery_tracks = self.df[self.df['play_count'] <= 2].copy()
        
        if len(discovery_tracks) > 0:
            # Prioritize tracks with interesting features
            if 'audio_valence' in discovery_tracks.columns:
                discovery_tracks['discovery_score'] = (
                    discovery_tracks['audio_valence'] * 0.3 +
                    discovery_tracks['audio_energy'] * 0.3 +
                    discovery_tracks['audio_danceability'] * 0.2 +
                    (1 - discovery_tracks['play_count'] / discovery_tracks['play_count'].max()) * 0.2
                )
                recommendations = discovery_tracks.nlargest(count, 'discovery_score').to_dict('records')
            else:
                recommendations = discovery_tracks.sample(min(count, len(discovery_tracks))).to_dict('records')
        else:
            # Fallback to medium-played tracks
            recommendations = self.df[
                self.df['play_count'].between(1, 5)
            ].sample(min(count, len(self.df))).to_dict('records')
        
        return recommendations[:count]
    
    def get_artist_deep_dive(self, artist: str, count: int = 15) -> List[Dict[str, Any]]:
        """Get deep dive recommendations for a specific artist"""
        logger.info(f"🎤 Generating deep dive for: {artist}")
        
        artist_tracks = self.df[
            self.df['artist'].str.contains(artist, case=False, na=False)
        ]
        
        if len(artist_tracks) > 0:
            # Sort by play count and variety
            recommendations = artist_tracks.nlargest(count * 2, 'play_count').sample(
                min(count, len(artist_tracks))
            ).to_dict('records')
        else:
            return []
        
        return recommendations[:count]
    
    def get_tempo_workout_playlist(self, target_bpm: int = 120, bpm_range: int = 20, count: int = 25) -> List[Dict[str, Any]]:
        """Generate workout playlist with specific tempo range"""
        logger.info(f"🏃 Generating workout playlist around {target_bpm} BPM...")
        
        tempo_tracks = self.df[
            (self.df['audio_tempo'] >= target_bpm - bpm_range) &
            (self.df['audio_tempo'] <= target_bpm + bpm_range) &
            (self.df['audio_energy'] > 0.5)  # High energy for workout
        ]
        
        if len(tempo_tracks) > 0:
            recommendations = tempo_tracks.nlargest(count * 2, 'play_count').sample(
                min(count, len(tempo_tracks))
            ).to_dict('records')
        else:
            # Fallback to high energy tracks
            recommendations = self.df[self.df['audio_energy'] > 0.7].nlargest(count, 'play_count').to_dict('records')
        
        return recommendations[:count]
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive recommendations report"""
        logger.info("📊 Generating comprehensive recommendations report...")
        
        report = {
            'generation_date': datetime.now().isoformat(),
            'library_stats': {
                'total_tracks': len(self.df),
                'real_analysis_tracks': len(self.df[self.df.get('data_quality', '') == 'real_analysis']),
                'fallback_tracks': len(self.df[self.df.get('data_quality', '') == 'fallback_neutral']),
                'total_plays': self.df['play_count'].sum(),
                'most_played_track': self.df.nlargest(1, 'play_count')[['artist', 'track', 'play_count']].to_dict('records')[0]
            },
            'recommendations': {
                'happy_mood': self.get_mood_recommendations('happy', 10),
                'calm_mood': self.get_mood_recommendations('calm', 10),
                'high_energy': self.get_energy_recommendations('high', 10),
                'low_energy': self.get_energy_recommendations('low', 10),
                'discovery': self.get_discovery_recommendations(15),
                'workout_playlist': self.get_tempo_workout_playlist(128, 15, 20)
            },
            'insights': self.generate_insights()
        }
        
        return report
    
    def generate_insights(self) -> Dict[str, Any]:
        """Generate insights about the music library"""
        insights = {}
        
        # Play pattern insights
        insights['most_played_artists'] = self.df.groupby('artist')['play_count'].sum().nlargest(10).to_dict()
        
        # Audio feature insights (if available)
        if 'audio_valence' in self.df.columns:
            insights['average_valence'] = float(self.df['audio_valence'].mean())
            insights['average_energy'] = float(self.df['audio_energy'].mean())
            insights['average_tempo'] = float(self.df['audio_tempo'].mean())
        
        # Data quality insights
        insights['analysis_quality'] = {
            'real_analysis_percentage': len(self.df[self.df.get('data_quality', '') == 'real_analysis']) / len(self.df) * 100,
            'fallback_percentage': len(self.df[self.df.get('data_quality', '') == 'fallback_neutral']) / len(self.df) * 100
        }
        
        return insights
    
    def save_recommendations(self, report: Dict[str, Any], output_file: str = 'recommendations_complete.json'):
        """Save recommendations to file"""
        logger.info(f"💾 Saving recommendations to {output_file}")
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"✅ Recommendations saved")

def main():
    print("🎯 SMART RECOMMENDATION GENERATOR")
    print("="*60)
    print("🎵 Generating intelligent recommendations from your complete library")
    print()
    
    # Initialize engine
    engine = SmartRecommendationEngine()
    
    print(f"📊 Library Overview:")
    print(f"   • Total tracks: {len(engine.df):,}")
    print(f"   • Real analysis: {len(engine.df[engine.df.get('data_quality', '') == 'real_analysis']):,}")
    print(f"   • Total scrobbles: {engine.df['play_count'].sum():,}")
    print()
    
    # Generate comprehensive report
    print("🚀 Generating comprehensive recommendations...")
    report = engine.generate_comprehensive_report()
    
    # Save recommendations
    engine.save_recommendations(report)
    
    # Display sample recommendations
    print("\n🎭 SAMPLE RECOMMENDATIONS:")
    print("\n😊 Happy Mood (Top 5):")
    for i, track in enumerate(report['recommendations']['happy_mood'][:5], 1):
        print(f"   {i}. {track['artist']} - {track['track']} ({track['play_count']} plays)")
    
    print("\n⚡ High Energy (Top 5):")
    for i, track in enumerate(report['recommendations']['high_energy'][:5], 1):
        print(f"   {i}. {track['artist']} - {track['track']} ({track['play_count']} plays)")
    
    print("\n🔍 Discovery Tracks (Top 5):")
    for i, track in enumerate(report['recommendations']['discovery'][:5], 1):
        print(f"   {i}. {track['artist']} - {track['track']} ({track['play_count']} plays)")
    
    print(f"\n📊 INSIGHTS:")
    insights = report['insights']
    print(f"   • Most played artist: {list(insights['most_played_artists'].keys())[0]} ({list(insights['most_played_artists'].values())[0]:,} plays)")
    if 'average_valence' in insights:
        print(f"   • Average happiness (valence): {insights['average_valence']:.2f}")
        print(f"   • Average energy: {insights['average_energy']:.2f}")
        print(f"   • Average tempo: {insights['average_tempo']:.0f} BPM")
    
    print(f"\n✅ Complete recommendations saved to recommendations_complete.json")
    print(f"🎉 Ready to explore your music with full library coverage!")

if __name__ == "__main__":
    main()
