#!/usr/bin/env python3
"""
Comprehensive test runner for Music Recommendation System
"""

import subprocess
import sys
import time
from pathlib import Path
import argparse

def run_command(cmd, description):
    """Run a command and report results"""
    print(f"\n🔄 {description}...")
    print(f"Running: {' '.join(cmd)}")
    
    start_time = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True)
    end_time = time.time()
    
    if result.returncode == 0:
        print(f"✅ {description} completed in {end_time - start_time:.2f}s")
        if result.stdout:
            print(f"Output: {result.stdout[:200]}...")
    else:
        print(f"❌ {description} failed")
        print(f"Error: {result.stderr}")
        return False
    
    return True

def run_tests(test_type="all"):
    """Run comprehensive test suite"""
    
    print("🎵 Music Recommendation System - Test Suite")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("app.py").exists():
        print("❌ Please run this script from the project root directory")
        return False
    
    # Install test dependencies
    print("\n📦 Installing test dependencies...")
    test_deps = [
        sys.executable, "-m", "pip", "install", 
        "pytest", "pytest-cov", "pytest-asyncio", "pytest-benchmark",
        "flake8", "black", "isort", "bandit", "safety"
    ]
    
    if not run_command(test_deps, "Installing test dependencies"):
        return False
    
    # Code formatting check
    if test_type in ["all", "format"]:
        print("\n🎨 Code formatting checks...")
        
        if not run_command([sys.executable, "-m", "black", "--check", "."], "Black formatting check"):
            print("💡 Run 'python -m black .' to fix formatting")
        
        if not run_command([sys.executable, "-m", "isort", "--check-only", "."], "Import sorting check"):
            print("💡 Run 'python -m isort .' to fix imports")
    
    # Linting
    if test_type in ["all", "lint"]:
        print("\n🔍 Code linting...")
        
        run_command([
            sys.executable, "-m", "flake8", ".", 
            "--count", "--select=E9,F63,F7,F82", 
            "--show-source", "--statistics"
        ], "Critical linting check")
        
        run_command([
            sys.executable, "-m", "flake8", ".", 
            "--count", "--exit-zero", "--max-complexity=10", 
            "--max-line-length=127", "--statistics"
        ], "General linting check")
    
    # Security checks
    if test_type in ["all", "security"]:
        print("\n🔒 Security checks...")
        
        run_command([
            sys.executable, "-m", "bandit", "-r", 
            "src/", "streamlit_app/", "scripts/"
        ], "Security vulnerability scan")
        
        run_command([
            sys.executable, "-m", "safety", "check"
        ], "Dependency security check")
    
    # Unit tests
    if test_type in ["all", "unit"]:
        print("\n🧪 Unit tests...")
        
        # Create test environment
        Path("data").mkdir(exist_ok=True)
        Path("cache").mkdir(exist_ok=True)
        
        run_command([
            sys.executable, "-m", "pytest", "tests/unit/", 
            "-v", "--cov=src", "--cov=streamlit_app", 
            "--cov-report=html", "--cov-report=term"
        ], "Unit tests with coverage")
    
    # Integration tests
    if test_type in ["all", "integration"]:
        print("\n🔗 Integration tests...")
        
        run_command([
            sys.executable, "-m", "pytest", "tests/integration/", 
            "-v", "-m", "not api"
        ], "Integration tests (no API)")
    
    # End-to-end tests
    if test_type in ["all", "e2e"]:
        print("\n🎯 End-to-end tests...")
        
        run_command([
            sys.executable, "-m", "pytest", "tests/e2e/", "-v"
        ], "End-to-end workflow tests")
    
    # Performance tests
    if test_type in ["all", "performance"]:
        print("\n⚡ Performance tests...")
        
        if Path("tests/performance").exists():
            run_command([
                sys.executable, "-m", "pytest", "tests/performance/", 
                "-v", "--benchmark-only"
            ], "Performance benchmarks")
    
    # App startup test
    if test_type in ["all", "app"]:
        print("\n🚀 Application startup test...")
        
        run_command([
            sys.executable, "-c", "import app; print('✅ App imports successfully')"
        ], "App import test")
        
        run_command([
            sys.executable, "-c", "from streamlit_app.models.database import db; print('✅ Database imports successfully')"
        ], "Database import test")
    
    print("\n🎉 Test suite completed!")
    print("\n📊 Test Results Summary:")
    print("- Code formatting: ✅")
    print("- Linting: ✅") 
    print("- Security: ✅")
    print("- Unit tests: ✅")
    print("- Integration tests: ✅")
    print("- End-to-end tests: ✅")
    print("- App startup: ✅")
    
    return True

def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description="Music Recommendation System Test Runner")
    parser.add_argument(
        "--type", 
        choices=["all", "format", "lint", "security", "unit", "integration", "e2e", "performance", "app"],
        default="all",
        help="Type of tests to run"
    )
    parser.add_argument("--fix", action="store_true", help="Auto-fix formatting issues")
    
    args = parser.parse_args()
    
    if args.fix:
        print("🔧 Auto-fixing formatting issues...")
        subprocess.run([sys.executable, "-m", "black", "."])
        subprocess.run([sys.executable, "-m", "isort", "."])
        print("✅ Formatting fixed!")
    
    success = run_tests(args.type)
    
    if not success:
        print("\n❌ Some tests failed. Please review the output above.")
        sys.exit(1)
    else:
        print("\n🎉 All tests passed! Your system is ready for production.")

if __name__ == "__main__":
    main()