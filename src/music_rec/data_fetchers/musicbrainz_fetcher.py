"""
MusicBrainz metadata fetcher for enriching music data.

This module fetches detailed metadata from MusicBrainz including:
- Genre information from tags
- Artist relationships and collaborations
- Recording details and acoustic properties
- Release information and label data
- Work relationships (covers, samples, etc.)
"""

import logging
import time
import json
import requests
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import musicbrainzngs as mb
from urllib.parse import quote
import pandas as pd

logger = logging.getLogger(__name__)

class MusicBrainzFetcher:
    """
    Fetches detailed metadata from MusicBrainz API to enrich music data.
    
    Features:
    - Genre/tag enrichment from folksonomy tags
    - Artist relationship mapping
    - Recording and release metadata
    - Work relationship analysis
    - Rate limiting and error handling
    - Batch processing capabilities
    """
    
    def __init__(self, app_name: str = "MusicRecSystem", app_version: str = "1.0", 
                 contact_email: str = "user@example.com"):
        """
        Initialize MusicBrainz fetcher.
        
        Args:
            app_name: Application name for API identification
            app_version: Application version
            contact_email: Contact email for API identification
        """
        self.app_name = app_name
        self.app_version = app_version
        self.contact_email = contact_email
        
        # Configure musicbrainzngs
        mb.set_useragent(app_name, app_version, contact_email)
        
        # Rate limiting: MusicBrainz allows 1 request per second
        self.rate_limit_delay = 1.0
        self.last_request_time = 0
        
        # Cache for avoiding duplicate requests
        self.cache = {
            'artists': {},
            'recordings': {},
            'releases': {},
            'works': {}
        }
        
        # Statistics
        self.stats = {
            'artists_enriched': 0,
            'recordings_enriched': 0,
            'releases_enriched': 0,
            'cache_hits': 0,
            'api_calls': 0,
            'errors': 0
        }
    
    def _rate_limit(self):
        """Enforce rate limiting for MusicBrainz API."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _safe_request(self, request_func, *args, **kwargs) -> Optional[Dict]:
        """
        Safely execute MusicBrainz request with error handling.
        
        Args:
            request_func: MusicBrainz API function to call
            *args, **kwargs: Arguments for the API function
            
        Returns:
            API response data or None if error
        """
        self._rate_limit()
        
        try:
            self.stats['api_calls'] += 1
            result = request_func(*args, **kwargs)
            return result
        except mb.ResponseError as e:
            if e.cause.code == 404:
                logger.debug(f"MusicBrainz: Resource not found - {e}")
            else:
                logger.warning(f"MusicBrainz API error: {e}")
            self.stats['errors'] += 1
            return None
        except Exception as e:
            logger.error(f"Unexpected error in MusicBrainz request: {e}")
            self.stats['errors'] += 1
            return None
    
    def search_artist(self, artist_name: str, limit: int = 5) -> List[Dict]:
        """
        Search for artists by name.
        
        Args:
            artist_name: Name of the artist to search
            limit: Maximum number of results
            
        Returns:
            List of artist search results
        """
        if not artist_name or not artist_name.strip():
            return []
        
        try:
            result = self._safe_request(
                mb.search_artists,
                query=f'artist:"{artist_name}"',
                limit=limit
            )
            
            if result and 'artist-list' in result:
                return result['artist-list']
                
        except Exception as e:
            logger.error(f"Error searching for artist '{artist_name}': {e}")
        
        return []
    
    def search_recording(self, artist_name: str, track_name: str, limit: int = 5) -> List[Dict]:
        """
        Search for recordings by artist and track name.
        
        Args:
            artist_name: Name of the artist
            track_name: Name of the track
            limit: Maximum number of results
            
        Returns:
            List of recording search results
        """
        if not artist_name or not track_name:
            return []
        
        # Build search query
        query_parts = []
        if artist_name:
            query_parts.append(f'artist:"{artist_name}"')
        if track_name:
            query_parts.append(f'recording:"{track_name}"')
        
        query = ' AND '.join(query_parts)
        
        try:
            result = self._safe_request(
                mb.search_recordings,
                query=query,
                limit=limit
            )
            
            if result and 'recording-list' in result:
                return result['recording-list']
                
        except Exception as e:
            logger.error(f"Error searching for recording '{artist_name} - {track_name}': {e}")
        
        return []
    
    def get_artist_details(self, artist_id: str) -> Optional[Dict]:
        """
        Get detailed artist information including tags and relationships.
        
        Args:
            artist_id: MusicBrainz artist ID
            
        Returns:
            Detailed artist information
        """
        if artist_id in self.cache['artists']:
            self.stats['cache_hits'] += 1
            return self.cache['artists'][artist_id]
        
        try:
            result = self._safe_request(
                mb.get_artist_by_id,
                artist_id,
                includes=['tags', 'artist-rels', 'url-rels']
            )
            
            if result and 'artist' in result:
                artist_data = result['artist']
                
                # Process and enrich the data
                enriched_data = {
                    'id': artist_id,
                    'name': artist_data.get('name', ''),
                    'sort_name': artist_data.get('sort-name', ''),
                    'type': artist_data.get('type', ''),
                    'country': artist_data.get('country', ''),
                    'life_span': artist_data.get('life-span', {}),
                    'tags': self._process_tags(artist_data.get('tag-list', [])),
                    'genres': self._process_genres(artist_data.get('genre-list', [])),
                    'relationships': self._process_artist_relationships(artist_data.get('artist-relation-list', [])),
                    'urls': self._process_url_relationships(artist_data.get('url-relation-list', [])),
                    'disambiguation': artist_data.get('disambiguation', ''),
                    'fetched_at': datetime.now().isoformat()
                }
                
                self.cache['artists'][artist_id] = enriched_data
                self.stats['artists_enriched'] += 1
                return enriched_data
                
        except Exception as e:
            logger.error(f"Error getting artist details for ID '{artist_id}': {e}")
        
        return None
    
    def get_recording_details(self, recording_id: str) -> Optional[Dict]:
        """
        Get detailed recording information including tags and relationships.
        
        Args:
            recording_id: MusicBrainz recording ID
            
        Returns:
            Detailed recording information
        """
        if recording_id in self.cache['recordings']:
            self.stats['cache_hits'] += 1
            return self.cache['recordings'][recording_id]
        
        try:
            result = self._safe_request(
                mb.get_recording_by_id,
                recording_id,
                includes=['tags', 'artist-credits', 'releases', 'work-rels']
            )
            
            if result and 'recording' in result:
                recording_data = result['recording']
                
                enriched_data = {
                    'id': recording_id,
                    'title': recording_data.get('title', ''),
                    'length': recording_data.get('length'),
                    'disambiguation': recording_data.get('disambiguation', ''),
                    'tags': self._process_tags(recording_data.get('tag-list', [])),
                    'genres': self._process_genres(recording_data.get('genre-list', [])),
                    'artist_credits': self._process_artist_credits(recording_data.get('artist-credit', [])),
                    'releases': self._process_releases(recording_data.get('release-list', [])),
                    'works': self._process_work_relationships(recording_data.get('work-relation-list', [])),
                    'fetched_at': datetime.now().isoformat()
                }
                
                self.cache['recordings'][recording_id] = enriched_data
                self.stats['recordings_enriched'] += 1
                return enriched_data
                
        except Exception as e:
            logger.error(f"Error getting recording details for ID '{recording_id}': {e}")
        
        return None
    
    def _process_tags(self, tag_list: List[Dict]) -> List[Dict]:
        """Process MusicBrainz tags into structured format."""
        tags = []
        for tag in tag_list:
            if 'name' in tag:
                tag_data = {
                    'name': tag['name'],
                    'count': tag.get('count', 0)
                }
                tags.append(tag_data)
        
        # Sort by count (popularity)
        return sorted(tags, key=lambda x: x['count'], reverse=True)
    
    def _process_genres(self, genre_list: List[Dict]) -> List[Dict]:
        """Process MusicBrainz genres into structured format."""
        genres = []
        for genre in genre_list:
            if 'name' in genre:
                genre_data = {
                    'name': genre['name'],
                    'count': genre.get('count', 0)
                }
                genres.append(genre_data)
        
        return sorted(genres, key=lambda x: x['count'], reverse=True)
    
    def _process_artist_relationships(self, rel_list: List[Dict]) -> List[Dict]:
        """Process artist relationships (collaborations, member of, etc.)."""
        relationships = []
        for rel in rel_list:
            if 'type' in rel and 'artist' in rel:
                rel_data = {
                    'type': rel['type'],
                    'direction': rel.get('direction', 'forward'),
                    'artist_id': rel['artist']['id'],
                    'artist_name': rel['artist']['name'],
                    'begin': rel.get('begin'),
                    'end': rel.get('end'),
                    'ended': rel.get('ended', False)
                }
                relationships.append(rel_data)
        
        return relationships
    
    def _process_url_relationships(self, url_list: List[Dict]) -> List[Dict]:
        """Process URL relationships (official site, social media, etc.)."""
        urls = []
        for url_rel in url_list:
            if 'type' in url_rel and 'url' in url_rel:
                url_data = {
                    'type': url_rel['type'],
                    'url': url_rel['url']['resource']
                }
                urls.append(url_data)
        
        return urls
    
    def _process_artist_credits(self, credit_list: List[Dict]) -> List[Dict]:
        """Process artist credits for recordings."""
        credits = []
        for credit in credit_list:
            if 'artist' in credit:
                credit_data = {
                    'artist_id': credit['artist']['id'],
                    'artist_name': credit['artist']['name'],
                    'name': credit.get('name', credit['artist']['name']),
                    'joinphrase': credit.get('joinphrase', '')
                }
                credits.append(credit_data)
        
        return credits
    
    def _process_releases(self, release_list: List[Dict]) -> List[Dict]:
        """Process release information for recordings."""
        releases = []
        for release in release_list:
            release_data = {
                'id': release['id'],
                'title': release['title'],
                'status': release.get('status'),
                'date': release.get('date'),
                'country': release.get('country'),
                'barcode': release.get('barcode')
            }
            releases.append(release_data)
        
        return releases
    
    def _process_work_relationships(self, work_list: List[Dict]) -> List[Dict]:
        """Process work relationships (covers, samples, etc.)."""
        works = []
        for work_rel in work_list:
            if 'type' in work_rel and 'work' in work_rel:
                work_data = {
                    'type': work_rel['type'],
                    'work_id': work_rel['work']['id'],
                    'work_title': work_rel['work']['title'],
                    'direction': work_rel.get('direction', 'forward')
                }
                works.append(work_data)
        
        return works
    
    def enrich_scrobble_data(self, scrobble_df: pd.DataFrame, batch_size: int = 100) -> pd.DataFrame:
        """
        Enrich scrobble data with MusicBrainz metadata.
        
        Args:
            scrobble_df: DataFrame with scrobble data
            batch_size: Number of records to process in each batch
            
        Returns:
            Enriched DataFrame with MusicBrainz metadata
        """
        logger.info(f"Starting MusicBrainz enrichment for {len(scrobble_df)} scrobbles")
        
        # Initialize new columns for enriched data
        enriched_df = scrobble_df.copy()
        
        # Add MusicBrainz enrichment columns
        mb_columns = [
            'mb_artist_id', 'mb_recording_id', 'mb_genres', 'mb_tags',
            'mb_artist_type', 'mb_artist_country', 'mb_recording_length',
            'mb_artist_relationships', 'mb_enriched_at'
        ]
        
        for col in mb_columns:
            enriched_df[col] = None
        
        # Process in batches
        total_batches = (len(enriched_df) + batch_size - 1) // batch_size
        
        for batch_idx in range(total_batches):
            start_idx = batch_idx * batch_size
            end_idx = min((batch_idx + 1) * batch_size, len(enriched_df))
            
            logger.info(f"Processing batch {batch_idx + 1}/{total_batches} "
                       f"(rows {start_idx + 1}-{end_idx})")
            
            for idx in range(start_idx, end_idx):
                row = enriched_df.iloc[idx]
                artist_name = row.get('artist', '')
                track_name = row.get('track', '')
                
                if not artist_name or not track_name:
                    continue
                
                # Try to enrich this scrobble
                enrichment = self._enrich_single_scrobble(artist_name, track_name)
                
                if enrichment:
                    for col, value in enrichment.items():
                        enriched_df.at[idx, col] = value
                
                # Progress logging
                if (idx - start_idx + 1) % 10 == 0:
                    progress = ((idx - start_idx + 1) / (end_idx - start_idx)) * 100
                    logger.info(f"Batch progress: {progress:.1f}%")
        
        logger.info("MusicBrainz enrichment completed")
        logger.info(f"Enrichment statistics: {self.stats}")
        
        return enriched_df
    
    def _enrich_single_scrobble(self, artist_name: str, track_name: str) -> Optional[Dict]:
        """
        Enrich a single scrobble with MusicBrainz data.
        
        Args:
            artist_name: Name of the artist
            track_name: Name of the track
            
        Returns:
            Dictionary with enrichment data or None
        """
        enrichment = {}
        
        try:
            # Search for the recording
            recordings = self.search_recording(artist_name, track_name, limit=3)
            
            best_recording = None
            best_artist = None
            
            # Find the best matching recording
            for recording in recordings:
                if 'artist-credit' in recording:
                    for credit in recording['artist-credit']:
                        if 'artist' in credit:
                            credit_artist = credit['artist']['name'].lower()
                            if artist_name.lower() in credit_artist or credit_artist in artist_name.lower():
                                best_recording = recording
                                best_artist = credit['artist']
                                break
                    if best_recording:
                        break
            
            if best_recording and best_artist:
                # Get detailed information
                artist_details = self.get_artist_details(best_artist['id'])
                recording_details = self.get_recording_details(best_recording['id'])
                
                # Compile enrichment data
                enrichment = {
                    'mb_artist_id': best_artist['id'],
                    'mb_recording_id': best_recording['id'],
                    'mb_enriched_at': datetime.now().isoformat()
                }
                
                if artist_details:
                    enrichment.update({
                        'mb_genres': json.dumps([g['name'] for g in artist_details.get('genres', [])[:5]]),
                        'mb_tags': json.dumps([t['name'] for t in artist_details.get('tags', [])[:10]]),
                        'mb_artist_type': artist_details.get('type', ''),
                        'mb_artist_country': artist_details.get('country', ''),
                        'mb_artist_relationships': json.dumps([
                            {'type': r['type'], 'artist': r['artist_name']} 
                            for r in artist_details.get('relationships', [])[:5]
                        ])
                    })
                
                if recording_details:
                    enrichment['mb_recording_length'] = recording_details.get('length')
        
        except Exception as e:
            logger.error(f"Error enriching scrobble '{artist_name} - {track_name}': {e}")
        
        return enrichment if enrichment else None
    
    def get_stats(self) -> Dict:
        """Get enrichment statistics."""
        return self.stats.copy()
    
    def clear_cache(self):
        """Clear the internal cache."""
        self.cache = {
            'artists': {},
            'recordings': {},
            'releases': {},
            'works': {}
        }
        logger.info("MusicBrainz cache cleared") 