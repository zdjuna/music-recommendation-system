#!/usr/bin/env python3
"""
Setup script for Musimap API trial integration
"""

import os
import sys
import requests
import json
from pathlib import Path

def print_banner():
    """Print setup banner"""
    print("=" * 60)
    print("🎵 MUSIMAP API TRIAL SETUP")
    print("=" * 60)
    print()

def print_step(step_num, title):
    """Print step header"""
    print(f"\n📋 STEP {step_num}: {title}")
    print("-" * 40)

def get_trial_signup_info():
    """Display trial signup information"""
    print_step(1, "SIGN UP FOR MUSIMAP TRIAL")
    
    print("🌐 Visit: https://www.musimap.com/")
    print("📝 Look for: '21 days free trial to discover our products!'")
    print("🔗 Click: 'I want to try!' button")
    print()
    print("📋 You'll need to provide:")
    print("   • Company/Organization name")
    print("   • Email address")
    print("   • Use case description")
    print("   • Contact information")
    print()
    print("💡 Tip: Mention you're building a music recommendation system")
    print("   and want to test MusiMotion for mood analysis.")
    print()
    
    input("Press Enter when you've completed the signup...")

def get_api_credentials():
    """Get API credentials from user"""
    print_step(2, "CONFIGURE API CREDENTIALS")
    
    print("After signing up, Musimap should provide you with:")
    print("   • Client ID")
    print("   • Client Secret")
    print("   • API documentation access")
    print()
    
    client_id = input("Enter your Musimap Client ID: ").strip()
    client_secret = input("Enter your Musimap Client Secret: ").strip()
    
    if not client_id or not client_secret:
        print("❌ Both Client ID and Client Secret are required!")
        return None, None
    
    return client_id, client_secret

def test_authentication(client_id, client_secret):
    """Test API authentication"""
    print_step(3, "TEST API AUTHENTICATION")
    
    print("🔐 Testing authentication with Musimap API...")
    
    auth_url = "https://api-v2.musimap.io/oauth/token"
    auth_data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret
    }
    
    try:
        response = requests.post(auth_url, data=auth_data, timeout=10)
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get('access_token')
            
            if access_token:
                print("✅ Authentication successful!")
                print(f"   Token type: {token_data.get('token_type', 'Bearer')}")
                print(f"   Expires in: {token_data.get('expires_in', 'Unknown')} seconds")
                return access_token
            else:
                print("❌ No access token received")
                return None
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return None

def save_credentials(client_id, client_secret):
    """Save credentials to .env file"""
    print_step(4, "SAVE CREDENTIALS")
    
    env_file = Path(".env")
    
    # Read existing .env file
    env_content = ""
    if env_file.exists():
        with open(env_file, 'r') as f:
            env_content = f.read()
    
    # Add Musimap credentials
    musimap_vars = f"""
# Musimap API Credentials
MUSIMAP_CLIENT_ID={client_id}
MUSIMAP_CLIENT_SECRET={client_secret}
"""
    
    # Check if Musimap vars already exist
    if "MUSIMAP_CLIENT_ID" in env_content:
        print("⚠️  Musimap credentials already exist in .env file")
        overwrite = input("Overwrite existing credentials? (y/n): ").lower().strip()
        if overwrite != 'y':
            print("Keeping existing credentials.")
            return
        
        # Remove existing Musimap credentials
        lines = env_content.split('\n')
        filtered_lines = []
        skip_next = False
        
        for line in lines:
            if line.startswith('MUSIMAP_') or line.strip() == "# Musimap API Credentials":
                continue
            filtered_lines.append(line)
        
        env_content = '\n'.join(filtered_lines)
    
    # Append new credentials
    with open(env_file, 'w') as f:
        f.write(env_content.rstrip() + musimap_vars)
    
    print("✅ Credentials saved to .env file")

def test_enricher():
    """Test the Musimap enricher"""
    print_step(5, "TEST MUSIMAP ENRICHER")
    
    print("🧪 Testing Musimap enricher with sample tracks...")
    
    try:
        from musimap_enricher import MusimapEnricher, MusimapConfig
        
        # Load credentials from environment
        client_id = os.getenv('MUSIMAP_CLIENT_ID')
        client_secret = os.getenv('MUSIMAP_CLIENT_SECRET')
        
        if not client_id or not client_secret:
            print("❌ Credentials not found in environment")
            return False
        
        # Initialize enricher
        config = MusimapConfig(client_id=client_id, client_secret=client_secret)
        enricher = MusimapEnricher(config)
        
        # Authenticate
        if not enricher.authenticate(client_id, client_secret):
            print("❌ Authentication failed")
            return False
        
        # Test with a simple track
        print("\n🎵 Testing with: The Beatles - Hey Jude")
        result = enricher.enrich_track("The Beatles", "Hey Jude")
        
        if result:
            print("✅ Enrichment successful!")
            print(f"   Moods: {result.get('musimap_moods', [])}")
            print(f"   Genres: {result.get('musimap_genres', [])}")
            print(f"   Primary mood: {result.get('primary_mood', 'Unknown')}")
            return True
        else:
            print("❌ Enrichment failed - track not found or API issue")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def create_hybrid_enricher():
    """Create a hybrid enricher that uses both MusicBrainz and Musimap"""
    print_step(6, "CREATE HYBRID ENRICHER")
    
    print("🔧 Creating hybrid enricher (MusicBrainz + Musimap)...")
    
    hybrid_code = '''#!/usr/bin/env python3
"""
Hybrid enricher using both MusicBrainz and Musimap
"""

import logging
from typing import Dict, List, Optional, Any
from musicbrainz_enricher import MusicBrainzEnricher
from musimap_enricher import MusimapEnricher, MusimapConfig
import os

class HybridEnricher:
    """
    Combines MusicBrainz (free, reliable) with Musimap (advanced mood analysis)
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize MusicBrainz enricher (always available)
        self.musicbrainz = MusicBrainzEnricher()
        
        # Initialize Musimap enricher (if credentials available)
        self.musimap = None
        self._setup_musimap()
    
    def _setup_musimap(self):
        """Setup Musimap enricher if credentials are available"""
        client_id = os.getenv('MUSIMAP_CLIENT_ID')
        client_secret = os.getenv('MUSIMAP_CLIENT_SECRET')
        
        if client_id and client_secret:
            try:
                config = MusimapConfig(client_id=client_id, client_secret=client_secret)
                self.musimap = MusimapEnricher(config)
                
                if self.musimap.authenticate(client_id, client_secret):
                    self.logger.info("Musimap enricher initialized successfully")
                else:
                    self.logger.warning("Musimap authentication failed")
                    self.musimap = None
            except Exception as e:
                self.logger.error(f"Failed to initialize Musimap: {e}")
                self.musimap = None
        else:
            self.logger.info("Musimap credentials not found, using MusicBrainz only")
    
    def enrich_track(self, artist: str, title: str) -> Optional[Dict[str, Any]]:
        """
        Enrich a track using both MusicBrainz and Musimap
        """
        # Start with MusicBrainz (reliable track identification)
        mb_result = self.musicbrainz.enrich_track(artist, title)
        
        if not mb_result:
            self.logger.warning(f"MusicBrainz failed to find: {artist} - {title}")
            return None
        
        # Enhance with Musimap if available
        if self.musimap:
            try:
                musimap_result = self.musimap.enrich_track(artist, title)
                if musimap_result:
                    # Merge results, prioritizing Musimap for mood/emotion data
                    enhanced_result = mb_result.copy()
                    enhanced_result.update({
                        'musimap_moods': musimap_result.get('musimap_moods', []),
                        'musimap_genres': musimap_result.get('musimap_genres', []),
                        'musimap_situations': musimap_result.get('musimap_situations', []),
                        'primary_mood': musimap_result.get('primary_mood'),
                        'mood_weights': musimap_result.get('mood_weights', {}),
                        'genre_weights': musimap_result.get('genre_weights', {}),
                        'situation_weights': musimap_result.get('situation_weights', {}),
                        'musimap_id': musimap_result.get('musimap_id'),
                        'energy': musimap_result.get('energy'),
                        'valence': musimap_result.get('valence'),
                        'danceability': musimap_result.get('danceability'),
                        'acousticness': musimap_result.get('acousticness'),
                    })
                    
                    # Update simplified mood with Musimap data
                    if musimap_result.get('primary_mood'):
                        enhanced_result['simplified_mood'] = musimap_result['primary_mood']
                    
                    self.logger.info(f"Enhanced {artist} - {title} with Musimap data")
                    return enhanced_result
                else:
                    self.logger.info(f"Musimap data not available for {artist} - {title}, using MusicBrainz only")
            except Exception as e:
                self.logger.error(f"Musimap enrichment failed for {artist} - {title}: {e}")
        
        return mb_result
    
    def enrich_tracks_batch(self, tracks: List[Dict[str, str]], max_tracks: int = 50) -> Dict[str, Dict[str, Any]]:
        """
        Enrich multiple tracks using hybrid approach
        """
        enriched_results = {}
        
        for i, track in enumerate(tracks[:max_tracks]):
            artist = track.get('artist', '').strip()
            title = track.get('title', '').strip()
            
            if not artist or not title:
                continue
            
            track_key = f"{artist} - {title}"
            
            try:
                result = self.enrich_track(artist, title)
                if result:
                    enriched_results[track_key] = result
                
                if (i + 1) % 10 == 0:
                    self.logger.info(f"Processed {i + 1} tracks")
                    
            except Exception as e:
                self.logger.error(f"Error enriching {track_key}: {e}")
                continue
        
        self.logger.info(f"Hybrid enrichment complete: {len(enriched_results)} tracks enriched")
        return enriched_results

def test_hybrid_enricher():
    """Test the hybrid enricher"""
    enricher = HybridEnricher()
    
    test_tracks = [
        {'artist': 'The Beatles', 'title': 'Hey Jude'},
        {'artist': 'Interpol', 'title': 'Evil'},
        {'artist': 'Queen', 'title': 'Bohemian Rhapsody'}
    ]
    
    print("Testing hybrid enricher...")
    for track in test_tracks:
        print(f"\\nTesting: {track['artist']} - {track['title']}")
        result = enricher.enrich_track(track['artist'], track['title'])
        if result:
            print(f"✅ MusicBrainz tags: {result.get('musicbrainz_tags', [])}")
            print(f"✅ Musimap moods: {result.get('musimap_moods', [])}")
            print(f"✅ Primary mood: {result.get('primary_mood', 'N/A')}")
        else:
            print("❌ Failed")

if __name__ == "__main__":
    test_hybrid_enricher()
'''
    
    with open('hybrid_enricher.py', 'w') as f:
        f.write(hybrid_code)
    
    print("✅ Created hybrid_enricher.py")
    print("   This combines MusicBrainz (reliable) + Musimap (advanced moods)")

def update_streamlit_app():
    """Show how to update the Streamlit app to use Musimap"""
    print_step(7, "UPDATE STREAMLIT APP")
    
    print("📝 To use Musimap in your Streamlit app:")
    print()
    print("1. Replace MusicBrainzEnricher with HybridEnricher in streamlit_app.py")
    print("2. Update the import statement:")
    print("   from hybrid_enricher import HybridEnricher")
    print()
    print("3. Change the enricher initialization:")
    print("   enricher = HybridEnricher()")
    print()
    print("4. The CSV output will now include Musimap fields:")
    print("   • musimap_moods")
    print("   • primary_mood") 
    print("   • mood_weights")
    print("   • energy, valence, danceability")
    print("   • musimap_situations")
    print()
    
    update_app = input("Would you like me to update streamlit_app.py automatically? (y/n): ").lower().strip()
    
    if update_app == 'y':
        try:
            # Read current streamlit app
            with open('streamlit_app.py', 'r') as f:
                content = f.read()
            
            # Make replacements
            updated_content = content.replace(
                'from musicbrainz_enricher import MusicBrainzEnricher',
                'from hybrid_enricher import HybridEnricher'
            ).replace(
                'enricher = MusicBrainzEnricher()',
                'enricher = HybridEnricher()'
            ).replace(
                'MusicBrainzEnricher()',
                'HybridEnricher()'
            )
            
            # Backup original
            with open('streamlit_app.py.backup', 'w') as f:
                f.write(content)
            
            # Write updated version
            with open('streamlit_app.py', 'w') as f:
                f.write(updated_content)
            
            print("✅ Updated streamlit_app.py (backup saved as streamlit_app.py.backup)")
            
        except Exception as e:
            print(f"❌ Failed to update automatically: {e}")
            print("Please update manually using the instructions above.")

def main():
    """Main setup function"""
    print_banner()
    
    print("This script will help you set up Musimap API integration")
    print("for advanced mood and emotion analysis in your music system.")
    print()
    
    # Step 1: Trial signup
    get_trial_signup_info()
    
    # Step 2: Get credentials
    client_id, client_secret = get_api_credentials()
    if not client_id or not client_secret:
        print("❌ Setup cancelled - credentials required")
        return
    
    # Step 3: Test authentication
    access_token = test_authentication(client_id, client_secret)
    if not access_token:
        print("❌ Setup failed - authentication error")
        return
    
    # Step 4: Save credentials
    save_credentials(client_id, client_secret)
    
    # Step 5: Test enricher
    test_success = test_enricher()
    
    # Step 6: Create hybrid enricher
    create_hybrid_enricher()
    
    # Step 7: Update Streamlit app
    update_streamlit_app()
    
    # Final summary
    print("\n" + "=" * 60)
    print("🎉 SETUP COMPLETE!")
    print("=" * 60)
    
    if test_success:
        print("✅ Musimap API is working correctly")
        print("✅ Hybrid enricher created (MusicBrainz + Musimap)")
        print("✅ Ready to process your music library with advanced mood analysis")
        print()
        print("🚀 Next steps:")
        print("   1. Run: python hybrid_enricher.py (to test)")
        print("   2. Run: streamlit run streamlit_app.py (to use in web app)")
        print("   3. Process your library with enhanced mood data!")
    else:
        print("⚠️  Basic setup complete, but testing failed")
        print("   You may need to check your trial account status")
        print("   or contact Musimap support for assistance")

if __name__ == "__main__":
    main() 