#!/usr/bin/env python3
"""
Roon Integration Setup Script

This script helps configure and test your Roon integration.
"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def setup_roon_config():
    """Interactive setup for Roon configuration"""
    print("🎵 Roon Integration Setup")
    print("=" * 50)
    
    config_file = Path('config/config.env')
    
    if not config_file.exists():
        print("📝 No configuration file found. Creating from template...")
        template_file = Path('config/config_template.env')
        if template_file.exists():
            import shutil
            shutil.copy(template_file, config_file)
            print(f"✅ Created {config_file}")
        else:
            print("❌ No template file found!")
            return False
    
    # Load existing config
    load_dotenv(config_file)
    
    print("\n📡 Roon Core Configuration:")
    print("To find your Roon Core IP address:")
    print("1. Open Roon app")
    print("2. Go to Settings > Setup")
    print("3. Look for 'Roon Core' information")
    print()
    
    current_host = os.getenv('ROON_CORE_HOST', '')
    current_port = os.getenv('ROON_CORE_PORT', '9100')
    
    if current_host:
        print(f"Current Roon Core Host: {current_host}")
        print(f"Current Roon Core Port: {current_port}")
        update = input("Update configuration? (y/n): ").lower().strip()
        if update != 'y':
            return True
    
    # Get new configuration
    while True:
        new_host = input("Enter Roon Core IP address (e.g., 192.168.1.100): ").strip()
        if new_host:
            break
        print("❌ IP address is required!")
    
    new_port = input(f"Enter Roon Core port [9100]: ").strip() or "9100"
    
    # Update config file
    config_content = config_file.read_text() if config_file.exists() else ""
    
    # Update or add Roon settings
    lines = config_content.split('\n')
    updated_lines = []
    host_found = False
    port_found = False
    
    for line in lines:
        if line.startswith('ROON_CORE_HOST='):
            updated_lines.append(f'ROON_CORE_HOST={new_host}')
            host_found = True
        elif line.startswith('ROON_CORE_PORT='):
            updated_lines.append(f'ROON_CORE_PORT={new_port}')
            port_found = True
        else:
            updated_lines.append(line)
    
    # Add if not found
    if not host_found:
        updated_lines.append(f'ROON_CORE_HOST={new_host}')
    if not port_found:
        updated_lines.append(f'ROON_CORE_PORT={new_port}')
    
    # Write back
    config_file.write_text('\n'.join(updated_lines))
    
    print(f"✅ Configuration saved to {config_file}")
    return True

async def test_roon_connection():
    """Test Roon connection"""
    print("\n🔧 Testing Roon Connection...")
    
    try:
        from music_rec.exporters import RoonClient
        
        core_host = os.getenv('ROON_CORE_HOST')
        core_port = int(os.getenv('ROON_CORE_PORT', '9100'))
        
        if not core_host:
            print("❌ No ROON_CORE_HOST configured!")
            return False
        
        print(f"📡 Connecting to {core_host}:{core_port}...")
        
        client = RoonClient(core_host, core_port)
        success = await client.connect()
        
        if success:
            print("✅ Connected successfully!")
            print("🎵 Please authorize the extension in Roon:")
            print("   1. Open Roon app")
            print("   2. Go to Settings > Extensions")
            print("   3. Find 'Music Recommendation System'")
            print("   4. Click 'Enable'")
            
            # Try to get zones
            zones = await client.get_zones()
            if zones:
                print(f"\n📺 Found {len(zones)} zone(s):")
                for zone in zones:
                    print(f"   - {zone.display_name} ({zone.state.value})")
            else:
                print("⚠️  No zones found (may need authorization)")
            
            await client.disconnect()
            return True
        else:
            print("❌ Connection failed!")
            print("\n🔧 Troubleshooting:")
            print("- Verify Roon Core is running")
            print("- Check IP address and port")
            print("- Ensure firewall allows connections")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def show_usage_examples():
    """Show usage examples"""
    print("\n📚 Roon Integration Usage Examples:")
    print("=" * 50)
    
    print("\n1. Test connection:")
    print("   python -m src.music_rec.cli roon-connect")
    
    print("\n2. Show zones:")
    print("   python -m src.music_rec.cli roon-zones")
    
    print("\n3. Create playlist:")
    print("   python -m src.music_rec.cli roon-playlist --mood energetic")
    
    print("\n4. Start auto-sync:")
    print("   python -m src.music_rec.cli roon-sync")
    
    print("\n5. Zone-specific playlist:")
    print("   python -m src.music_rec.cli roon-playlist --zone-id kitchen --auto-play")

async def main():
    """Main setup function"""
    print("🎵 Music Recommendation System - Roon Setup")
    print("=" * 60)
    
    # Step 1: Configure
    if not setup_roon_config():
        print("❌ Configuration setup failed!")
        return
    
    # Reload config
    load_dotenv('config/config.env')
    
    # Step 2: Test connection
    await test_roon_connection()
    
    # Step 3: Show usage
    show_usage_examples()
    
    print("\n" + "=" * 60)
    print("🎉 Roon integration setup completed!")
    print("\nNext steps:")
    print("1. Ensure you have Last.fm data: python -m src.music_rec.cli fetch")
    print("2. Test Roon commands: python -m src.music_rec.cli roon-connect")
    print("3. Create your first playlist: python -m src.music_rec.cli roon-playlist")

if __name__ == "__main__":
    asyncio.run(main())