#!/usr/bin/env python3
"""
Improved Cyanite.ai Music Analysis Script

This script combines the best matching logic from cyanite_mood_enricher.py
with dataset processing capabilities to provide accurate music analysis
for the music recommendation system.

Key improvements:
- Multiple search patterns for better accuracy
- Smart artist/title validation  
- Full audio analysis with mood and genre tags
- Comprehensive error handling and statistics
- Dataset processing capabilities
"""

import pandas as pd
import requests
import json
import time
import os
from dotenv import load_dotenv
from tqdm import tqdm
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ImprovedCyaniteEnricher:
    """Professional music analysis using Cyanite.ai with improved matching accuracy"""
    
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv('CYANITE_API_KEY')
        if not self.api_key:
            raise ValueError("CYANITE_API_KEY not found in environment variables")
        
        self.base_url = "https://api.cyanite.ai/graphql"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Cache for avoiding duplicate API calls
        self.cache = {}
        self.load_cache()
        
        # Comprehensive statistics
        self.stats = {
            'searches_performed': 0,
            'tracks_found': 0,
            'analysis_authorized': 0,
            'analysis_not_authorized': 0,
            'no_matches': 0,
            'errors': 0,
            'cache_hits': 0
        }
    
    def load_cache(self):
        """Load existing cache"""
        cache_file = "cache/cyanite_improved_cache.json"
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    self.cache = json.load(f)
                logger.info(f"Loaded {len(self.cache)} cached results")
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")
                self.cache = {}
        else:
            # Create cache directory if it doesn't exist
            os.makedirs("cache", exist_ok=True)
    
    def save_cache(self):
        """Save cache to disk"""
        cache_file = "cache/cyanite_improved_cache.json"
        try:
            with open(cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
            logger.info(f"Saved {len(self.cache)} cached results")
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
    
    def search_and_analyze_track(self, artist: str, track: str, timeout=30):
        """Search for a track and get comprehensive music analysis"""
        
        # Check cache first
        cache_key = f"{artist.lower()}||{track.lower()}"
        if cache_key in self.cache:
            self.stats['cache_hits'] += 1
            return self.cache[cache_key]
        
        self.stats['searches_performed'] += 1
        
        # Try multiple search patterns for better accuracy
        search_patterns = [
            f'"{artist}" "{track}"',           # Exact match with quotes
            f'{artist} - {track}',             # Dash separator format
            f'{artist} {track}',               # Simple concatenation
            f'artist:"{artist}" title:"{track}"', # Field-specific search (if supported)
            f'{track} {artist}',               # Reverse order sometimes works better
        ]
        
        for pattern in search_patterns:
            logger.debug(f"Trying search pattern: '{pattern}'")
            result = self._search_single_pattern(pattern, artist, track, timeout)
            if result:
                # Cache successful result
                self.cache[cache_key] = result
                return result
        
        # If no pattern worked, cache negative result to avoid repeated searches
        negative_result = {
            'cyanite_id': None,
            'matched_title': None,
            'original_artist': artist,
            'original_track': track,
            'search_successful': False,
            'mood_tags': [],
            'genre_tags': [],
            'simplified_mood': 'not_found',
            'analyzed_at': datetime.now().isoformat()
        }
        
        self.cache[cache_key] = negative_result
        self.stats['no_matches'] += 1
        logger.warning(f"No valid results found for '{artist} - {track}'")
        return negative_result
    
    def _search_single_pattern(self, search_text: str, original_artist: str, original_track: str, timeout=30):
        """Try a single search pattern and return result if found"""
        
        # GraphQL query using freeTextSearch to find Spotify tracks
        query = """
        query FreeTextSearchTrackImproved($searchText: String!) {
          freeTextSearch(
            first: 10
            target: { spotify: {} }
            searchText: $searchText
          ) {
            ... on FreeTextSearchError {
              message
              code
            }
            ... on FreeTextSearchConnection {
              edges {
                node {
                  id
                  title
                  __typename
                }
              }
            }
          }
        }
        """
        
        variables = {"searchText": search_text}

        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json={"query": query, "variables": variables},
                timeout=timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("errors"):
                    logger.error(f"GraphQL error for '{search_text}': {data['errors']}")
                    self.stats['errors'] += 1
                    return None 
                
                search_data = data.get("data", {}).get("freeTextSearch")
                
                if not search_data:
                    return None

                if search_data.get("__typename") == "FreeTextSearchError":
                    logger.error(f"Search failed for '{search_text}': {search_data.get('message')}")
                    self.stats['errors'] += 1
                    return None

                edges = search_data.get("edges", [])
                if edges:
                    logger.debug(f"Found {len(edges)} potential matches for '{search_text}'")
                    
                    # Find the best matching track using smart validation
                    for edge in edges:
                        node = edge.get("node", {})
                        if not node:
                            continue
                        
                        track_id = node.get("id")
                        actual_title = node.get("title", "")
                        
                        # Validate if this is a good match
                        if self._validate_track_match(actual_title, original_artist, original_track):
                            logger.info(f"Found valid match: '{actual_title}' for '{original_artist} - {original_track}'")
                            self.stats['tracks_found'] += 1
                            
                            # Get full audio analysis
                            analysis_result = self._fetch_audio_analysis(track_id, timeout)
                            
                            if analysis_result:
                                return {
                                    'cyanite_id': track_id,
                                    'matched_title': actual_title,
                                    'original_artist': original_artist,
                                    'original_track': original_track,
                                    'search_successful': True,
                                    'mood_tags': analysis_result.get("moodTags", []),
                                    'genre_tags': analysis_result.get("genreTags", []),
                                    'simplified_mood': self._classify_simplified_mood(analysis_result.get("moodTags", [])),
                                    'authorization_status': 'authorized',
                                    'analyzed_at': datetime.now().isoformat()
                                }
                            elif analysis_result is False:
                                # Not authorized but track found
                                self.stats['analysis_not_authorized'] += 1
                                return {
                                    'cyanite_id': track_id,
                                    'matched_title': actual_title,
                                    'original_artist': original_artist,
                                    'original_track': original_track,
                                    'search_successful': True,
                                    'mood_tags': [],
                                    'genre_tags': [],
                                    'simplified_mood': 'not_authorized',
                                    'authorization_status': 'not_authorized',
                                    'analyzed_at': datetime.now().isoformat()
                                }
                            else:
                                # Analysis failed, try next result
                                continue
                    
                    # No good matches found in results
                    logger.debug(f"No valid matches found in {len(edges)} results for '{original_artist} - {original_track}'")
                    return None
                else:
                    logger.debug(f"No results returned for '{search_text}'")
                    return None
                            
            else:
                logger.error(f"API request failed for '{search_text}': {response.status_code}")
                self.stats['errors'] += 1
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception for '{search_text}': {e}")
            self.stats['errors'] += 1
            
        return None
    
    def _validate_track_match(self, actual_title: str, original_artist: str, original_track: str):
        """Validate if the found track is a good match using smart comparison"""
        
        actual_title_lower = actual_title.lower()
        original_artist_lower = original_artist.lower()
        original_track_lower = original_track.lower()
        
        # Check for artist match
        artist_match = False
        if original_artist_lower in actual_title_lower:
            artist_match = True
        elif original_artist_lower.replace(" ", "") in actual_title_lower.replace(" ", ""):
            artist_match = True
        elif original_artist_lower.split()[0] in actual_title_lower:
            artist_match = True
            
        # Check for title match
        title_match = False
        if original_track_lower in actual_title_lower:
            title_match = True
        elif original_track_lower.replace(" ", "") in actual_title_lower.replace(" ", ""):
            title_match = True
        elif len(original_track_lower.split()) > 1 and " ".join(original_track_lower.split()[:2]) in actual_title_lower:
            title_match = True
        elif original_track_lower.split()[0] in actual_title_lower:
            title_match = True
        
        # Accept if we have either a good artist match or title match
        # (Sometimes Cyanite titles don't include artist, or vice versa)
        return artist_match or title_match
    
    def _fetch_audio_analysis(self, track_id: str, timeout=30):
        """Fetch comprehensive audio analysis for a track"""
        
        query = """
        query SpotifyTrackAnalysisImproved($trackId: ID!) {
          spotifyTrack(id: $trackId) {
            __typename
            ... on SpotifyTrack {
              id
              title
              audioAnalysisV7 {
                __typename
                ... on AudioAnalysisV7Finished {
                  result {
                    moodTags
                    genreTags
                  }
                }
                ... on AudioAnalysisV7Failed {
                  error {
                    message
                  }
                }
                ... on AudioAnalysisV7Processing {
                  __typename
                }
                ... on AudioAnalysisV7Enqueued {
                  __typename
                }
                ... on AudioAnalysisV7NotStarted {
                  __typename
                }
                ... on AudioAnalysisV7NotAuthorized {
                  message
                }
              }
            }
            ... on SpotifyTrackError {
              message
            }
          }
        }
        """
        
        variables = {"trackId": track_id}

        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json={"query": query, "variables": variables},
                timeout=timeout
            )
            
            if response.status_code != 200:
                logger.error(f"Audio analysis request failed for '{track_id}': {response.status_code}")
                return None
            
            data = response.json()
            if data.get("errors"):
                logger.error(f"GraphQL errors for audio analysis '{track_id}': {data['errors']}")
                return None
            
            spotify_track_result = data.get("data", {}).get("spotifyTrack")
            if not spotify_track_result:
                logger.warning(f"No spotifyTrack data for id '{track_id}'")
                return None

            result_typename = spotify_track_result.get("__typename")
            
            if result_typename == "SpotifyTrackError":
                error_msg = spotify_track_result.get("message", "Unknown error")
                logger.error(f"SpotifyTrackError for id '{track_id}': {error_msg}")
                return None
            
            elif result_typename == "SpotifyTrack":
                analysis_node = spotify_track_result.get("audioAnalysisV7")
                if not analysis_node:
                    logger.warning(f"No audioAnalysisV7 field for track '{track_id}'")
                    return None

                typename = analysis_node.get("__typename")
                if typename == "AudioAnalysisV7Finished":
                    result = analysis_node.get("result", {})
                    self.stats['analysis_authorized'] += 1
                    return {
                        "moodTags": result.get("moodTags", []),
                        "genreTags": result.get("genreTags", []),
                    }
                elif typename == "AudioAnalysisV7Failed":
                    err_msg = analysis_node.get("error", {}).get("message", "unknown")
                    logger.error(f"AudioAnalysisV7 failed for track '{track_id}': {err_msg}")
                elif typename in ["AudioAnalysisV7Processing", "AudioAnalysisV7Enqueued", "AudioAnalysisV7NotStarted"]:
                    logger.warning(f"AudioAnalysisV7 {typename.replace('AudioAnalysisV7', '').lower()} for track '{track_id}'")
                elif typename == "AudioAnalysisV7NotAuthorized":
                    logger.debug(f"AudioAnalysisV7 not authorized for track '{track_id}'")
                    self.stats['analysis_not_authorized'] += 1
                    return False  # Explicitly return False to indicate not authorized
                else:
                    logger.warning(f"Unhandled AudioAnalysisV7 typename '{typename}' for track '{track_id}'")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception for audio analysis '{track_id}': {e}")
            
        return None
    
    def _classify_simplified_mood(self, mood_tags):
        """Create simplified mood classification from Cyanite's mood tags"""
        
        if not mood_tags:
            return 'unknown'
        
        mood_tags_lower = [tag.lower() for tag in mood_tags]
        
        # Enhanced mood mapping based on common Cyanite tags
        mood_mapping = {
            'happy': ['happy', 'joyful', 'cheerful', 'gleeful', 'upbeat', 'positive'],
            'sad': ['sad', 'melancholic', 'sorrowful', 'melancholy', 'depressed'],
            'energetic': ['energetic', 'driving', 'powerful', 'intense', 'aggressive'],
            'calm': ['calm', 'peaceful', 'serene', 'relaxed', 'mellow', 'soft'],
            'angry': ['angry', 'dark', 'heavy', 'aggressive'],
            'romantic': ['romantic', 'sensual', 'intimate', 'loving'],
            'dreamy': ['dreamy', 'ethereal', 'atmospheric', 'ambient'],
            'epic': ['epic', 'heroic', 'dramatic', 'cinematic'],
            'groovy': ['groovy', 'funky', 'rhythmic'],
            'uplifting': ['uplifting', 'inspiring', 'motivational', 'empowering']
        }
        
        # Find best mood match
        for simplified_mood, keywords in mood_mapping.items():
            for keyword in keywords:
                for tag in mood_tags_lower:
                    if keyword in tag:
                        return simplified_mood
        
        # Fallback: return first tag or 'unknown'
        return mood_tags_lower[0] if mood_tags_lower else 'unknown'
    
    def enrich_dataset(self, df, artist_col='artist', track_col='track', max_tracks=None, delay=0.5):
        """Enrich dataset with comprehensive Cyanite music analysis"""
        
        logger.info(f"🎵 Starting improved Cyanite enrichment for {len(df)} tracks...")
        
        # Limit dataset if specified
        if max_tracks:
            df = df.head(max_tracks)
            logger.info(f"📊 Processing limited dataset of {max_tracks} tracks")
        
        enriched_data = []
        
        # Process tracks with progress bar
        for idx, row in tqdm(df.iterrows(), total=len(df), desc="Enriching tracks"):
            artist = str(row[artist_col])
            track = str(row[track_col])
            
            if idx % 50 == 0:  # Progress logging
                logger.info(f"📈 Processing track {idx + 1}/{len(df)}: {artist} - {track}")
                self._log_progress_stats()
            
            # Get comprehensive analysis
            analysis_result = self.search_and_analyze_track(artist, track)
            
            # Combine original data with analysis
            enriched_row = row.to_dict()
            enriched_row.update(analysis_result)
            enriched_data.append(enriched_row)
            
            # Rate limiting delay
            if delay > 0:
                time.sleep(delay)
            
            # Save progress periodically
            if idx % 100 == 0 and idx > 0:
                self.save_cache()
        
        # Final save
        self.save_cache()
        
        # Create enriched dataframe
        enriched_df = pd.DataFrame(enriched_data)
        
        # Log final statistics
        self._log_final_stats(len(df))
        
        return enriched_df
    
    def _log_progress_stats(self):
        """Log current progress statistics"""
        total = self.stats['searches_performed']
        if total > 0:
            found_rate = (self.stats['tracks_found'] / total) * 100
            cache_rate = (self.stats['cache_hits'] / (total + self.stats['cache_hits'])) * 100
            logger.info(f"   📊 Progress: {found_rate:.1f}% found, {cache_rate:.1f}% cached")
    
    def _log_final_stats(self, total_tracks):
        """Log comprehensive final statistics"""
        stats = self.stats
        total_searches = stats['searches_performed']
        
        logger.info(f"🎉 Enrichment complete!")
        logger.info(f"📊 Final Statistics:")
        logger.info(f"   - Total tracks processed: {total_tracks}")
        logger.info(f"   - Searches performed: {total_searches}")
        logger.info(f"   - Cache hits: {stats['cache_hits']}")
        logger.info(f"   - Tracks found: {stats['tracks_found']}")
        logger.info(f"   - Analysis authorized: {stats['analysis_authorized']}")
        logger.info(f"   - Analysis not authorized: {stats['analysis_not_authorized']}")
        logger.info(f"   - No matches: {stats['no_matches']}")
        logger.info(f"   - Errors: {stats['errors']}")
        
        if total_searches > 0:
            success_rate = (stats['tracks_found'] / total_searches) * 100
            logger.info(f"   - Success rate: {success_rate:.1f}%")


def main():
    """Test the improved enricher with a small sample"""
    
    # Initialize enricher
    enricher = ImprovedCyaniteEnricher()
    
    # Load user's scrobbles
    logger.info("Loading user's scrobbles...")
    df = pd.read_csv('data/zdjuna_scrobbles.csv')
    
    # Test with a small sample first
    test_df = df.head(20)
    logger.info(f"Testing with {len(test_df)} tracks...")
    
    # Enrich the sample
    enriched_df = enricher.enrich_dataset(test_df, max_tracks=20, delay=1.0)
    
    # Save results
    output_file = f'data/zdjuna_cyanite_improved_test_{len(test_df)}_tracks.csv'
    enriched_df.to_csv(output_file, index=False)
    logger.info(f"💾 Results saved to: {output_file}")
    
    # Show sample results
    successful_matches = enriched_df[enriched_df['search_successful'] == True]
    logger.info(f"✅ Successfully matched {len(successful_matches)}/{len(test_df)} tracks")
    
    if len(successful_matches) > 0:
        logger.info("\n🎵 Sample successful matches:")
        for _, row in successful_matches.head(5).iterrows():
            logger.info(f"   {row['original_artist']} - {row['original_track']}")
            logger.info(f"   → {row['matched_title']}")
            logger.info(f"   → Mood: {row['simplified_mood']}")
            logger.info(f"   → Tags: {row['mood_tags'][:3]}...")  # Show first 3 tags
            logger.info("")


if __name__ == "__main__":
    main()
