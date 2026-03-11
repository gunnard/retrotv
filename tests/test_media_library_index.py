"""Tests for MediaLibrary ID index and find_by_id."""

import pytest

from retrotv.models.media import (
    MediaLibrary, Series, Episode, Movie, MediaSource, MediaType,
)


def _make_episode(ep_id, title="Show", season=1, episode=1):
    return Episode(
        id=ep_id, source=MediaSource.JELLYFIN, title=title,
        normalized_title=title.lower(), media_type=MediaType.EPISODE,
        runtime_seconds=1320, season_number=season, episode_number=episode,
    )


def _make_movie(mov_id, title="Movie"):
    return Movie(
        id=mov_id, source=MediaSource.JELLYFIN, title=title,
        normalized_title=title.lower(), media_type=MediaType.MOVIE,
        runtime_seconds=5400,
    )


def _make_library():
    lib = MediaLibrary(source=MediaSource.JELLYFIN)
    ep1 = _make_episode("ep-1", "Seinfeld", 1, 1)
    ep2 = _make_episode("ep-2", "Seinfeld", 1, 2)
    lib.series["seinfeld"] = Series(
        id="s-1", source=MediaSource.JELLYFIN, title="Seinfeld",
        normalized_title="seinfeld", seasons={1: [ep1, ep2]}, total_episodes=2,
    )
    lib.movies["die hard"] = _make_movie("m-1", "Die Hard")
    return lib


class TestMediaLibraryIndex:
    """Test suite for MediaLibrary lazy ID index."""

    def test_find_by_id_episode(self):
        lib = _make_library()
        item = lib.find_by_id("ep-1")
        assert item is not None
        assert item.id == "ep-1"

    def test_find_by_id_movie(self):
        lib = _make_library()
        item = lib.find_by_id("m-1")
        assert item is not None
        assert item.id == "m-1"

    def test_find_by_id_series(self):
        lib = _make_library()
        item = lib.find_by_id("s-1")
        assert item is not None
        assert item.id == "s-1"

    def test_find_by_id_missing(self):
        lib = _make_library()
        assert lib.find_by_id("nonexistent") is None

    def test_index_built_lazily(self):
        lib = _make_library()
        assert lib._id_index is None
        lib.find_by_id("ep-1")
        assert lib._id_index is not None

    def test_invalidate_index(self):
        lib = _make_library()
        lib.find_by_id("ep-1")
        assert lib._id_index is not None
        lib.invalidate_index()
        assert lib._id_index is None

    def test_index_contains_all_items(self):
        lib = _make_library()
        lib.find_by_id("_trigger_build")
        # 1 series + 2 episodes + 1 movie = 4
        assert len(lib._id_index) == 4

    def test_empty_library(self):
        lib = MediaLibrary(source=MediaSource.JELLYFIN)
        assert lib.find_by_id("anything") is None
