"""
Multi-Platform Playlist Exporter

Export music recommendations to various streaming platforms and formats.
Supports Spotify, Apple Music, YouTube Music, M3U, and custom formats.
"""

import json
import asyncio
import logging
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
from urllib.parse import quote
import base64

logger = logging.getLogger(__name__)

class MultiPlatformExporter:
    """
    Export playlists to multiple music streaming platforms and formats.
    """
    
    SUPPORTED_PLATFORMS = [
        'spotify', 'apple_music', 'youtube_music', 
        'deezer', 'm3u', 'json', 'csv', 'roon'
    ]
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize exporter with platform credentials.
        
        Args:
            config: Configuration dict with API keys and settings
        """
        self.config = config
        self.clients = {}
        self.export_history = []
        
        # Initialize platform clients
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize clients for each platform."""
        # Spotify
        if self.config.get('spotify_client_id') and self.config.get('spotify_client_secret'):
            self.clients['spotify'] = SpotifyExporter(
                client_id=self.config['spotify_client_id'],
                client_secret=self.config['spotify_client_secret'],
                redirect_uri=self.config.get('spotify_redirect_uri', 'http://localhost:8080/callback')
            )
        
        # YouTube Music (requires ytmusicapi)
        if self.config.get('youtube_music_headers'):
            try:
                from ytmusicapi import YTMusic
                self.clients['youtube_music'] = YouTubeMusicExporter(
                    headers_auth=self.config['youtube_music_headers']
                )
            except ImportError:
                logger.warning("ytmusicapi not installed - YouTube Music export unavailable")
        
        # Always available exporters
        self.clients['m3u'] = M3UExporter()
        self.clients['json'] = JSONExporter()
        self.clients['csv'] = CSVExporter()
        self.clients['roon'] = RoonExporter()
    
    async def export_playlist(self, tracks: List[Dict], platform: str, 
                            playlist_name: str, **kwargs) -> Dict[str, Any]:
        """
        Export playlist to specified platform.
        
        Args:
            tracks: List of track dictionaries
            platform: Target platform
            playlist_name: Name for the playlist
            **kwargs: Platform-specific options
            
        Returns:
            Export result dictionary
        """
        if platform not in self.SUPPORTED_PLATFORMS:
            raise ValueError(f"Unsupported platform: {platform}")
        
        if platform not in self.clients:
            return {
                'success': False,
                'error': f"Client not configured for {platform}",
                'platform': platform
            }
        
        exporter = self.clients[platform]
        
        try:
            logger.info(f"Exporting {len(tracks)} tracks to {platform}")
            
            result = await exporter.export(tracks, playlist_name, **kwargs)
            
            # Track export history
            export_record = {
                'timestamp': datetime.now().isoformat(),
                'platform': platform,
                'playlist_name': playlist_name,
                'track_count': len(tracks),
                'success': result.get('success', False),
                'result': result
            }
            self.export_history.append(export_record)
            
            return result
            
        except Exception as e:
            logger.error(f"Error exporting to {platform}: {e}")
            return {
                'success': False,
                'error': str(e),
                'platform': platform
            }
    
    async def export_to_multiple_platforms(self, tracks: List[Dict], 
                                         playlist_name: str,
                                         platforms: List[str]) -> Dict[str, Any]:
        """
        Export playlist to multiple platforms simultaneously.
        
        Args:
            tracks: List of track dictionaries
            playlist_name: Name for the playlist
            platforms: List of platform names
            
        Returns:
            Dictionary with results for each platform
        """
        results = {}
        
        # Create export tasks
        tasks = []
        for platform in platforms:
            if platform in self.clients:
                task = self.export_playlist(tracks, platform, playlist_name)
                tasks.append((platform, task))
        
        # Execute exports concurrently
        for platform, task in tasks:
            try:
                result = await task
                results[platform] = result
            except Exception as e:
                results[platform] = {
                    'success': False,
                    'error': str(e),
                    'platform': platform
                }
        
        return results
    
    def get_available_platforms(self) -> List[str]:
        """Get list of available platforms."""
        return list(self.clients.keys())
    
    def get_export_history(self) -> List[Dict]:
        """Get export history."""
        return self.export_history.copy()


class SpotifyExporter:
    """Spotify playlist exporter."""
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.access_token = None
        self.refresh_token = None
    
    async def export(self, tracks: List[Dict], playlist_name: str, 
                    description: str = "", public: bool = False) -> Dict[str, Any]:
        """Export playlist to Spotify."""
        try:
            # Ensure we have access token
            if not await self._ensure_auth():
                return {
                    'success': False,
                    'error': 'Authentication failed',
                    'platform': 'spotify'
                }
            
            # Create playlist
            playlist_result = await self._create_playlist(playlist_name, description, public)
            if not playlist_result['success']:
                return playlist_result
            
            playlist_id = playlist_result['playlist_id']
            
            # Find tracks on Spotify
            spotify_tracks = []
            not_found = []
            
            for track in tracks:
                spotify_id = await self._search_track(track)
                if spotify_id:
                    spotify_tracks.append(spotify_id)
                else:
                    not_found.append(f"{track.get('artist', 'Unknown')} - {track.get('track', 'Unknown')}")
            
            # Add tracks to playlist
            if spotify_tracks:
                add_result = await self._add_tracks_to_playlist(playlist_id, spotify_tracks)
                if not add_result['success']:
                    return add_result
            
            return {
                'success': True,
                'platform': 'spotify',
                'playlist_id': playlist_id,
                'playlist_url': f"https://open.spotify.com/playlist/{playlist_id}",
                'tracks_added': len(spotify_tracks),
                'tracks_not_found': len(not_found),
                'not_found_tracks': not_found[:10]  # Limit to first 10
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'platform': 'spotify'
            }
    
    async def _ensure_auth(self) -> bool:
        """Ensure we have valid authentication."""
        # This would typically involve OAuth flow
        # For simplicity, assuming token is provided in config
        return self.access_token is not None
    
    async def _create_playlist(self, name: str, description: str, 
                             public: bool) -> Dict[str, Any]:
        """Create playlist on Spotify."""
        # Implementation would use Spotify Web API
        # Placeholder for actual implementation
        return {
            'success': True,
            'playlist_id': 'dummy_playlist_id'
        }
    
    async def _search_track(self, track: Dict) -> Optional[str]:
        """Search for track on Spotify and return track ID."""
        # Implementation would use Spotify search API
        # Placeholder for actual implementation
        return None
    
    async def _add_tracks_to_playlist(self, playlist_id: str, 
                                    track_ids: List[str]) -> Dict[str, Any]:
        """Add tracks to Spotify playlist."""
        # Implementation would use Spotify Web API
        # Placeholder for actual implementation
        return {'success': True}


class YouTubeMusicExporter:
    """YouTube Music playlist exporter."""
    
    def __init__(self, headers_auth: str):
        try:
            from ytmusicapi import YTMusic
            self.ytmusic = YTMusic(headers_auth)
        except ImportError:
            raise ImportError("ytmusicapi package required for YouTube Music export")
    
    async def export(self, tracks: List[Dict], playlist_name: str, 
                    description: str = "") -> Dict[str, Any]:
        """Export playlist to YouTube Music."""
        try:
            # Create playlist
            playlist_id = self.ytmusic.create_playlist(
                title=playlist_name,
                description=description
            )
            
            # Find and add tracks
            added_tracks = []
            not_found = []
            
            for track in tracks:
                search_query = f"{track.get('artist', '')} {track.get('track', '')}"
                search_results = self.ytmusic.search(search_query, filter="songs", limit=1)
                
                if search_results:
                    video_id = search_results[0]['videoId']
                    self.ytmusic.add_playlist_items(playlist_id, [video_id])
                    added_tracks.append(video_id)
                else:
                    not_found.append(f"{track.get('artist', 'Unknown')} - {track.get('track', 'Unknown')}")
            
            return {
                'success': True,
                'platform': 'youtube_music',
                'playlist_id': playlist_id,
                'tracks_added': len(added_tracks),
                'tracks_not_found': len(not_found),
                'not_found_tracks': not_found[:10]
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'platform': 'youtube_music'
            }


class M3UExporter:
    """M3U playlist file exporter."""
    
    async def export(self, tracks: List[Dict], playlist_name: str, 
                    output_dir: str = "playlists") -> Dict[str, Any]:
        """Export playlist to M3U format."""
        try:
            output_path = Path(output_dir)
            output_path.mkdir(exist_ok=True)
            
            filename = f"{playlist_name.replace(' ', '_')}.m3u"
            filepath = output_path / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("#EXTM3U\n")
                f.write(f"# Playlist: {playlist_name}\n")
                f.write(f"# Generated: {datetime.now().isoformat()}\n")
                f.write(f"# Tracks: {len(tracks)}\n\n")
                
                for track in tracks:
                    artist = track.get('artist', 'Unknown Artist')
                    title = track.get('track', 'Unknown Track')
                    duration = track.get('duration', 0)
                    
                    f.write(f"#EXTINF:{duration},{artist} - {title}\n")
                    
                    # Add file path or URL if available
                    file_path = track.get('file_path', f"{artist} - {title}.mp3")
                    f.write(f"{file_path}\n")
            
            return {
                'success': True,
                'platform': 'm3u',
                'file_path': str(filepath),
                'tracks_exported': len(tracks)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'platform': 'm3u'
            }


class JSONExporter:
    """JSON playlist exporter."""
    
    async def export(self, tracks: List[Dict], playlist_name: str, 
                    output_dir: str = "playlists") -> Dict[str, Any]:
        """Export playlist to JSON format."""
        try:
            output_path = Path(output_dir)
            output_path.mkdir(exist_ok=True)
            
            filename = f"{playlist_name.replace(' ', '_')}.json"
            filepath = output_path / filename
            
            playlist_data = {
                'name': playlist_name,
                'created': datetime.now().isoformat(),
                'track_count': len(tracks),
                'tracks': tracks
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(playlist_data, f, indent=2, ensure_ascii=False)
            
            return {
                'success': True,
                'platform': 'json',
                'file_path': str(filepath),
                'tracks_exported': len(tracks)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'platform': 'json'
            }


class CSVExporter:
    """CSV playlist exporter."""
    
    async def export(self, tracks: List[Dict], playlist_name: str, 
                    output_dir: str = "playlists") -> Dict[str, Any]:
        """Export playlist to CSV format."""
        try:
            output_path = Path(output_dir)
            output_path.mkdir(exist_ok=True)
            
            filename = f"{playlist_name.replace(' ', '_')}.csv"
            filepath = output_path / filename
            
            # Convert to DataFrame and save
            df = pd.DataFrame(tracks)
            df.to_csv(filepath, index=False, encoding='utf-8')
            
            return {
                'success': True,
                'platform': 'csv',
                'file_path': str(filepath),
                'tracks_exported': len(tracks)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'platform': 'csv'
            }


class RoonExporter:
    """Roon playlist exporter (integrates with existing Roon system)."""
    
    async def export(self, tracks: List[Dict], playlist_name: str, 
                    zone_id: Optional[str] = None) -> Dict[str, Any]:
        """Export playlist to Roon."""
        try:
            # This would integrate with the existing Roon integration
            # For now, export to a format that Roon can import
            
            roon_tracks = []
            for track in tracks:
                roon_track = {
                    'title': track.get('track', 'Unknown'),
                    'artist': track.get('artist', 'Unknown'),
                    'album': track.get('album', 'Unknown'),
                    'duration': track.get('duration', 0)
                }
                roon_tracks.append(roon_track)
            
            # Save in Roon-compatible format
            output_path = Path("playlists") / "roon"
            output_path.mkdir(parents=True, exist_ok=True)
            
            filename = f"{playlist_name.replace(' ', '_')}_roon.json"
            filepath = output_path / filename
            
            roon_playlist = {
                'name': playlist_name,
                'tracks': roon_tracks,
                'created': datetime.now().isoformat(),
                'zone_id': zone_id
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(roon_playlist, f, indent=2, ensure_ascii=False)
            
            return {
                'success': True,
                'platform': 'roon',
                'file_path': str(filepath),
                'tracks_exported': len(tracks),
                'note': 'Exported to Roon-compatible format. Use Roon integration to import.'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'platform': 'roon'
            }


# Streamlit integration helper
class StreamlitExportHelper:
    """Helper class for Streamlit playlist export interface."""
    
    @staticmethod
    def show_export_interface(tracks: List[Dict], default_name: str = "My Playlist"):
        """Show export interface in Streamlit."""
        import streamlit as st
        
        st.subheader("🎵 Export Playlist")
        
        # Get exporter configuration
        config = StreamlitExportHelper._get_export_config()
        exporter = MultiPlatformExporter(config)
        
        # Playlist settings
        col1, col2 = st.columns(2)
        
        with col1:
            playlist_name = st.text_input("Playlist Name", value=default_name)
        
        with col2:
            available_platforms = exporter.get_available_platforms()
            selected_platforms = st.multiselect(
                "Export to platforms:",
                available_platforms,
                default=['json', 'csv']
            )
        
        # Platform-specific options
        if 'spotify' in selected_platforms:
            st.subheader("🎵 Spotify Options")
            spotify_public = st.checkbox("Make playlist public", value=False)
            spotify_description = st.text_area("Playlist description", value="")
        
        # Export button
        if st.button("🚀 Export Playlist", type="primary"):
            if not selected_platforms:
                st.error("Please select at least one platform")
                return
            
            with st.spinner(f"Exporting to {len(selected_platforms)} platform(s)..."):
                # Run export
                import asyncio
                
                async def run_export():
                    return await exporter.export_to_multiple_platforms(
                        tracks, playlist_name, selected_platforms
                    )
                
                results = asyncio.run(run_export())
                
                # Show results
                StreamlitExportHelper._show_export_results(results)
    
    @staticmethod
    def _get_export_config() -> Dict[str, Any]:
        """Get export configuration from Streamlit secrets."""
        import streamlit as st
        
        config = {}
        
        # Try to get from secrets
        try:
            config.update({
                'spotify_client_id': st.secrets.get('SPOTIFY_CLIENT_ID'),
                'spotify_client_secret': st.secrets.get('SPOTIFY_CLIENT_SECRET'),
                'spotify_redirect_uri': st.secrets.get('SPOTIFY_REDIRECT_URI'),
                'youtube_music_headers': st.secrets.get('YOUTUBE_MUSIC_HEADERS')
            })
        except Exception as e:
            logging.warning(f"Failed to export to platform: {e}")
            pass
        
        return config
    
    @staticmethod
    def _show_export_results(results: Dict[str, Any]):
        """Show export results in Streamlit."""
        import streamlit as st
        
        for platform, result in results.items():
            if result['success']:
                st.success(f"✅ {platform.title()}: Successfully exported!")
                
                # Show additional info
                if 'file_path' in result:
                    st.info(f"📄 File saved: {result['file_path']}")
                
                if 'playlist_url' in result:
                    st.info(f"🔗 Playlist URL: {result['playlist_url']}")
                
                if 'tracks_not_found' in result and result['tracks_not_found'] > 0:
                    st.warning(f"⚠️ {result['tracks_not_found']} tracks not found on {platform}")
            else:
                st.error(f"❌ {platform.title()}: {result.get('error', 'Unknown error')}")  