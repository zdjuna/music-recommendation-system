#!/usr/bin/env python3
"""
API Rate Limit Tester

Tests current API status and rate limits before starting processing.
"""

import time
from real_music_analyzer_hybrid import RealMusicAnalyzer
from datetime import datetime

def test_api_rates():
    """Test current API rate limits"""
    print("🔍 TESTING API RATE LIMITS")
    print("=" * 50)
    
    analyzer = RealMusicAnalyzer()
    
    # Test tracks (popular ones likely to be found)
    test_tracks = [
        ("The Beatles", "Hey Jude"),
        ("Queen", "Bohemian Rhapsody"),
        ("Led Zeppelin", "Stairway to Heaven"),
        ("Pink Floyd", "Wish You Were Here"),
        ("The Rolling Stones", "(I Can't Get No) Satisfaction")
    ]
    
    successful_calls = 0
    start_time = time.time()
    
    for i, (artist, track) in enumerate(test_tracks, 1):
        print(f"\n🎵 Test {i}/5: {artist} - {track}")
        
        try:
            result = analyzer.analyze_track(artist, track)
            
            if result and result.get('spotify_found'):
                print(f"   ✅ Spotify: SUCCESS")
                successful_calls += 1
            else:
                print(f"   ❌ Spotify: FAILED")
            
            if result and result.get('lastfm_found'):
                print(f"   ✅ Last.fm: SUCCESS")
            else:
                print(f"   ❌ Last.fm: FAILED")
                
            # Small delay between tests
            time.sleep(0.5)
            
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
    
    elapsed = time.time() - start_time
    success_rate = (successful_calls / len(test_tracks)) * 100
    
    print(f"\n📊 API TEST RESULTS")
    print("=" * 30)
    print(f"Successful calls: {successful_calls}/{len(test_tracks)}")
    print(f"Success rate: {success_rate:.1f}%")
    print(f"Total time: {elapsed:.1f}s")
    print(f"Avg time per call: {elapsed/len(test_tracks):.1f}s")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS")
    print("=" * 30)
    
    if success_rate >= 80:
        print("✅ APIs working well - safe to proceed with processing")
        recommended_delay = 0.2
    elif success_rate >= 50:
        print("⚠️  APIs partially working - use longer delays")
        recommended_delay = 0.5
    else:
        print("❌ APIs struggling - wait before processing or use very long delays")
        recommended_delay = 1.0
    
    print(f"Recommended delay: {recommended_delay}s between calls")
    
    # Print cache stats
    cache_file = 'cache/real_music_analysis_cache.json'
    try:
        if hasattr(analyzer, 'cache') and analyzer.cache:
            cache_size = len(analyzer.cache)
            print(f"Cache entries available: {cache_size:,}")
        else:
            import json
            import os
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                    print(f"Cache entries available: {len(cache_data):,}")
    except Exception as e:
        print(f"Cache status unknown: {e}")
    
    return success_rate >= 50, recommended_delay

if __name__ == "__main__":
    test_api_rates()
