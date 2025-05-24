"""
Playlist Generator

Converts recommendations into various playlist formats:
- M3U playlists
- JSON exports
- CSV exports
- Roon-compatible formats
"""

import json
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from .recommendation_engine import RecommendationResult, RecommendationRequest

logger = logging.getLogger(__name__)

class PlaylistGenerator:
    """
    Generate playlists in various formats from recommendations
    """
    
    def __init__(self, output_dir: str = 'playlists'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_playlist(self, 
                         result: RecommendationResult, 
                         name: str,
                         formats: List[str] = ['json', 'csv', 'm3u']) -> Dict[str, Path]:
        """
        Generate playlist in multiple formats
        
        Args:
            result: Recommendation result
            name: Playlist name
            formats: List of formats to generate ('json', 'csv', 'm3u', 'roon')
            
        Returns:
            Dictionary mapping format to file path
        """
        
        generated_files = {}
        
        # Sanitize playlist name for filename
        safe_name = self._sanitize_filename(name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"{safe_name}_{timestamp}"
        
        for format_type in formats:
            try:
                if format_type == 'json':
                    file_path = self._generate_json(result, base_filename)
                elif format_type == 'csv':
                    file_path = self._generate_csv(result, base_filename)
                elif format_type == 'm3u':
                    file_path = self._generate_m3u(result, base_filename)
                elif format_type == 'roon':
                    file_path = self._generate_roon(result, base_filename)
                else:
                    logger.warning(f"Unknown format: {format_type}")
                    continue
                
                generated_files[format_type] = file_path
                logger.info(f"Generated {format_type} playlist: {file_path}")
                
            except Exception as e:
                logger.error(f"Failed to generate {format_type} playlist: {e}")
        
        return generated_files
    
    def _generate_json(self, result: RecommendationResult, base_filename: str) -> Path:
        """Generate JSON playlist"""
        
        playlist_data = {
            'name': base_filename,
            'generated_at': datetime.now().isoformat(),
            'confidence_score': result.confidence_score,
            'explanation': result.explanation,
            'metadata': result.metadata,
            'tracks': []
        }
        
        for i, track in enumerate(result.tracks, 1):
            track_data = {
                'position': i,
                'artist': track.get('artist', 'Unknown Artist'),
                'track': track.get('track', 'Unknown Track'),
                'album': track.get('album', 'Unknown Album'),
                'duration': track.get('duration'),
                'year': track.get('year'),
                'genre': track.get('primary_genre'),
                'mood': track.get('mood'),
                'energy': track.get('energy'),
                'valence': track.get('valence'),
                'popularity': track.get('popularity'),
                'url': track.get('url_track'),
                'scores': {
                    'total_score': track.get('total_score'),
                    'familiarity_score': track.get('familiarity_score'),
                    'mood_score': track.get('mood_score'),
                    'temporal_score': track.get('temporal_score'),
                    'diversity_score': track.get('diversity_score')
                }
            }
            playlist_data['tracks'].append(track_data)
        
        file_path = self.output_dir / f"{base_filename}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(playlist_data, f, indent=2, ensure_ascii=False)
        
        return file_path
    
    def _generate_csv(self, result: RecommendationResult, base_filename: str) -> Path:
        """Generate CSV playlist"""
        
        file_path = self.output_dir / f"{base_filename}.csv"
        
        fieldnames = [
            'position', 'artist', 'track', 'album', 'duration', 'year',
            'genre', 'mood', 'energy', 'valence', 'popularity', 'url',
            'total_score', 'familiarity_score', 'mood_score', 
            'temporal_score', 'diversity_score'
        ]
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for i, track in enumerate(result.tracks, 1):
                row = {
                    'position': i,
                    'artist': track.get('artist', 'Unknown Artist'),
                    'track': track.get('track', 'Unknown Track'),
                    'album': track.get('album', 'Unknown Album'),
                    'duration': track.get('duration'),
                    'year': track.get('year'),
                    'genre': track.get('primary_genre'),
                    'mood': track.get('mood'),
                    'energy': track.get('energy'),
                    'valence': track.get('valence'),
                    'popularity': track.get('popularity'),
                    'url': track.get('url_track'),
                    'total_score': track.get('total_score'),
                    'familiarity_score': track.get('familiarity_score'),
                    'mood_score': track.get('mood_score'),
                    'temporal_score': track.get('temporal_score'),
                    'diversity_score': track.get('diversity_score')
                }
                writer.writerow(row)
        
        return file_path
    
    def _generate_m3u(self, result: RecommendationResult, base_filename: str) -> Path:
        """Generate M3U playlist"""
        
        file_path = self.output_dir / f"{base_filename}.m3u"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("#EXTM3U\n")
            f.write(f"# Generated by Music Recommendation System\n")
            f.write(f"# {result.explanation}\n")
            f.write(f"# Confidence: {result.confidence_score:.2f}\n")
            f.write(f"# Generated: {datetime.now().isoformat()}\n\n")
            
            for track in result.tracks:
                artist = track.get('artist', 'Unknown Artist')
                title = track.get('track', 'Unknown Track')
                duration = track.get('duration', -1)
                
                # Convert duration from seconds to M3U format if available
                if duration and duration > 0:
                    duration_seconds = int(duration)
                else:
                    duration_seconds = -1
                
                f.write(f"#EXTINF:{duration_seconds},{artist} - {title}\n")
                
                # Add URL if available, otherwise use a placeholder
                url = track.get('url_track', f"# {artist} - {title}")
                f.write(f"{url}\n\n")
        
        return file_path
    
    def _generate_roon(self, result: RecommendationResult, base_filename: str) -> Path:
        """Generate Roon-compatible playlist"""
        
        # Roon uses a specific JSON format for playlists
        roon_data = {
            'name': base_filename.replace('_', ' ').title(),
            'description': f"{result.explanation} (Confidence: {result.confidence_score:.2f})",
            'tracks': []
        }
        
        for track in result.tracks:
            # Roon format focuses on artist/album/track identification
            roon_track = {
                'artist': track.get('artist', 'Unknown Artist'),
                'album': track.get('album', 'Unknown Album'),
                'track': track.get('track', 'Unknown Track'),
                'year': track.get('year'),
                'genre': track.get('primary_genre'),
                'mood': track.get('mood'),
                'energy_level': self._energy_to_level(track.get('energy')),
                'recommendation_score': track.get('total_score')
            }
            roon_data['tracks'].append(roon_track)
        
        file_path = self.output_dir / f"{base_filename}_roon.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(roon_data, f, indent=2, ensure_ascii=False)
        
        return file_path
    
    def _energy_to_level(self, energy: Optional[float]) -> str:
        """Convert energy score to level description"""
        if energy is None:
            return 'unknown'
        elif energy >= 0.7:
            return 'high'
        elif energy >= 0.3:
            return 'medium'
        else:
            return 'low'
    
    def _sanitize_filename(self, name: str) -> str:
        """Sanitize filename by removing invalid characters"""
        import re
        # Remove invalid filename characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', name)
        # Remove multiple underscores
        sanitized = re.sub(r'_+', '_', sanitized)
        # Remove leading/trailing underscores
        sanitized = sanitized.strip('_')
        # Limit length
        return sanitized[:50] if len(sanitized) > 50 else sanitized
    
    def generate_preset_playlists(self, 
                                 engine, 
                                 username: str,
                                 formats: List[str] = ['json', 'csv']) -> Dict[str, Dict[str, Path]]:
        """
        Generate playlists for all presets
        
        Args:
            engine: RecommendationEngine instance
            username: Username for file naming
            formats: List of formats to generate
            
        Returns:
            Dictionary mapping preset name to generated files
        """
        
        presets = engine.get_recommendation_presets()
        generated_playlists = {}
        
        for preset_name, request in presets.items():
            try:
                logger.info(f"Generating playlist for preset: {preset_name}")
                
                # Generate recommendations
                result = engine.generate_recommendations(request)
                
                # Generate playlist files
                playlist_name = f"{username}_{preset_name}"
                files = self.generate_playlist(result, playlist_name, formats)
                
                generated_playlists[preset_name] = files
                
            except Exception as e:
                logger.error(f"Failed to generate playlist for preset {preset_name}: {e}")
        
        return generated_playlists
    
    def create_playlist_summary(self, generated_playlists: Dict[str, Dict[str, Path]]) -> Path:
        """Create a summary of all generated playlists"""
        
        summary_data = {
            'generated_at': datetime.now().isoformat(),
            'total_playlists': len(generated_playlists),
            'playlists': {}
        }
        
        for preset_name, files in generated_playlists.items():
            summary_data['playlists'][preset_name] = {
                'files': {format_type: str(path) for format_type, path in files.items()},
                'file_count': len(files)
            }
        
        summary_path = self.output_dir / f"playlist_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)
        
        return summary_path 