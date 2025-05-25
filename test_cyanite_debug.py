#!/usr/bin/env python3
"""Debug script to test Cyanite search functionality"""

import os
from dotenv import load_dotenv
from cyanite_mood_enricher import CyaniteMoodEnricher
import logging

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG)

# Load environment variables
load_dotenv()

# Get API key
api_key = os.getenv('CYANITE_API_KEY')
if not api_key:
    print("❌ No CYANITE_API_KEY found in .env file")
    exit(1)

print(f"✅ Using API key: {api_key[:20]}...")

# Create enricher
enricher = CyaniteMoodEnricher(api_key)

# Test with a popular track that should definitely exist
test_tracks = [
    ("The Beatles", "Hey Jude"),
    ("Queen", "Bohemian Rhapsody"),
    ("Lily Allen", "Not Big"),
    ("Interpol", "Evil")
]

print("\n🔍 Testing Cyanite search...\n")

for artist, title in test_tracks:
    print(f"\n{'='*60}")
    print(f"Searching for: {artist} - {title}")
    print(f"{'='*60}")
    
    result = enricher.search_and_analyze_track(title=title, artist_name=artist)
    
    if result:
        print(f"\n✅ FOUND: {result.get('title')}")
        print(f"   ID: {result.get('id')}")
        print(f"   Mood Tags: {result.get('mood_tags', [])[:5]}...")  # First 5 tags
        print(f"   Genre Tags: {result.get('genre_tags', [])[:5]}...")
        print(f"   Simplified Mood: {result.get('simplified_mood')}")
    else:
        print(f"\n❌ NOT FOUND")

print("\n\n📊 Final Statistics:")
for key, value in enricher.stats.items():
    print(f"   {key}: {value}") 