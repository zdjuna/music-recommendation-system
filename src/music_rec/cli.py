"""
Command-line interface for the Music Recommendation System

Simple, user-friendly CLI designed for busy professionals.
"""

import os
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

# Add the src directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from music_rec.data_fetchers import LastFMFetcher
from music_rec.analyzers import PatternAnalyzer, AIInsightGenerator, ReportGenerator
from music_rec.enrichers import MetadataEnricher

console = Console()

@click.group()
@click.version_option(version='4.0.0', prog_name='Music Recommendation System')
def cli():
    """
    🎵 Music Recommendation System v4.0
    
    AI-powered playlist generation using your Last.fm listening data.
    Designed for busy professionals who want maximum results with minimal effort.
    
    NEW in v4.0: Intelligent recommendation engine with personalized playlists!
    v3.0: MusicBrainz metadata enrichment with mood & genre classification
    v2.0: AI-powered pattern analysis and insights
    v1.0: Last.fm data fetching and export
    """
    # Load configuration
    config_path = Path('config/config.env')
    if config_path.exists():
        load_dotenv(config_path)
    else:
        load_dotenv()  # Load from .env in current directory

@cli.command()
def setup():
    """Set up the system by creating configuration files."""
    console.print("[bold blue]🎵 Music Recommendation System Setup[/]")
    console.print()
    
    # Check if config directory exists
    config_dir = Path('config')
    if not config_dir.exists():
        config_dir.mkdir()
        console.print("[green]Created config directory[/]")
    
    # Check for existing config
    config_file = config_dir / 'config.env'
    template_file = config_dir / 'config_template.env'
    
    if config_file.exists():
        console.print(f"[yellow]Configuration file already exists: {config_file}[/]")
        if not click.confirm("Do you want to overwrite it?"):
            return
    
    if template_file.exists():
        console.print(f"[cyan]Template found at: {template_file}[/]")
        console.print("[yellow]Please copy config_template.env to config.env and fill in your API keys.[/]")
    else:
        console.print("[red]Template file not found. Please ensure config_template.env exists in the config directory.[/]")
    
    console.print()
    console.print("[bold]Next steps:[/]")
    console.print("1. Get your Last.fm API key from: https://www.last.fm/api/account/create")
    console.print("2. Copy config_template.env to config.env")
    console.print("3. Fill in your API credentials")
    console.print("4. Run: python -m music_rec.cli fetch")
    console.print()
    console.print("[bold cyan]NEW in v2.0:[/]")
    console.print("5. Run: python -m music_rec.cli analyze")
    console.print("6. Get AI-powered insights about your music taste!")

@cli.command()
@click.option('--username', help='Last.fm username (overrides config)')
@click.option('--incremental/--full', default=True, help='Incremental update vs full fetch')
@click.option('--start-date', help='Start date (YYYY-MM-DD)')
@click.option('--end-date', help='End date (YYYY-MM-DD)')
@click.option('--export-formats', default='csv,json', help='Export formats (csv,json,parquet)')
def fetch(username: Optional[str], incremental: bool, start_date: Optional[str], 
          end_date: Optional[str], export_formats: str):
    """Fetch all scrobble data from Last.fm."""
    
    # Get configuration
    api_key = os.getenv('LASTFM_API_KEY')
    if not api_key:
        console.print("[red]❌ LASTFM_API_KEY not found in configuration![/]")
        console.print("Run 'python -m music_rec.cli setup' to configure the system.")
        return
    
    username = username or os.getenv('LASTFM_USERNAME')
    if not username:
        console.print("[red]❌ LASTFM_USERNAME not found in configuration![/]")
        console.print("Either provide --username or set LASTFM_USERNAME in config.env")
        return
    
    console.print(f"[bold blue]🎵 Fetching Last.fm data for user: {username}[/]")
    
    try:
        # Initialize fetcher
        fetcher = LastFMFetcher(
            api_key=api_key,
            username=username,
            data_dir='data'
        )
        
        # Fetch data
        df = fetcher.fetch_all_scrobbles(
            incremental=incremental,
            start_date=start_date,
            end_date=end_date
        )
        
        if df.empty:
            console.print("[yellow]No data fetched.[/]")
            return
        
        # Export to requested formats
        formats = [fmt.strip() for fmt in export_formats.split(',')]
        fetcher.export_to_formats(df, formats)
        
        # Show summary
        stats = fetcher.get_summary_stats()
        show_summary(stats)
        
        # Suggest next steps
        console.print()
        console.print("[bold green]🎉 Data fetch complete![/]")
        console.print("[cyan]💡 Next step: Run analysis to get AI insights about your music taste:[/]")
        console.print(f"[cyan]   python -m music_rec.cli analyze --username {username}[/]")
        
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/]")
        sys.exit(1)

@cli.command()
@click.option('--username', help='Last.fm username (overrides config)')
@click.option('--ai/--no-ai', default=True, help='Use AI for insights generation')
@click.option('--export-formats', default='console,html,json', 
              help='Report formats (console,html,json,summary)')
@click.option('--save-reports/--no-save', default=True, help='Save reports to files')
def analyze(username: Optional[str], ai: bool, export_formats: str, save_reports: bool):
    """🧠 NEW: Analyze your music patterns with AI insights."""
    
    username = username or os.getenv('LASTFM_USERNAME')
    if not username:
        console.print("[red]❌ LASTFM_USERNAME not found in configuration![/]")
        console.print("Either provide --username or set LASTFM_USERNAME in config.env")
        return
    
    # Check for data file
    data_file = Path(f'data/{username}_scrobbles.csv')
    if not data_file.exists():
        console.print(f"[red]❌ No data found for {username}![/]")
        console.print("Run 'fetch' command first to download your Last.fm data.")
        return
    
    console.print(f"[bold blue]🧠 Analyzing music patterns for: {username}[/]")
    console.print()
    
    try:
        # Load data
        import pandas as pd
        console.print("[cyan]📊 Loading your music data...[/]")
        df = pd.read_csv(data_file)
        console.print(f"[green]✅ Loaded {len(df):,} scrobbles[/]")
        
        # Run pattern analysis
        console.print("[cyan]🔍 Analyzing listening patterns...[/]")
        analyzer = PatternAnalyzer(df)
        patterns = analyzer.analyze_all_patterns()
        console.print("[green]✅ Pattern analysis complete[/]")
        
        # Generate AI insights
        insights = {}
        if ai:
            console.print("[cyan]🤖 Generating AI insights...[/]")
            
            # Get API keys
            openai_key = os.getenv('OPENAI_API_KEY')
            anthropic_key = os.getenv('ANTHROPIC_API_KEY')
            
            if openai_key or anthropic_key:
                ai_generator = AIInsightGenerator(
                    openai_api_key=openai_key,
                    anthropic_api_key=anthropic_key
                )
                insights = ai_generator.generate_comprehensive_insights(patterns)
                console.print("[green]✅ AI insights generated[/]")
            else:
                console.print("[yellow]⚠️  No AI API keys found. Using fallback insights.[/]")
                ai_generator = AIInsightGenerator()
                insights = ai_generator.generate_comprehensive_insights(patterns)
        else:
            console.print("[cyan]📝 Generating basic insights...[/]")
            ai_generator = AIInsightGenerator()
            insights = ai_generator._generate_fallback_insights(patterns)
        
        # Generate reports
        console.print("[cyan]📋 Generating reports...[/]")
        report_generator = ReportGenerator()
        
        formats = [fmt.strip() for fmt in export_formats.split(',')]
        
        # Show console report
        if 'console' in formats:
            console.print()
            console.print("[bold green]🎵 YOUR MUSIC DNA ANALYSIS[/]")
            console.print("=" * 60)
            report_generator.generate_console_report(patterns, insights, username)
        
        # Save other formats
        saved_files = {}
        if save_reports:
            if 'html' in formats:
                html_path = report_generator.save_html_report(patterns, insights, username)
                saved_files['html'] = html_path
            
            if 'json' in formats:
                json_path = report_generator.save_json_report(patterns, insights, username)
                saved_files['json'] = json_path
            
            if 'summary' in formats:
                summary = report_generator.create_quick_summary(patterns, insights)
                summary_path = Path('reports') / f"{username}_quick_summary.txt"
                summary_path.parent.mkdir(exist_ok=True)
                with open(summary_path, 'w') as f:
                    f.write(summary)
                saved_files['summary'] = str(summary_path)
        
        # Show saved files
        if saved_files:
            console.print()
            console.print("[bold green]📁 Reports saved:[/]")
            for format_type, filepath in saved_files.items():
                console.print(f"[green]  {format_type.upper()}: {filepath}[/]")
        
        console.print()
        console.print("[bold green]🎉 Analysis complete![/]")
        
    except Exception as e:
        console.print(f"[red]❌ Error during analysis: {e}[/]")
        sys.exit(1)

@cli.command()
@click.option('--username', help='Last.fm username (overrides config)')
def quick_insights(username: Optional[str]):
    """⚡ Get a quick summary of your music taste (30 seconds)."""
    
    username = username or os.getenv('LASTFM_USERNAME')
    if not username:
        console.print("[red]❌ LASTFM_USERNAME not found in configuration![/]")
        return
    
    # Check for data file
    data_file = Path(f'data/{username}_scrobbles.csv')
    if not data_file.exists():
        console.print(f"[red]❌ No data found for {username}![/]")
        console.print("Run 'fetch' command first to download your Last.fm data.")
        return
    
    try:
        # Quick analysis
        import pandas as pd
        df = pd.read_csv(data_file)
        
        analyzer = PatternAnalyzer(df)
        patterns = analyzer.analyze_all_patterns()
        
        ai_generator = AIInsightGenerator()
        insights = ai_generator._generate_fallback_insights(patterns)
        
        report_generator = ReportGenerator()
        quick_summary = report_generator.create_quick_summary(patterns, insights)
        
        console.print(quick_summary)
        
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/]")

@cli.command()
@click.option('--username', help='Last.fm username (overrides config)')
def stats(username: Optional[str]):
    """Show statistics about your fetched data."""
    
    username = username or os.getenv('LASTFM_USERNAME')
    if not username:
        console.print("[red]❌ LASTFM_USERNAME not found in configuration![/]")
        return
    
    # Look for stats file
    stats_file = Path(f'data/{username}_stats.json')
    if not stats_file.exists():
        console.print(f"[red]❌ No stats found for {username}. Run fetch first.[/]")
        return
    
    try:
        import json
        with open(stats_file) as f:
            stats_data = json.load(f)
        
        show_summary(stats_data)
        
        # Suggest analysis
        console.print()
        console.print("[cyan]💡 Want deeper insights? Run:[/]")
        console.print(f"[cyan]   python -m music_rec.cli analyze --username {username}[/]")
        
    except Exception as e:
        console.print(f"[red]❌ Error reading stats: {e}[/]")

@cli.command()
@click.option('--username', help='Last.fm username (overrides config)')
@click.option('--sample-size', type=int, help='Limit to N records for testing (e.g., 100)')
@click.option('--batch-size', default=50, help='Batch size for processing')
@click.option('--output-format', default='csv', help='Output format (csv, json, parquet)')
def enrich(username: Optional[str], sample_size: Optional[int], batch_size: int, output_format: str):
    """🎨 NEW: Enrich your music data with MusicBrainz metadata."""
    
    username = username or os.getenv('LASTFM_USERNAME')
    if not username:
        console.print("[red]❌ LASTFM_USERNAME not found in configuration![/]")
        console.print("Either provide --username or set LASTFM_USERNAME in config.env")
        return
    
    # Check for data file
    data_file = Path(f'data/{username}_scrobbles.csv')
    if not data_file.exists():
        console.print(f"[red]❌ No data found for {username}![/]")
        console.print("Run 'fetch' command first to download your Last.fm data.")
        return
    
    console.print(f"[bold blue]🎨 Enriching music data with metadata for: {username}[/]")
    
    # Show sample warning
    if sample_size:
        console.print(f"[yellow]📝 Processing sample of {sample_size} records for testing[/]")
    else:
        console.print("[yellow]⚠️  This will process your entire dataset and may take time![/]")
        if not click.confirm("Continue with full dataset enrichment?"):
            console.print("[yellow]💡 Use --sample-size to test with fewer records first[/]")
            return
    
    console.print()
    
    try:
        # Initialize enricher
        console.print("[cyan]🔧 Initializing metadata enricher...[/]")
        enricher = MetadataEnricher(data_dir='data', cache_dir='cache')
        console.print("[green]✅ Enricher initialized[/]")
        
        # Set output file
        output_file = f'data/{username}_enriched.{output_format}'
        
        # Run enrichment
        console.print("[cyan]🎵 Starting MusicBrainz enrichment...[/]")
        console.print("[yellow]📡 This will make API calls to MusicBrainz (rate limited to 1/second)[/]")
        
        enriched_df = enricher.enrich_dataset(
            scrobble_file=str(data_file),
            output_file=output_file,
            batch_size=batch_size,
            sample_size=sample_size
        )
        
        if enriched_df.empty:
            console.print("[red]❌ No data was enriched[/]")
            return
        
        # Show enrichment summary
        console.print()
        console.print("[bold green]🎉 Metadata enrichment complete![/]")
        console.print(f"[green]📁 Enriched data saved to: {output_file}[/]")
        
        # Show enrichment statistics
        stats = enricher.get_stats()
        show_enrichment_summary(stats, len(enriched_df))
        
        # Analyze enrichment quality
        quality_analysis = enricher.analyze_enrichment_quality(enriched_df)
        show_enrichment_quality(quality_analysis)
        
        # Suggest next steps
        console.print()
        console.print("[cyan]💡 Next steps:[/]")
        console.print(f"[cyan]   python -m music_rec.cli analyze-enriched --username {username}[/]")
        console.print("[cyan]   python -m music_rec.cli mood-report --username {username}[/]")
        
    except Exception as e:
        console.print(f"[red]❌ Error during enrichment: {e}[/]")
        import traceback
        console.print(f"[red]Details: {traceback.format_exc()}[/]")
        sys.exit(1)

@cli.command()
@click.option('--username', help='Last.fm username (overrides config)')
@click.option('--top-n', default=20, help='Number of top items to show')
def analyze_enriched(username: Optional[str], top_n: int):
    """📊 Analyze your enriched music data with genre and mood insights."""
    
    username = username or os.getenv('LASTFM_USERNAME')
    if not username:
        console.print("[red]❌ LASTFM_USERNAME not found in configuration![/]")
        return
    
    # Check for enriched data file
    enriched_file = Path(f'data/{username}_enriched.csv')
    if not enriched_file.exists():
        console.print(f"[red]❌ No enriched data found for {username}![/]")
        console.print("Run 'enrich' command first to add metadata to your music data.")
        return
    
    console.print(f"[bold blue]📊 Analyzing enriched music data for: {username}[/]")
    console.print()
    
    try:
        import pandas as pd
        import json
        from collections import Counter
        
        # Load enriched data
        console.print("[cyan]📊 Loading enriched data...[/]")
        df = pd.read_csv(enriched_file)
        console.print(f"[green]✅ Loaded {len(df):,} enriched scrobbles[/]")
        
        # Analyze genres
        console.print()
        console.print("[bold blue]🎭 Genre Analysis[/]")
        genre_counter = Counter()
        
        for idx, row in df.iterrows():
            if pd.notna(row.get('mb_genres')):
                try:
                    genres = json.loads(row['mb_genres'])
                    genre_counter.update(genres)
                except (json.JSONDecodeError, TypeError):
                    pass
        
        if genre_counter:
            console.print(f"[green]🎵 Top {top_n} Genres in Your Library:[/]")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Rank", style="dim", width=6)
            table.add_column("Genre", style="cyan")
            table.add_column("Tracks", style="green", justify="right")
            
            for i, (genre, count) in enumerate(genre_counter.most_common(top_n), 1):
                table.add_row(str(i), genre, str(count))
            
            console.print(table)
        else:
            console.print("[yellow]⚠️  No genre data found in enriched dataset[/]")
        
        # Analyze moods
        console.print()
        console.print("[bold blue]😊 Mood Analysis[/]")
        mood_counter = Counter(df['mood_primary'].dropna())
        
        if mood_counter:
            console.print(f"[green]🎭 Your Music Mood Distribution:[/]")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Mood", style="cyan")
            table.add_column("Tracks", style="green", justify="right")
            table.add_column("Percentage", style="yellow", justify="right")
            
            total_mood_tracks = sum(mood_counter.values())
            for mood, count in mood_counter.most_common():
                percentage = (count / total_mood_tracks) * 100
                table.add_row(mood, str(count), f"{percentage:.1f}%")
            
            console.print(table)
        else:
            console.print("[yellow]⚠️  No mood data found in enriched dataset[/]")
        
        # Analyze energy levels
        console.print()
        console.print("[bold blue]⚡ Energy Level Analysis[/]")
        energy_counter = Counter(df['energy_level'].dropna())
        
        if energy_counter:
            console.print(f"[green]🔥 Your Music Energy Distribution:[/]")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Energy Level", style="cyan")
            table.add_column("Tracks", style="green", justify="right")
            table.add_column("Percentage", style="yellow", justify="right")
            
            total_energy_tracks = sum(energy_counter.values())
            energy_order = ['very_low', 'low', 'medium', 'high', 'very_high']
            
            for energy in energy_order:
                if energy in energy_counter:
                    count = energy_counter[energy]
                    percentage = (count / total_energy_tracks) * 100
                    table.add_row(energy.replace('_', ' ').title(), str(count), f"{percentage:.1f}%")
            
            console.print(table)
        else:
            console.print("[yellow]⚠️  No energy level data found in enriched dataset[/]")
        
        # Show coverage statistics
        console.print()
        console.print("[bold blue]📈 Enrichment Coverage[/]")
        
        enrichment_columns = ['mb_genres', 'mb_tags', 'mood_primary', 'energy_level']
        coverage_table = Table(show_header=True, header_style="bold magenta")
        coverage_table.add_column("Data Type", style="cyan")
        coverage_table.add_column("Coverage", style="green", justify="right")
        
        for col in enrichment_columns:
            if col in df.columns:
                coverage = (df[col].notna().sum() / len(df)) * 100
                coverage_table.add_row(
                    col.replace('mb_', '').replace('_', ' ').title(),
                    f"{coverage:.1f}%"
                )
        
        console.print(coverage_table)
        
    except Exception as e:
        console.print(f"[red]❌ Error during analysis: {e}[/]")
        sys.exit(1)

@cli.command()
@click.option('--username', help='Last.fm username (overrides config)')
@click.option('--mood', help='Filter by specific mood (e.g., happy, sad, calm)')
@click.option('--export-format', default='console', help='Export format (console, csv, json)')
def mood_report(username: Optional[str], mood: Optional[str], export_format: str):
    """🎭 Generate mood-based listening reports from enriched data."""
    
    username = username or os.getenv('LASTFM_USERNAME')
    if not username:
        console.print("[red]❌ LASTFM_USERNAME not found in configuration![/]")
        console.print("Either provide --username or set LASTFM_USERNAME in config.env")
        return
    
    # Check for enriched data
    enriched_file = Path(f'data/{username}_enriched.csv')
    if not enriched_file.exists():
        console.print(f"[red]❌ No enriched data found for {username}![/]")
        console.print("Run 'enrich' command first to add mood classifications.")
        return
    
    console.print(f"[bold blue]🎭 Generating mood report for: {username}[/]")
    if mood:
        console.print(f"[cyan]Filtering by mood: {mood}[/]")
    console.print()
    
    try:
        import pandas as pd
        from collections import Counter
        
        # Load enriched data
        df = pd.read_csv(enriched_file)
        
        # Filter by mood if specified
        if mood:
            df = df[df['mood'].str.lower() == mood.lower()]
            if df.empty:
                console.print(f"[yellow]No tracks found with mood '{mood}'[/]")
                return
        
        # Ensure we have mood data
        if 'mood' not in df.columns:
            console.print("[red]❌ No mood data found in enriched dataset![/]")
            return
        
        # Generate mood insights
        mood_insights = {
            'total_tracks': len(df),
            'mood_distribution': dict(Counter(df['mood_primary'].dropna())),
            'top_artists_by_mood': {},
            'listening_patterns': {},
            'energy_correlation': {}
        }
        
        # Top artists by mood
        if mood:
            top_artists = df['artist'].value_counts().head(10)
            mood_insights['top_artists_by_mood'][mood] = dict(top_artists)
        else:
            for m in df['mood_primary'].dropna().unique():
                mood_tracks = df[df['mood_primary'] == m]
                top_artists = mood_tracks['artist'].value_counts().head(5)
                mood_insights['top_artists_by_mood'][m] = dict(top_artists)
        
        # Time-based patterns
        if 'timestamp' in df.columns:
            df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
            hour_mood = df.groupby(['hour', 'mood_primary']).size().unstack(fill_value=0)
            mood_insights['listening_patterns']['by_hour'] = hour_mood.to_dict()
        
        # Display results
        if export_format == 'console':
            console.print(f"[bold green]🎵 Mood Report Summary[/]")
            console.print(f"[green]Total tracks analyzed: {mood_insights['total_tracks']:,}[/]")
            console.print()
            
            if mood:
                console.print(f"[bold blue]🎯 '{mood.title()}' Mood Analysis[/]")
                if mood in mood_insights['top_artists_by_mood']:
                    console.print("[cyan]Top Artists:[/]")
                    for artist, count in list(mood_insights['top_artists_by_mood'][mood].items())[:10]:
                        console.print(f"  • {artist}: {count} tracks")
            else:
                console.print("[bold blue]🎭 Mood Distribution[/]")
                for mood_name, count in mood_insights['mood_distribution'].items():
                    percentage = (count / mood_insights['total_tracks']) * 100
                    console.print(f"  • {mood_name.title()}: {count} tracks ({percentage:.1f}%)")
        
        elif export_format in ['csv', 'json']:
            # Save detailed report
            output_file = f'reports/{username}_mood_report.{export_format}'
            Path('reports').mkdir(exist_ok=True)
            
            if export_format == 'csv':
                df.to_csv(output_file, index=False)
            else:  # json
                import json
                with open(output_file, 'w') as f:
                    json.dump(mood_insights, f, indent=2)
            
            console.print(f"[green]📁 Mood report saved to: {output_file}[/]")
        
    except Exception as e:
        console.print(f"[red]❌ Error generating mood report: {e}[/]")
        sys.exit(1)

@cli.command()
@click.option('--username', help='Last.fm username (overrides config)')
@click.option('--mood', help='Mood preference (happy, sad, calm, energetic, etc.)')
@click.option('--energy-level', type=click.Choice(['low', 'medium', 'high']), help='Energy level preference')
@click.option('--discovery-level', type=float, default=0.3, help='Discovery level (0.0=familiar, 1.0=new)')
@click.option('--playlist-length', type=int, default=20, help='Number of tracks in playlist')
@click.option('--time-context', type=click.Choice(['morning', 'afternoon', 'evening', 'night']), help='Time of day context')
@click.option('--exclude-recent/--include-recent', default=True, help='Exclude recently played tracks')
@click.option('--formats', default='json,csv', help='Export formats (json,csv,m3u,roon)')
def recommend(username: Optional[str], mood: Optional[str], energy_level: Optional[str], 
              discovery_level: float, playlist_length: int, time_context: Optional[str],
              exclude_recent: bool, formats: str):
    """🎯 NEW: Generate personalized music recommendations."""
    
    username = username or os.getenv('LASTFM_USERNAME')
    if not username:
        console.print("[red]❌ LASTFM_USERNAME not found in configuration![/]")
        console.print("Either provide --username or set LASTFM_USERNAME in config.env")
        return
    
    # Check for required data
    scrobbles_file = Path(f'data/{username}_scrobbles.csv')
    if not scrobbles_file.exists():
        console.print(f"[red]❌ No scrobbles data found for {username}![/]")
        console.print("Run 'fetch' command first to download your Last.fm data.")
        return
    
    console.print(f"[bold blue]🎯 Generating recommendations for: {username}[/]")
    console.print()
    
    try:
        from music_rec.recommenders import RecommendationEngine, RecommendationRequest, PlaylistGenerator
        
        # Initialize recommendation engine
        console.print("[cyan]🔧 Initializing recommendation engine...[/]")
        engine = RecommendationEngine(username=username)
        
        # Create recommendation request
        request = RecommendationRequest(
            mood=mood,
            energy_level=energy_level,
            discovery_level=discovery_level,
            playlist_length=playlist_length,
            time_context=time_context,
            exclude_recent=exclude_recent
        )
        
        # Generate recommendations
        console.print("[cyan]🎵 Generating personalized recommendations...[/]")
        result = engine.generate_recommendations(request)
        
        # Display results
        console.print(f"[bold green]✅ Generated {len(result.tracks)} recommendations[/]")
        console.print(f"[green]Confidence Score: {result.confidence_score:.2f}[/]")
        console.print(f"[cyan]Explanation: {result.explanation}[/]")
        console.print()
        
        # Show top recommendations
        console.print("[bold blue]🎵 Top Recommendations:[/]")
        for i, track in enumerate(result.tracks[:10], 1):
            artist = track.get('artist', 'Unknown Artist')
            title = track.get('track', 'Unknown Track')
            album = track.get('album', 'Unknown Album')
            score = track.get('total_score', 0)
            
            console.print(f"  {i:2d}. [bold]{artist}[/] - {title}")
            console.print(f"      Album: {album} | Score: {score:.3f}")
            
            if track.get('mood'):
                console.print(f"      Mood: {track['mood']} | Energy: {track.get('energy', 'N/A')}")
            console.print()
        
        # Generate playlist files
        if formats:
            console.print("[cyan]💾 Generating playlist files...[/]")
            generator = PlaylistGenerator()
            format_list = [f.strip() for f in formats.split(',')]
            
            playlist_name = f"{username}_custom_recommendations"
            files = generator.generate_playlist(result, playlist_name, format_list)
            
            console.print("[bold green]📁 Generated playlist files:[/]")
            for format_type, file_path in files.items():
                console.print(f"  • {format_type.upper()}: {file_path}")
        
        # Show metadata
        if result.metadata:
            console.print()
            console.print("[bold blue]📊 Playlist Metadata:[/]")
            console.print(f"  • Unique Artists: {result.metadata.get('unique_artists', 0)}")
            
            if 'genre_distribution' in result.metadata:
                console.print("  • Genre Distribution:")
                for genre, count in list(result.metadata['genre_distribution'].items())[:5]:
                    console.print(f"    - {genre}: {count} tracks")
            
            if 'mood_distribution' in result.metadata:
                console.print("  • Mood Distribution:")
                for mood_name, count in result.metadata['mood_distribution'].items():
                    console.print(f"    - {mood_name}: {count} tracks")
        
    except Exception as e:
        console.print(f"[red]❌ Error generating recommendations: {e}[/]")
        import traceback
        console.print(f"[red]Details: {traceback.format_exc()}[/]")
        sys.exit(1)

@cli.command()
@click.option('--username', help='Last.fm username (overrides config)')
@click.option('--formats', default='json,csv', help='Export formats (json,csv,m3u,roon)')
def generate_presets(username: Optional[str], formats: str):
    """🎪 Generate playlists for all recommendation presets."""
    
    username = username or os.getenv('LASTFM_USERNAME')
    if not username:
        console.print("[red]❌ LASTFM_USERNAME not found in configuration![/]")
        console.print("Either provide --username or set LASTFM_USERNAME in config.env")
        return
    
    # Check for required data
    scrobbles_file = Path(f'data/{username}_scrobbles.csv')
    if not scrobbles_file.exists():
        console.print(f"[red]❌ No scrobbles data found for {username}![/]")
        console.print("Run 'fetch' command first to download your Last.fm data.")
        return
    
    console.print(f"[bold blue]🎪 Generating preset playlists for: {username}[/]")
    console.print()
    
    try:
        from music_rec.recommenders import RecommendationEngine, PlaylistGenerator
        
        # Initialize components
        console.print("[cyan]🔧 Initializing recommendation engine...[/]")
        engine = RecommendationEngine(username=username)
        generator = PlaylistGenerator()
        
        # Get available presets
        presets = engine.get_recommendation_presets()
        console.print(f"[green]Found {len(presets)} preset configurations[/]")
        console.print()
        
        # Generate playlists for all presets
        format_list = [f.strip() for f in formats.split(',')]
        generated_playlists = generator.generate_preset_playlists(
            engine=engine,
            username=username,
            formats=format_list
        )
        
        # Display results
        console.print(f"[bold green]✅ Generated {len(generated_playlists)} playlists[/]")
        console.print()
        
        for preset_name, files in generated_playlists.items():
            console.print(f"[bold blue]🎵 {preset_name.replace('_', ' ').title()}[/]")
            for format_type, file_path in files.items():
                console.print(f"  • {format_type.upper()}: {file_path}")
            console.print()
        
        # Create summary
        summary_path = generator.create_playlist_summary(generated_playlists)
        console.print(f"[cyan]📋 Playlist summary saved to: {summary_path}[/]")
        
        # Show preset descriptions
        console.print()
        console.print("[bold blue]🎯 Available Presets:[/]")
        preset_descriptions = {
            'morning_energy': 'High-energy tracks for starting your day',
            'focus_work': 'Calm, medium-energy music for concentration',
            'evening_chill': 'Relaxing tracks for winding down',
            'weekend_discovery': 'Explore new music and artists',
            'nostalgic_favorites': 'Your most-played comfort tracks',
            'party_mix': 'High-energy tracks for social gatherings'
        }
        
        for preset_name in generated_playlists.keys():
            description = preset_descriptions.get(preset_name, 'Custom playlist')
            console.print(f"  • [bold]{preset_name.replace('_', ' ').title()}[/]: {description}")
        
    except Exception as e:
        console.print(f"[red]❌ Error generating preset playlists: {e}[/]")
        import traceback
        console.print(f"[red]Details: {traceback.format_exc()}[/]")
        sys.exit(1)

@cli.command()
def test_api():
    """Test your Last.fm API connection."""
    
    api_key = os.getenv('LASTFM_API_KEY')
    username = os.getenv('LASTFM_USERNAME')
    
    if not api_key:
        console.print("[red]❌ LASTFM_API_KEY not found in configuration![/]")
        return
    
    if not username:
        console.print("[red]❌ LASTFM_USERNAME not found in configuration![/]")
        return
    
    console.print("[bold blue]🧪 Testing Last.fm API connection...[/]")
    
    try:
        fetcher = LastFMFetcher(api_key=api_key, username=username)
        user_info = fetcher.get_user_info()
        
        console.print("[bold green]✅ API connection successful![/]")
        console.print(f"[green]User: {user_info['username']}[/]")
        console.print(f"[green]Total scrobbles: {user_info['total_scrobbles']:,}[/]")
        
        if user_info.get('real_name'):
            console.print(f"[green]Real name: {user_info['real_name']}[/]")
        
        if user_info.get('country'):
            console.print(f"[green]Country: {user_info['country']}[/]")
        
        # Check for AI API keys
        console.print()
        console.print("[bold blue]🤖 AI API Status:[/]")
        
        openai_key = os.getenv('OPENAI_API_KEY')
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        
        if openai_key:
            console.print("[green]✅ OpenAI API key configured[/]")
        else:
            console.print("[yellow]⚠️  OpenAI API key not found[/]")
        
        if anthropic_key:
            console.print("[green]✅ Anthropic API key configured[/]")
        else:
            console.print("[yellow]⚠️  Anthropic API key not found[/]")
        
        if not openai_key and not anthropic_key:
            console.print("[cyan]💡 Add AI API keys for enhanced insights![/]")
            
    except Exception as e:
        console.print(f"[red]❌ API test failed: {e}[/]")

@cli.command()
@click.option('--core-host', help='Roon Core IP address (overrides config)')
@click.option('--core-port', default=9100, help='Roon Core port (default: 9100)')
def roon_connect(core_host: Optional[str], core_port: int):
    """🎵 Connect to Roon Core and test the connection."""
    
    # Get Roon Core configuration
    core_host = core_host or os.getenv('ROON_CORE_HOST')
    if not core_host:
        console.print("[red]❌ ROON_CORE_HOST not found in configuration![/]")
        console.print("Either provide --core-host or set ROON_CORE_HOST in config.env")
        return
    
    console.print(f"[bold blue]🎵 Connecting to Roon Core at {core_host}:{core_port}...[/]")
    
    try:
        import asyncio
        from music_rec.exporters import RoonClient
        
        async def test_connection():
            client = RoonClient(core_host, core_port)
            success = await client.connect()
            
            if success:
                console.print("[bold green]✅ Successfully connected to Roon Core![/]")
                
                # Get zones
                zones = await client.get_zones()
                console.print(f"[green]Found {len(zones)} zones:[/]")
                
                for zone in zones:
                    status_icon = "🎵" if zone.state.value == "playing" else "⏸️" if zone.state.value == "paused" else "⏹️"
                    console.print(f"  {status_icon} {zone.display_name} ({zone.state.value})")
                    if zone.now_playing:
                        console.print(f"    Now playing: {zone.now_playing.get('title', 'Unknown')}")
                
                await client.disconnect()
            else:
                console.print("[red]❌ Failed to connect to Roon Core[/]")
                console.print("Make sure Roon Core is running and the IP address is correct.")
        
        asyncio.run(test_connection())
        
    except ImportError:
        console.print("[red]❌ Missing dependencies for Roon integration![/]")
        console.print("Install with: pip install websockets aiohttp")
    except Exception as e:
        console.print(f"[red]❌ Connection failed: {e}[/]")

@cli.command()
@click.option('--username', help='Last.fm username (overrides config)')
@click.option('--core-host', help='Roon Core IP address (overrides config)')
@click.option('--zone-id', help='Specific zone ID to create playlist for')
@click.option('--playlist-name', help='Custom playlist name')
@click.option('--mood', help='Mood preference (happy, sad, calm, energetic, etc.)')
@click.option('--energy-level', type=click.Choice(['low', 'medium', 'high']), help='Energy level preference')
@click.option('--discovery-level', type=float, default=0.3, help='Discovery level (0.0=familiar, 1.0=new)')
@click.option('--playlist-length', type=int, default=20, help='Number of tracks in playlist')
@click.option('--auto-play/--no-auto-play', default=True, help='Start playing immediately')
def roon_playlist(username: Optional[str], core_host: Optional[str], zone_id: Optional[str],
                 playlist_name: Optional[str], mood: Optional[str], energy_level: Optional[str],
                 discovery_level: float, playlist_length: int, auto_play: bool):
    """🎵 Create a recommendation playlist directly in Roon."""
    
    # Get configuration
    username = username or os.getenv('LASTFM_USERNAME')
    core_host = core_host or os.getenv('ROON_CORE_HOST')
    
    if not username:
        console.print("[red]❌ LASTFM_USERNAME not found in configuration![/]")
        return
    
    if not core_host:
        console.print("[red]❌ ROON_CORE_HOST not found in configuration![/]")
        return
    
    console.print(f"[bold blue]🎵 Creating Roon playlist for: {username}[/]")
    
    try:
        import asyncio
        from music_rec.exporters import RoonIntegration
        from music_rec.recommenders import RecommendationEngine, RecommendationRequest
        
        async def create_playlist():
            # Initialize components
            console.print("[cyan]🔧 Initializing recommendation engine...[/]")
            engine = RecommendationEngine(username=username)
            
            console.print("[cyan]🎵 Connecting to Roon Core...[/]")
            roon_integration = RoonIntegration(core_host, engine)
            
            success = await roon_integration.connect()
            if not success:
                console.print("[red]❌ Failed to connect to Roon Core[/]")
                return
            
            try:
                # Create recommendation request
                request = RecommendationRequest(
                    mood=mood,
                    energy_level=energy_level,
                    discovery_level=discovery_level,
                    playlist_length=playlist_length,
                    exclude_recent=True
                )
                
                # Generate playlist name if not provided
                if not playlist_name:
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
                    name = f"Music Rec - {timestamp}"
                    if mood:
                        name = f"Music Rec - {mood.title()} - {timestamp}"
                else:
                    name = playlist_name
                
                console.print(f"[cyan]🎵 Creating playlist: {name}[/]")
                
                # Create the playlist
                success = await roon_integration.create_recommendation_playlist(
                    request=request,
                    playlist_name=name,
                    zone_id=zone_id,
                    auto_play=auto_play
                )
                
                if success:
                    console.print(f"[bold green]✅ Successfully created playlist: {name}[/]")
                    if auto_play and zone_id:
                        console.print(f"[green]🎵 Started playing in zone: {zone_id}[/]")
                else:
                    console.print("[red]❌ Failed to create playlist[/]")
                
            finally:
                await roon_integration.disconnect()
        
        asyncio.run(create_playlist())
        
    except ImportError:
        console.print("[red]❌ Missing dependencies for Roon integration![/]")
        console.print("Install with: pip install websockets aiohttp")
    except Exception as e:
        console.print(f"[red]❌ Error creating playlist: {e}[/]")
        import traceback
        console.print(f"[red]Details: {traceback.format_exc()}[/]")

@cli.command()
@click.option('--username', help='Last.fm username (overrides config)')
@click.option('--core-host', help='Roon Core IP address (overrides config)')
def roon_zones(username: Optional[str], core_host: Optional[str]):
    """🎵 Show all Roon zones and their current status."""
    
    # Get configuration
    username = username or os.getenv('LASTFM_USERNAME')
    core_host = core_host or os.getenv('ROON_CORE_HOST')
    
    if not core_host:
        console.print("[red]❌ ROON_CORE_HOST not found in configuration![/]")
        return
    
    console.print(f"[bold blue]🎵 Roon Zone Status[/]")
    
    try:
        import asyncio
        from music_rec.exporters import RoonIntegration
        from music_rec.recommenders import RecommendationEngine
        
        async def show_zones():
            # Initialize components
            engine = RecommendationEngine(username=username) if username else None
            roon_integration = RoonIntegration(core_host, engine) if engine else None
            
            if not roon_integration:
                # Use basic client if no username
                from music_rec.exporters import RoonClient
                client = RoonClient(core_host)
                success = await client.connect()
                if not success:
                    console.print("[red]❌ Failed to connect to Roon Core[/]")
                    return
                
                zones = await client.get_zones()
                await client.disconnect()
            else:
                success = await roon_integration.connect()
                if not success:
                    console.print("[red]❌ Failed to connect to Roon Core[/]")
                    return
                
                status = await roon_integration.get_zone_status()
                zones_data = status.get('zones', {})
                await roon_integration.disconnect()
                
                # Display zone information
                console.print()
                for zone_id, zone_info in zones_data.items():
                    name = zone_info['name']
                    state = zone_info['state']
                    queue_remaining = zone_info['queue_remaining']
                    
                    status_icon = "🎵" if state == "playing" else "⏸️" if state == "paused" else "⏹️"
                    console.print(f"{status_icon} [bold]{name}[/] ({state})")
                    
                    if zone_info['now_playing']:
                        now_playing = zone_info['now_playing']
                        console.print(f"  Now playing: {now_playing.get('title', 'Unknown')}")
                    
                    console.print(f"  Queue remaining: {queue_remaining} tracks")
                    
                    # Show context if available
                    context = zone_info.get('context', {}).get('context', {})
                    if context:
                        room_type = context.get('room_type', 'unknown')
                        time_context = context.get('time_context', 'unknown')
                        console.print(f"  Context: {room_type} room, {time_context} time")
                    
                    console.print()
                
                return
            
            # Display basic zone information
            console.print()
            for zone in zones:
                status_icon = "🎵" if zone.state.value == "playing" else "⏸️" if zone.state.value == "paused" else "⏹️"
                console.print(f"{status_icon} [bold]{zone.display_name}[/] ({zone.state.value})")
                
                if zone.now_playing:
                    console.print(f"  Now playing: {zone.now_playing.get('title', 'Unknown')}")
                
                console.print(f"  Queue remaining: {zone.queue_items_remaining} tracks")
                console.print()
        
        asyncio.run(show_zones())
        
    except ImportError:
        console.print("[red]❌ Missing dependencies for Roon integration![/]")
        console.print("Install with: pip install websockets aiohttp")
    except Exception as e:
        console.print(f"[red]❌ Error getting zone status: {e}[/]")

@cli.command()
@click.option('--username', help='Last.fm username (overrides config)')
@click.option('--core-host', help='Roon Core IP address (overrides config)')
@click.option('--auto-sync/--no-auto-sync', default=True, help='Enable automatic playlist synchronization')
def roon_sync(username: Optional[str], core_host: Optional[str], auto_sync: bool):
    """🎵 Start Roon integration with automatic playlist sync."""
    
    # Get configuration
    username = username or os.getenv('LASTFM_USERNAME')
    core_host = core_host or os.getenv('ROON_CORE_HOST')
    
    if not username:
        console.print("[red]❌ LASTFM_USERNAME not found in configuration![/]")
        return
    
    if not core_host:
        console.print("[red]❌ ROON_CORE_HOST not found in configuration![/]")
        return
    
    console.print(f"[bold blue]🎵 Starting Roon integration for: {username}[/]")
    console.print(f"[cyan]Auto-sync: {'Enabled' if auto_sync else 'Disabled'}[/]")
    
    try:
        import asyncio
        from music_rec.exporters import RoonIntegration
        from music_rec.recommenders import RecommendationEngine
        
        async def run_sync():
            # Initialize components
            console.print("[cyan]🔧 Initializing recommendation engine...[/]")
            engine = RecommendationEngine(username=username)
            
            console.print("[cyan]🎵 Connecting to Roon Core...[/]")
            roon_integration = RoonIntegration(core_host, engine, auto_sync=auto_sync)
            
            success = await roon_integration.connect()
            if not success:
                console.print("[red]❌ Failed to connect to Roon Core[/]")
                return
            
            try:
                console.print("[bold green]✅ Roon integration active![/]")
                console.print("[cyan]Press Ctrl+C to stop...[/]")
                
                # Keep running and show periodic status
                while True:
                    await asyncio.sleep(30)  # Update every 30 seconds
                    
                    status = await roon_integration.get_zone_status()
                    active_playlists = status.get('active_playlists', 0)
                    last_sync = status.get('last_sync')
                    
                    console.print(f"[dim]Status: {active_playlists} active playlists, last sync: {last_sync or 'Never'}[/]")
                    
            except KeyboardInterrupt:
                console.print("\n[yellow]Stopping Roon integration...[/]")
            finally:
                await roon_integration.disconnect()
                console.print("[green]Disconnected from Roon Core[/]")
        
        asyncio.run(run_sync())
        
    except ImportError:
        console.print("[red]❌ Missing dependencies for Roon integration![/]")
        console.print("Install with: pip install websockets aiohttp")
    except Exception as e:
        console.print(f"[red]❌ Error in Roon sync: {e}[/]")

def show_summary(stats: dict):
    """Display a formatted summary of statistics."""
    console.print()
    console.print("[bold blue]📊 Data Summary[/]")
    
    table = Table(show_header=False, box=None)
    table.add_column("Metric", style="bold")
    table.add_column("Value", style="green")
    
    table.add_row("Total Scrobbles", f"{stats.get('total_scrobbles', 0):,}")
    table.add_row("Unique Tracks", f"{stats.get('unique_tracks', 0):,}")
    table.add_row("Unique Artists", f"{stats.get('unique_artists', 0):,}")
    table.add_row("Unique Albums", f"{stats.get('unique_albums', 0):,}")
    
    date_range = stats.get('date_range', {})
    if date_range.get('from') and date_range.get('to'):
        table.add_row("Date Range", f"{date_range['from'][:10]} to {date_range['to'][:10]}")
    
    if stats.get('last_updated'):
        table.add_row("Last Updated", stats['last_updated'][:19].replace('T', ' '))
    
    console.print(table)
    console.print()

def show_enrichment_summary(stats: dict, total_records: int):
    """Display enrichment statistics summary."""
    console.print()
    console.print("[bold blue]📊 Enrichment Statistics[/]")
    
    table = Table(show_header=False, box=None)
    table.add_column("Metric", style="bold")
    table.add_column("Value", style="green")
    
    table.add_row("Total Records", f"{total_records:,}")
    table.add_row("Successfully Enriched", f"{stats.get('successfully_enriched', 0):,}")
    table.add_row("MusicBrainz API Calls", f"{stats.get('api_calls', 0):,}")
    table.add_row("Cache Hits", f"{stats.get('cache_hits', 0):,}")
    table.add_row("Mood Classifications", f"{stats.get('mood_classified', 0):,}")
    table.add_row("Energy Classifications", f"{stats.get('energy_classified', 0):,}")
    
    if stats.get('start_time') and stats.get('end_time'):
        duration = stats['end_time'] - stats['start_time']
        table.add_row("Processing Time", str(duration).split('.')[0])
    
    console.print(table)

def show_enrichment_quality(quality_analysis: dict):
    """Display enrichment quality analysis."""
    console.print()
    console.print("[bold blue]📈 Enrichment Quality Analysis[/]")
    
    coverage = quality_analysis.get('coverage', {})
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Data Type", style="cyan")
    table.add_column("Coverage", style="green", justify="right")
    table.add_column("Quality", style="yellow")
    
    for field, data in coverage.items():
        percentage = data.get('percentage', 0)
        
        # Determine quality rating
        if percentage >= 80:
            quality = "🟢 Excellent"
        elif percentage >= 60:
            quality = "🟡 Good"
        elif percentage >= 40:
            quality = "🟠 Fair"
        else:
            quality = "🔴 Poor"
        
        field_name = field.replace('mb_', '').replace('_', ' ').title()
        table.add_row(field_name, f"{percentage:.1f}%", quality)
    
    console.print(table)
    
    # Show recommendations
    recommendations = quality_analysis.get('recommendations', [])
    if recommendations:
        console.print()
        console.print("[bold yellow]💡 Recommendations:[/]")
        for rec in recommendations:
            console.print(f"  • {rec}")

if __name__ == '__main__':
    cli()  