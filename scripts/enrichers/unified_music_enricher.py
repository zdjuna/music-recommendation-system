#!/usr/bin/env python3
"""
Unified Music Enricher - Combines all data sources for comprehensive analysis
Priority: Cyanite > AcousticBrainz > MusicBrainz > Existing Data
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from typing import Dict, Optional, List, Tuple
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UnifiedMusicEnricher:
    """
    Combines multiple data sources for comprehensive music analysis:
    1. Cyanite.ai - Professional mood and audio analysis
    2. AcousticBrainz - Free audio features (BPM, key, etc.)
    3. MusicBrainz - Metadata and tags
    4. Existing enriched data
    """
    
    def __init__(self):
        self.data_dir = Path('data')
        self.cache_dir = Path('cache')
        self.enriched_data = self._load_all_enriched_data()
        logger.info(f"Loaded {len(self.enriched_data)} tracks with enrichment data")
        
    def _load_all_enriched_data(self) -> pd.DataFrame:
        """Load and combine all existing enriched data"""
        enriched_dfs = []
        
        # Load Cyanite data (highest priority)
        cyanite_files = [
            'zdjuna_unique_tracks_analysis_ULTIMATE.csv',
            'zdjuna_unique_tracks_analysis_COMPREHENSIVE_32759.csv',
            'zdjuna_cyanite_improved_test_20_tracks.csv'
        ]
        
        for file in cyanite_files:
            path = self.data_dir / file
            if path.exists():
                logger.info(f"Loading Cyanite data from {file}")
                df = pd.read_csv(path)
                df['enrichment_source'] = 'cyanite'
                df['enrichment_priority'] = 1
                enriched_dfs.append(df)
        
        # Load AcousticBrainz data
        acousticbrainz_files = list(self.data_dir.glob('*acousticbrainz_enriched*.csv'))
        for file in acousticbrainz_files:
            logger.info(f"Loading AcousticBrainz data from {file.name}")
            df = pd.read_csv(file)
            # Only keep tracks with actual features
            if 'bpm' in df.columns:
                df = df[df['bpm'].notna()]
                df['enrichment_source'] = 'acousticbrainz'
                df['enrichment_priority'] = 2
                enriched_dfs.append(df)
        
        # Load any other enriched data
        other_enriched = ['zdjuna_enriched.csv', 'real_audio_features.csv']
        for file in other_enriched:
            path = self.data_dir / file
            if path.exists():
                logger.info(f"Loading enriched data from {file}")
                df = pd.read_csv(path)
                df['enrichment_source'] = 'other'
                df['enrichment_priority'] = 3
                enriched_dfs.append(df)
        
        if enriched_dfs:
            # Combine all data
            combined = pd.concat(enriched_dfs, ignore_index=True)
            
            # Remove duplicates, keeping highest priority
            combined = combined.sort_values('enrichment_priority')
            combined = combined.drop_duplicates(subset=['artist', 'track'], keep='first')
            
            return combined
        else:
            return pd.DataFrame()
    
    def get_track_features(self, artist: str, track: str) -> Dict:
        """Get best available features for a track"""
        # Search in enriched data
        mask = (self.enriched_data['artist'].str.lower() == artist.lower()) & \
               (self.enriched_data['track'].str.lower() == track.lower())
        
        matches = self.enriched_data[mask]
        
        if len(matches) > 0:
            # Get the best match (highest priority)
            best_match = matches.iloc[0]
            return self._extract_features(best_match)
        
        return {}
    
    def _extract_features(self, row: pd.Series) -> Dict:
        """Extract and normalize features from different sources"""
        features = {
            'artist': row.get('artist'),
            'track': row.get('track'),
            'enrichment_source': row.get('enrichment_source', 'unknown')
        }
        
        # Audio features (normalize names across sources)
        audio_mappings = {
            # Cyanite/Spotify style -> Normalized
            'valence': 'valence',
            'energy': 'energy',
            'energy_level': 'energy',  # Cyanite uses energy_level
            'danceability': 'danceability',
            'tempo': 'tempo',
            'bpm': 'tempo',  # AcousticBrainz uses bpm
            'loudness': 'loudness',
            'average_loudness': 'loudness',
            'acousticness': 'acousticness',
            'acoustic': 'acousticness',
            'instrumentalness': 'instrumentalness',
            'instrumental': 'instrumentalness',
            'speechiness': 'speechiness',
            'liveness': 'liveness'
        }
        
        for source_col, target_col in audio_mappings.items():
            if source_col in row and pd.notna(row[source_col]):
                features[target_col] = float(row[source_col])
        
        # Normalize energy levels from text to numeric
        if 'energy_level' in row and isinstance(row['energy_level'], str):
            energy_map = {'low': 0.3, 'medium': 0.5, 'high': 0.7, 'very high': 0.9}
            features['energy'] = energy_map.get(row['energy_level'].lower(), 0.5)
        
        # Key and mode
        if 'key' in row and pd.notna(row['key']):
            features['key'] = row['key']
        if 'mode' in row and pd.notna(row['mode']):
            features['mode'] = row['mode']
        elif 'scale' in row and pd.notna(row['scale']):
            features['mode'] = 1 if row['scale'] == 'major' else 0
        
        # Mood features
        mood_cols = ['mood_primary', 'primary_mood', 'mood', 'mood_quadrant']
        for col in mood_cols:
            if col in row and pd.notna(row[col]):
                features['primary_mood'] = row[col]
                break
        
        # Genre/tags
        if 'lastfm_tags' in row and pd.notna(row['lastfm_tags']):
            features['tags'] = row['lastfm_tags']
        elif 'genre' in row and pd.notna(row['genre']):
            features['tags'] = row['genre']
        
        # Additional Cyanite features
        if 'mood_aggressive' in row:
            features['mood_aggressive'] = float(row['mood_aggressive'])
        if 'mood_happy' in row:
            features['mood_happy'] = float(row['mood_happy'])
        if 'mood_sad' in row:
            features['mood_sad'] = float(row['mood_sad'])
        if 'mood_relaxed' in row:
            features['mood_relaxed'] = float(row['mood_relaxed'])
        
        return features
    
    def enrich_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Enrich an entire dataframe with best available features"""
        logger.info(f"Enriching dataframe with {len(df)} rows")
        
        # Get unique tracks
        unique_tracks = df[['artist', 'track']].drop_duplicates()
        logger.info(f"Found {len(unique_tracks)} unique tracks")
        
        # Enrich each unique track
        enriched_features = []
        for _, row in unique_tracks.iterrows():
            features = self.get_track_features(row['artist'], row['track'])
            if features:
                enriched_features.append(features)
        
        if enriched_features:
            # Create enriched dataframe
            enriched_df = pd.DataFrame(enriched_features)
            
            # Merge with original
            result = df.merge(
                enriched_df, 
                on=['artist', 'track'], 
                how='left',
                suffixes=('', '_enriched')
            )
            
            # Add enrichment stats
            result['has_audio_features'] = result['tempo'].notna() | result['energy'].notna()
            result['has_mood_data'] = result['primary_mood'].notna()
            
            # Log statistics
            total = len(result)
            with_features = result['has_audio_features'].sum()
            with_mood = result['has_mood_data'].sum()
            
            logger.info(f"Enrichment complete:")
            logger.info(f"  - Total tracks: {total}")
            logger.info(f"  - With audio features: {with_features} ({with_features/total*100:.1f}%)")
            logger.info(f"  - With mood data: {with_mood} ({with_mood/total*100:.1f}%)")
            
            # Source breakdown
            if 'enrichment_source' in result.columns:
                source_counts = result['enrichment_source'].value_counts()
                logger.info("  - Sources:")
                for source, count in source_counts.items():
                    if pd.notna(source):
                        logger.info(f"    - {source}: {count} tracks")
            
            return result
        else:
            logger.warning("No enrichment data found")
            return df
    
    def get_enrichment_summary(self) -> Dict:
        """Get summary statistics of available enrichment data"""
        summary = {
            'total_enriched_tracks': len(self.enriched_data),
            'sources': {}
        }
        
        # Count by source
        if 'enrichment_source' in self.enriched_data.columns:
            source_counts = self.enriched_data['enrichment_source'].value_counts()
            summary['sources'] = source_counts.to_dict()
        
        # Feature coverage
        feature_coverage = {}
        for feature in ['tempo', 'energy', 'valence', 'primary_mood', 'key']:
            if feature in self.enriched_data.columns:
                coverage = self.enriched_data[feature].notna().sum()
                feature_coverage[feature] = {
                    'count': coverage,
                    'percentage': coverage / len(self.enriched_data) * 100
                }
        summary['feature_coverage'] = feature_coverage
        
        # Mood distribution
        if 'primary_mood' in self.enriched_data.columns:
            mood_dist = self.enriched_data['primary_mood'].value_counts().head(10)
            summary['top_moods'] = mood_dist.to_dict()
        
        return summary
    
    def create_unified_export(self, username: str, limit: Optional[int] = None) -> str:
        """Create a unified export with all available enrichment data"""
        # Load user's scrobbles
        scrobbles_file = self.data_dir / f"{username}_scrobbles.csv"
        if not scrobbles_file.exists():
            logger.error(f"Scrobbles file not found: {scrobbles_file}")
            return None
        
        df = pd.read_csv(scrobbles_file)
        
        if limit:
            df = df.head(limit)
        
        # Enrich the data
        enriched_df = self.enrich_dataframe(df)
        
        # Save the unified export
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.data_dir / f"{username}_unified_enriched_{timestamp}.csv"
        enriched_df.to_csv(output_file, index=False)
        
        logger.info(f"Unified export saved to: {output_file}")
        return str(output_file)


def main():
    """Test the unified enricher"""
    print("🎵 Unified Music Enricher")
    print("="*50)
    
    enricher = UnifiedMusicEnricher()
    
    # Show summary
    summary = enricher.get_enrichment_summary()
    print(f"\n📊 Enrichment Data Summary:")
    print(f"Total enriched tracks: {summary['total_enriched_tracks']:,}")
    
    print(f"\n📦 Data Sources:")
    for source, count in summary['sources'].items():
        print(f"  - {source}: {count:,} tracks")
    
    print(f"\n📈 Feature Coverage:")
    for feature, stats in summary['feature_coverage'].items():
        print(f"  - {feature}: {stats['count']:,} tracks ({stats['percentage']:.1f}%)")
    
    if 'top_moods' in summary:
        print(f"\n🎭 Top Moods:")
        for mood, count in list(summary['top_moods'].items())[:5]:
            print(f"  - {mood}: {count:,} tracks")
    
    # Test with a few tracks
    print(f"\n🧪 Testing with sample tracks:")
    test_tracks = [
        ("The Killers", "Bones"),
        ("Interpol", "Roland"),
        ("Kate Nash", "Foundations"),
        ("Radiohead", "Creep")
    ]
    
    for artist, track in test_tracks:
        features = enricher.get_track_features(artist, track)
        if features:
            print(f"\n✅ {artist} - {track}")
            print(f"   Source: {features.get('enrichment_source', 'unknown')}")
            if 'tempo' in features:
                print(f"   Tempo: {features['tempo']:.0f} BPM")
            if 'energy' in features:
                print(f"   Energy: {features['energy']:.2f}")
            if 'primary_mood' in features:
                print(f"   Mood: {features['primary_mood']}")
        else:
            print(f"\n❌ {artist} - {track} - No enrichment data")
    
    # Ask if user wants to create unified export
    print(f"\n📝 Create unified export?")
    print("This will combine all enrichment sources into one file.")
    choice = input("Enter 'y' to proceed: ").strip().lower()
    
    if choice == 'y':
        output_file = enricher.create_unified_export('zdjuna', limit=1000)
        if output_file:
            print(f"\n✅ Created unified export: {output_file}")


if __name__ == "__main__":
    main()