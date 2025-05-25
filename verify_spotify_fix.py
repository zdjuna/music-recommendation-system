#!/usr/bin/env python3
"""
Verify that RealMusicAnalyzer now works correctly
"""

import logging
logging.basicConfig(level=logging.DEBUG)

from real_music_analyzer import RealMusicAnalyzer

print("🔍 Testing RealMusicAnalyzer with environment variables...")

# Create analyzer (should auto-load from .env now)
analyzer = RealMusicAnalyzer()

# Test a track
print("\n🎵 Testing: The Killers - Bones")
features = analyzer.get_spotify_track_features("The Killers", "Bones")

if features:
    print("✅ Success! Found track features:")
    print(f"   Valence: {features.valence:.3f}")
    print(f"   Energy: {features.energy:.3f}")
    print(f"   Tempo: {features.tempo:.0f} BPM")
    
    mood = analyzer.analyze_mood_from_features(features)
    print(f"   Mood: {mood['primary_mood']} ({mood['mood_quadrant']})")
else:
    print("❌ Failed to get features")
    print("   Check if credentials are loaded properly") 