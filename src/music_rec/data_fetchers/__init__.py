"""Data fetchers for various music services."""

from .lastfm_fetcher import LastFMFetcher
from .musicbrainz_fetcher import MusicBrainzFetcher

__all__ = ['LastFMFetcher', 'MusicBrainzFetcher'] 