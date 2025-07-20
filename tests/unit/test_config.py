"""Test configuration and environment setup."""

import pytest
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))


def test_environment_variables():
    """Test that environment variables can be set and read."""
    # Test setting and getting an environment variable
    test_key = "TEST_MUSIC_REC_VAR"
    test_value = "test_value_123"
    
    os.environ[test_key] = test_value
    assert os.environ.get(test_key) == test_value
    
    # Clean up
    del os.environ[test_key]


def test_python_version():
    """Test that we're running on a supported Python version."""
    assert sys.version_info >= (3, 8), "Python 3.8+ is required"


def test_required_directories_exist():
    """Test that required project directories exist."""
    project_root = os.path.join(os.path.dirname(__file__), '..', '..')
    
    # Check that main directories exist
    assert os.path.exists(os.path.join(project_root, 'src'))
    assert os.path.exists(os.path.join(project_root, 'src', 'music_rec'))
    assert os.path.exists(os.path.join(project_root, 'tests'))