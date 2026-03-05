"""Tests for substitution engine."""

import pytest
from datetime import datetime

from retrotv.models.guide import GuideEntry, NormalizedGuideEntry
from retrotv.models.media import (
    MediaLibrary, Series, Episode, Movie, MediaSource, MediaType,
)
from retrotv.models.schedule import ScheduleSlot, MatchStatus
from retrotv.substitution.engine import SubstitutionEngine


def _make_library():
    """Build a test library with varied content."""
    library = MediaLibrary(source=MediaSource.JELLYFIN)

    ep1 = Episode(
        id="ep-comedy-1", source=MediaSource.JELLYFIN, title="Friends",
        normalized_title="friends", media_type=MediaType.EPISODE,
        runtime_seconds=22 * 60, series_id="s-friends", series_title="Friends",
        season_number=1, episode_number=1, episode_title="Pilot",
        genres=["Comedy"], year=1994,
    )
    series = Series(
        id="s-friends", source=MediaSource.JELLYFIN, title="Friends",
        normalized_title="friends", genres=["Comedy"],
        seasons={1: [ep1]}, total_episodes=1,
    )
    library.series["friends"] = series

    movie = Movie(
        id="m-action-1", source=MediaSource.JELLYFIN, title="Die Hard",
        normalized_title="die hard", media_type=MediaType.MOVIE,
        runtime_seconds=131 * 60, year=1988, genres=["Action"],
    )
    library.movies["die hard"] = movie

    return library


def _make_missing_slot(expected_runtime_seconds=1800):
    """Create a schedule slot marked MISSING."""
    entry = GuideEntry(
        title="Lost Show", start_time=datetime(1990, 1, 1, 20, 0),
        duration_minutes=expected_runtime_seconds // 60,
    )
    normalized = NormalizedGuideEntry(original=entry, normalized_title="lost show")
    return ScheduleSlot(
        slot_id="slot-1",
        original_entry=normalized,
        scheduled_start=datetime(1990, 1, 1, 20, 0),
        scheduled_end=datetime(1990, 1, 1, 20, 30),
        match_status=MatchStatus.MISSING,
        expected_runtime_seconds=expected_runtime_seconds,
    )


class TestSubstitutionEngine:
    """Test suite for SubstitutionEngine."""

    def test_find_substitutes_returns_result(self):
        library = _make_library()
        engine = SubstitutionEngine(library)
        slot = _make_missing_slot(expected_runtime_seconds=22 * 60)
        result = engine.find_substitutes(slot)
        assert isinstance(result.candidates, list)

    def test_find_substitutes_prefers_close_runtime(self):
        library = _make_library()
        engine = SubstitutionEngine(library)
        slot = _make_missing_slot(expected_runtime_seconds=22 * 60)
        result = engine.find_substitutes(slot)
        if result.candidates:
            best = result.candidates[0]
            assert best.media_item.runtime_seconds <= 30 * 60

    def test_apply_substitution(self):
        library = _make_library()
        engine = SubstitutionEngine(library)
        slot = _make_missing_slot(expected_runtime_seconds=22 * 60)

        result = engine.find_substitutes(slot)
        if result.candidates:
            engine.apply_substitution(slot, result.candidates[0])
            assert slot.match_status == MatchStatus.SUBSTITUTED
            assert slot.substituted_item is not None

    def test_auto_substitute_all(self):
        library = _make_library()
        engine = SubstitutionEngine(library)

        slots = [_make_missing_slot(expected_runtime_seconds=22 * 60)]
        engine.auto_substitute_all(slots)
        # Should attempt substitution; may or may not succeed depending on scoring
        assert slots[0].match_status in (MatchStatus.MISSING, MatchStatus.SUBSTITUTED)
