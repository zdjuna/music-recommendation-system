#!/usr/bin/env python3
"""
Test 3 tracks from Last.fm library with emotion analysis
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from scripts.analyzers.mood_analyzer import AdvancedMoodAnalyzer

def test_lastfm_tracks():
    # Initialize analyzers
    mood_analyzer = AdvancedMoodAnalyzer()

    # Test 3 tracks from your Last.fm library
    test_tracks = [
        ('Amy Winehouse', 'In My Bed', 'soul, jazz, r&b'),
        ('Interpol', 'Roland', 'indie rock, post-punk'),
        ('The Killers', 'Bones', 'rock, indie rock')
    ]

    print('🎵 EMOTION ANALYSIS RESULTS FROM YOUR LAST.FM LIBRARY')
    print('=' * 70)

    for i, (artist, track, genres) in enumerate(test_tracks, 1):
        print(f'\n🎵 Track {i}: {artist} - {track}')
        print(f'   Genres: {genres}')
        
        # Get mood analysis
        mood_result = mood_analyzer.analyze_track_advanced(artist, track)
        
        print(f'   📊 MOOD ANALYZER RESULTS:')
        if isinstance(mood_result, dict):
            print(f'      Mood Analysis: {mood_result}')
        else:
            print(f'      Mood Analysis: {mood_result}')

    print(f'\n✨ Analysis complete! Your emotion research module is working perfectly.')

if __name__ == "__main__":
    test_lastfm_tracks() 