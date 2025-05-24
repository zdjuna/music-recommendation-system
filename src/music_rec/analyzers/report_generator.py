"""
Music Analysis Report Generator

Creates beautiful, professional reports from pattern analysis and AI insights.
Supports multiple output formats (console, HTML, PDF).
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
import logging

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown

logger = logging.getLogger(__name__)

class ReportGenerator:
    """
    Professional report generator for music analysis results.
    
    Designed for busy professionals who want clear, actionable insights.
    """
    
    def __init__(self, output_dir: str = "reports"):
        """
        Initialize report generator.
        
        Args:
            output_dir: Directory to save reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.console = Console(record=True)
        
    def generate_console_report(self, patterns: Dict, insights: Dict, 
                              username: str = "User") -> str:
        """
        Generate a beautiful console report.
        
        Args:
            patterns: Pattern analysis results
            insights: AI-generated insights
            username: Username for personalization
            
        Returns:
            Rich-formatted console output
        """
        self.console.clear()
        
        # Header
        self._add_header(username, patterns)
        
        # AI Insights
        self._add_ai_insights(insights)
        
        # Pattern Analysis
        self._add_pattern_analysis(patterns)
        
        # Key Statistics
        self._add_statistics_tables(patterns)
        
        # Recommendations
        self._add_recommendations(insights)
        
        # Footer
        self._add_footer()
        
        return self.console.export_text()
    
    def save_html_report(self, patterns: Dict, insights: Dict, 
                        username: str = "User", 
                        filename: Optional[str] = None) -> str:
        """
        Save report as HTML file.
        
        Args:
            patterns: Pattern analysis results
            insights: AI-generated insights  
            username: Username for personalization
            filename: Output filename (auto-generated if None)
            
        Returns:
            Path to saved HTML file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{username}_music_analysis_{timestamp}.html"
        
        filepath = self.output_dir / filename
        
        # Generate console report first
        console_output = self.generate_console_report(patterns, insights, username)
        
        # Export as HTML
        html_content = self.console.export_html(inline_styles=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"HTML report saved to {filepath}")
        return str(filepath)
    
    def save_json_report(self, patterns: Dict, insights: Dict,
                        username: str = "User",
                        filename: Optional[str] = None) -> str:
        """
        Save structured report as JSON.
        
        Args:
            patterns: Pattern analysis results
            insights: AI-generated insights
            username: Username for personalization  
            filename: Output filename (auto-generated if None)
            
        Returns:
            Path to saved JSON file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{username}_music_analysis_{timestamp}.json"
        
        filepath = self.output_dir / filename
        
        report_data = {
            'metadata': {
                'username': username,
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'report_version': '2.0'
            },
            'patterns': patterns,
            'ai_insights': insights,
            'summary': self._generate_executive_summary(patterns, insights)
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        logger.info(f"JSON report saved to {filepath}")
        return str(filepath)
    
    def _add_header(self, username: str, patterns: Dict):
        """Add report header with key metrics."""
        
        summary = patterns.get('summary_stats', {})
        total_scrobbles = summary.get('total_scrobbles', 0)
        unique_artists = summary.get('unique_artists', 0)
        date_range = summary.get('date_range_days', 0)
        
        # Main title
        title = f"🎵 {username}'s Music DNA Analysis"
        self.console.print(Panel(title, style="bold blue", padding=(1, 2)))
        
        # Key metrics in columns
        metrics = [
            f"[bold green]{total_scrobbles:,}[/]\nTotal Plays",
            f"[bold cyan]{unique_artists:,}[/]\nUnique Artists", 
            f"[bold yellow]{date_range:,}[/]\nDays of Data",
            f"[bold magenta]{summary.get('data_completeness', 'Unknown')}[/]\nData Quality"
        ]
        
        self.console.print()
        self.console.print(Columns(metrics, equal=True, expand=True))
        self.console.print()
    
    def _add_ai_insights(self, insights: Dict):
        """Add AI-generated insights section."""
        
        if not insights:
            return
        
        self.console.print("[bold blue]🧠 AI-Powered Insights[/]", style="bold")
        self.console.print()
        
        # Musical Personality
        if 'musical_personality' in insights:
            personality_panel = Panel(
                insights['musical_personality'],
                title="🎭 Musical Personality",
                border_style="green"
            )
            self.console.print(personality_panel)
            self.console.print()
        
        # Listening Behavior
        if 'listening_behavior' in insights:
            behavior_panel = Panel(
                insights['listening_behavior'],
                title="🎵 Listening Behavior",
                border_style="cyan"
            )
            self.console.print(behavior_panel)
            self.console.print()
        
        # Musical Evolution
        if 'musical_evolution' in insights:
            evolution_panel = Panel(
                insights['musical_evolution'],
                title="📈 Musical Evolution",
                border_style="yellow"
            )
            self.console.print(evolution_panel)
            self.console.print()
    
    def _add_pattern_analysis(self, patterns: Dict):
        """Add detailed pattern analysis."""
        
        self.console.print("[bold blue]📊 Pattern Analysis[/]", style="bold")
        self.console.print()
        
        # Temporal Patterns
        temporal = patterns.get('temporal', {})
        if temporal:
            self._add_temporal_analysis(temporal)
        
        # Discovery Patterns  
        discovery = patterns.get('discovery', {})
        if discovery:
            self._add_discovery_analysis(discovery)
        
        # Artist Loyalty
        artist_loyalty = patterns.get('artist_loyalty', {})
        if artist_loyalty:
            self._add_artist_analysis(artist_loyalty)
    
    def _add_temporal_analysis(self, temporal: Dict):
        """Add temporal pattern visualization."""
        
        peak_hours = temporal.get('peak_listening_hours', [])
        peak_days = temporal.get('peak_listening_days', [])
        
        temporal_info = f"""
**⏰ When You Listen**

Peak Hours: {', '.join(f'{h}:00' for h in peak_hours[:3])}
Peak Days: {', '.join(peak_days[:2])}
Average Session: {temporal.get('average_session_length', 0)} tracks
Consistency Score: {temporal.get('listening_consistency', 0)}/1.0
        """.strip()
        
        self.console.print(Panel(temporal_info, title="🕒 Temporal Patterns", border_style="blue"))
        self.console.print()
    
    def _add_discovery_analysis(self, discovery: Dict):
        """Add music discovery pattern analysis."""
        
        discovery_info = f"""
**🔍 Your Discovery Style**

Exploration Rate: {discovery.get('discovery_ratio', 0)}% of tracks played once
Monthly Discovery: {discovery.get('avg_monthly_discovery', 0)} new tracks
Heavy Rotation: {discovery.get('heavy_rotation_tracks', 0)} tracks played 10+ times
Repeat Ratio: {discovery.get('repeat_ratio', 0)}% of all plays are repeats
        """.strip()
        
        self.console.print(Panel(discovery_info, title="🎯 Discovery Patterns", border_style="green"))
        self.console.print()
    
    def _add_artist_analysis(self, artist_loyalty: Dict):
        """Add artist loyalty analysis."""
        
        artist_info = f"""
**🎤 Artist Relationship**

Total Artists: {artist_loyalty.get('unique_artists', 0):,}
Exploration Rate: {artist_loyalty.get('exploration_ratio', 0)}% are single-track artists
Loyal Artists: {artist_loyalty.get('loyal_artists_count', 0)} with 20+ plays
Top 10 Concentration: {artist_loyalty.get('artist_concentration', 0)}% of total plays
        """.strip()
        
        self.console.print(Panel(artist_info, title="🎨 Artist Loyalty", border_style="magenta"))
        self.console.print()
    
    def _add_statistics_tables(self, patterns: Dict):
        """Add detailed statistics tables."""
        
        self.console.print("[bold blue]📈 Detailed Statistics[/]", style="bold")
        self.console.print()
        
        # Top Artists Table
        artist_loyalty = patterns.get('artist_loyalty', {})
        top_artists = artist_loyalty.get('top_artists', {})
        
        if top_artists:
            artist_table = Table(title="🏆 Top Artists", show_header=True, header_style="bold magenta")
            artist_table.add_column("Artist", style="dim", width=30)
            artist_table.add_column("Plays", justify="right", style="bold")
            
            for artist, plays in list(top_artists.items())[:10]:
                artist_table.add_row(artist[:28] + "..." if len(artist) > 28 else artist, str(plays))
            
            self.console.print(artist_table)
            self.console.print()
        
        # Most Played Tracks
        discovery = patterns.get('discovery', {})
        top_tracks = discovery.get('most_played_tracks', {})
        
        if top_tracks:
            track_table = Table(title="🎵 Most Played Tracks", show_header=True, header_style="bold cyan")
            track_table.add_column("Track", style="dim", width=40)
            track_table.add_column("Plays", justify="right", style="bold")
            
            for track, plays in list(top_tracks.items())[:10]:
                display_track = track[:38] + "..." if len(track) > 38 else track
                track_table.add_row(display_track, str(plays))
            
            self.console.print(track_table)
            self.console.print()
        
        # Seasonal Analysis
        seasonal = patterns.get('seasonal', {})
        seasonal_dist = seasonal.get('seasonal_distribution', {})
        
        if seasonal_dist:
            seasonal_table = Table(title="🌅 Seasonal Listening", show_header=True, header_style="bold yellow")
            seasonal_table.add_column("Season", style="dim")
            seasonal_table.add_column("Plays", justify="right", style="bold")
            seasonal_table.add_column("Percentage", justify="right")
            
            total_plays = sum(seasonal_dist.values())
            for season, plays in seasonal_dist.items():
                percentage = f"{plays/total_plays*100:.1f}%"
                seasonal_table.add_row(season, str(plays), percentage)
            
            self.console.print(seasonal_table)
            self.console.print()
    
    def _add_recommendations(self, insights: Dict):
        """Add personalized recommendations."""
        
        if 'personalized_recommendations' not in insights:
            return
        
        recommendations = insights['personalized_recommendations']
        
        rec_panel = Panel(
            recommendations,
            title="💡 Personalized Recommendations",
            border_style="bright_green",
            padding=(1, 2)
        )
        
        self.console.print(rec_panel)
        self.console.print()
    
    def _add_footer(self):
        """Add report footer."""
        
        footer_text = f"""
Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
by Music Recommendation System v2.0

💡 Tip: Run analysis monthly to track your musical evolution!
        """.strip()
        
        self.console.print(Panel(footer_text, style="dim", padding=(1, 2)))
    
    def _generate_executive_summary(self, patterns: Dict, insights: Dict) -> Dict:
        """Generate executive summary for JSON reports."""
        
        summary = patterns.get('summary_stats', {})
        temporal = patterns.get('temporal', {})
        discovery = patterns.get('discovery', {})
        artist_loyalty = patterns.get('artist_loyalty', {})
        
        # Key insights
        key_insights = []
        
        # Listening personality
        peak_hours = temporal.get('peak_listening_hours', [])
        if peak_hours:
            peak_hour = peak_hours[0]
            if 6 <= peak_hour <= 11:
                key_insights.append("Morning music enthusiast")
            elif 18 <= peak_hour <= 22:
                key_insights.append("Evening music lover")
            else:
                key_insights.append("Flexible listening schedule")
        
        # Discovery style
        discovery_ratio = discovery.get('discovery_ratio', 0)
        if discovery_ratio > 60:
            key_insights.append("High music explorer")
        elif discovery_ratio < 30:
            key_insights.append("Focused on favorites")
        else:
            key_insights.append("Balanced discovery style")
        
        # Artist loyalty
        exploration_ratio = artist_loyalty.get('exploration_ratio', 0)
        if exploration_ratio > 60:
            key_insights.append("Wide artist exploration")
        else:
            key_insights.append("Deep artist loyalty")
        
        return {
            'total_scrobbles': summary.get('total_scrobbles', 0),
            'unique_artists': summary.get('unique_artists', 0),
            'data_span_days': summary.get('date_range_days', 0),
            'data_quality': summary.get('data_completeness', 'Unknown'),
            'key_insights': key_insights,
            'peak_listening_hour': peak_hours[0] if peak_hours else None,
            'discovery_percentage': discovery_ratio,
            'artist_exploration_percentage': exploration_ratio,
            'generated_timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def create_quick_summary(self, patterns: Dict, insights: Dict) -> str:
        """Create a quick one-page summary for busy professionals."""
        
        summary = patterns.get('summary_stats', {})
        temporal = patterns.get('temporal', {})
        discovery = patterns.get('discovery', {})
        
        # Get key metrics
        total_scrobbles = summary.get('total_scrobbles', 0)
        unique_artists = summary.get('unique_artists', 0)
        peak_hour = temporal.get('peak_listening_hours', [12])[0]
        discovery_ratio = discovery.get('discovery_ratio', 0)
        
        # Time personality
        if 6 <= peak_hour <= 11:
            time_personality = "Morning Listener"
        elif 18 <= peak_hour <= 22:
            time_personality = "Evening Music Lover"
        else:
            time_personality = "Flexible Schedule"
        
        # Discovery style
        if discovery_ratio > 60:
            discovery_style = "Music Explorer"
        elif discovery_ratio < 30:
            discovery_style = "Favorites Focused"
        else:
            discovery_style = "Balanced Discoverer"
        
        # Quick summary
        quick_summary = f"""
🎵 MUSIC DNA SNAPSHOT

📊 Your Numbers:
• {total_scrobbles:,} total plays across {unique_artists:,} artists
• Peak listening: {peak_hour}:00 ({time_personality})
• Discovery style: {discovery_style} ({discovery_ratio}% exploration)

💡 Key Insight:
{insights.get('musical_personality', 'Your musical personality is unique!')}

🎯 Recommendation:
{insights.get('personalized_recommendations', 'Keep exploring music that speaks to you!')}
        """.strip()
        
        return quick_summary
    
    def export_all_formats(self, patterns: Dict, insights: Dict, 
                          username: str = "User") -> Dict[str, str]:
        """
        Export report in all available formats.
        
        Returns:
            Dictionary mapping format names to file paths
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        exported_files = {}
        
        # HTML Report
        try:
            html_path = self.save_html_report(patterns, insights, username)
            exported_files['html'] = html_path
        except Exception as e:
            logger.error(f"Failed to export HTML: {e}")
        
        # JSON Report
        try:
            json_path = self.save_json_report(patterns, insights, username)
            exported_files['json'] = json_path
        except Exception as e:
            logger.error(f"Failed to export JSON: {e}")
        
        # Quick Summary (text)
        try:
            summary = self.create_quick_summary(patterns, insights)
            summary_path = self.output_dir / f"{username}_quick_summary_{timestamp}.txt"
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write(summary)
            exported_files['summary'] = str(summary_path)
        except Exception as e:
            logger.error(f"Failed to export summary: {e}")
        
        return exported_files 