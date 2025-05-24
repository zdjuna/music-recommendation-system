#!/usr/bin/env python3
"""
Enrich Last.fm scrobble data with Cyanite.ai mood analysis
Alternative solution after Spotify deprecated audio features API
"""

import pandas as pd
import os
from cyanite_mood_enricher import CyaniteMoodEnricher
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_clean_data():
    """Load the cleaned CSV data"""
    csv_path = "data/zdjuna_scrobbles.csv"
    
    if not os.path.exists(csv_path):
        logger.error(f"❌ CSV file not found: {csv_path}")
        return None
    
    try:
        # Load data
        df = pd.read_csv(csv_path)
        logger.info(f"✅ Loaded {len(df)} scrobbles from CSV")
        
        # Get unique tracks
        unique_tracks = df[['artist', 'track']].drop_duplicates()
        logger.info(f"📊 Found {len(unique_tracks)} unique tracks")
        
        return df, unique_tracks
        
    except Exception as e:
        logger.error(f"❌ Error loading CSV: {e}")
        return None

def main():
    print("🎵 CYANITE.AI MOOD ENRICHMENT FOR LAST.FM DATA")
    print("=" * 60)
    print("🔄 Alternative solution after Spotify deprecated audio features API")
    print()
    
    # Get Cyanite API key
    api_key = input("Enter your Cyanite.ai API key (get one at https://cyanite.ai/): ").strip()
    
    if not api_key:
        print("❌ API key is required. Visit https://cyanite.ai/ to sign up.")
        return
    
    # Load data
    print("\n📂 Loading scrobble data...")
    data_result = load_clean_data()
    if not data_result:
        return
    
    full_df, unique_tracks = data_result
    
    # Get user preferences
    print(f"\n📊 You have {len(unique_tracks)} unique tracks to analyze.")
    print("💰 Note: Cyanite charges per API call, so consider starting with a subset.")
    
    max_tracks = input(f"How many tracks to analyze? (Enter for all {len(unique_tracks)}): ").strip()
    
    if max_tracks:
        try:
            max_tracks = int(max_tracks)
            unique_tracks = unique_tracks.head(max_tracks)
            print(f"📉 Limited to {max_tracks} tracks")
        except ValueError:
            print("❌ Invalid number, using all tracks")
            max_tracks = None
    else:
        max_tracks = None
    
    # Create enricher
    print(f"\n🤖 Initializing Cyanite.ai enricher...")
    enricher = CyaniteMoodEnricher(api_key)
    
    # Test with one track first
    print("\n🧪 Testing with first track...")
    test_artist = unique_tracks.iloc[0]['artist']
    test_track = unique_tracks.iloc[0]['track']
    
    print(f"   Testing: {test_artist} - {test_track}")
    test_result = enricher.search_and_analyze_track(test_artist, test_track)
    
    if not test_result:
        print("❌ Test failed. Please check your API key and internet connection.")
        return
    
    print(f"   ✅ Test successful! Mood: {test_result.get('simplified_mood', 'unknown')}")
    
    # Confirm before processing all
    if max_tracks is None or max_tracks > 100:
        confirm = input(f"\n⚠️  About to process {len(unique_tracks)} tracks. This may take time and cost money. Continue? (y/N): ").strip().lower()
        if confirm != 'y':
            print("❌ Cancelled by user")
            return
    
    # Enrich unique tracks
    print(f"\n🎯 Enriching {len(unique_tracks)} unique tracks with Cyanite.ai...")
    enriched_tracks = enricher.enrich_dataset(
        unique_tracks, 
        artist_col='artist', 
        track_col='track',
        delay=0.5  # Be respectful to API
    )
    
    # Merge back with full dataset
    print("\n🔗 Merging mood data back to full scrobble dataset...")
    
    # Create a lookup dictionary for mood data
    mood_lookup = {}
    for _, row in enriched_tracks.iterrows():
        key = (row['artist'], row['track'])
        mood_lookup[key] = {
            'simplified_mood': row.get('simplified_mood', 'unknown'),
            'cyanite_valence': row.get('cyanite_valence'),
            'cyanite_energy': row.get('cyanite_energy'),
            'cyanite_danceability': row.get('cyanite_danceability'),
            'cyanite_genre': row.get('cyanite_genre'),
            'cyanite_tempo': row.get('cyanite_tempo')
        }
    
    # Add mood data to full dataset
    full_df['cyanite_mood'] = full_df.apply(
        lambda row: mood_lookup.get((row['artist'], row['track']), {}).get('simplified_mood', 'unknown'), 
        axis=1
    )
    
    full_df['cyanite_valence'] = full_df.apply(
        lambda row: mood_lookup.get((row['artist'], row['track']), {}).get('cyanite_valence'), 
        axis=1
    )
    
    full_df['cyanite_energy'] = full_df.apply(
        lambda row: mood_lookup.get((row['artist'], row['track']), {}).get('cyanite_energy'), 
        axis=1
    )
    
    # Save enriched data
    output_path = "data/zdjuna_scrobbles_cyanite_enriched.csv"
    print(f"\n💾 Saving enriched data to {output_path}...")
    
    try:
        full_df.to_csv(output_path, index=False)
        logger.info(f"✅ Saved enriched dataset: {output_path}")
    except Exception as e:
        logger.error(f"❌ Error saving file: {e}")
        return
    
    # Save just the mood mappings for future use
    mood_mapping_path = "data/cyanite_mood_mappings.csv"
    print(f"💾 Saving mood mappings to {mood_mapping_path}...")
    
    try:
        enriched_tracks.to_csv(mood_mapping_path, index=False)
        logger.info(f"✅ Saved mood mappings: {mood_mapping_path}")
    except Exception as e:
        logger.error(f"❌ Error saving mood mappings: {e}")
    
    # Show results
    print("\n🎭 ENRICHMENT RESULTS:")
    print("=" * 50)
    
    enricher.analyze_mood_distribution(full_df.rename(columns={'cyanite_mood': 'simplified_mood'}))
    
    print(f"\n📈 SUCCESS SUMMARY:")
    total_enriched = len(full_df[full_df['cyanite_mood'] != 'unknown'])
    print(f"   • Total scrobbles: {len(full_df):,}")
    print(f"   • Unique tracks processed: {len(unique_tracks):,}")
    print(f"   • Successfully enriched: {total_enriched:,}")
    print(f"   • Success rate: {(total_enriched/len(full_df)*100):.1f}%")
    
    print(f"\n✅ Enrichment complete! Your mood-enhanced data is ready.")
    print(f"📁 Files created:")
    print(f"   • {output_path}")
    print(f"   • {mood_mapping_path}")
    
    print(f"\n🚀 Next steps:")
    print(f"   1. Update your Streamlit app to use 'cyanite_mood' column")
    print(f"   2. Test mood-based playlist generation")
    print(f"   3. Enjoy accurate mood classifications! 🎉")

if __name__ == "__main__":
    main() 