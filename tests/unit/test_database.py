"""
Unit tests for database functionality
"""

import pytest
import tempfile
import sqlite3
from pathlib import Path
import sys

# Add src to path
sys.path.append(str(Path(__file__).parent.parent.parent))
from streamlit_app.models.database import DatabaseManager

class TestDatabaseManager:
    """Test DatabaseManager functionality"""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        db = DatabaseManager(db_path)
        yield db
        
        # Cleanup
        Path(db_path).unlink(missing_ok=True)
    
    def test_database_initialization(self, temp_db):
        """Test database tables are created correctly"""
        # Check that all required tables exist
        with sqlite3.connect(temp_db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            required_tables = [
                'users', 'tracks', 'scrobbles', 'track_enrichment',
                'playlists', 'playlist_tracks', 'user_feedback'
            ]
            
            for table in required_tables:
                assert table in tables, f"Table {table} not found"
    
    def test_user_creation(self, temp_db):
        """Test user creation and retrieval"""
        user_id = temp_db.get_or_create_user("test_user", "Test User")
        assert isinstance(user_id, int)
        assert user_id > 0
        
        # Test duplicate user creation returns same ID
        user_id2 = temp_db.get_or_create_user("test_user", "Test User")
        assert user_id == user_id2
    
    def test_track_creation(self, temp_db):
        """Test track creation and retrieval"""
        track_id = temp_db.get_or_create_track("Test Artist", "Test Track", "Test Album")
        assert isinstance(track_id, int)
        assert track_id > 0
        
        # Test duplicate track creation returns same ID
        track_id2 = temp_db.get_or_create_track("Test Artist", "Test Track", "Test Album")
        assert track_id == track_id2
    
    def test_playlist_creation(self, temp_db):
        """Test playlist creation"""
        playlist_id = temp_db.create_playlist("test_user", "Test Playlist", "Test Description")
        assert isinstance(playlist_id, int)
        assert playlist_id > 0
        
        # Verify playlist was created
        playlists = temp_db.get_user_playlists("test_user")
        assert len(playlists) == 1
        assert playlists[0]['name'] == "Test Playlist"
    
    def test_playlist_tracks(self, temp_db):
        """Test adding tracks to playlist"""
        playlist_id = temp_db.create_playlist("test_user", "Test Playlist")
        
        tracks = [
            {"artist": "Artist 1", "track": "Track 1", "album": "Album 1"},
            {"artist": "Artist 2", "track": "Track 2", "album": "Album 2"}
        ]
        
        temp_db.add_tracks_to_playlist(playlist_id, tracks)
        
        playlist_tracks = temp_db.get_playlist_tracks(playlist_id)
        assert len(playlist_tracks) == 2
        assert playlist_tracks[0]['artist'] == "Artist 1"
        assert playlist_tracks[1]['artist'] == "Artist 2"
    
    def test_user_stats(self, temp_db):
        """Test user statistics calculation"""
        # Create user with some data
        user_id = temp_db.get_or_create_user("test_user")
        
        # Add some tracks and scrobbles
        with sqlite3.connect(temp_db.db_path) as conn:
            cursor = conn.cursor()
            
            # Add tracks
            cursor.execute("INSERT INTO tracks (artist, track) VALUES (?, ?)", ("Artist 1", "Track 1"))
            track_id1 = cursor.lastrowid
            cursor.execute("INSERT INTO tracks (artist, track) VALUES (?, ?)", ("Artist 2", "Track 2"))
            track_id2 = cursor.lastrowid
            
            # Add scrobbles
            cursor.execute("INSERT INTO scrobbles (user_id, track_id, timestamp) VALUES (?, ?, ?)", 
                         (user_id, track_id1, "2023-01-01 12:00:00"))
            cursor.execute("INSERT INTO scrobbles (user_id, track_id, timestamp) VALUES (?, ?, ?)", 
                         (user_id, track_id2, "2023-01-01 13:00:00"))
            
            conn.commit()
        
        stats = temp_db.get_user_stats("test_user")
        assert stats['total_scrobbles'] == 2
        assert stats['unique_artists'] == 2
        assert stats['unique_tracks'] == 2

if __name__ == "__main__":
    pytest.main([__file__])