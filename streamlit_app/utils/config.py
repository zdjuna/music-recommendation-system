"""
Configuration and environment management for the Streamlit app
"""

import os
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any, Optional

class Config:
    """Centralized configuration management"""
    
    def __init__(self):
        self._load_environment()
        self._setup_paths()
        
    def _load_environment(self):
        """Load environment variables"""
        env_file = Path('.env')
        config_env_file = Path('config/config.env')
        
        if env_file.exists():
            load_dotenv(env_file, override=True)
        elif config_env_file.exists():
            load_dotenv(config_env_file, override=True)
    
    def _setup_paths(self):
        """Setup important paths"""
        self.data_dir = Path('data')
        self.cache_dir = Path('cache')
        self.models_dir = Path('models')
        self.reports_dir = Path('reports')
        
        # Create directories if they don't exist
        for dir_path in [self.data_dir, self.cache_dir, self.models_dir, self.reports_dir]:
            dir_path.mkdir(exist_ok=True)
    
    @property
    def lastfm_api_key(self) -> Optional[str]:
        """Get LastFM API key"""
        return os.getenv('LASTFM_API_KEY')
    
    @property
    def cyanite_api_key(self) -> Optional[str]:
        """Get Cyanite API key"""
        return os.getenv('CYANITE_API_KEY')
    
    @property
    def spotify_client_id(self) -> Optional[str]:
        """Get Spotify client ID"""
        return os.getenv('SPOTIFY_CLIENT_ID')
    
    @property
    def spotify_client_secret(self) -> Optional[str]:
        """Get Spotify client secret"""
        return os.getenv('SPOTIFY_CLIENT_SECRET')
    
    def get_config_value(self, key: str, default: str = "") -> str:
        """Get configuration value from Streamlit secrets or environment variables"""
        try:
            return st.secrets[key]
        except (KeyError, FileNotFoundError):
            return os.getenv(key, default)
    
    @property
    def default_username(self) -> str:
        """Get default username"""
        return self.get_config_value('LASTFM_USERNAME', 'TestUser')
    
    @property
    def api_status(self) -> Dict[str, bool]:
        """Get status of all API configurations"""
        return {
            'lastfm': bool(self.lastfm_api_key),
            'cyanite': bool(self.cyanite_api_key),
            'spotify': bool(self.spotify_client_id and self.spotify_client_secret)
        }
    
    @property
    def is_production_ready(self) -> bool:
        """Check if system is ready for production use"""
        status = self.api_status
        return status['lastfm'] and (self.data_dir / f"{self.default_username}_scrobbles.csv").exists()

# Global config instance
config = Config()