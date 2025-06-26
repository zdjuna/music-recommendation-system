#!/usr/bin/env python3
"""
Real-time Large Batch Analysis Dashboard

Provides live updates on the large batch music analysis progress.
"""

import os
import time
import subprocess
from datetime import datetime

def get_process_info():
    """Get information about the running process"""
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        for line in lines:
            if 'process_large_batch.py' in line and 'grep' not in line:
                parts = line.split()
                if len(parts) >= 11:
                    pid = parts[1]
                    cpu = parts[2]
                    memory = parts[3]
                    time_used = parts[9]
                    return {'pid': pid, 'cpu': cpu, 'memory': memory, 'time': time_used}
    except:
        pass
    return None

def check_files():
    """Check for output files and their sizes"""
    files_info = {}
    
    # Check main output log
    try:
        size = os.path.getsize('/Users/zdjuna/music-recommendation-system/large_batch_output.log')
        files_info['output_log'] = size
    except:
        files_info['output_log'] = 0
    
    # Check processing log
    try:
        size = os.path.getsize('/Users/zdjuna/music-recommendation-system/large_batch_processing.log')
        files_info['processing_log'] = size
    except:
        files_info['processing_log'] = 0
    
    # Check for temp files
    try:
        data_dir = '/Users/zdjuna/music-recommendation-system/data'
        files = os.listdir(data_dir)
        temp_files = [f for f in files if 'temp' in f and 'analysis' in f]
        files_info['temp_files'] = len(temp_files)
        files_info['temp_list'] = temp_files
    except:
        files_info['temp_files'] = 0
        files_info['temp_list'] = []
    
    return files_info

def main():
    """Main monitoring function"""
    print("🎵 Real-time Large Batch Analysis Dashboard")
    print("=" * 60)
    print(f"Monitoring started: {datetime.now().strftime('%H:%M:%S')}")
    print("Press Ctrl+C to exit\n")
    
    start_time = datetime.now()
    cycle = 0
    
    try:
        while True:
            cycle += 1
            current_time = datetime.now()
            elapsed = current_time - start_time
            
            # Get process info
            proc_info = get_process_info()
            
            # Get file info
            file_info = check_files()
            
            # Clear screen and show status
            os.system('clear')
            
            print("🎵 Real-time Large Batch Analysis Dashboard")
            print("=" * 60)
            print(f"Current Time: {current_time.strftime('%H:%M:%S')}")
            print(f"Elapsed: {str(elapsed).split('.')[0]}")
            print(f"Refresh: #{cycle} (every 10s)")
            print()
            
            # Process status
            if proc_info:
                print("📊 PROCESS STATUS: ✅ RUNNING")
                print(f"   PID: {proc_info['pid']}")
                print(f"   CPU: {proc_info['cpu']}%")
                print(f"   Memory: {proc_info['memory']}%")
                print(f"   Runtime: {proc_info['time']}")
            else:
                print("📊 PROCESS STATUS: ❌ NOT RUNNING")
            print()
            
            # File status
            print("📁 FILE STATUS:")
            print(f"   Output Log: {file_info['output_log']:,} bytes")
            print(f"   Processing Log: {file_info['processing_log']:,} bytes")
            print(f"   Temp Files: {file_info['temp_files']}")
            
            if file_info['temp_list']:
                print("   Temp Files Created:")
                for temp_file in file_info['temp_list']:
                    print(f"     • {temp_file}")
            print()
            
            # Target info
            print("🎯 ANALYSIS TARGET:")
            print("   • Current: 4,200 tracks (6.3% coverage)")
            print("   • Processing: 10,000 tracks (4201-14200)")
            print("   • Target: 14,200 tracks (21.4% coverage)")
            print("   • Remaining: 52,232 tracks (78.6%)")
            print()
            
            # Progress estimation
            if file_info['temp_files'] > 0:
                estimated_progress = file_info['temp_files'] * 1000  # Assuming 1000 tracks per temp file
                print(f"📈 ESTIMATED PROGRESS:")
                print(f"   • Tracks processed: ~{estimated_progress:,}")
                print(f"   • Batch progress: {estimated_progress/10000*100:.1f}%")
            
            print("\nPress Ctrl+C to exit monitoring...")
            
            time.sleep(10)  # Update every 10 seconds
            
    except KeyboardInterrupt:
        print(f"\n\n⏹️  Monitoring stopped")
        print(f"Total monitoring time: {str(datetime.now() - start_time).split('.')[0]}")

if __name__ == "__main__":
    main()
