"""Test basic package imports and structure."""

import pytest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))


def test_package_import():
    """Test that the main package can be imported."""
    import music_rec
    assert music_rec.__version__ == "1.0.0"
    assert music_rec.__author__ == "Dr. Adam Zduńczyk"


def test_submodule_imports():
    """Test that main submodules can be imported."""
    try:
        import music_rec.data_fetchers
        import music_rec.analyzers
        import music_rec.enrichers
    except ImportError as e:
        pytest.fail(f"Failed to import submodules: {e}")


def test_cli_module_exists():
    """Test that CLI module exists."""
    try:
        import music_rec.cli
    except ImportError as e:
        pytest.fail(f"Failed to import CLI module: {e}")