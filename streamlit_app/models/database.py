"""
Database models and management for the music recommendation system
"""

import sqlite3
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
from datetime import datetime
import logging
from .database_utils import database_retry, validate_database_connection

logger = logging.getLogger(__name__)

class DatabaseManager:
    """SQLite database manager for music recommendation system"""
    
    def __init__(self, db_path: str = "data/music_rec.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self._init_database()
        
        # Validate database after initialization
        if not validate_database_connection(str(self.db_path)):
            raise RuntimeError(f"Database validation failed for {self.db_path}")
    
    def _get_connection(self):
        """Get database connection with proper settings"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")  # Better concurrency
        conn.execute("PRAGMA synchronous = NORMAL")
        return conn
    
    def _init_database(self):
        """Initialize database with required tables"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    display_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    preferences TEXT  -- JSON field for user preferences
                )
            ''')
            
            # Tracks table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tracks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    artist TEXT NOT NULL,
                    track TEXT NOT NULL,
                    album TEXT,
                    duration INTEGER,
                    spotify_id TEXT,
                    musicbrainz_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(artist, track)
                )
            ''')
            
            # Scrobbles table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scrobbles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    track_id INTEGER,
                    timestamp TIMESTAMP NOT NULL,
                    source TEXT DEFAULT 'lastfm',
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (track_id) REFERENCES tracks (id)
                )
            ''')
            
            # Track enrichment data
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS track_enrichment (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    track_id INTEGER,
                    source TEXT NOT NULL,  -- 'cyanite', 'spotify', etc.
                    mood_data TEXT,  -- JSON field
                    audio_features TEXT,  -- JSON field
                    tags TEXT,  -- JSON field
                    confidence REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (track_id) REFERENCES tracks (id)
                )
            ''')
            
            # Playlists table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS playlists (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    name TEXT NOT NULL,
                    description TEXT,
                    type TEXT DEFAULT 'custom',  -- 'custom', 'recommendation', 'auto'
                    settings TEXT,  -- JSON field for generation settings
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Playlist tracks table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS playlist_tracks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    playlist_id INTEGER,
                    track_id INTEGER,
                    position INTEGER,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (playlist_id) REFERENCES playlists (id),
                    FOREIGN KEY (track_id) REFERENCES tracks (id)
                )
            ''')
            
            # User feedback table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    track_id INTEGER,
                    playlist_id INTEGER,
                    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
                    feedback_type TEXT,  -- 'like', 'dislike', 'rating', 'skip'
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (track_id) REFERENCES tracks (id),
                    FOREIGN KEY (playlist_id) REFERENCES playlists (id)
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_scrobbles_user_time ON scrobbles(user_id, timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tracks_artist_track ON tracks(artist, track)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_playlist_tracks_playlist ON playlist_tracks(playlist_id, position)')
            
            conn.commit()
            logger.info("Database initialized successfully")
    
    def get_or_create_user(self, username: str, display_name: str = None) -> int:
        """Get existing user or create new one"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
            result = cursor.fetchone()
            
            if result:
                return result[0]
            
            cursor.execute(
                'INSERT INTO users (username, display_name) VALUES (?, ?)',
                (username, display_name or username)
            )
            return cursor.lastrowid
    
    def get_or_create_track(self, artist: str, track: str, album: str = None) -> int:
        """Get existing track or create new one"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT id FROM tracks WHERE artist = ? AND track = ?', (artist, track))
            result = cursor.fetchone()
            
            if result:
                return result[0]
            
            cursor.execute(
                'INSERT INTO tracks (artist, track, album) VALUES (?, ?, ?)',
                (artist, track, album)
            )
            return cursor.lastrowid
    
    @database_retry(max_retries=3)
    def import_csv_data(self, username: str, csv_path: Path):
        """Import existing CSV data into database"""
        if not csv_path.exists():
            logger.warning(f"CSV file not found: {csv_path}")
            return
        
        df = pd.read_csv(csv_path)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Get or create user within the same connection
            cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
            result = cursor.fetchone()
            
            if result:
                user_id = result[0]
            else:
                cursor.execute(
                    'INSERT INTO users (username, display_name) VALUES (?, ?)',
                    (username, username)
                )
                user_id = cursor.lastrowid
            
            for _, row in df.iterrows():
                # Get or create track within the same connection
                cursor.execute('SELECT id FROM tracks WHERE artist = ? AND track = ?', 
                             (row['artist'], row['track']))
                track_result = cursor.fetchone()
                
                if track_result:
                    track_id = track_result[0]
                else:
                    cursor.execute(
                        'INSERT INTO tracks (artist, track, album) VALUES (?, ?, ?)',
                        (row['artist'], row['track'], row.get('album'))
                    )
                    track_id = cursor.lastrowid
                
                # Insert scrobble
                cursor.execute('''
                    INSERT OR IGNORE INTO scrobbles (user_id, track_id, timestamp)
                    VALUES (?, ?, ?)
                ''', (user_id, track_id, row['timestamp']))
            
            conn.commit()
            logger.info(f"Imported {len(df)} scrobbles for user {username}")
    
    def get_user_stats(self, username: str) -> Dict[str, Any]:
        """Get comprehensive user statistics"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Get or create user within the same connection
            cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
            result = cursor.fetchone()
            
            if result:
                user_id = result[0]
            else:
                cursor.execute(
                    'INSERT INTO users (username, display_name) VALUES (?, ?)',
                    (username, username)
                )
                user_id = cursor.lastrowid
            
            # Total scrobbles
            cursor.execute('SELECT COUNT(*) FROM scrobbles WHERE user_id = ?', (user_id,))
            total_scrobbles = cursor.fetchone()[0]
            
            # Unique artists
            cursor.execute('''
                SELECT COUNT(DISTINCT t.artist) 
                FROM scrobbles s 
                JOIN tracks t ON s.track_id = t.id 
                WHERE s.user_id = ?
            ''', (user_id,))
            unique_artists = cursor.fetchone()[0]
            
            # Unique tracks
            cursor.execute('''
                SELECT COUNT(DISTINCT s.track_id) 
                FROM scrobbles s 
                WHERE s.user_id = ?
            ''', (user_id,))
            unique_tracks = cursor.fetchone()[0]
            
            # Playlists count
            cursor.execute('SELECT COUNT(*) FROM playlists WHERE user_id = ?', (user_id,))
            playlists_count = cursor.fetchone()[0]
            
            return {
                'total_scrobbles': total_scrobbles,
                'unique_artists': unique_artists,
                'unique_tracks': unique_tracks,
                'playlists_count': playlists_count
            }
    
    def create_playlist(self, username: str, name: str, description: str = None, 
                       playlist_type: str = 'custom') -> int:
        """Create a new playlist"""
        user_id = self.get_or_create_user(username)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO playlists (user_id, name, description, type)
                VALUES (?, ?, ?, ?)
            ''', (user_id, name, description, playlist_type))
            return cursor.lastrowid
    
    @database_retry(max_retries=3)
    def add_tracks_to_playlist(self, playlist_id: int, tracks: List[Dict[str, str]]):
        """Add tracks to a playlist"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            for position, track_info in enumerate(tracks):
                # Check if track exists first
                cursor.execute('SELECT id FROM tracks WHERE artist = ? AND track = ?', 
                             (track_info['artist'], track_info['track']))
                result = cursor.fetchone()
                
                if result:
                    track_id = result[0]
                else:
                    # Insert track within the same connection
                    cursor.execute(
                        'INSERT INTO tracks (artist, track, album) VALUES (?, ?, ?)',
                        (track_info['artist'], track_info['track'], track_info.get('album'))
                    )
                    track_id = cursor.lastrowid
                
                # Insert playlist track
                cursor.execute('''
                    INSERT INTO playlist_tracks (playlist_id, track_id, position)
                    VALUES (?, ?, ?)
                ''', (playlist_id, track_id, position))
            
            conn.commit()
    
    def get_user_playlists(self, username: str) -> List[Dict[str, Any]]:
        """Get all playlists for a user"""
        user_id = self.get_or_create_user(username)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, name, description, type, created_at, updated_at
                FROM playlists 
                WHERE user_id = ?
                ORDER BY updated_at DESC
            ''', (user_id,))
            
            playlists = []
            for row in cursor.fetchall():
                playlists.append({
                    'id': row[0],
                    'name': row[1],
                    'description': row[2],
                    'type': row[3],
                    'created_at': row[4],
                    'updated_at': row[5]
                })
            
            return playlists
    
    def get_playlist_tracks(self, playlist_id: int) -> List[Dict[str, Any]]:
        """Get all tracks in a playlist"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT t.artist, t.track, t.album, pt.position
                FROM playlist_tracks pt
                JOIN tracks t ON pt.track_id = t.id
                WHERE pt.playlist_id = ?
                ORDER BY pt.position
            ''', (playlist_id,))
            
            tracks = []
            for row in cursor.fetchall():
                tracks.append({
                    'artist': row[0],
                    'track': row[1],
                    'album': row[2],
                    'position': row[3]
                })
            
            return tracks

# Global database instance
db = DatabaseManager()