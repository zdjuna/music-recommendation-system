#!/usr/bin/env python3
"""
🔧 Music Recommendation System - Health Check
Comprehensive system health check for monitoring and troubleshooting
"""

import sys
import os
import json
import time
from pathlib import Path
from datetime import datetime
import subprocess

def check_python_version():
    """Check Python version compatibility"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 9:
        return True, f"✅ Python {version.major}.{version.minor}.{version.micro}"
    else:
        return False, f"❌ Python {version.major}.{version.minor}.{version.micro} (requires 3.9+)"

def check_dependencies():
    """Check if critical dependencies are available"""
    critical_deps = [
        'streamlit', 'pandas', 'numpy', 'plotly', 'requests',
        'openai', 'anthropic', 'rich', 'aiohttp'
    ]
    
    results = []
    for dep in critical_deps:
        try:
            __import__(dep)
            results.append(f"✅ {dep}")
        except ImportError:
            results.append(f"❌ {dep} - missing")
    
    return results

def check_data_files():
    """Check data directory and files"""
    data_dir = Path('data')
    if not data_dir.exists():
        return [f"❌ Data directory missing: {data_dir}"]
    
    results = [f"✅ Data directory exists: {data_dir}"]
    
    # Check for user data files
    csv_files = list(data_dir.glob("*_scrobbles.csv"))
    if csv_files:
        for file in csv_files:
            size_mb = file.stat().st_size / (1024 * 1024)
            results.append(f"✅ Scrobble data: {file.name} ({size_mb:.1f} MB)")
    else:
        results.append("⚠️ No scrobble data files found")
    
    return results

def check_config():
    """Check configuration files"""
    config_files = ['config/config.env', '.env']
    results = []
    
    for config_file in config_files:
        path = Path(config_file)
        if path.exists():
            results.append(f"✅ Config file: {config_file}")
            
            # Check for required keys
            try:
                with open(path) as f:
                    content = f.read()
                    required_keys = ['LASTFM_API_KEY', 'LASTFM_USERNAME']
                    for key in required_keys:
                        if f"{key}=" in content and "your_" not in content.split(f"{key}=")[1].split('\n')[0]:
                            results.append(f"✅ {key} configured")
                        else:
                            results.append(f"⚠️ {key} not configured")
            except Exception:
                results.append(f"⚠️ Could not parse {config_file}")
        else:
            results.append(f"❌ Config file missing: {config_file}")
    
    return results

def check_api_connectivity():
    """Basic API connectivity check"""
    results = []
    
    # Test Last.fm API
    try:
        import requests
        response = requests.get("https://ws.audioscrobbler.com/2.0/", timeout=5)
        if response.status_code == 200:
            results.append("✅ Last.fm API reachable")
        else:
            results.append(f"⚠️ Last.fm API returned {response.status_code}")
    except Exception as e:
        results.append(f"❌ Last.fm API unreachable: {e}")
    
    # Test Cyanite API
    try:
        response = requests.get("https://api.cyanite.ai/", timeout=5)
        results.append("✅ Cyanite.ai API reachable")
    except Exception as e:
        results.append(f"⚠️ Cyanite.ai API check failed: {e}")
    
    return results

def check_disk_space():
    """Check available disk space"""
    try:
        statvfs = os.statvfs('.')
        free_bytes = statvfs.f_frsize * statvfs.f_bavail
        free_gb = free_bytes / (1024**3)
        
        if free_gb > 1:
            return f"✅ Disk space: {free_gb:.1f} GB available"
        else:
            return f"⚠️ Low disk space: {free_gb:.1f} GB available"
    except Exception:
        return "⚠️ Could not check disk space"

def check_memory_usage():
    """Check system memory usage"""
    try:
        import psutil
        memory = psutil.virtual_memory()
        available_gb = memory.available / (1024**3)
        usage_percent = memory.percent
        
        if usage_percent < 80:
            return f"✅ Memory: {available_gb:.1f} GB available ({usage_percent:.1f}% used)"
        else:
            return f"⚠️ High memory usage: {usage_percent:.1f}% used"
    except ImportError:
        return "⚠️ psutil not available for memory check"
    except Exception as e:
        return f"⚠️ Memory check failed: {e}"

def run_health_check():
    """Run comprehensive health check"""
    print("🔧 Music Recommendation System - Health Check")
    print("=" * 60)
    print(f"🕐 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Python version
    print("🐍 Python Environment:")
    py_ok, py_msg = check_python_version()
    print(f"   {py_msg}")
    print()
    
    # Dependencies
    print("📦 Dependencies:")
    deps = check_dependencies()
    for dep in deps:
        print(f"   {dep}")
    print()
    
    # Configuration
    print("⚙️ Configuration:")
    config_results = check_config()
    for result in config_results:
        print(f"   {result}")
    print()
    
    # Data files
    print("📁 Data Files:")
    data_results = check_data_files()
    for result in data_results:
        print(f"   {result}")
    print()
    
    # API connectivity
    print("🌐 API Connectivity:")
    api_results = check_api_connectivity()
    for result in api_results:
        print(f"   {result}")
    print()
    
    # System resources
    print("💻 System Resources:")
    print(f"   {check_disk_space()}")
    print(f"   {check_memory_usage()}")
    print()
    
    # Overall status
    error_count = sum(1 for line in deps + config_results + data_results + api_results 
                     if line.startswith("❌"))
    warning_count = sum(1 for line in deps + config_results + data_results + api_results 
                       if line.startswith("⚠️"))
    
    print("📊 Overall Status:")
    if error_count == 0 and warning_count == 0:
        print("   🎉 All systems operational!")
    elif error_count == 0:
        print(f"   ✅ System functional with {warning_count} warnings")
    else:
        print(f"   ❌ {error_count} errors, {warning_count} warnings - needs attention")
    
    print()
    print("💡 For issues, check:")
    print("   • README.md for setup instructions")
    print("   • config/config_template.env for configuration examples")
    print("   • requirements.txt for dependency versions")

if __name__ == "__main__":
    run_health_check()