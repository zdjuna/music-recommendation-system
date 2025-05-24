"""
Last.fm Data Fetcher

Comprehensive module for fetching all scrobble data from Last.fm with:
- Robust error handling and retry logic
- Rate limiting to respect API limits
- Progress tracking for large datasets
- Data validation and cleaning
- Incremental updates support
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

import requests
import pandas as pd
from ratelimit import limits, sleep_and_retry
from retry import retry
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LastFMFetcher:
    """
    Last.fm data fetcher with comprehensive error handling and rate limiting.
    
    Designed for busy professionals who want reliability over complexity.
    """
    
    # Last.fm API rate limits: 5 requests per second
    RATE_LIMIT_CALLS = 5
    RATE_LIMIT_PERIOD = 1
    
    def __init__(self, api_key: str, username: str, data_dir: str = "data"):
        """
        Initialize the Last.fm fetcher.
        
        Args:
            api_key: Your Last.fm API key
            username: Your Last.fm username
            data_dir: Directory to store fetched data
        """
        self.api_key = api_key
        self.username = username
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.base_url = "https://ws.audioscrobbler.com/2.0/"
        self.session = requests.Session()
        self.console = Console()
        
        # Track statistics
        self.stats = {
            'total_scrobbles': 0,
            'unique_tracks': 0,
            'unique_artists': 0,
            'date_range': {'from': None, 'to': None},
            'last_updated': None
        }
    
    @sleep_and_retry
    @limits(calls=RATE_LIMIT_CALLS, period=RATE_LIMIT_PERIOD)
    def _make_request(self, method: str, params: Dict) -> Dict:
        """
        Make a rate-limited request to the Last.fm API.
        
        Args:
            method: Last.fm API method
            params: Additional parameters
            
        Returns:
            JSON response data
        """
        request_params = {
            'method': method,
            'user': self.username,
            'api_key': self.api_key,
            'format': 'json',
            **params
        }
        
        try:
            response = self.session.get(self.base_url, params=request_params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Check for Last.fm API errors
            if 'error' in data:
                error_msg = data.get('message', 'Unknown Last.fm API error')
                raise Exception(f"Last.fm API Error {data['error']}: {error_msg}")
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            raise
    
    @retry(tries=3, delay=2, backoff=2)
    def get_user_info(self) -> Dict:
        """
        Get user information including total scrobble count.
        
        Returns:
            User information dictionary
        """
        try:
            data = self._make_request('user.getinfo', {})
            user_info = data['user']
            
            self.stats['total_scrobbles'] = int(user_info['playcount'])
            
            return {
                'username': user_info['name'],
                'real_name': user_info.get('realname', ''),
                'total_scrobbles': int(user_info['playcount']),
                'registered': user_info.get('registered', {}).get('#text', ''),
                'country': user_info.get('country', ''),
                'last_updated': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            raise
    
    def _get_recent_tracks_page(self, page: int = 1, limit: int = 200, 
                               from_timestamp: Optional[int] = None, 
                               to_timestamp: Optional[int] = None) -> Dict:
        """
        Get a single page of recent tracks.
        
        Args:
            page: Page number (1-based)
            limit: Number of tracks per page (max 200)
            from_timestamp: Unix timestamp for start date
            to_timestamp: Unix timestamp for end date
            
        Returns:
            Recent tracks data
        """
        params = {
            'page': page,
            'limit': min(limit, 200)  # Last.fm max is 200
        }
        
        if from_timestamp:
            params['from'] = from_timestamp
        if to_timestamp:
            params['to'] = to_timestamp
        
        return self._make_request('user.getrecenttracks', params)
    
    def fetch_all_scrobbles(self, incremental: bool = True, 
                           start_date: Optional[str] = None,
                           end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Fetch all scrobbles with progress tracking and incremental updates.
        
        Args:
            incremental: Whether to only fetch new scrobbles since last update
            start_date: Start date in YYYY-MM-DD format (optional)
            end_date: End date in YYYY-MM-DD format (optional)
            
        Returns:
            DataFrame with all scrobbles
        """
        self.console.print("[bold blue]🎵 Starting Last.fm data fetch...[/]")
        
        # Load existing data if available and incremental update requested
        existing_data = None
        if incremental:
            existing_data = self._load_existing_data()
        
        # Get user info first
        try:
            user_info = self.get_user_info()
            self.console.print(f"[green]User: {user_info['username']} "
                             f"({user_info['total_scrobbles']:,} total scrobbles)[/]")
        except Exception as e:
            self.console.print(f"[red]Error getting user info: {e}[/]")
            return pd.DataFrame()
        
        # Calculate date range
        from_timestamp = None
        to_timestamp = None
        
        if start_date:
            from_timestamp = int(datetime.strptime(start_date, '%Y-%m-%d').timestamp())
        elif incremental and existing_data is not None and not existing_data.empty:
            # Get timestamp of latest scrobble + 1 second
            latest_timestamp = existing_data['timestamp'].max()
            from_timestamp = int(latest_timestamp + 1)
            self.console.print(f"[yellow]Incremental update from {datetime.fromtimestamp(from_timestamp)}[/]")
        
        if end_date:
            to_timestamp = int(datetime.strptime(end_date, '%Y-%m-%d').timestamp())
        
        # Get first page to determine total pages
        try:
            first_page = self._get_recent_tracks_page(1, 200, from_timestamp, to_timestamp)
            total_pages = int(first_page['recenttracks']['@attr']['totalPages'])
            total_tracks = int(first_page['recenttracks']['@attr']['total'])
            
            if total_tracks == 0:
                self.console.print("[yellow]No new tracks to fetch.[/]")
                return existing_data if existing_data is not None else pd.DataFrame()
            
            self.console.print(f"[cyan]Found {total_tracks:,} tracks across {total_pages:,} pages[/]")
            
        except Exception as e:
            self.console.print(f"[red]Error getting track count: {e}[/]")
            return pd.DataFrame()
        
        # Fetch all pages with progress tracking
        all_tracks = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console
        ) as progress:
            
            task = progress.add_task(
                f"Fetching {total_tracks:,} scrobbles...", 
                total=total_pages
            )
            
            for page in range(1, total_pages + 1):
                try:
                    page_data = self._get_recent_tracks_page(page, 200, from_timestamp, to_timestamp)
                    tracks = page_data['recenttracks']['track']
                    
                    # Handle single track vs list of tracks
                    if not isinstance(tracks, list):
                        tracks = [tracks]
                    
                    # Process tracks on this page
                    for track in tracks:
                        processed_track = self._process_track(track)
                        if processed_track:
                            all_tracks.append(processed_track)
                    
                    progress.update(task, advance=1)
                    
                    # Small delay to be respectful to Last.fm
                    if page % 10 == 0:
                        time.sleep(0.1)
                        
                except Exception as e:
                    logger.error(f"Error fetching page {page}: {e}")
                    # Continue with next page instead of failing completely
                    progress.update(task, advance=1)
                    continue
        
        # Convert to DataFrame
        if not all_tracks:
            self.console.print("[yellow]No tracks found in the specified range.[/]")
            return existing_data if existing_data is not None else pd.DataFrame()
        
        new_df = pd.DataFrame(all_tracks)
        
        # Combine with existing data if incremental
        if incremental and existing_data is not None and not existing_data.empty:
            combined_df = pd.concat([existing_data, new_df], ignore_index=True)
            combined_df = combined_df.drop_duplicates(subset=['timestamp'], keep='last')
            combined_df = combined_df.sort_values('timestamp').reset_index(drop=True)
            final_df = combined_df
        else:
            final_df = new_df.sort_values('timestamp').reset_index(drop=True)
        
        # Update statistics
        self._update_stats(final_df)
        
        # Save data
        self._save_data(final_df)
        
        self.console.print(f"[bold green]✅ Successfully fetched {len(new_df):,} new tracks![/]")
        self.console.print(f"[green]Total dataset now contains {len(final_df):,} scrobbles[/]")
        
        return final_df
    
    def _process_track(self, track: Dict) -> Optional[Dict]:
        """
        Process a single track from the API response.
        
        Args:
            track: Raw track data from Last.fm API
            
        Returns:
            Processed track dictionary or None if invalid
        """
        try:
            # Skip currently playing tracks (they don't have a timestamp)
            if '@attr' in track and track['@attr'].get('nowplaying') == 'true':
                return None
            
            # Extract timestamp
            if 'date' not in track:
                return None
            
            timestamp = int(track['date']['uts'])
            
            # Extract track information
            processed = {
                'timestamp': timestamp,
                'date': datetime.fromtimestamp(timestamp).isoformat(),
                'artist': track['artist'].get('#text', '') if isinstance(track['artist'], dict) else str(track['artist']),
                'track': track['name'],
                'album': track['album'].get('#text', '') if isinstance(track['album'], dict) else str(track['album']),
                'mbid_track': track.get('mbid', ''),
                'mbid_artist': track['artist'].get('mbid', '') if isinstance(track['artist'], dict) else '',
                'mbid_album': track['album'].get('mbid', '') if isinstance(track['album'], dict) else '',
                'url_track': track.get('url', ''),
                'image_url': ''
            }
            
            # Extract image URL (usually the largest available)
            if 'image' in track and isinstance(track['image'], list):
                for image in reversed(track['image']):  # Start from largest
                    if image.get('#text'):
                        processed['image_url'] = image['#text']
                        break
            
            return processed
            
        except Exception as e:
            logger.warning(f"Error processing track: {e}")
            return None
    
    def _load_existing_data(self) -> Optional[pd.DataFrame]:
        """Load existing scrobble data if available."""
        data_file = self.data_dir / f"{self.username}_scrobbles.csv"
        
        if data_file.exists():
            try:
                df = pd.read_csv(data_file)
                self.console.print(f"[cyan]Loaded {len(df):,} existing scrobbles[/]")
                return df
            except Exception as e:
                logger.warning(f"Error loading existing data: {e}")
        
        return None
    
    def _save_data(self, df: pd.DataFrame):
        """Save scrobble data to CSV and stats to JSON."""
        # Save main data
        data_file = self.data_dir / f"{self.username}_scrobbles.csv"
        df.to_csv(data_file, index=False)
        
        # Save statistics
        stats_file = self.data_dir / f"{self.username}_stats.json"
        with open(stats_file, 'w') as f:
            json.dump(self.stats, f, indent=2)
        
        self.console.print(f"[green]Data saved to {data_file}[/]")
    
    def _update_stats(self, df: pd.DataFrame):
        """Update statistics based on the current dataset."""
        if df.empty:
            return
        
        self.stats.update({
            'total_scrobbles': len(df),
            'unique_tracks': df['track'].nunique(),
            'unique_artists': df['artist'].nunique(),
            'unique_albums': df['album'].nunique(),
            'date_range': {
                'from': df['date'].min(),
                'to': df['date'].max()
            },
            'last_updated': datetime.now(timezone.utc).isoformat()
        })
    
    def get_summary_stats(self) -> Dict:
        """Get summary statistics of the fetched data."""
        return self.stats.copy()
    
    def export_to_formats(self, df: pd.DataFrame, formats: List[str] = ['csv', 'json']):
        """
        Export data to various formats.
        
        Args:
            df: DataFrame to export
            formats: List of formats ('csv', 'json', 'parquet')
        """
        base_filename = f"{self.username}_scrobbles"
        
        for fmt in formats:
            try:
                if fmt == 'csv':
                    filepath = self.data_dir / f"{base_filename}.csv"
                    df.to_csv(filepath, index=False)
                elif fmt == 'json':
                    filepath = self.data_dir / f"{base_filename}.json"
                    df.to_json(filepath, orient='records', date_format='iso')
                elif fmt == 'parquet':
                    filepath = self.data_dir / f"{base_filename}.parquet"
                    df.to_parquet(filepath, index=False)
                
                self.console.print(f"[green]Exported to {filepath}[/]")
                
            except Exception as e:
                logger.error(f"Error exporting to {fmt}: {e}") 