"""
Real-time Music Recommendation Updater

Automatically updates recommendations and insights based on recent listening patterns.
Provides live updates without needing to reprocess entire datasets.
"""

import asyncio
import pandas as pd
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from pathlib import Path
import time

logger = logging.getLogger(__name__)

class RealTimeUpdater:
    """
    Real-time updater for music recommendations and insights.
    
    Monitors for new scrobbles and incrementally updates recommendations
    without needing to reprocess entire datasets.
    """
    
    def __init__(self, username: str, data_dir: str = "data", 
                 update_interval: int = 300):  # 5 minutes default
        """
        Initialize real-time updater.
        
        Args:
            username: Last.fm username
            data_dir: Directory containing music data
            update_interval: Update interval in seconds
        """
        self.username = username
        self.data_dir = Path(data_dir)
        self.update_interval = update_interval
        
        # File paths
        self.scrobbles_file = self.data_dir / f"{username}_scrobbles.csv"
        self.enriched_file = self.data_dir / f"{username}_enriched.csv" 
        self.stats_file = self.data_dir / f"{username}_stats.json"
        self.cache_file = self.data_dir / f"{username}_realtime_cache.json"
        
        # State tracking
        self.last_update = None
        self.last_scrobble_count = 0
        self.running = False
        self.callbacks = []
        
        # Load initial state
        self._load_initial_state()
    
    def _load_initial_state(self):
        """Load initial state from existing data."""
        try:
            if self.scrobbles_file.exists():
                df = pd.read_csv(self.scrobbles_file)
                self.last_scrobble_count = len(df)
                
                # Get timestamp of latest scrobble
                if 'timestamp' in df.columns and len(df) > 0:
                    latest_timestamp = df['timestamp'].max()
                    self.last_update = pd.to_datetime(latest_timestamp)
                    
            logger.info(f"Initialized with {self.last_scrobble_count} scrobbles")
            
        except Exception as e:
            logger.error(f"Error loading initial state: {e}")
            self.last_scrobble_count = 0
    
    def register_callback(self, callback: Callable[[Dict], None]):
        """
        Register callback function for real-time updates.
        
        Args:
            callback: Function to call when updates are detected
        """
        self.callbacks.append(callback)
    
    async def start_monitoring(self):
        """Start real-time monitoring for updates."""
        self.running = True
        logger.info(f"Started real-time monitoring (update interval: {self.update_interval}s)")
        
        while self.running:
            try:
                await self._check_for_updates()
                await asyncio.sleep(self.update_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(30)  # Shorter retry interval
    
    def stop_monitoring(self):
        """Stop real-time monitoring."""
        self.running = False
        logger.info("Stopped real-time monitoring")
    
    async def _check_for_updates(self):
        """Check for new scrobbles and trigger updates if found."""
        try:
            if not self.scrobbles_file.exists():
                return
            
            # Quick check: compare file modification time
            file_mtime = datetime.fromtimestamp(self.scrobbles_file.stat().st_mtime)
            if self.last_update and file_mtime <= self.last_update:
                return
            
            # Load current data
            df = pd.read_csv(self.scrobbles_file)
            current_count = len(df)
            
            if current_count > self.last_scrobble_count:
                new_scrobbles = current_count - self.last_scrobble_count
                logger.info(f"Detected {new_scrobbles} new scrobbles")
                
                # Get new scrobbles
                new_data = df.tail(new_scrobbles)
                
                # Analyze new patterns
                update_info = await self._analyze_new_patterns(new_data, df)
                
                # Trigger callbacks
                for callback in self.callbacks:
                    try:
                        callback(update_info)
                    except Exception as e:
                        logger.error(f"Error in callback: {e}")
                
                # Update state
                self.last_scrobble_count = current_count
                self.last_update = datetime.now()
                
                # Cache update info
                self._cache_update_info(update_info)
                
        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
    
    async def _analyze_new_patterns(self, new_data: pd.DataFrame, 
                                   full_data: pd.DataFrame) -> Dict:
        """
        Analyze patterns in new scrobbles.
        
        Args:
            new_data: New scrobbles since last update
            full_data: Complete scrobble dataset
            
        Returns:
            Dictionary with analysis results
        """
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'new_scrobbles_count': len(new_data),
            'total_scrobbles': len(full_data),
            'time_range': self._get_time_range(new_data),
            'new_artists': self._find_new_artists(new_data, full_data),
            'mood_shift': self._detect_mood_shift(new_data),
            'listening_intensity': self._calculate_recent_intensity(new_data),
            'recommendations_refresh_needed': False
        }
        
        # Determine if recommendations need refreshing
        analysis['recommendations_refresh_needed'] = (
            len(analysis['new_artists']) > 2 or  # New artists discovered
            analysis['listening_intensity'] > 1.5 or  # High intensity listening
            len(new_data) > 50  # Large number of new scrobbles
        )
        
        return analysis
    
    def _get_time_range(self, data: pd.DataFrame) -> Dict:
        """Get time range of new data."""
        if 'timestamp' in data.columns and len(data) > 0:
            timestamps = pd.to_datetime(data['timestamp'])
            return {
                'start': timestamps.min().isoformat(),
                'end': timestamps.max().isoformat(),
                'duration_hours': (timestamps.max() - timestamps.min()).total_seconds() / 3600
            }
        return {}
    
    def _find_new_artists(self, new_data: pd.DataFrame, 
                         full_data: pd.DataFrame) -> List[str]:
        """Find artists that are new in recent scrobbles."""
        if 'artist' not in new_data.columns:
            return []
        
        # Get artists from recent data
        recent_artists = set(new_data['artist'].unique())
        
        # Get artists from older data (excluding recent)
        older_data = full_data.iloc[:-len(new_data)] if len(full_data) > len(new_data) else pd.DataFrame()
        if len(older_data) > 0 and 'artist' in older_data.columns:
            older_artists = set(older_data['artist'].unique())
        else:
            older_artists = set()
        
        # Find truly new artists
        new_artists = recent_artists - older_artists
        return list(new_artists)
    
    def _detect_mood_shift(self, data: pd.DataFrame) -> Dict:
        """Detect mood shifts in recent listening."""
        mood_info = {'detected': False, 'shift_type': None}
        
        if 'cyanite_mood' in data.columns:
            moods = data['cyanite_mood'].dropna()
            if len(moods) > 0:
                dominant_mood = moods.mode().iloc[0] if len(moods.mode()) > 0 else None
                mood_info = {
                    'detected': True,
                    'dominant_mood': dominant_mood,
                    'mood_distribution': moods.value_counts().to_dict()
                }
        
        return mood_info
    
    def _calculate_recent_intensity(self, data: pd.DataFrame) -> float:
        """Calculate listening intensity (tracks per hour)."""
        if 'timestamp' in data.columns and len(data) > 1:
            timestamps = pd.to_datetime(data['timestamp'])
            duration_hours = (timestamps.max() - timestamps.min()).total_seconds() / 3600
            
            if duration_hours > 0:
                return len(data) / duration_hours
        
        return 0.0
    
    def _cache_update_info(self, info: Dict):
        """Cache update information for later retrieval."""
        try:
            cache_data = {
                'last_update': info,
                'update_history': []
            }
            
            # Load existing cache
            if self.cache_file.exists():
                with open(self.cache_file) as f:
                    existing_cache = json.load(f)
                    cache_data['update_history'] = existing_cache.get('update_history', [])
            
            # Add current update to history (keep last 10)
            cache_data['update_history'].append(info)
            cache_data['update_history'] = cache_data['update_history'][-10:]
            
            # Save cache
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error caching update info: {e}")
    
    def get_recent_updates(self) -> Dict:
        """Get recent update information."""
        try:
            if self.cache_file.exists():
                with open(self.cache_file) as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading recent updates: {e}")
        
        return {'last_update': None, 'update_history': []}
    
    def force_update_check(self) -> Dict:
        """Force an immediate update check."""
        logger.info("Forcing update check...")
        
        # Run update check synchronously
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(self._check_for_updates())
            return self.get_recent_updates()
        finally:
            loop.close()
    
    def get_monitoring_status(self) -> Dict:
        """Get current monitoring status."""
        return {
            'running': self.running,
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'scrobble_count': self.last_scrobble_count,
            'update_interval': self.update_interval,
            'callbacks_registered': len(self.callbacks)
        }


class StreamlitUpdater:
    """
    Streamlit-specific real-time updater with session state management.
    """
    
    @staticmethod
    def initialize_realtime_updates(username: str):
        """Initialize real-time updates for Streamlit app."""
        import streamlit as st
        
        # Initialize updater in session state
        if 'rt_updater' not in st.session_state:
            st.session_state.rt_updater = RealTimeUpdater(username)
            
            # Register callback for Streamlit updates
            def streamlit_callback(update_info):
                if 'last_rt_update' not in st.session_state:
                    st.session_state.last_rt_update = {}
                st.session_state.last_rt_update = update_info
                
                # Trigger rerun if significant update
                if update_info.get('recommendations_refresh_needed'):
                    st.rerun()
            
            st.session_state.rt_updater.register_callback(streamlit_callback)
    
    @staticmethod
    def show_realtime_status():
        """Show real-time update status in Streamlit."""
        import streamlit as st
        
        if 'rt_updater' not in st.session_state:
            return
        
        updater = st.session_state.rt_updater
        status = updater.get_monitoring_status()
        recent_updates = updater.get_recent_updates()
        
        # Show status
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if status['running']:
                st.success("🟢 Real-time monitoring active")
            else:
                st.error("🔴 Real-time monitoring inactive")
        
        with col2:
            if status['last_update']:
                last_update = pd.to_datetime(status['last_update'])
                time_ago = datetime.now() - last_update
                st.info(f"⏱️ Last check: {time_ago.seconds // 60}m ago")
            else:
                st.warning("⏱️ No updates yet")
        
        with col3:
            st.metric("📊 Total Scrobbles", f"{status['scrobble_count']:,}")
        
        # Show recent update if available
        if recent_updates.get('last_update'):
            with st.expander("📈 Latest Update Details", expanded=False):
                update = recent_updates['last_update']
                
                st.write(f"**New scrobbles:** {update.get('new_scrobbles_count', 0)}")
                
                if update.get('new_artists'):
                    st.write("**New artists discovered:**")
                    for artist in update['new_artists'][:5]:  # Show first 5
                        st.write(f"• {artist}")
                
                if update.get('mood_shift', {}).get('detected'):
                    mood = update['mood_shift'].get('dominant_mood')
                    st.write(f"**Current mood:** {mood}")
                
                intensity = update.get('listening_intensity', 0)
                if intensity > 0:
                    st.write(f"**Listening intensity:** {intensity:.1f} tracks/hour")
        
        # Manual update button
        if st.button("🔄 Check for Updates Now"):
            with st.spinner("Checking for updates..."):
                updater.force_update_check()
                st.rerun()
    
    @staticmethod
    def start_background_monitoring():
        """Start background monitoring (for deployment)."""
        import streamlit as st
        
        if 'rt_updater' not in st.session_state:
            return
        
        updater = st.session_state.rt_updater
        
        if not updater.running:
            # Start monitoring in background thread
            import threading
            
            def run_monitoring():
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(updater.start_monitoring())
            
            thread = threading.Thread(target=run_monitoring, daemon=True)
            thread.start()
            
            st.success("Started background monitoring!") 