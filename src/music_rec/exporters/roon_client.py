"""
Roon API Client

Direct integration with Roon Core for:
- Playlist creation and management
- Zone discovery and control
- Real-time music control
- Library browsing and search

Based on Roon's WebSocket API and HTTP endpoints.
"""

import json
import asyncio
import websockets
import aiohttp
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class RoonTransportState(Enum):
    """Roon transport states"""
    PLAYING = "playing"
    PAUSED = "paused"
    STOPPED = "stopped"
    LOADING = "loading"

@dataclass
class RoonZone:
    """Represents a Roon zone"""
    zone_id: str
    display_name: str
    state: RoonTransportState
    outputs: List[Dict[str, Any]]
    now_playing: Optional[Dict[str, Any]] = None
    queue_items_remaining: int = 0
    queue_time_remaining: int = 0

@dataclass
class RoonTrack:
    """Represents a track in Roon's format"""
    title: str
    artist: str
    album: str
    duration: Optional[int] = None
    track_id: Optional[str] = None
    image_key: Optional[str] = None

class RoonClient:
    """
    Roon API Client for direct integration with Roon Core
    
    Handles authentication, zone management, playlist operations,
    and real-time control of Roon music system.
    """
    
    def __init__(self, 
                 core_host: str,
                 core_port: int = 9100,
                 app_name: str = "Music Recommendation System",
                 app_version: str = "1.0.0"):
        """
        Initialize Roon client
        
        Args:
            core_host: IP address of Roon Core
            core_port: Port for Roon Core API (default 9100)
            app_name: Name of this application
            app_version: Version of this application
        """
        self.core_host = core_host
        self.core_port = core_port
        self.app_name = app_name
        self.app_version = app_version
        
        # Connection state
        self.websocket = None
        self.session = None
        self.authenticated = False
        self.core_id = None
        self.token = None
        
        # Cached data
        self.zones = {}
        self.outputs = {}
        
        # Event callbacks
        self.zone_callbacks = []
        self.transport_callbacks = []
        
        # API endpoints
        self.base_url = f"http://{core_host}:{core_port}/api/v1"
        self.ws_url = f"ws://{core_host}:{core_port}/api/v1/ws"
    
    async def connect(self) -> bool:
        """
        Connect to Roon Core and authenticate
        
        Returns:
            True if connection successful
        """
        try:
            # Create HTTP session
            self.session = aiohttp.ClientSession()
            
            # Test HTTP connection first
            async with self.session.get(f"{self.base_url}/ping") as response:
                if response.status != 200:
                    logger.error(f"Failed to ping Roon Core: {response.status}")
                    return False
            
            # Connect WebSocket
            self.websocket = await websockets.connect(self.ws_url)
            logger.info(f"Connected to Roon Core at {self.core_host}:{self.core_port}")
            
            # Authenticate
            auth_success = await self._authenticate()
            if not auth_success:
                logger.error("Failed to authenticate with Roon Core")
                return False
            
            # Start listening for events
            asyncio.create_task(self._listen_for_events())
            
            # Subscribe to zone and transport events
            await self._subscribe_to_events()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Roon Core: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from Roon Core"""
        if self.websocket:
            await self.websocket.close()
        if self.session:
            await self.session.close()
        
        self.authenticated = False
        logger.info("Disconnected from Roon Core")
    
    async def _authenticate(self) -> bool:
        """Authenticate with Roon Core"""
        auth_message = {
            "verb": "REQUEST",
            "request_id": "auth_request",
            "body": {
                "extension_id": "com.musicrec.roon",
                "display_name": self.app_name,
                "display_version": self.app_version,
                "publisher": "Music Recommendation System",
                "email": "support@musicrec.com"
            }
        }
        
        await self.websocket.send(json.dumps(auth_message))
        
        # Wait for authentication response
        try:
            response = await asyncio.wait_for(self.websocket.recv(), timeout=10.0)
            auth_response = json.loads(response)
            
            if auth_response.get("verb") == "SUCCESS":
                self.authenticated = True
                self.core_id = auth_response.get("body", {}).get("core_id")
                self.token = auth_response.get("body", {}).get("token")
                logger.info("Successfully authenticated with Roon Core")
                return True
            else:
                logger.error(f"Authentication failed: {auth_response}")
                return False
                
        except asyncio.TimeoutError:
            logger.error("Authentication timeout")
            return False
    
    async def _subscribe_to_events(self):
        """Subscribe to Roon events"""
        # Subscribe to zone events
        zone_subscribe = {
            "verb": "SUBSCRIBE",
            "request_id": "zone_subscribe",
            "body": {
                "subscription_key": "zones"
            }
        }
        await self.websocket.send(json.dumps(zone_subscribe))
        
        # Subscribe to transport events
        transport_subscribe = {
            "verb": "SUBSCRIBE", 
            "request_id": "transport_subscribe",
            "body": {
                "subscription_key": "transport"
            }
        }
        await self.websocket.send(json.dumps(transport_subscribe))
    
    async def _listen_for_events(self):
        """Listen for events from Roon Core"""
        try:
            async for message in self.websocket:
                try:
                    event = json.loads(message)
                    await self._handle_event(event)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON received: {message}")
                except Exception as e:
                    logger.error(f"Error handling event: {e}")
        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket connection closed")
        except Exception as e:
            logger.error(f"Error in event listener: {e}")
    
    async def _handle_event(self, event: Dict[str, Any]):
        """Handle events from Roon Core"""
        verb = event.get("verb")
        body = event.get("body", {})
        
        if verb == "EVENT":
            subscription_key = body.get("subscription_key")
            
            if subscription_key == "zones":
                await self._handle_zone_event(body)
            elif subscription_key == "transport":
                await self._handle_transport_event(body)
    
    async def _handle_zone_event(self, body: Dict[str, Any]):
        """Handle zone events"""
        zones_changed = body.get("zones_changed", [])
        zones_seek_changed = body.get("zones_seek_changed", [])
        
        for zone_data in zones_changed:
            zone = self._parse_zone(zone_data)
            self.zones[zone.zone_id] = zone
            
            # Notify callbacks
            for callback in self.zone_callbacks:
                try:
                    await callback(zone)
                except Exception as e:
                    logger.error(f"Error in zone callback: {e}")
    
    async def _handle_transport_event(self, body: Dict[str, Any]):
        """Handle transport events"""
        zones_changed = body.get("zones_changed", [])
        
        for zone_data in zones_changed:
            zone_id = zone_data.get("zone_id")
            if zone_id in self.zones:
                # Update transport state
                self.zones[zone_id].state = RoonTransportState(
                    zone_data.get("state", "stopped")
                )
                
                # Notify callbacks
                for callback in self.transport_callbacks:
                    try:
                        await callback(self.zones[zone_id])
                    except Exception as e:
                        logger.error(f"Error in transport callback: {e}")
    
    def _parse_zone(self, zone_data: Dict[str, Any]) -> RoonZone:
        """Parse zone data from Roon"""
        return RoonZone(
            zone_id=zone_data.get("zone_id"),
            display_name=zone_data.get("display_name", "Unknown Zone"),
            state=RoonTransportState(zone_data.get("state", "stopped")),
            outputs=zone_data.get("outputs", []),
            now_playing=zone_data.get("now_playing"),
            queue_items_remaining=zone_data.get("queue_items_remaining", 0),
            queue_time_remaining=zone_data.get("queue_time_remaining", 0)
        )
    
    async def get_zones(self) -> List[RoonZone]:
        """Get all available zones"""
        if not self.authenticated:
            raise Exception("Not authenticated with Roon Core")
        
        request = {
            "verb": "REQUEST",
            "request_id": "get_zones",
            "body": {
                "subscription_key": "zones"
            }
        }
        
        await self.websocket.send(json.dumps(request))
        
        # Return cached zones for now
        return list(self.zones.values())
    
    async def create_playlist(self, 
                            name: str, 
                            tracks: List[RoonTrack],
                            zone_id: Optional[str] = None) -> bool:
        """
        Create a playlist in Roon
        
        Args:
            name: Playlist name
            tracks: List of tracks to add
            zone_id: Optional zone to start playing immediately
            
        Returns:
            True if successful
        """
        try:
            # Search for tracks in Roon library
            roon_tracks = []
            for track in tracks:
                found_track = await self._search_track(track)
                if found_track:
                    roon_tracks.append(found_track)
                else:
                    logger.warning(f"Track not found in Roon library: {track.artist} - {track.title}")
            
            if not roon_tracks:
                logger.error("No tracks found in Roon library")
                return False
            
            # Create playlist via HTTP API
            playlist_data = {
                "name": name,
                "description": f"Generated by Music Recommendation System at {datetime.now().isoformat()}",
                "tracks": roon_tracks
            }
            
            async with self.session.post(
                f"{self.base_url}/playlists",
                json=playlist_data,
                headers={"Authorization": f"Bearer {self.token}"}
            ) as response:
                if response.status == 201:
                    playlist_id = (await response.json()).get("playlist_id")
                    logger.info(f"Created playlist '{name}' with ID: {playlist_id}")
                    
                    # Optionally start playing in specified zone
                    if zone_id and playlist_id:
                        await self.play_playlist(playlist_id, zone_id)
                    
                    return True
                else:
                    logger.error(f"Failed to create playlist: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error creating playlist: {e}")
            return False
    
    async def _search_track(self, track: RoonTrack) -> Optional[Dict[str, Any]]:
        """Search for a track in Roon library"""
        try:
            search_query = f"{track.artist} {track.title}"
            
            async with self.session.get(
                f"{self.base_url}/browse/search",
                params={"query": search_query, "type": "tracks"},
                headers={"Authorization": f"Bearer {self.token}"}
            ) as response:
                if response.status == 200:
                    results = await response.json()
                    tracks = results.get("tracks", [])
                    
                    # Find best match
                    for result_track in tracks:
                        if (result_track.get("title", "").lower() == track.title.lower() and
                            result_track.get("artist", "").lower() == track.artist.lower()):
                            return result_track
                    
                    # Return first result if exact match not found
                    return tracks[0] if tracks else None
                else:
                    logger.warning(f"Search failed for track: {track.artist} - {track.title}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error searching for track: {e}")
            return None
    
    async def play_playlist(self, playlist_id: str, zone_id: str) -> bool:
        """Play a playlist in a specific zone"""
        try:
            play_request = {
                "verb": "REQUEST",
                "request_id": "play_playlist",
                "body": {
                    "zone_id": zone_id,
                    "playlist_id": playlist_id,
                    "action": "play"
                }
            }
            
            await self.websocket.send(json.dumps(play_request))
            logger.info(f"Started playing playlist {playlist_id} in zone {zone_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error playing playlist: {e}")
            return False
    
    async def control_transport(self, zone_id: str, action: str) -> bool:
        """
        Control transport in a zone
        
        Args:
            zone_id: Zone to control
            action: 'play', 'pause', 'stop', 'next', 'previous'
        """
        try:
            control_request = {
                "verb": "REQUEST",
                "request_id": "transport_control",
                "body": {
                    "zone_id": zone_id,
                    "control": action
                }
            }
            
            await self.websocket.send(json.dumps(control_request))
            logger.info(f"Transport control '{action}' sent to zone {zone_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error controlling transport: {e}")
            return False
    
    def add_zone_callback(self, callback: Callable[[RoonZone], None]):
        """Add callback for zone events"""
        self.zone_callbacks.append(callback)
    
    def add_transport_callback(self, callback: Callable[[RoonZone], None]):
        """Add callback for transport events"""
        self.transport_callbacks.append(callback)
    
    async def get_zone_recommendations(self, zone_id: str) -> Dict[str, Any]:
        """
        Get zone-specific information for recommendations
        
        Returns:
            Dictionary with zone context for recommendations
        """
        if zone_id not in self.zones:
            return {}
        
        zone = self.zones[zone_id]
        
        return {
            "zone_name": zone.display_name,
            "current_state": zone.state.value,
            "now_playing": zone.now_playing,
            "queue_remaining": zone.queue_items_remaining,
            "outputs": zone.outputs,
            "context": self._infer_zone_context(zone)
        }
    
    def _infer_zone_context(self, zone: RoonZone) -> Dict[str, Any]:
        """Infer context from zone information"""
        context = {
            "room_type": "unknown",
            "activity": "unknown",
            "time_context": "unknown"
        }
        
        # Infer room type from zone name
        zone_name_lower = zone.display_name.lower()
        if any(word in zone_name_lower for word in ["kitchen", "dining"]):
            context["room_type"] = "kitchen"
        elif any(word in zone_name_lower for word in ["bedroom", "master"]):
            context["room_type"] = "bedroom"
        elif any(word in zone_name_lower for word in ["living", "lounge", "family"]):
            context["room_type"] = "living_room"
        elif any(word in zone_name_lower for word in ["office", "study", "work"]):
            context["room_type"] = "office"
        elif any(word in zone_name_lower for word in ["bathroom", "bath"]):
            context["room_type"] = "bathroom"
        
        # Infer activity from current state and time
        current_hour = datetime.now().hour
        if 6 <= current_hour <= 10:
            context["time_context"] = "morning"
        elif 11 <= current_hour <= 14:
            context["time_context"] = "afternoon"
        elif 15 <= current_hour <= 19:
            context["time_context"] = "evening"
        else:
            context["time_context"] = "night"
        
        return context 