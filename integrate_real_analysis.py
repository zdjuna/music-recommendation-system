#!/usr/bin/env python3
"""
Script to integrate REAL music analysis into the Streamlit app
Replaces fake text-based emotion analysis with actual Spotify audio features
"""

import os
import shutil
from pathlib import Path

def backup_files():
    """Backup existing files before modification"""
    files_to_backup = [
        'streamlit_app.py',
        'src/music_rec/enrichment.py'
    ]
    
    backup_dir = Path('backups/before_real_analysis')
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    for file in files_to_backup:
        if Path(file).exists():
            dest = backup_dir / Path(file).name
            shutil.copy2(file, dest)
            print(f"✅ Backed up {file} to {dest}")

def update_streamlit_enrichment():
    """Update the enrichment logic in Streamlit to use real analysis"""
    
    # Create new enrichment module that uses real analysis
    enrichment_code = '''"""
Real Music Enrichment Module
Uses Spotify audio features instead of fake text analysis
"""

import pandas as pd
import logging
from pathlib import Path
from typing import Optional
import os

logger = logging.getLogger(__name__)

class RealMusicEnricher:
    """Enriches music data with REAL audio features from Spotify"""
    
    def __init__(self):
        # Check if we have Spotify enriched data
        self.spotify_enriched_files = list(Path('data').glob('*spotify_enriched*.csv'))
        self.has_spotify_data = len(self.spotify_enriched_files) > 0
        
    def enrich_data(self, df: pd.DataFrame, username: str) -> pd.DataFrame:
        """Enrich data with real music features"""
        logger.info("Starting REAL music enrichment...")
        
        if not self.has_spotify_data:
            logger.warning("No Spotify enriched data found. Please run: python enrich_with_spotify.py")
            # Return original data with a notice
            df['enrichment_note'] = 'Run enrich_with_spotify.py for real audio features'
            return df
        
        # Use the most recent Spotify enriched file
        latest_spotify_file = max(self.spotify_enriched_files, key=lambda p: p.stat().st_mtime)
        logger.info(f"Using Spotify data from: {latest_spotify_file}")
        
        # Load Spotify enriched data
        spotify_df = pd.read_csv(latest_spotify_file)
        
        # Select relevant columns
        spotify_features = [
            'artist', 'track', 'valence', 'energy', 'danceability',
            'acousticness', 'instrumentalness', 'tempo', 'loudness',
            'mood_quadrant', 'primary_mood', 'is_acoustic', 'is_danceable',
            'is_major_key', 'tempo_category'
        ]
        
        available_features = [col for col in spotify_features if col in spotify_df.columns]
        spotify_subset = spotify_df[available_features].drop_duplicates(subset=['artist', 'track'])
        
        # Merge with original data
        enriched_df = df.merge(spotify_subset, on=['artist', 'track'], how='left')
        
        # Add enrichment metadata
        enriched_df['enrichment_source'] = 'spotify_audio_features'
        enriched_df['has_real_features'] = enriched_df['valence'].notna()
        
        # Summary statistics
        total_tracks = len(enriched_df)
        enriched_tracks = enriched_df['has_real_features'].sum()
        enrichment_rate = (enriched_tracks / total_tracks) * 100
        
        logger.info(f"✅ Enriched {enriched_tracks}/{total_tracks} tracks ({enrichment_rate:.1f}%) with real audio features")
        
        if enriched_tracks > 0:
            logger.info(f"Average valence: {enriched_df['valence'].mean():.3f}")
            logger.info(f"Average energy: {enriched_df['energy'].mean():.3f}")
            
            mood_dist = enriched_df['primary_mood'].value_counts()
            logger.info("Mood distribution:")
            for mood, count in mood_dist.head(5).items():
                logger.info(f"  {mood}: {count} tracks")
        
        return enriched_df

# Legacy compatibility wrapper
def enrich_with_advanced_emotions(df: pd.DataFrame, username: str) -> pd.DataFrame:
    """Legacy function name - redirects to real enrichment"""
    enricher = RealMusicEnricher()
    return enricher.enrich_data(df, username)
'''
    
    # Write the new enrichment module
    enrichment_path = Path('src/music_rec/real_enrichment.py')
    enrichment_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(enrichment_path, 'w') as f:
        f.write(enrichment_code)
    
    print(f"✅ Created real enrichment module: {enrichment_path}")
    
    # Update imports in streamlit_app.py
    streamlit_path = Path('streamlit_app.py')
    if streamlit_path.exists():
        content = streamlit_path.read_text()
        
        # Replace emotion analyzer imports with real enrichment
        replacements = [
            ('from research_based_emotion_analyzer import ResearchBasedEmotionAnalyzer',
             'from src.music_rec.real_enrichment import RealMusicEnricher'),
            ('from research_based_mood_analyzer import ResearchBasedMoodAnalyzer',
             '# Removed fake mood analyzer - using real Spotify data now'),
            ('emotion_analyzer = ResearchBasedEmotionAnalyzer()',
             'music_enricher = RealMusicEnricher()'),
            ('mood_analyzer = ResearchBasedMoodAnalyzer()',
             '# Using real music enricher instead of fake mood analyzer'),
            ('enriched_df = enrich_with_advanced_emotions(df, username)',
             'enriched_df = music_enricher.enrich_data(df, username)')
        ]
        
        for old, new in replacements:
            if old in content:
                content = content.replace(old, new)
                print(f"✅ Replaced: {old[:50]}...")
        
        # Write updated content
        streamlit_path.write_text(content)
        print("✅ Updated streamlit_app.py to use real music analysis")

def create_migration_guide():
    """Create a guide for migrating to real analysis"""
    guide = '''# 🎵 Migration to Real Music Analysis

## What Changed?

We've replaced the fake text-based emotion analysis with REAL Spotify audio features:

### ❌ OLD (Fake) Analysis:
- Analyzed emotions by reading artist names and track titles
- Used "emotion lexicons" to guess mood from text
- Trained ML models on artist names (not music!)
- Generated made-up emotion scores

### ✅ NEW (Real) Analysis:
- Uses Spotify's audio analysis API
- Actual musical features: valence, energy, danceability
- Real tempo, key, and mode detection
- Mood derived from actual audio characteristics

## How to Use:

### 1. Get Spotify API Credentials:
```bash
python setup_spotify.py
```

### 2. Enrich Your Music Library:
```bash
python enrich_with_spotify.py
```

### 3. Use in Streamlit:
The app will automatically use the real enriched data when available.

## Data Comparison:

### Before (Fake):
```
Artist: Interpol
Track: Evil
Emotion: "brooding" (guessed from the word "Interpol")
Valence: -0.2 (made up based on artist name)
```

### After (Real):
```
Artist: Interpol  
Track: Evil
Valence: 0.234 (actual audio feature)
Energy: 0.567 (actual audio feature)
Tempo: 142 BPM (actual tempo)
Key: A minor (actual key detection)
Mood: "energetic" (derived from real features)
```

## Benefits:

1. **Accurate mood detection** based on actual music
2. **Better recommendations** using real audio similarity
3. **Tempo-based playlists** (workout, study, party)
4. **Key-compatible mixing** for DJs
5. **Energy flow management** in playlists

## FAQ:

**Q: What about tracks not on Spotify?**
A: They won't have audio features, but you'll still have your listening history data.

**Q: Is this free?**
A: Yes! Spotify's API is free for personal use.

**Q: How long does enrichment take?**
A: About 3-4 tracks per second (rate limited for stability).

## Next Steps:

After enriching your library with real data, you can:
- Create energy-based playlists
- Find songs with similar audio characteristics  
- Analyze your taste in terms of actual musical features
- Generate better AI recommendations based on real music data

Welcome to REAL music analysis! 🎵
'''
    
    with open('REAL_MUSIC_MIGRATION.md', 'w') as f:
        f.write(guide)
    
    print("✅ Created migration guide: REAL_MUSIC_MIGRATION.md")

def main():
    print("🎵 Integrating Real Music Analysis")
    print("="*50)
    
    # Backup existing files
    print("\n📦 Backing up existing files...")
    backup_files()
    
    # Update Streamlit enrichment
    print("\n🔧 Updating Streamlit app...")
    update_streamlit_enrichment()
    
    # Create migration guide
    print("\n📝 Creating migration guide...")
    create_migration_guide()
    
    print("\n✅ Integration complete!")
    print("\n📋 Next steps:")
    print("1. Run: python setup_spotify.py")
    print("2. Run: python enrich_with_spotify.py")
    print("3. Launch Streamlit and enjoy REAL music analysis!")
    
    print("\n⚠️  Note: The fake emotion analyzers are still in the codebase.")
    print("You can safely delete these files:")
    print("  - research_based_emotion_analyzer.py")
    print("  - research_based_mood_analyzer.py")
    print("  - complete_emotion_research_module.py")

if __name__ == "__main__":
    main() 