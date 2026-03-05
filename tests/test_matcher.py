"""Tests for library matcher engine."""

import pytest
from datetime import datetime

from retrotv.models.guide import GuideEntry, NormalizedGuideEntry
from retrotv.models.media import (
    MediaLibrary, Series, Episode, Movie, MediaSource, MediaType,
)
from retrotv.models.schedule import MatchStatus
from retrotv.matching.matcher import LibraryMatcher, MatchResult


def _make_entry(title, normalized, duration_minutes=30, season=None, episode=None, episode_title=None):
    """Helper to create a NormalizedGuideEntry for tests."""
    entry = GuideEntry(
        title=title,
        start_time=datetime(1990, 1, 1, 20, 0),
        duration_minutes=duration_minutes,
        season_number=season,
        episode_number=episode,
        episode_title=episode_title,
    )
    return NormalizedGuideEntry(original=entry, normalized_title=normalized)


def _make_library():
    """Build a small test library."""
    library = MediaLibrary(source=MediaSource.JELLYFIN)

    ep1 = Episode(
        id="ep1", source=MediaSource.JELLYFIN, title="Seinfeld",
        normalized_title="seinfeld", media_type=MediaType.EPISODE,
        runtime_seconds=22 * 60, series_id="s1", series_title="Seinfeld",
        season_number=1, episode_number=1, episode_title="The Seinfeld Chronicles",
    )
    ep2 = Episode(
        id="ep2", source=MediaSource.JELLYFIN, title="Seinfeld",
        normalized_title="seinfeld", media_type=MediaType.EPISODE,
        runtime_seconds=22 * 60, series_id="s1", series_title="Seinfeld",
        season_number=1, episode_number=2, episode_title="The Stake Out",
    )
    series = Series(
        id="s1", source=MediaSource.JELLYFIN, title="Seinfeld",
        normalized_title="seinfeld", genres=["Comedy"],
        seasons={1: [ep1, ep2]}, total_episodes=2,
    )
    library.series["seinfeld"] = series

    movie = Movie(
        id="m1", source=MediaSource.JELLYFIN, title="Ghostbusters",
        normalized_title="ghostbusters", media_type=MediaType.MOVIE,
        runtime_seconds=105 * 60, year=1984, genres=["Comedy", "Fantasy"],
    )
    library.movies["ghostbusters"] = movie

    return library


class TestLibraryMatcher:
    """Test suite for LibraryMatcher."""

    def test_exact_series_episode_match(self):
        library = _make_library()
        matcher = LibraryMatcher(library, fuzzy_threshold=70)
        entry = _make_entry("Seinfeld", "seinfeld", season=1, episode=1)
        result = matcher.match_entry(entry)
        assert result.status == MatchStatus.MATCHED
        assert result.matched_item.id == "ep1"

    def test_series_partial_match_no_episode_info(self):
        library = _make_library()
        matcher = LibraryMatcher(library, fuzzy_threshold=70)
        entry = _make_entry("Seinfeld", "seinfeld", duration_minutes=22)
        result = matcher.match_entry(entry)
        assert result.status in (MatchStatus.MATCHED, MatchStatus.PARTIAL)
        assert result.matched_item is not None

    def test_movie_match(self):
        library = _make_library()
        matcher = LibraryMatcher(library, fuzzy_threshold=70)
        entry = _make_entry("Ghostbusters", "ghostbusters", duration_minutes=120)
        result = matcher.match_entry(entry)
        assert result.status in (MatchStatus.MATCHED, MatchStatus.PARTIAL)
        assert result.matched_item.id == "m1"

    def test_no_match_returns_missing(self):
        library = _make_library()
        matcher = LibraryMatcher(library, fuzzy_threshold=70)
        entry = _make_entry("Unknown Show XYZ", "unknown show xyz")
        result = matcher.match_entry(entry)
        assert result.status == MatchStatus.MISSING

    def test_match_all_returns_list(self):
        library = _make_library()
        matcher = LibraryMatcher(library, fuzzy_threshold=70)
        entries = [
            _make_entry("Seinfeld", "seinfeld", season=1, episode=1),
            _make_entry("Unknown", "unknown"),
        ]
        results = matcher.match_all(entries)
        assert len(results) == 2
        assert results[0].status == MatchStatus.MATCHED
        assert results[1].status == MatchStatus.MISSING

    def test_match_statistics(self):
        library = _make_library()
        matcher = LibraryMatcher(library, fuzzy_threshold=70)
        entries = [
            _make_entry("Seinfeld", "seinfeld", season=1, episode=1),
            _make_entry("Unknown", "unknown"),
        ]
        results = matcher.match_all(entries)
        stats = matcher.get_match_statistics(results)
        assert stats["total"] == 2
        assert stats["matched"] == 1
        assert stats["missing"] == 1
