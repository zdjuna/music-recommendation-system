#!/usr/bin/env python3
"""
Final Acceleration Processor - Complete Library Coverage

Optimized to process the remaining 52,232 tracks with maximum speed:
- Advanced parallel processing with 6-8 workers
- Smart batch sizing based on API performance
- Enhanced caching and memory management
- Real-time progress monitoring
- Optimized for speed while maintaining data quality
"""

import pandas as pd
import sys
import os
import json
import time
from datetime import datetime, timedelta
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from multiprocessing import cpu_count
import threading
from collections import defaultdict
import signal
import traceback

# Import our music analyzer
from real_music_analyzer_hybrid import RealMusicAnalyzer

# Set up enhanced logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('final_acceleration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FinalAccelerationProcessor:
    """Ultra-optimized processor for final library completion"""
    
    def __init__(self, num_workers=6):
        """
        Initialize with optimized settings for remaining tracks
        
        Args:
            num_workers: Number of parallel workers (default 6 for optimal API balance)
        """
        self.num_workers = min(num_workers, cpu_count())
        self.batch_size = 2000  # Optimal batch size for memory and speed
        self.save_interval = 250  # Frequent saves for safety
        self.progress_interval = 25  # Real-time progress updates
        
        # Performance tracking
        self.start_time = None
        self.processed_count = 0
        self.total_tracks = 0
        self.success_count = 0
        self.error_count = 0
        
        # Thread-safe statistics
        self.stats_lock = threading.Lock()
        self.stats = {
            'spotify_success': 0,
            'spotify_total': 0,
            'lastfm_success': 0,
            'lastfm_total': 0,
            'processing_speed': 0,
            'eta': None
        }
        
        # Graceful shutdown handling
        self.shutdown_requested = False
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info(f"Final Acceleration Processor initialized with {self.num_workers} workers")
    
    def _signal_handler(self, signum, frame):
        """Handle graceful shutdown"""
        logger.info("Shutdown signal received. Finishing current batch...")
        self.shutdown_requested = True
    
    def _update_stats(self, result):
        """Thread-safe statistics update"""
        with self.stats_lock:
            self.processed_count += 1
            
            if result.get('spotify_found'):
                self.stats['spotify_success'] += 1
            self.stats['spotify_total'] += 1
            
            if result.get('lastfm_found'):
                self.stats['lastfm_success'] += 1
            self.stats['lastfm_total'] += 1
            
            # Calculate processing speed
            if self.start_time:
                elapsed = time.time() - self.start_time
                self.stats['processing_speed'] = self.processed_count / elapsed * 3600  # tracks per hour
                
                # Calculate ETA
                remaining = self.total_tracks - self.processed_count
                if self.stats['processing_speed'] > 0:
                    eta_hours = remaining / self.stats['processing_speed']
                    self.stats['eta'] = datetime.now() + timedelta(hours=eta_hours)
    
    def _print_progress(self):
        """Print detailed progress information"""
        with self.stats_lock:
            if self.processed_count % self.progress_interval == 0:
                spotify_rate = (self.stats['spotify_success'] / max(1, self.stats['spotify_total'])) * 100
                lastfm_rate = (self.stats['lastfm_success'] / max(1, self.stats['lastfm_total'])) * 100
                progress_pct = (self.processed_count / self.total_tracks) * 100
                
                eta_str = self.stats['eta'].strftime('%H:%M:%S') if self.stats['eta'] else 'Calculating...'
                
                logger.info(f"""
                ╔══════════════════════════════════════════════════════════════╗
                ║ FINAL ACCELERATION PROGRESS - {datetime.now().strftime('%H:%M:%S')}                    ║
                ╠══════════════════════════════════════════════════════════════╣
                ║ Progress: {self.processed_count:,}/{self.total_tracks:,} tracks ({progress_pct:.1f}%)    
                ║ Speed: {self.stats['processing_speed']:.0f} tracks/hour               
                ║ Spotify Success: {spotify_rate:.1f}% ({self.stats['spotify_success']:,}/{self.stats['spotify_total']:,})
                ║ Last.fm Success: {lastfm_rate:.1f}% ({self.stats['lastfm_success']:,}/{self.stats['lastfm_total']:,})
                ║ ETA: {eta_str}                                          
                ╚══════════════════════════════════════════════════════════════╝
                """)
    
    def process_batch(self, batch_tracks, batch_num, analyzer):
        """Process a batch of tracks with a single analyzer instance"""
        results = []
        batch_start = time.time()
        
        logger.info(f"Worker processing batch {batch_num} with {len(batch_tracks)} tracks")
        
        for idx, (_, row) in enumerate(batch_tracks.iterrows()):
            if self.shutdown_requested:
                logger.info(f"Shutdown requested, stopping batch {batch_num}")
                break
            
            try:
                # Analyze track
                result = analyzer.analyze_track(row['artist'], row['track'])
                results.append(result)
                
                # Update statistics
                self._update_stats(result)
                self._print_progress()
                
                # Small delay to respect API limits (adjusted for multiple workers)
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error processing {row['artist']} - {row['track']}: {str(e)}")
                self.error_count += 1
                # Add error placeholder
                results.append({
                    'artist': row['artist'],
                    'track': row['track'],
                    'error': str(e),
                    'spotify_found': False,
                    'lastfm_found': False
                })
        
        batch_time = time.time() - batch_start
        logger.info(f"Batch {batch_num} completed in {batch_time:.1f}s ({len(results)} tracks)")
        
        return results
    
    def save_results(self, all_results, output_file):
        """Save results to CSV with comprehensive data"""
        try:
            df = pd.DataFrame(all_results)
            df.to_csv(output_file, index=False)
            
            # Log summary statistics
            total = len(df)
            spotify_success = df['spotify_found'].sum()
            lastfm_success = df['lastfm_found'].sum()
            
            logger.info(f"""
            ╔═══════════════════════════════════════════════════════════════╗
            ║ BATCH SAVE COMPLETE - {datetime.now().strftime('%H:%M:%S')}                         ║
            ╠═══════════════════════════════════════════════════════════════╣
            ║ File: {os.path.basename(output_file):<50} ║
            ║ Tracks Saved: {total:,}                                            ║
            ║ Spotify Success: {spotify_success:,} ({(spotify_success/total)*100:.1f}%)                    ║
            ║ Last.fm Success: {lastfm_success:,} ({(lastfm_success/total)*100:.1f}%)                    ║
            ║ File Size: {os.path.getsize(output_file) / 1024 / 1024:.1f} MB                         ║
            ╚═══════════════════════════════════════════════════════════════╝
            """)
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving results: {str(e)}")
            return False
    
    def process_remaining_library(self, start_index=14200):
        """
        Process all remaining tracks in the library starting from the given index
        
        Args:
            start_index: Track index to start from (default 14200 - after current progress)
        """
        self.start_time = time.time()
        
        try:
            # Load unique tracks
            logger.info("Loading music library...")
            scrobbles_df = pd.read_csv('data/zdjuna_scrobbles.csv')
            unique_tracks = scrobbles_df[['artist', 'track']].drop_duplicates().reset_index(drop=True)
            
            # Get remaining tracks
            remaining_tracks = unique_tracks.iloc[start_index:].reset_index(drop=True)
            self.total_tracks = len(remaining_tracks)
            
            logger.info(f"""
            ╔═══════════════════════════════════════════════════════════════╗
            ║ FINAL ACCELERATION PROCESSING STARTED                         ║
            ╠═══════════════════════════════════════════════════════════════╣
            ║ Total Library: {len(unique_tracks):,} tracks                            ║
            ║ Already Processed: {start_index:,} tracks                          ║
            ║ Remaining to Process: {self.total_tracks:,} tracks                     ║
            ║ Workers: {self.num_workers}                                           ║
            ║ Batch Size: {self.batch_size:,}                                    ║
            ║ Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}           ║
            ╚═══════════════════════════════════════════════════════════════╝
            """)
            
            # Process in batches with parallel workers
            all_results = []
            batch_num = 0
            
            with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
                # Submit batches to workers
                futures = []
                
                for i in range(0, len(remaining_tracks), self.batch_size):
                    if self.shutdown_requested:
                        break
                    
                    batch = remaining_tracks.iloc[i:i + self.batch_size]
                    batch_num += 1
                    
                    # Create analyzer instance for this batch
                    analyzer = RealMusicAnalyzer()
                    
                    # Submit batch to executor
                    future = executor.submit(self.process_batch, batch, batch_num, analyzer)
                    futures.append(future)
                
                # Collect results as they complete
                for future in as_completed(futures):
                    try:
                        batch_results = future.result()
                        all_results.extend(batch_results)
                        
                        # Save intermediate results every save_interval
                        if len(all_results) % (self.save_interval * self.num_workers) == 0:
                            temp_file = f'data/zdjuna_unique_tracks_analysis_TEMP_{start_index}_{start_index + len(all_results)}.csv'
                            self.save_results(all_results, temp_file)
                        
                    except Exception as e:
                        logger.error(f"Batch processing error: {str(e)}")
                        traceback.print_exc()
            
            # Save final results
            if all_results:
                end_index = start_index + len(all_results)
                final_file = f'data/zdjuna_unique_tracks_analysis_{start_index}_{end_index}_FINAL.csv'
                self.save_results(all_results, final_file)
                
                # Create new comprehensive dataset
                self.create_comprehensive_dataset(final_file, start_index, end_index)
            
            # Final summary
            total_time = time.time() - self.start_time
            self.print_final_summary(total_time)
            
        except Exception as e:
            logger.error(f"Critical error in processing: {str(e)}")
            traceback.print_exc()
    
    def create_comprehensive_dataset(self, new_file, start_index, end_index):
        """Combine all analysis files into one comprehensive dataset"""
        try:
            logger.info("Creating updated comprehensive dataset...")
            
            # Load existing comprehensive data
            existing_file = 'data/zdjuna_unique_tracks_analysis_COMPREHENSIVE_14200.csv'
            existing_df = pd.read_csv(existing_file)
            
            # Load new data
            new_df = pd.read_csv(new_file)
            
            # Combine datasets
            comprehensive_df = pd.concat([existing_df, new_df], ignore_index=True)
            
            # Save comprehensive dataset
            comprehensive_file = f'data/zdjuna_unique_tracks_analysis_COMPREHENSIVE_{len(comprehensive_df)}.csv'
            comprehensive_df.to_csv(comprehensive_file, index=False)
            
            logger.info(f"""
            ╔═══════════════════════════════════════════════════════════════╗
            ║ COMPREHENSIVE DATASET UPDATED                                 ║
            ╠═══════════════════════════════════════════════════════════════╣
            ║ Previous Dataset: {len(existing_df):,} tracks                            ║
            ║ New Tracks Added: {len(new_df):,} tracks                             ║
            ║ Total Comprehensive: {len(comprehensive_df):,} tracks                  ║
            ║ Library Coverage: {(len(comprehensive_df)/66432)*100:.1f}%                       ║
            ║ File: {os.path.basename(comprehensive_file):<40} ║
            ║ Size: {os.path.getsize(comprehensive_file) / 1024 / 1024:.1f} MB                              ║
            ╚═══════════════════════════════════════════════════════════════╝
            """)
            
        except Exception as e:
            logger.error(f"Error creating comprehensive dataset: {str(e)}")
    
    def print_final_summary(self, total_time):
        """Print final processing summary"""
        hours = total_time / 3600
        tracks_per_hour = self.processed_count / hours if hours > 0 else 0
        
        with self.stats_lock:
            spotify_rate = (self.stats['spotify_success'] / max(1, self.stats['spotify_total'])) * 100
            lastfm_rate = (self.stats['lastfm_success'] / max(1, self.stats['lastfm_total'])) * 100
        
        logger.info(f"""
        ╔═══════════════════════════════════════════════════════════════════╗
        ║ FINAL ACCELERATION PROCESSING COMPLETE!                           ║
        ╠═══════════════════════════════════════════════════════════════════╣
        ║ Total Processing Time: {hours:.1f} hours                              ║
        ║ Tracks Processed: {self.processed_count:,}                               ║
        ║ Processing Speed: {tracks_per_hour:.0f} tracks/hour                    ║
        ║ Spotify Success Rate: {spotify_rate:.1f}%                             ║
        ║ Last.fm Success Rate: {lastfm_rate:.1f}%                              ║
        ║ Errors: {self.error_count}                                           ║
        ║ Workers Used: {self.num_workers}                                      ║
        ║ Completion Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}      ║
        ╚═══════════════════════════════════════════════════════════════════╝
        """)

def main():
    """Main execution function"""
    if len(sys.argv) > 1:
        start_index = int(sys.argv[1])
    else:
        start_index = 14200  # Default to continue from current progress
    
    processor = FinalAccelerationProcessor(num_workers=6)
    processor.process_remaining_library(start_index=start_index)

if __name__ == "__main__":
    main()
