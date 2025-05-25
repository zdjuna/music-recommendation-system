#!/usr/bin/env python3
"""
Enrich music library with MusicBrainz data
"""

import pandas as pd
import argparse
import logging
from pathlib import Path
from musicbrainz_enricher import MusicBrainzEnricher

def main():
    parser = argparse.ArgumentParser(description='Enrich music library with MusicBrainz data')
    parser.add_argument('--username', required=True, help='Username for data files')
    parser.add_argument('--max-tracks', type=int, default=200, help='Maximum tracks to process')
    parser.add_argument('--skip-existing', action='store_true', default=True, help='Skip already enriched tracks')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # File paths
    scrobbles_file = f"data/{args.username}_scrobbles.csv"
    enriched_file = f"data/{args.username}_enriched.csv"
    
    # Check if scrobbles file exists
    if not Path(scrobbles_file).exists():
        logger.error(f"Scrobbles file not found: {scrobbles_file}")
        return
    
    # Load scrobbles
    logger.info(f"Loading scrobbles from {scrobbles_file}")
    df = pd.read_csv(scrobbles_file)
    logger.info(f"Loaded {len(df)} scrobbles")
    
    # Get unique tracks
    unique_tracks = df[['artist', 'track']].drop_duplicates()
    logger.info(f"Found {len(unique_tracks)} unique tracks")
    
    # Load existing enriched data if it exists
    already_enriched = set()
    if Path(enriched_file).exists() and args.skip_existing:
        logger.info(f"Loading existing enriched data from {enriched_file}")
        enriched_df = pd.read_csv(enriched_file)
        already_enriched = set(zip(enriched_df['artist'], enriched_df['track']))
        logger.info(f"Found {len(already_enriched)} already enriched tracks")
    
    # Filter out already enriched tracks
    if already_enriched:
        mask = ~unique_tracks.apply(lambda row: (row['artist'], row['track']) in already_enriched, axis=1)
        tracks_to_process = unique_tracks[mask]
        logger.info(f"Skipping {len(already_enriched)} already enriched tracks")
    else:
        tracks_to_process = unique_tracks
    
    logger.info(f"Will process {len(tracks_to_process)} new tracks")
    
    if len(tracks_to_process) == 0:
        logger.info("No new tracks to process!")
        return
    
    # Limit tracks if specified
    if args.max_tracks:
        tracks_to_process = tracks_to_process.head(args.max_tracks)
        logger.info(f"Limited to {len(tracks_to_process)} tracks")
    
    # Convert to list of dicts for enricher
    tracks_list = []
    for _, row in tracks_to_process.iterrows():
        tracks_list.append({
            'artist': row['artist'],
            'title': row['track']
        })
    
    # Initialize enricher
    logger.info("Initializing MusicBrainz enricher...")
    enricher = MusicBrainzEnricher()
    
    # Enrich tracks
    logger.info(f"Starting enrichment of {len(tracks_list)} tracks...")
    enriched_results = enricher.enrich_tracks_batch(tracks_list, max_tracks=args.max_tracks)
    
    if not enriched_results:
        logger.warning("No tracks were successfully enriched!")
        return
    
    # Convert results to DataFrame
    enriched_data = []
    for track_key, enriched_info in enriched_results.items():
        artist, title = track_key.split(' - ', 1)
        enriched_data.append({
            'artist': artist,
            'track': title,
            'musicbrainz_tags': ', '.join(enriched_info.get('musicbrainz_tags', [])),
            'musicbrainz_genres': ', '.join(enriched_info.get('musicbrainz_genres', [])),
            'simplified_mood': enriched_info.get('simplified_mood', 'neutral'),
            'first_release_date': enriched_info.get('first_release_date'),
            'country': enriched_info.get('country'),
            'label': enriched_info.get('label'),
            'musicbrainz_id': enriched_info.get('musicbrainz_id'),
            'musicbrainz_url': enriched_info.get('musicbrainz_url'),
            'length': enriched_info.get('length')
        })
    
    new_enriched_df = pd.DataFrame(enriched_data)
    
    # Append to existing enriched file or create new one
    if Path(enriched_file).exists():
        logger.info(f"Appending {len(new_enriched_df)} new enriched tracks to {enriched_file}")
        existing_df = pd.read_csv(enriched_file)
        combined_df = pd.concat([existing_df, new_enriched_df], ignore_index=True)
        combined_df.to_csv(enriched_file, index=False)
        logger.info(f"Total enriched tracks: {len(combined_df)}")
    else:
        logger.info(f"Creating new enriched file with {len(new_enriched_df)} tracks")
        new_enriched_df.to_csv(enriched_file, index=False)
    
    logger.info("Enrichment complete!")
    logger.info(f"Successfully enriched {len(enriched_results)} tracks")
    logger.info(f"Enriched data saved to: {enriched_file}")

if __name__ == "__main__":
    main() 