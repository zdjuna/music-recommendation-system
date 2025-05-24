#!/usr/bin/env python3
"""
🎵 Cyanite.ai Setup Helper
Easy setup and testing for Cyanite.ai music analysis API
"""

import os
import sys
from pathlib import Path

def print_banner():
    print("🎵" + "="*60 + "🎵")
    print("🎤  CYANITE.AI SETUP & TESTING HELPER  🎤")
    print("🎵" + "="*60 + "🎵")
    print()
    print("This script will help you:")
    print("✅ Get your Cyanite.ai API key")
    print("✅ Configure your environment")
    print("✅ Test the API connection")
    print("✅ Run your first mood analysis")
    print()

def show_registration_steps():
    print("📝 STEP 1: GET YOUR CYANITE.AI API KEY")
    print("-" * 50)
    print("1. 🌐 Go to: https://cyanite.ai/")
    print("2. 📧 Click 'Get Started' or 'Sign Up'")
    print("3. 📝 Create your free account")
    print("4. 🔑 Go to your Dashboard")
    print("5. ➕ Click 'Create Integration' or 'New Integration'")
    print("6. 📋 Fill out the integration form:")
    print("   • Name: 'Music Recommendation System'")
    print("   • Description: 'Personal music mood analysis'")
    print("   • Use case: 'Music Analysis & Recommendation'")
    print("7. 💾 Save the integration")
    print("8. 📋 Copy your API key/access token")
    print()
    print("💡 TIP: Look for 'API Key', 'Access Token', or 'Bearer Token'")
    print("🔒 The key usually starts with letters/numbers and is long")
    print()

def configure_api_key():
    print("🔧 STEP 2: CONFIGURE YOUR API KEY")
    print("-" * 50)
    
    api_key = input("🔑 Paste your Cyanite.ai API key here: ").strip()
    
    if not api_key:
        print("❌ No API key provided. Please try again.")
        return None
    
    # Update config file
    config_file = Path('config/config.env')
    
    if not config_file.exists():
        print("❌ Config file not found. Creating from template...")
        template_file = Path('config/config_template.env')
        if template_file.exists():
            import shutil
            shutil.copy(template_file, config_file)
        else:
            print("❌ No config template found!")
            return None
    
    # Read current config
    try:
        with open(config_file, 'r') as f:
            content = f.read()
        
        # Update Cyanite API key
        if 'CYANITE_API_KEY=' in content:
            # Replace existing key
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('CYANITE_API_KEY='):
                    lines[i] = f'CYANITE_API_KEY={api_key}'
                    break
            content = '\n'.join(lines)
        else:
            # Add new key
            content += f'\nCYANITE_API_KEY={api_key}\n'
        
        # Write back
        with open(config_file, 'w') as f:
            f.write(content)
        
        print(f"✅ API key saved to {config_file}")
        return api_key
        
    except Exception as e:
        print(f"❌ Error saving config: {e}")
        return None

def test_api_connection(api_key):
    print("🧪 STEP 3: TEST API CONNECTION")
    print("-" * 50)
    
    try:
        # Import test function
        sys.path.append('.')
        from test_cyanite_simple import test_cyanite_api
        
        # Temporarily set the API key for testing
        original_input = __builtins__['input']
        __builtins__['input'] = lambda prompt: api_key
        
        print("🔍 Testing with The Beatles - Hey Jude...")
        test_cyanite_api()
        
        # Restore original input function
        __builtins__['input'] = original_input
        
    except Exception as e:
        print(f"❌ Error running test: {e}")
        print("💡 You can test manually by running: python test_cyanite_simple.py")

def show_next_steps():
    print()
    print("🚀 NEXT STEPS")
    print("-" * 50)
    print("Now that Cyanite.ai is configured, you can:")
    print()
    print("1. 🌐 Launch the web app:")
    print("   python launch_web_app.py")
    print()
    print("2. 🎵 Enrich your music data:")
    print("   python enrich_with_cyanite.py")
    print()
    print("3. 📊 Run mood analysis:")
    print("   python cyanite_mood_enricher.py")
    print()
    print("4. 🎯 Generate mood-based playlists in the web interface!")
    print()
    print("💡 TIP: The web app now includes Cyanite-powered mood analysis")
    print("🎭 You'll see much more accurate mood classifications!")
    print()

def main():
    print_banner()
    
    # Check if already configured
    config_file = Path('config/config.env')
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                content = f.read()
                if 'CYANITE_API_KEY=' in content and 'your_cyanite_api_key_here' not in content:
                    print("✅ Cyanite.ai API key already configured!")
                    print("🧪 Would you like to test the connection? (y/n): ", end="")
                    if input().lower().startswith('y'):
                        # Extract API key
                        for line in content.split('\n'):
                            if line.startswith('CYANITE_API_KEY='):
                                api_key = line.split('=', 1)[1].strip()
                                test_api_connection(api_key)
                                break
                    show_next_steps()
                    return
        except Exception:
            pass
    
    # Show registration steps
    show_registration_steps()
    
    input("Press Enter when you have your API key...")
    
    # Configure API key
    api_key = configure_api_key()
    
    if api_key:
        print()
        test_api_connection(api_key)
        show_next_steps()
    
    print("🎵 Setup complete! Enjoy your enhanced music recommendations! 🎵")

if __name__ == "__main__":
    main() 