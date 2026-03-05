"""Tests for core data models."""

import pytest
from datetime import datetime, timedelta

from retrotv.models.guide import GuideEntry, NormalizedGuideEntry, GuideMetadata, GuideSource
from retrotv.models.media import (
    MediaLibrary, Series, Episode, Movie, MediaSource, MediaType,
)
from retrotv.models.schedule import ScheduleSlot, MatchStatus, ChannelSchedule


class TestGuideEntry:
    """Test suite for GuideEntry model."""

    def test_calculated_duration_from_explicit(self):
        entry = GuideEntry(title="Test", start_time=datetime.now(), duration_minutes=30)
        assert entry.calculated_duration == timedelta(minutes=30)

    def test_calculated_duration_from_times(self):
        start = datetime(2000, 1, 1, 20, 0)
        end = datetime(2000, 1, 1, 21, 0)
        entry = GuideEntry(title="Test", start_time=start, end_time=end)
        assert entry.calculated_duration == timedelta(hours=1)

    def test_calculated_duration_default(self):
        entry = GuideEntry(title="Test", start_time=datetime.now())
        assert entry.calculated_duration == timedelta(minutes=30)

    def test_duration_seconds(self):
        entry = GuideEntry(title="Test", start_time=datetime.now(), duration_minutes=60)
        assert entry.duration_seconds == 3600


class TestGuideMetadata:
    """Test suite for GuideMetadata model."""

    def test_decade_auto_calculated(self):
        meta = GuideMetadata(broadcast_date=datetime(1985, 6, 15))
        assert meta.decade == "1980s"

    def test_decade_explicit(self):
        meta = GuideMetadata(decade="1970s", broadcast_date=datetime(1975, 1, 1))
        assert meta.decade == "1970s"


class TestSeries:
    """Test suite for Series model."""

    def test_get_episode_exact(self):
        ep = Episode(
            id="e1", source=MediaSource.JELLYFIN, title="Show",
            normalized_title="show", media_type=MediaType.EPISODE,
            runtime_seconds=1320, season_number=2, episode_number=5,
        )
        series = Series(
            id="s1", source=MediaSource.JELLYFIN, title="Show",
            normalized_title="show", seasons={2: [ep]},
        )
        assert series.get_episode(2, 5) == ep
        assert series.get_episode(1, 1) is None

    def test_get_random_episode(self):
        ep = Episode(
            id="e1", source=MediaSource.JELLYFIN, title="Show",
            normalized_title="show", media_type=MediaType.EPISODE,
            runtime_seconds=1320, season_number=1, episode_number=1,
        )
        series = Series(
            id="s1", source=MediaSource.JELLYFIN, title="Show",
            normalized_title="show", seasons={1: [ep]},
        )
        assert series.get_random_episode() == ep

    def test_get_random_episode_empty(self):
        series = Series(
            id="s1", source=MediaSource.JELLYFIN, title="Show",
            normalized_title="show",
        )
        assert series.get_random_episode() is None

    def test_get_all_episodes(self):
        ep1 = Episode(
            id="e1", source=MediaSource.JELLYFIN, title="Show",
            normalized_title="show", media_type=MediaType.EPISODE,
            runtime_seconds=1320, season_number=1, episode_number=1,
        )
        ep2 = Episode(
            id="e2", source=MediaSource.JELLYFIN, title="Show",
            normalized_title="show", media_type=MediaType.EPISODE,
            runtime_seconds=1320, season_number=2, episode_number=1,
        )
        series = Series(
            id="s1", source=MediaSource.JELLYFIN, title="Show",
            normalized_title="show", seasons={1: [ep1], 2: [ep2]},
        )
        assert len(series.get_all_episodes()) == 2


class TestMediaLibrary:
    """Test suite for MediaLibrary model."""

    def test_empty_library_counts(self):
        lib = MediaLibrary(source=MediaSource.JELLYFIN)
        assert lib.total_series == 0
        assert lib.total_movies == 0
        assert lib.total_episodes == 0

    def test_library_counts(self):
        ep = Episode(
            id="e1", source=MediaSource.JELLYFIN, title="Show",
            normalized_title="show", media_type=MediaType.EPISODE,
            runtime_seconds=1320, season_number=1, episode_number=1,
        )
        lib = MediaLibrary(source=MediaSource.JELLYFIN)
        lib.series["show"] = Series(
            id="s1", source=MediaSource.JELLYFIN, title="Show",
            normalized_title="show", seasons={1: [ep]}, total_episodes=1,
        )
        lib.movies["movie"] = Movie(
            id="m1", source=MediaSource.JELLYFIN, title="Movie",
            normalized_title="movie", media_type=MediaType.MOVIE,
            runtime_seconds=5400,
        )
        assert lib.total_series == 1
        assert lib.total_movies == 1
        assert lib.total_episodes == 1


class TestScheduleSlot:
    """Test suite for ScheduleSlot model."""

    def test_final_item_matched(self):
        ep = Episode(
            id="e1", source=MediaSource.JELLYFIN, title="Show",
            normalized_title="show", media_type=MediaType.EPISODE,
            runtime_seconds=1320, season_number=1, episode_number=1,
        )
        entry = GuideEntry(title="Show", start_time=datetime.now())
        normalized = NormalizedGuideEntry(original=entry, normalized_title="show")
        slot = ScheduleSlot(
            slot_id="s1", original_entry=normalized,
            scheduled_start=datetime.now(), scheduled_end=datetime.now(),
            match_status=MatchStatus.MATCHED, matched_item=ep,
        )
        assert slot.final_item == ep

    def test_final_item_substituted(self):
        sub = Episode(
            id="e2", source=MediaSource.JELLYFIN, title="Other",
            normalized_title="other", media_type=MediaType.EPISODE,
            runtime_seconds=1320, season_number=1, episode_number=1,
        )
        entry = GuideEntry(title="Show", start_time=datetime.now())
        normalized = NormalizedGuideEntry(original=entry, normalized_title="show")
        slot = ScheduleSlot(
            slot_id="s1", original_entry=normalized,
            scheduled_start=datetime.now(), scheduled_end=datetime.now(),
            match_status=MatchStatus.SUBSTITUTED, substituted_item=sub,
        )
        assert slot.final_item == sub

    def test_has_content_missing(self):
        entry = GuideEntry(title="Show", start_time=datetime.now())
        normalized = NormalizedGuideEntry(original=entry, normalized_title="show")
        slot = ScheduleSlot(
            slot_id="s1", original_entry=normalized,
            scheduled_start=datetime.now(), scheduled_end=datetime.now(),
            match_status=MatchStatus.MISSING,
        )
        assert slot.has_content is False
