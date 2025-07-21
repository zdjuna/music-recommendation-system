#!/usr/bin/env python3
"""
Test suite for enhanced temporal analytics functionality
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.music_rec.analyzers.pattern_analyzer import PatternAnalyzer
from streamlit_app.components.charts import create_yearly_evolution_chart, create_musical_phases_chart, create_temporal_heatmap_enhanced

def create_test_data():
    """Create test scrobble data spanning multiple years"""
    np.random.seed(42)
    
    start_date = datetime(2019, 1, 1)
    end_date = datetime(2023, 12, 31)
    
    dates = pd.date_range(start_date, end_date, freq='H')
    
    n_scrobbles = 10000
    random_dates = np.random.choice(dates, n_scrobbles)
    
    artists = ['Artist A', 'Artist B', 'Artist C', 'Artist D', 'Artist E'] * 2000
    tracks = ['Track 1', 'Track 2', 'Track 3', 'Track 4', 'Track 5'] * 2000
    albums = ['Album X', 'Album Y', 'Album Z'] * 3334
    
    data = pd.DataFrame({
        'timestamp': random_dates,
        'artist': np.random.choice(artists, n_scrobbles),
        'track': np.random.choice(tracks, n_scrobbles),
        'album': np.random.choice(albums, n_scrobbles)
    })
    
    return data.sort_values('timestamp').reset_index(drop=True)

def test_yearly_evolution_analysis():
    """Test yearly evolution analysis functionality"""
    test_data = create_test_data()
    analyzer = PatternAnalyzer(test_data)
    
    yearly_evolution = analyzer.analyze_yearly_evolution()
    
    assert 'yearly_stats' in yearly_evolution
    assert 'evolution_metrics' in yearly_evolution
    assert 'total_years' in yearly_evolution
    assert 'most_active_year' in yearly_evolution
    
    assert yearly_evolution['total_years'] >= 4
    
    yearly_stats = yearly_evolution['yearly_stats']
    for year, stats in yearly_stats.items():
        assert 'total_scrobbles' in stats
        assert 'unique_artists' in stats
        assert 'unique_tracks' in stats
        assert 'discovery_rate' in stats
        assert 'artist_diversity' in stats

def test_musical_phases_detection():
    """Test musical phases detection functionality"""
    test_data = create_test_data()
    analyzer = PatternAnalyzer(test_data)
    
    musical_phases = analyzer.detect_musical_phases()
    
    assert 'phases' in musical_phases
    assert 'total_phases' in musical_phases
    assert 'current_phase' in musical_phases
    assert 'phase_summary' in musical_phases
    
    assert musical_phases['total_phases'] >= 1
    
    phases = musical_phases['phases']
    for phase in phases:
        assert 'start' in phase
        assert 'end' in phase
        assert 'type' in phase
        assert 'description' in phase
        assert 'characteristics' in phase

def test_yearly_evolution_chart():
    """Test yearly evolution chart creation"""
    test_data = create_test_data()
    analyzer = PatternAnalyzer(test_data)
    patterns = analyzer.analyze_all_patterns()
    
    fig = create_yearly_evolution_chart(patterns)
    
    assert fig is not None
    assert hasattr(fig, 'data')
    assert len(fig.data) > 0

def test_musical_phases_chart():
    """Test musical phases chart creation"""
    test_data = create_test_data()
    analyzer = PatternAnalyzer(test_data)
    patterns = analyzer.analyze_all_patterns()
    
    fig = create_musical_phases_chart(patterns)
    
    assert fig is not None
    assert hasattr(fig, 'data')

def test_temporal_heatmap_enhanced():
    """Test enhanced temporal heatmap creation"""
    test_data = create_test_data()
    
    fig = create_temporal_heatmap_enhanced(test_data)
    
    assert fig is not None
    assert hasattr(fig, 'data')
    assert len(fig.data) > 0

if __name__ == "__main__":
    print("Running temporal analytics tests...")
    
    test_yearly_evolution_analysis()
    print("✅ Yearly evolution analysis test passed")
    
    test_musical_phases_detection()
    print("✅ Musical phases detection test passed")
    
    test_yearly_evolution_chart()
    print("✅ Yearly evolution chart test passed")
    
    test_musical_phases_chart()
    print("✅ Musical phases chart test passed")
    
    test_temporal_heatmap_enhanced()
    print("✅ Enhanced temporal heatmap test passed")
    
    print("🎉 All temporal analytics tests passed!")
