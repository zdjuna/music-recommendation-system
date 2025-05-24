"""
Metadata enricher for music recommendation system.

This module orchestrates the enrichment of music data with external metadata sources,
providing genre classification, mood analysis, and additional contextual information.
"""

import logging
import json
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import os
from pathlib import Path

from ..data_fetchers.musicbrainz_fetcher import MusicBrainzFetcher

logger = logging.getLogger(__name__)

class MetadataEnricher:
    """
    Orchestrates metadata enrichment from multiple sources.
    
    Features:
    - MusicBrainz genre and tag enrichment
    - Mood and energy classification
    - Artist relationship analysis
    - Popularity and discovery metrics
    - Intelligent caching and batch processing
    """
    
    def __init__(self, data_dir: str = "data", cache_dir: str = "cache"):
        """
        Initialize metadata enricher.
        
        Args:
            data_dir: Directory containing music data
            cache_dir: Directory for caching enriched data
        """
        self.data_dir = Path(data_dir)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Initialize MusicBrainz fetcher
        self.mb_fetcher = MusicBrainzFetcher()
        
        # Mood and energy mapping
        self.mood_mapping = self._build_mood_mapping()
        self.energy_mapping = self._build_energy_mapping()
        
        # Statistics
        self.stats = {
            'total_processed': 0,
            'successfully_enriched': 0,
            'cache_hits': 0,
            'mb_enriched': 0,
            'mood_classified': 0,
            'energy_classified': 0,
            'start_time': None,
            'end_time': None
        }
    
    def _build_mood_mapping(self) -> Dict[str, List[str]]:
        """Build mapping of tags/genres to mood categories."""
        return {
            'happy': [
                'upbeat', 'cheerful', 'joyful', 'uplifting', 'positive', 'energetic',
                'dance', 'party', 'feel good', 'optimistic', 'bright', 'fun'
            ],
            'sad': [
                'melancholy', 'depressing', 'somber', 'mournful', 'tragic', 'sorrowful',
                'blues', 'depressed', 'downbeat', 'gloomy', 'moody', 'emotional'
            ],
            'angry': [
                'aggressive', 'intense', 'harsh', 'brutal', 'furious', 'rage',
                'metal', 'hardcore', 'punk', 'angry', 'violent', 'hostile'
            ],
            'calm': [
                'peaceful', 'relaxing', 'soothing', 'tranquil', 'serene', 'gentle',
                'ambient', 'chill', 'meditative', 'soft', 'quiet', 'mellow'
            ],
            'romantic': [
                'love', 'romantic', 'sensual', 'intimate', 'passionate', 'tender',
                'smooth', 'sultry', 'seductive', 'sweet', 'loving', 'affectionate'
            ],
            'nostalgic': [
                'nostalgic', 'vintage', 'retro', 'classic', 'oldies', 'memories',
                'wistful', 'reminiscent', 'sentimental', 'longing', 'reflective'
            ],
            'mysterious': [
                'dark', 'mysterious', 'atmospheric', 'haunting', 'eerie', 'gothic',
                'shadowy', 'cryptic', 'enigmatic', 'noir', 'brooding', 'ominous'
            ],
            'motivational': [
                'inspiring', 'motivational', 'empowering', 'triumphant', 'heroic',
                'uplifting', 'encouraging', 'determined', 'confident', 'strong'
            ]
        }
    
    def _build_energy_mapping(self) -> Dict[str, List[str]]:
        """Build mapping of tags/genres to energy levels."""
        return {
            'very_high': [
                'hardcore', 'metal', 'punk', 'drum and bass', 'speedcore', 'thrash',
                'death metal', 'gabber', 'breakcore', 'grindcore', 'powerviolence'
            ],
            'high': [
                'rock', 'dance', 'electronic', 'techno', 'house', 'trance',
                'pop punk', 'alternative rock', 'hard rock', 'funk', 'disco'
            ],
            'medium': [
                'pop', 'indie', 'alternative', 'hip hop', 'r&b', 'reggae',
                'ska', 'blues', 'country', 'folk rock', 'indie rock'
            ],
            'low': [
                'folk', 'acoustic', 'singer-songwriter', 'ballad', 'slow',
                'soft rock', 'easy listening', 'lounge', 'downtempo'
            ],
            'very_low': [
                'ambient', 'drone', 'meditation', 'new age', 'minimalism',
                'field recording', 'sleep music', 'peaceful', 'calm'
            ]
        }
    
    def enrich_dataset(self, scrobble_file: str, output_file: Optional[str] = None,
                      batch_size: int = 50, sample_size: Optional[int] = None) -> pd.DataFrame:
        """
        Enrich a complete scrobble dataset with metadata.
        
        Args:
            scrobble_file: Path to scrobble data file (CSV or JSON)
            output_file: Path for enriched output file
            batch_size: Number of records to process per batch
            sample_size: Limit processing to N records (for testing)
            
        Returns:
            Enriched DataFrame
        """
        logger.info(f"Starting metadata enrichment for {scrobble_file}")
        self.stats['start_time'] = datetime.now()
        
        # Load scrobble data
        df = self._load_scrobble_data(scrobble_file)
        if df is None or len(df) == 0:
            logger.error("No data loaded for enrichment")
            return pd.DataFrame()
        
        # Sample data if requested
        if sample_size and len(df) > sample_size:
            logger.info(f"Sampling {sample_size} records from {len(df)} total")
            df = df.sample(n=sample_size, random_state=42)
        
        logger.info(f"Processing {len(df)} records in batches of {batch_size}")
        
        # Check for existing enriched data
        enriched_df = self._load_cached_enrichment(scrobble_file)
        if enriched_df is not None:
            logger.info("Found cached enriched data, merging with new data")
            df = self._merge_enriched_data(df, enriched_df)
        
        # Deduplicate by artist-track combination for enrichment
        unique_tracks = self._get_unique_tracks(df)
        logger.info(f"Found {len(unique_tracks)} unique artist-track combinations")
        
        # Enrich unique tracks
        enriched_tracks = self._enrich_unique_tracks(unique_tracks, batch_size)
        
        # Apply enrichment back to full dataset
        enriched_df = self._apply_enrichment_to_dataset(df, enriched_tracks)
        
        # Add derived features
        enriched_df = self._add_derived_features(enriched_df)
        
        # Save results
        if output_file:
            self._save_enriched_data(enriched_df, output_file)
        
        # Cache enrichment for future use
        self._cache_enrichment(scrobble_file, enriched_df)
        
        self.stats['end_time'] = datetime.now()
        self.stats['total_processed'] = len(enriched_df)
        
        logger.info("Metadata enrichment completed")
        self._log_enrichment_stats()
        
        return enriched_df
    
    def _load_scrobble_data(self, file_path: str) -> Optional[pd.DataFrame]:
        """Load scrobble data from CSV or JSON file."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.error(f"Scrobble file not found: {file_path}")
            return None
        
        try:
            if file_path.suffix.lower() == '.csv':
                df = pd.read_csv(file_path)
            elif file_path.suffix.lower() == '.json':
                df = pd.read_json(file_path)
            else:
                logger.error(f"Unsupported file format: {file_path.suffix}")
                return None
            
            logger.info(f"Loaded {len(df)} scrobbles from {file_path}")
            return df
            
        except Exception as e:
            logger.error(f"Error loading scrobble data from {file_path}: {e}")
            return None
    
    def _get_unique_tracks(self, df: pd.DataFrame) -> pd.DataFrame:
        """Get unique artist-track combinations for enrichment."""
        unique_df = df[['artist', 'track']].drop_duplicates()
        unique_df = unique_df.dropna(subset=['artist', 'track'])
        unique_df = unique_df.reset_index(drop=True)
        return unique_df
    
    def _enrich_unique_tracks(self, unique_tracks: pd.DataFrame, 
                            batch_size: int) -> pd.DataFrame:
        """Enrich unique tracks with metadata."""
        logger.info(f"Enriching {len(unique_tracks)} unique tracks")
        
        # Add enrichment columns
        enrichment_columns = [
            'mb_artist_id', 'mb_recording_id', 'mb_genres', 'mb_tags',
            'mb_artist_type', 'mb_artist_country', 'mb_recording_length',
            'mb_artist_relationships', 'mood_primary', 'mood_secondary',
            'energy_level', 'danceability', 'popularity_score', 'enriched_at'
        ]
        
        for col in enrichment_columns:
            unique_tracks[col] = None
        
        # Process in batches
        total_batches = (len(unique_tracks) + batch_size - 1) // batch_size
        
        for batch_idx in range(total_batches):
            start_idx = batch_idx * batch_size
            end_idx = min((batch_idx + 1) * batch_size, len(unique_tracks))
            
            logger.info(f"Processing batch {batch_idx + 1}/{total_batches} "
                       f"(tracks {start_idx + 1}-{end_idx})")
            
            batch_df = unique_tracks.iloc[start_idx:end_idx].copy()
            
            # MusicBrainz enrichment
            enriched_batch = self.mb_fetcher.enrich_scrobble_data(batch_df, batch_size=10)
            
            # Apply MusicBrainz data back to main DataFrame
            for idx in range(start_idx, end_idx):
                batch_row_idx = idx - start_idx
                if batch_row_idx < len(enriched_batch):
                    enriched_row = enriched_batch.iloc[batch_row_idx]
                    
                    # Copy MusicBrainz data
                    mb_columns = [col for col in enriched_row.index if col.startswith('mb_')]
                    for col in mb_columns:
                        if col in unique_tracks.columns:
                            unique_tracks.at[idx, col] = enriched_row[col]
                    
                    # Add mood and energy classification
                    mood_energy = self._classify_mood_and_energy(enriched_row)
                    for key, value in mood_energy.items():
                        if key in unique_tracks.columns:
                            unique_tracks.at[idx, key] = value
                    
                    # Add derived metrics
                    derived = self._calculate_derived_metrics(enriched_row)
                    for key, value in derived.items():
                        if key in unique_tracks.columns:
                            unique_tracks.at[idx, key] = value
                    
                    unique_tracks.at[idx, 'enriched_at'] = datetime.now().isoformat()
                    self.stats['successfully_enriched'] += 1
            
            # Progress update
            progress = (batch_idx + 1) / total_batches * 100
            logger.info(f"Enrichment progress: {progress:.1f}%")
        
        return unique_tracks
    
    def _classify_mood_and_energy(self, row: pd.Series) -> Dict[str, Any]:
        """Classify mood and energy based on tags and genres."""
        result = {
            'mood_primary': None,
            'mood_secondary': None,
            'energy_level': None,
            'danceability': 0.0
        }
        
        # Extract tags and genres
        tags = []
        genres = []
        
        try:
            if pd.notna(row.get('mb_tags')):
                tags = json.loads(row['mb_tags'])
            if pd.notna(row.get('mb_genres')):
                genres = json.loads(row['mb_genres'])
        except (json.JSONDecodeError, TypeError):
            pass
        
        all_descriptors = [tag.lower() for tag in tags] + [genre.lower() for genre in genres]
        
        if not all_descriptors:
            return result
        
        # Mood classification
        mood_scores = {}
        for mood, keywords in self.mood_mapping.items():
            score = sum(1 for desc in all_descriptors if any(keyword in desc for keyword in keywords))
            if score > 0:
                mood_scores[mood] = score
        
        if mood_scores:
            sorted_moods = sorted(mood_scores.items(), key=lambda x: x[1], reverse=True)
            result['mood_primary'] = sorted_moods[0][0]
            if len(sorted_moods) > 1:
                result['mood_secondary'] = sorted_moods[1][0]
            
            self.stats['mood_classified'] += 1
        
        # Energy classification
        energy_scores = {}
        for energy, keywords in self.energy_mapping.items():
            score = sum(1 for desc in all_descriptors if any(keyword in desc for keyword in keywords))
            if score > 0:
                energy_scores[energy] = score
        
        if energy_scores:
            result['energy_level'] = max(energy_scores.items(), key=lambda x: x[1])[0]
            self.stats['energy_classified'] += 1
        
        # Danceability heuristic
        dance_keywords = ['dance', 'disco', 'funk', 'house', 'techno', 'electronic', 'beat']
        dance_score = sum(1 for desc in all_descriptors if any(keyword in desc for keyword in dance_keywords))
        result['danceability'] = min(dance_score / len(all_descriptors), 1.0) if all_descriptors else 0.0
        
        return result
    
    def _calculate_derived_metrics(self, row: pd.Series) -> Dict[str, Any]:
        """Calculate derived metrics like popularity score."""
        result = {
            'popularity_score': 0.0
        }
        
        # Simple popularity heuristic based on tag counts and artist type
        try:
            tags = []
            if pd.notna(row.get('mb_tags')):
                tag_data = json.loads(row['mb_tags'])
                if isinstance(tag_data, list) and tag_data:
                    # If we have tag count information, use it
                    if isinstance(tag_data[0], dict) and 'count' in tag_data[0]:
                        total_tag_count = sum(tag.get('count', 0) for tag in tag_data)
                        result['popularity_score'] = min(total_tag_count / 1000, 1.0)
                    else:
                        # If just tag names, use number of tags as proxy
                        result['popularity_score'] = min(len(tag_data) / 20, 1.0)
        except (json.JSONDecodeError, TypeError):
            pass
        
        return result
    
    def _apply_enrichment_to_dataset(self, original_df: pd.DataFrame, 
                                   enriched_tracks: pd.DataFrame) -> pd.DataFrame:
        """Apply enrichment data back to the full dataset."""
        logger.info("Applying enrichment to full dataset")
        
        # Create a mapping from (artist, track) to enrichment data
        enrichment_dict = {}
        for _, row in enriched_tracks.iterrows():
            key = (row['artist'], row['track'])
            enrichment_dict[key] = row.to_dict()
        
        # Apply enrichment to original data
        enriched_df = original_df.copy()
        
        # Add enrichment columns
        enrichment_columns = [col for col in enriched_tracks.columns 
                            if col not in ['artist', 'track']]
        
        for col in enrichment_columns:
            enriched_df[col] = None
        
        # Fill in enrichment data
        for idx, row in enriched_df.iterrows():
            key = (row['artist'], row['track'])
            if key in enrichment_dict:
                enrichment_data = enrichment_dict[key]
                for col in enrichment_columns:
                    if col in enrichment_data:
                        enriched_df.at[idx, col] = enrichment_data[col]
        
        return enriched_df
    
    def _add_derived_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add derived features based on enriched metadata."""
        logger.info("Adding derived features")
        
        # Time-based features
        if 'timestamp' in df.columns:
            df['hour_of_day'] = pd.to_datetime(df['timestamp']).dt.hour
            df['day_of_week'] = pd.to_datetime(df['timestamp']).dt.dayofweek
            df['is_weekend'] = df['day_of_week'].isin([5, 6])
        
        # Genre diversity metrics
        if 'mb_genres' in df.columns:
            df['genre_count'] = df['mb_genres'].apply(self._count_genres)
        
        # Mood transition analysis
        if 'mood_primary' in df.columns:
            df['mood_change'] = df['mood_primary'].ne(df['mood_primary'].shift()).astype(int)
        
        return df
    
    def _count_genres(self, genres_json: str) -> int:
        """Count number of genres for a track."""
        if pd.isna(genres_json):
            return 0
        try:
            genres = json.loads(genres_json)
            return len(genres) if isinstance(genres, list) else 0
        except (json.JSONDecodeError, TypeError):
            return 0
    
    def _load_cached_enrichment(self, original_file: str) -> Optional[pd.DataFrame]:
        """Load cached enrichment data if available."""
        cache_file = self.cache_dir / f"{Path(original_file).stem}_enriched.parquet"
        
        if cache_file.exists():
            try:
                df = pd.read_parquet(cache_file)
                logger.info(f"Loaded cached enrichment from {cache_file}")
                return df
            except Exception as e:
                logger.warning(f"Failed to load cached enrichment: {e}")
        
        return None
    
    def _merge_enriched_data(self, new_df: pd.DataFrame, 
                           cached_df: pd.DataFrame) -> pd.DataFrame:
        """Merge new data with cached enrichment."""
        # This is a simple implementation - in practice you'd want more sophisticated merging
        return new_df
    
    def _cache_enrichment(self, original_file: str, enriched_df: pd.DataFrame):
        """Cache enriched data for future use."""
        cache_file = self.cache_dir / f"{Path(original_file).stem}_enriched.parquet"
        
        try:
            enriched_df.to_parquet(cache_file, index=False)
            logger.info(f"Cached enriched data to {cache_file}")
        except Exception as e:
            logger.warning(f"Failed to cache enriched data: {e}")
    
    def _save_enriched_data(self, df: pd.DataFrame, output_file: str):
        """Save enriched data to file."""
        output_path = Path(output_file)
        
        try:
            if output_path.suffix.lower() == '.csv':
                df.to_csv(output_path, index=False)
            elif output_path.suffix.lower() == '.json':
                df.to_json(output_path, orient='records', date_format='iso')
            elif output_path.suffix.lower() == '.parquet':
                df.to_parquet(output_path, index=False)
            else:
                logger.warning(f"Unsupported output format: {output_path.suffix}")
                return
            
            logger.info(f"Saved enriched data to {output_path}")
        except Exception as e:
            logger.error(f"Failed to save enriched data: {e}")
    
    def _log_enrichment_stats(self):
        """Log detailed enrichment statistics."""
        duration = self.stats['end_time'] - self.stats['start_time']
        
        logger.info("=== Metadata Enrichment Statistics ===")
        logger.info(f"Total processed: {self.stats['total_processed']}")
        logger.info(f"Successfully enriched: {self.stats['successfully_enriched']}")
        logger.info(f"MusicBrainz enriched: {self.stats['mb_enriched']}")
        logger.info(f"Mood classified: {self.stats['mood_classified']}")
        logger.info(f"Energy classified: {self.stats['energy_classified']}")
        logger.info(f"Cache hits: {self.stats['cache_hits']}")
        logger.info(f"Duration: {duration}")
        logger.info("=" * 40)
    
    def analyze_enrichment_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze the quality and coverage of enrichment."""
        analysis = {
            'total_records': len(df),
            'coverage': {},
            'quality_metrics': {},
            'recommendations': []
        }
        
        # Coverage analysis
        enrichment_columns = [col for col in df.columns if col.startswith('mb_') or 
                            col in ['mood_primary', 'energy_level', 'danceability']]
        
        for col in enrichment_columns:
            non_null_count = df[col].notna().sum()
            coverage_pct = (non_null_count / len(df)) * 100
            analysis['coverage'][col] = {
                'count': non_null_count,
                'percentage': coverage_pct
            }
        
        # Quality metrics
        if 'mb_genres' in df.columns:
            genre_diversity = df['mb_genres'].apply(self._count_genres).mean()
            analysis['quality_metrics']['avg_genres_per_track'] = genre_diversity
        
        if 'mood_primary' in df.columns:
            mood_coverage = (df['mood_primary'].notna().sum() / len(df)) * 100
            analysis['quality_metrics']['mood_classification_rate'] = mood_coverage
        
        # Recommendations
        if analysis['coverage'].get('mb_genres', {}).get('percentage', 0) < 50:
            analysis['recommendations'].append("Low genre coverage - consider alternative data sources")
        
        if analysis['coverage'].get('mood_primary', {}).get('percentage', 0) < 30:
            analysis['recommendations'].append("Low mood classification - review mood mapping rules")
        
        return analysis
    
    def get_stats(self) -> Dict[str, Any]:
        """Get enrichment statistics."""
        return self.stats.copy() 