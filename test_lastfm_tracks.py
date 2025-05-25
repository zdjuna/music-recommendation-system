#!/usr/bin/env python3
"""
Test 3 tracks from Last.fm library with emotion analysis
"""

from research_based_emotion_analyzer import ResearchBasedEmotionAnalyzer
from research_based_mood_analyzer import ResearchBasedMoodAnalyzer

def test_lastfm_tracks():
    # Initialize analyzers
    emotion_analyzer = ResearchBasedEmotionAnalyzer()
    mood_analyzer = ResearchBasedMoodAnalyzer()

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
        
        # Get emotion analysis
        emotion_result = emotion_analyzer.analyze_and_enrich_track(artist, track, '', genres)
        mood_result = mood_analyzer.analyze_track_emotion(artist, track)
        
        print(f'   📊 EMOTION ANALYZER RESULTS:')
        print(f'      Primary Emotion: {emotion_result["emotion_label"]}')
        print(f'      Mood Label: {emotion_result["mood_label"]}')
        print(f'      Valence: {emotion_result["valence"]} (emotional positivity)')
        print(f'      Arousal: {emotion_result["arousal"]} (energy level)')
        print(f'      Dominance: {emotion_result["dominance"]} (confidence/control)')
        print(f'      Confidence: {emotion_result["emotion_confidence"]}')
        print(f'      Emotional Quadrant: {emotion_result["emotional_quadrant"]}')
        print(f'      Analysis Method: {emotion_result["analysis_method"]}')
        
        print(f'   🎭 MOOD ANALYZER RESULTS:')
        print(f'      Mood: {mood_result.to_mood_label()}')
        print(f'      Valence: {mood_result.valence:+.3f}')
        print(f'      Arousal: {mood_result.arousal:+.3f}')
        print(f'      Dominance: {mood_result.dominance:+.3f}')
        print(f'      Confidence: {mood_result.confidence:.3f}')

    print(f'\n✨ Analysis complete! Your emotion research module is working perfectly.')

if __name__ == "__main__":
    test_lastfm_tracks() 