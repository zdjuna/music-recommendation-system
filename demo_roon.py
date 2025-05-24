#!/usr/bin/env python3
"""
Roon Integration Demo

Demonstrates the new Roon integration features in the Music Recommendation System v5.0
"""

import asyncio
import os
from pathlib import Path

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from music_rec.exporters import RoonClient, RoonIntegration
from music_rec.recommenders import RecommendationEngine, RecommendationRequest

async def demo_roon_integration():
    """Demo the Roon integration features"""
    
    print("🎵 Music Recommendation System v5.0 - Roon Integration Demo")
    print("=" * 60)
    print()
    
    # Configuration
    roon_host = os.getenv('ROON_CORE_HOST', '192.168.1.100')  # Default IP
    username = os.getenv('LASTFM_USERNAME', 'TestUser')
    
    print(f"🔧 Configuration:")
    print(f"   Roon Core Host: {roon_host}")
    print(f"   Last.fm User: {username}")
    print()
    
    # Test basic Roon connection
    print("1️⃣ Testing Roon Core Connection...")
    print("   (This would normally connect to your Roon Core)")
    print("   ✅ Connection test complete (simulated)")
    print()
    
    # Demo zone discovery
    print("2️⃣ Zone Discovery:")
    print("   🎵 Living Room (playing)")
    print("   ⏸️  Kitchen (paused)")
    print("   ⏹️  Bedroom (stopped)")
    print("   ⏹️  Office (stopped)")
    print()
    
    # Demo recommendation engine
    print("3️⃣ Generating Zone-Specific Recommendations...")
    try:
        engine = RecommendationEngine(username=username)
        
        # Create different requests for different zones
        requests = {
            'Living Room': RecommendationRequest(
                mood='calm',
                time_context='evening',
                playlist_length=15,
                discovery_level=0.2
            ),
            'Kitchen': RecommendationRequest(
                mood='energetic',
                energy_level='high',
                playlist_length=20,
                discovery_level=0.4
            ),
            'Office': RecommendationRequest(
                mood='focus',
                energy_level='medium',
                playlist_length=25,
                discovery_level=0.1
            )
        }
        
        for zone_name, request in requests.items():
            print(f"   🎯 {zone_name}: {request.mood or 'balanced'} mood, "
                  f"{request.playlist_length} tracks, "
                  f"{int(request.discovery_level * 100)}% discovery")
        
        print("   ✅ Recommendations generated")
        
    except Exception as e:
        print(f"   ⚠️  Demo mode: {e}")
    
    print()
    
    # Demo playlist creation
    print("4️⃣ Playlist Creation Features:")
    print("   📝 Context-aware recommendations based on:")
    print("      • Room type (kitchen → energetic, bedroom → calm)")
    print("      • Time of day (morning → high energy, night → low energy)")
    print("      • Current queue status (auto-refresh when low)")
    print("      • User listening patterns")
    print()
    
    # Demo auto-sync
    print("5️⃣ Auto-Sync Features:")
    print("   🔄 Monitors all zones in real-time")
    print("   🎵 Automatically creates new playlists when queue is low")
    print("   📊 Tracks playlist performance and user preferences")
    print("   ⚡ Updates recommendations based on listening context")
    print()
    
    # Demo CLI commands
    print("6️⃣ Available CLI Commands:")
    commands = [
        ("roon-connect", "Test connection to Roon Core"),
        ("roon-zones", "Show all zones and their status"),
        ("roon-playlist", "Create recommendation playlist in Roon"),
        ("roon-sync", "Start automatic playlist synchronization")
    ]
    
    for cmd, desc in commands:
        print(f"   python -m src.music_rec.cli {cmd}")
        print(f"   └─ {desc}")
        print()
    
    print("🎉 Roon Integration Demo Complete!")
    print()
    print("💡 To use with real Roon Core:")
    print("   1. Set ROON_CORE_HOST in config/config.env")
    print("   2. Make sure Roon Core is running")
    print("   3. Run: python -m src.music_rec.cli roon-connect")
    print("   4. Authorize in Roon Settings > Extensions")

if __name__ == '__main__':
    asyncio.run(demo_roon_integration()) 