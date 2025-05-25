#!/usr/bin/env python3
"""
Check current status of Spotify integration
"""

import os
from pathlib import Path
import json

print("🎵 Spotify Integration Status Check")
print("="*50)

# Check for .env file
env_exists = Path('.env').exists()
print(f"\n📄 .env file exists: {'✅' if env_exists else '❌'}")

if env_exists:
    # Check for Spotify credentials in environment
    has_client_id = bool(os.getenv('SPOTIFY_CLIENT_ID'))
    has_client_secret = bool(os.getenv('SPOTIFY_CLIENT_SECRET'))
    print(f"🔑 SPOTIFY_CLIENT_ID: {'✅ Set' if has_client_id else '❌ Not set'}")
    print(f"🔑 SPOTIFY_CLIENT_SECRET: {'✅ Set' if has_client_secret else '❌ Not set'}")
else:
    print("   → Run: python3 setup_spotify.py")

# Check for cache
cache_file = Path('cache/spotify_features_cache.json')
print(f"\n💾 Cache file exists: {'✅' if cache_file.exists() else '❌'}")

if cache_file.exists():
    with open(cache_file, 'r') as f:
        cache = json.load(f)
    print(f"   → Cached tracks: {len(cache)}")

# Check for enriched data
enriched_files = list(Path('data').glob('*spotify_enriched*.csv'))
print(f"\n📊 Spotify enriched files: {len(enriched_files)}")

for file in enriched_files:
    size_mb = file.stat().st_size / (1024 * 1024)
    print(f"   → {file.name} ({size_mb:.1f} MB)")

# Check for scrobbles data
scrobbles_file = Path('data/zdjuna_scrobbles.csv')
print(f"\n🎧 Scrobbles data exists: {'✅' if scrobbles_file.exists() else '❌'}")

if scrobbles_file.exists():
    import pandas as pd
    df = pd.read_csv(scrobbles_file)
    unique_tracks = len(df[['artist', 'track']].drop_duplicates())
    print(f"   → Total scrobbles: {len(df):,}")
    print(f"   → Unique tracks: {unique_tracks:,}")

print("\n📋 Next Steps:")
if not env_exists:
    print("1. Complete the Spotify setup that's running")
    print("2. Run: python3 enrich_with_spotify.py")
    print("3. Run: python3 integrate_real_analysis.py")
else:
    if len(enriched_files) == 0:
        print("1. Run: python3 enrich_with_spotify.py")
        print("2. Run: python3 integrate_real_analysis.py")
    else:
        print("1. Run: python3 integrate_real_analysis.py")
        print("2. Launch Streamlit and enjoy real music analysis!")

print("\n✨ Remember: Real music analysis uses audio features, not text!") 