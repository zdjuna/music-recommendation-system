"""
End-to-end workflow tests
"""

import pytest
import tempfile
import pandas as pd
from pathlib import Path
import sys

# Add src to path
sys.path.append(str(Path(__file__).parent.parent.parent))
from streamlit_app.models.database import DatabaseManager

class TestCompleteWorkflow:
    """Test complete user workflows"""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        db = DatabaseManager(db_path)
        yield db
        
        # Cleanup
        Path(db_path).unlink(missing_ok=True)
    
    @pytest.fixture
    def sample_csv_data(self):
        """Create sample CSV data"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            # Write sample CSV data
            f.write("artist,track,album,timestamp\n")
            f.write("The Beatles,Hey Jude,The Beatles 1967-1970,2023-01-01 12:00:00\n")
            f.write("Queen,Bohemian Rhapsody,A Night at the Opera,2023-01-01 13:00:00\n")
            f.write("Led Zeppelin,Stairway to Heaven,Led Zeppelin IV,2023-01-01 14:00:00\n")
            csv_path = f.name
        
        yield Path(csv_path)
        
        # Cleanup
        Path(csv_path).unlink(missing_ok=True)
    
    def test_data_import_workflow(self, temp_db, sample_csv_data):
        """Test complete data import workflow"""
        username = "test_user"
        
        # Import CSV data
        temp_db.import_csv_data(username, sample_csv_data)
        
        # Verify user was created
        user_id = temp_db.get_or_create_user(username)
        assert user_id > 0
        
        # Verify stats
        stats = temp_db.get_user_stats(username)
        assert stats['total_scrobbles'] == 3
        assert stats['unique_artists'] == 3
        assert stats['unique_tracks'] == 3
    
    def test_playlist_creation_workflow(self, temp_db):
        """Test complete playlist creation workflow"""
        username = "test_user"
        
        # Create playlist
        playlist_id = temp_db.create_playlist(
            username=username,
            name="My Test Playlist",
            description="A test playlist"
        )
        
        # Add tracks
        tracks = [
            {"artist": "Artist 1", "track": "Track 1", "album": "Album 1"},
            {"artist": "Artist 2", "track": "Track 2", "album": "Album 2"}
        ]
        temp_db.add_tracks_to_playlist(playlist_id, tracks)
        
        # Verify playlist exists
        playlists = temp_db.get_user_playlists(username)
        assert len(playlists) == 1
        assert playlists[0]['name'] == "My Test Playlist"
        
        # Verify tracks
        playlist_tracks = temp_db.get_playlist_tracks(playlist_id)
        assert len(playlist_tracks) == 2
        assert playlist_tracks[0]['artist'] == "Artist 1"
    
    def test_multi_user_workflow(self, temp_db):
        """Test workflow with multiple users"""
        # Create multiple users
        user1_id = temp_db.get_or_create_user("user1", "User One")
        user2_id = temp_db.get_or_create_user("user2", "User Two")
        
        assert user1_id != user2_id
        
        # Create playlists for each user
        playlist1_id = temp_db.create_playlist("user1", "User 1 Playlist")
        playlist2_id = temp_db.create_playlist("user2", "User 2 Playlist")
        
        # Verify playlists are separated by user
        user1_playlists = temp_db.get_user_playlists("user1")
        user2_playlists = temp_db.get_user_playlists("user2")
        
        assert len(user1_playlists) == 1
        assert len(user2_playlists) == 1
        assert user1_playlists[0]['name'] == "User 1 Playlist"
        assert user2_playlists[0]['name'] == "User 2 Playlist"

if __name__ == "__main__":
    pytest.main([__file__])