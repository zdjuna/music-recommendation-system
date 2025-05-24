"""
Music Recommendation System

A comprehensive AI-powered music recommendation system that fetches data from Last.fm,
enriches it with metadata from MusicBrainz, analyzes listening patterns, and provides
intelligent recommendations.
"""

__version__ = "1.0.0"
__author__ = "Dr. Adam Zduńczyk"

from . import data_fetchers, analyzers, enrichers 