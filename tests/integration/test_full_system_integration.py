"""
Full system integration tests
"""

import pytest
import tempfile
import pandas as pd
from pathlib import Path
import sys
import asyncio

# Add src to path
sys.path.append(str(Path(__file__).parent.parent.parent))

class TestFullSystemIntegration:
    """Test complete system integration"""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        from streamlit_app.models.database import DatabaseManager
        db = DatabaseManager(db_path)
        yield db
        
        # Cleanup
        Path(db_path).unlink(missing_ok=True)
    
    @pytest.fixture
    def sample_csv(self):
        """Create sample CSV data"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("artist,track,album,timestamp\n")
            f.write("The Beatles,Hey Jude,The Beatles 1967-1970,2023-01-01 12:00:00\n")
            f.write("Queen,Bohemian Rhapsody,A Night at the Opera,2023-01-01 13:00:00\n")
            f.write("Led Zeppelin,Stairway to Heaven,Led Zeppelin IV,2023-01-01 14:00:00\n")
            csv_path = f.name
        
        yield Path(csv_path)
        Path(csv_path).unlink(missing_ok=True)
    
    def test_complete_data_pipeline(self, temp_db, sample_csv):
        """Test complete data pipeline from CSV to database to analysis"""
        username = "integration_test_user"
        
        # Step 1: Import CSV data
        temp_db.import_csv_data(username, sample_csv)
        
        # Step 2: Verify data import
        stats = temp_db.get_user_stats(username)
        assert stats['total_scrobbles'] == 3
        assert stats['unique_artists'] == 3
        assert stats['unique_tracks'] == 3
        
        # Step 3: Create and populate playlist
        playlist_id = temp_db.create_playlist(username, "Integration Test Playlist")
        tracks = [
            {"artist": "Test Artist 1", "track": "Test Track 1", "album": "Test Album 1"},
            {"artist": "Test Artist 2", "track": "Test Track 2", "album": "Test Album 2"}
        ]
        temp_db.add_tracks_to_playlist(playlist_id, tracks)
        
        # Step 4: Verify playlist creation
        playlist_tracks = temp_db.get_playlist_tracks(playlist_id)
        assert len(playlist_tracks) == 2
        assert playlist_tracks[0]['artist'] == "Test Artist 1"
        
        # Step 5: Verify updated stats
        final_stats = temp_db.get_user_stats(username)
        assert final_stats['playlists_count'] == 1
    
    def test_modular_component_integration(self):
        """Test integration between modular components"""
        
        # Test configuration system
        from streamlit_app.utils.config import Config
        config = Config()
        assert hasattr(config, 'api_status')
        assert isinstance(config.api_status, dict)
        
        # Test chart creation with sample data
        from streamlit_app.components.charts import create_listening_timeline, create_top_artists_chart
        import pandas as pd
        from datetime import datetime
        
        sample_data = pd.DataFrame({
            'artist': ['Artist A', 'Artist B', 'Artist A', 'Artist C'],
            'track': ['Track 1', 'Track 2', 'Track 3', 'Track 4'],
            'timestamp': [datetime.now() for _ in range(4)]
        })
        
        timeline_fig = create_listening_timeline(sample_data)
        artists_fig = create_top_artists_chart(sample_data)
        
        assert timeline_fig is not None
        assert artists_fig is not None
    
    @pytest.mark.asyncio
    async def test_async_processing_integration(self):
        """Test async processing system integration"""
        
        from src.music_rec.core.async_processor import AsyncProcessor
        
        def sample_processor(item):
            return {'processed': item, 'status': 'success'}
        
        test_items = [{'id': i} for i in range(5)]
        
        async with AsyncProcessor(max_concurrent=3) as processor:
            results = await processor.process_tracks_parallel(test_items, sample_processor)
            
            assert len(results) == 5
            assert all(result['status'] == 'success' for result in results)
            
            # Test performance stats
            stats = processor.get_performance_stats()
            assert 'total_tasks' in stats
            assert 'max_concurrent' in stats
    
    def test_health_monitoring_integration(self):
        """Test health monitoring system integration"""
        
        from src.music_rec.monitoring.health_monitor import HealthMonitor
        
        monitor = HealthMonitor()
        
        # Test service registration
        def dummy_health_check():
            return True
        
        monitor.register_service("test_service", dummy_health_check)
        assert "test_service" in monitor.services
        assert "test_service" in monitor.circuit_breakers
    
    def test_app_initialization_integration(self):
        """Test complete app initialization"""
        
        # Test main app import
        import app
        assert hasattr(app, 'main')
        
        # Test CLI import
        import run
        assert hasattr(run, 'main')
        
        # Test start script import
        import start
        assert hasattr(start, 'main')
    
    def test_database_utils_integration(self, temp_db):
        """Test database utilities integration"""
        
        from streamlit_app.models.database_utils import (
            validate_database_connection, 
            get_database_info,
            repair_database
        )
        
        # Test validation
        assert validate_database_connection(str(temp_db.db_path))
        
        # Test database info
        info = get_database_info(str(temp_db.db_path))
        assert 'tables' in info
        assert 'table_counts' in info
        assert len(info['tables']) > 0
        
        # Test repair functionality
        assert repair_database(str(temp_db.db_path))
    
    def test_error_handling_integration(self, temp_db):
        """Test error handling across the system"""
        
        # Test database error handling
        try:
            # This should work fine
            temp_db.get_user_stats("error_test_user")
        except Exception as e:
            pytest.fail(f"Basic database operation failed: {e}")
        
        # Test configuration error handling
        from streamlit_app.utils.config import Config
        config = Config()
        
        # Should handle missing API keys gracefully
        api_status = config.api_status
        assert isinstance(api_status, dict)
        
        # Test chart error handling with empty data
        from streamlit_app.components.charts import create_listening_timeline
        
        empty_df = pd.DataFrame()
        fig = create_listening_timeline(empty_df)
        assert fig is not None  # Should return empty figure, not crash

if __name__ == "__main__":
    pytest.main([__file__])