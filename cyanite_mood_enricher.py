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
    
    def __init__(self, api_key, graphql_url="https://api.cyanite.ai/graphql"):
        """Initialize Cyanite client"""
        self.api_key = api_key
        self.graphql_url = graphql_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.logger = logger
        
    def search_and_analyze_track(self, title: str, artist_name: str, timeout=30):
        """Search for a track and get its mood analysis using AudioAnalysisV7 and advancedSearch."""
        
        searchText = f"{artist_name} {title}"

        # GraphQL query using freeTextSearch to find the Spotify track by text
        query = """
        query FreeTextSearchTrackV7($searchText: String!) {
          freeTextSearch(
            first: 1
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
                }
              }
            }
          }
        }
        """
        variables = {"searchText": searchText}

        self.logger.info(f"[Cyanite Debug V7] Searching with freeTextSearch for: '{searchText}'")
        try:
            response = requests.post(
                self.graphql_url,
                headers=self.headers,
                json={"query": query, "variables": variables},
                timeout=timeout
            )
            self.logger.info(f"[Cyanite Debug V7] API Raw Response for '{searchText}': Status={response.status_code}, Text={response.text[:1000]}...")

            if response.status_code == 200:
                data = response.json()
                self.logger.info(f"[Cyanite Debug V7] API JSON Response for '{searchText}': {json.dumps(data, indent=2)}")
                
                if data.get("errors"):
                    self.logger.error(f"Cyanite API returned GraphQL-level errors for '{searchText}': {data['errors']}")
                    return None 
                
                search_data = data.get("data", {}).get("freeTextSearch")
                
                if not search_data:
                    self.logger.warning(f"No 'freeTextSearch' data in response for '{searchText}'. API Response Data: {data.get('data')}")
                    return None

                if search_data.get("__typename") == "FreeTextSearchError":
                    self.logger.error(f"freeTextSearch failed for '{searchText}': Code: {search_data.get('code')}, Message: {search_data.get('message')}")
                    return None

                edges = search_data.get("edges", [])
                if edges:
                    node_wrapper = edges[0].get("node")
                    if not node_wrapper:
                        self.logger.warning(f"No 'node' in the first edge for '{searchText}'. Edges: {edges}")
                        return None

                    # Node payload is directly the SpotifyTrack
                    track_node = node_wrapper

                    if not track_node:
                        self.logger.warning(f"No track information found in response for '{searchText}'. Node wrapper: {node_wrapper}")
                        return None

                    typename = track_node.get("__typename")
                    if typename != "AdvancedSearchNodeSpotifyTrack":
                        self.logger.warning(f"Unexpected track __typename '{typename}' for '{searchText}'.")
                        # proceed but warn

                    track_id = track_node.get("id")
                    actual_title = track_node.get("title")

                    # Step 2: fetch audio analysis via spotifyTrack query
                    analysis_result = self._fetch_spotify_analysis_v7(track_id, timeout=timeout)
                    if not analysis_result:
                        return None

                    mood_tags_list = analysis_result.get("moodTags", [])
                    genre_tags_list = analysis_result.get("genreTags", [])

                    return {
                        "id": track_id,
                        "title": actual_title,
                        "artist": artist_name,
                        "mood_tags": mood_tags_list,
                        "genre_tags": genre_tags_list,
                        "simplified_mood": self._classify_simplified_mood_from_tags(mood_tags_list)
                    }
                else:
                    self.logger.warning(f"No track edges found in API response for '{searchText}' using freeTextSearch query.")
                    return None
            else:
                self.logger.error(f"Cyanite API request failed for track '{searchText}': {response.status_code} - {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request exception during Cyanite search for '{searchText}': {e}")
            return None
    
    def _process_track_data(self, track_data):
        """Process and clean track data from Cyanite API"""
        try:
            processed = {
                'cyanite_id': track_data.get('id'),
                'matched_title': track_data.get('title'),
                'matched_artist': track_data.get('artist'),
                'cyanite_genre_tags': track_data.get('genre_tags'),
                'cyanite_mood_tags': track_data.get('mood_tags'),
                'cyanite_enriched_at': datetime.now().isoformat()
            }
            
            # Add simplified mood classification based on new mood_tags
            processed['simplified_mood'] = self._classify_simplified_mood_from_tags(processed.get('cyanite_mood_tags', []))
            
            return processed
            
        except Exception as e:
            logger.error(f"❌ Error processing track data: {e}")
            return None
    
    def _classify_simplified_mood(self, features):
        """
        DEPRECATED: Create simplified mood classification from Cyanite's detailed features
        Similar to what we had planned for Spotify.
        This method is kept for reference but might not be directly usable with V7 moodTags only.
        """
        if not features:
            return 'unknown'
        
        # This part relied on specific mood fields like 'cyanite_mood', 'valence', 'energy'
        # which are not directly available from the current V7 query.
        # It needs to be adapted or replaced if simplified mood is still required from moodTags.
        
        # Example: if features.get('cyanite_mood'): # This field is no longer populated directly
        #     mood = features['cyanite_mood'].lower() 
        #     # ... existing mapping ...

        # Fallback logic also used fields not directly available
        # valence = features.get('cyanite_valence', 0.5)
        # energy = features.get('cyanite_energy', 0.5)
        # danceability = features.get('cyanite_danceability', 0.5)
        # # ... existing logic ...

        logger.warning("'_classify_simplified_mood' is deprecated with current V7 query. Use '_classify_simplified_mood_from_tags'.")
        return 'unknown' # Default for deprecated method

    def _classify_simplified_mood_from_tags(self, mood_tags):
        """
        Create simplified mood classification from Cyanite's V7 moodTags.
        Maps known mood tags to simplified categories.
        """
        if not mood_tags:
            return 'unknown'
        
        mood_tags_lower = [tag.lower() for tag in mood_tags]
        
        # Define mappings from Cyanite mood tags (or parts of them) to simplified moods
        # This mapping will likely need refinement based on actual tags returned by Cyanite V7
        mood_mapping = {
            'happy': 'happy', 'joyful': 'happy', 'cheerful': 'happy', 'gleeful': 'happy',
            'sad': 'sad', 'melancholic': 'melancholy', 'sorrowful': 'sad',
            'energetic': 'energetic', 'upbeat': 'energetic', 'driving': 'energetic', 'powerful': 'energetic',
            'calm': 'calm', 'peaceful': 'peaceful', 'serene': 'calm', 'relaxed': 'calm',
            'angry': 'angry', 'aggressive': 'angry', 'dark': 'angry', # Dark can be ambiguous
            'romantic': 'romantic', 'sensual': 'romantic',
            'dreamy': 'dreamy', 'ethereal': 'dreamy',
            'epic': 'epic', 'heroic': 'epic',
            'groovy': 'groovy', 'funky': 'groovy',
            'intense': 'intense', 'suspenseful': 'intense',
            'uplifting': 'uplifting',
            'empowering': 'empowering',
            # Add more mappings as needed based on observed Cyanite V7 mood tags
        }

        for tag_part, simple_mood in mood_mapping.items():
            for full_tag in mood_tags_lower:
                if tag_part in full_tag:
                    return simple_mood
        
        # Fallback if no specific mapping found, maybe return the most prominent tag or 'unknown'
        # For now, returning the first tag if available, otherwise 'unknown'
        if mood_tags_lower:
            # You might want a more sophisticated way to pick a "primary" mood if multiple tags are present
            # and none map directly.
            # For now, just an example:
            first_tag = mood_tags_lower[0]
            # A very basic attempt to map some common general terms if not caught above
            if 'positive' in first_tag: return 'happy'
            if 'negative' in first_tag: return 'sad'
            if 'high energy' in first_tag: return 'energetic'
            if 'low energy' in first_tag: return 'calm'
            return first_tag # Or 'unknown' if returning the tag itself is not desired
            
        return 'unknown'

    def _fetch_spotify_analysis_v7(self, track_id: str, timeout=30):
        """Fetch AudioAnalysisV7 for a given Spotify track id. Returns dict with moodTags/genreTags or None if not finished."""
        query = """
        query SpotifyTrackAnalysis($trackId: ID!) {
          spotifyTrack(id: $trackId) {
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
                error { message }
              }
              ... on AudioAnalysisV7NotStarted { __typename }
              ... on AudioAnalysisV7Enqueued { __typename }
              ... on AudioAnalysisV7Processing { __typename }
              ... on AudioAnalysisV7NotAuthorized { __typename }
            }
          }
        }
        """
        variables = {"trackId": track_id}

        try:
            response = requests.post(
                self.graphql_url,
                headers=self.headers,
                json={"query": query, "variables": variables},
                timeout=timeout,
            )
            if response.status_code != 200:
                self.logger.error(f"SpotifyTrack query failed for '{track_id}': {response.status_code} - {response.text}")
                return None
            data = response.json()
            if data.get("errors"):
                self.logger.error(f"GraphQL errors fetching SpotifyTrack '{track_id}': {data['errors']}")
                return None
            track_data = data.get("data", {}).get("spotifyTrack")
            if not track_data:
                self.logger.warning(f"No spotifyTrack data for id '{track_id}'.")
                return None

            analysis_node = track_data.get("audioAnalysisV7")
            if not analysis_node:
                self.logger.warning(f"No audioAnalysisV7 field for Spotify track '{track_id}'.")
                return None

            typename = analysis_node.get("__typename")
            if typename == "AudioAnalysisV7Finished":
                result = analysis_node.get("result", {})
                return {
                    "moodTags": result.get("moodTags", []),
                    "genreTags": result.get("genreTags", []),
                }
            elif typename == "AudioAnalysisV7Failed":
                err_msg = analysis_node.get("error", {}).get("message", "unknown")
                self.logger.error(f"AudioAnalysisV7 failed for track '{track_id}': {err_msg}")
            elif typename == "AudioAnalysisV7NotStarted":
                self.logger.warning(f"AudioAnalysisV7 not started for track '{track_id}'.")
            elif typename == "AudioAnalysisV7Enqueued":
                self.logger.warning(f"AudioAnalysisV7 enqueued for track '{track_id}'.")
            elif typename == "AudioAnalysisV7Processing":
                self.logger.warning(f"AudioAnalysisV7 processing for track '{track_id}'.")
            elif typename == "AudioAnalysisV7NotAuthorized":
                self.logger.warning(f"AudioAnalysisV7 not authorized for track '{track_id}'.")
            else:
                self.logger.warning(f"Unhandled AudioAnalysisV7 typename '{typename}' for track '{track_id}'.")
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request exception fetching AudioAnalysisV7 for track '{track_id}': {e}")
        return None

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
            artist_name_from_df = str(row[artist_col]) # Renamed for clarity
            title_from_df = str(row[track_col])   # Renamed for clarity
            
            if idx % 100 == 0:  # Reduced logging frequency
                logger.info(f"📈 Processing track {idx + 1}/{len(df)}: {artist_name_from_df} - {title_from_df}")
            
            # Search and analyze track with Cyanite
            cyanite_data = self.search_and_analyze_track(title=title_from_df, artist_name=artist_name_from_df)
            
            enriched_row = row.to_dict()
            
            if cyanite_data:
                # Add all Cyanite data
                enriched_row.update(cyanite_data)
                successful_matches += 1
                
                mood = cyanite_data.get('simplified_mood', 'unknown')
                logger.debug(f"✅ Enriched: {artist_name_from_df} - {title_from_df} → {mood}")
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
            logger.warning("Column 'simplified_mood' not found for mood distribution analysis.")
            return pd.Series(dtype='int64')

        mood_distribution = df['simplified_mood'].value_counts(normalize=True) * 100
        logger.info("🎵 Mood Distribution (based on simplified_mood from Cyanite V7 moodTags):")
        logger.info(mood_distribution)
        return mood_distribution

    def get_top_moods_and_genres(self, df, top_n=10):
        """Get top N moods and genres from the enriched dataset."""
        if 'simplified_mood' not in df.columns:
            logger.warning("Column 'simplified_mood' not found for top moods analysis.")
            top_moods = pd.Series(dtype='object')
        else:
            top_moods = df['simplified_mood'].value_counts().nlargest(top_n)

        if 'cyanite_genre_tags' not in df.columns:
            logger.warning("Column 'cyanite_genre_tags' not found for top genres analysis.")
            top_genres = pd.Series(dtype='object')
        else:
            # Explode the list of genre tags into separate rows to count individual tags
            all_genres = df['cyanite_genre_tags'].explode().dropna()
            top_genres = all_genres.value_counts().nlargest(top_n)

        logger.info(f"🎵 Top {top_n} Moods (from simplified_mood):")
        logger.info(top_moods)
        logger.info(f"🎵 Top {top_n} Genres (from cyanite_genre_tags):")
        logger.info(top_genres)
        return top_moods, top_genres

def main():
    """Example usage of CyaniteMoodEnricher"""
    logger.info("🧪 Starting CyaniteMoodEnricher example...")

    # --- Configuration ---
    # IMPORTANT: Replace with your actual Cyanite API Key
    # Consider loading from environment variable or config file for security
    CYANITE_API_KEY = "YOUR_CYANITE_API_KEY" 
    if CYANITE_API_KEY == "YOUR_CYANITE_API_KEY":
        logger.warning("🚨 Please replace 'YOUR_CYANITE_API_KEY' with your actual Cyanite API key in the script.")
        # Attempt to load from environment variable as a fallback
        import os
        CYANITE_API_KEY = os.getenv("CYANITE_API_KEY")
        if not CYANITE_API_KEY:
            logger.error("❌ Cyanite API Key not found in environment variable CYANITE_API_KEY either. Exiting.")
            return

    enricher = CyaniteMoodEnricher(api_key=CYANITE_API_KEY)

    # --- Test 1: Search and Analyze a Single Track ---
    logger.info("🎵 --- Test 1: Search and Analyze Single Track ---")
    # track_title = "Bohemian Rhapsody" # Example with a space
    # artist_name = "Queen"
    track_title = "Hey Jude"
    artist_name = "The Beatles"
    
    analysis_result = enricher.search_and_analyze_track(title=track_title, artist_name=artist_name)
    if analysis_result:
        logger.info(f"✅ Analysis for '{track_title}' by '{artist_name}':")
        logger.info(f"  ID: {analysis_result.get('id')}")
        logger.info(f"  Matched Title: {analysis_result.get('title')}")
        logger.info(f"  Mood Tags: {analysis_result.get('mood_tags')}")
        logger.info(f"  Genre Tags: {analysis_result.get('genre_tags')}")
        simplified = enricher._classify_simplified_mood_from_tags(analysis_result.get('mood_tags', []))
        logger.info(f"  Simplified Mood (from tags): {simplified}")

    else:
        logger.error(f"❌ Failed to get analysis for '{track_title}' by '{artist_name}'. Check logs above for details.")

    # --- Test 2: Enrich a Sample DataFrame (Optional) ---
    # Create a dummy DataFrame for testing enrichment
    # sample_data = {
    # 'artist': ['Daft Punk', 'Adele', 'Led Zeppelin', 'Unknown Artist'],
    # 'track': ['Get Lucky', 'Hello', 'Stairway to Heaven', 'Missing Track Test']
    # }
    # sample_df = pd.DataFrame(sample_data)
    #
    # logger.info("🎵 --- Test 2: Enrich Sample DataFrame ---")
    # enriched_df = enricher.enrich_dataset(sample_df.copy(), max_tracks=2, delay=1) # Enrich only 2 for quick test
    # logger.info("Enriched DataFrame:")
    # print(enriched_df[['artist', 'track', 'cyanite_mood_tags', 'cyanite_genre_tags', 'simplified_mood']].head())
    #
    # --- Test 3: Analyze Mood Distribution (Optional, if Test 2 is run) ---
    # if not enriched_df.empty and 'simplified_mood' in enriched_df.columns:
    # logger.info("🎵 --- Test 3: Mood Distribution ---")
    # enricher.analyze_mood_distribution(enriched_df)
    #
    # --- Test 4: Get Top Moods and Genres (Optional, if Test 2 is run) ---
    # if not enriched_df.empty:
    # logger.info("🎵 --- Test 4: Top Moods and Genres ---")
    # enricher.get_top_moods_and_genres(enriched_df)

    logger.info("🎉 CyaniteMoodEnricher example finished.")

if __name__ == "__main__":
    main() 