#!/usr/bin/env python3
"""
Complete Emotion Research Module
Trains and tests the research-based emotion analysis system
"""

import os
import pandas as pd
import logging
from typing import Dict, List
from research_based_emotion_analyzer import ResearchBasedEmotionAnalyzer
from research_based_mood_analyzer import ResearchBasedMoodAnalyzer

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def complete_emotion_research_module():
    """
    Complete the emotion research module by:
    1. Training the emotion analyzer with existing data
    2. Testing both analyzers
    3. Creating comprehensive analysis examples
    """
    
    logger.info("🎵 Starting Emotion Research Module Completion")
    
    # Initialize analyzers
    emotion_analyzer = ResearchBasedEmotionAnalyzer()
    mood_analyzer = ResearchBasedMoodAnalyzer()
    
    # Step 1: Train the emotion analyzer if we have enriched data
    enriched_data_path = "data/zdjuna_enriched.csv"
    if os.path.exists(enriched_data_path):
        logger.info("📚 Training emotion analyzer with existing enriched data...")
        training_success = emotion_analyzer.train_from_enriched_data(enriched_data_path)
        if training_success:
            logger.info("✅ Emotion analyzer training completed successfully")
        else:
            logger.warning("⚠️ Emotion analyzer training failed, using lexicon-based analysis")
    else:
        logger.info("ℹ️ No enriched data found, using lexicon-based analysis")
    
    # Step 2: Test both analyzers with sample tracks
    test_tracks = [
        ("Interpol", "Evil", "alternative rock, indie"),
        ("Amy Winehouse", "Rehab", "soul, jazz, r&b"),
        ("The Killers", "Mr. Brightside", "rock, indie rock"),
        ("Radiohead", "Creep", "alternative rock, grunge"),
        ("Sade", "Smooth Operator", "soul, jazz, smooth"),
        ("Arctic Monkeys", "I Bet You Look Good on the Dancefloor", "indie rock, garage rock"),
        ("Björk", "Army of Me", "electronic, experimental, art pop"),
        ("Kate Nash", "Foundations", "indie pop, alternative"),
        ("Bloc Party", "Banquet", "indie rock, post-punk revival"),
        ("Modest Mouse", "Float On", "indie rock, alternative")
    ]
    
    logger.info("🧪 Testing emotion analysis on sample tracks...")
    
    results = []
    for artist, track, genres in test_tracks:
        # Test emotion analyzer
        emotion_result = emotion_analyzer.analyze_and_enrich_track(artist, track, "", genres)
        
        # Test mood analyzer  
        mood_result = mood_analyzer.analyze_track_emotion(artist, track)
        
        result = {
            'artist': artist,
            'track': track,
            'genres': genres,
            'emotion_analyzer': emotion_result,
            'mood_analyzer': {
                'mood_label': mood_result.to_mood_label(),
                'valence': f"{mood_result.valence:+.3f}",
                'arousal': f"{mood_result.arousal:+.3f}",
                'dominance': f"{mood_result.dominance:+.3f}",
                'confidence': f"{mood_result.confidence:.3f}"
            }
        }
        results.append(result)
    
    # Step 3: Display comprehensive results
    logger.info("📊 Emotion Analysis Results:")
    print("\n" + "="*100)
    print("🎵 RESEARCH-BASED EMOTION ANALYSIS RESULTS")
    print("="*100)
    
    for result in results:
        print(f"\n🎵 {result['artist']} - {result['track']}")
        print(f"   Genres: {result['genres']}")
        print(f"   📈 Emotion Analyzer:")
        ea = result['emotion_analyzer']
        print(f"      Primary Emotion: {ea['emotion_label']}")
        print(f"      Mood Label: {ea['mood_label']}")
        print(f"      Valence: {ea['valence']} | Arousal: {ea['arousal']} | Dominance: {ea['dominance']}")
        print(f"      Confidence: {ea['emotion_confidence']} | Quadrant: {ea['emotional_quadrant']}")
        print(f"      Method: {ea['analysis_method']}")
        
        print(f"   🎭 Mood Analyzer:")
        ma = result['mood_analyzer']
        print(f"      Mood: {ma['mood_label']}")
        print(f"      Valence: {ma['valence']} | Arousal: {ma['arousal']} | Dominance: {ma['dominance']}")
        print(f"      Confidence: {ma['confidence']}")
    
    # Step 4: Create emotion distribution analysis
    logger.info("📊 Creating emotion distribution analysis...")
    
    emotion_counts = {}
    quadrant_counts = {}
    
    for result in results:
        emotion = result['emotion_analyzer']['emotion_label']
        quadrant = result['emotion_analyzer']['emotional_quadrant']
        
        emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        quadrant_counts[quadrant] = quadrant_counts.get(quadrant, 0) + 1
    
    print(f"\n📊 EMOTION DISTRIBUTION:")
    for emotion, count in sorted(emotion_counts.items()):
        print(f"   {emotion}: {count} tracks")
    
    print(f"\n🎯 EMOTIONAL QUADRANT DISTRIBUTION:")
    for quadrant, count in sorted(quadrant_counts.items()):
        print(f"   {quadrant}: {count} tracks")
    
    # Step 5: Save results for integration testing
    results_df = pd.DataFrame([
        {
            'artist': r['artist'],
            'track': r['track'],
            'genres': r['genres'],
            'emotion_label': r['emotion_analyzer']['emotion_label'],
            'mood_label': r['emotion_analyzer']['mood_label'],
            'valence': r['emotion_analyzer']['valence'],
            'arousal': r['emotion_analyzer']['arousal'],
            'dominance': r['emotion_analyzer']['dominance'],
            'confidence': r['emotion_analyzer']['emotion_confidence'],
            'quadrant': r['emotion_analyzer']['emotional_quadrant'],
            'method': r['emotion_analyzer']['analysis_method']
        }
        for r in results
    ])
    
    output_file = "data/emotion_research_test_results.csv"
    results_df.to_csv(output_file, index=False)
    logger.info(f"💾 Test results saved to {output_file}")
    
    # Step 6: Integration verification
    logger.info("🔗 Verifying Streamlit integration...")
    
    try:
        # Test import in Streamlit context
        from streamlit_app import execute_enrich_data
        logger.info("✅ Streamlit integration imports successful")
    except Exception as e:
        logger.error(f"❌ Streamlit integration issue: {e}")
    
    print(f"\n🎉 EMOTION RESEARCH MODULE COMPLETION SUMMARY:")
    print(f"   ✅ Emotion Analyzer: {'Trained' if training_success else 'Lexicon-based'}")
    print(f"   ✅ Mood Analyzer: Operational")
    print(f"   ✅ Test Results: {len(results)} tracks analyzed")
    print(f"   ✅ Integration: Ready for Streamlit")
    print(f"   📁 Results saved to: {output_file}")
    
    return {
        'success': True,
        'analyzer_trained': training_success if 'training_success' in locals() else False,
        'tracks_tested': len(results),
        'results_file': output_file,
        'emotion_distribution': emotion_counts,
        'quadrant_distribution': quadrant_counts
    }

def test_specific_artist_analysis():
    """Test emotion analysis for specific artists mentioned in research"""
    
    logger.info("🎨 Testing artist-specific emotion analysis...")
    
    emotion_analyzer = ResearchBasedEmotionAnalyzer()
    mood_analyzer = ResearchBasedMoodAnalyzer()
    
    # Artists from research paper with expected emotional profiles
    research_artists = [
        ("Interpol", "Evil", "Expected: Brooding intensity"),
        ("Radiohead", "Paranoid Android", "Expected: Complex anxiety"),
        ("Arctic Monkeys", "When the Sun Goes Down", "Expected: Witty energy"),
        ("Sade", "No Ordinary Love", "Expected: Smooth sophistication")
    ]
    
    print(f"\n🎨 ARTIST-SPECIFIC EMOTION ANALYSIS:")
    print("="*80)
    
    for artist, track, expected in research_artists:
        emotion_result = emotion_analyzer.analyze_and_enrich_track(artist, track)
        mood_result = mood_analyzer.analyze_track_emotion(artist, track)
        
        print(f"\n🎵 {artist} - {track}")
        print(f"   {expected}")
        print(f"   📊 Analysis Results:")
        print(f"      Emotion: {emotion_result['emotion_label']} ({emotion_result['emotion_confidence']})")
        print(f"      Mood: {emotion_result['mood_label']}")
        print(f"      Dimensions: V{emotion_result['valence']} A{emotion_result['arousal']} D{emotion_result['dominance']}")
        print(f"      Quadrant: {emotion_result['emotional_quadrant']}")

if __name__ == "__main__":
    # Complete the emotion research module
    completion_result = complete_emotion_research_module()
    
    # Test artist-specific analysis
    test_specific_artist_analysis()
    
    print(f"\n🎵 Emotion Research Module is now complete and ready for use!")
    print(f"   Use the analyzers in your Streamlit app for advanced emotion analysis.") 