#!/usr/bin/env python3
"""
Discogs Music Enricher

This module provides functionality to enrich music track data using the Discogs API.
It searches for tracks by artist and title, then retrieves detailed metadata including
genres, styles, and release information.
"""

import requests
import time
import logging
from datetime import datetime
from difflib import SequenceMatcher
import re
from typing import Dict, List, Optional, Any

class DiscogsEnricher:
    """Enriches music data using the Discogs API"""
    
    def __init__(self, user_agent: str = "MusicRecommendationSystem/1.0"):
        """
        Initialize the Discogs enricher
        
        Args:
            user_agent: User agent string for API requests
        """
        self.base_url = "https://api.discogs.com"
        self.headers = {
            "User-Agent": user_agent,
            "Accept": "application/vnd.discogs.v2.discogs+json"
        }
        self.logger = logging.getLogger(__name__)
        self.rate_limit_delay = 1.0  # Discogs allows 60 requests per minute
        self.last_request_time = 0
        
    def _rate_limit(self):
        """Ensure we don't exceed rate limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict]:
        """Make a request to the Discogs API with rate limiting"""
        self._rate_limit()
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                self.logger.warning("Rate limit exceeded, waiting longer...")
                time.sleep(60)  # Wait a minute if rate limited
                return self._make_request(endpoint, params)
            else:
                self.logger.error(f"Discogs API error {response.status_code}: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed: {e}")
            return None
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings"""
        if not str1 or not str2:
            return 0.0
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
    
    def _clean_string(self, text: str) -> str:
        """Clean and normalize string for comparison"""
        if not text:
            return ""
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        # Remove common variations
        text = re.sub(r'\(.*?\)', '', text)  # Remove parentheses content
        text = re.sub(r'\[.*?\]', '', text)  # Remove bracket content
        return text.strip()
    
    def _search_releases(self, artist: str, title: str) -> List[Dict]:
        """Search for releases matching artist and title"""
        # Try different search strategies
        search_queries = [
            f'artist:"{artist}" title:"{title}"',
            f'artist:"{artist}" "{title}"',
            f'"{artist}" "{title}"',
            f'{artist} {title}'
        ]
        
        all_results = []
        
        for query in search_queries:
            self.logger.info(f"Searching Discogs with query: {query}")
            
            params = {
                'q': query,
                'type': 'release',
                'per_page': 25
            }
            
            data = self._make_request('database/search', params)
            if data and 'results' in data:
                results = data['results']
                self.logger.info(f"Found {len(results)} results for query: {query}")
                all_results.extend(results)
                
                # If we found good matches, don't need to try more queries
                if len(results) > 0:
                    break
            else:
                self.logger.warning(f"No results for query: {query}")
        
        return all_results
    
    def _find_best_match(self, results: List[Dict], target_artist: str, target_title: str) -> Optional[Dict]:
        """Find the best matching release from search results"""
        if not results:
            return None
        
        best_match = None
        best_score = 0.0
        
        target_artist_clean = self._clean_string(target_artist)
        target_title_clean = self._clean_string(target_title)
        
        for result in results:
            # Get basic info
            result_title = result.get('title', '')
            result_artist = result.get('artist', '')
            
            # Clean the strings
            result_artist_clean = self._clean_string(result_artist)
            result_title_clean = self._clean_string(result_title)
            
            # Calculate similarity scores
            artist_score = self._calculate_similarity(target_artist_clean, result_artist_clean)
            title_score = self._calculate_similarity(target_title_clean, result_title_clean)
            
            # Combined score (weighted towards title match)
            combined_score = (artist_score * 0.4) + (title_score * 0.6)
            
            self.logger.debug(f"Match candidate: '{result_artist}' - '{result_title}' "
                            f"(artist: {artist_score:.2f}, title: {title_score:.2f}, "
                            f"combined: {combined_score:.2f})")
            
            if combined_score > best_score and combined_score > 0.6:  # Minimum threshold
                best_score = combined_score
                best_match = result
        
        if best_match:
            self.logger.info(f"Best match found: '{best_match.get('artist')}' - '{best_match.get('title')}' "
                           f"(score: {best_score:.2f})")
        else:
            self.logger.warning(f"No good match found for '{target_artist}' - '{target_title}'")
        
        return best_match
    
    def _get_release_details(self, release_id: str) -> Optional[Dict]:
        """Get detailed information about a specific release"""
        data = self._make_request(f'releases/{release_id}', {})
        return data
    
    def _extract_genres_and_styles(self, release_data: Dict) -> Dict[str, List[str]]:
        """Extract genres and styles from release data"""
        genres = release_data.get('genres', [])
        styles = release_data.get('styles', [])
        
        return {
            'genres': genres,
            'styles': styles,
            'combined_tags': genres + styles
        }
    
    def _classify_mood_from_genres(self, genres: List[str], styles: List[str]) -> str:
        """Classify mood based on genres and styles"""
        all_tags = [tag.lower() for tag in (genres + styles)]
        
        # Define mood mappings
        mood_mappings = {
            'energetic': ['rock', 'punk', 'metal', 'electronic', 'dance', 'techno', 'house', 'drum n bass'],
            'calm': ['ambient', 'classical', 'new age', 'folk', 'acoustic', 'meditation'],
            'happy': ['pop', 'disco', 'funk', 'soul', 'reggae', 'ska'],
            'melancholic': ['blues', 'country', 'indie', 'alternative', 'post-rock'],
            'aggressive': ['hardcore', 'metal', 'punk', 'industrial', 'noise'],
            'romantic': ['r&b', 'soul', 'jazz', 'bossa nova', 'lounge']
        }
        
        mood_scores = {}
        for mood, keywords in mood_mappings.items():
            score = sum(1 for tag in all_tags if any(keyword in tag for keyword in keywords))
            if score > 0:
                mood_scores[mood] = score
        
        if mood_scores:
            return max(mood_scores.keys(), key=lambda k: mood_scores[k])
        return 'neutral'
    
    def enrich_track(self, artist: str, title: str) -> Optional[Dict]:
        """
        Enrich a single track with Discogs data
        
        Args:
            artist: Artist name
            title: Track title
            
        Returns:
            Dictionary with enriched track data or None if not found
        """
        self.logger.info(f"Enriching track: '{artist}' - '{title}'")
        
        # Search for releases
        search_results = self._search_releases(artist, title)
        if not search_results:
            self.logger.warning(f"No search results found for '{artist}' - '{title}'")
            return None
        
        # Find best match
        best_match = self._find_best_match(search_results, artist, title)
        if not best_match:
            return None
        
        # Get detailed release information
        release_id = best_match.get('id')
        if not release_id:
            self.logger.error("No release ID found in best match")
            return None
        
        release_details = self._get_release_details(str(release_id))
        if not release_details:
            self.logger.error(f"Could not get release details for ID: {release_id}")
            return None
        
        # Extract genres and styles
        genre_data = self._extract_genres_and_styles(release_details)
        
        # Classify mood
        mood = self._classify_mood_from_genres(genre_data['genres'], genre_data['styles'])
        
        # Build enriched data
        enriched_data = {
            'discogs_id': release_id,
            'matched_artist': best_match.get('artist'),
            'matched_title': best_match.get('title'),
            'discogs_genres': genre_data['genres'],
            'discogs_styles': genre_data['styles'],
            'discogs_tags': genre_data['combined_tags'],
            'simplified_mood': mood,
            'year': release_details.get('year'),
            'country': release_details.get('country'),
            'label': release_details.get('labels', [{}])[0].get('name') if release_details.get('labels') else None,
            'format': release_details.get('formats', [{}])[0].get('name') if release_details.get('formats') else None,
            'discogs_enriched_at': datetime.now().isoformat(),
            'discogs_url': release_details.get('uri')
        }
        
        self.logger.info(f"Successfully enriched '{artist}' - '{title}' with Discogs data")
        return enriched_data
    
    def enrich_tracks_batch(self, tracks: List[Dict[str, str]], max_tracks: Optional[int] = None) -> Dict[str, Dict]:
        """
        Enrich multiple tracks with Discogs data
        
        Args:
            tracks: List of dictionaries with 'artist' and 'title' keys
            max_tracks: Maximum number of tracks to process (for testing)
            
        Returns:
            Dictionary mapping track keys to enriched data
        """
        results = {}
        processed = 0
        
        for track in tracks:
            if max_tracks and processed >= max_tracks:
                break
                
            artist = track.get('artist', '').strip()
            title = track.get('title', '').strip()
            
            if not artist or not title:
                self.logger.warning(f"Skipping track with missing artist or title: {track}")
                continue
            
            track_key = f"{artist} - {title}"
            
            try:
                enriched_data = self.enrich_track(artist, title)
                if enriched_data:
                    results[track_key] = enriched_data
                else:
                    self.logger.warning(f"Could not enrich track: {track_key}")
                    
            except Exception as e:
                self.logger.error(f"Error enriching track '{track_key}': {e}")
                continue
            
            processed += 1
            
            # Progress logging
            if processed % 10 == 0:
                self.logger.info(f"Processed {processed} tracks, found {len(results)} matches")
        
        self.logger.info(f"Batch enrichment complete: {processed} tracks processed, {len(results)} enriched")
        return results


if __name__ == "__main__":
    # Test the enricher
    logging.basicConfig(level=logging.INFO)
    
    enricher = DiscogsEnricher()
    
    # Test with a few tracks
    test_tracks = [
        {"artist": "The Beatles", "title": "Hey Jude"},
        {"artist": "Queen", "title": "Bohemian Rhapsody"},
        {"artist": "Interpol", "title": "Evil"}
    ]
    
    print("Testing Discogs enricher...")
    for track in test_tracks:
        result = enricher.enrich_track(track["artist"], track["title"])
        if result:
            print(f"\n✅ Found: {track['artist']} - {track['title']}")
            print(f"   Genres: {result.get('discogs_genres', [])}")
            print(f"   Styles: {result.get('discogs_styles', [])}")
            print(f"   Mood: {result.get('simplified_mood')}")
        else:
            print(f"\n❌ Not found: {track['artist']} - {track['title']}")  