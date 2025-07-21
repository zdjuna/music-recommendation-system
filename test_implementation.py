#!/usr/bin/env python3
"""
Test script to validate the enhanced temporal analytics implementation
"""

import sys
import os
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all new imports work correctly"""
    print("Testing imports...")
    
    try:
        from streamlit_app.pages.temporal_analytics import show_temporal_analytics
        print("✓ temporal_analytics import successful")
    except Exception as e:
        print(f"✗ temporal_analytics import failed: {e}")
        return False

    try:
        from streamlit_app.components.charts import create_yearly_evolution_chart, create_musical_phases_timeline
        print("✓ new chart functions import successful")
    except Exception as e:
        print(f"✗ new chart functions import failed: {e}")
        return False

    return True

def test_pattern_analyzer():
    """Test the enhanced PatternAnalyzer functionality"""
    print("\nTesting PatternAnalyzer enhancements...")
    
    try:
        from src.music_rec.analyzers.pattern_analyzer import PatternAnalyzer
        import pandas as pd
        
        test_data = pd.DataFrame({
            'artist': ['Test Artist'] * 10,
            'track_id': [f'track_{i}' for i in range(10)],
            'datetime': pd.date_range('2023-01-01', periods=10),
            'year': [2023] * 10,
            'quarter': [1] * 10
        })
        
        analyzer = PatternAnalyzer(test_data)
        result = analyzer.analyze_yearly_evolution()
        
        expected_keys = ['yearly_stats', 'year_over_year_changes', 'musical_phases']
        if all(key in result for key in expected_keys):
            print(f"✓ yearly evolution analysis successful: {len(result)} keys")
            return True
        else:
            print(f"✗ yearly evolution analysis missing keys: {result.keys()}")
            return False
            
    except Exception as e:
        print(f"✗ yearly evolution analysis failed: {e}")
        return False

def test_ai_insights():
    """Test the enhanced AI insights functionality"""
    print("\nTesting AI insights enhancements...")
    
    try:
        from src.music_rec.analyzers.ai_insights import AIInsightGenerator
        
        ai_generator = AIInsightGenerator()
        
        if hasattr(ai_generator, '_generate_temporal_evolution_insights'):
            print("✓ temporal evolution insights method exists")
            return True
        else:
            print("✗ temporal evolution insights method missing")
            return False
            
    except Exception as e:
        print(f"✗ AI insights test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Enhanced Temporal Analytics Implementation\n")
    
    tests = [
        test_imports,
        test_pattern_analyzer,
        test_ai_insights
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print(f"\n📊 Test Results: {sum(results)}/{len(results)} passed")
    
    if all(results):
        print("🎉 All tests passed! Implementation is ready.")
        return True
    else:
        print("❌ Some tests failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
