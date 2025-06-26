"""
Unit tests for configuration management
"""

import pytest
import os
import tempfile
from pathlib import Path
import sys

# Add src to path
sys.path.append(str(Path(__file__).parent.parent.parent))

class TestConfig:
    """Test configuration management"""
    
    def test_config_initialization(self):
        """Test config initializes correctly"""
        from streamlit_app.utils.config import Config
        
        config = Config()
        assert hasattr(config, 'data_dir')
        assert hasattr(config, 'cache_dir')
        assert hasattr(config, 'models_dir')
        assert hasattr(config, 'reports_dir')
    
    def test_api_status(self):
        """Test API status detection"""
        from streamlit_app.utils.config import Config
        
        # Test with no API keys
        config = Config()
        status = config.api_status
        
        assert isinstance(status, dict)
        assert 'lastfm' in status
        assert 'cyanite' in status
        assert 'spotify' in status
        assert isinstance(status['lastfm'], bool)
        assert isinstance(status['cyanite'], bool)
        assert isinstance(status['spotify'], bool)
    
    def test_production_readiness(self):
        """Test production readiness check"""
        from streamlit_app.utils.config import Config
        
        config = Config()
        ready = config.is_production_ready
        assert isinstance(ready, bool)
    
    def test_default_values(self):
        """Test default configuration values"""
        from streamlit_app.utils.config import Config
        
        config = Config()
        username = config.default_username
        assert isinstance(username, str)
        assert len(username) > 0

if __name__ == "__main__":
    pytest.main([__file__])