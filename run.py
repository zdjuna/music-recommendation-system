#!/usr/bin/env python3
"""
Simple runner script for the Music Recommendation System v5.0

For busy professionals who just want to run the system without remembering commands.
"""

import sys
import subprocess
from pathlib import Path

def main():
    """Main entry point with simple menu."""
    
    print("🎵 Music Recommendation System v5.0")
    print("=" * 45)
    print()
    print("Choose an option:")
    print("1. Setup (first time)")
    print("2. Test API connection")
    print("3. Fetch my music data")
    print("4. Update with new scrobbles")
    print("5. Show statistics")
    print()
    print("🧠 AI ANALYSIS:")
    print("6. Analyze my music patterns")
    print("7. Quick insights (30 seconds)")
    print()
    print("🎯 RECOMMENDATIONS:")
    print("8. Generate custom playlist")
    print("9. Generate all preset playlists")
    print()
    print("🎵 ROON INTEGRATION (NEW!):")
    print("10. Test Roon connection")
    print("11. Show Roon zones")
    print("12. Create Roon playlist")
    print("13. Start Roon auto-sync")
    print()
    print("14. Help")
    print("0. Exit")
    print()
    
    while True:
        try:
            choice = input("Enter your choice (0-14): ").strip()
            
            if choice == '0':
                print("Goodbye! 🎧")
                break
            elif choice == '1':
                run_command(['python', '-m', 'src.music_rec.cli', 'setup'])
            elif choice == '2':
                run_command(['python', '-m', 'src.music_rec.cli', 'test-api'])
            elif choice == '3':
                print("\n🎵 This will fetch ALL your Last.fm data (may take 30-60 minutes for 430k+ scrobbles)")
                if input("Continue? (y/N): ").lower().startswith('y'):
                    run_command(['python', '-m', 'src.music_rec.cli', 'fetch', '--full'])
            elif choice == '4':
                run_command(['python', '-m', 'src.music_rec.cli', 'fetch', '--incremental'])
            elif choice == '5':
                run_command(['python', '-m', 'src.music_rec.cli', 'stats'])
            elif choice == '6':
                print("\n🧠 This will analyze your music patterns and generate AI insights")
                print("   Choose analysis type:")
                print("   a) Full AI analysis (requires OpenAI/Anthropic API key)")
                print("   b) Basic analysis (no AI key needed)")
                
                try:
                    analysis_choice = input("Enter choice (a/b): ").strip().lower()
                    if analysis_choice == 'a':
                        run_command(['python', '-m', 'src.music_rec.cli', 'analyze', '--ai'])
                    elif analysis_choice == 'b':
                        run_command(['python', '-m', 'src.music_rec.cli', 'analyze', '--no-ai'])
                    else:
                        print("Invalid choice.")
                except EOFError:
                    print("\nGoodbye! 🎧")
                    break
            elif choice == '7':
                run_command(['python', '-m', 'src.music_rec.cli', 'quick-insights'])
            elif choice == '8':
                print("\n🎯 Generate a custom recommendation playlist")
                mood = input("Mood (optional, e.g., happy, calm, energetic): ").strip() or None
                energy = input("Energy level (optional: low, medium, high): ").strip() or None
                length = input("Playlist length (default 20): ").strip() or "20"
                
                cmd = ['python', '-m', 'src.music_rec.cli', 'recommend', '--playlist-length', length]
                if mood:
                    cmd.extend(['--mood', mood])
                if energy:
                    cmd.extend(['--energy-level', energy])
                
                run_command(cmd)
            elif choice == '9':
                run_command(['python', '-m', 'src.music_rec.cli', 'generate-presets'])
            elif choice == '10':
                run_command(['python', '-m', 'src.music_rec.cli', 'roon-connect'])
            elif choice == '11':
                run_command(['python', '-m', 'src.music_rec.cli', 'roon-zones'])
            elif choice == '12':
                print("\n🎵 Create a playlist directly in Roon")
                playlist_name = input("Playlist name (optional): ").strip() or None
                mood = input("Mood (optional, e.g., happy, calm, energetic): ").strip() or None
                energy = input("Energy level (optional: low, medium, high): ").strip() or None
                length = input("Playlist length (default 20): ").strip() or "20"
                
                cmd = ['python', '-m', 'src.music_rec.cli', 'roon-playlist', '--playlist-length', length]
                if playlist_name:
                    cmd.extend(['--playlist-name', playlist_name])
                if mood:
                    cmd.extend(['--mood', mood])
                if energy:
                    cmd.extend(['--energy-level', energy])
                
                run_command(cmd)
            elif choice == '13':
                print("\n🔄 Starting Roon auto-sync (press Ctrl+C to stop)")
                if input("Continue? (y/N): ").lower().startswith('y'):
                    run_command(['python', '-m', 'src.music_rec.cli', 'roon-sync'])
            elif choice == '14':
                show_help()
            else:
                print("Invalid choice. Please enter 0-14.")
                
        except KeyboardInterrupt:
            print("\n\nGoodbye! 🎧")
            break
        except EOFError:
            print("\nGoodbye! 🎧")
            break
        except Exception as e:
            print(f"Error: {e}")
            
        print()  # Add spacing between runs

def run_command(cmd):
    """Run a command and handle errors gracefully."""
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}")
    except FileNotFoundError:
        print("Error: Python not found. Make sure Python is installed and in your PATH.")

def show_help():
    """Show help information."""
    print()
    print("🆘 Quick Help:")
    print()
    print("FIRST TIME SETUP:")
    print("1. Choose option 1 to setup configuration")
    print("2. Get Last.fm API key from: https://www.last.fm/api/account/create")
    print("3. Edit config/config.env with your credentials")
    print("4. Choose option 2 to test your connection")
    print("5. Choose option 3 to fetch all your data")
    print()
    print("REGULAR USE:")
    print("- Choose option 4 to get new scrobbles (recommended)")
    print("- Choose option 5 to see your listening statistics")
    print()
    print("AI ANALYSIS:")
    print("- Choose option 6 for comprehensive AI-powered analysis")
    print("- Choose option 7 for quick insights (no setup needed)")
    print("- Get insights about your musical personality!")
    print("- Discover patterns in your listening habits")
    print("- Receive personalized recommendations")
    print()
    print("RECOMMENDATIONS:")
    print("- Choose option 8 for custom playlists with mood/energy preferences")
    print("- Choose option 9 to generate all preset playlists")
    print("- Presets include: Morning Energy, Focus Work, Evening Chill, etc.")
    print("- Export to JSON, CSV, M3U, or Roon formats")
    print()
    print("NEW IN V5.0 - ROON INTEGRATION:")
    print("- Choose option 10 to test connection to your Roon Core")
    print("- Choose option 11 to see all your Roon zones and their status")
    print("- Choose option 12 to create playlists directly in Roon")
    print("- Choose option 13 for automatic playlist sync (keeps running)")
    print("- Context-aware recommendations based on room type and time")
    print("- Automatic playlist updates when queue runs low")
    print()
    print("ROON SETUP:")
    print("1. Add ROON_CORE_HOST=your_roon_ip to config/config.env")
    print("2. Make sure Roon Core is running on your network")
    print("3. Test connection with option 10")
    print("4. Authorize the app in Roon's Settings > Extensions")
    print()
    print("AI ANALYSIS FEATURES:")
    print("• Musical personality analysis")
    print("• Listening behavior insights") 
    print("• Discovery pattern analysis")
    print("• Temporal pattern recognition")
    print("• Personalized recommendations")
    print("• Beautiful reports (HTML, JSON)")
    print()
    print("OPTIONAL ENHANCEMENTS:")
    print("For enhanced insights, add API keys to config/config.env:")
    print("- OPENAI_API_KEY for GPT-powered analysis")
    print("- ANTHROPIC_API_KEY for Claude-powered analysis")
    print("- ROON_CORE_HOST for direct Roon integration")
    print("(Basic analysis works without these)")
    print()
    print("For more detailed help, see README.md")

if __name__ == '__main__':
    main() 