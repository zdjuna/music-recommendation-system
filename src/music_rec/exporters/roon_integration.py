"""
Roon Integration Module

High-level integration with Roon music system:
- Automatic playlist creation and synchronization
- Zone-specific recommendations
- Real-time playlist updates
- Context-aware music suggestions
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path

from .roon_client import RoonClient, RoonTrack, RoonZone
from ..recommenders.recommendation_engine import RecommendationEngine, RecommendationRequest
from ..recommenders.playlist_generator import PlaylistGenerator

logger = logging.getLogger(__name__)

class RoonIntegration:
    """
    High-level Roon integration for the Music Recommendation System
    
    Provides seamless integration between recommendation engine and Roon Core
    """
    
    def __init__(self, 
                 core_host: str,
                 recommendation_engine: RecommendationEngine,
                 core_port: int = 9100,
                 auto_sync: bool = True):
        """
        Initialize Roon integration
        
        Args:
            core_host: IP address of Roon Core
            recommendation_engine: Recommendation engine instance
            core_port: Roon Core port (default 9100)
            auto_sync: Enable automatic playlist synchronization
        """
        self.roon_client = RoonClient(core_host, core_port)
        self.recommendation_engine = recommendation_engine
        self.playlist_generator = PlaylistGenerator()
        self.auto_sync = auto_sync
        
        # State tracking
        self.connected = False
        self.active_playlists = {}  # playlist_id -> metadata
        self.zone_contexts = {}     # zone_id -> context info
        
        # Auto-sync settings
        self.sync_interval = 300    # 5 minutes
        self.last_sync = None
        
        # Event handlers
        self.roon_client.add_zone_callback(self._on_zone_changed)
        self.roon_client.add_transport_callback(self._on_transport_changed)
    
    async def connect(self) -> bool:
        """Connect to Roon Core"""
        try:
            success = await self.roon_client.connect()
            if success:
                self.connected = True
                logger.info("Successfully connected to Roon Core")
                
                # Start auto-sync if enabled
                if self.auto_sync:
                    asyncio.create_task(self._auto_sync_loop())
                
                return True
            else:
                logger.error("Failed to connect to Roon Core")
                return False
                
        except Exception as e:
            logger.error(f"Error connecting to Roon: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from Roon Core"""
        await self.roon_client.disconnect()
        self.connected = False
        logger.info("Disconnected from Roon Core")
    
    async def create_recommendation_playlist(self, 
                                           request: RecommendationRequest,
                                           playlist_name: str,
                                           zone_id: Optional[str] = None,
                                           auto_play: bool = False) -> bool:
        """
        Create a recommendation playlist in Roon
        
        Args:
            request: Recommendation request parameters
            playlist_name: Name for the playlist
            zone_id: Optional zone for context-aware recommendations
            auto_play: Start playing immediately
            
        Returns:
            True if successful
        """
        if not self.connected:
            logger.error("Not connected to Roon Core")
            return False
        
        try:
            # Enhance request with zone context if provided
            if zone_id:
                zone_context = await self.roon_client.get_zone_recommendations(zone_id)
                request = self._enhance_request_with_zone_context(request, zone_context)
            
            # Generate recommendations
            logger.info(f"Generating recommendations for playlist: {playlist_name}")
            result = self.recommendation_engine.generate_recommendations(request)
            
            if not result.tracks:
                logger.warning("No recommendations generated")
                return False
            
            # Convert to Roon tracks
            roon_tracks = self._convert_to_roon_tracks(result.tracks)
            
            # Create playlist in Roon
            success = await self.roon_client.create_playlist(
                name=playlist_name,
                tracks=roon_tracks,
                zone_id=zone_id if auto_play else None
            )
            
            if success:
                # Track the playlist
                self.active_playlists[playlist_name] = {
                    'created_at': datetime.now(),
                    'request': request,
                    'zone_id': zone_id,
                    'track_count': len(roon_tracks)
                }
                
                logger.info(f"Successfully created Roon playlist: {playlist_name}")
                return True
            else:
                logger.error(f"Failed to create Roon playlist: {playlist_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error creating recommendation playlist: {e}")
            return False
    
    async def create_zone_specific_playlist(self, 
                                          zone_id: str,
                                          playlist_length: int = 20,
                                          auto_play: bool = True) -> bool:
        """
        Create a playlist specifically tailored for a zone
        
        Args:
            zone_id: Target zone ID
            playlist_length: Number of tracks
            auto_play: Start playing immediately
            
        Returns:
            True if successful
        """
        if not self.connected:
            logger.error("Not connected to Roon Core")
            return False
        
        try:
            # Get zone information
            zones = await self.roon_client.get_zones()
            target_zone = next((z for z in zones if z.zone_id == zone_id), None)
            
            if not target_zone:
                logger.error(f"Zone not found: {zone_id}")
                return False
            
            # Get zone context for recommendations
            zone_context = await self.roon_client.get_zone_recommendations(zone_id)
            
            # Create context-aware recommendation request
            request = self._create_zone_request(zone_context, playlist_length)
            
            # Generate playlist name
            playlist_name = f"{target_zone.display_name} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            # Create the playlist
            return await self.create_recommendation_playlist(
                request=request,
                playlist_name=playlist_name,
                zone_id=zone_id,
                auto_play=auto_play
            )
            
        except Exception as e:
            logger.error(f"Error creating zone-specific playlist: {e}")
            return False
    
    async def update_playlist_for_zone(self, zone_id: str) -> bool:
        """
        Update or create a fresh playlist for a zone based on current context
        
        Args:
            zone_id: Zone to update playlist for
            
        Returns:
            True if successful
        """
        try:
            # Check if zone has an active playlist
            zone_playlist = None
            for playlist_name, metadata in self.active_playlists.items():
                if metadata.get('zone_id') == zone_id:
                    zone_playlist = playlist_name
                    break
            
            if zone_playlist:
                # Update existing playlist
                logger.info(f"Updating existing playlist for zone: {zone_id}")
                # For now, create a new playlist (Roon API limitations)
                return await self.create_zone_specific_playlist(zone_id, auto_play=False)
            else:
                # Create new playlist
                logger.info(f"Creating new playlist for zone: {zone_id}")
                return await self.create_zone_specific_playlist(zone_id, auto_play=False)
                
        except Exception as e:
            logger.error(f"Error updating playlist for zone: {e}")
            return False
    
    async def get_zone_status(self) -> Dict[str, Any]:
        """Get status of all zones and their playlists"""
        if not self.connected:
            return {"error": "Not connected to Roon Core"}
        
        try:
            zones = await self.roon_client.get_zones()
            zone_status = {}
            
            for zone in zones:
                zone_status[zone.zone_id] = {
                    'name': zone.display_name,
                    'state': zone.state.value,
                    'now_playing': zone.now_playing,
                    'queue_remaining': zone.queue_items_remaining,
                    'has_active_playlist': any(
                        metadata.get('zone_id') == zone.zone_id 
                        for metadata in self.active_playlists.values()
                    ),
                    'context': await self.roon_client.get_zone_recommendations(zone.zone_id)
                }
            
            return {
                'connected': True,
                'zones': zone_status,
                'active_playlists': len(self.active_playlists),
                'last_sync': self.last_sync.isoformat() if self.last_sync else None
            }
            
        except Exception as e:
            logger.error(f"Error getting zone status: {e}")
            return {"error": str(e)}
    
    async def control_zone_transport(self, zone_id: str, action: str) -> bool:
        """
        Control transport in a specific zone
        
        Args:
            zone_id: Zone to control
            action: 'play', 'pause', 'stop', 'next', 'previous'
            
        Returns:
            True if successful
        """
        if not self.connected:
            logger.error("Not connected to Roon Core")
            return False
        
        return await self.roon_client.control_transport(zone_id, action)
    
    def _convert_to_roon_tracks(self, tracks: List[Dict[str, Any]]) -> List[RoonTrack]:
        """Convert recommendation tracks to Roon format"""
        roon_tracks = []
        
        for track in tracks:
            roon_track = RoonTrack(
                title=track.get('track', 'Unknown Track'),
                artist=track.get('artist', 'Unknown Artist'),
                album=track.get('album', 'Unknown Album'),
                duration=track.get('duration')
            )
            roon_tracks.append(roon_track)
        
        return roon_tracks
    
    def _enhance_request_with_zone_context(self, 
                                         request: RecommendationRequest, 
                                         zone_context: Dict[str, Any]) -> RecommendationRequest:
        """Enhance recommendation request with zone context"""
        context = zone_context.get('context', {})
        
        # Adjust mood based on room type and time
        room_type = context.get('room_type', 'unknown')
        time_context = context.get('time_context', 'unknown')
        
        # Room-specific mood adjustments
        if room_type == 'kitchen' and not request.mood:
            request.mood = 'energetic'
        elif room_type == 'bedroom' and not request.mood:
            request.mood = 'calm'
        elif room_type == 'office' and not request.mood:
            request.mood = 'focus'
        
        # Time-specific adjustments
        if time_context == 'morning' and not request.energy_level:
            request.energy_level = 'high'
        elif time_context == 'evening' and not request.energy_level:
            request.energy_level = 'medium'
        elif time_context == 'night' and not request.energy_level:
            request.energy_level = 'low'
        
        # Set time context if not specified
        if not request.time_context:
            request.time_context = time_context
        
        return request
    
    def _create_zone_request(self, zone_context: Dict[str, Any], playlist_length: int) -> RecommendationRequest:
        """Create a recommendation request based on zone context"""
        context = zone_context.get('context', {})
        
        # Base request
        request = RecommendationRequest(
            playlist_length=playlist_length,
            discovery_level=0.3,  # Balanced discovery
            exclude_recent=True
        )
        
        # Enhance with context
        return self._enhance_request_with_zone_context(request, zone_context)
    
    async def _on_zone_changed(self, zone: RoonZone):
        """Handle zone change events"""
        logger.debug(f"Zone changed: {zone.display_name} ({zone.state.value})")
        
        # Update zone context
        self.zone_contexts[zone.zone_id] = {
            'last_updated': datetime.now(),
            'state': zone.state.value,
            'now_playing': zone.now_playing
        }
    
    async def _on_transport_changed(self, zone: RoonZone):
        """Handle transport change events"""
        logger.debug(f"Transport changed in {zone.display_name}: {zone.state.value}")
        
        # If a zone stops playing and has low queue, suggest updating playlist
        if (zone.state.value == 'stopped' and 
            zone.queue_items_remaining < 3 and
            self.auto_sync):
            
            logger.info(f"Zone {zone.display_name} has low queue, considering playlist update")
            # Could trigger automatic playlist refresh here
    
    async def _auto_sync_loop(self):
        """Automatic synchronization loop"""
        while self.connected:
            try:
                await asyncio.sleep(self.sync_interval)
                
                if not self.connected:
                    break
                
                # Check for zones that need playlist updates
                zones = await self.roon_client.get_zones()
                
                for zone in zones:
                    # Update playlists for zones with low queue
                    if (zone.queue_items_remaining < 5 and 
                        zone.state.value in ['playing', 'paused']):
                        
                        logger.info(f"Auto-updating playlist for zone: {zone.display_name}")
                        await self.update_playlist_for_zone(zone.zone_id)
                
                self.last_sync = datetime.now()
                logger.debug("Auto-sync completed")
                
            except Exception as e:
                logger.error(f"Error in auto-sync loop: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def generate_preset_playlists_for_zones(self) -> Dict[str, bool]:
        """Generate preset playlists for all zones"""
        if not self.connected:
            logger.error("Not connected to Roon Core")
            return {}
        
        results = {}
        
        try:
            zones = await self.roon_client.get_zones()
            
            for zone in zones:
                logger.info(f"Generating preset playlists for zone: {zone.display_name}")
                
                # Create different playlists for different times/moods
                presets = [
                    ('Morning Energy', {'mood': 'energetic', 'time_context': 'morning'}),
                    ('Focus Work', {'mood': 'calm', 'energy_level': 'medium'}),
                    ('Evening Chill', {'mood': 'calm', 'time_context': 'evening'}),
                    ('Weekend Discovery', {'discovery_level': 0.7, 'playlist_length': 30})
                ]
                
                zone_results = {}
                for preset_name, params in presets:
                    request = RecommendationRequest(**params)
                    playlist_name = f"{zone.display_name} - {preset_name}"
                    
                    success = await self.create_recommendation_playlist(
                        request=request,
                        playlist_name=playlist_name,
                        zone_id=zone.zone_id,
                        auto_play=False
                    )
                    
                    zone_results[preset_name] = success
                
                results[zone.display_name] = zone_results
            
            return results
            
        except Exception as e:
            logger.error(f"Error generating preset playlists: {e}")
            return {} 