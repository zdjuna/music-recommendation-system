#!/usr/bin/env python3
"""
Import user's CSV data into the music recommendation system database
"""
from streamlit_app.models.database import db
import sys
from pathlib import Path

def main():
    username = 'zdjuna'
    csv_path = Path('data/zdjuna_scrobbles.csv')
    
    print(f'Importing CSV data from {csv_path}...')
    if csv_path.exists():
        print(f'File size: {csv_path.stat().st_size / (1024*1024):.1f} MB')
        
        try:
            db.import_csv_data(username, csv_path)
            print('✅ Data import completed!')
            
            stats = db.get_user_stats(username)
            print(f'📊 Import Statistics:')
            print(f'  - Total scrobbles: {stats["total_scrobbles"]:,}')
            print(f'  - Unique artists: {stats["unique_artists"]:,}')
            print(f'  - Unique tracks: {stats["unique_tracks"]:,}')
            print(f'  - Playlists: {stats["playlists_count"]:,}')
            
            if stats["total_scrobbles"] > 0:
                print('🎉 Data import successful!')
                return True
            else:
                print('❌ No data was imported')
                return False
                
        except Exception as e:
            print(f'❌ Import failed: {e}')
            return False
    else:
        print(f'❌ CSV file not found at {csv_path}')
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
