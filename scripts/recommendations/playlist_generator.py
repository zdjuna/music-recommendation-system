#!/usr/bin/env python3
"""
Smart Recommendation Rebuilder - Phase 6
Automatically optimizes recommendations based on expanded coverage
"""

import pandas as pd
import numpy as np
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SmartRecommendationEngine:
    """Advanced recommendation engine optimized for larger datasets"""
    
    def __init__(self, min_coverage_threshold: int = 100):
        self.min_coverage_threshold = min_coverage_threshold
        self.features_df = None
        self.scaler = StandardScaler()
        self.feature_columns = ['tempo', 'danceability', 'valence', 'energy']
        
    def load_data(self) -> bool:
        """Load and validate audio features data"""
        try:
            self.features_df = pd.read_csv('data/real_audio_features.csv')
            logger.info(f"Loaded {len(self.features_df)} tracks with audio features")
            
            if len(self.features_df) < self.min_coverage_threshold:
                logger.warning(f"Coverage below threshold ({len(self.features_df)} < {self.min_coverage_threshold})")
                return False
            
            # Validate feature columns
            missing_cols = [col for col in self.feature_columns if col not in self.features_df.columns]
            if missing_cols:
                logger.error(f"Missing feature columns: {missing_cols}")
                return False
            
            return True
            
        except FileNotFoundError:
            logger.error("Audio features file not found")
            return False
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return False
    
    def create_advanced_clusters(self, n_clusters: int = None) -> Dict[str, List[Dict]]:
        """Create smart audio clusters based on expanded data"""
        if self.features_df is None:
            return {}
        
        # Auto-determine optimal cluster count based on data size
        if n_clusters is None:
            data_size = len(self.features_df)
            if data_size < 100:
                n_clusters = 4
            elif data_size < 300:
                n_clusters = 6
            elif data_size < 500:
                n_clusters = 8
            else:
                n_clusters = 10
        
        logger.info(f"Creating {n_clusters} smart clusters from {len(self.features_df)} tracks")
        
        # Prepare features for clustering
        feature_data = self.features_df[self.feature_columns].fillna(0)
        scaled_features = self.scaler.fit_transform(feature_data)
        
        # Perform clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(scaled_features)
        
        # Create cluster playlists
        clusters = {}
        for cluster_id in range(n_clusters):
            cluster_tracks = self.features_df[cluster_labels == cluster_id]
            
            if len(cluster_tracks) == 0:
                continue
            
            # Analyze cluster characteristics
            cluster_name, cluster_description = self._analyze_cluster_characteristics(cluster_tracks)
            
            # Sort by play count and create playlist
            top_tracks = cluster_tracks.nlargest(min(25, len(cluster_tracks)), 'play_count')
            
            playlist = {
                'name': cluster_name,
                'description': cluster_description,
                'tracks': [
                    {
                        'artist': row['artist'],
                        'track': row['track'],
                        'play_count': int(row['play_count']),
                        'tempo': float(row['tempo']),
                        'energy': float(row['energy']),
                        'valence': float(row['valence']),
                        'danceability': float(row['danceability'])
                    }
                    for _, row in top_tracks.iterrows()
                ],
                'total_tracks': len(top_tracks),
                'avg_tempo': float(cluster_tracks['tempo'].mean()),
                'avg_energy': float(cluster_tracks['energy'].mean()),
                'avg_valence': float(cluster_tracks['valence'].mean()),
                'cluster_size': len(cluster_tracks)
            }
            
            clusters[f"smart_cluster_{cluster_id + 1}"] = [playlist]
        
        return clusters
    
    def _analyze_cluster_characteristics(self, cluster_tracks: pd.DataFrame) -> tuple:
        """Analyze cluster to determine meaningful name and description"""
        avg_tempo = cluster_tracks['tempo'].mean()
        avg_energy = cluster_tracks['energy'].mean()
        avg_valence = cluster_tracks['valence'].mean()
        avg_danceability = cluster_tracks['danceability'].mean()
        
        # Determine cluster name based on characteristics
        if avg_energy > 0.7 and avg_tempo > 130:
            name = "🔥 High Energy Bangers"
            description = "Intense, high-energy tracks perfect for workouts and pumping up"
        elif avg_danceability > 0.8 and avg_valence > 0.6:
            name = "💃 Dance Floor Favorites"
            description = "Infectious, danceable tracks that make you move"
        elif avg_valence > 0.7 and avg_energy < 0.5:
            name = "☀️ Feel-Good Vibes"
            description = "Uplifting, positive tracks that brighten your mood"
        elif avg_tempo < 100 and avg_energy < 0.4:
            name = "🌙 Chill & Relax"
            description = "Mellow, low-tempo tracks for relaxation and focus"
        elif avg_valence < 0.4 and avg_energy > 0.5:
            name = "🎭 Intense & Moody"
            description = "Emotionally complex tracks with depth and intensity"
        elif avg_tempo > 140 and avg_danceability > 0.6:
            name = "⚡ Electronic Energy"
            description = "Fast-paced electronic and dance-oriented tracks"
        else:
            name = "🎵 Signature Sound"
            description = "A distinctive collection showcasing your unique taste"
        
        return name, description
    
    def create_enhanced_similarity_playlists(self, top_n: int = 10) -> Dict[str, List[Dict]]:
        """Create similarity playlists for top tracks"""
        if self.features_df is None:
            return {}
        
        # Get top played tracks
        top_tracks = self.features_df.nlargest(top_n, 'play_count')
        
        playlists = {}
        feature_data = self.features_df[self.feature_columns].fillna(0)
        scaled_features = self.scaler.fit_transform(feature_data)
        
        for idx, target_track in top_tracks.iterrows():
            target_features = scaled_features[idx].reshape(1, -1)
            similarities = cosine_similarity(target_features, scaled_features)[0]
            
            # Get most similar tracks (excluding the target track itself)
            similar_indices = np.argsort(similarities)[::-1][1:21]  # Top 20 similar tracks
            similar_tracks = self.features_df.iloc[similar_indices]
            
            playlist_name = f"similar_to_{target_track['artist'].replace(' ', '_').lower()}"
            playlist = {
                'name': f"🎯 Similar to {target_track['artist']} - {target_track['track']}",
                'description': f"Tracks with similar audio characteristics to this {target_track['play_count']}-play favorite",
                'tracks': [
                    {
                        'artist': row['artist'],
                        'track': row['track'],
                        'play_count': int(row['play_count']),
                        'similarity_score': float(similarities[similar_indices[i]]),
                        'tempo': float(row['tempo']),
                        'energy': float(row['energy']),
                        'valence': float(row['valence'])
                    }
                    for i, (_, row) in enumerate(similar_tracks.iterrows())
                ],
                'target_track': {
                    'artist': target_track['artist'],
                    'track': target_track['track'],
                    'play_count': int(target_track['play_count'])
                },
                'total_tracks': len(similar_tracks)
            }
            
            playlists[playlist_name] = [playlist]
        
        return playlists
    
    def create_discovery_playlists(self) -> Dict[str, List[Dict]]:
        """Create enhanced discovery playlists"""
        if self.features_df is None:
            return {}
        
        playlists = {}
        
        # 1. Hidden Gems - Low play count but good features
        hidden_gems = self.features_df[
            (self.features_df['play_count'] >= 5) & 
            (self.features_df['play_count'] <= 25)
        ].sample(min(30, len(self.features_df[self.features_df['play_count'] <= 25])))
        
        if len(hidden_gems) > 0:
            playlists['hidden_gems'] = [{
                'name': '💎 Hidden Gems',
                'description': 'Underappreciated tracks from your library worth rediscovering',
                'tracks': [
                    {
                        'artist': row['artist'],
                        'track': row['track'],
                        'play_count': int(row['play_count']),
                        'energy': float(row['energy']),
                        'valence': float(row['valence'])
                    }
                    for _, row in hidden_gems.iterrows()
                ],
                'total_tracks': len(hidden_gems)
            }]
        
        # 2. Tempo Journey - Tracks across tempo spectrum
        tempo_sorted = self.features_df.sort_values('tempo')
        tempo_journey = pd.concat([
            tempo_sorted.head(8),  # Slowest
            tempo_sorted.iloc[len(tempo_sorted)//4:len(tempo_sorted)//4 + 8],  # Mid-slow
            tempo_sorted.iloc[len(tempo_sorted)//2:len(tempo_sorted)//2 + 8],  # Mid
            tempo_sorted.tail(8)   # Fastest
        ]).drop_duplicates()
        
        if len(tempo_journey) > 0:
            playlists['tempo_journey'] = [{
                'name': '🎼 Tempo Journey',
                'description': 'A musical journey from your slowest to fastest tracks',
                'tracks': [
                    {
                        'artist': row['artist'],
                        'track': row['track'],
                        'tempo': float(row['tempo']),
                        'play_count': int(row['play_count'])
                    }
                    for _, row in tempo_journey.iterrows()
                ],
                'total_tracks': len(tempo_journey)
            }]
        
        # 3. Emotional Range - Valence spectrum
        valence_sorted = self.features_df.sort_values('valence')
        emotional_range = pd.concat([
            valence_sorted.head(10),  # Most negative
            valence_sorted.tail(10)   # Most positive
        ]).drop_duplicates()
        
        if len(emotional_range) > 0:
            playlists['emotional_range'] = [{
                'name': '🎭 Emotional Range',
                'description': 'From your most melancholic to most uplifting tracks',
                'tracks': [
                    {
                        'artist': row['artist'],
                        'track': row['track'],
                        'valence': float(row['valence']),
                        'play_count': int(row['play_count'])
                    }
                    for _, row in emotional_range.iterrows()
                ],
                'total_tracks': len(emotional_range)
            }]
        
        return playlists
    
    def create_context_playlists(self) -> Dict[str, List[Dict]]:
        """Create enhanced context-aware playlists"""
        if self.features_df is None:
            return {}
        
        playlists = {}
        
        # 1. Deep Focus - Low energy, moderate valence, consistent tempo
        focus_tracks = self.features_df[
            (self.features_df['energy'] <= 0.5) &
            (self.features_df['valence'] >= 0.3) &
            (self.features_df['valence'] <= 0.7) &
            (self.features_df['tempo'] >= 80) &
            (self.features_df['tempo'] <= 130)
        ].nlargest(25, 'play_count')
        
        if len(focus_tracks) > 0:
            playlists['deep_focus'] = [{
                'name': '🎯 Deep Focus',
                'description': 'Carefully selected tracks for concentration and productivity',
                'tracks': [
                    {
                        'artist': row['artist'],
                        'track': row['track'],
                        'play_count': int(row['play_count']),
                        'energy': float(row['energy']),
                        'tempo': float(row['tempo'])
                    }
                    for _, row in focus_tracks.iterrows()
                ],
                'total_tracks': len(focus_tracks),
                'avg_energy': float(focus_tracks['energy'].mean()),
                'avg_tempo': float(focus_tracks['tempo'].mean())
            }]
        
        # 2. Workout Intensity - High energy, fast tempo
        workout_tracks = self.features_df[
            (self.features_df['energy'] >= 0.6) &
            (self.features_df['tempo'] >= 120) &
            (self.features_df['danceability'] >= 0.5)
        ].nlargest(25, 'play_count')
        
        if len(workout_tracks) > 0:
            playlists['workout_intensity'] = [{
                'name': '💪 Workout Intensity',
                'description': 'High-energy tracks to fuel your workout sessions',
                'tracks': [
                    {
                        'artist': row['artist'],
                        'track': row['track'],
                        'play_count': int(row['play_count']),
                        'energy': float(row['energy']),
                        'tempo': float(row['tempo']),
                        'danceability': float(row['danceability'])
                    }
                    for _, row in workout_tracks.iterrows()
                ],
                'total_tracks': len(workout_tracks),
                'avg_energy': float(workout_tracks['energy'].mean()),
                'avg_tempo': float(workout_tracks['tempo'].mean())
            }]
        
        # 3. Evening Wind Down - Low energy, positive valence, slow tempo
        winddown_tracks = self.features_df[
            (self.features_df['energy'] <= 0.4) &
            (self.features_df['valence'] >= 0.4) &
            (self.features_df['tempo'] <= 110)
        ].nlargest(20, 'play_count')
        
        if len(winddown_tracks) > 0:
            playlists['evening_winddown'] = [{
                'name': '🌅 Evening Wind Down',
                'description': 'Gentle, soothing tracks for relaxation and reflection',
                'tracks': [
                    {
                        'artist': row['artist'],
                        'track': row['track'],
                        'play_count': int(row['play_count']),
                        'energy': float(row['energy']),
                        'valence': float(row['valence']),
                        'tempo': float(row['tempo'])
                    }
                    for _, row in winddown_tracks.iterrows()
                ],
                'total_tracks': len(winddown_tracks)
            }]
        
        return playlists
    
    def generate_smart_recommendations(self) -> Dict[str, Any]:
        """Generate comprehensive smart recommendations"""
        if not self.load_data():
            return {'error': 'Failed to load data or insufficient coverage'}
        
        logger.info("🧠 Generating smart recommendations with expanded coverage...")
        
        recommendations = {
            'metadata': {
                'total_tracks_analyzed': len(self.features_df),
                'generation_method': 'smart_enhanced',
                'feature_columns': self.feature_columns,
                'coverage_level': self._determine_coverage_level(),
                'timestamp': pd.Timestamp.now().isoformat()
            },
            'playlists': {}
        }
        
        # Generate different types of playlists
        logger.info("Creating smart clusters...")
        clusters = self.create_advanced_clusters()
        recommendations['playlists'].update(clusters)
        
        logger.info("Creating similarity playlists...")
        similarity_playlists = self.create_enhanced_similarity_playlists()
        recommendations['playlists'].update(similarity_playlists)
        
        logger.info("Creating discovery playlists...")
        discovery_playlists = self.create_discovery_playlists()
        recommendations['playlists'].update(discovery_playlists)
        
        logger.info("Creating context playlists...")
        context_playlists = self.create_context_playlists()
        recommendations['playlists'].update(context_playlists)
        
        # Add summary statistics
        total_playlists = sum(len(playlists) for playlists in recommendations['playlists'].values())
        recommendations['metadata']['total_playlists'] = total_playlists
        
        logger.info(f"✅ Generated {total_playlists} smart playlists")
        
        return recommendations
    
    def _determine_coverage_level(self) -> str:
        """Determine coverage level based on data size"""
        if self.features_df is None:
            return 'none'
        
        size = len(self.features_df)
        if size < 100:
            return 'basic'
        elif size < 300:
            return 'good'
        elif size < 500:
            return 'excellent'
        else:
            return 'exceptional'
    
    def save_recommendations(self, recommendations: Dict[str, Any], filename: str = 'recommendations_smart_enhanced.json'):
        """Save recommendations to file"""
        try:
            with open(filename, 'w') as f:
                json.dump(recommendations, f, indent=2)
            logger.info(f"💾 Saved recommendations to {filename}")
            return True
        except Exception as e:
            logger.error(f"Error saving recommendations: {e}")
            return False


def main():
    """Main execution"""
    print("🧠 Smart Recommendation Rebuilder - Phase 6")
    print("="*50)
    
    engine = SmartRecommendationEngine()
    
    # Check current coverage
    if engine.load_data():
        coverage_level = engine._determine_coverage_level()
        track_count = len(engine.features_df)
        
        print(f"📊 Current Coverage: {track_count} tracks ({coverage_level} level)")
        
        if track_count < engine.min_coverage_threshold:
            print(f"⚠️  Coverage below recommended threshold ({track_count} < {engine.min_coverage_threshold})")
            print("Consider running mass coverage expansion first.")
            return
        
        print(f"\n🚀 Generating smart recommendations...")
        
        recommendations = engine.generate_smart_recommendations()
        
        if 'error' in recommendations:
            print(f"❌ Error: {recommendations['error']}")
            return
        
        # Save recommendations
        filename = 'recommendations_smart_enhanced.json'
        if engine.save_recommendations(recommendations, filename):
            print(f"\n✅ Smart recommendations generated successfully!")
            print(f"   File: {filename}")
            print(f"   Playlists: {recommendations['metadata']['total_playlists']}")
            print(f"   Coverage level: {recommendations['metadata']['coverage_level']}")
            print(f"\n🎉 Your recommendation system is now powered by advanced AI!")
        
    else:
        print("❌ Could not load audio features data.")
        print("Run coverage expansion first to generate recommendations.")


if __name__ == "__main__":
    main()
