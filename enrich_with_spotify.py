#!/usr/bin/env python3
"""
Enrich your music library with REAL Spotify audio features
No more fake text analysis - this is actual music data!
"""

import pandas as pd
import os
from pathlib import Path
import time
import json
from typing import Dict, Optional
from real_music_analyzer import RealMusicAnalyzer, TrackFeatures
import logging
from tqdm import tqdm
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SpotifyEnricher:
    def __init__(self):
        self.client_id = os.getenv('SPOTIFY_CLIENT_ID')
        self.client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        
        if not self.client_id or not self.client_secret:
            raise ValueError("Spotify credentials not found! Run setup_spotify.py first.")
        
        self.analyzer = RealMusicAnalyzer(self.client_id, self.client_secret)
        self.cache_file = Path('cache/spotify_features_cache.json')
        self.cache = self._load_cache()
        
    def _load_cache(self) -> Dict:
        """Load cached Spotify features to avoid API limits"""
        if self.cache_file.exists():
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_cache(self):
        """Save cache to disk"""
        self.cache_file.parent.mkdir(exist_ok=True)
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)
    
    def _get_cache_key(self, artist: str, track: str) -> str:
        """Create cache key for track"""
        return f"{artist.lower().strip()}|||{track.lower().strip()}"
    
    def get_track_features(self, artist: str, track: str) -> Optional[Dict]:
        """Get track features from cache or API"""
        cache_key = self._get_cache_key(artist, track)
        
        # Check cache first
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Get from Spotify API
        features = self.analyzer.get_spotify_track_features(artist, track)
        if features:
            features_dict = {
                'valence': features.valence,
                'energy': features.energy,
                'danceability': features.danceability,
                'acousticness': features.acousticness,
                'instrumentalness': features.instrumentalness,
                'speechiness': features.speechiness,
                'tempo': features.tempo,
                'key': features.key,
                'mode': features.mode,
                'loudness': features.loudness,
                'duration_ms': features.duration_ms
            }
            
            # Analyze mood from features
            mood_analysis = self.analyzer.analyze_mood_from_features(features)
            features_dict.update({
                'mood_quadrant': mood_analysis['mood_quadrant'],
                'primary_mood': mood_analysis['primary_mood'],
                'is_acoustic': mood_analysis['is_acoustic'],
                'is_danceable': mood_analysis['is_danceable'],
                'is_major_key': mood_analysis['is_major_key'],
                'tempo_category': mood_analysis['tempo_category']
            })
            
            # Cache the result
            self.cache[cache_key] = features_dict
            self._save_cache()
            
            # Rate limiting (Spotify allows ~180 requests per minute)
            time.sleep(0.35)  # ~170 requests per minute to be safe
            
            return features_dict
        
        return None
    
    def enrich_library(self, input_file: str, output_file: str, limit: Optional[int] = None):
        """Enrich music library with Spotify audio features"""
        logger.info(f"Loading data from {input_file}")
        df = pd.read_csv(input_file)
        
        # Get unique tracks
        unique_tracks = df[['artist', 'track']].drop_duplicates()
        total_tracks = len(unique_tracks)
        
        if limit:
            unique_tracks = unique_tracks.head(limit)
            logger.info(f"Processing first {limit} unique tracks")
        else:
            logger.info(f"Processing {total_tracks} unique tracks")
        
        # Process tracks with progress bar
        enriched_data = []
        processed = 0
        found = 0
        
        print("\n🎵 Enriching your music library with REAL audio features...")
        
        with tqdm(total=len(unique_tracks), desc="Analyzing tracks") as pbar:
            for _, row in unique_tracks.iterrows():
                artist = row['artist']
                track = row['track']
                
                features = self.get_track_features(artist, track)
                
                if features:
                    found += 1
                    enriched_data.append({
                        'artist': artist,
                        'track': track,
                        **features
                    })
                    pbar.set_postfix({'found': f'{found}/{processed+1}'})
                
                processed += 1
                pbar.update(1)
        
        # Create enriched DataFrame
        if enriched_data:
            enriched_df = pd.DataFrame(enriched_data)
            
            # Merge with original data
            logger.info("\nMerging with original data...")
            result_df = df.merge(enriched_df, on=['artist', 'track'], how='left')
            
            # Save results
            logger.info(f"Saving enriched data to {output_file}")
            result_df.to_csv(output_file, index=False)
            
            # Summary statistics
            print("\n" + "="*50)
            print("🎵 ENRICHMENT COMPLETE!")
            print("="*50)
            print(f"Total tracks in library: {len(df)}")
            print(f"Unique tracks processed: {processed}")
            print(f"Tracks found on Spotify: {found} ({found/processed*100:.1f}%)")
            
            # Mood distribution
            mood_dist = enriched_df['primary_mood'].value_counts()
            print("\n📊 Mood Distribution (based on REAL audio):")
            for mood, count in mood_dist.items():
                print(f"  {mood}: {count} tracks ({count/len(enriched_df)*100:.1f}%)")
            
            # Average features
            print("\n📈 Your Music Taste (Average Audio Features):")
            print(f"  Valence (happiness): {enriched_df['valence'].mean():.3f}")
            print(f"  Energy: {enriched_df['energy'].mean():.3f}")
            print(f"  Danceability: {enriched_df['danceability'].mean():.3f}")
            print(f"  Acousticness: {enriched_df['acousticness'].mean():.3f}")
            print(f"  Tempo: {enriched_df['tempo'].mean():.1f} BPM")
            
            # Interesting insights
            print("\n💡 Interesting Insights:")
            
            # Most energetic tracks
            most_energetic = enriched_df.nlargest(3, 'energy')[['artist', 'track', 'energy']]
            print("\n🔥 Most Energetic Tracks:")
            for _, track in most_energetic.iterrows():
                print(f"  {track['artist']} - {track['track']} (Energy: {track['energy']:.3f})")
            
            # Most relaxing tracks
            most_relaxing = enriched_df.nsmallest(3, 'energy')[['artist', 'track', 'energy', 'valence']]
            print("\n😌 Most Relaxing Tracks:")
            for _, track in most_relaxing.iterrows():
                print(f"  {track['artist']} - {track['track']} (Energy: {track['energy']:.3f})")
            
            # Happiest tracks
            happiest = enriched_df.nlargest(3, 'valence')[['artist', 'track', 'valence']]
            print("\n😊 Happiest Tracks:")
            for _, track in happiest.iterrows():
                print(f"  {track['artist']} - {track['track']} (Valence: {track['valence']:.3f})")
            
            return result_df
            
        else:
            logger.error("No tracks could be enriched!")
            return df

def main():
    """Main function to run enrichment"""
    print("🎵 Spotify Music Enrichment")
    print("="*50)
    
    # Check for Spotify credentials
    if not os.getenv('SPOTIFY_CLIENT_ID') or not os.getenv('SPOTIFY_CLIENT_SECRET'):
        print("\n❌ Spotify credentials not found!")
        print("Please run: python setup_spotify.py")
        return
    
    # Check for data files
    scrobbles_file = 'data/zdjuna_scrobbles.csv'
    if not Path(scrobbles_file).exists():
        print(f"\n❌ Scrobbles file not found: {scrobbles_file}")
        print("Please fetch your Last.fm data first!")
        return
    
    # Ask user for options
    print("\n📝 Enrichment Options:")
    print("1. Quick test (first 20 tracks)")
    print("2. Small batch (first 100 tracks)")
    print("3. Medium batch (first 500 tracks)")
    print("4. Large batch (first 1000 tracks)")
    print("5. Full library (all tracks - may take hours!)")
    
    choice = input("\nSelect option (1-5): ").strip()
    
    limits = {
        '1': 20,
        '2': 100,
        '3': 500,
        '4': 1000,
        '5': None
    }
    
    limit = limits.get(choice, 20)
    
    # Output file
    if limit:
        output_file = f'data/zdjuna_spotify_enriched_{limit}_tracks.csv'
    else:
        output_file = 'data/zdjuna_spotify_enriched_full.csv'
    
    print(f"\n🚀 Starting enrichment...")
    print(f"Output will be saved to: {output_file}\n")
    
    # Estimate time
    if limit:
        estimated_time = (limit * 0.35) / 60  # 0.35 seconds per track
        print(f"⏱️  Estimated time: {estimated_time:.1f} minutes\n")
    
    # Run enrichment
    try:
        enricher = SpotifyEnricher()
        enricher.enrich_library(scrobbles_file, output_file, limit)
        
        print("\n✨ Done! Your music library now has REAL audio features!")
        print("\n🎯 Next steps:")
        print("1. Run 'python streamlit_app.py' to see your enriched data")
        print("2. Explore the new mood analysis based on actual music")
        print("3. Create playlists using real audio features!")
        
    except Exception as e:
        logger.error(f"Enrichment failed: {e}")
        print("\n❌ Something went wrong. Check the error above.")

if __name__ == "__main__":
    main() 
