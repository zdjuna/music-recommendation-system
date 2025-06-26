# 🔌 API Reference Guide

## Overview

This document provides comprehensive documentation for all APIs, modules, and functions in the Music Recommendation System.

## 📊 Database API

### DatabaseManager Class

```python
from streamlit_app.models.database import DatabaseManager, db

# Initialize database
db = DatabaseManager("data/music_rec.db")
```

#### User Management

```python
# Create or get user
user_id = db.get_or_create_user(username: str, display_name: str = None) -> int

# Get user statistics
stats = db.get_user_stats(username: str) -> Dict[str, Any]
# Returns: {
#     'total_scrobbles': int,
#     'unique_artists': int,
#     'unique_tracks': int,
#     'playlists_count': int
# }
```

#### Track Management

```python
# Create or get track
track_id = db.get_or_create_track(artist: str, track: str, album: str = None) -> int

# Import CSV data
db.import_csv_data(username: str, csv_path: Path)
```

#### Playlist Management

```python
# Create playlist
playlist_id = db.create_playlist(
    username: str, 
    name: str, 
    description: str = None,
    playlist_type: str = 'custom'
) -> int

# Add tracks to playlist
db.add_tracks_to_playlist(playlist_id: int, tracks: List[Dict[str, str]])

# Get user playlists
playlists = db.get_user_playlists(username: str) -> List[Dict[str, Any]]

# Get playlist tracks
tracks = db.get_playlist_tracks(playlist_id: int) -> List[Dict[str, Any]]
```

## ⚡ Async Processing API

### AsyncProcessor Class

```python
from src.music_rec.core.async_processor import AsyncProcessor, process_music_data_async

# High-level async processing
results = await process_music_data_async(
    tracks: List[Dict[str, str]],
    enrichment_func: Callable,
    max_concurrent: int = 10,
    progress_callback: Optional[Callable] = None
) -> List[Dict[str, Any]]
```

#### Advanced Usage

```python
async with AsyncProcessor(max_concurrent=10, timeout=30.0) as processor:
    # Parallel track processing
    results = await processor.process_tracks_parallel(
        tracks=tracks,
        processor_func=enrichment_function,
        progress_callback=progress_callback
    )
    
    # Batch API requests
    api_results = await processor.batch_api_requests(
        requests=request_list,
        request_func=api_function
    )
    
    # Rate-limited processing
    limited_results = await processor.process_with_rate_limiting(
        items=items,
        processor_func=processor,
        rate_limit=1.0  # 1 request per second
    )
```

#### Performance Monitoring

```python
# Get performance statistics
stats = processor.get_performance_stats()
# Returns: {
#     'total_tasks': int,
#     'completed_tasks': int,
#     'failed_tasks': int,
#     'success_rate': float,
#     'avg_processing_time': float,
#     'max_concurrent': int
# }
```

## 🏥 Health Monitoring API

### HealthMonitor Class

```python
from src.music_rec.monitoring.health_monitor import HealthMonitor, health_monitor

# Register a service
health_monitor.register_service(
    name: str,
    health_check_func: Callable,
    circuit_breaker_config: Optional[Dict] = None
)

# Check service health
health_check = await health_monitor.check_service_health(service_name: str)

# Check all services
all_health = await health_monitor.check_all_services() -> Dict[str, HealthCheck]

# Get system health report
health_report = health_monitor.get_system_health() -> Dict[str, Any]
```

#### Circuit Breaker Usage

```python
# Make protected API call
result = await health_monitor.call_with_circuit_breaker(
    service_name="spotify",
    func=spotify_api_call,
    *args,
    **kwargs
)
```

#### Continuous Monitoring

```python
# Start monitoring (runs in background)
await health_monitor.start_monitoring()

# Stop monitoring
health_monitor.stop_monitoring()
```

## 🎨 Streamlit Components API

### Configuration Management

```python
from streamlit_app.utils.config import config

# API status
api_status = config.api_status  # Dict[str, bool]

# API keys
lastfm_key = config.lastfm_api_key
cyanite_key = config.cyanite_api_key
spotify_id = config.spotify_client_id

# System readiness
is_ready = config.is_production_ready  # bool
```

### Status Dashboard

```python
from streamlit_app.components.status_dashboard import (
    render_system_status,
    render_quick_actions,
    render_welcome_message
)

# Render status components
render_system_status()      # System status grid
render_quick_actions()      # Test buttons
render_welcome_message()    # Welcome for new users
```

### Charts and Visualization

```python
from streamlit_app.components.charts import (
    create_listening_timeline,
    create_top_artists_chart,
    create_mood_distribution,
    render_charts_grid
)

# Create individual charts
timeline_fig = create_listening_timeline(df)
artists_fig = create_top_artists_chart(df, top_n=15)
mood_fig = create_mood_distribution(enriched_df)

# Render complete chart grid
render_charts_grid(df, enriched_df)
```

## 🎯 Core Music Analysis API

### Music Analyzer

```python
from scripts.analyzers.music_analyzer import RealMusicAnalyzer

analyzer = RealMusicAnalyzer()

# Analyze tracks
results = analyzer.analyze_tracks(tracks: List[Dict])

# Get analysis statistics
stats = analyzer.get_stats()
```

### Mood Analysis

```python
from scripts.analyzers.mood_analyzer import AdvancedMoodAnalyzer

mood_analyzer = AdvancedMoodAnalyzer()

# Analyze track mood
mood_result = mood_analyzer.analyze_track_advanced(
    artist: str,
    track: str,
    basic_tags: List[str] = None
) -> Dict[str, Any]
```

## 🎵 Playlist Generation API

### Playlist Manager

```python
from streamlit_app.pages.playlist_manager import (
    generate_playlist,
    create_m3u_playlist
)

# Generate recommendation playlist
generate_playlist(
    username: str,
    playlist_type: str,  # "similar_recent", "discovery", "trending"
    settings: Dict[str, Any]
)

# Create M3U export
m3u_content = create_m3u_playlist(tracks: List[Dict[str, Any]]) -> str
```

## 🔧 Utility Functions

### Data Loading

```python
from streamlit_app.pages.dashboard import load_user_data

# Load user data with caching
user_data = load_user_data(username: str)
# Returns: {
#     'source': str,  # 'database' or 'csv'
#     'has_scrobbles': bool,
#     'has_enriched': bool,
#     'scrobbles': Optional[pd.DataFrame],
#     'enriched': Optional[pd.DataFrame],
#     'stats': Optional[Dict]
# }
```

### Configuration

```python
from streamlit_app.utils.config import Config

config = Config()

# Get configuration value
value = config.get_config_value(key: str, default: str = "") -> str

# Check API availability
api_status = config.api_status -> Dict[str, bool]
```

## 📝 Data Models

### HealthCheck Model

```python
@dataclass
class HealthCheck:
    timestamp: float
    success: bool
    response_time: float
    error: Optional[str] = None
```

### ServiceHealth Model

```python
@dataclass
class ServiceHealth:
    name: str
    status: ServiceStatus
    last_check: Optional[float]
    response_time: float
    success_rate: float
    error_count: int
    checks: deque
```

### Task Model

```python
@dataclass
class Task:
    id: str
    func: Callable
    args: tuple
    kwargs: dict
    status: TaskStatus
    result: Any
    error: Optional[Exception]
    created_at: float
    started_at: Optional[float]
    completed_at: Optional[float]
```

## 🔄 Async/Await Patterns

### Common Async Patterns

```python
# Pattern 1: Async context manager
async with AsyncProcessor() as processor:
    results = await processor.process_tracks_parallel(tracks, func)

# Pattern 2: Async function calls
results = await process_music_data_async(tracks, enrichment_func)

# Pattern 3: Health monitoring
health_status = await health_monitor.check_all_services()

# Pattern 4: Circuit breaker protection
result = await health_monitor.call_with_circuit_breaker("api", func, args)
```

### Error Handling

```python
try:
    results = await async_function()
except asyncio.TimeoutError:
    # Handle timeout
    pass
except aiohttp.ClientError:
    # Handle network errors
    pass
except Exception as e:
    # Handle general errors
    logger.error(f"Unexpected error: {e}")
```

## 📊 Response Formats

### Standard API Response

```json
{
    "success": true,
    "data": {...},
    "timestamp": 1640995200,
    "processing_time": 1.23
}
```

### Error Response

```json
{
    "success": false,
    "error": "Error description",
    "error_code": "API_ERROR",
    "timestamp": 1640995200
}
```

### Health Check Response

```json
{
    "timestamp": 1640995200,
    "overall_status": "healthy",
    "services": {
        "lastfm": {
            "status": "healthy",
            "success_rate": 0.95,
            "response_time": 0.45,
            "circuit_breaker_state": "closed"
        }
    }
}
```

## 🧪 Testing API

### Test Utilities

```python
# Import test fixtures
from tests.conftest import sample_scrobbles_data, mock_env_vars

# Database testing
from tests.unit.test_database import TestDatabaseManager

# Configuration testing
from tests.unit.test_config import TestConfig

# End-to-end testing
from tests.e2e.test_complete_workflow import TestCompleteWorkflow
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test categories
pytest tests/unit/          # Unit tests
pytest tests/integration/   # Integration tests
pytest tests/e2e/          # End-to-end tests

# Run with coverage
pytest tests/ --cov=src --cov=streamlit_app

# Run specific test
pytest tests/unit/test_database.py::TestDatabaseManager::test_user_creation
```

## 📈 Performance Optimization

### Caching Best Practices

```python
# Streamlit caching
@st.cache_data(ttl=300)  # 5 minutes
def expensive_computation():
    pass

@st.cache_data(ttl=1800)  # 30 minutes
def chart_generation():
    pass

# Clear cache when needed
st.cache_data.clear()
```

### Async Best Practices

```python
# Use semaphores for concurrency control
async with asyncio.Semaphore(10):
    result = await api_call()

# Batch operations for efficiency
results = await asyncio.gather(*[
    process_track(track) for track in tracks
])

# Use connection pooling
connector = aiohttp.TCPConnector(limit=100)
session = aiohttp.ClientSession(connector=connector)
```

This API reference provides comprehensive documentation for all major components of the Music Recommendation System, enabling developers to effectively use and extend the system.