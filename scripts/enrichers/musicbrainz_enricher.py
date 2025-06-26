#!/usr/bin/env python3
"""
MusicBrainz Music Enricher

This module provides functionality to enrich music track data using the MusicBrainz API.
It searches for recordings by artist and title, then retrieves detailed metadata including
genres, release information, and relationships.
"""

import requests
import time
import logging
from datetime import datetime
from difflib import SequenceMatcher
import re
from typing import Dict, List, Optional, Any
import urllib.parse

class MusicBrainzEnricher:
    """Enriches music data using the MusicBrainz API"""
    
    def __init__(self, user_agent: str = "MusicRecommendationSystem/1.0 (contact@example.com)"):
        """
        Initialize the MusicBrainz enricher
        
        Args:
            user_agent: User agent string for API requests (required by MusicBrainz)
        """
        self.base_url = "https://musicbrainz.org/ws/2"
        self.headers = {
            "User-Agent": user_agent,
            "Accept": "application/json"
        }
        self.logger = logging.getLogger(__name__)
        self.rate_limit_delay = 1.0  # MusicBrainz requires 1 request per second
        self.last_request_time = 0
        
    def _rate_limit(self):
        """Ensure we don't exceed rate limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict]:
        """Make a request to the MusicBrainz API with rate limiting"""
        self._rate_limit()
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 503:
                self.logger.warning("MusicBrainz service unavailable, waiting...")
                time.sleep(5)
                return self._make_request(endpoint, params)
            else:
                self.logger.error(f"MusicBrainz API error {response.status_code}: {response.text}")
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
    
    def _search_recordings(self, artist: str, title: str) -> List[Dict]:
        """Search for recordings matching artist and title"""
        # Try different search strategies
        search_queries = [
            f'artist:"{artist}" AND recording:"{title}"',
            f'artist:"{artist}" AND "{title}"',
            f'"{artist}" AND recording:"{title}"',
            f'{artist} {title}'
        ]
        
        all_results = []
        
        for query in search_queries:
            self.logger.info(f"Searching MusicBrainz with query: {query}")
            
            params = {
                'query': query,
                'fmt': 'json',
                'limit': 25
            }
            
            data = self._make_request('recording', params)
            if data and 'recordings' in data:
                recordings = data['recordings']
                self.logger.info(f"Found {len(recordings)} results for query: {query}")
                all_results.extend(recordings)
                
                # If we found good matches, don't need to try more queries
                if len(recordings) > 0:
                    break
            else:
                self.logger.warning(f"No results for query: {query}")
        
        return all_results
    
    def _find_best_match(self, results: List[Dict], target_artist: str, target_title: str) -> Optional[Dict]:
        """Find the best matching recording from search results"""
        if not results:
            return None
        
        best_match = None
        best_score = 0.0
        
        target_artist_clean = self._clean_string(target_artist)
        target_title_clean = self._clean_string(target_title)
        
        for result in results:
            # Get basic info
            result_title = result.get('title', '')
            
            # Get artist credit
            artist_credit = result.get('artist-credit', [])
            if artist_credit:
                result_artist = artist_credit[0].get('name', '')
            else:
                result_artist = ''
            
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
            artist_credit = best_match.get('artist-credit', [])
            matched_artist = artist_credit[0].get('name', '') if artist_credit else ''
            self.logger.info(f"Best match found: '{matched_artist}' - '{best_match.get('title')}' "
                           f"(score: {best_score:.2f})")
        else:
            self.logger.warning(f"No good match found for '{target_artist}' - '{target_title}'")
        
        return best_match
    
    def _get_recording_details(self, recording_id: str) -> Optional[Dict]:
        """Get detailed information about a specific recording"""
        params = {
            'inc': 'releases+release-groups+artist-credits+tags+genres',
            'fmt': 'json'
        }
        data = self._make_request(f'recording/{recording_id}', params)
        return data
    
    def _extract_tags_and_genres(self, recording_data: Dict) -> Dict[str, List[str]]:
        """Extract tags and genres from recording data"""
        tags = []
        genres = []
        
        # Get tags
        if 'tags' in recording_data:
            tags = [tag['name'] for tag in recording_data['tags']]
        
        # Get genres (newer MusicBrainz feature)
        if 'genres' in recording_data:
            genres = [genre['name'] for genre in recording_data['genres']]
        
        # Also check releases for additional genre info
        releases = recording_data.get('releases', [])
        for release in releases:
            if 'release-group' in release:
                rg = release['release-group']
                if 'tags' in rg:
                    tags.extend([tag['name'] for tag in rg['tags']])
                if 'genres' in rg:
                    genres.extend([genre['name'] for genre in rg['genres']])
        
        # Remove duplicates
        tags = list(set(tags))
        genres = list(set(genres))
        
        return {
            'tags': tags,
            'genres': genres,
            'combined_tags': tags + genres
        }
    
    def _classify_mood_from_tags(self, tags: List[str], genres: List[str]) -> str:
        """Classify mood based on tags and genres"""
        all_tags = [tag.lower() for tag in (tags + genres)]
        
        # Define mood mappings
        mood_mappings = {
            'energetic': ['rock', 'punk', 'metal', 'electronic', 'dance', 'techno', 'house', 'drum and bass', 'energetic', 'upbeat'],
            'calm': ['ambient', 'classical', 'new age', 'folk', 'acoustic', 'meditation', 'peaceful', 'relaxing', 'calm'],
            'happy': ['pop', 'disco', 'funk', 'soul', 'reggae', 'ska', 'happy', 'cheerful', 'uplifting', 'joyful'],
            'melancholic': ['blues', 'country', 'indie', 'alternative', 'post-rock', 'sad', 'melancholic', 'melancholy', 'depressing'],
            'aggressive': ['hardcore', 'metal', 'punk', 'industrial', 'noise', 'aggressive', 'angry', 'violent'],
            'romantic': ['r&b', 'soul', 'jazz', 'bossa nova', 'lounge', 'romantic', 'love', 'sensual']
        }
        
        mood_scores = {}
        for mood, keywords in mood_mappings.items():
            score = sum(1 for tag in all_tags if any(keyword in tag for keyword in keywords))
            if score > 0:
                mood_scores[mood] = score
        
        if mood_scores:
            return max(mood_scores, key=mood_scores.get)
        return 'neutral'
    
    def enrich_track(self, artist: str, title: str) -> Optional[Dict]:
        """
        Enrich a single track with MusicBrainz data
        
        Args:
            artist: Artist name
            title: Track title
            
        Returns:
            Dictionary with enriched track data or None if not found
        """
        self.logger.info(f"Enriching track: '{artist}' - '{title}'")
        
        # Search for recordings
        search_results = self._search_recordings(artist, title)
        if not search_results:
            self.logger.warning(f"No search results found for '{artist}' - '{title}'")
            return None
        
        # Find best match
        best_match = self._find_best_match(search_results, artist, title)
        if not best_match:
            return None
        
        # Get detailed recording information
        recording_id = best_match.get('id')
        if not recording_id:
            self.logger.error("No recording ID found in best match")
            return None
        
        recording_details = self._get_recording_details(recording_id)
        if not recording_details:
            self.logger.error(f"Could not get recording details for ID: {recording_id}")
            return None
        
        # Extract tags and genres
        tag_data = self._extract_tags_and_genres(recording_details)
        
        # Classify mood
        mood = self._classify_mood_from_tags(tag_data['tags'], tag_data['genres'])
        
        # Get artist info
        artist_credit = best_match.get('artist-credit', [])
        matched_artist = artist_credit[0].get('name', '') if artist_credit else ''
        
        # Get release info
        releases = recording_details.get('releases', [])
        first_release_date = None
        country = None
        label = None
        
        if releases:
            # Sort by date to get earliest release
            dated_releases = [r for r in releases if r.get('date')]
            if dated_releases:
                earliest = min(dated_releases, key=lambda x: x.get('date', ''))
                first_release_date = earliest.get('date')
                country = earliest.get('country')
                
                # Get label info
                if 'label-info' in earliest:
                    label_info = earliest['label-info']
                    if label_info and 'label' in label_info[0]:
                        label = label_info[0]['label'].get('name')
        
        # Build enriched data
        enriched_data = {
            'musicbrainz_id': recording_id,
            'matched_artist': matched_artist,
            'matched_title': best_match.get('title'),
            'musicbrainz_tags': tag_data['tags'],
            'musicbrainz_genres': tag_data['genres'],
            'musicbrainz_combined_tags': tag_data['combined_tags'],
            'simplified_mood': mood,
            'first_release_date': first_release_date,
            'country': country,
            'label': label,
            'length': best_match.get('length'),  # in milliseconds
            'disambiguation': best_match.get('disambiguation'),
            'musicbrainz_enriched_at': datetime.now().isoformat(),
            'musicbrainz_url': f"https://musicbrainz.org/recording/{recording_id}"
        }
        
        self.logger.info(f"Successfully enriched '{artist}' - '{title}' with MusicBrainz data")
        return enriched_data
    
    def enrich_tracks_batch(self, tracks: List[Dict[str, str]], max_tracks: int = None) -> Dict[str, Dict]:
        """
        Enrich multiple tracks with MusicBrainz data
        
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
    
    enricher = MusicBrainzEnricher()
    
    # Test with a few tracks
    test_tracks = [
        {"artist": "The Beatles", "title": "Hey Jude"},
        {"artist": "Queen", "title": "Bohemian Rhapsody"},
        {"artist": "Interpol", "title": "Evil"}
    ]
    
    print("Testing MusicBrainz enricher...")
    for track in test_tracks:
        result = enricher.enrich_track(track["artist"], track["title"])
        if result:
            print(f"\n✅ Found: {track['artist']} - {track['title']}")
            print(f"   Tags: {result.get('musicbrainz_tags', [])}")
            print(f"   Genres: {result.get('musicbrainz_genres', [])}")
            print(f"   Mood: {result.get('simplified_mood')}")
            print(f"   Release Date: {result.get('first_release_date')}")
        else:
            print(f"\n❌ Not found: {track['artist']} - {track['title']}") 