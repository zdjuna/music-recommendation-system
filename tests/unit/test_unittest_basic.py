"""Basic unittest-compatible tests."""

import unittest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))


class TestBasicFunctionality(unittest.TestCase):
    """Basic functionality tests using unittest framework."""

    def test_package_import(self):
        """Test that the main package can be imported."""
        import music_rec
        self.assertEqual(music_rec.__version__, "1.0.0")
        self.assertEqual(music_rec.__author__, "Dr. Adam Zduńczyk")

    def test_python_version(self):
        """Test that we're running on a supported Python version."""
        self.assertGreaterEqual(sys.version_info, (3, 8), "Python 3.8+ is required")

    def test_project_structure(self):
        """Test that required project directories exist."""
        project_root = os.path.join(os.path.dirname(__file__), '..', '..')
        
        # Check that main directories exist
        self.assertTrue(os.path.exists(os.path.join(project_root, 'src')))
        self.assertTrue(os.path.exists(os.path.join(project_root, 'src', 'music_rec')))
        self.assertTrue(os.path.exists(os.path.join(project_root, 'tests')))


if __name__ == '__main__':
    unittest.main()