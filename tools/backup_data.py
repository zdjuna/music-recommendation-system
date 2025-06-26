#!/usr/bin/env python3
"""
💾 Music Recommendation System - Data Backup Utility
Automated backup system for your precious music data
"""

import os
import shutil
import gzip
import json
from datetime import datetime
from pathlib import Path
import subprocess

def create_backup():
    """Create a comprehensive backup of all music data"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = Path(f"backups/backup_{timestamp}")
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    print("💾 Music Recommendation System - Data Backup")
    print("=" * 50)
    print(f"🕐 Backup started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 Backup location: {backup_dir}")
    print()
    
    total_size = 0
    files_backed_up = 0
    
    # Backup data directory
    data_dir = Path("data")
    if data_dir.exists():
        print("📊 Backing up data files...")
        backup_data_dir = backup_dir / "data"
        backup_data_dir.mkdir(exist_ok=True)
        
        for file in data_dir.glob("*"):
            if file.is_file():
                # Compress large CSV files
                if file.suffix == '.csv' and file.stat().st_size > 1024 * 1024:  # 1MB+
                    compressed_path = backup_data_dir / f"{file.name}.gz"
                    with open(file, 'rb') as f_in:
                        with gzip.open(compressed_path, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    size = compressed_path.stat().st_size
                    print(f"   ✅ {file.name} → {file.name}.gz ({size/1024/1024:.1f} MB)")
                else:
                    shutil.copy2(file, backup_data_dir)
                    size = file.stat().st_size
                    print(f"   ✅ {file.name} ({size/1024/1024:.1f} MB)")
                
                total_size += size
                files_backed_up += 1
    
    # Backup configuration
    config_files = ["config/config.env", ".env", "config/config_template.env"]
    print("\n⚙️ Backing up configuration...")
    backup_config_dir = backup_dir / "config"
    backup_config_dir.mkdir(exist_ok=True)
    
    for config_file in config_files:
        config_path = Path(config_file)
        if config_path.exists():
            shutil.copy2(config_path, backup_config_dir / config_path.name)
            print(f"   ✅ {config_file}")
            files_backed_up += 1
    
    # Backup playlists
    playlists_dir = Path("playlists")
    if playlists_dir.exists():
        print("\n🎵 Backing up playlists...")
        backup_playlists_dir = backup_dir / "playlists"
        shutil.copytree(playlists_dir, backup_playlists_dir)
        playlist_count = len(list(playlists_dir.glob("*")))
        print(f"   ✅ {playlist_count} playlist files")
        files_backed_up += playlist_count
    
    # Backup reports
    reports_dir = Path("reports")
    if reports_dir.exists():
        print("\n📊 Backing up reports...")
        backup_reports_dir = backup_dir / "reports"
        shutil.copytree(reports_dir, backup_reports_dir)
        report_count = len(list(reports_dir.glob("*")))
        print(f"   ✅ {report_count} report files")
        files_backed_up += report_count
    
    # Create backup manifest
    manifest = {
        "backup_timestamp": timestamp,
        "backup_date": datetime.now().isoformat(),
        "total_files": files_backed_up,
        "total_size_mb": total_size / 1024 / 1024,
        "directories_backed_up": [
            "data", "config", "playlists", "reports"
        ],
        "backup_location": str(backup_dir),
        "system_info": {
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "operating_system": os.name,
            "hostname": os.uname().nodename if hasattr(os, 'uname') else 'unknown'
        }
    }
    
    with open(backup_dir / "backup_manifest.json", 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print("\n📋 Backup Summary:")
    print(f"   📁 Files backed up: {files_backed_up}")
    print(f"   💾 Total size: {total_size/1024/1024:.1f} MB")
    print(f"   📍 Location: {backup_dir}")
    print(f"   🕐 Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Create quick restore script
    restore_script = backup_dir / "restore.py"
    with open(restore_script, 'w') as f:
        f.write(f'''#!/usr/bin/env python3
"""Auto-generated restore script for backup {timestamp}"""
import shutil
import gzip
from pathlib import Path

def restore():
    print("🔄 Restoring backup {timestamp}...")
    
    # Restore data (decompress if needed)
    data_backup = Path("data")
    if data_backup.exists():
        for file in data_backup.glob("*"):
            if file.suffix == '.gz':
                original_name = file.stem
                with gzip.open(file, 'rb') as f_in:
                    with open(Path("../../data") / original_name, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
            else:
                shutil.copy2(file, Path("../../data"))
    
    # Restore config
    if Path("config").exists():
        for file in Path("config").glob("*"):
            shutil.copy2(file, Path("../../config"))
    
    print("✅ Restore completed!")

if __name__ == "__main__":
    restore()
''')
    
    os.chmod(restore_script, 0o755)
    
    print(f"\n💡 To restore this backup, run:")
    print(f"   cd {backup_dir}")
    print(f"   python restore.py")
    
    return backup_dir

def cleanup_old_backups(keep_days=30):
    """Clean up backups older than specified days"""
    backups_dir = Path("backups")
    if not backups_dir.exists():
        return
    
    cutoff_date = datetime.now().timestamp() - (keep_days * 24 * 60 * 60)
    cleaned_count = 0
    
    for backup_folder in backups_dir.glob("backup_*"):
        if backup_folder.is_dir() and backup_folder.stat().st_mtime < cutoff_date:
            shutil.rmtree(backup_folder)
            cleaned_count += 1
            print(f"🗑️ Cleaned old backup: {backup_folder.name}")
    
    if cleaned_count == 0:
        print(f"✅ No old backups to clean (keeping {keep_days} days)")
    else:
        print(f"🗑️ Cleaned {cleaned_count} old backup(s)")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "cleanup":
        cleanup_old_backups()
    else:
        backup_location = create_backup()
        print("\n🎉 Backup completed successfully!")
        print("\n💡 Pro tips:")
        print("   • Run this script regularly to keep your data safe")
        print("   • Store backups in cloud storage for extra protection")
        print("   • Use 'python backup_data.py cleanup' to remove old backups")