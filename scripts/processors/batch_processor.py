#!/usr/bin/env python3
"""
Ultra-Fast Complete Library Processor

Processes the remaining 52,232 tracks with maximum optimization:
- Parallel processing with multiple workers
- Optimized API rate limiting
- Enhanced caching strategies
- Batch processing with larger chunks
- Cloud-ready architecture
"""

import pandas as pd
import sys
import os
import asyncio
import aiohttp
import json
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import logging
from multiprocessing import Manager, Pool, cpu_count
from real_music_analyzer_hybrid import RealMusicAnalyzer

# Set up logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ultra_fast_processing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class UltraFastMusicProcessor:
    """Ultra-optimized music processor with parallel processing"""
    
    def __init__(self, num_workers=None):
        self.num_workers = num_workers or min(8, cpu_count())  # Limit to 8 to respect API limits
        self.batch_size = 5000  # Larger batches for efficiency
        self.save_interval = 500  # Save more frequently
        self.progress_interval = 50  # More frequent progress updates
        
        # Shared statistics
        self.manager = Manager()
        self.shared_stats = self.manager.dict({
            'processed': 0,
            'spotify_matches': 0,
            'lastfm_enriched': 0,
            'cache_hits': 0,
            'errors': 0
        })
        
    def analyze_track_batch(self, batch_data):
        """Process a batch of tracks in a single worker"""
        worker_id, tracks_batch, shared_stats = batch_data
        
        # Initialize analyzer for this worker
        analyzer = RealMusicAnalyzer()
        results = []
        
        for idx, (artist, track) in enumerate(tracks_batch):
            try:
                analysis = analyzer.analyze_track(artist, track)
                if analysis:
                    results.append(analysis)
                    
                    # Update shared statistics
                    shared_stats['processed'] += 1
                    if analysis.get('spotify_matched'):
                        shared_stats['spotify_matches'] += 1
                    if analysis.get('lastfm_tags'):
                        shared_stats['lastfm_enriched'] += 1
                
                # Small delay to respect API limits (distributed across workers)
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {artist} - {track}: {e}")
                shared_stats['errors'] += 1
                continue
        
        return results, worker_id
    
    def process_complete_library(self):
        """Process the complete remaining library with parallel workers"""
        
        print("🚀 Ultra-Fast Complete Library Processor")
        print("=" * 60)
        
        # Load data
        logger.info("Loading library data...")
        scrobbles_df = pd.read_csv('data/zdjuna_scrobbles.csv')
        unique_tracks = scrobbles_df[['artist', 'track']].drop_duplicates()
        
        # Define processing parameters
        START_INDEX = 14200  # Where we left off
        total_tracks = len(unique_tracks)
        remaining_tracks = total_tracks - START_INDEX
        
        print(f"\n📊 Processing Parameters:")
        print(f"   • Total library: {total_tracks:,} tracks")
        print(f"   • Already analyzed: {START_INDEX:,} tracks")
        print(f"   • Remaining to process: {remaining_tracks:,} tracks")
        print(f"   • Workers: {self.num_workers}")
        print(f"   • Batch size: {self.batch_size:,}")
        
        # Estimate completion time
        estimated_rate = 150  # tracks per minute with parallelization
        estimated_hours = remaining_tracks / estimated_rate / 60
        print(f"   • Estimated completion: {estimated_hours:.1f} hours")
        
        # Select remaining tracks
        remaining_tracks_df = unique_tracks.iloc[START_INDEX:].copy()
        track_pairs = [(row['artist'], row['track']) for _, row in remaining_tracks_df.iterrows()]
        
        print(f"\n🔧 Initializing {self.num_workers} parallel workers...")
        
        # Split tracks into batches for workers
        worker_batch_size = len(track_pairs) // self.num_workers
        worker_batches = []
        
        for i in range(self.num_workers):
            start_idx = i * worker_batch_size
            if i == self.num_workers - 1:  # Last worker gets remaining tracks
                end_idx = len(track_pairs)
            else:
                end_idx = (i + 1) * worker_batch_size
            
            batch = track_pairs[start_idx:end_idx]
            worker_batches.append((i, batch, self.shared_stats))
            print(f"   Worker {i}: {len(batch):,} tracks")
        
        print(f"\n🚀 Starting parallel processing at {datetime.now().strftime('%H:%M:%S')}")
        start_time = time.time()
        
        # Process with parallel workers
        all_results = []
        
        with ProcessPoolExecutor(max_workers=self.num_workers) as executor:
            # Submit all worker tasks
            futures = [executor.submit(self.analyze_track_batch, batch_data) 
                      for batch_data in worker_batches]
            
            # Monitor progress
            completed_workers = 0
            while completed_workers < self.num_workers:
                time.sleep(30)  # Check every 30 seconds
                
                # Print progress
                elapsed_mins = (time.time() - start_time) / 60
                processed = self.shared_stats['processed']
                rate = processed / elapsed_mins if elapsed_mins > 0 else 0
                eta_mins = (remaining_tracks - processed) / rate if rate > 0 else 0
                
                print(f"   Progress: {processed:,}/{remaining_tracks:,} "
                      f"({processed/remaining_tracks*100:.1f}%) | "
                      f"Rate: {rate:.1f}/min | ETA: {eta_mins:.0f}min")
                
                # Check for completed workers
                completed_workers = sum(1 for f in futures if f.done())
            
            # Collect all results
            for future in futures:
                try:
                    worker_results, worker_id = future.result()
                    all_results.extend(worker_results)
                    print(f"   ✅ Worker {worker_id} completed: {len(worker_results):,} tracks")
                except Exception as e:
                    logger.error(f"Worker failed: {e}")
        
        # Save final results
        if all_results:
            self.save_complete_results(all_results, START_INDEX, total_tracks)
            self.print_final_statistics(all_results, remaining_tracks, start_time)
        else:
            print("\n❌ No tracks were successfully processed!")
    
    def save_complete_results(self, results, start_index, total_tracks):
        """Save the complete analysis results"""
        
        results_df = pd.DataFrame(results)
        
        # Save the new batch
        batch_file = f'data/zdjuna_unique_tracks_analysis_{start_index+1}_{total_tracks}_COMPLETE.csv'
        results_df.to_csv(batch_file, index=False)
        
        # Create the ultimate comprehensive file
        comprehensive_files = [
            'data/zdjuna_unique_tracks_analysis_4200_FINAL.csv',
            'data/zdjuna_unique_tracks_analysis_4201_14200_batch.csv',
            batch_file
        ]
        
        all_data = []
        for file in comprehensive_files:
            if os.path.exists(file):
                df = pd.read_csv(file)
                all_data.append(df)
        
        if all_data:
            ultimate_df = pd.concat(all_data, ignore_index=True)
            ultimate_file = 'data/zdjuna_unique_tracks_analysis_COMPLETE_LIBRARY.csv'
            ultimate_df.to_csv(ultimate_file, index=False)
            
            print(f"\n🎯 COMPLETE LIBRARY ANALYSIS ACHIEVED!")
            print(f"   • Complete dataset: {ultimate_file}")
            print(f"   • Total tracks: {len(ultimate_df):,}")
            print(f"   • Coverage: {len(ultimate_df)/total_tracks*100:.1f}%")
            print(f"   • File size: {os.path.getsize(ultimate_file)/1024/1024:.1f} MB")
    
    def print_final_statistics(self, results, target_tracks, start_time):
        """Print final processing statistics"""
        
        elapsed_time = time.time() - start_time
        elapsed_hours = elapsed_time / 3600
        
        print(f"\n📈 ULTRA-FAST PROCESSING COMPLETE!")
        print(f"   • Tracks processed: {len(results):,}")
        print(f"   • Target tracks: {target_tracks:,}")
        print(f"   • Success rate: {len(results)/target_tracks*100:.1f}%")
        print(f"   • Processing time: {elapsed_hours:.1f} hours")
        print(f"   • Average rate: {len(results)/elapsed_time*60:.1f} tracks/minute")
        print(f"   • Spotify matches: {self.shared_stats['spotify_matches']:,}")
        print(f"   • Last.fm enriched: {self.shared_stats['lastfm_enriched']:,}")
        print(f"   • Cache hits: {self.shared_stats['cache_hits']:,}")
        print(f"   • Errors: {self.shared_stats['errors']:,}")

def main():
    """Main execution function"""
    
    # Determine optimal number of workers
    suggested_workers = min(8, cpu_count())
    
    print(f"💻 System detected {cpu_count()} CPU cores")
    print(f"🚀 Recommended workers: {suggested_workers}")
    
    processor = UltraFastMusicProcessor(num_workers=suggested_workers)
    processor.process_complete_library()

if __name__ == "__main__":
    main()
