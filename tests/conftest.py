"""
Pytest configuration and shared fixtures
"""

import pytest
import tempfile
import sqlite3
from pathlib import Path
import sys
import os

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

@pytest.fixture(scope="session")
def test_data_dir():
    """Create temporary directory for test data"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_scrobbles_data():
    """Sample scrobbles data for testing"""
    return [
        {
            'artist': 'The Beatles',
            'track': 'Hey Jude',
            'album': 'The Beatles 1967-1970',
            'timestamp': '2023-01-01 12:00:00'
        },
        {
            'artist': 'Queen',
            'track': 'Bohemian Rhapsody',
            'album': 'A Night at the Opera',
            'timestamp': '2023-01-01 13:00:00'
        },
        {
            'artist': 'Led Zeppelin',
            'track': 'Stairway to Heaven',
            'album': 'Led Zeppelin IV',
            'timestamp': '2023-01-01 14:00:00'
        }
    ]

@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing"""
    test_vars = {
        'LASTFM_API_KEY': 'test_lastfm_key',
        'CYANITE_API_KEY': 'test_cyanite_key',
        'SPOTIFY_CLIENT_ID': 'test_spotify_id',
        'SPOTIFY_CLIENT_SECRET': 'test_spotify_secret',
        'LASTFM_USERNAME': 'test_user'
    }
    
    for key, value in test_vars.items():
        monkeypatch.setenv(key, value)
    
    return test_vars

@pytest.fixture
def clean_cache():
    """Clean any cached data before/after tests"""
    # Clear any existing cache
    yield
    
    # Cleanup after test
    try:
        import streamlit as st
        st.cache_data.clear()
    except:
        pass

def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "api: mark test as requiring API access"
    )