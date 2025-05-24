#!/usr/bin/env python3
"""
Cyanite.ai Mood Enricher
Professional music analysis API for accurate mood classification
Alternative to Spotify's deprecated audio features API
"""

import pandas as pd
import requests
import time
import logging
from datetime import datetime
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CyaniteMoodEnricher:
    """Enriches music data with Cyanite.ai's professional music analysis"""
    
    def __init__(self, api_key):
        """Initialize Cyanite client"""
        self.api_key = api_key
        self.base_url = "https://api.cyanite.ai/graphql"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
    def search_and_analyze_track(self, artist, track, max_retries=3):
        """Search for a track and get its mood analysis"""
        
        # GraphQL query to search and analyze
        query = """
        query SearchTracks($searchText: String!) {
          searchTracks(searchText: $searchText, first: 1) {
            edges {
              node {
                id
                title
                artist
                genre
                mood
                energy
                valence
                danceability
                tempo
                key
                mode
                acousticness
                instrumentalness
                liveness
                loudness
                speechiness
                tags
                similarityVector
              }
            }
          }
        }
        """
        
        search_text = f"{artist} {track}"
        variables = {"searchText": search_text}
        
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.base_url,
                    headers=self.headers,
                    json={"query": query, "variables": variables},
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get('data', {}).get('searchTracks', {}).get('edges'):
                        track_data = data['data']['searchTracks']['edges'][0]['node']
                        return self._process_track_data(track_data)
                    else:
                        logger.warning(f"🔍 No Cyanite match found for: {artist} - {track}")
                        return None
                        
                elif response.status_code == 429:  # Rate limited
                    wait_time = 2 ** attempt
                    logger.warning(f"⏱️ Rate limited, waiting {wait_time}s (attempt {attempt + 1})")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"❌ Cyanite API error: {response.status_code} - {response.text}")
                    return None
                    
            except Exception as e:
                logger.error(f"❌ Unexpected error searching for {artist} - {track}: {e}")
                return None
        
        return None
    
    def _process_track_data(self, track_data):
        """Process and clean track data from Cyanite API"""
        try:
            processed = {
                'cyanite_id': track_data.get('id'),
                'matched_title': track_data.get('title'),
                'matched_artist': track_data.get('artist'),
                'cyanite_genre': track_data.get('genre'),
                'cyanite_mood': track_data.get('mood'),
                'cyanite_energy': track_data.get('energy'),
                'cyanite_valence': track_data.get('valence'),
                'cyanite_danceability': track_data.get('danceability'),
                'cyanite_tempo': track_data.get('tempo'),
                'cyanite_key': track_data.get('key'),
                'cyanite_mode': track_data.get('mode'),
                'cyanite_acousticness': track_data.get('acousticness'),
                'cyanite_instrumentalness': track_data.get('instrumentalness'),
                'cyanite_liveness': track_data.get('liveness'),
                'cyanite_loudness': track_data.get('loudness'),
                'cyanite_speechiness': track_data.get('speechiness'),
                'cyanite_tags': track_data.get('tags', [])
            }
            
            # Add simplified mood classification
            processed['simplified_mood'] = self._classify_simplified_mood(processed)
            
            return processed
            
        except Exception as e:
            logger.error(f"❌ Error processing track data: {e}")
            return None
    
    def _classify_simplified_mood(self, features):
        """
        Create simplified mood classification from Cyanite's detailed features
        Similar to what we had planned for Spotify
        """
        if not features:
            return 'unknown'
        
        # Use Cyanite's mood if available
        if features.get('cyanite_mood'):
            mood = features['cyanite_mood'].lower()
            # Map Cyanite moods to our simplified categories
            mood_mapping = {
                'happy': 'happy',
                'sad': 'sad',
                'energetic': 'energetic',
                'calm': 'calm',
                'angry': 'angry',
                'peaceful': 'peaceful',
                'melancholy': 'melancholy',
                'upbeat': 'upbeat',
                'contemplative': 'contemplative',
                'euphoric': 'euphoric',
                'groovy': 'groovy',
                'intense': 'intense'
            }
            
            for cyanite_mood, simple_mood in mood_mapping.items():
                if cyanite_mood in mood:
                    return simple_mood
        
        # Fallback to valence/energy if specific mood not found
        valence = features.get('cyanite_valence', 0.5)
        energy = features.get('cyanite_energy', 0.5)
        danceability = features.get('cyanite_danceability', 0.5)
        
        if valence >= 0.7 and energy >= 0.6:
            return 'euphoric'
        elif valence >= 0.6 and danceability >= 0.7:
            return 'happy'
        elif valence >= 0.5 and energy >= 0.7:
            return 'energetic'
        elif valence >= 0.6 and energy <= 0.4:
            return 'peaceful'
        elif valence >= 0.4 and energy <= 0.4:
            return 'calm'
        elif valence <= 0.3 and energy <= 0.4:
            return 'melancholy'
        elif valence <= 0.3 and energy >= 0.6:
            return 'angry'
        elif valence <= 0.4:
            return 'sad'
        elif energy >= 0.8:
            return 'intense'
        elif danceability >= 0.7:
            return 'groovy'
        elif valence >= 0.5:
            return 'upbeat'
        else:
            return 'contemplative'
    
    def enrich_dataset(self, df, artist_col='artist', track_col='track', 
                      max_tracks=None, delay=0.5):
        """
        Enrich a dataset with Cyanite.ai music analysis and mood classifications
        """
        logger.info(f"🎵 Starting Cyanite enrichment for {len(df)} tracks...")
        
        # Limit dataset size if specified
        if max_tracks:
            df = df.head(max_tracks)
            logger.info(f"📊 Processing limited dataset of {max_tracks} tracks")
        
        # Initialize new columns
        enriched_data = []
        successful_matches = 0
        
        for idx, row in df.iterrows():
            artist = row[artist_col]
            track = row[track_col]
            
            if idx % 100 == 0:  # Reduced logging frequency
                logger.info(f"📈 Processing track {idx + 1}/{len(df)}: {artist} - {track}")
            
            # Search and analyze track with Cyanite
            cyanite_data = self.search_and_analyze_track(artist, track)
            
            enriched_row = row.to_dict()
            
            if cyanite_data:
                # Add all Cyanite data
                enriched_row.update(cyanite_data)
                successful_matches += 1
                
                mood = cyanite_data.get('simplified_mood', 'unknown')
                logger.debug(f"✅ Enriched: {artist} - {track} → {mood}")
            else:
                # No Cyanite match found
                enriched_row['simplified_mood'] = 'not_found'
            
            enriched_data.append(enriched_row)
            
            # Rate limiting delay (Cyanite has rate limits)
            if delay > 0:
                time.sleep(delay)
        
        enriched_df = pd.DataFrame(enriched_data)
        
        success_rate = (successful_matches / len(df)) * 100
        logger.info(f"🎉 Enrichment complete! Successfully matched {successful_matches}/{len(df)} tracks")
        logger.info(f"📊 Success rate: {success_rate:.1f}%")
        
        return enriched_df
    
    def analyze_mood_distribution(self, df):
        """Analyze the mood distribution in the enriched dataset"""
        if 'simplified_mood' not in df.columns:
            logger.error("❌ No mood data found. Run enrichment first.")
            return
            
        mood_counts = df['simplified_mood'].value_counts()
        
        logger.info("🎭 MOOD DISTRIBUTION:")
        logger.info("=" * 50)
        for mood, count in mood_counts.items():
            percentage = (count / len(df)) * 100
            logger.info(f"   {mood:15} | {count:5} tracks ({percentage:5.1f}%)")
        
        return mood_counts

def main():
    """Test the Cyanite enricher"""
    print("🧪 CYANITE.AI MOOD ENRICHER TEST")
    print("=" * 50)
    
    api_key = input("Enter your Cyanite.ai API key: ").strip()
    
    if not api_key:
        print("❌ API key is required")
        return
    
    # Test with a few popular tracks
    test_tracks = [
        {"artist": "The Beatles", "track": "Hey Jude"},
        {"artist": "Lana Del Rey", "track": "Hope Is a Dangerous Thing for a Woman Like Me to Have - But I Have It"},
        {"artist": "Bloc Party", "track": "Biko"},
        {"artist": "LCD Soundsystem", "track": "Dance Yrself Clean"},
        {"artist": "Bon Iver", "track": "Skinny Love"}
    ]
    
    test_df = pd.DataFrame(test_tracks)
    
    enricher = CyaniteMoodEnricher(api_key)
    
    print("\n🔍 Testing individual track searches...")
    for _, row in test_df.iterrows():
        artist = row['artist']
        track = row['track']
        
        print(f"\n🎵 Searching: {artist} - {track}")
        result = enricher.search_and_analyze_track(artist, track)
        
        if result:
            mood = result.get('simplified_mood', 'unknown')
            valence = result.get('cyanite_valence', 'N/A')
            energy = result.get('cyanite_energy', 'N/A')
            print(f"   ✅ Mood: {mood} (valence: {valence}, energy: {energy})")
        else:
            print(f"   ❌ No match found")
    
    print("\n📊 Testing dataframe enrichment...")
    enriched_df = enricher.enrich_dataset(test_df, max_tracks=5)
    
    print("\n🎭 Results:")
    for _, row in enriched_df.iterrows():
        artist = row['artist']
        track = row['track']
        mood = row.get('simplified_mood', 'unknown')
        print(f"   {artist} - {track}: {mood}")
    
    enricher.analyze_mood_distribution(enriched_df)

if __name__ == "__main__":
    main() 