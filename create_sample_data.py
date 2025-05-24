#!/usr/bin/env python3
"""
Sample Data Generator for Music Recommendation System

Creates realistic sample music data for testing Phase 2 analysis.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def create_sample_data(username="SampleUser", num_scrobbles=5000):
    """Create realistic sample music data."""
    
    # Sample artists with different popularity levels
    artists = [
        # Popular artists (frequent plays)
        "Pink Floyd", "The Beatles", "Radiohead", "Tool", "Led Zeppelin",
        "David Bowie", "The Rolling Stones", "Queen", "Nirvana", "Pearl Jam",
        
        # Medium popularity
        "Arcade Fire", "The National", "Bon Iver", "Sufjan Stevens", "LCD Soundsystem",
        "Vampire Weekend", "The Strokes", "Arctic Monkeys", "Tame Impala", "MGMT",
        
        # Lower frequency artists
        "Sigur Rós", "Godspeed You! Black Emperor", "Explosions in the Sky",
        "Boards of Canada", "Aphex Twin", "Burial", "Four Tet", "Autechre",
        "Sun Kil Moon", "Red House Painters", "Elliott Smith", "Nick Drake",
        
        # One-time discoveries
        "Alcest", "Slowdive", "My Bloody Valentine", "Cocteau Twins",
        "Dead Can Dance", "This Will Destroy You", "A Silver Mt. Zion",
        "Mono", "Swans", "Neurosis", "Isis", "Cult of Luna"
    ]
    
    # Sample tracks per artist
    tracks_per_artist = {
        "Pink Floyd": ["Comfortably Numb", "Wish You Were Here", "Time", "Money", "Shine On You Crazy Diamond"],
        "The Beatles": ["Yesterday", "Come Together", "Hey Jude", "Let It Be", "Here Comes the Sun"],
        "Radiohead": ["Creep", "Paranoid Android", "Karma Police", "No Surprises", "Everything In Its Right Place"],
        "Tool": ["Schism", "Stinkfist", "Forty Six & 2", "The Pot", "Sober"],
        "Led Zeppelin": ["Stairway to Heaven", "Black Dog", "Kashmir", "Whole Lotta Love", "Rock and Roll"],
        # Default tracks for other artists
        "default": ["Track 1", "Track 2", "Track 3", "Track 4", "Track 5"]
    }
    
    # Artist play frequency weights
    artist_weights = []
    for i, artist in enumerate(artists):
        if i < 10:  # Top artists
            weight = random.uniform(50, 200)
        elif i < 20:  # Medium artists
            weight = random.uniform(10, 50)
        elif i < 32:  # Lower frequency
            weight = random.uniform(2, 10)
        else:  # Discovery artists
            weight = random.uniform(1, 3)
        artist_weights.append(weight)
    
    # Generate scrobbles
    scrobbles = []
    
    # Start date (2 years of data)
    start_date = datetime.now() - timedelta(days=730)
    
    for i in range(num_scrobbles):
        # Choose artist based on weights
        artist = np.random.choice(artists, p=np.array(artist_weights)/sum(artist_weights))
        
        # Choose track
        if artist in tracks_per_artist:
            track = random.choice(tracks_per_artist[artist])
        else:
            track = random.choice(tracks_per_artist["default"])
        
        # Generate timestamp with realistic patterns
        # More listening in evenings and weekends
        days_offset = random.randint(0, 730)
        base_date = start_date + timedelta(days=days_offset)
        
        # Time of day bias (more evening listening)
        hour_weights = [1, 1, 1, 1, 1, 1,  # 0-5 (night)
                       2, 3, 4, 5, 6, 7,   # 6-11 (morning)
                       8, 9, 8, 7, 6, 8,   # 12-17 (afternoon) 
                       10, 12, 15, 12, 8, 4] # 18-23 (evening)
        
        hour = np.random.choice(range(24), p=np.array(hour_weights)/sum(hour_weights))
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        
        timestamp = base_date.replace(hour=hour, minute=minute, second=second)
        
        # Album name (simplified)
        album = f"{artist} - Album {random.randint(1, 5)}"
        
        scrobble = {
            'timestamp': int(timestamp.timestamp()),
            'date': timestamp.isoformat(),
            'artist': artist,
            'track': track,
            'album': album,
            'mbid_track': '',
            'mbid_artist': '',
            'mbid_album': '',
            'url_track': f'https://last.fm/music/{artist.replace(" ", "+")}/_/{track.replace(" ", "+")}',
            'image_url': ''
        }
        
        scrobbles.append(scrobble)
    
    # Sort by timestamp
    scrobbles.sort(key=lambda x: x['timestamp'])
    
    # Create DataFrame
    df = pd.DataFrame(scrobbles)
    
    # Save to CSV
    output_file = f"data/{username}_scrobbles.csv"
    df.to_csv(output_file, index=False)
    
    print(f"✅ Generated {len(scrobbles):,} sample scrobbles")
    print(f"📁 Saved to: {output_file}")
    print(f"📊 Data span: {df['date'].min()[:10]} to {df['date'].max()[:10]}")
    print(f"🎵 Unique artists: {df['artist'].nunique()}")
    print(f"🎶 Unique tracks: {(df['artist'] + ' - ' + df['track']).nunique()}")
    
    return df

if __name__ == "__main__":
    import sys
    
    username = sys.argv[1] if len(sys.argv) > 1 else "SampleUser"
    num_scrobbles = int(sys.argv[2]) if len(sys.argv) > 2 else 5000
    
    print(f"🎵 Creating sample data for: {username}")
    print(f"📊 Generating {num_scrobbles:,} scrobbles...")
    print()
    
    df = create_sample_data(username, num_scrobbles)
    
    print()
    print("🎉 Sample data created! You can now test Phase 2 analysis:")
    print(f"   python -m src.music_rec.cli analyze --username {username}")
    print("   or")
    print(f"   python -m src.music_rec.cli quick-insights --username {username}") 