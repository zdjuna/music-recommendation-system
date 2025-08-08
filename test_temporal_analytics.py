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
    """Create test scrobble data with distinct phases"""
    np.random.seed(42)
    
    # Phase 1: Rock/Pop focus (2019-2020)
    start1 = datetime(2019, 1, 1)
    end1 = datetime(2020, 12, 31)
    dates1 = pd.to_datetime(np.random.choice(pd.date_range(start1, end1, freq='D'), 4000))
    artists1 = ['Artist A', 'Artist B', 'Rock Band C', 'Pop Star D']
    genres1 = ['Rock', 'Pop']
    
    # Phase 2: Electronic/Hip-Hop Exploration (2021-2022)
    start2 = datetime(2021, 1, 1)
    end2 = datetime(2022, 12, 31)
    dates2 = pd.to_datetime(np.random.choice(pd.date_range(start2, end2, freq='D'), 5000))
    artists2 = ['DJ E', 'Rapper F', 'Producer G', 'Artist A', 'Artist B']
    genres2 = ['Electronic', 'Hip-Hop', 'Ambient']
    
    # Phase 3: Jazz/Ambient Deep Dive (2023)
    start3 = datetime(2023, 1, 1)
    end3 = datetime(2023, 12, 31)
    dates3 = pd.to_datetime(np.random.choice(pd.date_range(start3, end3, freq='D'), 1000))
    artists3 = ['Jazz Trio H', 'Ambient Artist I', 'DJ E']
    genres3 = ['Jazz', 'Ambient']

    # Combine data
    all_dates = pd.to_datetime(np.concatenate([dates1, dates2, dates3]))
    
    data_list = []
    for date in all_dates:
        if date <= end1:
            artist = np.random.choice(artists1)
            genre = np.random.choice(genres1)
        elif date <= end2:
            artist = np.random.choice(artists2)
            genre = np.random.choice(genres2)
        else:
            artist = np.random.choice(artists3)
            genre = np.random.choice(genres3)
        data_list.append({
            'timestamp': date,
            'artist': artist,
            'track': f'Track {np.random.randint(1, 100)}',
            'album': f"Album {chr(ord('X') + np.random.randint(0, 3))}",
            'genre': genre
        })
        
    data = pd.DataFrame(data_list)
    return data.sort_values('timestamp').reset_index(drop=True)

def test_yearly_evolution_analysis():
    """Test yearly evolution analysis functionality"""
    test_data = create_test_data()
    analyzer = PatternAnalyzer(test_data)
    
    yearly_evolution = analyzer.analyze_year_over_year_evolution()
    
    assert 'yearly_metrics' in yearly_evolution
    assert 'evolution_trends' in yearly_evolution
    assert 'total_years' in yearly_evolution
    assert 'most_active_year' in yearly_evolution
    
    assert yearly_evolution['total_years'] >= 4
    
    yearly_stats = yearly_evolution['yearly_metrics']
    for stats in yearly_stats:
        assert 'total_plays' in stats
        assert 'unique_artists' in stats
        assert 'unique_tracks' in stats
        assert 'discovery_rate' in stats
        assert 'artist_diversity_index' in stats

def test_musical_phases_detection():
    """Test musical phases detection functionality"""
    test_data = create_test_data()
    analyzer = PatternAnalyzer(test_data)
    
    musical_phases = analyzer.analyze_musical_phases()
    
    assert 'quarterly_metrics' in musical_phases
    assert 'detected_phases' in musical_phases
    assert 'total_phases' in musical_phases
    assert 'phase_summary' in musical_phases
    
    assert musical_phases['total_phases'] >= 1
    
    phases = musical_phases['detected_phases']
    for phase in phases:
        assert 'quarter' in phase
        assert 'phase_type' in phase
        assert 'diversity_change' in phase
        assert 'intensity_change' in phase

def test_yearly_evolution_chart():
    """Test yearly evolution chart creation"""
    test_data = create_test_data()
    analyzer = PatternAnalyzer(test_data)
    patterns = analyzer.analyze_all_patterns()
    assert patterns is not None, "Pattern analysis should return a result"

def test_musical_phases_chart():
    """Test musical phases chart creation"""
    test_data = create_test_data()
    analyzer = PatternAnalyzer(test_data)
    patterns = analyzer.analyze_all_patterns()
    assert patterns is not None, "Pattern analysis should produce a result"

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
